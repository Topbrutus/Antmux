import {
  Ant,
  AntCaste,
  AntState,
  GroundItem,
  DigTask,
  ColonyRoom,
  BroodItem,
  CarriedItem,
  ResourceType,
  AntTaskType,
  TASK_LABELS,
  RoomType,
} from '../types/colony';
import {
  GRID_WIDTH,
  GRID_HEIGHT,
  isWalkable,
  revealRadius,
  getAccessibleDigFronts,
  isDesignatedRoom,
  updateBurrowChambers,
} from './grid';
import { DigFront } from '../types/burrow';
import { findPath, getAdjacentWalkableTile } from './pathfinding';
import { soundEngine } from '../audio/soundEngine';
import {
  generateAntAttributes,
  logAntAction,
  getVisibleCells,
  getAntInspectionData,
} from './antAgent';
import { stigmergyEngine } from './stigmergyEngine';
import { PheromoneSignalType } from '../types/stigmergy';
import {
  getInitialTaskAffinities,
  getInitialTaskExperience,
  computeDominantSpecialty,
  evaluateAntTaskSwitch,
  recordTaskCompletion,
} from './divisionOfLabour';
import { GridState } from './grid';
import { DeterministicRNG } from './rng';

const ANT_NAMES: Record<AntCaste, string[]> = {
  QUEEN: ['Reine Séléné Ière', 'Grande Mère Bruta', 'Reine Aurélia'],
  MINER: [
    'Forreuse K-01',
    'Chipeuse Silice',
    'Pic de Schiste',
    'Mandibule Acier',
    'Creuseuse Rox',
    'Perce-Roche',
    'Foreuse Z-9',
    'Terrassière Brune',
    'Filonnière',
  ],
  CARRIER: [
    'Porteuse Atlas',
    'Trotteuse Cristalline',
    'Convoyeur B-12',
    'Lesteuse Topaze',
    'Mule Souterraine',
    'Haleuse Jade',
    'Navetteur C-4',
    'Courrière d’Or',
  ],
  NURSE: [
    'Nourrice Cléo',
    'Couvaison Alba',
    'Veilleuse d’Œufs',
    'Douce Larvaire',
    'Maternelle Flor',
    'Garde-Berceau',
  ],
  BUILDER: [
    'Charpentière Résine',
    'Maçonne Basalte',
    'Architecte V-7',
    'Étayeuse Solide',
    'Plâtrière Glaise',
  ],
  GUARD: [
    'Sentinelle Fauve',
    'Pince d’Ébène',
    'Vigie du Seuil',
    'Cuirassée Noire',
    'Garde de l’Abîme',
  ],
};

let antIdCounter = 1;

export function createAnt(
  caste: AntCaste,
  x: number,
  y: number,
  name?: string,
  forcedSize?: number
): Ant {
  const names = ANT_NAMES[caste] || ['Ouvrière'];
  const assignedName = name || names[Math.floor(Math.random() * names.length)];
  const id = `ant_${antIdCounter++}_${Date.now() % 10000}`;
  const attrs = generateAntAttributes(caste, forcedSize);

  // Bloc 5: Adaptive division of labour initialization
  const taskAffinity = getInitialTaskAffinities(caste);
  const taskExperience = getInitialTaskExperience(caste);
  const dominantSpecialty = computeDominantSpecialty(taskAffinity, taskExperience);

  const initialTaskByCaste: Record<AntCaste, AntTaskType> = {
    QUEEN: 'brood',
    MINER: 'dig',
    CARRIER: 'carry',
    NURSE: 'brood',
    BUILDER: 'build',
    GUARD: 'defense',
  };
  const activeTask = initialTaskByCaste[caste] || 'explore';

  return {
    id,
    ant_id: id,
    name: assignedName,
    caste,
    x,
    y,
    vx: 0,
    vy: 0,
    angle: Math.random() * Math.PI * 2,
    state: caste === 'QUEEN' ? 'RESTING' : 'WANDERING',
    carrying: null,
    targetTile: null,
    currentDestination: null,
    currentTask: caste === 'QUEEN' ? 'Veille sur le destin de la colonie' : TASK_LABELS[activeTask]?.name || 'Exploration de galerie',
    path: [],
    pathIndex: 0,
    actionTimer: 0,
    energy: 100,
    tripsCompleted: 0,
    crystalsDiscovered: 0,
    legPhase: Math.random() * Math.PI * 2,
    antennaeWiggle: 0,
    currentThought: caste === 'QUEEN' ? 'Veille sur le destin de la colonie' : `Début d'activité : ${TASK_LABELS[activeTask]?.name}`,
    
    // Bloc 3: Individual agent attributes
    age: 0,
    size: attrs.size,
    speed: attrs.speed,
    strength: attrs.strength,
    carryCapacity: attrs.carryCapacity,
    digProficiency: attrs.digProficiency,
    perceptionRadius: attrs.perceptionRadius,
    recentActions: [
      {
        tick: 0,
        action: 'Éclosion et intégration à la colonie',
        location: { x: Math.round(x), y: Math.round(y) },
      },
    ],
    knownCells: [`${Math.round(x)},${Math.round(y)}`],

    // Bloc 5: Division du travail adaptative & seuils de réponse
    activeTask,
    taskAffinity,
    taskExperience,
    dominantSpecialty,
    lastTaskSwitchReason: 'Spécialisation initiale selon la caste d’origine',
    taskEvaluationTimer: Math.floor(Math.random() * 30),
  };
}

export function generateInitialAnts(): Ant[] {
  const ants: Ant[] = [];

  // Queen stays beside the command terminal in the Royal Chamber (x=41, y=20)
  ants.push(createAnt('QUEEN', 41, 20, 'Grande Reine Bruta'));

  return ants;
}

/**
 * Updates ant physics, path navigation, and caste-specific behaviors.
 */
