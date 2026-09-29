import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { PERIODIC_TABLE } from "./periodic-table.mjs";
import {
  C3,
  buildWorlds,
  echoAddress,
  elementForTick,
  snakeNext
} from "./core.mjs";

const viewport = document.querySelector("#viewport");
const tickEl = document.querySelector("#tick");
const phaseEl = document.querySelector("#phase");
const activeWorldEl = document.querySelector("#active-world");
const activeElementEl = document.querySelector("#active-element");
const echoEl = document.querySelector("#echo");
const selectionEl = document.querySelector("#selection");
const toggleBtn = document.querySelector("#toggle");
const stepBtn = document.querySelector("#step");
const resetBtn = document.querySelector("#reset");
const speedInput = document.querySelector("#speed");
const speedValue = document.querySelector("#speed-value");

const worlds = buildWorlds(PERIODIC_TABLE);
const route = C3.snakeRoute;
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x05070d, 0.018);

const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 120);
camera.position.set(0, 13, 25);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.minDistance = 8;
controls.maxDistance = 44;
controls.target.set(0, 0, 0);

scene.add(new THREE.AmbientLight(0x9bbcff, 0.7));
const keyLight = new THREE.PointLight(0xffd28f, 55, 50);
keyLight.position.set(2, 8, 8);
scene.add(keyLight);
const fillLight = new THREE.PointLight(0x6f7dff, 40, 45);
fillLight.position.set(-10, -4, -8);
scene.add(fillLight);

const root = new THREE.Group();
scene.add(root);

function wireSphere(radius, color, opacity, scaleY = 1) {
  const geometry = new THREE.SphereGeometry(radius, 48, 32);
  const material = new THREE.MeshBasicMaterial({
    color,
    wireframe: true,
    transparent: true,
    opacity
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.scale.y = scaleY;
  root.add(mesh);
  return mesh;
}

const envelope = wireSphere(11.5, 0xf0c878, 0.18, 0.82);
const zShell = wireSphere(8.25, 0x72b7ff, 0.16, 0.72);
const negZShell = wireSphere(6.4, 0xa487ff, 0.16, 0.72);

const verso = new THREE.Mesh(
  new THREE.IcosahedronGeometry(0.85, 2),
  new THREE.MeshStandardMaterial({
    color: 0xe6ecff,
    emissive: 0x7d79ff,
    emissiveIntensity: 1.7,
    roughness: 0.18,
    metalness: 0.35
  })
);
verso.userData.kind = "verso";
root.add(verso);

const axisMaterial = new THREE.LineBasicMaterial({ color: 0xd3ddff, transparent: true, opacity: 0.22 });
const axisPoints = [new THREE.Vector3(0, -10, 0), new THREE.Vector3(0, 10, 0)];
root.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(axisPoints), axisMaterial));

const worldPositions = new Map();
const worldMeshes = [];
const ringRadius = 7.6;

for (const world of worlds) {
  const angle = -Math.PI / 2 + ((world.id - 1) / C3.worldCount) * Math.PI * 2;
  const y = Math.sin(angle * 3) * 1.8;
  const position = new THREE.Vector3(
    Math.cos(angle) * ringRadius,
    y,
    Math.sin(angle) * ringRadius
  );
  worldPositions.set(world.id, position);

  const mesh = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.48, 2),
    new THREE.MeshStandardMaterial({
      color: world.triangle === 1 ? 0x75b7ff : world.triangle === 2 ? 0xe3a6ff : 0xf2c676,
      emissive: world.triangle === 1 ? 0x173e76 : world.triangle === 2 ? 0x54296c : 0x624716,
      emissiveIntensity: 0.9,
      roughness: 0.32,
      metalness: 0.22
    })
  );
  mesh.position.copy(position);
  mesh.userData = { kind: "world", worldId: world.id };
  root.add(mesh);
  worldMeshes.push(mesh);

  const label = makeLabel(`W${world.id}`);
  label.position.copy(position).add(new THREE.Vector3(0, 0.9, 0));
  root.add(label);
}

