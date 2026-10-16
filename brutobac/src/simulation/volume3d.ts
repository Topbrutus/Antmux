import { TileType, ColonyRoom } from '../types/colony';
import {
  VOLUME_CENTER_Z,
  VOLUME_DEPTH,
  VOLUME_HEIGHT,
  VOLUME_WIDTH,
  VolumeSource,
  VolumeTerrain,
  VolumeTiles,
} from '../types/volume';

function indexOf(x: number, y: number, z: number): number {
  return z * VOLUME_WIDTH * VOLUME_HEIGHT + y * VOLUME_WIDTH + x;
}

function roomAt(rooms: ColonyRoom[], x: number, y: number): ColonyRoom | undefined {
  return rooms.find((room) => room.tiles.some((tile) => tile.x === x && tile.y === y));
}

function sliceDepth(room: ColonyRoom): number {
  if (room.type === 'QUEEN') return 10;
  if (room.type === 'CRYSTAL_VAULT') return 12;
  return 6;
}

function isOpenAtDepth(room: ColonyRoom, x: number, y: number, z: number): boolean {
  const depth = Math.abs(z - VOLUME_CENTER_Z);
  const maxDepth = sliceDepth(room);
  if (depth > maxDepth) return false;

  const depthScale = Math.sqrt(Math.max(0, 1 - (depth * depth) / (maxDepth * maxDepth)));
  const horizontalDistance = Math.max(Math.abs(x - room.center.x), Math.abs(y - room.center.y));
  const baseRadius = Math.max(
    1,
    Math.max(room.bounds.maxX - room.bounds.minX, room.bounds.maxY - room.bounds.minY) / 2
  );
  return horizontalDistance <= Math.max(1, baseRadius * depthScale);
}

export function createVolumeFromGrid(source: VolumeSource): VolumeTerrain {
  const solid = new Uint8Array(VOLUME_WIDTH * VOLUME_HEIGHT * VOLUME_DEPTH);

  for (let z = 0; z < VOLUME_DEPTH; z++) {
    for (let y = 0; y < VOLUME_HEIGHT; y++) {
      for (let x = 0; x < VOLUME_WIDTH; x++) {
        const tile = source.tiles[y]?.[x];
        let isSolid = tile !== 'AIR' && tile !== 'SURFACE_AIR';
        const room = roomAt(source.rooms, x, y);

        if (room && tile === 'AIR') {
          isSolid = !isOpenAtDepth(room, x, y, z);
        } else if (!room && tile === 'AIR') {
          isSolid = Math.abs(z - VOLUME_CENTER_Z) > 5;
        }

        solid[indexOf(x, y, z)] = isSolid ? 1 : 0;
      }
    }
  }

  return {
    width: VOLUME_WIDTH,
    height: VOLUME_HEIGHT,
    depth: VOLUME_DEPTH,
    centerZ: VOLUME_CENTER_Z,
    solid,
  };
}

export function isVolumeSolid(volume: VolumeTerrain, x: number, y: number, z: number): boolean {
  if (x < 0 || x >= volume.width || y < 0 || y >= volume.height || z < 0 || z >= volume.depth) return true;
  return volume.solid[indexOf(x, y, z)] === 1;
}

export function getVolumeSliceTiles(
  volume: VolumeTerrain,
  z: number,
  baseTiles: TileType[][]
): VolumeTiles {
  const slice = Array.from({ length: volume.height }, (_, y) =>
    Array.from({ length: volume.width }, (_, x) => {
      if (y < 7) return 'SURFACE_AIR' as TileType;
      if (isVolumeSolid(volume, x, y, z)) return baseTiles[y]?.[x] ?? 'DIRT_HUMUS';
      return 'AIR' as TileType;
    })
  );
  return slice;
}

export function excavateVolumeCell(volume: VolumeTerrain, x: number, y: number, z: number): void {
  if (x < 0 || x >= volume.width || y < 0 || y >= volume.height || z < 0 || z >= volume.depth) return;
  volume.solid[indexOf(x, y, z)] = 0;
}
