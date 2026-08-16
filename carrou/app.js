const WINDOW_RADIUS = 2;
const AUTOPLAY_MS = 6500;

const stage = document.querySelector('#stage');
const previousButton = document.querySelector('#previous');
const nextButton = document.querySelector('#next');
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
let current = 0;
let autoplay = false;
let timer = 0;
let pointerStart = null;

const imageUrl = (name) => `./image/${encodeURIComponent(name)}`;

function normalizeIndex(value) {
  return (value + images.length) % images.length;
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
  const normalized = normalizeIndex(index);

  slide.className = `slide ${depth === 0 ? 'current' : ''}`;
  slide.dataset.depth = String(depth);
  slide.style.setProperty('--x', `${depth * 25}%`);
  slide.style.setProperty('--y', `${Math.abs(depth) * 2}px`);
  slide.style.setProperty('--z', `${-Math.abs(depth) * 110}px`);
  slide.style.setProperty('--r', `${depth * 4.5}deg`);
  slide.style.setProperty('--s', `${1 - Math.abs(depth) * .08}`);
  slide.style.setProperty('--o', depth === 0 ? '1' : depth === -1 || depth === 1 ? '.68' : '.28');
  slide.style.setProperty('--sat', depth === 0 ? '1' : '.55');
  slide.style.setProperty('--bright', depth === 0 ? '1' : '.68');
  slide.setAttribute('aria-hidden', depth === 0 ? 'false' : 'true');

  image.alt = images[normalized];
  image.loading = depth === 0 ? 'eager' : 'lazy';
  image.decoding = 'async';
  image.src = imageUrl(images[normalized]);
  image.addEventListener('load', () => image.classList.add('ready'), { once: true });
  image.addEventListener('error', () => slide.classList.add('broken'), { once: true });

  label.textContent = images[normalized].replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ');
  position.textContent = String(normalized + 1).padStart(4, '0');
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
  const active = normalizeIndex(current);
  activeCount.textContent = '5';
  totalCount.textContent = images.length.toLocaleString('fr-FR');
  currentName.textContent = images[active];
  currentIndex.textContent = String(active + 1).padStart(4, '0');
  progress.style.width = `${((active + 1) / images.length) * 100}%`;
  setStatus('FLUX ACTIF');
}

function move(step) {
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
    render();
  } catch (error) {
    stage.innerHTML = '<div class="loading-state">Le catalogue d’images est indisponible.</div>';
    setStatus('ERREUR CATALOGUE');
    console.error(error);
  }
}

previousButton.addEventListener('click', () => move(-1));
nextButton.addEventListener('click', () => move(1));
randomButton.addEventListener('click', () => {
  if (images.length < 2) return;
  let next = current;
  while (next === current) next = Math.floor(Math.random() * images.length);
  current = next;
  render();
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