function makeLoop(ids, color, opacity = 0.42) {
  const points = ids.map(id => worldPositions.get(id).clone());
  points.push(points[0].clone());
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(points),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity })
  );
  root.add(line);
  return line;
}

makeLoop([1, 2, 3], 0x68b3ff);
makeLoop([4, 5, 6], 0xd997ff);
makeLoop([7, 8, 9], 0xf4c96d);

const snakePoints = route.map(id => worldPositions.get(id).clone());
snakePoints.push(snakePoints[0].clone());
const snake = new THREE.Line(
  new THREE.BufferGeometry().setFromPoints(snakePoints),
  new THREE.LineDashedMaterial({
    color: 0xffffff,
    dashSize: 0.32,
    gapSize: 0.18,
    transparent: true,
    opacity: 0.55
  })
);
snake.computeLineDistances();
root.add(snake);

const elementPositions = [];
for (const world of worlds) {
  const center = worldPositions.get(world.id);
  for (const element of PERIODIC_TABLE) {
    const n = element.atomicNumber - 1;
    const fraction = n / (PERIODIC_TABLE.length - 1);
    const angle = n * 2.399963229728653 + world.id * 0.41;
    const localRadius = 1.5 - fraction * 1.1;
    elementPositions.push(
      center.x + Math.cos(angle) * localRadius,
      center.y + (fraction - 0.5) * 1.2,
      center.z + Math.sin(angle) * localRadius
    );
  }
}
const elementGeometry = new THREE.BufferGeometry();
elementGeometry.setAttribute("position", new THREE.Float32BufferAttribute(elementPositions, 3));
const elementCloud = new THREE.Points(
  elementGeometry,
  new THREE.PointsMaterial({
    color: 0xcbd9ff,
    size: 0.055,
    transparent: true,
    opacity: 0.62,
    sizeAttenuation: true
  })
);
root.add(elementCloud);

const stars = [];
for (let i = 0; i < 900; i += 1) {
  const u = pseudo(i * 3 + 1);
  const v = pseudo(i * 3 + 2);
  const w = pseudo(i * 3 + 3);
  const radius = 18 + u * 32;
  const theta = v * Math.PI * 2;
  const phi = Math.acos(2 * w - 1);
  stars.push(
    radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}
const starGeometry = new THREE.BufferGeometry();
starGeometry.setAttribute("position", new THREE.Float32BufferAttribute(stars, 3));
scene.add(new THREE.Points(
  starGeometry,
  new THREE.PointsMaterial({ color: 0xaac4ff, size: 0.08, transparent: true, opacity: 0.5 })
));

const ants = Array.from({ length: 9 }, (_, index) => {
  const ant = makeAnt(index);
  root.add(ant);
  return ant;
});

let running = false;
let tick = 0;
let progress = 0;
let speed = 1;
let selectedWorldId = null;
let lastTime = performance.now();

function makeAnt(index) {
  const group = new THREE.Group();
  const material = new THREE.MeshStandardMaterial({
    color: index % 3 === 0 ? 0xffd277 : index % 3 === 1 ? 0xb4c7ff : 0xe5b0ff,
    emissive: 0x38220a,
    emissiveIntensity: 0.5,
    roughness: 0.35
  });
  const body = new THREE.Mesh(new THREE.SphereGeometry(0.13, 12, 8), material);
  body.scale.set(1.35, 0.8, 0.9);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 8), material);
  head.position.x = 0.18;
  const tail = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 8), material);
  tail.position.x = -0.2;
  group.add(body, head, tail);
  group.userData.antIndex = index;
  return group;
}

