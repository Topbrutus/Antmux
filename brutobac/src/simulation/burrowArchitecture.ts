import { ColonyRoom, RoomType, TileType } from '../types/colony';
import { TerrainCell } from '../types/terrain';
import { GridState, GRID_WIDTH, GRID_HEIGHT, revealRadius } from './grid';
export type { GridState };
import { TunnelNode, TunnelNodeType, DigFront, BurrowStats } from '../types/burrow';

/**
 * Checks if coordinates are valid inside the subterranean grid
 */
export function inBounds(x: number, y: number): boolean {
  return x >= 0 && x < GRID_WIDTH && y >= 0 && y < GRID_HEIGHT;
}

/**
 * Checks if a cell is excavated/walkable
 */
export function isExcavated(grid: GridState, x: number, y: number): boolean {
  if (!inBounds(x, y)) return false;
  return grid.cells[y]?.[x]?.excavated === true || grid.tiles[y]?.[x] === 'AIR';
}

/**
 * Identifies all accessible solid cells bordering existing excavated tunnels/rooms.
 * These are the exact digging fronts available to the colony.
 */
export function getAccessibleDigFronts(grid: GridState): DigFront[] {
  const fronts: DigFront[] = [];
  const visited = new Set<string>();

  const neighbors = [
    { dx: 0, dy: -1 }, // Up
    { dx: 0, dy: 1 },  // Down
    { dx: -1, dy: 0 }, // Left
    { dx: 1, dy: 0 },  // Right
  ];

  for (let y = 7; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      const cell = grid.cells[y]?.[x];
      if (!cell || cell.excavated) continue;

      const key = `${x},${y}`;
      if (visited.has(key)) continue;

      const adjacentExcavated: Array<{ x: number; y: number }> = [];

      for (const { dx, dy } of neighbors) {
        const nx = x + dx;
        const ny = y + dy;
        if (inBounds(nx, ny) && isExcavated(grid, nx, ny)) {
          adjacentExcavated.push({ x: nx, y: ny });
        }
      }

      if (adjacentExcavated.length > 0) {
        visited.add(key);

        // Determine front type based on adjacent tunnel geometry
        let frontType: DigFront['frontType'] = 'EXPLORATION';
        const hasTop = adjacentExcavated.some((p) => p.y === y - 1);
        const hasLeftOrRight = adjacentExcavated.some((p) => p.x !== x);

        if (hasTop && !hasLeftOrRight) {
          frontType = 'DEEPEN_SHAFT';
        } else if (hasLeftOrRight && !hasTop) {
          frontType = 'EXPAND_HORIZONTAL';
        } else if (adjacentExcavated.length >= 2) {
          frontType = 'EXPAND_CAVITY';
        }

        fronts.push({
          x,
          y,
          cell_id: cell.cell_id,
          depth: cell.depth,
          material_type: cell.material_type,
          hardness: cell.hardness,
          resource_type: cell.resource_type,
          resource_amount: cell.resource_amount,
          adjacentExcavated,
          frontType,
        });
      }
    }
  }

  return fronts;
}

/**
 * Classifies subterranean tunnel network topology for each excavated cell:
 * horizontal tunnels, vertical shafts, culs-de-sac, bifurcations, intersections.
 */
