const WINDOW_RADIUS = 2;
const AUTOPLAY_MS = 6500;

const stage = document.querySelector('#stage');
const previousButton = document.querySelector('#previous');
const nextButton = document.querySelector('#next');
const previousFloatButton = document.querySelector('#previous-float');
const nextFloatButton = document.querySelector('#next-float');
const randomButton = document.querySelector('#random');
const playButton = document.querySelector('#play');
const playLabel = document.querySelector('#play-label');
const activeCount = document.querySelector('#active-count');
const totalCount = document.querySelector('#total-count');
const currentName = document.querySelector('#current-name');
const currentIndex = document.querySelector('#current-index');
const progress = document.querySelector('#progress');
const status = document.querySelector('#status');
const collectionState = document.querySelector('#collection-state');

let images = [];
let sequence = [];
let current = 0;
let autoplay = false;
let timer = 0;
let pointerStart = null;

const imageUrl = (name) => `./image/${encodeURIComponent(name)}`;

function normalizeIndex(value) {
  return (value + images.length) % images.length;
}

function shuffleSequence(avoidImage = -1) {
  sequence = images.map((_, index) => index);
  for (let index = sequence.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [sequence[index], sequence[swapIndex]] = [sequence[swapIndex], sequence[index]];
  }
  if (sequence.length > 1 && sequence[0] === avoidImage) {
    [sequence[0], sequence[1]] = [sequence[1], sequence[0]];
  }
  current = 0;
}

function setStatus(message) {
  status.textContent = message;
  collectionState.textContent = message;
}

function createSlide(index, depth) {
  const slide = document.createElement('article');
  const image = document.createElement('img');
  const label = document.createElement('span');
  const position = document.createElement('span');
  const sequenceIndex = normalizeIndex(index);
  const imageIndex = sequence[sequenceIndex];
  const imageName = images[imageIndex];

  slide.className = `slide ${depth === 0 ? 'current' : ''}`;
  slide.dataset.depth = String(depth);
  slide.style.zIndex = String(depth === 0 ? 20 : 20 - Math.abs(depth) * 2 - (depth > 0 ? 1 : 0));
  slide.style.setProperty('--x', `${depth * 82}%`);
  slide.style.setProperty('--y', `${Math.abs(depth) * 2}px`);
  slide.style.setProperty('--z', `${-Math.abs(depth) * 110}px`);
  slide.style.setProperty('--r', `${depth * 4.5}deg`);
  slide.style.setProperty('--s', `${depth === 0 ? 1.08 : 1 - Math.abs(depth) * .08}`);
  slide.style.setProperty('--o', depth === 0 ? '1' : depth === -1 || depth === 1 ? '.68' : '.28');
  slide.style.setProperty('--sat', depth === 0 ? '1' : '.55');
  slide.style.setProperty('--bright', depth === 0 ? '1' : '.68');
  slide.setAttribute('aria-hidden', depth === 0 ? 'false' : 'true');

  image.alt = imageName;
  image.loading = depth === 0 ? 'eager' : 'lazy';
  image.decoding = 'async';
  image.src = imageUrl(imageName);
  image.addEventListener('load', () => image.classList.add('ready'), { once: true });
  image.addEventListener('error', () => slide.classList.add('broken'), { once: true });

  label.textContent = imageName.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ');
  position.textContent = String(sequenceIndex + 1).padStart(4, '0');
  label.className = 'slide-label';
  position.className = 'slide-position';
  slide.append(image);
  const tag = document.createElement('div');
  tag.className = 'slide-tag';
  tag.append(label, position);
  slide.append(tag);
  return slide;
}

function render() {
  if (!images.length) return;
  const fragment = document.createDocumentFragment();
  for (let depth = -WINDOW_RADIUS; depth <= WINDOW_RADIUS; depth += 1) {
    fragment.append(createSlide(current + depth, depth));
  }
  stage.replaceChildren(fragment);
  const active = sequence[normalizeIndex(current)];
  activeCount.textContent = '5';
  totalCount.textContent = images.length.toLocaleString('fr-FR');
  currentName.textContent = images[active];
  currentIndex.textContent = String(normalizeIndex(current) + 1).padStart(4, '0');
  progress.style.width = `${((normalizeIndex(current) + 1) / images.length) * 100}%`;
  setStatus('FLUX ACTIF');
}

function move(step) {
  if (step > 0 && current === sequence.length - 1) {
    shuffleSequence(sequence[current]);
    render();
    return;
  }
  current = normalizeIndex(current + step);
  render();
}

function setAutoplay(value) {
  autoplay = value;
  window.clearInterval(timer);
  timer = autoplay ? window.setInterval(() => move(1), AUTOPLAY_MS) : 0;
  playButton.setAttribute('aria-pressed', String(autoplay));
  playLabel.textContent = autoplay ? 'PAUSE DU FLUX' : 'DÉFILEMENT';
  playButton.querySelector('.play-icon').textContent = autoplay ? 'Ⅱ' : '▶';
}

async function loadCollection() {
  try {
    const response = await fetch('./images.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`catalogue ${response.status}`);
    images = await response.json();
    if (!Array.isArray(images) || !images.length) throw new Error('catalogue vide');
    shuffleSequence();
    render();
  } catch (error) {
    stage.innerHTML = '<div class="loading-state">Le catalogue d’images est indisponible.</div>';
    setStatus('ERREUR CATALOGUE');
    console.error(error);
  }
}

previousButton.addEventListener('click', () => move(-1));
nextButton.addEventListener('click', () => move(1));
previousFloatButton.addEventListener('click', () => move(-1));
nextFloatButton.addEventListener('click', () => move(1));
randomButton.addEventListener('click', () => {
  if (images.length > 1) move(1);
});
playButton.addEventListener('click', () => setAutoplay(!autoplay));
document.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft') move(-1);
  if (event.key === 'ArrowRight') move(1);
  if (event.key === ' ') { event.preventDefault(); setAutoplay(!autoplay); }
});
stage.addEventListener('pointerdown', (event) => { pointerStart = event.clientX; stage.setPointerCapture?.(event.pointerId); });
stage.addEventListener('pointerup', (event) => {
  if (pointerStart === null) return;
  const distance = event.clientX - pointerStart;
  pointerStart = null;
  if (Math.abs(distance) > 45) move(distance > 0 ? -1 : 1);
});
document.addEventListener('visibilitychange', () => { if (document.hidden) setAutoplay(false); });

loadCollection();
