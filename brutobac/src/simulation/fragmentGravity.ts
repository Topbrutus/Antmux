import { GRID_HEIGHT, GRID_WIDTH } from './grid';
import { TerrainFragment } from '../types/fragments';
import { TileType } from '../types/colony';

const AIR_TILES = new Set<TileType>(['AIR', 'SURFACE_AIR']);

export function createTerrainFragment(
  id: string,
  x: number,
  y: number,
  material: TerrainFragment['material'],
  crystalDust: number,
  seed = 0
): TerrainFragment {
  const size = 1 + ((Math.abs(seed) + x * 17 + y * 31) % 10);
  return {
    id,
    x,
    y,
    size,
    material,
    mass: Math.max(0.1, size * size * size * 0.001),
    cohesion: Math.min(1, 0.15 + size * 0.06),
    crystalDust: Math.max(0, crystalDust),
    velocityY: 0,
    settled: false,
  };
}

export function advanceTerrainFragments(
  fragments: TerrainFragment[],
  tiles: TileType[][],
  delta: number
): void {
  for (const fragment of fragments) {
    if (fragment.settled) continue;

    const nextY = fragment.y + fragment.velocityY * delta;
    const checkX = Math.max(0, Math.min(GRID_WIDTH - 1, Math.floor(fragment.x)));
    const checkY = Math.floor(nextY + 0.5);
    const below = checkY < GRID_HEIGHT ? tiles[checkY]?.[checkX] : undefined;

    if (below && AIR_TILES.has(below)) {
      fragment.velocityY = Math.min(0.35, fragment.velocityY + (0.018 / Math.max(0.25, fragment.mass)) * delta);
      fragment.y = Math.min(GRID_HEIGHT - 1, nextY);
      continue;
    }

    fragment.y = Math.max(0, Math.min(GRID_HEIGHT - 1, Math.floor(fragment.y) + 0.48));
    fragment.velocityY = 0;
    fragment.settled = true;
  }
}
