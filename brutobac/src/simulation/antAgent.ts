import { Ant, AntCaste, AntState, GroundItem, TASK_LABELS, AntTaskType } from '../types/colony';
import { AntActionRecord, VisibleCellInfo, AntInspectionData } from '../types/agent';
import { GridState, inBounds, isExcavated } from './burrowArchitecture';
import { GRID_WIDTH, GRID_HEIGHT } from './grid';
import {
  getInitialTaskAffinities,
  getInitialTaskExperience,
  computeDominantSpecialty,
} from './divisionOfLabour';

/**
 * Appends a new action to the ant's rolling history (max 8 recent entries)
 */
export function logAntAction(
  ant: Ant,
  tick: number,
  action: string,
  location?: { x: number; y: number }
): void {
  if (!ant.recentActions) {
    ant.recentActions = [];
  }

  // Prevent logging exact duplicates consecutively
  const last = ant.recentActions[ant.recentActions.length - 1];
  if (last && last.action === action && Math.abs(last.tick - tick) < 5) {
    return;
  }

  ant.recentActions.push({
    tick,
    action,
    location: location ? { x: Math.round(location.x), y: Math.round(location.y) } : undefined,
  });

  if (ant.recentActions.length > 8) {
    ant.recentActions.shift();
  }
}

/**
 * Computes individual physical traits based on natural biological variation in size.
 * Note: No rigid rules like "big = guard, small = worker" — all castes have natural size ranges!
 */
export function generateAntAttributes(
  caste: AntCaste,
  forcedSize?: number
): {
  size: number;
  strength: number;
  speed: number;
  carryCapacity: number;
  digProficiency: number;
  perceptionRadius: number;
} {
  // Natural variation in size: mean ~1.0 with variation, Queen is naturally larger
  let size: number;
  if (forcedSize !== undefined) {
    size = forcedSize;
  } else if (caste === 'QUEEN') {
    size = 1.5;
  } else {
    // Normal distribution approximation: 0.82 to 1.32
    const variance = (Math.random() + Math.random() + Math.random()) / 3; // Bell curve [0, 1]
    size = Number((0.8 + variance * 0.5).toFixed(2));
  }

  // Strength increases with size
  const strengthVariance = Math.floor(Math.random() * 3) - 1;
  const strength = Math.max(3, Math.round(size * 7 + strengthVariance));

  // Speed: smaller ants are more nimble; larger ants have more inertia
  const baseSpeed = 0.075 / Math.sqrt(size);
  const speed = Number((baseSpeed * (0.95 + Math.random() * 0.1)).toFixed(3));

  // Carry capacity scales with size and strength
  const carryCapacity = Math.max(1, Math.round(size * 1.8));

  // Dig proficiency: mandibles and muscular power
  const digProficiency = Number((size * 1.1 + (Math.random() * 0.4 - 0.2)).toFixed(2));

  // Perception radius: typically 4 to 6 cells
  const perceptionRadius = caste === 'GUARD' ? 6 : Math.round(4 + Math.random() * 1.5);

  return {
    size,
    strength,
    speed,
    carryCapacity,
    digProficiency,
    perceptionRadius,
  };
}

/**
 * Local perception around each ant:
 * An ant does NOT possess omniscient knowledge of the entire map.
 * It detects nearby cells within its sensory radius and stores them in local memory.
 */
export function getVisibleCells(
  ant: Ant,
  grid: GridState,
  radius?: number
): VisibleCellInfo[] {
  const visible: VisibleCellInfo[] = [];
  const r = radius ?? ant.perceptionRadius ?? 4;
  const cx = Math.round(ant.x);
  const cy = Math.round(ant.y);

  if (!ant.knownCells) {
    ant.knownCells = [];
  }

  const rSq = r * r;
  const minX = Math.max(0, cx - r);
  const maxX = Math.min(GRID_WIDTH - 1, cx + r);
  const minY = Math.max(0, cy - r);
  const maxY = Math.min(GRID_HEIGHT - 1, cy + r);

  for (let y = minY; y <= maxY; y++) {
    for (let x = minX; x <= maxX; x++) {
      const dx = x - ant.x;
      const dy = y - ant.y;
      if (dx * dx + dy * dy <= rSq) {
        const cell = grid.cells[y]?.[x];
        if (!cell) continue;

        const walkable = isExcavated(grid, x, y);
        const hasGroundItem = grid.groundItems.some(
          (gi: GroundItem) => Math.round(gi.x) === x && Math.round(gi.y) === y
        );

        // Check if there are neighboring excavated cells (is accessible front)
        let isAccessibleFront = false;
        if (!cell.excavated) {
          isAccessibleFront =
            (inBounds(x + 1, y) && isExcavated(grid, x + 1, y)) ||
            (inBounds(x - 1, y) && isExcavated(grid, x - 1, y)) ||
            (inBounds(x, y + 1) && isExcavated(grid, x, y + 1)) ||
            (inBounds(x, y - 1) && isExcavated(grid, x, y - 1));
        }

        visible.push({
          x,
          y,
          cell_id: cell.cell_id,
          isWalkable: walkable,
          excavated: cell.excavated,
          hardness: cell.hardness,
          resource_type: cell.resource_type,
          resource_amount: cell.resource_amount,
          hasGroundItem,
          hasDigTask: false,
          isAccessibleFront,
        });

        // Memorize in local memory
        const cellKey = `${x},${y}`;
        if (!ant.knownCells.includes(cellKey)) {
          ant.knownCells.push(cellKey);
          if (ant.knownCells.length > 100) {
            ant.knownCells.shift();
          }
        }
      }
    }
  }

  return visible;
}

