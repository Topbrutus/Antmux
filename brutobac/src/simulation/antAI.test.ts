/**
 * Automated Test Suite — BLOC 3: FOURMIS INDIVIDUELLES ET AGENTS LOCAUX
 * Validates individual ant identity, physical traits, local perception,
 * action history, size scaling, and inspection data completeness.
 */

import {
  createAnt,
  generateInitialAnts,
  evaluateQueenDigOrders,
  evaluateQueenRoomOrders,
  executeQueenRoomOrder,
  decideQueenRoomOrder,
  getAvailableCavities,
  QUEEN_ALLOWED_ROOM_TYPES,
  QueenRoomOrder,
} from './antAI';
import { generateInitialGrid, getAccessibleDigFronts, isDesignatedRoom, digOrganicCavity } from './grid';
import {
  getVisibleCells,
  logAntAction,
  getAntInspectionData,
  generateAntAttributes,
} from './antAgent';
import { Ant, DigTask } from '../types/colony';
import { ColonyEngine } from './colonyEngine';

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function assertNotNull<T>(val: T, message: string): asserts val is NonNullable<T> {
  if (val === null || val === undefined) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function runAntAgentTests() {
  console.log('================================================================');
  console.log('RUNNING AGENT SUITE — BLOC 3: FOURMIS INDIVIDUELLES');
  console.log('================================================================\n');

  // ---------------------------------------------------------------------------
  // TEST 1 — INDIVIDUAL ANT ATTRIBUTES & STABLE ANT_ID
  // ---------------------------------------------------------------------------
  console.log('TEST 1: Verification of individual attributes & stable ant_id...');
  const initialAnts = generateInitialAnts();

  assert(initialAnts.length > 0, 'Initial ants array should not be empty');

  for (const ant of initialAnts) {
    assert(typeof ant.id === 'string' && ant.id.length > 0, 'Ant must have id');
    assert(typeof ant.ant_id === 'string' && ant.ant_id === ant.id, 'ant_id must match id and be stable');
    assert(typeof ant.x === 'number' && typeof ant.y === 'number', 'Position (x,y) must be numbers');
    assert(typeof ant.age === 'number' && ant.age >= 0, 'Age must be a positive number');
    assert(typeof ant.size === 'number' && ant.size >= 0.75 && ant.size <= 1.6, 'Size must be in valid scale');
    assert(typeof ant.speed === 'number' && ant.speed > 0, 'Speed must be positive');
    assert(typeof ant.strength === 'number' && ant.strength > 0, 'Strength must be positive');
    assert(typeof ant.carryCapacity === 'number' && ant.carryCapacity >= 1, 'Carry capacity must be >= 1');
    assert(typeof ant.digProficiency === 'number' && ant.digProficiency > 0, 'Dig proficiency must be positive');
    assert(typeof ant.currentTask === 'string' && ant.currentTask.length > 0, 'Current task must be a non-empty string');
    assert(ant.currentDestination === null || typeof ant.currentDestination === 'object', 'Destination must be valid');
    assert(Array.isArray(ant.recentActions), 'Recent actions must be an array');
    assert(ant.recentActions.length > 0, 'Initial action history should be seeded');
  }

  console.log(`PASS — INDIVIDUAL_ATTRIBUTES_VALIDATED (${initialAnts.length} ants checked)\n`);

  // ---------------------------------------------------------------------------
  // TEST 2 — LOCAL SENSORY PERCEPTION (getVisibleCells)
  // ---------------------------------------------------------------------------
  console.log('TEST 2: Local Perception (getVisibleCells) & Sensory Radius...');
  const grid = generateInitialGrid(3861);
  const testAnt = createAnt('MINER', 41, 20);

  const radius = 4;
  const visible = getVisibleCells(testAnt, grid, radius);

  assert(visible.length > 0, 'Ant must detect nearby cells');

  // Verify that all returned cells are within Euclidean distance <= radius
  for (const vc of visible) {
    const dist = Math.hypot(vc.x - testAnt.x, vc.y - testAnt.y);
    assert(
      dist <= radius + 0.1,
      `Cell at (${vc.x}, ${vc.y}) is at distance ${dist.toFixed(2)}, which exceeds radius ${radius}`
    );
  }

  // A distant cell (e.g. at x=10, y=80) must NOT be perceived
  const distantFound = visible.some((vc) => vc.x === 10 && vc.y === 80);
  assert(!distantFound, 'Distant cell outside sensory perimeter must NOT be visible');

  // Check that the ant updated its local memory
  assert(testAnt.knownCells.length > 0, 'Ant must record perceived cells in local memory');
  assert(testAnt.knownCells.includes('41,20'), 'Current location must be in known cells');

  console.log(`PASS — LOCAL_PERCEPTION_VALIDATED (${visible.length} cells perceived within radius ${radius})\n`);

  // ---------------------------------------------------------------------------
  // TEST 3 — SIZE DIVERSITY & ATTRIBUTE CORRELATIONS
  // ---------------------------------------------------------------------------
  console.log('TEST 3: Biological Size Diversity & Attribute Scaling...');
  const sampleSizes: number[] = [];
  const smallAntAttrs = generateAntAttributes('MINER', 0.85);
  const largeAntAttrs = generateAntAttributes('MINER', 1.30);

  // Strength scales positively with size
  assert(
    largeAntAttrs.strength >= smallAntAttrs.strength,
    'Larger ant must have equal or greater physical strength'
  );

  // Dig proficiency scales positively with size
  assert(
    largeAntAttrs.digProficiency > smallAntAttrs.digProficiency,
    'Larger ant must have higher dig proficiency'
  );

  // Speed scales inversely with size (smaller is lighter and nimbler)
  assert(
    smallAntAttrs.speed >= largeAntAttrs.speed,
    'Smaller ant must be nimbler and have equal or higher speed'
  );

  // Check diversity among generated population
  for (let i = 0; i < 20; i++) {
    const ant = createAnt('CARRIER', 30, 25);
    sampleSizes.push(ant.size);
  }
  const minSize = Math.min(...sampleSizes);
  const maxSize = Math.max(...sampleSizes);
  assert(maxSize > minSize, 'Population must exhibit size diversity');

  console.log(`PASS — ATTRIBUTE_SCALING_VALIDATED (Size range: [${minSize.toFixed(2)}, ${maxSize.toFixed(2)}])\n`);

  // ---------------------------------------------------------------------------
  // TEST 4 — ROLLING ACTION HISTORY
  // ---------------------------------------------------------------------------
  console.log('TEST 4: Action History Logging (FIFO & Capped Buffer)...');
  const worker = createAnt('BUILDER', 35, 18);
  const initialHistoryLength = worker.recentActions.length;

  logAntAction(worker, 10, 'Acheminement de terreau', { x: 36, y: 18 });
  logAntAction(worker, 20, 'Renforcement de paroi sud', { x: 36, y: 19 });
  logAntAction(worker, 30, 'Pause au seuil de la chambre', { x: 35, y: 19 });

  assert(
    worker.recentActions.length === initialHistoryLength + 3,
    'Action history must record consecutive actions'
  );

  // Verify newest action is at the end of the history array
  assert(
    worker.recentActions[worker.recentActions.length - 1].action === 'Pause au seuil de la chambre',
    'Latest action must be correctly recorded'
  );

  // Verify buffer cap (max 8 entries)
  for (let i = 1; i <= 15; i++) {
    logAntAction(worker, 40 + i * 5, `Action test numéro ${i}`);
  }
  assert(worker.recentActions.length <= 8, `Action history must be capped at 8 entries (has ${worker.recentActions.length})`);

  console.log('PASS — ACTION_HISTORY_VALIDATED\n');

  // ---------------------------------------------------------------------------
  // TEST 5 — INSPECTION DATA COMPLETENESS
  // ---------------------------------------------------------------------------
  console.log('TEST 5: Inspection Data Format Completeness...');
  const inspectorAnt = createAnt('CARRIER', 42, 28);
  inspectorAnt.age = 240;
  inspectorAnt.carrying = { type: 'crystal', name: 'Éclat cyan', color: '#38bdf8' };
  inspectorAnt.currentDestination = { x: 56, y: 19 };

  const info = getAntInspectionData(inspectorAnt);

  assert(info.ant_id === inspectorAnt.ant_id, 'ant_id must match');
  assert(info.position.x === 42 && info.position.y === 28, 'Position must match');
  assert(typeof info.ageFormatted === 'string' && info.ageFormatted.length > 0, 'ageFormatted must exist');
  assert(typeof info.sizeCategory === 'string' && info.sizeCategory.length > 0, 'sizeCategory must exist');
  assert(info.destination !== null, 'Destination must exist');
  assert(info.destination?.x === 56 && info.destination?.y === 19, 'Destination coordinates must match');
  assert(info.load.item === 'Éclat cyan', 'Carried item name must match');
  assert(info.aptitudes.strength > 0, 'Strength aptitude must exist');
  assert(info.aptitudes.speed > 0, 'Speed aptitude must exist');
  assert(info.aptitudes.digProficiency > 0, 'Dig aptitude must exist');
  assert(info.aptitudes.carryCapacity > 0, 'Carry capacity must exist');
  assert(typeof info.stateLabel === 'string' && info.stateLabel.length > 0, 'State label must exist');
  assert(Array.isArray(info.recentActions), 'Recent actions must exist as array in inspection');

  console.log('PASS — INSPECTION_DATA_VALIDATED\n');

  // ---------------------------------------------------------------------------
  // TEST 6 — AUTONOMOUS DIG FRONT DESIGNATION BY THE QUEEN
  // ---------------------------------------------------------------------------
  console.log('TEST 6: Autonomous Dig Front Designation by the Queen...');

  // 1. Démarrer sans digTask manuel
  const testGrid = generateInitialGrid(3861);
  const queen = createAnt('QUEEN', 41, 20, 'Reine Séléné');
  const digTasks: DigTask[] = []; // No manual tasks
  let taskCounter = 1;

  const mockAddDigTask = (x: number, y: number): DigTask | null => {
    if (testGrid.tiles[y][x] === 'AIR' || testGrid.tiles[y][x] === 'SURFACE_AIR') return null;
    const task: DigTask = {
      id: `task_${taskCounter++}`,
      x,
      y,
      progress: 0,
    };
    digTasks.push(task);
    return task;
  };

  assert(digTasks.length === 0, 'Colony must start without any manual digTask');

  // 2. Laisser la Reine évaluer
  const createdTask = evaluateQueenDigOrders(queen, testGrid, digTasks, mockAddDigTask, 3);

  // 3. Vérifier qu’un digTask valide est créé automatiquement
  assertNotNull(createdTask, 'Queen must automatically create a valid digTask');
  assert(digTasks.length === 1, 'digTasks array must contain the newly created task');
  assert(typeof createdTask.id === 'string' && createdTask.id.length > 0, 'digTask must have a valid id');
  assert(typeof createdTask.x === 'number' && typeof createdTask.y === 'number', 'digTask coordinates must be numbers');
  assert(createdTask.progress === 0, 'digTask progress must start at 0');

  // 4. Vérifier qu’il se trouve sur un front accessible
  const accessibleFronts = getAccessibleDigFronts(testGrid);
  assert(accessibleFronts.length > 0, 'Burrow must contain accessible fronts');
  const isAccessible = accessibleFronts.some(
    (f) => f.x === createdTask.x && f.y === createdTask.y
  );
  assert(
    isAccessible,
    `Queen digTask at (${createdTask.x}, ${createdTask.y}) must be located on an accessible front`
  );

  // Vérifier que la cellule cible n'est pas encore excavée et est de la roche solide
  const targetCell = testGrid.cells[createdTask.y][createdTask.x];
  assert(!targetCell.excavated, 'Target cell of digTask must not be already excavated');
  assert(
    testGrid.tiles[createdTask.y][createdTask.x] !== 'AIR',
    'Target tile must not be AIR'
  );

  // 5. Test d'intégration avec ColonyEngine
  const engine = new ColonyEngine(3861);
  engine.clearDigTasks(); // Démarrer sans digTask manuel
  assert(engine.state.digTasks.length === 0, 'ColonyEngine must start without manual dig tasks');

  // Laisser la Reine évaluer dans le moteur
  const engineTask = engine.evaluateQueenDigOrders(3);
  assertNotNull(engineTask, 'ColonyEngine Queen evaluation must create a digTask');
  assert(engine.state.digTasks.length === 1, 'ColonyEngine must now hold 1 digTask');

  const engineAccessibleFronts = engine.getAccessibleDigFronts();
  const engineTaskIsAccessible = engineAccessibleFronts.some(
    (f) => f.x === engineTask.x && f.y === engineTask.y
  );
  assert(
    engineTaskIsAccessible,
    `ColonyEngine Queen digTask at (${engineTask.x}, ${engineTask.y}) must be on an accessible front`
  );

  // Si le nombre de digTasks atteint le seuil (ex: 3), la reine n'en ajoute plus inutilement
  engine.evaluateQueenDigOrders(3); // 2nd task
  engine.evaluateQueenDigOrders(3); // 3rd task
  assert(engine.state.digTasks.length === 3, 'ColonyEngine should now hold 3 active dig tasks');
  const fourthAttempt = engine.evaluateQueenDigOrders(3);
  assert(fourthAttempt === null, 'Queen must not create tasks when threshold is already satisfied');

  console.log(
    `PASS — QUEEN_DIG_DESIGNATION_VALIDATED (Queen automatically designated front at (${createdTask.x}, ${createdTask.y}))\n`
  );

  // ---------------------------------------------------------------------------
  // TEST 7 — ORGANIC & DISTRIBUTED SUCCESSIVE QUEEN DIG ORDERS
  // ---------------------------------------------------------------------------
  console.log('TEST 7: Organic & Distributed Successive Queen Dig Orders...');

  const multiEngine = new ColonyEngine(3861);
  multiEngine.clearDigTasks();
  assert(multiEngine.state.digTasks.length === 0, 'Must start with 0 tasks');

  // 1. Faire créer plusieurs digTasks successifs par la Reine
  const createdTasks: DigTask[] = [];
  const TOTAL_SUCCESSIVE_TASKS = 4;

  for (let i = 0; i < TOTAL_SUCCESSIVE_TASKS; i++) {
    const task = multiEngine.evaluateQueenDigOrders(TOTAL_SUCCESSIVE_TASKS);
    assertNotNull(task, `Queen must successfully create task #${i + 1}`);
    createdTasks.push(task);
  }

  assert(
    createdTasks.length === TOTAL_SUCCESSIVE_TASKS,
    `Queen must have created exactly ${TOTAL_SUCCESSIVE_TASKS} successive tasks`
  );

  // 2. Vérifier qu'ils sont tous accessibles
  const currentAccessibleFronts = multiEngine.getAccessibleDigFronts();
  for (let i = 0; i < createdTasks.length; i++) {
    const t = createdTasks[i];
    const isAccessible = currentAccessibleFronts.some((f) => f.x === t.x && f.y === t.y);
    assert(
      isAccessible,
      `Task #${i + 1} at (${t.x}, ${t.y}) must be located on an accessible front`
    );
  }

  // 3. Vérifier qu'ils ne sont pas tous au même endroit ni tous sur le même front
  // Coordonnées uniques
  const uniquePositions = new Set(createdTasks.map((t) => `${t.x},${t.y}`));
  assert(
    uniquePositions.size === createdTasks.length,
    `All ${createdTasks.length} tasks must have unique coordinates (got ${uniquePositions.size})`
  );

  // Distance entre chaque paire : pas de regroupement sur le même front immédiat
  for (let i = 0; i < createdTasks.length; i++) {
    for (let j = i + 1; j < createdTasks.length; j++) {
      const dist = Math.hypot(
        createdTasks[i].x - createdTasks[j].x,
        createdTasks[i].y - createdTasks[j].y
      );
      assert(
        dist >= 3.0,
        `Tasks #${i + 1} (${createdTasks[i].x}, ${createdTasks[i].y}) and #${j + 1} (${createdTasks[j].x}, ${createdTasks[j].y}) must not be clustered together (distance: ${dist.toFixed(2)} < 3.0)`
      );
    }
  }

  // Répartition entre types de fronts (approfondissement, horizontal, exploration)
  const frontTypes = createdTasks.map((t) => {
    const front = currentAccessibleFronts.find((f) => f.x === t.x && f.y === t.y);
    return front?.frontType || 'UNKNOWN';
  });
  const uniqueFrontTypes = new Set(frontTypes);
  assert(
    uniqueFrontTypes.size >= 2,
    `Tasks must be distributed across different front types (got: ${Array.from(uniqueFrontTypes).join(', ')})`
  );

  // 4. Vérifier qu'aucune salle désignée n'est touchée
  const allRooms = multiEngine.state.grid.rooms;
  for (let i = 0; i < createdTasks.length; i++) {
    const t = createdTasks[i];
    for (const room of allRooms) {
      const inRoom = room.tiles.some((rt) => rt.x === t.x && rt.y === t.y);
      assert(
        !inRoom,
        `Task #${i + 1} at (${t.x}, ${t.y}) must not touch designated room "${room.name}" (${room.type})`
      );
    }
  }

  // 5. Vérifier le déterminisme avec la world_seed
  const repeatEngine = new ColonyEngine(3861);
  repeatEngine.clearDigTasks();
  for (let i = 0; i < TOTAL_SUCCESSIVE_TASKS; i++) {
    const repeatTask = repeatEngine.evaluateQueenDigOrders(TOTAL_SUCCESSIVE_TASKS);
    assertNotNull(repeatTask, `Repeat engine must create task #${i + 1}`);
    assert(
      repeatTask.x === createdTasks[i].x && repeatTask.y === createdTasks[i].y,
      `Determinism check: task #${i + 1} mismatch (${repeatTask.x}, ${repeatTask.y}) vs (${createdTasks[i].x}, ${createdTasks[i].y})`
    );
  }

  console.log(
    `PASS — ORGANIC_DISTRIBUTED_QUEEN_DIG_ORDERS_VALIDATED (${createdTasks.length} distinct fronts, types: [${frontTypes.join(', ')}], 0 room violations, 100% deterministic)\n`
  );

  // ---------------------------------------------------------------------------
  // TEST 8 — AUTOMATED QUEEN ROOM DESIGNATION (AVAILABLE CAVITIES & COMMANDS)
  // ---------------------------------------------------------------------------
  console.log('TEST 8: Automated Queen Room Designation Pipeline...');

  const roomEngine = new ColonyEngine(3861);
  const initialRooms = [...roomEngine.state.grid.rooms];
  const initialRoomCount = initialRooms.length;

  // Vérifier que toutes les salles de départ sont reconnues comme désignées
  for (const r of initialRooms) {
    assert(isDesignatedRoom(r), `Initial room "${r.name}" (${r.type}) must be designated`);
  }

  // 1. Creuser une galerie et une nouvelle cavité organique rattachée aux galeries (x=41..50, y=28)
  roomEngine.digHorizontal(41, 50, 28);
  const carvedCount = roomEngine.digCavity(50, 28, 3, 2);
  assert(carvedCount >= 8, `New organic cavity must carve cells (got ${carvedCount})`);

  // 2. La Reine examine les cavités déjà creusées et disponibles
  const availableCavities = roomEngine.getAvailableCavities();
  assert(availableCavities.length >= 1, 'Newly carved cavity must be recognized as available');
  const targetCavity = availableCavities.find((c) =>
    c.tiles.some((t) => Math.hypot(t.x - 50, t.y - 28) <= 2)
  );
  assertNotNull(targetCavity, 'Carved cavity at (50, 28) must be in available cavities');
  assert(!isDesignatedRoom(targetCavity), 'Available cavity must not yet be designated');
  assert(targetCavity.type === 'NONE', 'Cavity initial type must be NONE');
  const originalCavityId = targetCavity.id;

  // 3. La Reine décide de la salle (décision locale / interface commande compatible JEV)
  const order = roomEngine.decideQueenRoomOrder();
  assertNotNull(order, 'Queen must decide an order for the available cavity');
  assert(
    availableCavities.some((c) => c.id === order.cavityId),
    `Order cavityId (${order.cavityId}) must belong to the list of available cavities`
  );
  assert(
    QUEEN_ALLOWED_ROOM_TYPES.includes(order.roomType),
    `Room type "${order.roomType}" must be one of the allowed types`
  );
  assert(typeof order.reason === 'string' && order.reason.length > 0, 'Order reason must be provided');

  // 4. Exécution de l'ordre par la Reine via le système actuel "Aménager salle"
  const designatedRoom = roomEngine.evaluateQueenRoomOrders();
  assertNotNull(designatedRoom, 'Queen must successfully furnish and designate the room');
  assert(isDesignatedRoom(designatedRoom), 'Designated room must now be isDesignated=true');
  assert(designatedRoom.type === order.roomType, `Designated room type must be ${order.roomType}`);
  assert(designatedRoom.room_function === order.roomType, `Designated room_function must be ${order.roomType}`);

  // 5. Conserver le room_id persistant
  assert(
    designatedRoom.id === order.cavityId,
    `Stable room_id must be preserved (expected ${order.cavityId}, got ${designatedRoom.id})`
  );
  for (const t of designatedRoom.tiles) {
    assert(
      roomEngine.state.grid.cells[t.y][t.x].room_id === designatedRoom.id,
      `Cell (${t.x},${t.y}) must link to stable room_id = ${designatedRoom.id}`
    );
  }

  // 5b. Test d'exécution de commande directe (format JEV) sur la cavité creusée si elle est encore disponible
  const remainingCavities = roomEngine.getAvailableCavities();
  const unassignedTarget = remainingCavities.find((c) => c.id === targetCavity.id);
  if (unassignedTarget) {
    const directOrder: QueenRoomOrder = {
      cavityId: unassignedTarget.id,
      centerX: unassignedTarget.center.x,
      centerY: unassignedTarget.center.y,
      roomType: 'WORKSHOP',
      reason: 'Ordre de commande directe type JEV',
    };
    const directResult = roomEngine.executeQueenRoomOrder(directOrder);
    assertNotNull(directResult, 'executeQueenRoomOrder must designate targeted cavity');
    assert(directResult.type === 'WORKSHOP', 'Direct order roomType must be WORKSHOP');
    assert(directResult.id === unassignedTarget.id, 'Direct order room_id must match cavity');
  }

  // 6. Ne jamais remplacer ou supprimer une salle existante
  for (const originalRoom of initialRooms) {
    const current = roomEngine.state.grid.rooms.find((r) => r.id === originalRoom.id);
    assertNotNull(current, `Original designated room "${originalRoom.name}" must not be removed`);
    assert(
      current.type === originalRoom.type,
      `Original room "${originalRoom.name}" type must not be modified`
    );
    assert(
      current.tiles.length === originalRoom.tiles.length,
      `Original room "${originalRoom.name}" tiles must not be altered`
    );
  }
  const addedRooms = 1 + (unassignedTarget ? 1 : 0);
  assert(
    roomEngine.state.grid.rooms.filter(isDesignatedRoom).length === initialRoomCount + addedRooms,
    `Designated room count must increase by exactly ${addedRooms}`
  );

  // 7. Rejet des zones solides ou non accessibles
  const solidOrder: QueenRoomOrder = {
    cavityId: 'invalid_solid',
    centerX: 10,
    centerY: 55,
    roomType: 'STORAGE',
    reason: 'Tentative d’aménager de la roche solide',
  };
  const solidResult = roomEngine.executeQueenRoomOrder(solidOrder);
  assert(solidResult === null, 'executeQueenRoomOrder must reject solid unexcavated rock');

  // 8. Rejet du remplacement forcé d'une salle déjà désignée
  const overwriteOrder: QueenRoomOrder = {
    cavityId: 'illegal_overwrite',
    centerX: 41,
    centerY: 20, // Inside Queen chamber
    roomType: 'WORKSHOP',
    reason: 'Tentative illégale d’écraser la chambre royale',
  };
  const overwriteResult = roomEngine.executeQueenRoomOrder(overwriteOrder);
  assert(overwriteResult === null, 'executeQueenRoomOrder must refuse to replace an existing designated room');

  console.log(
    `PASS — QUEEN_ROOM_DESIGNATION_VALIDATED (Cavity "${originalCavityId}" designated as "${designatedRoom.name}" [${designatedRoom.type}], 0 room removals, solid rock rejected)\n`
  );

  console.log('================================================================');
  console.log('ALL 8 AGENT SUITE TESTS PASSED SUCCESSFULLY!');
  console.log('================================================================');
}

runAntAgentTests();
