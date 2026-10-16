import { TileType, ColonyRoom, GroundItem, ResourceType } from '../types/colony';
import {
  MaterialType,
  TerrainCell,
  SerializedTerrainCell,
  TerrainSaveData,
  ConcentrationType,
  TerrainBlock3D,
} from '../types/terrain';
import { DeterministicRNG } from './rng';
import {
  calculateCellMatterTotals,
  generate5x5x5MicroCells,
  liberateAllRemainingMatter,
  LiberatedMatter,
  CellMatterTotals,
} from './matterDistribution';

export const GRID_WIDTH = 84;
export const GRID_HEIGHT = 125;
export const GRID_DEPTH = 84;
export const TILE_SIZE = 16;
export const DEFAULT_WORLD_SEED = 3861;

export interface MaterialProperties {
  baseHardness: number;
  baseStability: number;
  baseHumidity: number;
  baseTemperature: number;
  primaryTile: TileType;
  defaultResource: ResourceType | null;
  defaultResourceAmount: number;
}

export const MATERIAL_PROPERTIES: Record<MaterialType, MaterialProperties> = {
  SURFACE: {
    baseHardness: 0.8,
    baseStability: 0.8,
    baseHumidity: 0.45,
    baseTemperature: 20.0,
    primaryTile: 'SURFACE_GRASS',
    defaultResource: 'dirt',
    defaultResourceAmount: 1,
  },
  SOFT_SOIL: {
    baseHardness: 0.9,
    baseStability: 0.7,
    baseHumidity: 0.65,
    baseTemperature: 18.0,
    primaryTile: 'DIRT_HUMUS',
    defaultResource: 'dirt',
    defaultResourceAmount: 1,
  },
  HUMUS: {
    baseHardness: 1.0,
    baseStability: 0.75,
    baseHumidity: 0.7,
    baseTemperature: 17.5,
    primaryTile: 'DIRT_HUMUS',
    defaultResource: 'dirt',
    defaultResourceAmount: 2,
  },
  CLAY: {
    baseHardness: 1.3,
    baseStability: 0.85,
    baseHumidity: 0.6,
    baseTemperature: 17.0,
    primaryTile: 'CLAY_DENSE',
    defaultResource: 'dirt',
    defaultResourceAmount: 1,
  },
  COMPACT_CLAY: {
    baseHardness: 1.5,
    baseStability: 0.88,
    baseHumidity: 0.55,
    baseTemperature: 17.5,
    primaryTile: 'CLAY_DENSE',
    defaultResource: 'dirt',
    defaultResourceAmount: 2,
  },
  ROCK: {
    baseHardness: 1.9,
    baseStability: 0.92,
    baseHumidity: 0.4,
    baseTemperature: 19.0,
    primaryTile: 'STONE_MINERAL',
    defaultResource: 'mineral',
    defaultResourceAmount: 1,
  },
  MINERAL_ROCK: {
    baseHardness: 2.1,
    baseStability: 0.9,
    baseHumidity: 0.35,
    baseTemperature: 20.5,
    primaryTile: 'VEIN_MINERAL',
    defaultResource: 'mineral',
    defaultResourceAmount: 2,
  },
  CRYSTAL_BEARING_ROCK: {
    baseHardness: 2.3,
    baseStability: 0.85,
    baseHumidity: 0.3,
    baseTemperature: 22.0,
    primaryTile: 'VEIN_CRYSTAL',
    defaultResource: 'crystal',
    defaultResourceAmount: 2,
  },
  NATURAL_CAVITY: {
    baseHardness: 0.0,
    baseStability: 0.95,
    baseHumidity: 0.5,
    baseTemperature: 18.5,
    primaryTile: 'AIR',
    defaultResource: null,
    defaultResourceAmount: 0,
  },
  DEEP_ROCK: {
    baseHardness: 2.8,
    baseStability: 0.98,
    baseHumidity: 0.25,
    baseTemperature: 26.5,
    primaryTile: 'ABYSSAL_BEDROCK',
    defaultResource: 'mineral',
    defaultResourceAmount: 2,
  },
};

/**
 * Calculates continuous depth in meters from y coordinate
 */
export function calculateDepthMeters(y: number): number {
  if (y < 7) return 0;
  return Number(((y - 7) * 0.52).toFixed(2));
}

/**
 * Maps MaterialType and excavation status to rendering TileType
 */