export function classifyBurrowTopology(grid: GridState): TunnelNode[] {
  const nodes: TunnelNode[] = [];
  const roomTileMap = new Map<string, string>(); // 'x,y' -> roomId

  for (const r of grid.rooms) {
    for (const t of r.tiles) {
      roomTileMap.set(`${t.x},${t.y}`, r.id);
    }
  }

  for (let y = 7; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      if (!isExcavated(grid, x, y)) continue;

      const up = inBounds(x, y - 1) && isExcavated(grid, x, y - 1);
      const down = inBounds(x, y + 1) && isExcavated(grid, x, y + 1);
      const left = inBounds(x - 1, y) && isExcavated(grid, x - 1, y);
      const right = inBounds(x + 1, y) && isExcavated(grid, x + 1, y);

      const count = (up ? 1 : 0) + (down ? 1 : 0) + (left ? 1 : 0) + (right ? 1 : 0);
      const roomId = roomTileMap.get(`${x},${y}`);

      let type: TunnelNodeType;

      if (roomId) {
        // Part of an established room/chamber
        const touchesTunnel =
          (up && !roomTileMap.has(`${x},${y - 1}`)) ||
          (down && !roomTileMap.has(`${x},${y + 1}`)) ||
          (left && !roomTileMap.has(`${x - 1},${y}`)) ||
          (right && !roomTileMap.has(`${x + 1},${y}`));

        type = touchesTunnel ? 'CHAMBER_ENTRANCE' : 'CHAMBER_INTERIOR';
      } else {
        // Tunnel segment classification
        if (count <= 1) {
          type = 'CUL_DE_SAC'; // Dead-end
        } else if (count === 2) {
          if (left && right) {
            type = 'HORIZONTAL_TUNNEL';
          } else if (up && down) {
            type = 'VERTICAL_SHAFT';
          } else {
            type = 'CORNER';
          }
        } else if (count === 3) {
          type = 'BIFURCATION'; // T-junction
        } else {
          type = 'INTERSECTION'; // 4-way crossroad
        }
      }

      nodes.push({
        x,
        y,
        type,
        neighborsCount: count,
        isEntrance: type === 'CHAMBER_ENTRANCE',
        roomId,
      });
    }
  }

  return nodes;
}

/**
 * Computes architectural statistics of the subterranean burrow
 */
export function getBurrowStats(grid: GridState): BurrowStats {
  const nodes = classifyBurrowTopology(grid);
  const fronts = getAccessibleDigFronts(grid);

  let horiz = 0;
  let vert = 0;
  let culs = 0;
  let bifurc = 0;
  let inter = 0;
  let interior = 0;

  for (const n of nodes) {
    switch (n.type) {
      case 'HORIZONTAL_TUNNEL':
        horiz++;
        break;
      case 'VERTICAL_SHAFT':
        vert++;
        break;
      case 'CUL_DE_SAC':
        culs++;
        break;
      case 'BIFURCATION':
        bifurc++;
        break;
      case 'INTERSECTION':
        inter++;
        break;
      case 'CHAMBER_INTERIOR':
      case 'CHAMBER_ENTRANCE':
        interior++;
        break;
    }
  }

  return {
    totalExcavatedVolume: nodes.length,
    horizontalTunnelLength: horiz,
    verticalShaftLength: vert,
    culDeSacsCount: culs,
    bifurcationsCount: bifurc,
    intersectionsCount: inter,
    cavitiesCount: grid.rooms.filter((r) => r.room_function === 'NONE' || r.type === 'NONE').length,
    chambersCount: grid.rooms.length,
    accessibleFrontsCount: fronts.length,
  };
}

/**
 * Helper to distinguish player-designated or starter chambers from natural unassigned cavities.
 */
export function isDesignatedRoom(room: ColonyRoom): boolean {
  return (
    room.isDesignated === true ||
    room.type !== 'NONE' ||
    (room.room_function !== undefined && room.room_function !== 'NONE')
  );
}

/**
 * Automatic Cavity & Chamber Detection & Life Cycle:
 * - Detects contiguous open cavities (width >= 3 and height >= 3, or clusters >= 8 tiles).
 * - Separates automatic natural cavities from player-designated rooms.
 * - Player-designated rooms (Queen, Nursery, Storage, Crystal Vault, Workshop, Recycling, Guard)
 *   are NEVER deleted, merged, or recreated by automatic cavity detection.
 * - Newly dug cells are NOT automatically added to existing designated rooms (CREUSER != EFFACER UNE SALLE).
 * - Cells already linked to a designated room preserve their stable room_id.
 * - Handles room expansion, entrance recognition, and room mergers ONLY for unassigned organic cavities.
 * - Updates tunnel entrances on designated rooms when newly connected to tunnels.
 */
