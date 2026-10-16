import { MaterialType } from './terrain';
import { ResourceType } from './colony';

export type TunnelNodeType =
  | 'HORIZONTAL_TUNNEL'
  | 'VERTICAL_SHAFT'
  | 'CUL_DE_SAC'
  | 'BIFURCATION'
  | 'INTERSECTION'
  | 'CORNER'
  | 'CHAMBER_INTERIOR'
  | 'CHAMBER_ENTRANCE';

export interface TunnelNode {
  x: number;
  y: number;
  type: TunnelNodeType;
  neighborsCount: number;
  isEntrance: boolean;
  roomId?: string;
}

export interface DigFront {
  x: number;
  y: number;
  cell_id: string;
  depth: number;
  material_type: MaterialType;
  hardness: number;
  resource_type: ResourceType | null;
  resource_amount: number;
  adjacentExcavated: Array<{ x: number; y: number }>;
  frontType: 'EXPAND_HORIZONTAL' | 'DEEPEN_SHAFT' | 'EXPAND_CAVITY' | 'EXPLORATION';
}

export interface BurrowStats {
  totalExcavatedVolume: number;
  horizontalTunnelLength: number;
  verticalShaftLength: number;
  culDeSacsCount: number;
  bifurcationsCount: number;
  intersectionsCount: number;
  cavitiesCount: number;
  chambersCount: number;
  accessibleFrontsCount: number;
}
