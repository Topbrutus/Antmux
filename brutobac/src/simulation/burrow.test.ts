/**
 * Automated Test Suite — BLOC 2: CREUSAGE ET ARCHITECTURE DU TERRIER
 * Validates organic burrow creation, automatic cavity recognition,
 * chamber expansion, entrance tracking, chamber merger,
 * tunnel topology classification (horizontal/vertical/cul-de-sac/bifurcation/intersection),
 * and accessible dig frontlines.
 */

import { generateInitialGrid, saveTerrain, loadTerrain } from './grid';
import { ColonyRoom } from '../types/colony';
import {
  updateBurrowChambers,
  getAccessibleDigFronts,
  classifyBurrowTopology,
  digHorizontalTunnel,
  digVerticalShaft,
  digOrganicCavity,
  isDesignatedRoom,
  inBounds,
} from './burrowArchitecture';

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

function runBurrowArchitectureTests() {
  console.log('================================================================');
  console.log('RUNNING BURROW SUITE — BLOC 2: ARCHITECTURE & CREUSAGE');
  console.log('================================================================\n');

  // ---------------------------------------------------------------------------
  // TEST 1 — AUTOMATIC CAVITY RECOGNITION & STABLE ROOM_ID
  // ---------------------------------------------------------------------------
  console.log('TEST 1: Automatic Cavity Recognition & Stable Room ID...');
  const grid = generateInitialGrid(3861);
  const initialRoomCount = grid.rooms.length;

  // Carve a new cavity in virgin rock (x=60, y=45)
  const dug = digOrganicCavity(grid, 60, 45, 3, 2, 50);
  assert(dug >= 8, `Cavity should excavate multiple cells (dug ${dug})`);

  // Verify that an organic room was recognized
  assert(grid.rooms.length > initialRoomCount, 'New organic room should be recognized');
  const recognizedRoom = grid.rooms.find((r) =>
    r.tiles.some((t) => Math.hypot(t.x - 60, t.y - 45) <= 1.5)
  );

  assertNotNull(recognizedRoom, 'Recognized room must exist around center');
  assert(recognizedRoom.room_function === 'NONE', 'Room function must be NONE');
  assert(recognizedRoom.type === 'NONE', 'Room type must be NONE');
  assert(recognizedRoom.id.length > 0, 'Room must have a valid stable ID');
  const savedRoomId = recognizedRoom.id;

  console.log(`PASS — CAVITY_RECOGNIZED (room_id: ${savedRoomId}, tiles: ${recognizedRoom.tiles.length})\n`);

  // ---------------------------------------------------------------------------
  // TEST 2 — CHAMBER EXPANSION & NEW ENTRANCES
  // ---------------------------------------------------------------------------
  console.log('TEST 2: Chamber Expansion & Entrance Detection...');
  const initialTilesCount = recognizedRoom.tiles.length;

  // Enlarge the cavity by digging adjacent tiles
  digOrganicCavity(grid, 62, 45, 3, 2, 60);

  // The room should have expanded
  const expandedRoom = grid.rooms.find((r) => r.id === savedRoomId);
  assertNotNull(expandedRoom, 'Room must preserve its stable room_id during expansion');
  assert(expandedRoom.id === savedRoomId, 'Stable room_id must be strictly preserved');
  assert(expandedRoom.tiles.length > initialTilesCount, 'Room tiles must increase after expansion');

  // Dig a connecting tunnel into the chamber from a distance to create a new entrance
  digHorizontalTunnel(grid, 50, 58, 45, 70);
  updateBurrowChambers(grid, 70);

  const roomWithEntrance = grid.rooms.find((r) => r.id === savedRoomId);
  assertNotNull(roomWithEntrance, 'Room must exist');
  assertNotNull(roomWithEntrance.entrances, 'Entrances array must exist');
  assert(roomWithEntrance.entrances.length > 0, 'Room must detect its tunnel entrances');

  console.log(`PASS — CHAMBER_EXPANDED (stable ID maintained: ${savedRoomId}, entrances: ${roomWithEntrance.entrances.length})\n`);

  // ---------------------------------------------------------------------------
  // TEST 3 — CHAMBER MERGER
  // ---------------------------------------------------------------------------
  console.log('TEST 3: Chamber Merger...');
  // Create two separate cavities in solid ground (e.g. depth 75)
  digOrganicCavity(grid, 20, 75, 2, 2, 80);
  digOrganicCavity(grid, 32, 75, 2, 2, 80);

  const roomA = grid.rooms.find((r) => r.tiles.some((t) => t.x === 20 && t.y === 75));
  const roomB = grid.rooms.find((r) => r.tiles.some((t) => t.x === 32 && t.y === 75));

  assertNotNull(roomA, 'Room A must exist');
  assertNotNull(roomB, 'Room B must exist');
  assert(roomA.id !== roomB.id, 'Rooms A and B must initially have distinct IDs');

  const idA = roomA.id;
  const idB = roomB.id;
  const combinedTilesCount = roomA.tiles.length + roomB.tiles.length;

  // Now dig a wide connecting gallery between the two cavities
  digHorizontalTunnel(grid, 22, 30, 75, 90);
  digHorizontalTunnel(grid, 22, 30, 76, 90);
  updateBurrowChambers(grid, 90);

  // Check that the two rooms have merged
  const remainingRooms = grid.rooms.filter((r) => r.id === idA || r.id === idB);
  assert(remainingRooms.length === 1, `Rooms must merge into exactly 1 chamber (found ${remainingRooms.length})`);

  const mergedRoom = remainingRooms[0];
  assert(
    mergedRoom.tiles.length >= combinedTilesCount,
    'Merged room must contain all combined tiles plus connecting excavation'
  );

  console.log(`PASS — CHAMBERS_MERGED (Merged into single stable ID: ${mergedRoom.id})\n`);

  // ---------------------------------------------------------------------------
  // TEST 4 — TUNNEL TOPOLOGY CLASSIFICATION
  // ---------------------------------------------------------------------------
  console.log('TEST 4: Tunnel Topology Classification...');
  // Create an isolated tunnel network with distinct structural features at y=95
  // Horizontal tunnel
  digHorizontalTunnel(grid, 10, 20, 95, 100);
  // Vertical shaft
  digVerticalShaft(grid, 15, 92, 98, 1, 100);

  const topology = classifyBurrowTopology(grid);

  // In this cross shape:
  // (15, 95) has 4 walkable neighbors -> INTERSECTION
  const intersectionNode = topology.find((n) => n.x === 15 && n.y === 95);
  assertNotNull(intersectionNode, 'Node at (15, 95) must exist');
  assert(intersectionNode.type === 'INTERSECTION', `Node at (15, 95) should be INTERSECTION, got ${intersectionNode.type}`);

  // (10, 95) has 1 neighbor -> CUL_DE_SAC
  const culDeSacNode = topology.find((n) => n.x === 10 && n.y === 95);
  assertNotNull(culDeSacNode, 'Node at (10, 95) must exist');
  assert(culDeSacNode.type === 'CUL_DE_SAC', `Node at (10, 95) should be CUL_DE_SAC, got ${culDeSacNode.type}`);

  // (12, 95) has left & right neighbors -> HORIZONTAL_TUNNEL
  const horizNode = topology.find((n) => n.x === 12 && n.y === 95);
  assertNotNull(horizNode, 'Node at (12, 95) must exist');
  assert(horizNode.type === 'HORIZONTAL_TUNNEL', `Node at (12, 95) should be HORIZONTAL_TUNNEL, got ${horizNode.type}`);

  // (15, 93) has up & down neighbors -> VERTICAL_SHAFT
  const vertNode = topology.find((n) => n.x === 15 && n.y === 93);
  assertNotNull(vertNode, 'Node at (15, 93) must exist');
  assert(vertNode.type === 'VERTICAL_SHAFT', `Node at (15, 93) should be VERTICAL_SHAFT, got ${vertNode.type}`);

  // Now create a 3-way T-junction (BIFURCATION) at (18, 95) branching down to (18, 96)
  grid.cells[96][18].excavated = true;
  grid.cells[96][18].hardness = 0;
  grid.tiles[96][18] = 'AIR';

  const updatedTopology = classifyBurrowTopology(grid);
  const bifurcationNode = updatedTopology.find((n) => n.x === 18 && n.y === 95);
  assertNotNull(bifurcationNode, 'Node at (18, 95) must exist');
  assert(bifurcationNode.type === 'BIFURCATION', `Node at (18, 95) should be BIFURCATION, got ${bifurcationNode.type}`);

  console.log('PASS — TOPOLOGY_CLASSIFIED (cul-de-sac, shaft, horiz, bifurcation, intersection validated)\n');

  // ---------------------------------------------------------------------------
  // TEST 5 — ACCESSIBLE DIG FRONTS
  // ---------------------------------------------------------------------------
  console.log('TEST 5: Accessible Dig Frontlines Detection...');
  const fronts = getAccessibleDigFronts(grid);

  assert(fronts.length > 0, 'There should be accessible dig fronts');

  // Verify that all fronts are solid (unexcavated) cells
  for (const f of fronts) {
    const c = grid.cells[f.y][f.x];
    assert(!c.excavated, `Front at (${f.x}, ${f.y}) must be unexcavated`);
    assert(f.adjacentExcavated.length > 0, `Front at (${f.x}, ${f.y}) must have adjacent excavated cells`);
  }

  // Deep solid cell away from any tunnels (e.g. x=2, y=120) must NOT be a front
  const isDeepFront = fronts.some((f) => f.x === 2 && f.y === 120);
  assert(!isDeepFront, 'Deep isolated cell must NOT be an accessible front');

  // Pick an accessible front, excavate it, and verify frontline updates
  const testFront = fronts[0];
  grid.cells[testFront.y][testFront.x].excavated = true;
  grid.cells[testFront.y][testFront.x].hardness = 0;
  grid.tiles[testFront.y][testFront.x] = 'AIR';

  const newFronts = getAccessibleDigFronts(grid);
  // The newly excavated tile must no longer be in fronts
  const stillFront = newFronts.some((f) => f.x === testFront.x && f.y === testFront.y);
  assert(!stillFront, 'Excavated tile must no longer be a frontline');

  console.log(`PASS — ACCESSIBLE_FRONTS_VALIDATED (${fronts.length} accessible fronts identified)\n`);

  // ---------------------------------------------------------------------------
  // TEST 6 — DESIGNATED ROOM PERSISTENCE & DIGGING NON-DESTRUCTION
  // RÈGLE : CREUSER ≠ EFFACER UNE SALLE
  // ---------------------------------------------------------------------------
  console.log('TEST 6: Designated Room Persistence (CREUSER ≠ EFFACER UNE SALLE)...');

  // Verify starter rooms exist and have stable room_id on their cells
  const queenRoom = grid.rooms.find((r) => r.type === 'QUEEN');
  assertNotNull(queenRoom, 'Queen room must exist');
  assert(queenRoom.id.length > 0, 'Queen room must have stable id');
  assert(isDesignatedRoom(queenRoom), 'Queen room must be recognized as designated');
  for (const t of queenRoom.tiles) {
    assert(grid.cells[t.y][t.x].room_id === queenRoom.id, `Cell (${t.x},${t.y}) must link to queen room id`);
  }

  // 1. Excavate and design a specialized room (e.g. Réserve de cristaux at depth 55)
  const roomOriginX = 35;
  const roomOriginY = 55;
  const roomW = 4;
  const roomH = 3;
  const designatedTiles: Array<{ x: number; y: number }> = [];

  for (let dy = 0; dy < roomH; dy++) {
    for (let dx = 0; dx < roomW; dx++) {
      const cx = roomOriginX + dx;
      const cy = roomOriginY + dy;
      grid.cells[cy][cx].excavated = true;
      grid.cells[cy][cx].hardness = 0;
      grid.tiles[cy][cx] = 'AIR';
      designatedTiles.push({ x: cx, y: cy });
    }
  }

  const customRoomId = 'room_crystal_vault_35_55';
  const customRoomType = 'CRYSTAL_VAULT';
  const designatedRoom: ColonyRoom = {
    id: customRoomId,
    type: customRoomType,
    room_function: customRoomType,
    isDesignated: true,
    name: 'Réserve Cristaux Alpha',
    color: '#06b6d4',
    tiles: [...designatedTiles],
    bounds: {
      minX: roomOriginX,
      maxX: roomOriginX + roomW - 1,
      minY: roomOriginY,
      maxY: roomOriginY + roomH - 1,
    },
    center: {
      x: Math.round((roomOriginX * 2 + roomW - 1) / 2),
      y: Math.round((roomOriginY * 2 + roomH - 1) / 2),
    },
    level: 1,
    storedResources: { crystal: 42, dirt: 15, mineral: 8, resin: 6 },
    capacity: designatedTiles.length * 5,
    createdAtTick: 100,
  };

  // Bind cell.room_id to stable customRoomId
  for (const t of designatedTiles) {
    grid.cells[t.y][t.x].room_id = customRoomId;
  }
  grid.rooms.push(designatedRoom);

  // 2. Creuser des cellules adjacentes juste à côté de la salle
  // Dig an adjacent tunnel / cavity right along the eastern wall of the room (x = 39, y = 55..57)
  const adjacentDigCoords = [
    { x: 39, y: 55 },
    { x: 39, y: 56 },
    { x: 39, y: 57 },
    { x: 40, y: 55 },
    { x: 40, y: 56 },
    { x: 40, y: 57 },
    { x: 41, y: 56 },
  ];

  for (const coord of adjacentDigCoords) {
    grid.cells[coord.y][coord.x].excavated = true;
    grid.cells[coord.y][coord.x].hardness = 0;
    grid.tiles[coord.y][coord.x] = 'AIR';
    // Newly dug cell is unassigned (no room_id)
    grid.cells[coord.y][coord.x].room_id = null;
  }

  // 3. Recalculer l'architecture du terrier (updateBurrowChambers)
  updateBurrowChambers(grid, 110);

  // 4. Vérifier que la salle existe toujours avec le même room_id, le même type et les mêmes ressources
  const verifiedRoom = grid.rooms.find((r) => r.id === customRoomId);
  assertNotNull(verifiedRoom, 'Designated room must still exist after adjacent excavation');
  assert(verifiedRoom.id === customRoomId, `room_id must be strictly preserved (expected ${customRoomId}, got ${verifiedRoom.id})`);
  assert(verifiedRoom.type === customRoomType, `room type must be preserved (expected ${customRoomType}, got ${verifiedRoom.type})`);
  assert(verifiedRoom.storedResources.crystal === 42, 'Stored crystals must remain 42');
  assert(verifiedRoom.storedResources.dirt === 15, 'Stored dirt must remain 15');
  assert(verifiedRoom.tiles.length === designatedTiles.length, `Room must NOT automatically absorb newly dug adjacent cells (expected ${designatedTiles.length}, got ${verifiedRoom.tiles.length})`);

  // Verify that all original cells still maintain their room_id link
  for (const t of verifiedRoom.tiles) {
    assert(grid.cells[t.y][t.x].room_id === customRoomId, `Cell (${t.x},${t.y}) must keep its room_id = ${customRoomId}`);
  }

  // Verify that newly dug adjacent cells were NOT given the room_id
  for (const coord of adjacentDigCoords) {
    assert(
      grid.cells[coord.y][coord.x].room_id !== customRoomId,
      `Newly dug cell (${coord.x},${coord.y}) must NOT be linked to room ${customRoomId}`
    );
  }

  // 5. Test Save & Load roundtrip of room_id, type, cells, and resources
  const savedState = saveTerrain(grid, 120);
  const reloadedGrid = loadTerrain(savedState);

  const reloadedRoom = reloadedGrid.rooms.find((r) => r.id === customRoomId);
  assertNotNull(reloadedRoom, 'Reloaded world must contain the designated room');
  assert(reloadedRoom.id === customRoomId, 'Reloaded room_id must match');
  assert(reloadedRoom.type === customRoomType, 'Reloaded room type must match');
  assert(reloadedRoom.storedResources.crystal === 42, 'Reloaded crystal resources must match');
  assert(reloadedRoom.tiles.length === designatedTiles.length, 'Reloaded tiles count must match');

  for (const t of reloadedRoom.tiles) {
    assert(
      reloadedGrid.cells[t.y][t.x].room_id === customRoomId,
      `Reloaded cell (${t.x},${t.y}) must maintain room_id = ${customRoomId}`
    );
  }

  console.log(`PASS — ROOM_PERSISTENCE_VALIDATED (room_id: ${customRoomId}, type: ${customRoomType}, CREUSER ≠ EFFACER UNE SALLE)\n`);

  console.log('================================================================');
  console.log('ALL 6 BURROW ARCHITECTURE TESTS PASSED SUCCESSFULLY!');
  console.log('================================================================');
}

runBurrowArchitectureTests();