export function updateAnt(
  ant: Ant,
  tiles: string[][],
  revealed: boolean[][],
  hardness: number[][],
  rooms: ColonyRoom[],
  groundItems: GroundItem[],
  digTasks: DigTask[],
  broodItems: BroodItem[],
  onResourceMined: (type: ResourceType, count: number, x: number, y: number) => void,
  onResourceDelivered: (type: ResourceType, roomId: string) => void,
  onNewBroodLayed: (x: number, y: number) => void,
  delta: number,
  onCellExcavated?: (x: number, y: number) => void,
  colonyStimuli?: Record<AntTaskType, number>,
  gridState?: GridState,
  onDesignateDig?: (x: number, y: number) => DigTask | null,
  onDesignateRoom?: (centerX: number, centerY: number, roomType: RoomType) => ColonyRoom | null | void
) {
  // 1. Strict subterranean boundary enforcement: Ants never float in the sky (y < 7)
  if (ant.y < 7) {
    ant.y = 7;
    ant.path = [];
    ant.pathIndex = 0;
  }

  // 2. Strict cell walkability validation: Ensure ant is always inside a valid excavated cell
  const curCellX = Math.round(ant.x);
  const curCellY = Math.round(ant.y);
  if (curCellY < 7 || !isWalkable(tiles[curCellY]?.[curCellX] as any)) {
    const candidates = [
      { x: curCellX, y: curCellY },
      { x: curCellX, y: Math.max(7, curCellY + 1) },
      { x: curCellX, y: Math.max(7, curCellY - 1) },
      { x: curCellX + 1, y: Math.max(7, curCellY) },
      { x: curCellX - 1, y: Math.max(7, curCellY) },
    ];
    const valid = candidates.find(
      (c) => c.x >= 0 && c.x < GRID_WIDTH && c.y >= 7 && c.y < GRID_HEIGHT && isWalkable(tiles[c.y]?.[c.x] as any)
    );
    if (valid) {
      ant.x = valid.x;
      ant.y = valid.y;
    } else {
      ant.x = 41;
      ant.y = 20;
    }
    ant.path = [];
    ant.pathIndex = 0;
  }

  // Leg & antennae animation
  ant.legPhase += 0.25 * delta;
  ant.antennaeWiggle = Math.sin(Date.now() * 0.006 + ant.x * 2) * 0.4;
  ant.age = (ant.age || 0) + 1;
  ant.currentDestination = ant.targetTile;
  ant.currentTask = ant.currentThought || TASK_LABELS[ant.activeTask]?.name || 'Activité souterraine';

  // Reveal area around ant as it walks
  const rx = Math.round(ant.x);
  const ry = Math.round(ant.y);
  revealRadius(revealed, rx, ry, 2);

  // Stigmergic virtual pheromone deposits based on active state and task
  if (ant.carrying) {
    const sType: PheromoneSignalType = ant.carrying.type === 'crystal' ? 'CRYSTAL' : 'RESOURCE';
    stigmergyEngine.depositSignal(rx, ry, sType, 2.5);
    stigmergyEngine.depositSignal(rx, ry, 'RETURN', 2.0);
  } else if (ant.activeTask === 'defense' || ant.caste === 'GUARD') {
    stigmergyEngine.depositSignal(rx, ry, 'DEFENSE', 1.0);
  } else if (ant.activeTask === 'brood' || ant.caste === 'NURSE') {
    stigmergyEngine.depositSignal(rx, ry, 'BROOD', 1.0);
  } else if (ant.activeTask === 'dig' && ant.state === 'DIGGING') {
    stigmergyEngine.depositSignal(rx, ry, 'DIG', 3.0);
  } else if (ant.activeTask === 'explore') {
    stigmergyEngine.depositSignal(rx, ry, 'EXPLORE', 0.8);
  }

  // Follow active path if any
  if (ant.path && ant.path.length > 0 && ant.pathIndex < ant.path.length) {
    const target = ant.path[ant.pathIndex];

    // General path safety: verify that the next target waypoint is within subterranean bounds and strictly walkable
    if (target.y < 7 || !isWalkable(tiles[target.y]?.[target.x] as any)) {
      // The next cell is an obstacle / no longer traversable! Cancel path and recalculate if destination exists
      const dest = ant.targetTile;
      ant.path = [];
      ant.pathIndex = 0;
      if (dest && dest.y >= 7 && isWalkable(tiles[dest.y]?.[dest.x] as any)) {
        const recalculated = findPath(ant.x, ant.y, dest.x, dest.y, tiles as any);
        if (recalculated && recalculated.length > 0) {
          ant.path = recalculated;
          ant.pathIndex = 0;
        }
      }
      return;
    }

    const dx = target.x - ant.x;
    const dy = target.y - ant.y;
    const dist = Math.hypot(dx, dy);

    // Movement speed varies by individual speed trait, caste and load
    let baseSpeed = (ant.speed || 0.065) * delta;
    if (ant.caste === 'QUEEN') baseSpeed = 0.02 * delta;
    if (ant.carrying) baseSpeed *= 0.85;

    if (dist < 0.15) {
      ant.x = target.x;
      ant.y = target.y;
      ant.pathIndex++;
      if (ant.pathIndex >= ant.path.length) {
        ant.path = [];
        ant.pathIndex = 0;
      }
    } else {
      const angle = Math.atan2(dy, dx);
      // Smooth turning
      ant.angle = angle;
      const step = Math.min(baseSpeed, dist);
      const nextX = ant.x + Math.cos(angle) * step;
      const nextY = ant.y + Math.sin(angle) * step;

      // Obstacle safety during continuous movement: verify target continuous position does not enter a wall
      const nextCellX = Math.round(nextX);
      const nextCellY = Math.round(nextY);
      if (nextCellY < 7 || !isWalkable(tiles[nextCellY]?.[nextCellX] as any)) {
        // Obstacle ahead: cancel path and attempt to recalculate rather than traversing the obstacle
        const dest = ant.targetTile;
        ant.path = [];
        ant.pathIndex = 0;
        if (dest && dest.y >= 7 && isWalkable(tiles[dest.y]?.[dest.x] as any)) {
          const recalculated = findPath(ant.x, ant.y, dest.x, dest.y, tiles as any);
          if (recalculated && recalculated.length > 0) {
            ant.path = recalculated;
            ant.pathIndex = 0;
          }
        }
        return;
      }

      ant.x = nextX;
      ant.y = nextY;
    }
    return;
  }

  // Bloc 5: Decentralized adaptive task evaluation
  // Queen stays in Queen's chamber. Workers evaluate collective needs & local stimulus.
  if (ant.caste !== 'QUEEN') {
    if (!ant.taskAffinity) {
      ant.taskAffinity = getInitialTaskAffinities(ant.caste);
    }
    if (!ant.taskExperience) {
      ant.taskExperience = getInitialTaskExperience(ant.caste);
    }
    if (!ant.activeTask) {
      ant.activeTask = 'explore';
    }

    // Only switch if free-handed (not currently carrying resources)
    if (!ant.carrying) {
      ant.taskEvaluationTimer = (ant.taskEvaluationTimer || 0) + delta;
      const isFreeToSwitch = ant.state === 'IDLE' || ant.state === 'WANDERING' || ant.state === 'RESTING';
      const switchThreshold = isFreeToSwitch ? 20 : 50;

      if (ant.taskEvaluationTimer >= switchThreshold && colonyStimuli && gridState) {
        ant.taskEvaluationTimer = 0;
        const switchDecision = evaluateAntTaskSwitch(
          ant,
          colonyStimuli,
          gridState,
          digTasks,
          broodItems
        );

        if (switchDecision && switchDecision.newActiveTask !== ant.activeTask) {
          ant.activeTask = switchDecision.newActiveTask;
          ant.lastTaskSwitchReason = switchDecision.reason;
          ant.dominantSpecialty = computeDominantSpecialty(ant.taskAffinity, ant.taskExperience);
          ant.targetTile = null;
          ant.currentDestination = null;
          ant.path = [];
          ant.pathIndex = 0;
          ant.state = 'IDLE';
          ant.currentTask = TASK_LABELS[ant.activeTask]?.name || 'Exploration';
          ant.currentThought = switchDecision.reason;

          logAntAction(
            ant,
            ant.age,
            `Réaffectation adaptative : ${TASK_LABELS[ant.activeTask]?.name} (${switchDecision.reason})`,
            { x: ant.x, y: ant.y }
          );
        }
      }
    }
  }

  // State behavior according to Queen status, Carried load, and Active Task
  if (ant.caste === 'QUEEN') {
    updateQueen(
      ant,
      rooms,
      broodItems,
      onNewBroodLayed,
      delta,
      tiles,
      gridState,
      digTasks,
      onDesignateDig,
      onDesignateRoom
    );
  } else if (ant.carrying) {
    // Delivery takes absolute priority when holding a load
    updateCarrier(ant, tiles, rooms, groundItems, onResourceDelivered, delta);
  } else {
    switch (ant.activeTask) {
      case 'dig':
        updateMiner(
          ant,
          tiles,
          revealed,
          hardness,
          digTasks,
          onResourceMined,
          delta,
          onCellExcavated,
          groundItems
        );
        break;
      case 'carry':
        updateCarrier(ant, tiles, rooms, groundItems, onResourceDelivered, delta);
        break;
      case 'explore':
        updateExplorer(ant, tiles, revealed, delta);
        break;
      case 'build':
        updateBuilder(ant, tiles, rooms, delta);
        break;
      case 'brood':
        updateNurse(ant, tiles, rooms, broodItems, delta);
        break;
      case 'defense':
        updateGuard(ant, tiles, rooms, delta);
        break;
      case 'recycle':
        updateRecycler(ant, tiles, rooms, groundItems, delta);
        break;
      default:
        wanderAnt(ant, tiles, groundItems);
        break;
    }
  }
}

