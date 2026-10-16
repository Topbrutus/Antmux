import { MaterialType } from './terrain';

export interface TerrainFragment {
  id: string;
  x: number;
  y: number;
  size: number;
  material: MaterialType;
  mass: number;
  cohesion: number;
  crystalDust: number;
  velocityY: number;
  settled: boolean;
}
