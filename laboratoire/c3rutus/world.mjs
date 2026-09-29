import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { PERIODIC_TABLE } from "./periodic-table.mjs";
import { lifeClockSample } from "./life-clock.mjs";
import {
  C3,
  buildLocalProjections,
  echoAddress,
  elementForTick,
  snakeNext
} from "./core.mjs";
import {
  GLOBAL_BUBBLE,
  WORLD_CATALOG,
  encodeCarrier,
  routeWorld,
  transportEnvelope
} from "./world-router.mjs";

const CURRENT_WORLD = "MATTER/CARBON";
const CRYPTO_WORLD = "INFORMATION/CRYPTO";

const viewport = document.querySelector("#viewport");
const tickEl = document.querySelector("#tick");
const lifeBeatEl = document.querySelector("#life-beat");
const lifePhaseEl = document.querySelector("#life-phase");
const lifeResiduesEl = document.querySelector("#life-residues");
const phaseEl = document.querySelector("#phase");
const activeWorldEl = document.querySelector("#active-world");
const activeProjectionEl = document.querySelector("#active-projection");
const activeElementEl = document.querySelector("#active-element");
const echoEl = document.querySelector("#echo");
const selectionEl = document.querySelector("#selection");
const toggleBtn = document.querySelector("#toggle");
const stepBtn = document.querySelector("#step");
const resetBtn = document.querySelector("#reset");
const speedInput = document.querySelector("#speed");
const speedValue = document.querySelector("#speed-value");
const worldFromEl = document.querySelector("#world-from");
const worldToEl = document.querySelector("#world-to");
const routeWorldBtn = document.querySelector("#route-world");
const routeStatusEl = document.querySelector("#route-status");
const carrierOutputEl = document.querySelector("#carrier-output");

const projections = buildLocalProjections(PERIODIC_TABLE, CURRENT_WORLD);
const route = C3.snakeRoute;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x05070d, 0.016);

const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 140);
camera.position.set(0, 14, 29);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.minDistance = 9;
controls.maxDistance = 52;
controls.target.set(0, 0, 0);

scene.add(new THREE.AmbientLight(0x9bbcff, 0.7));
const keyLight = new THREE.PointLight(0xffd28f, 65, 58);
keyLight.position.set(2, 8, 8);
scene.add(keyLight);
const fillLight = new THREE.PointLight(0x6f7dff, 48, 52);
fillLight.position.set(-10, -4, -8);
scene.add(fillLight);

const root = new THREE.Group();
scene.add(root);