/**
 * Autonomous designation of digging fronts by the Queen.
 * Reuses the existing accessible dig fronts system (getAccessibleDigFronts).
 * At regular intervals or when active dig tasks are too low, the Queen chooses a valid accessible front
 * and creates a digTask identical to manual player designation.
 */
export function evaluateQueenDigOrders(
  queen: Ant | undefined,
  grid: GridState,
  digTasks: DigTask[],
  createDigTask: (x: number, y: number) => DigTask | null,
  minThreshold: number = 3
): DigTask | null {
  if (digTasks.length >= minThreshold) {
    return null;
  }

  // 1. Reuse existing accessible dig fronts system
  const fronts = getAccessibleDigFronts(grid);
  if (!fronts || fronts.length === 0) return null;

  // Helper: check if a tile belongs to an already designated colony room
  const isInsideDesignatedRoom = (x: number, y: number): boolean => {
    if (!grid.rooms || grid.rooms.length === 0) return false;
    return grid.rooms.some((room) =>
      room.tiles.some((t) => t.x === x && t.y === y)
    );
  };

  // 2. Filter fronts: subterranean, solid non-air earth, not already assigned a digTask, not in a designated room
  const candidates = fronts.filter((f) => {
    if (f.y < 7 || f.y >= GRID_HEIGHT || f.x < 0 || f.x >= GRID_WIDTH) return false;
    const tile = grid.tiles[f.y]?.[f.x];
    if (!tile || tile === 'AIR' || tile === 'SURFACE_AIR') return false;
    if (isInsideDesignatedRoom(f.x, f.y)) return false;
    return !digTasks.some((t) => t.x === f.x && t.y === f.y);
  });

  if (candidates.length === 0) return null;

  // 3. Classify front categories to distribute between: deepening, horizontal expansion, and exploration
  type FrontCategory = 'DEEPEN' | 'HORIZONTAL' | 'EXPLORATION';

  const getFrontCategory = (f: DigFront): FrontCategory => {
    if (f.frontType === 'DEEPEN_SHAFT') return 'DEEPEN';
    if (f.frontType === 'EXPAND_HORIZONTAL') return 'HORIZONTAL';
    return 'EXPLORATION';
  };

  // Tally active tasks per category to balance development
  const activeCategoryCounts: Record<FrontCategory, number> = {
    DEEPEN: 0,
    HORIZONTAL: 0,
    EXPLORATION: 0,
  };

  for (const t of digTasks) {
    const match = fronts.find((f) => f.x === t.x && f.y === t.y);
    if (match) {
      activeCategoryCounts[getFrontCategory(match)]++;
    } else {
      const hasTop = t.y > 7 && (grid.tiles[t.y - 1]?.[t.x] === 'AIR' || grid.tiles[t.y - 1]?.[t.x] === 'SURFACE_AIR');
      const hasSides =
        (t.x > 0 && grid.tiles[t.y]?.[t.x - 1] === 'AIR') ||
        (t.x < GRID_WIDTH - 1 && grid.tiles[t.y]?.[t.x + 1] === 'AIR');
      if (hasTop && !hasSides) activeCategoryCounts.DEEPEN++;
      else if (hasSides && !hasTop) activeCategoryCounts.HORIZONTAL++;
      else activeCategoryCounts.EXPLORATION++;
    }
  }

  // 4. Spatial separation: avoid placing multiple digTasks too close to one another (min separation 3.5 tiles)
  const MIN_SEPARATION = 3.5;
  const candidatesWithSpacing = candidates.filter((f) => {
    if (digTasks.length === 0) return true;
    return digTasks.every((t) => Math.hypot(t.x - f.x, t.y - f.y) >= MIN_SEPARATION);
  });

  // Use well-spaced candidates when available, falling back smoothly if the burrow is very compact
  const pool = candidatesWithSpacing.length > 0 ? candidatesWithSpacing : candidates;

  const queenY = queen ? queen.y : 20;

  // 5. Score candidates with balanced multi-criteria evaluation
  const scoredCandidates = pool.map((f) => {
    let score = 25;
    const cat = getFrontCategory(f);

    // A. Strategic category balance: prioritize unrepresented goals to maintain diversity
    const catCount = activeCategoryCounts[cat];
    if (catCount === 0) {
      score += 30; // Strong incentive to distribute across deepening, horizontal, and exploration
    } else {
      score -= catCount * 12; // Avoid over-concentrating in a single front type
    }

    // Inherent value per category
    if (cat === 'DEEPEN') score += 12;
    else if (cat === 'HORIZONTAL') score += 10;
    else if (cat === 'EXPLORATION') score += 10;

    // B. Reasonable preference for interesting resources (without obsessively pulling entire colony)
    if (f.resource_type === 'crystal') score += 18;
    else if (f.resource_type === 'mineral') score += 10;
    else if (f.resource_type === 'resin') score += 8;

    // C. Distance to existing tasks: reward spreading out across different sectors
    if (digTasks.length > 0) {
      const minDist = Math.min(
        ...digTasks.map((t) => Math.hypot(t.x - f.x, t.y - f.y))
      );
      if (minDist < 3.5) {
        score -= 40; // Discourage adjacent clustering
      } else {
        score += Math.min(15, (minDist - 3.5) * 2.5); // Reward healthy spacing
      }
    }

    // D. Organic downward exploration gradient: gentle preference for expanding downwards from Queen
    if (f.y > queenY) {
      score += Math.min(15, (f.y - queenY) * 0.35);
    }

    // E. Rock hardness consideration: accessible soft/clay earth requires less energy than dense rock
    if (f.hardness) {
      score += Math.max(0, (2.0 - f.hardness) * 4);
    }

    return { front: f, score, category: cat };
  });

  // Sort descending by score
  scoredCandidates.sort((a, b) => b.score - a.score);

  // 6. Deterministic selection among the top viable candidates (avoid always taking the first best score)
  const bestScore = scoredCandidates[0].score;
  const topTier = scoredCandidates.filter((c) => c.score >= bestScore - 12).slice(0, 4);

  // Derive a 100% deterministic pseudo-random seed from world_seed, currentTick, queen, and task states
  const worldSeed = grid.worldSeed || 3861;
  const tick = grid.currentTick || 0;
  const queenAge = queen ? queen.age : 0;
  let taskHash = 0;
  for (let i = 0; i < digTasks.length; i++) {
    taskHash = (taskHash * 31 + digTasks[i].x * 17 + digTasks[i].y * 13 + (i + 1) * 7) | 0;
  }
  const decisionSeed =
    ((worldSeed ^ ((tick * 1103515245 + queenAge * 2654435761 + taskHash * 1013904223 + 17) >>> 0)) >>> 0);

  const rng = new DeterministicRNG(decisionSeed);
  const chosenIndex = rng.nextInt(0, topTier.length - 1);
  const chosen = topTier[chosenIndex].front;

  // 7. Create the exact same digTask
  const task = createDigTask(chosen.x, chosen.y);

  if (task && queen) {
    const catLabel =
      chosen.frontType === 'DEEPEN_SHAFT'
        ? 'd’approfondissement'
        : chosen.frontType === 'EXPAND_HORIZONTAL'
        ? 'd’expansion latérale'
        : 'd’exploration organique';

    queen.currentThought = `Ordonne un front ${catLabel} en (${chosen.x}, ${chosen.y})`;
    logAntAction(
      queen,
      queen.age,
      `Désignation d'un front ${catLabel} en (${chosen.x}, ${chosen.y})`,
      { x: chosen.x, y: chosen.y }
    );
  }

  return task;
}