export function materialToTileType(
  material: MaterialType,
  excavated: boolean,
  y: number
): TileType {
  if (excavated) {
    return y < 7 ? 'SURFACE_AIR' : 'AIR';
  }
  if (y < 7) {
    return 'SURFACE_AIR';
  }
  if (y === 7) {
    return 'SURFACE_GRASS';
  }

  switch (material) {
    case 'SURFACE':
      return 'SURFACE_GRASS';
    case 'SOFT_SOIL':
    case 'HUMUS':
      return 'DIRT_HUMUS';
    case 'CLAY':
    case 'COMPACT_CLAY':
      return 'CLAY_DENSE';
    case 'ROCK':
      return 'STONE_MINERAL';
    case 'MINERAL_ROCK':
      return 'VEIN_MINERAL';
    case 'CRYSTAL_BEARING_ROCK':
      return 'VEIN_CRYSTAL';
    case 'NATURAL_CAVITY':
      return 'AIR';
    case 'DEEP_ROCK':
      return y <= 104 ? 'DEEP_CRYSTAL_SLATE' : 'ABYSSAL_BEDROCK';
    default:
      return 'DIRT_HUMUS';
  }
}

/**
 * Creates a single terrain cell with deterministic environmental values
 */
export function createCell(
  x: number,
  y: number,
  material: MaterialType,
  rng: DeterministicRNG,
  initialTick = 0,
  worldSeed: number = DEFAULT_WORLD_SEED
): TerrainCell {
  const depth = calculateDepthMeters(y);
  const props = MATERIAL_PROPERTIES[material];

  // Continuous geothermal temperature gradient (+0.18°C per meter depth)
  const tempVariance = rng.nextRange(-0.4, 0.4);
  const temperature = Number((props.baseTemperature + depth * 0.18 + tempVariance).toFixed(2));

  // Depth-adjusted humidity (soils near surface slightly more humid, deeper slightly drier)
  const humVariance = rng.nextRange(-0.03, 0.03);
  const depthHumFactor = Math.max(0.2, 1 - depth * 0.007);
  const humidity = Number(Math.max(0.05, Math.min(1.0, props.baseHumidity * depthHumFactor + humVariance)).toFixed(3));

  // Stability modulated by depth pressure and material
  const stabVariance = rng.nextRange(-0.02, 0.02);
  const stability = Number(Math.max(0.3, Math.min(1.0, props.baseStability + stabVariance)).toFixed(3));

  // Hardness
  const hardVariance = rng.nextRange(-0.05, 0.05);
  const hardness = material === 'NATURAL_CAVITY' || y < 7
    ? 0
    : Number(Math.max(0.1, props.baseHardness + hardVariance).toFixed(2));

  // Initial excavation and discovery state
  const excavated = material === 'NATURAL_CAVITY' || y < 7;
  const discovered = y <= 7;

  // Calcul déterministe de la matière stockée dans les 125 micro-cellules (5 × 5 × 5)
  const totals = calculateCellMatterTotals(worldSeed, x, y, material);
  const micro_cells = generate5x5x5MicroCells(worldSeed, x, y, totals, excavated);

  // Type et quantité de ressource principale affichés / révélés
  let resType: ResourceType | null = props.defaultResource;
  let resAmount = props.defaultResourceAmount;
  if (material === 'CRYSTAL_BEARING_ROCK') {
    resType = 'crystal';
    resAmount = Math.max(1, totals.crystal);
  } else if (material === 'MINERAL_ROCK') {
    resType = 'mineral';
    resAmount = Math.max(1, totals.mineral);
  } else if (totals.crystal > 0) {
    resType = 'crystal';
    resAmount = totals.crystal;
  }

  return {
    cell_id: `cell_${x}_${y}`,
    x,
    y,
    depth,
    material_type: material,
    hardness,
    humidity,
    temperature,
    stability,
    excavated,
    discovered,
    resource_type: resType,
    resource_amount: resAmount,
    modified_at_tick: initialTick,
    crystal_dust_amount: totals.crystalDust,
    crystal_amount: totals.crystal,
    mineral_amount: totals.mineral,
    dirt_amount: totals.dirt,
    resin_amount: totals.resin,
    concentration_type: totals.concentration,
    excavated_micro_cells: excavated ? 125 : 0,
    micro_cells,
  };
}

/**
 * Reveals circular radius on revealed grid and marks corresponding cells as discovered
 */
export function revealRadiusInCells(
  cells: TerrainCell[][],
  revealed: boolean[][],
  centerX: number,
  centerY: number,
  radius: number
): void {
  for (let dy = -radius; dy <= radius; dy++) {
    for (let dx = -radius; dx <= radius; dx++) {
      const nx = centerX + dx;
      const ny = centerY + dy;
      if (nx >= 0 && nx < GRID_WIDTH && ny >= 0 && ny < GRID_HEIGHT) {
        if (dx * dx + dy * dy <= radius * radius) {
          revealed[ny][nx] = true;
          if (cells[ny]?.[nx]) {
            cells[ny][nx].discovered = true;
          }
        }
      }
    }
  }
}

/**
 * Result structure of generated terrain world
 */
export interface GeneratedTerrainWorld {
  cells: TerrainCell[][];
  tiles: TileType[][];
  revealed: boolean[][];
  hardness: number[][];
  rooms: ColonyRoom[];
  groundItems: GroundItem[];
  worldSeed: number;
  currentTick: number;
}

