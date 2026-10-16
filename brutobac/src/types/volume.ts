import { TileType, ColonyRoom } from './colony';

export const VOLUME_WIDTH = 84;
export const VOLUME_HEIGHT = 125;
export const VOLUME_DEPTH = 84;
export const VOLUME_CENTER_Z = 41;

export interface VolumeTerrain {
  width: number;
  height: number;
  depth: number;
  centerZ: number;
  solid: Uint8Array;
}

export type VolumeTiles = TileType[][];

export interface VolumeSource {
  tiles: TileType[][];
  rooms: ColonyRoom[];
}