/**
 * Structured command interface for Queen room designation.
 * Decoupled so JEV or high-level AI can directly produce orders without modifying game engine internals.
 */
export interface QueenRoomOrder {
  cavityId: string;
  centerX: number;
  centerY: number;
  roomType: RoomType;
  reason: string;
}

export const QUEEN_ALLOWED_ROOM_TYPES: RoomType[] = [
  'QUEEN',
  'NURSERY',
  'CRYSTAL_VAULT',
  'STORAGE',
  'WORKSHOP',
  'RECYCLING',
  'GUARD_POST',
];

/**
 * Identifies all unassigned excavated cavities available for room designation.
 * Strictly ignores solid, unexcavated, inaccessible, or already designated rooms.
 */
export function getAvailableCavities(grid: GridState): ColonyRoom[] {
  // Ensure all newly excavated cavities are recognized
  updateBurrowChambers(grid, grid.currentTick || 0);

  // Set of all tiles currently belonging to already designated rooms
  const designatedTileKeys = new Set<string>();
  for (const r of grid.rooms) {
    if (isDesignatedRoom(r)) {
      for (const t of r.tiles) {
        designatedTileKeys.add(`${t.x},${t.y}`);
      }
    }
  }

  return grid.rooms.filter((room) => {
    // 1. Must NOT be an already designated room
    if (isDesignatedRoom(room)) return false;

    // 2. Must contain valid tiles (minimum 4 tiles for a functional chamber)
    if (!room.tiles || room.tiles.length < 4) return false;

    // 3. Must be completely subterranean (y >= 7) and fully excavated AIR
    const allExcavatedAir = room.tiles.every((t) => {
      if (t.y < 7 || t.y >= GRID_HEIGHT || t.x < 0 || t.x >= GRID_WIDTH) return false;
      const tile = grid.tiles[t.y]?.[t.x];
      return tile === 'AIR' || tile === 'SURFACE_AIR';
    });
    if (!allExcavatedAir) return false;

    // 4. Must not overlap with any tile of an existing designated room
    const overlapsDesignated = room.tiles.some((t) =>
      designatedTileKeys.has(`${t.x},${t.y}`)
    );
    if (overlapsDesignated) return false;

    // 5. Must be accessible from the burrow network (has at least 1 entrance or adjacent tunnel connection)
    const isAccessible =
      (room.entrances && room.entrances.length > 0) ||
      room.tiles.some((t) => {
        const neighbors = [
          { x: t.x + 1, y: t.y },
          { x: t.x - 1, y: t.y },
          { x: t.x, y: t.y + 1 },
          { x: t.x, y: t.y - 1 },
        ];
        return neighbors.some(
          (n) =>
            n.x >= 0 &&
            n.x < GRID_WIDTH &&
            n.y >= 7 &&
            n.y < GRID_HEIGHT &&
            (grid.tiles[n.y]?.[n.x] === 'AIR' || grid.tiles[n.y]?.[n.x] === 'SURFACE_AIR') &&
            !room.tiles.some((rt) => rt.x === n.x && rt.y === n.y)
        );
      });

    return isAccessible;
  });
}

/**
 * Local Queen decision logic:
 * Evaluates available cavities and determines the most appropriate room type
 * based on depth, surrounding resources, size, and colony strategic balance.
 * Prepared cleanly behind a structured command interface so that JEV can
 * later substitute or drive decisions without altering the engine.
 */
export function decideQueenRoomOrder(
  queen: Ant | undefined,
  grid: GridState
): QueenRoomOrder | null {
  const cavities = getAvailableCavities(grid);
  if (cavities.length === 0) return null;

  // Tally current designated rooms by type
  const counts: Record<RoomType, number> = {
    NONE: 0,
    QUEEN: 0,
    NURSERY: 0,
    STORAGE: 0,
    CRYSTAL_VAULT: 0,
    WORKSHOP: 0,
    RECYCLING: 0,
    GUARD_POST: 0,
  };

  for (const r of grid.rooms) {
    if (isDesignatedRoom(r)) {
      counts[r.type] = (counts[r.type] || 0) + 1;
    }
  }

  // Evaluate each cavity and candidate room type to find the best assignment
  let bestCandidate: {
    cavity: ColonyRoom;
    roomType: RoomType;
    score: number;
    reason: string;
  } | null = null;

  for (const cavity of cavities) {
    const depth = cavity.center.y;
    const area = cavity.tiles.length;
    const depthMeters = Math.round(depth * 0.52);

    // Analyze nearby geological context in a 6-tile radius around cavity center
    let nearbyCrystals = 0;
    let nearbyMinerals = 0;
    const r = 6;
    const minX = Math.max(0, cavity.center.x - r);
    const maxX = Math.min(GRID_WIDTH - 1, cavity.center.x + r);
    const minY = Math.max(7, cavity.center.y - r);
    const maxY = Math.min(GRID_HEIGHT - 1, cavity.center.y + r);

    for (let cy = minY; cy <= maxY; cy++) {
      for (let cx = minX; cx <= maxX; cx++) {
        const t = grid.tiles[cy]?.[cx];
        const c = grid.cells[cy]?.[cx];
        if (t === 'VEIN_CRYSTAL' || c?.resource_type === 'crystal') nearbyCrystals++;
        if (t === 'VEIN_MINERAL' || t === 'STONE_MINERAL' || c?.resource_type === 'mineral') nearbyMinerals++;
      }
    }

    for (const type of QUEEN_ALLOWED_ROOM_TYPES) {
      let score = 20;
      let reason = '';

      switch (type) {
        case 'QUEEN':
          // Queen chamber: absolute priority if none exists, otherwise do not duplicate
          if (counts.QUEEN === 0) {
            score = 1000;
            reason = 'Établissement de la Chambre Royale souveraine';
          } else {
            score = -100;
            reason = 'Chambre Royale déjà établie';
          }
          break;

        case 'GUARD_POST':
          score = 25;
          if (depth <= 16) {
            // Near surface entrance: crucial defensive checkpoint
            score += 45;
            reason = `Aménagement d'un avant-poste de garde au seuil de surface (-${depthMeters}m)`;
          } else if (depth >= 85) {
            // Deep subterranean abyss threshold
            score += 35;
            reason = `Aménagement d'un avant-poste de garde face aux profondeurs (-${depthMeters}m)`;
          } else {
            reason = `Aménagement d'une vigie de garde à -${depthMeters}m`;
          }
          if (counts.GUARD_POST === 0) score += 30;
          else if (counts.GUARD_POST >= 2) score -= 25;
          break;

        case 'CRYSTAL_VAULT':
          score = 20;
          if (nearbyCrystals > 0) {
            score += Math.min(45, nearbyCrystals * 8);
          }
          if (depth >= 55) {
            score += 30;
          } else if (depth >= 35) {
            score += 15;
          }
          if (counts.CRYSTAL_VAULT === 0) score += 35;
          else if (counts.CRYSTAL_VAULT >= 3) score -= 20;
          reason = `Aménagement d'une réserve aux cristaux sécurisée à -${depthMeters}m`;
          break;

        case 'NURSERY':
          score = 22;
          // Nurseries thrive in warm, secure mid-depth strata close to Queen (depth 12 - 32)
          if (depth >= 12 && depth <= 32) {
            score += 35;
            reason = `Aménagement d'une nurserie pour le couvain en zone tempérée (-${depthMeters}m)`;
          } else {
            score -= 10;
            reason = `Aménagement d'une nurserie secondaire (-${depthMeters}m)`;
          }
          if (counts.NURSERY === 0) score += 40;
          else if (counts.NURSERY === 1) score += 10;
          else if (counts.NURSERY >= 2) score -= 25;
          break;

        case 'STORAGE':
          score = 25;
          if (area >= 12) score += 20; // Spacious cavity is great for bulk materials
          if (depth >= 15 && depth <= 60) score += 15;
          if (counts.STORAGE === 0) score += 35;
          else if (counts.STORAGE < 2) score += 20;
          else if (counts.STORAGE >= 3) score -= 15;
          reason = `Aménagement d'un entrepôt de stockage de matériaux (${area} alvéoles)`;
          break;

        case 'WORKSHOP':
          score = 20;
          if (nearbyMinerals > 0) score += 25;
          if (depth >= 20 && depth <= 65) score += 15;
          if (counts.WORKSHOP === 0) score += 30;
          else if (counts.WORKSHOP < 2) score += 15;
          else if (counts.WORKSHOP >= 2) score -= 20;
          reason = `Aménagement d'un atelier Brutoficateur de manufacture (-${depthMeters}m)`;
          break;

        case 'RECYCLING':
          score = 18;
          if (counts.RECYCLING === 0) score += 30;
          else if (counts.RECYCLING < 2) score += 10;
          else if (counts.RECYCLING >= 2) score -= 25;
          reason = `Aménagement d'une chambre de compostage et recyclage (-${depthMeters}m)`;
          break;
      }

      // Bonus for larger, well-formed cavities
      if (area >= 8) score += Math.min(15, area * 0.8);

      if (!bestCandidate || score > bestCandidate.score) {
        bestCandidate = {
          cavity,
          roomType: type,
          score,
          reason,
        };
      }
    }
  }

  if (!bestCandidate || bestCandidate.score < 20) return null;

  return {
    cavityId: bestCandidate.cavity.id,
    centerX: bestCandidate.cavity.center.x,
    centerY: bestCandidate.cavity.center.y,
    roomType: bestCandidate.roomType,
    reason: bestCandidate.reason,
  };
}