function wireSphere(radius, color, opacity, scaleY = 1, position = null) {
  const geometry = new THREE.SphereGeometry(radius, 48, 32);
  const material = new THREE.MeshBasicMaterial({
    color,
    wireframe: true,
    transparent: true,
    opacity
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.scale.y = scaleY;
  if (position) mesh.position.copy(position);
  root.add(mesh);
  return mesh;
}

// Niveau 0 : bulle globale ANTMUX.
const globalEnvelope = wireSphere(14.4, 0xd8e6ff, 0.095, 0.9);
globalEnvelope.userData.kind = "global-envelope";

// Niveau 1 : monde actif CARBONE avec son Verso local.
const localEnvelope = wireSphere(9.0, 0xf0c878, 0.17, 0.82);
const zShell = wireSphere(6.7, 0x72b7ff, 0.16, 0.72);
const negZShell = wireSphere(5.25, 0xa487ff, 0.16, 0.72);

const localVerso = new THREE.Mesh(
  new THREE.IcosahedronGeometry(0.78, 2),
  new THREE.MeshStandardMaterial({
    color: 0xe6ecff,
    emissive: 0x7d79ff,
    emissiveIntensity: 1.7,
    roughness: 0.18,
    metalness: 0.35
  })
);
localVerso.userData.kind = "verso-local";
root.add(localVerso);

const carbonLabel = makeLabel("MATTER / CARBON", 22);
carbonLabel.position.set(0, 8.1, 0);
root.add(carbonLabel);

// Monde CRYPTO distinct, contenu dans la même grande bulle.
const cryptoCenter = new THREE.Vector3(10.15, 4.1, -3.0);
const cryptoBubble = wireSphere(2.05, 0x71ffd7, 0.32, 1, cryptoCenter);
cryptoBubble.userData.kind = "world-crypto";

const cryptoCore = new THREE.Mesh(
  new THREE.OctahedronGeometry(0.62, 1),
  new THREE.MeshStandardMaterial({
    color: 0xb7fff0,
    emissive: 0x0bffc9,
    emissiveIntensity: 1.4,
    roughness: 0.25,
    metalness: 0.45
  })
);
cryptoCore.position.copy(cryptoCenter);
root.add(cryptoCore);

const cryptoLabel = makeLabel("INFORMATION / CRYPTO", 20);
cryptoLabel.position.copy(cryptoCenter).add(new THREE.Vector3(0, 2.75, 0));
root.add(cryptoLabel);

const cryptoBits = [];
for (let i = 0; i < 96; i += 1) {
  const angle = i * 2.399963229728653;
  const r = 0.5 + (i % 12) * 0.09;
  cryptoBits.push(
    cryptoCenter.x + Math.cos(angle) * r,
    cryptoCenter.y + ((i % 9) - 4) * 0.12,
    cryptoCenter.z + Math.sin(angle) * r
  );
}
const cryptoBitGeometry = new THREE.BufferGeometry();
cryptoBitGeometry.setAttribute("position", new THREE.Float32BufferAttribute(cryptoBits, 3));
const cryptoBitCloud = new THREE.Points(
  cryptoBitGeometry,
  new THREE.PointsMaterial({
    color: 0x7dffd9,
    size: 0.075,
    transparent: true,
    opacity: 0.75
  })
);
root.add(cryptoBitCloud);

// Verso global : il ne remplace pas le Verso local, il ajoute la porte inter-mondes.
const globalVersoPosition = new THREE.Vector3(7.2, 2.85, -2.1);
const globalVerso = new THREE.Mesh(
  new THREE.TorusGeometry(0.78, 0.12, 18, 72),
  new THREE.MeshStandardMaterial({
    color: 0xffffff,
    emissive: 0x49e8ff,
    emissiveIntensity: 1.2,
    roughness: 0.22,
    metalness: 0.55
  })
);
globalVerso.position.copy(globalVersoPosition);
globalVerso.rotation.y = Math.PI / 3;
globalVerso.userData.kind = "verso-global";
root.add(globalVerso);

const globalVersoLabel = makeLabel("VERSO GLOBAL", 20);
globalVersoLabel.position.copy(globalVersoPosition).add(new THREE.Vector3(0, 1.35, 0));
root.add(globalVersoLabel);

const portalCurve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(0, 0, 0),
  new THREE.Vector3(3.7, 1.2, -0.8),
  globalVersoPosition.clone(),
  cryptoCenter.clone()
]);
const portalGeometry = new THREE.BufferGeometry().setFromPoints(portalCurve.getPoints(96));
const portalMaterial = new THREE.LineDashedMaterial({
  color: 0x8fffea,
  dashSize: 0.34,
  gapSize: 0.18,
  transparent: true,
  opacity: 0.5
});
const portalLine = new THREE.Line(portalGeometry, portalMaterial);
portalLine.computeLineDistances();
root.add(portalLine);

// Familles non réalisées : ancres visibles, mais portails fermés tant qu'aucun contrat n'existe.
const familyAnchors = [
  ["TIME/CLOCK", new THREE.Vector3(-10.2, 5.2, -2.4), 0xb6c8ff],
  ["MATH/GEOMETRY", new THREE.Vector3(-9.4, -4.8, 4.2), 0xffcf8b],
  ["BIO/CELL", new THREE.Vector3(8.2, -6.0, 3.8), 0xa5ffb8],
  ["ENERGY/FREQUENCY", new THREE.Vector3(0.5, 7.4, -9.6), 0xff9fca]
];
for (const [id, position, color] of familyAnchors) {
  const anchor = new THREE.Mesh(
    new THREE.DodecahedronGeometry(0.42, 0),
    new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: 0.45,
      roughness: 0.45,
      metalness: 0.22,
      transparent: true,
      opacity: 0.72
    })
  );
  anchor.position.copy(position);
  anchor.userData = { kind: "world-stub", worldAddress: id };
  root.add(anchor);
  const label = makeLabel(id, 17);
  label.position.copy(position).add(new THREE.Vector3(0, 0.85, 0));
  root.add(label);
}

