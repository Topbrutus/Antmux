/**
 * Automated Test Suite — BLOC 1: TERRAIN SOUTERRAIN PERSISTANT ET DÉTERMINISTE
 * Validates deterministic world generation, continuous depth, cell persistence,
 * excavation mechanics, and resource conservation.
 */

import {
  generateInitialGrid,
  saveTerrain,
  loadTerrain,
  excavateCell,
  isCellWalkable,
  getCell,
  setCell,
  clearSparseBlocks3D,
  createBlock3D,
  GRID_WIDTH,
  GRID_HEIGHT,
} from './grid';
import { TerrainCell, TerrainBlock3D } from '../types/terrain';

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

function runAllTerrainTests() {
  console.log('================================================================');
  console.log('RUNNING TERRAIN SUITE — BLOC 1: PERSISTANT & DÉTERMINISTE');
  console.log('================================================================\n');

  // ---------------------------------------------------------------------------
  // TEST 1 — DÉTERMINISME
  // ---------------------------------------------------------------------------
  console.log('TEST 1: Verification of deterministic generation with seed = 3861...');
  const worldA = generateInitialGrid(3861);
  const worldB = generateInitialGrid(3861);

  assert(worldA.cells.length === GRID_HEIGHT, 'World A height mismatch');
  assert(worldB.cells.length === GRID_HEIGHT, 'World B height mismatch');

  let identicalCells = 0;
  for (let y = 0; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      const ca: TerrainCell = worldA.cells[y][x];
      const cb: TerrainCell = worldB.cells[y][x];

      assert(ca.cell_id === cb.cell_id, `Cell ID mismatch at (${x}, ${y})`);
      assert(ca.x === cb.x && ca.y === cb.y, `Coordinates mismatch at (${x}, ${y})`);
      assert(ca.depth === cb.depth, `Depth mismatch at (${x}, ${y})`);
      assert(ca.material_type === cb.material_type, `Material mismatch at (${x}, ${y})`);
      assert(ca.hardness === cb.hardness, `Hardness mismatch at (${x}, ${y})`);
      assert(ca.humidity === cb.humidity, `Humidity mismatch at (${x}, ${y})`);
      assert(ca.temperature === cb.temperature, `Temperature mismatch at (${x}, ${y})`);
      assert(ca.stability === cb.stability, `Stability mismatch at (${x}, ${y})`);
      assert(ca.excavated === cb.excavated, `Excavated flag mismatch at (${x}, ${y})`);
      assert(ca.discovered === cb.discovered, `Discovered flag mismatch at (${x}, ${y})`);
      assert(ca.resource_type === cb.resource_type, `Resource type mismatch at (${x}, ${y})`);
      assert(ca.resource_amount === cb.resource_amount, `Resource amount mismatch at (${x}, ${y})`);
      assert(ca.modified_at_tick === cb.modified_at_tick, `Modified tick mismatch at (${x}, ${y})`);
      assert(worldA.tiles[y][x] === worldB.tiles[y][x], `TileType mismatch at (${x}, ${y})`);

      identicalCells++;
    }
  }

  assert(identicalCells === GRID_WIDTH * GRID_HEIGHT, 'Not all cells were identical');
  console.log(`Verified ${identicalCells} cells identical.`);
  console.log('PASS — IDENTICAL_WORLD\n');

  // ---------------------------------------------------------------------------
  // TEST 2 — SEEDS DIFFÉRENTES
  // ---------------------------------------------------------------------------
  console.log('TEST 2: Verification of alternative seeds (3861 vs 5764801)...');
  const worldSeed1 = generateInitialGrid(3861);
  const worldSeed2 = generateInitialGrid(5764801);

  assert(worldSeed1.worldSeed === 3861, 'World 1 seed mismatch');
  assert(worldSeed2.worldSeed === 5764801, 'World 2 seed mismatch');

  let differencesFound = 0;
  for (let y = 8; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      if (
        worldSeed1.cells[y][x].material_type !== worldSeed2.cells[y][x].material_type ||
        worldSeed1.cells[y][x].hardness !== worldSeed2.cells[y][x].hardness
      ) {
        differencesFound++;
      }
    }
  }

  assert(differencesFound > 0, 'Different seeds should produce different geological features');
  console.log(`Accepted both seeds cleanly (${differencesFound} distinct geological variances).`);
  console.log('PASS — MULTIPLE_SEEDS_SUPPORTED\n');

  // ---------------------------------------------------------------------------
  // TEST 3 — SAVE / LOAD
  // ---------------------------------------------------------------------------
  console.log('TEST 3: Verification of Save / Load roundtrip...');
  const baseWorld = generateInitialGrid(3861);

  // Excavate a sequence of cells across depths
  const testCoords = [
    { x: 30, y: 15 },
    { x: 45, y: 32 },
    { x: 50, y: 70 },
    { x: 60, y: 110 },
  ];

  testCoords.forEach(({ x, y }, idx) => {
    excavateCell(baseWorld, x, y, 100 + idx * 50);
  });

  const savedData = saveTerrain(baseWorld, 1250);
  assert(savedData.schema_version === 'BRUTOBAC-TERRAIN-v1', 'Schema version mismatch');
  assert(savedData.mode === 'SIMULATION', 'Simulation mode mismatch');
  assert(savedData.world_seed === 3861, 'Seed mismatch in save');
  assert(savedData.tick === 1250, 'Tick mismatch in save');

  const reloadedWorld = loadTerrain(savedData);

  for (let y = 0; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      const orig = baseWorld.cells[y][x];
      const copy = reloadedWorld.cells[y][x];

      assert(orig.cell_id === copy.cell_id, `Roundtrip ID mismatch at (${x}, ${y})`);
      assert(orig.excavated === copy.excavated, `Roundtrip excavated mismatch at (${x}, ${y})`);
      assert(orig.discovered === copy.discovered, `Roundtrip discovered mismatch at (${x}, ${y})`);
      assert(orig.hardness === copy.hardness, `Roundtrip hardness mismatch at (${x}, ${y})`);
      assert(orig.material_type === copy.material_type, `Roundtrip material mismatch at (${x}, ${y})`);
      assert(orig.resource_type === copy.resource_type, `Roundtrip resource_type mismatch at (${x}, ${y})`);
      assert(orig.resource_amount === copy.resource_amount, `Roundtrip resource_amount mismatch at (${x}, ${y})`);
      assert(orig.modified_at_tick === copy.modified_at_tick, `Roundtrip tick mismatch at (${x}, ${y})`);
      assert(orig.temperature === copy.temperature, `Roundtrip temp mismatch at (${x}, ${y})`);
      assert(orig.humidity === copy.humidity, `Roundtrip humidity mismatch at (${x}, ${y})`);
      assert(orig.stability === copy.stability, `Roundtrip stability mismatch at (${x}, ${y})`);
      assert(baseWorld.tiles[y][x] === reloadedWorld.tiles[y][x], `Roundtrip tile mismatch at (${x}, ${y})`);
    }
  }

  console.log('PASS — TERRAIN_ROUNDTRIP_EXACT\n');

  // ---------------------------------------------------------------------------
  // TEST 4 — CREUSAGE
  // ---------------------------------------------------------------------------
  console.log('TEST 4: Verification of cell excavation, walkability & persistence...');
  const digWorld = generateInitialGrid(3861);
  const targetX = 35;
  const targetY = 25;

  const targetCell = digWorld.cells[targetY][targetX];
  assert(targetCell.hardness > 0, 'Cell should have initial hardness');
  assert(targetCell.excavated === false, 'Cell should not be excavated initially');
  assert(isCellWalkable(targetCell) === false, 'Solid cell should not be walkable');

  const digResult = excavateCell(digWorld, targetX, targetY, 320);
  assert(digResult !== null, 'Excavation should succeed');
  assert(targetCell.excavated === true, 'Cell should now be excavated');
  assert(targetCell.hardness === 0, 'Hardness should be 0 after excavation');
  assert(isCellWalkable(targetCell) === true, 'Excavated cell must be walkable');
  assert(digWorld.tiles[targetY][targetX] === 'AIR', 'Tile should be AIR');

  // Verify neighbors got discovered
  assert(digWorld.cells[targetY][targetX + 1].discovered === true, 'Neighbor should be revealed');

  // Save and reload
  const digSave = saveTerrain(digWorld, 320);
  const digReloaded = loadTerrain(digSave);
  const reloadedCell = digReloaded.cells[targetY][targetX];

  assert(reloadedCell.excavated === true, 'Excavated status must persist after load');
  assert(reloadedCell.hardness === 0, 'Zero hardness must persist after load');
  assert(isCellWalkable(reloadedCell) === true, 'Cell must remain walkable after load');
  assert(reloadedCell.modified_at_tick === 320, 'Modified tick must persist after load');

  console.log('PASS — DIG_STATE_PERSISTED\n');

  // ---------------------------------------------------------------------------
  // TEST 5 — RESSOURCE
  // ---------------------------------------------------------------------------
  console.log('TEST 5: Verification of resource preservation & revelation...');
  const resWorld = generateInitialGrid(3861);

  // Locate an unexcavated cell with a resource
  let resX = -1;
  let resY = -1;
  for (let y = 10; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      const c = resWorld.cells[y][x];
      if (!c.excavated && c.resource_type !== null && c.resource_amount > 0) {
        resX = x;
        resY = y;
        break;
      }
    }
    if (resX !== -1) break;
  }

  assert(resX !== -1, 'Should find at least one cell containing a resource');
  const sourceCell = resWorld.cells[resY][resX];
  const expectedResType = sourceCell.resource_type;
  const expectedResAmount = sourceCell.resource_amount;

  // Reveal by excavation
  const resExcavation = excavateCell(resWorld, resX, resY, 450);
  assertNotNull(resExcavation, 'Resource excavation should succeed');
  assertNotNull(resExcavation.revealedResource, 'Resource should be revealed upon excavation');
  assert(resExcavation.revealedResource.type === expectedResType, 'Revealed type must match');
  assert(resExcavation.revealedResource.count === expectedResAmount, 'Revealed amount must match');

  // Save and reload
  const resSave = saveTerrain(resWorld, 450);
  const resReloaded = loadTerrain(resSave);
  const reloadedResCell = resReloaded.cells[resY][resX];

  assert(reloadedResCell.resource_type === expectedResType, 'Resource type must be preserved after load');
  assert(reloadedResCell.excavated === true, 'Excavated state must be preserved');
  assert(reloadedResCell.modified_at_tick === 450, 'Tick must be preserved');

  console.log('PASS — RESOURCE_STATE_PERSISTED\n');

  // ---------------------------------------------------------------------------
  // TEST 6 — DISTRIBUTION 5 × 5 × 5 ET CONSERVATION DE MATIÈRE
  // ---------------------------------------------------------------------------
  console.log('TEST 6: Verification of 5x5x5 micro-cells, natural concentrations & matter conservation...');
  const matterWorld = generateInitialGrid(3861);
  const matterWorldCopy = generateInitialGrid(3861);

  let verified5x5x5Cells = 0;
  const concentrationsFound = new Set<string>();

  for (let y = 8; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      const c = matterWorld.cells[y][x];
      const copy = matterWorldCopy.cells[y][x];

      // Exact deterministic distribution match
      assert(c.crystal_dust_amount === copy.crystal_dust_amount, `Dust mismatch at (${x}, ${y})`);
      assert(c.crystal_amount === copy.crystal_amount, `Crystal mismatch at (${x}, ${y})`);
      assert(c.mineral_amount === copy.mineral_amount, `Mineral mismatch at (${x}, ${y})`);
      assert(c.dirt_amount === copy.dirt_amount, `Dirt mismatch at (${x}, ${y})`);
      assert(c.resin_amount === copy.resin_amount, `Resin mismatch at (${x}, ${y})`);
      assert(c.concentration_type === copy.concentration_type, `Concentration type mismatch at (${x}, ${y})`);

      if (c.concentration_type) {
        concentrationsFound.add(c.concentration_type);
      }

      // Check 5x5x5 micro-cells structure
      assertNotNull(c.micro_cells, `Micro-cells must exist at (${x}, ${y})`);
      assert(c.micro_cells.length === 125, `Each cell must contain exactly 125 micro-cells (5x5x5)`);

      // Verify matter conservation inside solid cell (hidden before excavation)
      let sumDust = 0;
      let sumCrystal = 0;
      let sumMineral = 0;
      let sumDirt = 0;
      let sumResin = 0;

      for (const mc of c.micro_cells) {
        sumDust += mc.crystal_dust_amount;
        sumCrystal += mc.crystal_amount;
        sumMineral += mc.mineral_amount;
        sumDirt += mc.dirt_amount;
        sumResin += mc.resin_amount;
        if (!c.excavated) {
          assert(mc.excavated === false, 'Solid cell must have unexcavated micro-cells (hidden content)');
        }
      }

      assert(sumDust === c.crystal_dust_amount, `Dust sum mismatch in micro-cells at (${x}, ${y})`);
      assert(sumCrystal === c.crystal_amount, `Crystal sum mismatch in micro-cells at (${x}, ${y})`);
      assert(sumMineral === c.mineral_amount, `Mineral sum mismatch in micro-cells at (${x}, ${y})`);
      assert(sumDirt === c.dirt_amount, `Dirt sum mismatch in micro-cells at (${x}, ${y})`);
      assert(sumResin === c.resin_amount, `Resin sum mismatch in micro-cells at (${x}, ${y})`);

      verified5x5x5Cells++;
    }
  }

  // Verify that natural concentrations exist across the terrain
  assert(concentrationsFound.has('rare_geode'), 'Terrain must contain rare geodes');
  assert(concentrationsFound.has('rich_zone'), 'Terrain must contain rich zones');
  assert(concentrationsFound.has('vein'), 'Terrain must contain veins');
  assert(concentrationsFound.has('cluster'), 'Terrain must contain clusters');
  assert(concentrationsFound.has('small_pocket'), 'Terrain must contain small pockets');
  assert(concentrationsFound.has('isolated_crystal'), 'Terrain must contain isolated crystals');

  // Verify matter liberation upon excavation
  const targetSolidX = 22;
  const targetSolidY = 112; // In rare geode
  const geodeCell = matterWorld.cells[targetSolidY][targetSolidX];
  const initialDust = geodeCell.crystal_dust_amount;
  const initialCrystal = geodeCell.crystal_amount;
  assert(initialDust > 0, 'Rare geode must have crystal dust');
  assert(initialCrystal > 0, 'Rare geode must have crystals');

  const geodeExcavation = excavateCell(matterWorld, targetSolidX, targetSolidY, 600);
  assertNotNull(geodeExcavation, 'Excavation should succeed');
  assertNotNull(geodeExcavation.liberatedMatter, 'Liberated matter must be returned');
  assert(geodeExcavation.liberatedMatter.crystalDust === initialDust, 'All crystal dust must be liberated');
  assert(geodeExcavation.liberatedMatter.crystal === initialCrystal, 'All crystals must be liberated');
  assert(geodeCell.excavated_micro_cells === 125, 'All 125 micro-cells must now be excavated');
  assert(geodeCell.micro_cells!.every((mc) => mc.excavated === true), 'All micro-cells must be marked excavated');

  console.log(`Verified ${verified5x5x5Cells} cells with 5x5x5 micro-cells (125 voxels each).`);
  console.log(`Natural concentrations confirmed: ${Array.from(concentrationsFound).join(', ')}.`);
  console.log('PASS — 5X5X5_MATTER_CONSERVATION_VERIFIED\n');

  // ---------------------------------------------------------------------------
  // TEST 7 — VRAI BLOC VOLUMÉTRIQUE 3D DE TERRAIN (Topbrutus/hole)
  // ---------------------------------------------------------------------------
  console.log('TEST 7: Verification of real volumetric 3D terrain blocks and getCell(x, y, z)...');

  // A. Standalone query without pre-constructing 84 × 84 × 124 in RAM
  const standaloneBlock = getCell(25, 40, 2);
  assertNotNull(standaloneBlock, 'getCell(25, 40, 2) should return a valid TerrainBlock3D');
  assert(standaloneBlock.x === 25, 'Block X coordinate mismatch');
  assert(standaloneBlock.y === 40, 'Block Y coordinate mismatch');
  assert(standaloneBlock.z === 2, 'Block Z coordinate mismatch');
  assert(typeof standaloneBlock.material_type === 'string', 'material_type must be a valid string');
  assert(typeof standaloneBlock.solid === 'boolean', 'solid must be a boolean');
  assert(standaloneBlock.state === 'solid' || standaloneBlock.state === 'air', 'state must be solid or air');
  assert(typeof standaloneBlock.hardness === 'number', 'hardness must be a number');
  assert(typeof standaloneBlock.excavated === 'boolean', 'excavated must be a boolean');
  assert('resource_type' in standaloneBlock, 'resource_type field must exist');
  assert(typeof standaloneBlock.resource_amount === 'number', 'resource_amount must be a number');
  assert('room_id' in standaloneBlock, 'room_id field must exist');
  assert(typeof standaloneBlock.modified_at_tick === 'number', 'modified_at_tick must be a number');

  // Solid block properties
  assert(standaloneBlock.solid === true, 'Subterranean rock block should be solid');
  assert(standaloneBlock.state === 'solid', 'State should be solid');
  assert(standaloneBlock.hardness > 0, 'Solid block should have non-zero hardness');
  assert(standaloneBlock.excavated === false, 'Unexcavated block should have excavated = false');

  // B. Querying world context at various depths (z = 0, 1, 2, 4)
  const world3D = generateInitialGrid(3861);

  // Surface sky block (y < 7)
  const skyBlock = getCell(42, 2, 0, world3D);
  assertNotNull(skyBlock, 'Sky block should exist');
  assert(skyBlock.solid === false, 'Surface sky must not be solid');
  assert(skyBlock.state === 'air', 'Surface sky state must be air');
  assert(skyBlock.excavated === true, 'Surface sky must be excavated/traversable');
  assert(skyBlock.hardness === 0, 'Surface sky hardness must be 0');

  // Subterranean solid rock block at z = 0 and z = 3
  const rockBlockZ0 = getCell(30, 20, 0, world3D);
  const rockBlockZ3 = getCell(30, 20, 3, world3D);
  assertNotNull(rockBlockZ0, 'Rock at z=0 must exist');
  assertNotNull(rockBlockZ3, 'Rock at z=3 must exist');
  assert(rockBlockZ0.x === 30 && rockBlockZ0.y === 20 && rockBlockZ0.z === 0, 'Coordinates of Z0 mismatch');
  assert(rockBlockZ3.x === 30 && rockBlockZ3.y === 20 && rockBlockZ3.z === 3, 'Coordinates of Z3 mismatch');
  assert(rockBlockZ0.solid === true && rockBlockZ3.solid === true, 'Rock blocks must be solid');

  // Excavate a cell and check its 3D volumetric representation
  excavateCell(world3D, 30, 20, 750);
  const excavatedBlockZ0 = getCell(30, 20, 0, world3D);
  assertNotNull(excavatedBlockZ0, 'Excavated block at z=0 must exist');
  assert(excavatedBlockZ0.solid === false, 'Excavated block must not be solid');
  assert(excavatedBlockZ0.state === 'air', 'Excavated block state must be air');
  assert(excavatedBlockZ0.excavated === true, 'Excavated block must have excavated = true');
  assert(excavatedBlockZ0.hardness === 0, 'Excavated block hardness must be 0');
  assert(excavatedBlockZ0.modified_at_tick === 750, 'Modified tick must match excavation tick');

  // C. Test boundary checks
  assert(getCell(-1, 10, 0) === null, 'Negative X must return null');
  assert(getCell(GRID_WIDTH, 10, 0) === null, 'Out of bounds X must return null');
  assert(getCell(10, -1, 0) === null, 'Negative Y must return null');
  assert(getCell(10, GRID_HEIGHT, 0) === null, 'Out of bounds Y must return null');
  assert(getCell(10, 10, -1) === null, 'Negative Z must return null');

  // D. Test individual 3D block modification via setCell
  clearSparseBlocks3D();
  const customBlock = createBlock3D({
    x: 55,
    y: 60,
    z: 4,
    material_type: 'CRYSTAL_BEARING_ROCK',
    solid: true,
    hardness: 2.5,
    excavated: false,
    resource_type: 'crystal',
    resource_amount: 3,
    room_id: 'vault_alpha',
    modified_at_tick: 888,
  });
  setCell(customBlock);

  const retrievedCustom = getCell(55, 60, 4);
  assertNotNull(retrievedCustom, 'Custom 3D block must be retrieved');
  assert(retrievedCustom.x === 55 && retrievedCustom.y === 60 && retrievedCustom.z === 4, 'Custom coordinates mismatch');
  assert(retrievedCustom.material_type === 'CRYSTAL_BEARING_ROCK', 'Custom material mismatch');
  assert(retrievedCustom.hardness === 2.5, 'Custom hardness mismatch');
  assert(retrievedCustom.resource_type === 'crystal', 'Custom resource_type mismatch');
  assert(retrievedCustom.resource_amount === 3, 'Custom resource_amount mismatch');
  assert(retrievedCustom.room_id === 'vault_alpha', 'Custom room_id mismatch');
  assert(retrievedCustom.modified_at_tick === 888, 'Custom modified tick mismatch');
  clearSparseBlocks3D();

  console.log('PASS — REAL_VOLUMETRIC_3D_BLOCK_VERIFIED\n');

  console.log('================================================================');
  console.log('ALL 7 MANDATORY TESTS PASSED SUCCESSFULLY!');
  console.log('================================================================');
}

runAllTerrainTests();