/**
 * Executes a QueenRoomOrder by invoking the existing room designation system.
 * Transparent and modular: callable by either the local Queen decision logic
 * or later by JEV without modifying game engine internals.
 */
export function executeQueenRoomOrder(
  order: QueenRoomOrder,
  grid: GridState,
  designateRoom: (centerX: number, centerY: number, roomType: RoomType) => ColonyRoom | null | void,
  queen?: Ant
): ColonyRoom | null {
  // 1. Boundary & subterranean check
  if (
    order.centerX < 0 ||
    order.centerX >= GRID_WIDTH ||
    order.centerY < 7 ||
    order.centerY >= GRID_HEIGHT
  ) {
    return null;
  }

  // 2. Solid earth or non-excavated check: never designate unexcavated / solid zone
  const targetTile = grid.tiles[order.centerY]?.[order.centerX];
  if (targetTile !== 'AIR' && targetTile !== 'SURFACE_AIR') {
    return null;
  }

  // 3. Safety check: never overwrite an already designated room
  const existingDesignated = grid.rooms.find(
    (r) =>
      isDesignatedRoom(r) &&
      r.tiles.some((t) => t.x === order.centerX && t.y === order.centerY)
  );
  if (existingDesignated) {
    return null; // Refuse to overwrite or replace existing designated rooms
  }

  // 4. Call the current designating system
  const designated = designateRoom(order.centerX, order.centerY, order.roomType);

  // 5. Queen feedback & action logging
  if (queen) {
    queen.currentThought = order.reason;
    logAntAction(
      queen,
      queen.age,
      order.reason,
      { x: order.centerX, y: order.centerY }
    );
  }

  // 6. Return designated room object
  if (designated && typeof designated === 'object' && 'id' in designated) {
    return designated as ColonyRoom;
  }

  return (
    grid.rooms.find(
      (r) =>
        isDesignatedRoom(r) &&
        r.tiles.some((t) => t.x === order.centerX && t.y === order.centerY)
    ) || null
  );
}

/**
 * REINE → examine et choisit une cavité existante → choisit un type de salle → appelle le système actuel "Aménager salle".
 */
export function evaluateQueenRoomOrders(
  queen: Ant | undefined,
  grid: GridState,
  designateRoom: (centerX: number, centerY: number, roomType: RoomType) => ColonyRoom | null | void
): ColonyRoom | null {
  const order = decideQueenRoomOrder(queen, grid);
  if (!order) return null;
  return executeQueenRoomOrder(order, grid, designateRoom, queen);
}

function updateQueen(
  ant: Ant,
  rooms: ColonyRoom[],
  broodItems: BroodItem[],
  onNewBroodLayed: (x: number, y: number) => void,
  delta: number,
  tiles: string[][],
  grid?: GridState,
  digTasks?: DigTask[],
  onDesignateDig?: (x: number, y: number) => DigTask | null,
  onDesignateRoom?: (centerX: number, centerY: number, roomType: RoomType) => ColonyRoom | null | void
) {
  const queenRoom = rooms.find((r) => r.type === 'QUEEN');
  if (!queenRoom) return;

  const terminal = queenRoom.commandTerminalPosition ?? { x: queenRoom.center.x + 1, y: queenRoom.center.y };

  ant.actionTimer += delta;

  // Gentle wandering inside queen chamber using real pathfinding
  if (ant.actionTimer % 180 < 1 && (!ant.path || ant.path.length === 0)) {
    // 1. Choose a traversable destination strictly within the Queen's Chamber
    const validTiles = queenRoom.tiles.filter(
      (t) =>
        t.y >= 7 &&
        Math.abs(t.x - terminal.x) + Math.abs(t.y - terminal.y) <= 1 &&
        isWalkable(tiles[t.y]?.[t.x] as any)
    );

    if (validTiles.length > 0) {
      const curX = Math.round(ant.x);
      const curY = Math.round(ant.y);
      // Exclude current tile so the queen picks a new spot
      const destinationCandidates = validTiles.filter(
        (t) => t.x !== curX || t.y !== curY
      );
      const candidatesToUse = destinationCandidates.length > 0 ? destinationCandidates : validTiles;
      const randomTile = candidatesToUse[Math.floor(Math.random() * candidatesToUse.length)];

      if (curX !== randomTile.x || curY !== randomTile.y) {
        // 2. Compute real path from current position to destination using findPath()
        const path = findPath(ant.x, ant.y, randomTile.x, randomTile.y, tiles as any);
        if (path && path.length > 0) {
          // 3. Ensure the Queen strictly stays in the Royal Chamber and follows only walkable cells
          const isQueenRoomTile = (x: number, y: number) =>
            queenRoom.tiles.some((qt) => qt.x === x && qt.y === y);

          const staysInChamberAndWalkable = path.every(
            (p) => isWalkable(tiles[p.y]?.[p.x] as any) && isQueenRoomTile(p.x, p.y)
          );

          if (staysInChamberAndWalkable) {
            ant.path = path;
            ant.pathIndex = 0;
            ant.targetTile = { x: randomTile.x, y: randomTile.y };
            ant.currentThought = 'Supervise l’harmonie des ouvrières';
          }
        }
        // If no valid path exists, ant.path is not modified and no teleportation occurs
      }
    }
  }

  // Periodic Egg Laying (every ~20 seconds at normal speed)
  if (ant.actionTimer > 400 && broodItems.length < 15) {
    ant.actionTimer = 0;
    ant.currentThought = 'Dépose un nouvel œuf royal pour la colonie';
    soundEngine.playQueenPulse();
    // Lay egg at queen position or nearby nursery
    const nursery = rooms.find((r) => r.type === 'NURSERY');
    const targetX = nursery ? nursery.center.x : ant.x;
    const targetY = nursery ? nursery.center.y : ant.y;
    onNewBroodLayed(targetX, targetY);
  }

  // Periodic autonomous dig front designation when active tasks are too low
  if (grid && digTasks && onDesignateDig && digTasks.length < 3) {
    if (ant.actionTimer % 90 < delta) {
      evaluateQueenDigOrders(ant, grid, digTasks, onDesignateDig, 3);
    }
  }

  // Periodic autonomous room evaluation: if unassigned cavities exist, Queen designates according to colony needs
  if (grid && onDesignateRoom) {
    if (ant.actionTimer % 180 < delta) {
      evaluateQueenRoomOrders(ant, grid, onDesignateRoom);
    }
  }
}