const axisMaterial = new THREE.LineBasicMaterial({
  color: 0xd3ddff,
  transparent: true,
  opacity: 0.16
});
const axisPoints = [new THREE.Vector3(0, -10, 0), new THREE.Vector3(0, 10, 0)];
root.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(axisPoints), axisMaterial));

const projectionPositions = new Map();
const projectionMeshes = [];
const ringRadius = 5.9;

for (const projection of projections) {
  const angle = -Math.PI / 2 + ((projection.id - 1) / C3.projectionCount) * Math.PI * 2;
  const y = Math.sin(angle * 3) * 1.45;
  const position = new THREE.Vector3(
    Math.cos(angle) * ringRadius,
    y,
    Math.sin(angle) * ringRadius
  );
  projectionPositions.set(projection.id, position);

  const mesh = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.43, 2),
    new THREE.MeshStandardMaterial({
      color: projection.triangle === 1 ? 0x75b7ff : projection.triangle === 2 ? 0xe3a6ff : 0xf2c676,
      emissive: projection.triangle === 1 ? 0x173e76 : projection.triangle === 2 ? 0x54296c : 0x624716,
      emissiveIntensity: 0.9,
      roughness: 0.32,
      metalness: 0.22
    })
  );
  mesh.position.copy(position);
  mesh.userData = { kind: "projection", projectionId: projection.id };
  root.add(mesh);
  projectionMeshes.push(mesh);

  const label = makeLabel(`P${projection.id}`, 24);
  label.position.copy(position).add(new THREE.Vector3(0, 0.78, 0));
  root.add(label);
}

function makeLoop(ids, color, opacity = 0.42) {
  const points = ids.map(id => projectionPositions.get(id).clone());
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

const snakePoints = route.map(id => projectionPositions.get(id).clone());
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

// Le tableau périodique est une référence locale partagée par les 9 projections.
const elementPositions = [];
for (const projection of projections) {
  const center = projectionPositions.get(projection.id);
  for (const element of PERIODIC_TABLE) {
    const n = element.atomicNumber - 1;
    const fraction = n / (PERIODIC_TABLE.length - 1);
    const angle = n * 2.399963229728653 + projection.id * 0.41;
    const localRadius = 1.2 - fraction * 0.85;
    elementPositions.push(
      center.x + Math.cos(angle) * localRadius,
      center.y + (fraction - 0.5) * 0.95,
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
    size: 0.05,
    transparent: true,
    opacity: 0.58,
    sizeAttenuation: true
  })
);
root.add(elementCloud);

const stars = [];
for (let i = 0; i < 900; i += 1) {
  const u = pseudo(i * 3 + 1);
  const v = pseudo(i * 3 + 2);
  const w = pseudo(i * 3 + 3);
  const radius = 19 + u * 35;
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
  new THREE.PointsMaterial({
    color: 0xaac4ff,
    size: 0.08,
    transparent: true,
    opacity: 0.5
  })
));

const ants = Array.from({ length: C3.projectionCount }, (_, index) => {
  const ant = makeAnt(index);
  root.add(ant);
  return ant;
});

const travelerAnt = makeAnt(10);
travelerAnt.visible = false;
travelerAnt.scale.setScalar(1.45);
root.add(travelerAnt);

let running = false;
let elapsedMs = 0;
let tick = 0;
let progress = 0;
let speed = 1;
let selectedProjectionId = null;
let lastTime = performance.now();
let portalTravel = null;
let portalPulse = 0;

populateRouter();

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
    const from = projectionPositions.get(fromId);
    const to = projectionPositions.get(toId);
    ant.position.lerpVectors(from, to, eased);
    ant.lookAt(to);
  });
}

function currentState() {
  const projectionId = route[tick % route.length];
  const element = elementForTick(projectionId, tick, PERIODIC_TABLE);
  return {
    projectionId,
    element,
    echo: echoAddress(CURRENT_WORLD, projectionId, element.atomicNumber, tick)
  };
}

