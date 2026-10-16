import { TileType, StratumInfo, ColonyRoom, RoomType, GroundItem } from '../types/colony';
import { TerrainCell } from '../types/terrain';
import { TerrainFragment } from '../types/fragments';
import {
  generateTerrainWorld,
  DEFAULT_WORLD_SEED,
  saveTerrain as saveTerrainInternal,
  loadTerrain as loadTerrainInternal,
  getCellInfo as getCellInfoInternal,
  getCellById as getCellByIdInternal,
  getCell as getCellInternal,
  createBlock3D,
  setCell,
  clearSparseBlocks3D,
  excavateCell as excavateCellInternal,
  GeneratedTerrainWorld,
} from './terrain';

export const GRID_WIDTH = 84;
export const GRID_HEIGHT = 125;
export const GRID_DEPTH = 84;
export const TILE_SIZE = 16; // Pixels per cell in native coordinates

export const STRATA: StratumInfo[] = [
  {
    id: 0,
    name: 'Surface & Tertre',
    depthLabel: '0m',
    startRow: 0,
    endRow: 7,
    primaryTile: 'SURFACE_AIR',
    themeColor: '#78c269',
    description: 'Accès extérieur, herbes et monticule protecteur.',
    discoveryBonus: 'Lumière naturelle & ventilation',
  },
  {
    id: 1,
    name: 'Humus & Terre Meuble',
    depthLabel: '-2m à -12m',
    startRow: 8,
    endRow: 28,
    primaryTile: 'DIRT_HUMUS',
    themeColor: '#8a5e3a',
    description: 'Terre riche, racines superficielles et galeries initiales.',
    discoveryBonus: 'Creusage rapide, matière brute abondante',
  },
  {
    id: 2,
    name: 'Argile Compacte',
    depthLabel: '-12m à -28m',
    startRow: 29,
    endRow: 55,
    primaryTile: 'CLAY_DENSE',
    themeColor: '#b46738',
    description: 'Sol dense et stable, idéal pour le stockage et les chambres durables.',
    discoveryBonus: 'Stabilité élevée des parois',
  },
  {
    id: 3,
    name: 'Roche Minérale & Schiste',
    depthLabel: '-28m à -44m',
    startRow: 56,
    endRow: 84,
    primaryTile: 'STONE_MINERAL',
    themeColor: '#4f5669',
    description: 'Strate géologique dure contenant de riches filons métalliques et fragments.',
    discoveryBonus: 'Fragments minéraux & fabrication',
  },
  {
    id: 4,
    name: 'Noyau Cristallin',
    depthLabel: '-44m à -55m',
    startRow: 85,
    endRow: 104,
    primaryTile: 'DEEP_CRYSTAL_SLATE',
    themeColor: '#1d486e',
    description: 'Basalte sombre illuminé par des amas de cristaux résonants bleus et pourpres.',
    discoveryBonus: 'Cristaux purs haut potentiel',
  },
  {
    id: 5,
    name: 'Socle Abyssal & Géodes',
    depthLabel: '-55m à -65m',
    startRow: 105,
    endRow: 123,
    primaryTile: 'ABYSSAL_BEDROCK',
    themeColor: '#1c1b2b',
    description: 'Profondeurs primordiales, géodes géantes et fossiles ancestraux.',
    discoveryBonus: 'Énergie brute résonante colossale',
  },
];

export interface GridState {
  cells: TerrainCell[][];
  tiles: TileType[][];
  revealed: boolean[][];
  hardness: number[][]; // Remaining hit points to dig (1.0 default)
  rooms: ColonyRoom[];
  groundItems: GroundItem[];
  terrainFragments: TerrainFragment[];
  worldSeed: number;
  currentTick: number;
}

/**
 * Procedurally generates the subterranean world with stratified geological layers,
 * buried crystal clusters, mineral pockets, and an initial living starter nest deterministically.
 */
export function generateInitialGrid(worldSeed: number = DEFAULT_WORLD_SEED): GridState {
  const world: GeneratedTerrainWorld = generateTerrainWorld(worldSeed);
  return {
    cells: world.cells,
    tiles: world.tiles,
    revealed: world.revealed,
    hardness: world.hardness,
    rooms: world.rooms,
    groundItems: world.groundItems,
    terrainFragments: [],
    worldSeed: world.worldSeed,
    currentTick: world.currentTick,
  };
}