function updateMiner(
  ant: Ant,
  tiles: string[][],
  revealed: boolean[][],
  hardness: number[][],
  digTasks: DigTask[],
  onResourceMined: (type: ResourceType, count: number, x: number, y: number) => void,
  delta: number,
  onCellExcavated?: (x: number, y: number) => void,
  groundItems?: GroundItem[]
) {
  // If currently digging
  if (ant.state === 'DIGGING' && ant.targetTile) {
    const { x, y } = ant.targetTile;
    ant.currentThought = `Excavation active de la roche en (${x}, ${y})`;
    ant.actionTimer += delta;

    // Small chipping sound & vibration
    if (Math.random() < 0.04) {
      soundEngine.playDig(tiles[y]?.[x] === 'STONE_MINERAL' || tiles[y]?.[x] === 'VEIN_CRYSTAL');
    }

    // Dig efficiency based on individual ant's proficiency
    hardness[y][x] -= 0.02 * (ant.digProficiency || 1.0) * delta;

    if (hardness[y][x] <= 0) {
      // Tile broken!
      const oldType = tiles[y][x];
      tiles[y][x] = 'AIR';
      hardness[y][x] = 0;
      revealRadius(revealed, x, y, 4);

      if (onCellExcavated) {
        onCellExcavated(x, y);
      }

      logAntAction(ant, ant.age, `Roche forée avec succès en (${x}, ${y})`, { x, y });
      recordTaskCompletion(ant, 'dig', 1.0);

      // Remove task
      const taskIdx = digTasks.findIndex((t) => t.x === x && t.y === y);
      if (taskIdx >= 0) digTasks.splice(taskIdx, 1);

      // Reward resources according to mined tile:
      // If onCellExcavated is present, it liberates the deterministic pre-stored matter.
      // Otherwise fallback for isolated testing harnesses.
      if (!onCellExcavated) {
        if (oldType === 'VEIN_CRYSTAL') {
          soundEngine.playCrystalChime(1.2);
          ant.crystalsDiscovered += 2;
          onResourceMined('crystal', 2, x, y);
        } else if (oldType === 'VEIN_MINERAL' || oldType === 'STONE_MINERAL') {
          onResourceMined('mineral', 2, x, y);
        } else if (oldType === 'VEIN_ORGANIC') {
          onResourceMined('resin', 1, x, y);
          onResourceMined('dirt', 2, x, y);
        } else {
          onResourceMined('dirt', 1, x, y);
        }
      } else if (oldType === 'VEIN_CRYSTAL') {
        ant.crystalsDiscovered += 1;
      }

      ant.state = 'IDLE';
      ant.targetTile = null;
      ant.actionTimer = 0;
      ant.currentThought = 'Roche creusée avec succès ! Recherche prochaine cible';
    }
    return;
  }

  // Look for nearest dig task
  if (digTasks.length > 0) {
    let closestTask: DigTask | null = null;
    let closestDist = Infinity;

    for (const task of digTasks) {
      const dist = Math.hypot(task.x - ant.x, task.y - ant.y);
      if (dist < closestDist) {
        closestDist = dist;
        closestTask = task;
      }
    }

    if (closestTask) {
      const standTile = getAdjacentWalkableTile(closestTask.x, closestTask.y, tiles as any);
      if (standTile) {
        // If already adjacent
        const d = Math.hypot(standTile.x - ant.x, standTile.y - ant.y);
        if (d <= 1.2) {
          ant.state = 'DIGGING';
          ant.targetTile = { x: closestTask.x, y: closestTask.y };
          ant.angle = Math.atan2(closestTask.y - ant.y, closestTask.x - ant.x);
          return;
        }

        // Navigate to stand tile
        const path = findPath(ant.x, ant.y, standTile.x, standTile.y, tiles as any);
        if (path && path.length > 0) {
          ant.path = path;
          ant.pathIndex = 0;
          ant.state = 'MOVING_TO_DIG';
          ant.targetTile = { x: closestTask.x, y: closestTask.y };
          ant.currentThought = 'En route vers la roche désignée';
          return;
        }
      }
    }
  }

  // If no active dig task, opportunistically pick up nearby loose earth or dust to clear the front
  if (groundItems && groundItems.length > 0) {
    const nearbyLoose = groundItems.find(
      (it) => (!it.reservedBy || it.reservedBy === ant.id) && Math.hypot(it.x - ant.x, it.y - ant.y) < 1.8
    );
    if (nearbyLoose) {
      ant.carrying = {
        type: nearbyLoose.type,
        color: nearbyLoose.color,
        name: nearbyLoose.name,
      };
      const idx = groundItems.findIndex((it) => it.id === nearbyLoose.id);
      if (idx >= 0) groundItems.splice(idx, 1);
      ant.state = 'CARRYING';
      ant.path = [];
      ant.pathIndex = 0;
      ant.currentThought = `Déblaye ${ant.carrying.name} du front de creusage`;
      return;
    }
  }

  // Wander or rest if no tasks
  wanderAnt(ant, tiles, groundItems);
}