export function determineMaterial(y: number, _rng?: DeterministicRNG): MaterialType {
  if (y < 7) {
    return 'SURFACE';
  } else if (y === 7) {
    return 'SURFACE';
  } else if (y <= 16) {
    return 'SOFT_SOIL';
  } else if (y <= 28) {
    return 'HUMUS';
  } else if (y <= 42) {
    return 'CLAY';
  } else if (y <= 55) {
    return 'COMPACT_CLAY';
  } else if (y <= 84) {
    return 'ROCK';
  } else if (y <= 104) {
    return 'ROCK';
  } else {
    return 'DEEP_ROCK';
  }
}

/**
 * Deterministically generates the entire subterranean world using worldSeed.
 * Uses ONLY the provided deterministic RNG (no Math.random()).
 */
export function generateTerrainWorld(worldSeed: number = DEFAULT_WORLD_SEED): GeneratedTerrainWorld {
  const rng = new DeterministicRNG(worldSeed);

  const cells: TerrainCell[][] = [];
  const tiles: TileType[][] = [];
  const revealed: boolean[][] = [];
  const hardness: number[][] = [];

  // 1. Base geological strata generation
  for (let y = 0; y < GRID_HEIGHT; y++) {
    cells[y] = [];
    tiles[y] = [];
    revealed[y] = [];
    hardness[y] = [];

    for (let x = 0; x < GRID_WIDTH; x++) {
      let material: MaterialType;

      if (y < 7) {
        material = 'SURFACE';
      } else if (y === 7) {
        material = 'SURFACE';
      } else if (y <= 16) {
        material = 'SOFT_SOIL';
      } else if (y <= 28) {
        material = 'HUMUS';
      } else if (y <= 42) {
        material = 'CLAY';
      } else if (y <= 55) {
        material = 'COMPACT_CLAY';
      } else if (y <= 84) {
        material = 'ROCK';
      } else if (y <= 104) {
        material = 'ROCK';
      } else {
        material = 'DEEP_ROCK';
      }

      const cell = createCell(x, y, material, rng, 0, worldSeed);
      cells[y][x] = cell;
      revealed[y][x] = cell.discovered;
      hardness[y][x] = cell.hardness;
      tiles[y][x] = materialToTileType(cell.material_type, cell.excavated, y);
    }
  }

  // Helper for deterministic vein clusters
  const seedCluster = (
    centerX: number,
    centerY: number,
    radius: number,
    material: MaterialType,
    density = 0.75,
    customResType?: ResourceType | null,
    customResAmount?: number
  ) => {
    for (let dy = -radius; dy <= radius; dy++) {
      for (let dx = -radius; dx <= radius; dx++) {
        const nx = centerX + dx;
        const ny = centerY + dy;
        if (nx >= 1 && nx < GRID_WIDTH - 1 && ny >= 8 && ny < GRID_HEIGHT - 1) {
          const dist = Math.hypot(dx, dy);
          if (dist <= radius && rng.nextFloat() < density) {
            const cell = createCell(nx, ny, material, rng, 0, worldSeed);
            if (customResType !== undefined) {
              cell.resource_type = customResType;
              cell.resource_amount = customResAmount ?? 1;
              if (customResType === 'crystal') {
                cell.crystal_amount = Math.max(cell.crystal_amount, customResAmount ?? 1);
              } else if (customResType === 'mineral') {
                cell.mineral_amount = Math.max(cell.mineral_amount, customResAmount ?? 1);
              } else if (customResType === 'resin') {
                cell.resin_amount = Math.max(cell.resin_amount, customResAmount ?? 1);
              }
              const updatedTotals: CellMatterTotals = {
                crystalDust: cell.crystal_dust_amount,
                crystal: cell.crystal_amount,
                mineral: cell.mineral_amount,
                dirt: cell.dirt_amount,
                resin: cell.resin_amount,
                concentration: cell.concentration_type ?? 'diffuse',
              };
              cell.micro_cells = generate5x5x5MicroCells(worldSeed, nx, ny, updatedTotals, cell.excavated);
            }
            cells[ny][nx] = cell;
            hardness[ny][nx] = cell.hardness;
            tiles[ny][nx] = materialToTileType(material, false, ny);
          }
        }
      }
    }
  };

  // Organic matter pockets in layer 1
  for (let i = 0; i < 9; i++) {
    const rx = 5 + rng.nextInt(0, GRID_WIDTH - 11);
    const ry = 9 + rng.nextInt(0, 18);
    seedCluster(rx, ry, 2, 'HUMUS', 0.85, 'resin', 1);
  }

  // Early small crystal nodes in upper layers
  seedCluster(24, 15, 2, 'CRYSTAL_BEARING_ROCK', 0.9, 'crystal', 2);
  seedCluster(58, 22, 2, 'CRYSTAL_BEARING_ROCK', 0.9, 'crystal', 2);

  // Mineral veins in layer 2 & 3
  for (let i = 0; i < 14; i++) {
    const rx = 6 + rng.nextInt(0, GRID_WIDTH - 13);
    const ry = 30 + rng.nextInt(0, 52);
    seedCluster(rx, ry, 2 + rng.nextInt(0, 1), 'MINERAL_ROCK', 0.8, 'mineral', 2);
  }

  // Natural cavities (geological hollow caverns)
  for (let i = 0; i < 6; i++) {
    const cx = 10 + rng.nextInt(0, GRID_WIDTH - 20);
    const cy = 25 + rng.nextInt(0, 70);
    seedCluster(cx, cy, 2, 'NATURAL_CAVITY', 0.85, null, 0);
  }

  // Significant Crystal Veins in layer 3 & 4
  for (let i = 0; i < 16; i++) {
    const rx = 6 + rng.nextInt(0, GRID_WIDTH - 13);
    const ry = 60 + rng.nextInt(0, 42);
    seedCluster(rx, ry, 2 + rng.nextInt(0, 2), 'CRYSTAL_BEARING_ROCK', 0.85, 'crystal', 2);
  }

  // Deep Abyssal Giant Geodes in layer 5
  seedCluster(22, 112, 4, 'CRYSTAL_BEARING_ROCK', 0.95, 'crystal', 3);
  seedCluster(62, 114, 5, 'CRYSTAL_BEARING_ROCK', 0.95, 'crystal', 3);
  seedCluster(42, 118, 3, 'MINERAL_ROCK', 0.9, 'mineral', 3);

  // 2. Starter burrow excavation (tunnels and living starter rooms)
  const starterTunnels: Array<{ x: number; y: number }> = [];

  // Main vertical entrance shaft (column 41-42, rows 7 down to 22)
  for (let y = 7; y <= 22; y++) {
    starterTunnels.push({ x: 41, y });
    starterTunnels.push({ x: 42, y });
  }

  // Queen Chamber (centered at x=41, y=20; 9 tiles wide, 5 tiles high rounded)
  const queenTiles: Array<{ x: number; y: number }> = [];
  for (let dy = -2; dy <= 2; dy++) {
    for (let dx = -4; dx <= 4; dx++) {
      if (Math.abs(dx) + Math.abs(dy) <= 5) {
        const qx = 41 + dx;
        const qy = 20 + dy;
        starterTunnels.push({ x: qx, y: qy });
        queenTiles.push({ x: qx, y: qy });
      }
    }
  }

  // Left gallery leading to Nursery (x=27 to 37, y=18)
  for (let x = 27; x <= 37; x++) {
    starterTunnels.push({ x, y: 18 });
  }

  // Nursery Chamber (around x=24, y=18; 7 tiles wide, 4 high)
  const nurseryTiles: Array<{ x: number; y: number }> = [];
  for (let dy = -2; dy <= 1; dy++) {
    for (let dx = -3; dx <= 3; dx++) {
      if (Math.abs(dx) + Math.abs(dy) <= 4) {
        const nx = 24 + dx;
        const ny = 18 + dy;
        starterTunnels.push({ x: nx, y: ny });
        nurseryTiles.push({ x: nx, y: ny });
      }
    }
  }

  // Right gallery leading to Material Storage (x=45 to 55, y=19)
  for (let x = 45; x <= 55; x++) {
    starterTunnels.push({ x, y: 19 });
  }

  // Storage Chamber (around x=56, y=19)
  const storageTiles: Array<{ x: number; y: number }> = [];
  for (let dy = -2; dy <= 2; dy++) {
    for (let dx = -3; dx <= 3; dx++) {
      if (Math.abs(dx) + Math.abs(dy) <= 4) {
        const sx = 56 + dx;
        const sy = 19 + dy;
        starterTunnels.push({ x: sx, y: sy });
        storageTiles.push({ x: sx, y: sy });
      }
    }
  }

  // Deep exploratory shaft going down to Layer 2 (around row 35)
  for (let y = 22; y <= 35; y++) {
    starterTunnels.push({ x: 41, y });
  }
  for (let dx = -3; dx <= 3; dx++) {
    starterTunnels.push({ x: 41 + dx, y: 35 });
  }

  // Apply excavation to starter burrow
  starterTunnels.forEach(({ x, y }) => {
    if (x >= 0 && x < GRID_WIDTH && y >= 0 && y < GRID_HEIGHT) {
      const cell = cells[y][x];
      cell.excavated = true;
      cell.hardness = 0;
      cell.material_type = y < 7 ? 'SURFACE' : 'NATURAL_CAVITY';
      cell.excavated_micro_cells = 125;
      if (cell.micro_cells) {
        cell.micro_cells.forEach((mc) => {
          mc.excavated = true;
        });
      }
      tiles[y][x] = y < 7 ? 'SURFACE_AIR' : 'AIR';
      hardness[y][x] = 0;
    }
  });

  // Reveal around starter tunnels
  starterTunnels.forEach(({ x, y }) => {
    revealRadiusInCells(cells, revealed, x, y, 4);
  });

  // Starter Rooms
  const rooms: ColonyRoom[] = [
    {
      id: 'room_queen_1',
      type: 'QUEEN',
      hasCommandTerminal: true,
      name: 'Chambre Royale de la Reine',
      color: '#f59e0b',
      tiles: queenTiles,
      bounds: { minX: 37, maxX: 45, minY: 18, maxY: 22 },
      center: { x: 41, y: 20 },
      level: 1,
      storedResources: { crystal: 2, dirt: 12, mineral: 4, resin: 2 },
      capacity: 50,
    },
    {
      id: 'room_nursery_1',
      type: 'NURSERY',
      name: 'Nurserie du Couvain',
      color: '#ec4899',
      tiles: nurseryTiles,
      bounds: { minX: 21, maxX: 27, minY: 16, maxY: 19 },
      center: { x: 24, y: 18 },
      level: 1,
      storedResources: { crystal: 0, dirt: 8, mineral: 0, resin: 0 },
      capacity: 30,
    },
    {
      id: 'room_storage_1',
      type: 'STORAGE',
      name: 'Stockage des Matériaux',
      color: '#a16207',
      tiles: storageTiles,
      bounds: { minX: 53, maxX: 59, minY: 17, maxY: 21 },
      center: { x: 56, y: 19 },
      level: 1,
      storedResources: { crystal: 4, dirt: 26, mineral: 8, resin: 4 },
      capacity: 100,
    },
  ];

  // Set isDesignated and link cells to their stable room_id for starter chambers
  for (const r of rooms) {
    r.isDesignated = true;
    for (const t of r.tiles) {
      if (cells[t.y]?.[t.x]) {
        cells[t.y][t.x].room_id = r.id;
      }
    }
  }

  // Ground items left on the floor from initial excavation (seeded deterministically)
  const groundItems: GroundItem[] = [
    {
      id: 'item_1',
      x: 39,
      y: 35,
      type: 'dirt',
      color: '#8a5e3a',
      name: 'Motte de terre meuble',
      createdAt: 1000,
    },
    {
      id: 'item_2',
      x: 43,
      y: 35,
      type: 'crystal',
      color: '#38bdf8',
      name: 'Éclat de cristal cyan',
      createdAt: 1000,
    },
    {
      id: 'item_3',
      x: 42,
      y: 35,
      type: 'mineral',
      color: '#94a3b8',
      name: 'Fragment minéral',
      createdAt: 1000,
    },
  ];

  return {
    cells,
    tiles,
    revealed,
    hardness,
    rooms,
    groundItems,
    worldSeed,
    currentTick: 0,
  };
}

