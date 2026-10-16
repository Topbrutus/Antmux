import { TileType, ResourceType, ColonyRoom, GroundItem } from './colony';

export type MaterialType =
  | 'SURFACE'
  | 'SOFT_SOIL'
  | 'HUMUS'
  | 'CLAY'
  | 'COMPACT_CLAY'
  | 'ROCK'
  | 'MINERAL_ROCK'
  | 'CRYSTAL_BEARING_ROCK'
  | 'NATURAL_CAVITY'
  | 'DEEP_ROCK';

export interface MicroCell {
  index: number; // 0 to 124 (5 * 5 * 5)
  subX: number; // 0 to 4
  subY: number; // 0 to 4
  subZ: number; // 0 to 4
  excavated: boolean; // false = solid (hidden inside rock), true = liberated
  crystal_dust_amount: number;
  crystal_amount: number;
  mineral_amount: number;
  dirt_amount: number;
  resin_amount: number;
}

export type ConcentrationType =
  | 'isolated_crystal'
  | 'small_pocket'
  | 'cluster'
  | 'vein'
  | 'rich_zone'
  | 'rare_geode'
  | 'diffuse';

/**
 * Bloc volumétrique 3D réel de matière (Topbrutus/hole).
 * Représente un bloc physique individuel à des coordonnées (x, y, z).
 * Chaque position du bac à sable peut être représentée sous forme d'un vrai bloc de terrain.
 */
export interface TerrainBlock3D {
  x: number; // Coordonnée X (0..83)
  y: number; // Coordonnée Y (0..123)
  z: number; // Coordonnée Z (profondeur volumétrique)
  material_type: MaterialType; // Type de matière
  material?: MaterialType; // Alias d'ergonomie
  solid: boolean; // true = matière solide, false = vide/air
  is_solid: boolean; // Alias d'ergonomie
  state: 'solid' | 'air'; // Représentation explicite solid / air
  hardness: number; // Dureté / résistance au creusage (0 si air/excavé)
  excavated: boolean; // true si cavé/traversable
  resource_type: ResourceType | null; // Type de ressource contenue ou libérée
  resource_amount: number; // Quantité de ressource
  room_id?: string | null; // Identifiant de salle ou galerie éventuelle
  modified_at_tick: number; // Tick de simulation de dernière modification

  // Propriétés volumétriques et conservatrices complémentaires
  depth?: number; // Profondeur métrique continue
  crystal_dust_amount?: number;
  crystal_amount?: number;
  mineral_amount?: number;
  dirt_amount?: number;
  resin_amount?: number;
}

export type Block3D = TerrainBlock3D;
export type TerrainCell3D = TerrainBlock3D;

export interface TerrainCell {
  cell_id: string;
  room_id?: string | null; // Stable room_id if cell is part of an excavated chamber
  x: number;
  y: number;
  depth: number; // Continuous depth in meters
  material_type: MaterialType;
  hardness: number; // Resistance to excavation (0 = excavated/air)
  humidity: number; // 0.0 to 1.0
  temperature: number; // In Celsius (°C)
  stability: number; // 0.0 to 1.0 (structural integrity)
  excavated: boolean; // True if carved out/walkable
  discovered: boolean; // True if revealed by exploration
  resource_type: ResourceType | null;
  resource_amount: number;
  modified_at_tick: number; // Simulation tick of last state change

  // Micro-distribution 5x5x5 & Conservation de matière
  crystal_dust_amount: number;
  crystal_amount: number;
  mineral_amount: number;
  dirt_amount: number;
  resin_amount: number;
  concentration_type?: ConcentrationType;
  excavated_micro_cells: number; // 0 to 125
  micro_cells?: MicroCell[];
}

export interface SerializedTerrainCell {
  cell_id: string;
  room_id?: string | null;
  x: number;
  y: number;
  depth: number;
  material_type: MaterialType;
  hardness: number;
  humidity: number;
  temperature: number;
  stability: number;
  excavated: boolean;
  discovered: boolean;
  resource_type: ResourceType | null;
  resource_amount: number;
  modified_at_tick: number;

  crystal_dust_amount?: number;
  crystal_amount?: number;
  mineral_amount?: number;
  dirt_amount?: number;
  resin_amount?: number;
  concentration_type?: ConcentrationType;
  excavated_micro_cells?: number;
}

export interface TerrainSaveData {
  schema_version: 'BRUTOBAC-TERRAIN-v1';
  mode: 'SIMULATION';
  world_seed: number;
  width: number;
  height: number;
  tick: number;
  cells: SerializedTerrainCell[];
  rooms?: ColonyRoom[];
  groundItems?: GroundItem[];
  metadata?: {
    description: string;
    totalDugCells: number;
    deepestMeters: number;
  };
}