export function updateBurrowChambers(grid: GridState, currentTick = 0): {
  created: ColonyRoom[];
  expanded: ColonyRoom[];
  merged: ColonyRoom[];
} {
  const created: ColonyRoom[] = [];
  const expanded: ColonyRoom[] = [];
  const merged: ColonyRoom[] = [];

  // 0. Maintain link for all existing designated rooms and collect their tiles
  const designatedRoomMap = new Map<string, ColonyRoom>();
  const designatedTileKeys = new Set<string>();

  for (const r of grid.rooms) {
    if (isDesignatedRoom(r)) {
      r.isDesignated = true;
      designatedRoomMap.set(r.id, r);
      for (const t of r.tiles) {
        designatedTileKeys.add(`${t.x},${t.y}`);
        if (grid.cells[t.y]?.[t.x]) {
          grid.cells[t.y][t.x].room_id = r.id;
        }
      }
    }
  }

  // 1. Find all connected components of excavated cells below surface (y >= 7)
  // EXCLUDING cells that already belong to player-designated rooms!
  const visited = new Set<string>();
  const connectedCavities: Array<Array<{ x: number; y: number }>> = [];

  for (let y = 7; y < GRID_HEIGHT; y++) {
    for (let x = 0; x < GRID_WIDTH; x++) {
      if (!isExcavated(grid, x, y)) continue;

      const key = `${x},${y}`;
      if (visited.has(key)) continue;

      // Strictly exclude cells belonging to designated rooms from automatic cavity formation
      if (designatedTileKeys.has(key)) {
        visited.add(key);
        continue;
      }

      // Flood fill candidate cavity
      const component: Array<{ x: number; y: number }> = [];
      const queue = [{ x, y }];
      visited.add(key);

      while (queue.length > 0) {
        const cur = queue.shift()!;
        component.push(cur);

        const neighbors = [
          { nx: cur.x + 1, ny: cur.y },
          { nx: cur.x - 1, ny: cur.y },
          { nx: cur.x, ny: cur.y + 1 },
          { nx: cur.x, ny: cur.y - 1 },
        ];

        for (const { nx, ny } of neighbors) {
          if (inBounds(nx, ny) && ny >= 7 && isExcavated(grid, nx, ny)) {
            const nKey = `${nx},${ny}`;
            if (!visited.has(nKey) && !designatedTileKeys.has(nKey)) {
              visited.add(nKey);
              queue.push({ x: nx, y: ny });
            }
          }
        }
      }

      // Check if this component has cavity characteristics (area >= 8 and bounding box >= 3x3)
      if (component.length >= 8) {
        let minX = GRID_WIDTH;
        let maxX = 0;
        let minY = GRID_HEIGHT;
        let maxY = 0;

        for (const p of component) {
          minX = Math.min(minX, p.x);
          maxX = Math.max(maxX, p.x);
          minY = Math.min(minY, p.y);
          maxY = Math.max(maxY, p.y);
        }

        // Check for 2D morphological thickness (must contain at least one 2x2 open block)
        const compSet = new Set(component.map((p) => `${p.x},${p.y}`));
        const kernelTiles = new Set<string>();

        for (const p of component) {
          if (
            compSet.has(`${p.x + 1},${p.y}`) &&
            compSet.has(`${p.x},${p.y + 1}`) &&
            compSet.has(`${p.x + 1},${p.y + 1}`)
          ) {
            kernelTiles.add(`${p.x},${p.y}`);
            kernelTiles.add(`${p.x + 1},${p.y}`);
            kernelTiles.add(`${p.x + 1},${p.y + 1}`);
            kernelTiles.add(`${p.x},${p.y + 1}`);
          }
        }

        if (kernelTiles.size >= 4) {
          // Collect kernel tiles and immediate adjacent cavity body tiles
          const cavityTilesList: Array<{ x: number; y: number }> = [];
          for (const p of component) {
            if (kernelTiles.has(`${p.x},${p.y}`)) {
              cavityTilesList.push(p);
            } else {
              let adjacentKernels = 0;
              if (kernelTiles.has(`${p.x + 1},${p.y}`)) adjacentKernels++;
              if (kernelTiles.has(`${p.x - 1},${p.y}`)) adjacentKernels++;
              if (kernelTiles.has(`${p.x},${p.y + 1}`)) adjacentKernels++;
              if (kernelTiles.has(`${p.x},${p.y - 1}`)) adjacentKernels++;
              if (adjacentKernels >= 1) {
                cavityTilesList.push(p);
              }
            }
          }

          if (cavityTilesList.length >= 6) {
            connectedCavities.push(cavityTilesList);
          }
        }
      }
    }
  }

  // 2. Associate cavities with existing UNASSIGNED organic rooms, handle expansion and mergers
  for (const cavityTiles of connectedCavities) {
    const cavitySet = new Set(cavityTiles.map((t) => `${t.x},${t.y}`));

    // Find all existing UNASSIGNED organic rooms that overlap this cavity
    // Designated rooms are strictly excluded so they are never merged, overwritten, or modified
    const overlappingRooms = grid.rooms.filter(
      (r) => !isDesignatedRoom(r) && r.tiles.some((t) => cavitySet.has(`${t.x},${t.y}`))
    );

    if (overlappingRooms.length === 0) {
      // BRAND NEW ORGANIC CAVITY RECOGNIZED!
      let minX = GRID_WIDTH;
      let maxX = 0;
      let minY = GRID_HEIGHT;
      let maxY = 0;

      for (const t of cavityTiles) {
        minX = Math.min(minX, t.x);
        maxX = Math.max(maxX, t.x);
        minY = Math.min(minY, t.y);
        maxY = Math.max(maxY, t.y);
      }

      // Find entrances (cavity tiles that connect to tunnels outside this cavity)
      const entrances: Array<{ x: number; y: number }> = [];
      for (const t of cavityTiles) {
        const neighbors = [
          { x: t.x + 1, y: t.y },
          { x: t.x - 1, y: t.y },
          { x: t.x, y: t.y + 1 },
          { x: t.x, y: t.y - 1 },
        ];
        for (const n of neighbors) {
          if (inBounds(n.x, n.y) && isExcavated(grid, n.x, n.y) && !cavitySet.has(`${n.x},${n.y}`)) {
            entrances.push({ x: t.x, y: t.y });
            break;
          }
        }
      }

      const stableId = `chamber_${minX}_${minY}`;
      const isLarge = cavityTiles.length >= 18;
      const newRoom: ColonyRoom = {
        id: stableId,
        type: 'NONE',
        room_function: 'NONE',
        isDesignated: false,
        name: isLarge ? `Grande Chambre ${grid.rooms.length + 1}` : `Petite Cavité ${grid.rooms.length + 1}`,
        color: isLarge ? '#64748b' : '#78716c',
        tiles: cavityTiles,
        bounds: { minX, maxX, minY, maxY },
        center: {
          x: Math.round((minX + maxX) / 2),
          y: Math.round((minY + maxY) / 2),
        },
        level: 1,
        storedResources: { crystal: 0, dirt: 0, mineral: 0, resin: 0 },
        capacity: cavityTiles.length * 5,
        entrances,
        createdAtTick: currentTick,
      };

      for (const t of cavityTiles) {
        if (grid.cells[t.y]?.[t.x] && !designatedTileKeys.has(`${t.x},${t.y}`)) {
          grid.cells[t.y][t.x].room_id = stableId;
        }
      }

      grid.rooms.push(newRoom);
      created.push(newRoom);
    } else if (overlappingRooms.length === 1) {
      // ORGANIC CAVITY EXPANSION: Organic cavity grows and gains new tiles / entrances
      const room = overlappingRooms[0];
      const previousTileCount = room.tiles.length;

      // Merge tiles
      const mergedSet = new Set(room.tiles.map((t) => `${t.x},${t.y}`));
      cavityTiles.forEach((t) => mergedSet.add(`${t.x},${t.y}`));

      const updatedTiles: Array<{ x: number; y: number }> = [];
      let minX = GRID_WIDTH;
      let maxX = 0;
      let minY = GRID_HEIGHT;
      let maxY = 0;

      mergedSet.forEach((key) => {
        const [sx, sy] = key.split(',').map((n) => parseInt(n, 10));
        updatedTiles.push({ x: sx, y: sy });
        minX = Math.min(minX, sx);
        maxX = Math.max(maxX, sx);
        minY = Math.min(minY, sy);
        maxY = Math.max(maxY, sy);
      });

      // Update entrances
      const entrances: Array<{ x: number; y: number }> = [];
      for (const t of updatedTiles) {
        const neighbors = [
          { x: t.x + 1, y: t.y },
          { x: t.x - 1, y: t.y },
          { x: t.x, y: t.y + 1 },
          { x: t.x, y: t.y - 1 },
        ];
        for (const n of neighbors) {
          if (inBounds(n.x, n.y) && isExcavated(grid, n.x, n.y) && !mergedSet.has(`${n.x},${n.y}`)) {
            entrances.push({ x: t.x, y: t.y });
            break;
          }
        }
      }

      room.tiles = updatedTiles;
      room.bounds = { minX, maxX, minY, maxY };
      room.center = {
        x: Math.round((minX + maxX) / 2),
        y: Math.round((minY + maxY) / 2),
      };
      room.capacity = updatedTiles.length * 5;
      room.entrances = entrances;

      for (const t of updatedTiles) {
        if (grid.cells[t.y]?.[t.x] && !designatedTileKeys.has(`${t.x},${t.y}`)) {
          grid.cells[t.y][t.x].room_id = room.id;
        }
      }

      if (updatedTiles.length > previousTileCount) {
        expanded.push(room);
      }
    } else {
      // ORGANIC CAVITY MERGER: Two or more unassigned rooms merged because excavation connected them!
      overlappingRooms.sort((a, b) => b.tiles.length - a.tiles.length);
      const primaryRoom = overlappingRooms[0];
      const absorbedRooms = overlappingRooms.slice(1);

      const mergedSet = new Set<string>();
      overlappingRooms.forEach((r) => r.tiles.forEach((t) => mergedSet.add(`${t.x},${t.y}`)));
      cavityTiles.forEach((t) => mergedSet.add(`${t.x},${t.y}`));

      // Combine resources
      absorbedRooms.forEach((r) => {
        primaryRoom.storedResources.crystal += r.storedResources.crystal;
        primaryRoom.storedResources.dirt += r.storedResources.dirt;
        primaryRoom.storedResources.mineral += r.storedResources.mineral;
        primaryRoom.storedResources.resin += r.storedResources.resin;
      });

      const updatedTiles: Array<{ x: number; y: number }> = [];
      let minX = GRID_WIDTH;
      let maxX = 0;
      let minY = GRID_HEIGHT;
      let maxY = 0;

      mergedSet.forEach((key) => {
        const [sx, sy] = key.split(',').map((n) => parseInt(n, 10));
        updatedTiles.push({ x: sx, y: sy });
        minX = Math.min(minX, sx);
        maxX = Math.max(maxX, sx);
        minY = Math.min(minY, sy);
        maxY = Math.max(maxY, sy);
      });

      // Update entrances
      const entrances: Array<{ x: number; y: number }> = [];
      for (const t of updatedTiles) {
        const neighbors = [
          { x: t.x + 1, y: t.y },
          { x: t.x - 1, y: t.y },
          { x: t.x, y: t.y + 1 },
          { x: t.x, y: t.y - 1 },
        ];
        for (const n of neighbors) {
          if (inBounds(n.x, n.y) && isExcavated(grid, n.x, n.y) && !mergedSet.has(`${n.x},${n.y}`)) {
            entrances.push({ x: t.x, y: t.y });
            break;
          }
        }
      }

      primaryRoom.tiles = updatedTiles;
      primaryRoom.bounds = { minX, maxX, minY, maxY };
      primaryRoom.center = {
        x: Math.round((minX + maxX) / 2),
        y: Math.round((minY + maxY) / 2),
      };
      primaryRoom.capacity = updatedTiles.length * 5;
      primaryRoom.entrances = entrances;

      for (const t of updatedTiles) {
        if (grid.cells[t.y]?.[t.x] && !designatedTileKeys.has(`${t.x},${t.y}`)) {
          grid.cells[t.y][t.x].room_id = primaryRoom.id;
        }
      }

      // Remove absorbed unassigned rooms from the colony grid
      const absorbedIds = new Set(absorbedRooms.map((r) => r.id));
      grid.rooms = grid.rooms.filter((r) => !absorbedIds.has(r.id));

      merged.push(primaryRoom);
    }
  }

  // 3. Update tunnel entrances on DESIGNATED rooms if newly connected to excavated tunnels
  for (const r of grid.rooms) {
    if (isDesignatedRoom(r)) {
      const roomTileSet = new Set(r.tiles.map((t) => `${t.x},${t.y}`));
      const entrances: Array<{ x: number; y: number }> = [];
      for (const t of r.tiles) {
        const neighbors = [
          { x: t.x + 1, y: t.y },
          { x: t.x - 1, y: t.y },
          { x: t.x, y: t.y + 1 },
          { x: t.x, y: t.y - 1 },
        ];
        for (const n of neighbors) {
          if (inBounds(n.x, n.y) && isExcavated(grid, n.x, n.y) && !roomTileSet.has(`${n.x},${n.y}`)) {
            entrances.push({ x: t.x, y: t.y });
            break;
          }
        }
      }
      r.entrances = entrances;
    }
  }

  return { created, expanded, merged };
}

