import { TileType } from '../types/colony';
import { GRID_WIDTH, GRID_HEIGHT, isWalkable } from './grid';

interface Node {
  x: number;
  y: number;
  g: number;
  h: number;
  f: number;
  parent: Node | null;
}

/**
 * Fast A* pathfinding on grid for ants traversing walkable tunnels.
 */
export function findPath(
  startX: number,
  startY: number,
  endX: number,
  endY: number,
  tiles: TileType[][],
  maxSteps: number = 600
): Array<{ x: number; y: number }> | null {
  let sx = Math.round(startX);
  let sy = Math.round(startY);
  const tx = Math.round(endX);
  const ty = Math.round(endY);

  if (sx === tx && sy === ty) return [{ x: tx, y: ty }];

  // Ground level or subterranean only (y >= 7), never sky
  if (tx < 0 || tx >= GRID_WIDTH || ty < 7 || ty >= GRID_HEIGHT) return null;
  if (!isWalkable(tiles[ty]?.[tx])) return null;

  // Ensure start node is walkable; if fractional ant coords were slightly off, snap to closest adjacent walkable tile
  if (sy < 7 || !isWalkable(tiles[sy]?.[sx])) {
    const candidates = [
      { x: sx, y: Math.max(7, sy) },
      { x: sx, y: Math.max(7, sy + 1) },
      { x: sx, y: Math.max(7, sy - 1) },
      { x: sx + 1, y: Math.max(7, sy) },
      { x: sx - 1, y: Math.max(7, sy) },
    ];
    const valid = candidates.find(
      (c) => c.x >= 0 && c.x < GRID_WIDTH && c.y >= 7 && c.y < GRID_HEIGHT && isWalkable(tiles[c.y]?.[c.x])
    );
    if (valid) {
      sx = valid.x;
      sy = valid.y;
    } else {
      return null;
    }
  }

  const openList: Node[] = [];
  const closedSet = new Uint8Array(GRID_WIDTH * GRID_HEIGHT);

  const startNode: Node = {
    x: sx,
    y: sy,
    g: 0,
    h: Math.abs(tx - sx) + Math.abs(ty - sy),
    f: Math.abs(tx - sx) + Math.abs(ty - sy),
    parent: null,
  };

  openList.push(startNode);

  // 4 cardinal directions strictly ensure ants follow excavated tunnel corridors without clipping wall corners
  const dirs = [
    { dx: 1, dy: 0 },
    { dx: -1, dy: 0 },
    { dx: 0, dy: 1 },
    { dx: 0, dy: -1 },
  ];

  let steps = 0;

  while (openList.length > 0 && steps++ < maxSteps) {
    let bestIdx = 0;
    for (let i = 1; i < openList.length; i++) {
      if (openList[i].f < openList[bestIdx].f) {
        bestIdx = i;
      }
    }

    const current = openList.splice(bestIdx, 1)[0];
    const currentIndex = current.y * GRID_WIDTH + current.x;
    closedSet[currentIndex] = 1;

    // Check goal
    if (current.x === tx && current.y === ty) {
      const path: Array<{ x: number; y: number }> = [];
      let curr: Node | null = current;
      while (curr) {
        path.push({ x: curr.x, y: curr.y });
        curr = curr.parent;
      }
      return path.reverse();
    }

    for (const dir of dirs) {
      const nx = current.x + dir.dx;
      const ny = current.y + dir.dy;

      // ny must strictly be >= 7 (subterranean and surface entrance level only, never sky)
      if (nx < 0 || nx >= GRID_WIDTH || ny < 7 || ny >= GRID_HEIGHT) continue;

      const nIndex = ny * GRID_WIDTH + nx;
      if (closedSet[nIndex]) continue;

      if (!isWalkable(tiles[ny]?.[nx])) continue;

      const gScore = current.g + 1.0;
      const hScore = Math.abs(tx - nx) + Math.abs(ty - ny);
      const fScore = gScore + hScore;

      const existing = openList.find((node) => node.x === nx && node.y === ny);
      if (existing) {
        if (gScore < existing.g) {
          existing.g = gScore;
          existing.f = fScore;
          existing.parent = current;
        }
      } else {
        openList.push({
          x: nx,
          y: ny,
          g: gScore,
          h: hScore,
          f: fScore,
          parent: current,
        });
      }
    }
  }

  return null;
}

/**
 * Finds an adjacent walkable tile next to a target solid tile to enable ants to stand next to it and dig.
 */
export function getAdjacentWalkableTile(
  targetX: number,
  targetY: number,
  tiles: TileType[][]
): { x: number; y: number } | null {
  const neighbors = [
    { x: targetX, y: targetY - 1 },
    { x: targetX, y: targetY + 1 },
    { x: targetX - 1, y: targetY },
    { x: targetX + 1, y: targetY },
  ];

  for (const n of neighbors) {
    if (n.x >= 0 && n.x < GRID_WIDTH && n.y >= 7 && n.y < GRID_HEIGHT) {
      if (isWalkable(tiles[n.y]?.[n.x])) {
        return n;
      }
    }
  }
  return null;
}
