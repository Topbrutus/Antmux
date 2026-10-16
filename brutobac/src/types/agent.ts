import { ResourceType, AntTaskType } from './colony';

export interface AntActionRecord {
  tick: number;
  action: string;
  location?: { x: number; y: number };
}

export interface VisibleCellInfo {
  x: number;
  y: number;
  cell_id: string;
  isWalkable: boolean;
  excavated: boolean;
  hardness: number;
  resource_type: ResourceType | null;
  resource_amount: number;
  hasGroundItem: boolean;
  hasDigTask: boolean;
  isAccessibleFront: boolean;
}

export interface AntInspectionData {
  ant_id: string;
  name: string;
  caste: string;
  age: number;
  ageFormatted: string;
  size: number;
  sizeCategory: string;
  position: { x: number; y: number; depthMeters: number };
  task: string;
  activeTask: AntTaskType;
  activeTaskLabel: string;
  dominantSpecialty: AntTaskType;
  dominantSpecialtyLabel: string;
  taskAffinity: Record<AntTaskType, number>;
  taskExperience: Record<AntTaskType, number>;
  lastTaskSwitchReason: string;
  destination: { x: number; y: number } | null;
  destinationLabel: string;
  load: {
    item: string;
    color?: string;
    amount: number;
    capacity: number;
  };
  aptitudes: {
    strength: number;
    speed: number;
    digProficiency: number;
    carryCapacity: number;
  };
  state: string;
  stateLabel: string;
  recentActions: AntActionRecord[];
}