/**
 * Organic excavation builder: carves a horizontal tunnel
 */
export function digHorizontalTunnel(
  grid: GridState,
  startX: number,
  endX: number,
  y: number,
  tick = 0
): number {
  let dug = 0;
  const minX = Math.max(0, Math.min(startX, endX));
  const maxX = Math.min(GRID_WIDTH - 1, Math.max(startX, endX));

  for (let x = minX; x <= maxX; x++) {
    const cell = grid.cells[y]?.[x];
    if (cell && !cell.excavated) {
      cell.excavated = true;
      cell.hardness = 0;
      cell.material_type = y < 7 ? 'SURFACE' : 'NATURAL_CAVITY';
      cell.modified_at_tick = tick;
      grid.tiles[y][x] = y < 7 ? 'SURFACE_AIR' : 'AIR';
      grid.hardness[y][x] = 0;
      revealRadius(grid.revealed, x, y, 4, grid.cells);
      dug++;
    }
  }

  updateBurrowChambers(grid, tick);
  return dug;
}

/**
 * Organic excavation builder: carves a vertical shaft / well (puits)
 */
export function digVerticalShaft(
  grid: GridState,
  x: number,
  startY: number,
  endY: number,
  width = 1,
  tick = 0
): number {
  let dug = 0;
  const minY = Math.max(7, Math.min(startY, endY));
  const maxY = Math.min(GRID_HEIGHT - 1, Math.max(startY, endY));

  for (let y = minY; y <= maxY; y++) {
    for (let w = 0; w < width; w++) {
      const cx = x + w;
      if (inBounds(cx, y)) {
        const cell = grid.cells[y]?.[cx];
        if (cell && !cell.excavated) {
          cell.excavated = true;
          cell.hardness = 0;
          cell.material_type = 'NATURAL_CAVITY';
          cell.modified_at_tick = tick;
          grid.tiles[y][cx] = 'AIR';
          grid.hardness[y][cx] = 0;
          revealRadius(grid.revealed, cx, y, 4, grid.cells);
          dug++;
        }
      }
    }
  }

  updateBurrowChambers(grid, tick);
  return dug;
}

/**
 * Organic excavation builder: carves a rounded cavity or chamber
 */
export function digOrganicCavity(
  grid: GridState,
  centerX: number,
  centerY: number,
  radiusX: number,
  radiusY: number,
  tick = 0
): number {
  let dug = 0;

  for (let dy = -radiusY; dy <= radiusY; dy++) {
    for (let dx = -radiusX; dx <= radiusX; dx++) {
      const x = centerX + dx;
      const y = centerY + dy;
      if (inBounds(x, y) && y >= 7) {
        if ((dx * dx) / (radiusX * radiusX) + (dy * dy) / (radiusY * radiusY) <= 1.05) {
          const cell = grid.cells[y]?.[x];
          if (cell && !cell.excavated) {
            cell.excavated = true;
            cell.hardness = 0;
            cell.material_type = 'NATURAL_CAVITY';
            cell.modified_at_tick = tick;
            grid.tiles[y][x] = 'AIR';
            grid.hardness[y][x] = 0;
            revealRadius(grid.revealed, x, y, 4, grid.cells);
            dug++;
          }
        }
      }
    }
  }

  updateBurrowChambers(grid, tick);
  return dug;
}