function updateCarrier(
  ant: Ant,
  tiles: string[][],
  rooms: ColonyRoom[],
  groundItems: GroundItem[],
  onResourceDelivered: (type: ResourceType, roomId: string) => void,
  delta: number
) {
  // If carrying a resource, path to destination room
  if (ant.carrying) {
    let targetRoom: ColonyRoom | undefined;

    if (ant.carrying.type === 'crystal' || ant.carrying.type === 'crystal_dust') {
      targetRoom = rooms.find((r) => r.type === 'CRYSTAL_VAULT') || rooms.find((r) => r.type === 'STORAGE');
    } else if (ant.carrying.type === 'mineral' || ant.carrying.type === 'dirt') {
      targetRoom = rooms.find((r) => r.type === 'STORAGE') || rooms.find((r) => r.type === 'WORKSHOP');
    } else if (ant.carrying.type === 'resin') {
      targetRoom = rooms.find((r) => r.type === 'WORKSHOP') || rooms.find((r) => r.type === 'STORAGE');
    }

    if (!targetRoom && rooms.length > 0) {
      targetRoom = rooms[0];
    }

    if (targetRoom) {
      const distToRoom = Math.hypot(targetRoom.center.x - ant.x, targetRoom.center.y - ant.y);
      if (distToRoom < 2.0) {
        // Deposit!
        soundEngine.playDeposit();
        if (ant.carrying.type === 'crystal' || ant.carrying.type === 'crystal_dust') {
          soundEngine.playCrystalChime(1.5);
        }
        onResourceDelivered(ant.carrying.type, targetRoom.id);
        ant.carrying = null;
        ant.tripsCompleted++;
        ant.state = 'IDLE';
        ant.currentThought = `Matériau déposé à la ${targetRoom.name}`;
        logAntAction(ant, ant.age, `Ressource acheminée avec succès vers ${targetRoom.name}`, { x: ant.x, y: ant.y });
        recordTaskCompletion(ant, 'carry', 1.0);
        return;
      }

      // If not navigating towards room, plan path
      if (!ant.path || ant.path.length === 0) {
        const path = findPath(ant.x, ant.y, targetRoom.center.x, targetRoom.center.y, tiles as any);
        if (path) {
          ant.path = path;
          ant.pathIndex = 0;
          ant.currentThought = `Transporte ${ant.carrying.name} vers ${targetRoom.name}`;
        }
      }
    }
    return;
  }

  // Search for ground item to pick up
  const availableItems = groundItems.filter(
    (item) => !item.reservedBy || item.reservedBy === ant.id
  );

  if (availableItems.length > 0) {
    let closestItem: GroundItem | null = null;
    let closestDist = Infinity;

    for (const item of availableItems) {
      const dist = Math.hypot(item.x - ant.x, item.y - ant.y);
      if (dist < closestDist) {
        closestDist = dist;
        closestItem = item;
      }
    }

    if (closestItem) {
      if (closestDist < 1.0) {
        // Pick it up!
        ant.carrying = {
          type: closestItem.type,
          color: closestItem.color,
          name: closestItem.name,
        };
        // Remove from ground items
        const itemIdx = groundItems.findIndex((it) => it.id === closestItem?.id);
        if (itemIdx >= 0) groundItems.splice(itemIdx, 1);

        ant.state = 'CARRYING';
        ant.path = [];
        ant.pathIndex = 0;
        ant.currentThought = `Porte ${ant.carrying.name} sur la tête`;
        return;
      }

      // Navigate to item
      if (!ant.path || ant.path.length === 0) {
        const path = findPath(ant.x, ant.y, closestItem.x, closestItem.y, tiles as any);
        if (path) {
          closestItem.reservedBy = ant.id;
          ant.path = path;
          ant.pathIndex = 0;
          ant.currentThought = `Va ramasser ${closestItem.name}`;
          return;
        }
      }
    }
  }

  wanderAnt(ant, tiles);
}

function updateNurse(
  ant: Ant,
  tiles: string[][],
  rooms: ColonyRoom[],
  broodItems: BroodItem[],
  delta: number
) {
  const nursery = rooms.find((r) => r.type === 'NURSERY');
  if (!nursery) {
    wanderAnt(ant, tiles);
    return;
  }

  // Head to nursery if far
  const dist = Math.hypot(nursery.center.x - ant.x, nursery.center.y - ant.y);
  if (dist > 4 && (!ant.path || ant.path.length === 0)) {
    const path = findPath(ant.x, ant.y, nursery.center.x, nursery.center.y, tiles as any);
    if (path) {
      ant.path = path;
      ant.pathIndex = 0;
      ant.currentThought = 'Rejoint le couvain pour soigner les larves';
    }
    return;
  }

  // In nursery, tend brood
  if (broodItems.length > 0) {
    const unTended = broodItems.find((b) => !b.tendedBy || b.tendedBy === ant.id);
    if (unTended) {
      unTended.tendedBy = ant.id;
      unTended.progress += 0.08 * delta;
      ant.currentThought = `Prend soin d'une jeune larve (croissance: ${Math.round(unTended.progress)}%)`;
      if (Math.random() < 0.04) {
        recordTaskCompletion(ant, 'brood', 0.4);
      }
    }
  } else {
    ant.currentThought = 'Veille sur les cellules du berceau';
  }

  if (Math.random() < 0.01 && (!ant.path || ant.path.length === 0)) {
    const validTiles = nursery.tiles.filter(
      (t) => t.y >= 7 && isWalkable(tiles[t.y]?.[t.x] as any)
    );
    if (validTiles.length > 0) {
      const randomTile = validTiles[Math.floor(Math.random() * validTiles.length)];
      const path = findPath(ant.x, ant.y, randomTile.x, randomTile.y, tiles as any);
      if (path && path.length > 0) {
        ant.path = path;
        ant.pathIndex = 0;
      }
    }
  }
}

function updateBuilder(ant: Ant, tiles: string[][], rooms: ColonyRoom[], delta: number) {
  const workshop = rooms.find((r) => r.type === 'WORKSHOP');
  ant.actionTimer += delta;

  if (workshop && Math.random() < 0.02) {
    ant.currentThought = 'Confectionne des étayages pour les galeries profondes';
    recordTaskCompletion(ant, 'build', 0.25);
  } else {
    ant.currentThought = 'Inspecte la solidité des parois de terre';
    if (Math.random() < 0.01) {
      recordTaskCompletion(ant, 'build', 0.15);
    }
  }

  wanderAnt(ant, tiles);
}

function updateGuard(ant: Ant, tiles: string[][], rooms: ColonyRoom[], delta: number) {
  const guardPost = rooms.find((r) => r.type === 'GUARD_POST');

  if (guardPost && Math.hypot(guardPost.center.x - ant.x, guardPost.center.y - ant.y) > 3) {
    if (!ant.path || ant.path.length === 0) {
      const path = findPath(ant.x, ant.y, guardPost.center.x, guardPost.center.y, tiles as any);
      if (path && path.length > 0) {
        ant.path = path;
        ant.pathIndex = 0;
      }
    }
    ant.currentThought = 'Rallie le poste de sentinelle';
    return;
  }

  ant.currentThought = 'Vérifie les vibrations souterraines et protège le terrier';
  if (Math.random() < 0.015) {
    recordTaskCompletion(ant, 'defense', 0.2);
    wanderAnt(ant, tiles);
  }
}

function updateExplorer(
  ant: Ant,
  tiles: string[][],
  revealed: boolean[][],
  delta: number
) {
  ant.actionTimer += delta;
  ant.currentTask = 'Exploration';

  // Check if we just revealed unvisited terrain around our position
  const rx = Math.round(ant.x);
  const ry = Math.round(ant.y);
  let newlyRevealed = false;
  for (let dy = -2; dy <= 2; dy++) {
    for (let dx = -2; dx <= 2; dx++) {
      const nx = rx + dx;
      const ny = ry + dy;
      if (nx >= 0 && nx < GRID_WIDTH && ny >= 7 && ny < GRID_HEIGHT) {
        if (!revealed[ny]?.[nx]) {
          revealed[ny][nx] = true;
          newlyRevealed = true;
        }
      }
    }
  }

  if (newlyRevealed) {
    ant.currentThought = 'Cartographie une nouvelle section de galerie';
    recordTaskCompletion(ant, 'explore', 0.6);
    stigmergyEngine.depositSignal(rx, ry, 'EXPLORE', 2.0);
    logAntAction(ant, ant.age, `Secteur souterrain cartographié en (${rx}, ${ry})`, { x: rx, y: ry });
  } else {
    ant.currentThought = 'Progression en éclaireuse dans les galeries';
  }

  // If not moving, find an unexplored nearby walkable tile or follow EXPLORE signal / wander
  if (!ant.path || ant.path.length === 0) {
    // Look for nearby unrevealed walkable tiles within radius 8
    let targetUnrevealed: { x: number; y: number } | null = null;
    let minDist = Infinity;
    for (let dy = -7; dy <= 7; dy++) {
      for (let dx = -7; dx <= 7; dx++) {
        const nx = rx + dx;
        const ny = ry + dy;
        if (nx >= 0 && nx < GRID_WIDTH && ny >= 7 && ny < GRID_HEIGHT) {
          if (!revealed[ny]?.[nx] && isWalkable(tiles[ny]?.[nx] as any)) {
            const dist = Math.hypot(dx, dy);
            if (dist < minDist) {
              minDist = dist;
              targetUnrevealed = { x: nx, y: ny };
            }
          }
        }
      }
    }

    if (targetUnrevealed) {
      const path = findPath(ant.x, ant.y, targetUnrevealed.x, targetUnrevealed.y, tiles as any);
      if (path && path.length > 0) {
        ant.path = path;
        ant.pathIndex = 0;
        ant.targetTile = targetUnrevealed;
        return;
      }
    }

    wanderAnt(ant, tiles);
  }
}

