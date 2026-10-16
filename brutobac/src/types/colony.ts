import { AntActionRecord } from './agent';

export type TileType =
  | 'AIR'
  | 'SURFACE_AIR'
  | 'SURFACE_GRASS'
  | 'DIRT_HUMUS'
  | 'CLAY_DENSE'
  | 'STONE_MINERAL'
  | 'DEEP_CRYSTAL_SLATE'
  | 'ABYSSAL_BEDROCK'
  | 'VEIN_CRYSTAL'
  | 'VEIN_MINERAL'
  | 'VEIN_ORGANIC'
  | 'VEIN_FOSSIL';

export type RoomType =
  | 'NONE'
  | 'QUEEN'
  | 'NURSERY'
  | 'STORAGE'
  | 'CRYSTAL_VAULT'
  | 'WORKSHOP'
  | 'RECYCLING'
  | 'GUARD_POST';

export type AntCaste =
  | 'QUEEN'
  | 'MINER'
  | 'CARRIER'
  | 'NURSE'
  | 'BUILDER'
  | 'GUARD';

export type AntTaskType =
  | 'dig'
  | 'carry'
  | 'explore'
  | 'build'
  | 'brood'
  | 'defense'
  | 'recycle';

export const ALL_ANT_TASKS: AntTaskType[] = [
  'dig',
  'carry',
  'explore',
  'build',
  'brood',
  'defense',
  'recycle',
];

export const TASK_LABELS: Record<
  AntTaskType,
  { name: string; icon: string; color: string; desc: string }
> = {
  dig: {
    name: 'Creusage',
    icon: 'Pickaxe',
    color: '#f59e0b',
    desc: 'Forage et excavation des roches et filons',
  },
  carry: {
    name: 'Transport',
    icon: 'Briefcase',
    color: '#06b6d4',
    desc: 'Acheminement des matières et cristaux vers les chambres',
  },
  explore: {
    name: 'Exploration',
    icon: 'Compass',
    color: '#a855f7',
    desc: 'Reconnaissance des galeries et révélation du terrain',
  },
  build: {
    name: 'Construction',
    icon: 'Hammer',
    color: '#10b981',
    desc: 'Aménagement et consolidation des salles',
  },
  brood: {
    name: 'Couvain',
    icon: 'Egg',
    color: '#ec4899',
    desc: 'Incubation, nourrissage des larves et soins aux œufs',
  },
  defense: {
    name: 'Défense',
    icon: 'Shield',
    color: '#ef4444',
    desc: 'Surveillance des seuils, patrouille et sécurité',
  },
  recycle: {
    name: 'Recyclage',
    icon: 'Recycle',
    color: '#84cc16',
    desc: 'Tri des gravats, compost et nettoyage des débris',
  },
};

export type AntState =
  | 'IDLE'
  | 'WANDERING'
  | 'MOVING_TO_DIG'
  | 'DIGGING'
  | 'PICKING_UP'
  | 'CARRYING'
  | 'DELIVERING'
  | 'TENDING_BROOD'
  | 'PATROLLING'
  | 'RESTING';

export type ResourceType = 'crystal' | 'crystal_dust' | 'dirt' | 'mineral' | 'resin' | 'egg';

export interface CarriedItem {
  type: ResourceType;
  color: string;
  name: string;
}

export interface GroundItem {
  id: string;
  x: number;
  y: number;
  type: ResourceType;
  color: string;
  name: string;
  createdAt: number;
  reservedBy?: string; // Ant ID
  amount?: number; // Stack quantity
  vy?: number; // Vertical falling velocity (for powder/earth falling under gravity)
  isSettled?: boolean; // True once settled on tunnel floor
}