function updateUI() {
  const state = currentState();
  const life = lifeClockSample(elapsedMs);
  tickEl.textContent = String(tick);
  lifeBeatEl.textContent = life.beat.toLocaleString("fr-CA");
  lifePhaseEl.textContent = `${String(life.phase546).padStart(3, "0")}/545`;
  lifeResiduesEl.textContent = `${life.r6} · ${life.r7} · ${life.r13}`;
  phaseEl.textContent = `${(tick % 3) + 1}/3`;
  activeWorldEl.textContent = CURRENT_WORLD;
  activeProjectionEl.textContent = `P${String(state.projectionId).padStart(2, "0")}`;
  activeElementEl.textContent = `${state.element.symbol} · ${state.element.atomicNumber}`;
  echoEl.textContent = state.echo;

  projectionMeshes.forEach(mesh => {
    const active = mesh.userData.projectionId === state.projectionId;
    mesh.scale.setScalar(active ? 1.45 : 1);
  });

  if (selectedProjectionId !== null) updateSelection(selectedProjectionId);
}

function updateSelection(projectionId) {
  const projection = projections[projectionId - 1];
  const element = elementForTick(projectionId, tick, PERIODIC_TABLE);
  const echo = echoAddress(CURRENT_WORLD, projectionId, element.atomicNumber, tick);
  selectionEl.innerHTML = [
    `<strong>${escapeHtml(CURRENT_WORLD)} · P${String(projectionId).padStart(2, "0")}</strong>`,
    `Triangle ${projection.triangle} · position locale ${projection.localPosition}`,
    `Z=${projection.zBase} · −Z=${projection.negZBase} · enveloppe locale=${projection.envelope}`,
    `Verso local : Z ↔ −Z`,
    `Référence périodique active : ${element.symbol} (${element.atomicNumber})`,
    `<code>${escapeHtml(echo)}</code>`
  ].join("<br>");
}

function populateRouter() {
  for (const world of WORLD_CATALOG) {
    const fromOption = document.createElement("option");
    fromOption.value = world.id;
    fromOption.textContent = `${world.id} · ${world.status}`;
    worldFromEl.appendChild(fromOption);

    const toOption = fromOption.cloneNode(true);
    worldToEl.appendChild(toOption);
  }
  worldFromEl.value = CURRENT_WORLD;
  worldToEl.value = CRYPTO_WORLD;
}

function runWorldRoute() {
  const from = worldFromEl.value;
  const to = worldToEl.value;
  const worldRoute = routeWorld(from, to);

  if (!worldRoute.open) {
    routeStatusEl.innerHTML = [
      `<strong>PORTAIL FERMÉ</strong>`,
      `${escapeHtml(from)} → ${escapeHtml(to)}`,
      `Raison : ${escapeHtml(worldRoute.reason)}`,
      `Aucune transformation définie = aucun passage arbitraire.`
    ].join("<br>");
    carrierOutputEl.textContent = "Transport : —";
    return;
  }

  const state = currentState();
  const envelope = transportEnvelope({
    antId: "ANT-PORTAL-01",
    from,
    to,
    tick,
    state: "ROUTING",
    proofRef: worldRoute.portal?.id ?? "SAME-WORLD",
    echo: state.echo
  });

  routeStatusEl.innerHTML = [
    `<strong>PORTAIL OUVERT</strong>`,
    `${escapeHtml(worldRoute.path.join(" → "))}`,
    `Identité transportée : ${escapeHtml(envelope.invariant?.antId ?? "—")}`,
    `Tick conservé : ${escapeHtml(String(envelope.invariant?.tick ?? "—"))}`
  ].join("<br>");

  if (from === CURRENT_WORLD && to === CRYPTO_WORLD) {
    const carrier = encodeCarrier("C");
    carrierOutputEl.innerHTML = [
      `<strong>Transport UTF‑8, pas chiffrement :</strong>`,
      `C → hex ${carrier.hex} → bits ${carrier.binary}`,
      `Le monde Crypto reçoit une représentation transportable; les opérations cryptographiques viennent après.`
    ].join("<br>");
    portalTravel = { startedAt: performance.now(), duration: 2200, reverse: false };
    portalPulse = 1;
  } else if (from === CRYPTO_WORLD && to === CURRENT_WORLD) {
    const carrier = encodeCarrier("C");
    carrierOutputEl.innerHTML = [
      `<strong>Retour vérifiable :</strong>`,
      `hex ${carrier.hex} → C`,
      `Contrat : ${escapeHtml(worldRoute.portal?.id ?? "—")}`
    ].join("<br>");
    portalTravel = { startedAt: performance.now(), duration: 2200, reverse: true };
    portalPulse = 1;
  } else {
    carrierOutputEl.textContent = "Transport : même monde, aucune traduction nécessaire.";
  }
}