/**
 * Crée une instance d'un vrai bloc volumétrique 3D de matière de terrain (Topbrutus/hole).
 */
export function createBlock3D(params: {
  x: number;
  y: number;
  z: number;
  material_type: MaterialType;
  solid?: boolean;
  state?: 'solid' | 'air';
  hardness?: number;
  excavated?: boolean;
  resource_type?: ResourceType | null;
  resource_amount?: number;
  room_id?: string | null;
  modified_at_tick?: number;
  depth?: number;
  crystal_dust_amount?: number;
  crystal_amount?: number;
  mineral_amount?: number;
  dirt_amount?: number;
  resin_amount?: number;
}): TerrainBlock3D {
  const isSolid = params.solid ?? (params.state ? params.state === 'solid' : !(params.excavated ?? false));
  const isExcavated = params.excavated ?? !isSolid;
  const hard = isSolid ? (params.hardness !== undefined ? params.hardness : 1.0) : 0;

  return {
    x: params.x,
    y: params.y,
    z: params.z,
    material_type: params.material_type,
    material: params.material_type,
    solid: isSolid,
    is_solid: isSolid,
    state: isSolid ? 'solid' : 'air',
    hardness: hard,
    excavated: isExcavated,
    resource_type: params.resource_type ?? null,
    resource_amount: params.resource_amount ?? 0,
    room_id: params.room_id ?? null,
    modified_at_tick: params.modified_at_tick ?? 0,
    depth: params.depth ?? Number((params.y * 0.52).toFixed(2)),
    crystal_dust_amount: params.crystal_dust_amount ?? 0,
    crystal_amount: params.crystal_amount ?? 0,
    mineral_amount: params.mineral_amount ?? 0,
    dirt_amount: params.dirt_amount ?? 0,
    resin_amount: params.resin_amount ?? 0,
  };
}