export interface Ant {
  id: string;
  ant_id: string; // Unique stable identifier for Bloc 3
  name: string;
  caste: AntCaste;
  x: number; // grid coords (floating point for smooth movement)
  y: number;
  vx: number;
  vy: number;
  angle: number; // in radians
  state: AntState;
  carrying: CarriedItem | null;
  targetTile: { x: number; y: number } | null;
  currentDestination: { x: number; y: number } | null;
  currentTask: string;
  path: Array<{ x: number; y: number }>;
  pathIndex: number;
  actionTimer: number; // For digging duration, tending, etc.
  energy: number; // 0 to 100
  tripsCompleted: number;
  crystalsDiscovered: number;
  legPhase: number;
  antennaeWiggle: number;
  assignedRoomId?: string;
  currentThought: string;
  
  // Bloc 3: Individual agent attributes & local perception
  age: number; // in simulation ticks
  size: number; // relative size metric (0.8 - 1.5)
  speed: number; // movement velocity multiplier
  strength: number; // physical carrying and defense power
  carryCapacity: number; // maximum carry units
  digProficiency: number; // digging efficiency
  perceptionRadius: number; // radius of local vision
  recentActions: AntActionRecord[]; // recent action history (FIFO)
  knownCells: string[]; // local memory of explored cell IDs

  // Bloc 5: Division du travail adaptative & seuils de réponse
  activeTask: AntTaskType;
  taskAffinity: Record<AntTaskType, number>;
  taskExperience: Record<AntTaskType, number>;
  dominantSpecialty: AntTaskType;
  lastTaskSwitchReason: string;
  taskEvaluationTimer?: number;
}

export interface ColonyRoom {
  id: string; // stable room_id
  type: RoomType;
  room_function?: RoomType; // Defaults to 'NONE' for organic chambers
  hasCommandTerminal?: boolean; // Queen command terminal anchored in this room
  commandTerminalPosition?: { x: number; y: number };
  isDesignated?: boolean; // True for player-designed chambers (never overwritten or auto-deleted)
  name: string;
  color: string;
  tiles: Array<{ x: number; y: number }>;
  bounds: { minX: number; maxX: number; minY: number; maxY: number };
  center: { x: number; y: number };
  level: number;
  storedResources: {
    crystal: number;
    crystalDust?: number;
    dirt: number;
    mineral: number;
    resin: number;
  };
  capacity: number;
  entrances?: Array<{ x: number; y: number }>; // Connection points to tunnels
  createdAtTick?: number;
}

export interface DigTask {
  id: string;
  x: number;
  y: number;
  progress: number; // 0 to 1
  assignedAntId?: string;
}

export interface BroodItem {
  id: string;
  type: 'egg' | 'larva' | 'cocoon';
  x: number;
  y: number;
  progress: number; // 0 to 100% until hatching
  tendedBy?: string;
}

export interface StratumInfo {
  id: number;
  name: string;
  depthLabel: string;
  startRow: number;
  endRow: number;
  primaryTile: TileType;
  themeColor: string;
  description: string;
  discoveryBonus: string;
}

export interface ColonyStats {
  crystals: number;
  crystalDust?: number;
  dirt: number;
  minerals: number;
  resin: number;
  totalDugTiles: number;
  deepestDugMeters: number;
  population: number;
  queenHealth: number;
  queenMorale: number;
  resonantEnergy: number;
}

export interface QueenFormulaPriority {
  formulaId: string;
  name: string;
  slot: number;
  priority: number;
}

export interface QueenTerminalState {
  connected: boolean;
  source: string;
  activeLimit: number;
  active: QueenFormulaPriority[];
  queued: QueenFormulaPriority[];
  lastSyncAt: number | null;
}

export interface SharedWorldState {
  connected: boolean;
  source: string;
  worldId: string;
  depth: { width: number; height: number; slices: number; centerZ: number } | null;
  crystalsProduced: number;
  observationsProcessed: number;
  latestCrystalCount: number;
  lastSyncAt: number | null;
}

export type ActiveTool =
  | 'DIG_MANUAL'
  | 'DESIGNATE_DIG'
  | 'DESIGNATE_ROOM'
  | 'INSPECT_ANT'
  | 'PHEROMONE';