/**
 * Returns human-friendly label for Ant states
 */
export function getAntStateLabel(state: AntState): string {
  switch (state) {
    case 'IDLE':
      return 'En attente / Repos actif';
    case 'WANDERING':
      return 'Patrouille & Exploration locale';
    case 'MOVING_TO_DIG':
      return 'En route vers le front de roche';
    case 'DIGGING':
      return 'Excavation de galerie en cours';
    case 'PICKING_UP':
      return 'Prise en charge d’une ressource';
    case 'CARRYING':
    case 'DELIVERING':
      return 'Transport vers les dépôts';
    case 'TENDING_BROOD':
      return 'Soins attentifs au couvain';
    case 'PATROLLING':
      return 'Garde et surveillance des failles';
    case 'RESTING':
      return 'Repos biologique régénérateur';
    default:
      return 'Activité souterraine';
  }
}

/**
 * Extracts complete structured inspection data for an individual ant
 */
export function getAntInspectionData(ant: Ant): AntInspectionData {
  const depthMeters = Number(((ant.y - 7) * 0.52).toFixed(1));
  const ageSeconds = Math.round(ant.age / 60);
  const ageFormatted =
    ageSeconds < 60
      ? `${ageSeconds}s (Tick ${ant.age})`
      : `${Math.floor(ageSeconds / 60)}m ${ageSeconds % 60}s (Tick ${ant.age})`;

  let sizeCategory = 'Gabarit standard (1.0x)';
  if (ant.size < 0.9) {
    sizeCategory = `Gabarit svelte (${ant.size}x)`;
  } else if (ant.size > 1.35) {
    sizeCategory = `Gabarit colossal (${ant.size}x)`;
  } else if (ant.size > 1.15) {
    sizeCategory = `Gabarit robuste (${ant.size}x)`;
  }

  let destinationLabel = 'Aucune (Déplacement libre)';
  if (ant.currentDestination) {
    destinationLabel = `X: ${ant.currentDestination.x}, Y: ${ant.currentDestination.y} (-${Math.round(ant.currentDestination.y * 0.52)}m)`;
  } else if (ant.targetTile) {
    destinationLabel = `X: ${ant.targetTile.x}, Y: ${ant.targetTile.y} (-${Math.round(ant.targetTile.y * 0.52)}m)`;
  }

  const load = ant.carrying
    ? {
        item: ant.carrying.name,
        color: ant.carrying.color,
        amount: 1,
        capacity: ant.carryCapacity,
      }
    : {
        item: 'Pattes libres (Aucune charge)',
        amount: 0,
        capacity: ant.carryCapacity,
      };

  const taskAffinity = ant.taskAffinity || getInitialTaskAffinities(ant.caste);
  const taskExperience = ant.taskExperience || getInitialTaskExperience(ant.caste);
  const dominantSpecialty =
    ant.dominantSpecialty || computeDominantSpecialty(taskAffinity, taskExperience);
  const activeTask = ant.activeTask || 'explore';

  return {
    ant_id: ant.ant_id || ant.id,
    name: ant.name,
    caste: ant.caste,
    age: ant.age,
    ageFormatted,
    size: ant.size,
    sizeCategory,
    position: {
      x: Number(ant.x.toFixed(1)),
      y: Number(ant.y.toFixed(1)),
      depthMeters: Math.max(0, depthMeters),
    },
    task: ant.currentTask || ant.currentThought || 'Exploration de galerie',
    activeTask,
    activeTaskLabel: TASK_LABELS[activeTask]?.name || 'Exploration',
    dominantSpecialty,
    dominantSpecialtyLabel: TASK_LABELS[dominantSpecialty]?.name || 'Polyvalente',
    taskAffinity,
    taskExperience,
    lastTaskSwitchReason:
      ant.lastTaskSwitchReason || 'Spécialisation initiale selon la caste d’origine',
    destination: ant.currentDestination || ant.targetTile,
    destinationLabel,
    load,
    aptitudes: {
      strength: ant.strength,
      speed: ant.speed,
      digProficiency: ant.digProficiency,
      carryCapacity: ant.carryCapacity,
    },
    state: ant.state,
    stateLabel: getAntStateLabel(ant.state),
    recentActions: ant.recentActions ? [...ant.recentActions].reverse() : [],
  };
}