function setRunning(next) {
  running = next;
  toggleBtn.textContent = running ? "Pause" : "Démarrer";
}

toggleBtn.addEventListener("click", () => setRunning(!running));
stepBtn.addEventListener("click", () => {
  setRunning(false);
  elapsedMs += 1000;
  const life = lifeClockSample(elapsedMs);
  tick = life.actionTick;
  progress = life.seconds - tick;
  updateUI();
});
resetBtn.addEventListener("click", () => {
  setRunning(false);
  elapsedMs = 0;
  tick = 0;
  progress = 0;
  portalTravel = null;
  travelerAnt.visible = false;
  controls.reset();
  updateUI();
});
speedInput.addEventListener("input", () => {
  speed = Number(speedInput.value);
  speedValue.textContent = `${speed.toFixed(2).replace(/0+$/, "").replace(/\.$/, "")}×`;
});
routeWorldBtn.addEventListener("click", runWorldRoute);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
renderer.domElement.addEventListener("pointerdown", event => {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(projectionMeshes, false)[0];
  if (!hit) return;
  selectedProjectionId = hit.object.userData.projectionId;
  updateSelection(selectedProjectionId);
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

function animatePortal(now) {
  if (!portalTravel) {
    travelerAnt.visible = false;
    return;
  }

  let t = Math.min(1, (now - portalTravel.startedAt) / portalTravel.duration);
  if (portalTravel.reverse) t = 1 - t;
  const point = portalCurve.getPoint(t);
  const look = portalCurve.getPoint(Math.min(1, Math.max(0, t + (portalTravel.reverse ? -0.01 : 0.01))));
  travelerAnt.visible = true;
  travelerAnt.position.copy(point);
  travelerAnt.lookAt(look);

  if (now - portalTravel.startedAt >= portalTravel.duration) {
    travelerAnt.visible = false;
    portalTravel = null;
  }
}

function animate(now) {
  const dt = Math.min((now - lastTime) / 1000, 0.1);
  lastTime = now;

  if (running) {
    elapsedMs += dt * 1000 * speed;
    const life = lifeClockSample(elapsedMs);
    const nextTick = life.actionTick;
    progress = life.seconds - nextTick;
    if (nextTick !== tick) tick = nextTick;
    updateUI();
  }

  updateAnts();
  animatePortal(now);

  const lifePhase = lifeClockSample(elapsedMs).fraction;
  globalEnvelope.rotation.y += dt * 0.009;
  localEnvelope.rotation.y += dt * 0.022;
  zShell.rotation.y -= dt * 0.035;
  negZShell.rotation.y += dt * 0.045;
  localVerso.rotation.z = lifePhase * Math.PI * 2;
  localVerso.rotation.x += dt * 0.22;
  localVerso.rotation.y -= dt * 0.27;
  globalVerso.rotation.z += dt * 0.45;
  cryptoBubble.rotation.y -= dt * 0.08;
  cryptoCore.rotation.x += dt * 0.28;
  cryptoCore.rotation.y -= dt * 0.34;
  cryptoBitCloud.rotation.y += dt * 0.05;
  elementCloud.rotation.y += dt * 0.006;

  portalPulse = Math.max(0, portalPulse - dt * 0.42);
  globalVerso.material.emissiveIntensity = 1.2 + portalPulse * 3.0;
  portalMaterial.opacity = 0.5 + portalPulse * 0.45;

  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

function makeLabel(text, fontSize = 24) {
  const canvas = document.createElement("canvas");
  canvas.width = 320;
  canvas.height = 72;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = `600 ${fontSize}px system-ui`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#eef4ff";
  ctx.fillText(text, 160, 36);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false
  }));
  sprite.scale.set(3.2, 0.72, 1);
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