// Magasin éparse pour les blocs 3D modifiés individuellement (sans allouer 84 × 84 × 125 en mémoire)
const sparseBlocks3D = new Map<string, TerrainBlock3D>();

/**
 * Définit ou met à jour un bloc 3D volumétrique réel dans le bac à sable.
 */
export function setCell(block: TerrainBlock3D): void {
  const key = `${block.x},${block.y},${block.z}`;
  sparseBlocks3D.set(key, block);
}

/**
 * Réinitialise le stockage éparse des blocs 3D modifiés.
 */
export function clearSparseBlocks3D(): void {
  sparseBlocks3D.clear();
}

/**
 * Récupère un vrai bloc volumétrique de terrain à la position (x, y, z).
 * Permet de demander getCell(x, y, z) et de recevoir un vrai bloc 3D de matière.
 * Ne construit PAS tout le monde 84 × 84 × 125 en mémoire.
 */
export function getCell(
  x: number,
  y: number,
  z: number = 0,
  context?: GeneratedTerrainWorld | { cells: TerrainCell[][]; worldSeed?: number } | TerrainCell[][]
): TerrainBlock3D | null {
  // 1. Validation stricte des coordonnées du bac à sable 84 × 84 × 125
  if (x < 0 || x >= GRID_WIDTH || y < 0 || y >= GRID_HEIGHT || z < 0 || z >= GRID_DEPTH) {
    return null;
  }

  // 2. Vérification dans le magasin éparse de blocs 3D modifiés
  const key = `${x},${y},${z}`;
  if (sparseBlocks3D.has(key)) {
    return sparseBlocks3D.get(key)!;
  }

  // 3. Extraction de la grille existante si fournie
  let cells: TerrainCell[][] | undefined;
  let worldSeed = DEFAULT_WORLD_SEED;

  if (context) {
    if (Array.isArray(context)) {
      cells = context;
    } else if ('cells' in context && Array.isArray(context.cells)) {
      cells = context.cells;
      if (context.worldSeed) worldSeed = context.worldSeed;
    }
  }

  // 4. Si la position est en surface (ciel ouvert)
  if (y < 7) {
    return createBlock3D({
      x,
      y,
      z,
      material_type: 'SURFACE',
      solid: false,
      state: 'air',
      hardness: 0,
      excavated: true,
      resource_type: null,
      resource_amount: 0,
      room_id: null,
      modified_at_tick: 0,
      depth: 0,
    });
  }

  // 5. Résolution à partir de la macro-cellule existante si présente
  const cell = cells ? cells[y]?.[x] : null;

  if (cell) {
    if (cell.excavated) {
      // Cavité excavée principale (couche z=0 ou volume entièrement excavé)
      const isZExcavated = z === 0 || cell.excavated_micro_cells >= 125;
      if (isZExcavated) {
        return createBlock3D({
          x,
          y,
          z,
          material_type: cell.material_type,
          solid: false,
          state: 'air',
          hardness: 0,
          excavated: true,
          resource_type: cell.resource_type,
          resource_amount: 0,
          room_id: cell.room_id ?? null,
          modified_at_tick: cell.modified_at_tick,
          depth: cell.depth,
        });
      } else {
        // z > 0 dans une cellule partiellement forée : vérification de la micro-cellule correspondante
        const subZ = z % 5;
        const mc = cell.micro_cells?.find((m) => m.subZ === subZ);
        const isMcExcavated = mc?.excavated ?? false;
        return createBlock3D({
          x,
          y,
          z,
          material_type: cell.material_type,
          solid: !isMcExcavated,
          state: isMcExcavated ? 'air' : 'solid',
          hardness: isMcExcavated ? 0 : cell.hardness,
          excavated: isMcExcavated,
          resource_type: mc
            ? mc.crystal_amount > 0
              ? 'crystal'
              : mc.crystal_dust_amount > 0
              ? 'crystal_dust'
              : mc.mineral_amount > 0
              ? 'mineral'
              : mc.dirt_amount > 0
              ? 'dirt'
              : mc.resin_amount > 0
              ? 'resin'
              : null
            : cell.resource_type,
          resource_amount: mc
            ? mc.crystal_amount || mc.crystal_dust_amount || mc.mineral_amount || mc.dirt_amount || mc.resin_amount || 0
            : 0,
          room_id: isMcExcavated ? cell.room_id ?? null : null,
          modified_at_tick: cell.modified_at_tick,
          depth: cell.depth,
          crystal_dust_amount: mc?.crystal_dust_amount ?? 0,
          crystal_amount: mc?.crystal_amount ?? 0,
          mineral_amount: mc?.mineral_amount ?? 0,
          dirt_amount: mc?.dirt_amount ?? 0,
          resin_amount: mc?.resin_amount ?? 0,
        });
      }
    } else {
      // Bloc solide non-excavé
      const subZ = z % 5;
      const mc = cell.micro_cells?.find((m) => m.subZ === subZ);
      return createBlock3D({
        x,
        y,
        z,
        material_type: cell.material_type,
        solid: true,
        state: 'solid',
        hardness: cell.hardness,
        excavated: false,
        resource_type: mc
          ? mc.crystal_amount > 0
            ? 'crystal'
            : mc.crystal_dust_amount > 0
            ? 'crystal_dust'
            : mc.mineral_amount > 0
            ? 'mineral'
            : mc.dirt_amount > 0
            ? 'dirt'
            : mc.resin_amount > 0
            ? 'resin'
            : null
          : cell.resource_type,
        resource_amount: mc
          ? mc.crystal_amount || mc.crystal_dust_amount || mc.mineral_amount || mc.dirt_amount || mc.resin_amount || 0
          : cell.resource_amount,
        room_id: null,
        modified_at_tick: cell.modified_at_tick,
        depth: cell.depth,
        crystal_dust_amount: mc?.crystal_dust_amount ?? cell.crystal_dust_amount,
        crystal_amount: mc?.crystal_amount ?? cell.crystal_amount,
        mineral_amount: mc?.mineral_amount ?? cell.mineral_amount,
        dirt_amount: mc?.dirt_amount ?? cell.dirt_amount,
        resin_amount: mc?.resin_amount ?? cell.resin_amount,
      });
    }
  }

  // 6. Résolution déterministe à la demande pour n'importe quel coordonnée (x, y, z)
  // sans instanciation d'un tableau volumineux de 874 944 cellules en mémoire
  const voxelSeed = (worldSeed ^ (x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) >>> 0;
  const cellRng = new DeterministicRNG(voxelSeed);
  const material = determineMaterial(y, cellRng);
  const props = MATERIAL_PROPERTIES[material];

  return createBlock3D({
    x,
    y,
    z,
    material_type: material,
    solid: true,
    state: 'solid',
    hardness: props.baseHardness,
    excavated: false,
    resource_type: props.defaultResource,
    resource_amount: props.defaultResourceAmount,
    room_id: null,
    modified_at_tick: 0,
    depth: Number((y * 0.52).toFixed(2)),
  });
}

/**
 * Inspection helper: retrieves all properties of a cell by coordinates
 */
export function getCellInfo(cells: TerrainCell[][], x: number, y: number): TerrainCell | null {
  if (y < 0 || y >= GRID_HEIGHT || x < 0 || x >= GRID_WIDTH) {
    return null;
  }
  return cells[y]?.[x] ?? null;
}

/**
 * Inspection helper: retrieves cell by its stable cell_id
 */
export function getCellById(cells: TerrainCell[][], cellId: string): TerrainCell | null {
  const match = cellId.match(/^cell_(\d+)_(\d+)$/);
  if (match) {
    const x = parseInt(match[1], 10);
    const y = parseInt(match[2], 10);
    return getCellInfo(cells, x, y);
  }
  // Fallback linear scan if non-standard ID
  for (let y = 0; y < cells.length; y++) {
    for (let x = 0; x < cells[y].length; x++) {
      if (cells[y][x]?.cell_id === cellId) {
        return cells[y][x];
      }
    }
  }
  return null;
}

/**
 * Excavates a cell, updating hardness, excavated state, tile type,
 * revealing neighbor cells, and yielding any buried resource.
 */
export function excavateCell(
  world: GeneratedTerrainWorld,
  x: number,
  y: number,
  tick: number
): {
  cell: TerrainCell;
  revealedResource: { type: ResourceType; count: number } | null;
  liberatedMatter?: LiberatedMatter;
} | null {
  if (x < 0 || x >= GRID_WIDTH || y < 0 || y >= GRID_HEIGHT) {
    return null;
  }

  const cell = world.cells[y][x];
  if (!cell || cell.excavated) {
    return null;
  }

  // Libération de la matière qui était cachée dans la roche solide
  const liberatedMatter = liberateAllRemainingMatter(cell);

  cell.excavated = true;
  cell.hardness = 0;
  cell.material_type = y < 7 ? 'SURFACE' : 'NATURAL_CAVITY';
  cell.modified_at_tick = tick;
  cell.excavated_micro_cells = 125;

  world.hardness[y][x] = 0;
  world.tiles[y][x] = y < 7 ? 'SURFACE_AIR' : 'AIR';

  revealRadiusInCells(world.cells, world.revealed, x, y, 4);

  let revealedResource: { type: ResourceType; count: number } | null = null;
  if (cell.resource_type && cell.resource_amount > 0) {
    revealedResource = {
      type: cell.resource_type,
      count: cell.resource_amount,
    };
  }

  return { cell, revealedResource, liberatedMatter };
}

/**
 * Serializes the current terrain world into a JSON-compatible representation.
 */
export function saveTerrain(world: GeneratedTerrainWorld, currentTick = 0): TerrainSaveData {
  let totalDug = 0;
  let deepest = 0;
  const serializedCells: SerializedTerrainCell[] = [];

  for (let y = 0; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      const c = world.cells[y][x];
      if (c.excavated) {
        totalDug++;
        if (c.depth > deepest) {
          deepest = c.depth;
        }
      }
      serializedCells.push({
        cell_id: c.cell_id,
        room_id: c.room_id ?? null,
        x: c.x,
        y: c.y,
        depth: c.depth,
        material_type: c.material_type,
        hardness: c.hardness,
        humidity: c.humidity,
        temperature: c.temperature,
        stability: c.stability,
        excavated: c.excavated,
        discovered: c.discovered,
        resource_type: c.resource_type,
        resource_amount: c.resource_amount,
        modified_at_tick: c.modified_at_tick,
        crystal_dust_amount: c.crystal_dust_amount,
        crystal_amount: c.crystal_amount,
        mineral_amount: c.mineral_amount,
        dirt_amount: c.dirt_amount,
        resin_amount: c.resin_amount,
        concentration_type: c.concentration_type,
        excavated_micro_cells: c.excavated_micro_cells,
      });
    }
  }

  return {
    schema_version: 'BRUTOBAC-TERRAIN-v1',
    mode: 'SIMULATION',
    world_seed: world.worldSeed,
    width: GRID_WIDTH,
    height: GRID_HEIGHT,
    tick: currentTick || world.currentTick || 0,
    cells: serializedCells,
    rooms: world.rooms ? JSON.parse(JSON.stringify(world.rooms)) : [],
    groundItems: world.groundItems ? JSON.parse(JSON.stringify(world.groundItems)) : [],
    metadata: {
      description: 'Simulation vivante du terrier multi-étages BrutoBac',
      totalDugCells: totalDug,
      deepestMeters: deepest,
    },
  };
}