function updateAnts() {
  const eased = progress * progress * (3 - 2 * progress);
  ants.forEach((ant, index) => {
    const fromId = route[(tick + index) % route.length];
    const toId = snakeNext(fromId);
    const from = worldPositions.get(fromId);
    const to = worldPositions.get(toId);
    ant.position.lerpVectors(from, to, eased);
    ant.lookAt(to);
  });
}

function currentState() {
  const worldId = route[tick % route.length];
  const element = elementForTick(worldId, tick, PERIODIC_TABLE);
  return {
    worldId,
    element,
    echo: echoAddress(worldId, element.atomicNumber, tick)
  };
}

function updateUI() {
  const state = currentState();
  tickEl.textContent = String(tick);
  phaseEl.textContent = `${(tick % 3) + 1}/3`;
  activeWorldEl.textContent = `W${String(state.worldId).padStart(2, "0")}`;
  activeElementEl.textContent = `${state.element.symbol} · ${state.element.atomicNumber}`;
  echoEl.textContent = state.echo;

  worldMeshes.forEach(mesh => {
    const active = mesh.userData.worldId === state.worldId;
    mesh.scale.setScalar(active ? 1.45 : 1);
  });

  if (selectedWorldId !== null) updateSelection(selectedWorldId);
}

function updateSelection(worldId) {
  const world = worlds[worldId - 1];
  const element = elementForTick(worldId, tick, PERIODIC_TABLE);
  const echo = echoAddress(worldId, element.atomicNumber, tick);
  selectionEl.innerHTML = [
    `<strong>W${String(worldId).padStart(2, "0")}</strong>`,
    `Triangle ${world.triangle} · position locale ${world.localPosition}`,
    `Z=${world.zBase} · −Z=${world.negZBase} · enveloppe=${world.envelope}`,
    `118 éléments partagés · actif: ${element.symbol} (${element.atomicNumber})`,
    `<code>${escapeHtml(echo)}</code>`
  ].join("<br>");
}

function setRunning(next) {
  running = next;
  toggleBtn.textContent = running ? "Pause" : "Démarrer";
}

toggleBtn.addEventListener("click", () => setRunning(!running));
stepBtn.addEventListener("click", () => {
  setRunning(false);
  tick += 1;
  progress = 0;
  updateUI();
});
resetBtn.addEventListener("click", () => {
  setRunning(false);
  tick = 0;
  progress = 0;
  controls.reset();
  updateUI();
});
speedInput.addEventListener("input", () => {
  speed = Number(speedInput.value);
  speedValue.textContent = `${speed.toFixed(2).replace(/0+$/, "").replace(/\.$/, "")}×`;
});

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
renderer.domElement.addEventListener("pointerdown", event => {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(worldMeshes, false)[0];
  if (!hit) return;
  selectedWorldId = hit.object.userData.worldId;
  updateSelection(selectedWorldId);
});

const resizeObserver = new ResizeObserver(resize);
resizeObserver.observe(viewport);

function resize() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function animate(now) {
  const dt = Math.min((now - lastTime) / 1000, 0.1);
  lastTime = now;

  if (running) {
    progress += dt * speed / 1.15;
    while (progress >= 1) {
      progress -= 1;
      tick += 1;
      updateUI();
    }
  }

  updateAnts();
  envelope.rotation.y += dt * 0.025;
  zShell.rotation.y -= dt * 0.035;
  negZShell.rotation.y += dt * 0.045;
  verso.rotation.x += dt * 0.22;
  verso.rotation.y -= dt * 0.27;
  elementCloud.rotation.y += dt * 0.006;
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

function makeLabel(text) {
  const canvas = document.createElement("canvas");
  canvas.width = 160;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = "600 30px system-ui";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#eef4ff";
  ctx.fillText(text, 80, 32);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false }));
  sprite.scale.set(1.6, 0.64, 1);
  return sprite;
}

function pseudo(seed) {
  const x = Math.sin(seed * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}

resize();
updateUI();
updateAnts();
requestAnimationFrame(animate);