/**
 * Reveal tiles in circular radius when dug or traversed
 */
export function revealRadius(
  revealed: boolean[][],
  centerX: number,
  centerY: number,
  radius: number,
  cells?: TerrainCell[][]
) {
  for (let dy = -radius; dy <= radius; dy++) {
    for (let dx = -radius; dx <= radius; dx++) {
      const nx = centerX + dx;
      const ny = centerY + dy;
      if (nx >= 0 && nx < GRID_WIDTH && ny >= 0 && ny < GRID_HEIGHT) {
        if (dx * dx + dy * dy <= radius * radius) {
          revealed[ny][nx] = true;
          if (cells && cells[ny]?.[nx]) {
            cells[ny][nx].discovered = true;
          }
        }
      }
    }
  }
}

/**
 * Checks if a tile is walkable for ants (only excavated subterranean air, never sky)
 */
export function isWalkable(tile: TileType): boolean {
  return tile === 'AIR';
}

/**
 * Checks if a cell is walkable
 */
export function isCellWalkable(cell: TerrainCell): boolean {
  return cell.excavated || cell.material_type === 'NATURAL_CAVITY';
}

/**
 * Helper to get stratum at given row
 */
export function getStratumAtRow(row: number): StratumInfo {
  for (const stratum of STRATA) {
    if (row >= stratum.startRow && row <= stratum.endRow) {
      return stratum;
    }
  }
  return STRATA[STRATA.length - 1];
}

export const ROOM_PRESETS: Record<
  RoomType,
  { name: string; color: string; description: string; icon: string }
> = {
  NONE: {
    name: 'Galerie Simple',
    color: '#71717a',
    description: 'Voie de passage et transit.',
    icon: 'DoorOpen',
  },
  QUEEN: {
    name: 'Chambre Royale',
    color: '#f59e0b',
    description: 'Cœur biologique de la colonie, ponte et phéromones régénérantes.',
    icon: 'Crown',
  },
  NURSERY: {
    name: 'Nurserie / Couvain',
    color: '#ec4899',
    description: 'Incubation des œufs, larves et cocons soignés par les nourrices.',
    icon: 'Egg',
  },
  STORAGE: {
    name: 'Stockage Général',
    color: '#d97706',
    description: 'Accumulation des matières brutes et fragments excavés.',
    icon: 'Boxes',
  },
  CRYSTAL_VAULT: {
    name: 'Réserve des Cristaux',
    color: '#06b6d4',
    description: 'Sanctuaire illuminé pour les cristaux découverts, émet de l’énergie résonante.',
    icon: 'Gem',
  },
  WORKSHOP: {
    name: 'Atelier Brutoficateur',
    color: '#10b981',
    description: 'Transformation des fragments en bio-résine et renforts de parois.',
    icon: 'Hammer',
  },
  RECYCLING: {
    name: 'Compost & Recyclage',
    color: '#84cc16',
    description: 'Tri des gravats et débris pour produire un substrat fertile.',
    icon: 'Recycle',
  },
  GUARD_POST: {
    name: 'Avant-poste de Garde',
    color: '#ef4444',
    description: 'Poste de défense pour surveiller les entrées et sécuriser les failles.',
    icon: 'Shield',
  },
};

export {
  saveTerrainInternal as saveTerrain,
  getCellInfoInternal as getCellInfo,
  getCellByIdInternal as getCellById,
  getCellInternal as getCell,
  createBlock3D,
  setCell,
  clearSparseBlocks3D,
  excavateCellInternal as excavateCell,
};

export function loadTerrain(saveData: Parameters<typeof loadTerrainInternal>[0]): GridState {
  return {
    ...loadTerrainInternal(saveData),
    terrainFragments: [],
  };
}

export {
  calculateCellMatterTotals,
  generate5x5x5MicroCells,
  liberateMicroCells,
  liberateAllRemainingMatter,
  verifyCellMatterConservation,
  detectNaturalConcentration,
} from './matterDistribution';

export {
  getAccessibleDigFronts,
  classifyBurrowTopology,
  getBurrowStats,
  updateBurrowChambers,
  isDesignatedRoom,
  digHorizontalTunnel,
  digVerticalShaft,
  digOrganicCavity,
} from './burrowArchitecture';