function updateRecycler(
  ant: Ant,
  tiles: string[][],
  rooms: ColonyRoom[],
  groundItems: GroundItem[],
  delta: number
) {
  ant.actionTimer += delta;
  ant.currentTask = 'Recyclage';

  // If carrying dirt/debris, bring it to RECYCLING room or STORAGE
  if (ant.carrying) {
    const recyclingRoom =
      rooms.find((r) => r.type === 'RECYCLING') ||
      rooms.find((r) => r.type === 'STORAGE') ||
      rooms[0];

    if (recyclingRoom) {
      const dist = Math.hypot(recyclingRoom.center.x - ant.x, recyclingRoom.center.y - ant.y);
      if (dist < 2.0) {
        soundEngine.playDeposit();
        recyclingRoom.storedResources.dirt += 1;
        recordTaskCompletion(ant, 'recycle', 1.0);
        logAntAction(
          ant,
          ant.age,
          `Débris traités et recyclés à la ${recyclingRoom.name}`,
          { x: ant.x, y: ant.y }
        );
        ant.carrying = null;
        ant.state = 'IDLE';
        ant.currentThought = 'Gravats recyclés avec succès';
        return;
      }

      if (!ant.path || ant.path.length === 0) {
        const path = findPath(ant.x, ant.y, recyclingRoom.center.x, recyclingRoom.center.y, tiles as any);
        if (path) {
          ant.path = path;
          ant.pathIndex = 0;
          ant.currentThought = `Achemine les résidus vers ${recyclingRoom.name}`;
          return;
        }
      }
    }
    return;
  }

  // Look for loose dirt items on the ground
  const looseDirtItems = groundItems.filter(
    (item) => item.type === 'dirt' && (!item.reservedBy || item.reservedBy === ant.id)
  );

  if (looseDirtItems.length > 0) {
    let closestItem: GroundItem | null = null;
    let closestDist = Infinity;
    for (const item of looseDirtItems) {
      const dist = Math.hypot(item.x - ant.x, item.y - ant.y);
      if (dist < closestDist) {
        closestDist = dist;
        closestItem = item;
      }
    }

    if (closestItem) {
      if (closestDist < 1.0) {
        ant.carrying = {
          type: closestItem.type,
          color: closestItem.color,
          name: closestItem.name,
        };
        const idx = groundItems.findIndex((it) => it.id === closestItem?.id);
        if (idx >= 0) groundItems.splice(idx, 1);
        ant.state = 'CARRYING';
        ant.path = [];
        ant.pathIndex = 0;
        ant.currentThought = 'Ramasse des gravats pour recyclage';
        return;
      }

      if (!ant.path || ant.path.length === 0) {
        const path = findPath(ant.x, ant.y, closestItem.x, closestItem.y, tiles as any);
        if (path) {
          closestItem.reservedBy = ant.id;
          ant.path = path;
          ant.pathIndex = 0;
          ant.currentThought = 'Rejoint un tas de gravats à nettoyer';
          return;
        }
      }
    }
  }

  // If no debris, visit recycling room or wander
  const recyclingRoom = rooms.find((r) => r.type === 'RECYCLING');
  if (recyclingRoom && Math.hypot(recyclingRoom.center.x - ant.x, recyclingRoom.center.y - ant.y) > 4) {
    if (!ant.path || ant.path.length === 0 && Math.random() < 0.05) {
      const path = findPath(ant.x, ant.y, recyclingRoom.center.x, recyclingRoom.center.y, tiles as any);
      if (path) {
        ant.path = path;
        ant.pathIndex = 0;
        ant.currentThought = 'Rallie le centre de recyclage';
        return;
      }
    }
  }

  wanderAnt(ant, tiles);
}

function wanderAnt(ant: Ant, tiles: string[][], groundItems?: GroundItem[]) {
  if (ant.path && ant.path.length > 0) return;

  // Opportunistic pickup: if idle ant is adjacent to loose earth or crystal dust, pick it up!
  if (!ant.carrying && groundItems && groundItems.length > 0) {
    const nearbyItem = groundItems.find(
      (it) => (!it.reservedBy || it.reservedBy === ant.id) && Math.hypot(it.x - ant.x, it.y - ant.y) < 1.3
    );
    if (nearbyItem) {
      ant.carrying = {
        type: nearbyItem.type,
        color: nearbyItem.color,
        name: nearbyItem.name,
      };
      const idx = groundItems.findIndex((it) => it.id === nearbyItem.id);
      if (idx >= 0) groundItems.splice(idx, 1);
      ant.state = 'CARRYING';
      ant.path = [];
      ant.pathIndex = 0;
      ant.currentThought = `Ramasse ${ant.carrying.name} au sol`;
      return;
    }
  }

  if (Math.random() > 0.05) return;

  const curX = Math.round(ant.x);
  const curY = Math.round(ant.y);

  // Check if there is an active local pheromone gradient for this ant's current active task
  let preferredSignal: PheromoneSignalType | undefined;
  const task = ant.activeTask || (ant.caste === 'MINER' ? 'dig' : ant.caste === 'CARRIER' ? 'carry' : ant.caste === 'NURSE' ? 'brood' : ant.caste === 'GUARD' ? 'defense' : 'explore');
  if (task === 'dig') preferredSignal = 'DIG';
  else if (task === 'carry') preferredSignal = ant.carrying ? 'RETURN' : 'RESOURCE';
  else if (task === 'brood') preferredSignal = 'BROOD';
  else if (task === 'defense') preferredSignal = 'DEFENSE';
  else if (task === 'explore') preferredSignal = 'EXPLORE';

  if (preferredSignal) {
    const bestNeighbor = stigmergyEngine.getStrongestSignalNeighbor(
      ant,
      preferredSignal,
      (x, y) => y >= 7 && isWalkable(tiles[y]?.[x] as any)
    );
    if (bestNeighbor && Math.random() < 0.65) {
      if (bestNeighbor.y >= 7 && isWalkable(tiles[bestNeighbor.y]?.[bestNeighbor.x] as any)) {
        ant.path = [{ x: bestNeighbor.x, y: bestNeighbor.y }];
        ant.pathIndex = 0;
        return;
      }
    }
  }

  const candidates: Array<{ x: number; y: number }> = [];
  const dirs = [
    { x: 1, y: 0 },
    { x: -1, y: 0 },
    { x: 0, y: 1 },
    { x: 0, y: -1 },
  ];

  for (const d of dirs) {
    const nx = curX + d.x;
    const ny = curY + d.y;
    // CRITICAL: ny >= 7 to strictly prevent wandering into the sky (rows 0..6)
    if (nx >= 0 && nx < GRID_WIDTH && ny >= 7 && ny < GRID_HEIGHT) {
      if (isWalkable(tiles[ny]?.[nx] as any)) {
        candidates.push({ x: nx, y: ny });
      }
    }
  }

  if (candidates.length > 0) {
    const chosen = candidates[Math.floor(Math.random() * candidates.length)];
    ant.path = [chosen];
    ant.pathIndex = 0;
  }
}

export {
  generateAntAttributes,
  logAntAction,
  getVisibleCells,
  getAntInspectionData,
} from './antAgent';