/**
 * Loads and reconstructs the terrain world from saved data.
 * Guarantees exact state restoration: terrain_before === terrain_after.
 */
export function loadTerrain(saveData: TerrainSaveData): GeneratedTerrainWorld {
  if (saveData.schema_version !== 'BRUTOBAC-TERRAIN-v1') {
    throw new Error(`Unsupported schema version: ${saveData.schema_version}`);
  }

  const cells: TerrainCell[][] = [];
  const tiles: TileType[][] = [];
  const revealed: boolean[][] = [];
  const hardness: number[][] = [];

  for (let y = 0; y < saveData.height; y++) {
    cells[y] = [];
    tiles[y] = [];
    revealed[y] = [];
    hardness[y] = [];
  }

  for (const sc of saveData.cells) {
    const { x, y } = sc;
    const totals: CellMatterTotals = {
      crystalDust: sc.crystal_dust_amount ?? 0,
      crystal: sc.crystal_amount ?? 0,
      mineral: sc.mineral_amount ?? 0,
      dirt: sc.dirt_amount ?? 0,
      resin: sc.resin_amount ?? 0,
      concentration: sc.concentration_type ?? 'diffuse',
    };
    const micro_cells = generate5x5x5MicroCells(saveData.world_seed, x, y, totals, sc.excavated);

    const cell: TerrainCell = {
      cell_id: sc.cell_id,
      room_id: sc.room_id ?? null,
      x: sc.x,
      y: sc.y,
      depth: sc.depth,
      material_type: sc.material_type,
      hardness: sc.hardness,
      humidity: sc.humidity,
      temperature: sc.temperature,
      stability: sc.stability,
      excavated: sc.excavated,
      discovered: sc.discovered,
      resource_type: sc.resource_type,
      resource_amount: sc.resource_amount,
      modified_at_tick: sc.modified_at_tick,
      crystal_dust_amount: sc.crystal_dust_amount ?? totals.crystalDust,
      crystal_amount: sc.crystal_amount ?? totals.crystal,
      mineral_amount: sc.mineral_amount ?? totals.mineral,
      dirt_amount: sc.dirt_amount ?? totals.dirt,
      resin_amount: sc.resin_amount ?? totals.resin,
      concentration_type: sc.concentration_type ?? totals.concentration,
      excavated_micro_cells: sc.excavated_micro_cells ?? (sc.excavated ? 125 : 0),
      micro_cells,
    };

    cells[y][x] = cell;
    hardness[y][x] = cell.hardness;
    revealed[y][x] = cell.discovered;
    tiles[y][x] = materialToTileType(cell.material_type, cell.excavated, y);
  }

  const loadedRooms: ColonyRoom[] = saveData.rooms ? JSON.parse(JSON.stringify(saveData.rooms)) : [];
  for (const r of loadedRooms) {
    if (r.type !== 'NONE') {
      r.isDesignated = true;
    }
    for (const t of r.tiles) {
      if (cells[t.y]?.[t.x]) {
        cells[t.y][t.x].room_id = r.id;
      }
    }
  }

  return {
    cells,
    tiles,
    revealed,
    hardness,
    rooms: loadedRooms,
    groundItems: saveData.groundItems ? JSON.parse(JSON.stringify(saveData.groundItems)) : [],
    worldSeed: saveData.world_seed,
    currentTick: saveData.tick,
  };
}
