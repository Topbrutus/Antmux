import {
  Ant,
  AntCaste,
  AntTaskType,
  ALL_ANT_TASKS,
  DigTask,
  BroodItem,
} from '../types/colony';
import { GridState } from './grid';
import { stigmergyEngine } from './stigmergyEngine';

/**
 * Initial task affinity profiles by caste.
 * Each ant has affinities [0.0 - 1.0] representing response thresholds for all 7 tasks.
 * While initial castes provide natural baselines, ants are never locked into them!
 */
export function getInitialTaskAffinities(caste: AntCaste): Record<AntTaskType, number> {
  switch (caste) {
    case 'MINER':
      return {
        dig: 0.85,
        carry: 0.45,
        explore: 0.55,
        build: 0.40,
        brood: 0.15,
        defense: 0.30,
        recycle: 0.35,
      };
    case 'CARRIER':
      return {
        carry: 0.85,
        dig: 0.40,
        explore: 0.55,
        build: 0.35,
        brood: 0.25,
        defense: 0.25,
        recycle: 0.50,
      };
    case 'NURSE':
      return {
        brood: 0.90,
        carry: 0.45,
        explore: 0.30,
        build: 0.35,
        dig: 0.20,
        defense: 0.30,
        recycle: 0.45,
      };
    case 'BUILDER':
      return {
        build: 0.85,
        dig: 0.60,
        carry: 0.50,
        explore: 0.40,
        brood: 0.20,
        defense: 0.35,
        recycle: 0.45,
      };
    case 'GUARD':
      return {
        defense: 0.90,
        explore: 0.60,
        dig: 0.35,
        carry: 0.30,
        build: 0.35,
        brood: 0.15,
        recycle: 0.20,
      };
    case 'QUEEN':
      return {
        brood: 0.95,
        defense: 0.20,
        explore: 0.10,
        dig: 0.05,
        carry: 0.05,
        build: 0.10,
        recycle: 0.05,
      };
    default:
      return {
        dig: 0.5,
        carry: 0.5,
        explore: 0.5,
        build: 0.5,
        brood: 0.5,
        defense: 0.5,
        recycle: 0.5,
      };
  }
}

/**
 * Initial baseline experience points per task.
 */
export function getInitialTaskExperience(caste: AntCaste): Record<AntTaskType, number> {
  const exp: Record<AntTaskType, number> = {
    dig: 0,
    carry: 0,
    explore: 0,
    build: 0,
    brood: 0,
    defense: 0,
    recycle: 0,
  };
  const primaryTask: Record<AntCaste, AntTaskType> = {
    MINER: 'dig',
    CARRIER: 'carry',
    NURSE: 'brood',
    BUILDER: 'build',
    GUARD: 'defense',
    QUEEN: 'brood',
  };
  const pt = primaryTask[caste] || 'explore';
  exp[pt] = 15;
  return exp;
}

/**
 * Computes dominant specialty derived from highest affinity and accumulated experience.
 */
export function computeDominantSpecialty(
  affinities: Record<AntTaskType, number>,
  experiences: Record<AntTaskType, number>
): AntTaskType {
  let highestTask: AntTaskType = 'explore';
  let highestScore = -Infinity;

  for (const t of ALL_ANT_TASKS) {
    const score = (affinities[t] || 0) * 1.5 + (experiences[t] || 0) * 0.08;
    if (score > highestScore) {
      highestScore = score;
      highestTask = t;
    }
  }

  return highestTask;
}

/**
 * Computes the collective environmental stimuli for the 7 tasks based on global colony state.
 */
export function computeColonyStimuli(
  grid: GridState,
  digTasks: DigTask[],
  brood: BroodItem[],
  ants: Ant[]
): Record<AntTaskType, number> {
  // 1. DIG stimulus: designated excavation tasks & available dig fronts
  const activeDigTasksCount = digTasks.length;
  const digStimulus = Math.min(0.95, 0.2 + activeDigTasksCount * 0.18);

  // 2. CARRY stimulus: loose resources waiting on ground
  const groundItemsCount = grid.groundItems.length;
  const carryStimulus = Math.min(0.95, 0.15 + groundItemsCount * 0.15);

  // 3. EXPLORE stimulus: unmapped frontiers & dark unrevealed subterranean cells
  let unrevealedCount = 0;
  for (let y = 15; y < 70; y += 8) {
    for (let x = 10; x < 70; x += 8) {
      if (!grid.revealed[y]?.[x]) {
        unrevealedCount++;
      }
    }
  }
  const exploreStimulus = Math.min(0.9, 0.25 + unrevealedCount * 0.02);

  // 4. BROOD stimulus: eggs, larvae, cocoons needing incubation and care
  const needyBroodCount = brood.filter((b) => b.progress < 100).length;
  const broodStimulus = Math.min(0.95, 0.2 + needyBroodCount * 0.15);

  // 5. BUILD stimulus: workshop activities, room expansions and maintenance
  const hasWorkshop = grid.rooms.some((r) => r.type === 'WORKSHOP');
  const buildStimulus = hasWorkshop ? 0.45 : 0.25;

  // 6. DEFENSE stimulus: surface entrance perimeter vigilance and security
  const guardsAtSurface = ants.filter((a) => a.y <= 14 && a.activeTask === 'defense').length;
  const defenseStimulus = guardsAtSurface < 2 ? 0.6 : 0.25;

  // 7. RECYCLE stimulus: accumulation of dirt/debris, compost maintenance
  const dirtItemsCount = grid.groundItems.filter((i) => i.type === 'dirt').length;
  const hasRecycleRoom = grid.rooms.some((r) => r.type === 'RECYCLING');
  const recycleStimulus = Math.min(0.85, 0.2 + dirtItemsCount * 0.12 + (hasRecycleRoom ? 0.15 : 0));

  return {
    dig: digStimulus,
    carry: carryStimulus,
    explore: exploreStimulus,
    build: buildStimulus,
    brood: broodStimulus,
    defense: defenseStimulus,
    recycle: recycleStimulus,
  };
}

/**
 * Decentralized task adoption based on response thresholds, local perception & stigmergy signals.
 * Evaluates whether an ant should organically switch its active task.
 */
export function evaluateAntTaskSwitch(
  ant: Ant,
  colonyStimuli: Record<AntTaskType, number>,
  grid: GridState,
  digTasks: DigTask[],
  brood: BroodItem[]
): { newActiveTask: AntTaskType; reason: string } | null {
  // Queen never switches tasks
  if (ant.caste === 'QUEEN') {
    return null;
  }

  // If already carrying a resource, finish delivery first!
  if (ant.carrying) {
    return null;
  }

  if (!ant.taskAffinity) {
    ant.taskAffinity = getInitialTaskAffinities(ant.caste);
  }
  if (!ant.taskExperience) {
    ant.taskExperience = getInitialTaskExperience(ant.caste);
  }

  const cx = Math.round(ant.x);
  const cy = Math.round(ant.y);

  // 1. Gather local stigmergic signals (Bloc 4) at current ant position
  const localSignals = stigmergyEngine.getLocalSignals(ant);
  let localDigPheromone = 0;
  let localCarryPheromone = 0;
  let localBroodPheromone = 0;
  let localDefensePheromone = 0;
  let localExplorePheromone = 0;

  for (const s of localSignals) {
    if (s.signalType === 'DIG') localDigPheromone = Math.max(localDigPheromone, s.intensity);
    else if (s.signalType === 'RESOURCE' || s.signalType === 'CRYSTAL' || s.signalType === 'RETURN')
      localCarryPheromone = Math.max(localCarryPheromone, s.intensity);
    else if (s.signalType === 'BROOD') localBroodPheromone = Math.max(localBroodPheromone, s.intensity);
    else if (s.signalType === 'DEFENSE')
      localDefensePheromone = Math.max(localDefensePheromone, s.intensity);
    else if (s.signalType === 'EXPLORE')
      localExplorePheromone = Math.max(localExplorePheromone, s.intensity);
  }

  // 2. Evaluate local proximity stimuli (within sensory range ~6 tiles)
  let nearbyGroundItems = 0;
  let nearbyDigTasks = 0;
  let nearbyUntendedBrood = 0;

  for (const gi of grid.groundItems) {
    if (Math.hypot(gi.x - ant.x, gi.y - ant.y) <= 6) {
      nearbyGroundItems++;
    }
  }

  for (const dt of digTasks) {
    if (Math.hypot(dt.x - ant.x, dt.y - ant.y) <= 6) {
      nearbyDigTasks++;
    }
  }

  for (const bi of brood) {
    if (Math.hypot(bi.x - ant.x, bi.y - ant.y) <= 7 && (!bi.tendedBy || bi.tendedBy === ant.id)) {
      nearbyUntendedBrood++;
    }
  }

  const nearSurfaceOrGate = cy <= 12;
  const inWorkshop = grid.rooms.some(
    (r) => r.type === 'WORKSHOP' && Math.hypot(r.center.x - ant.x, r.center.y - ant.y) <= 5
  );
  const inRecycling = grid.rooms.some(
    (r) => r.type === 'RECYCLING' && Math.hypot(r.center.x - ant.x, r.center.y - ant.y) <= 5
  );

  // 3. Compute combined local stimulus per task
  const localBoosts: Record<AntTaskType, number> = {
    dig: Math.min(0.6, nearbyDigTasks * 0.25 + localDigPheromone * 0.05),
    carry: Math.min(0.6, nearbyGroundItems * 0.25 + localCarryPheromone * 0.05),
    explore: Math.min(0.4, (cy > 40 ? 0.2 : 0) + localExplorePheromone * 0.05),
    brood: Math.min(0.6, nearbyUntendedBrood * 0.3 + localBroodPheromone * 0.05),
    build: inWorkshop ? 0.35 : 0.05,
    defense: (nearSurfaceOrGate ? 0.35 : 0.05) + localDefensePheromone * 0.05,
    recycle: inRecycling ? 0.35 : 0.05,
  };

  // 4. Score each task using the Response Threshold Model
  // Score = (ColonyStimulus + LocalBoost) * (Affinity + 0.3) * (1 + Experience * 0.012)
  const scores: Record<AntTaskType, number> = {
    dig: 0,
    carry: 0,
    explore: 0,
    build: 0,
    brood: 0,
    defense: 0,
    recycle: 0,
  };

  for (const t of ALL_ANT_TASKS) {
    const stimulus = (colonyStimuli[t] || 0.2) + (localBoosts[t] || 0);
    const affinity = ant.taskAffinity[t] ?? 0.4;
    const exp = ant.taskExperience[t] ?? 0;
    scores[t] = stimulus * (affinity + 0.3) * (1 + exp * 0.012);
  }

  // 5. Select the highest scoring task
  let bestTask: AntTaskType = ant.activeTask || 'explore';
  let bestScore = scores[bestTask];

  for (const t of ALL_ANT_TASKS) {
    if (scores[t] > bestScore) {
      bestScore = scores[t];
      bestTask = t;
    }
  }

  // Avoid erratic flickering: switch only if new task score significantly exceeds current task (+0.12 threshold)
  const currentScore = scores[ant.activeTask || 'explore'] || 0;
  if (bestTask === ant.activeTask || bestScore < currentScore + 0.12) {
    return null;
  }

  // 6. Generate contextual emergent reason for the task switch
  let reason = 'Réorientation selon les besoins collectifs du terrier';
  if (bestTask === 'carry' && nearbyGroundItems > 0) {
    reason = 'Détection de ressources à acheminer vers les réserves';
  } else if (bestTask === 'carry' && colonyStimuli.carry > 0.6) {
    reason = 'Forte demande de transport dans les galeries';
  } else if (bestTask === 'dig' && nearbyDigTasks > 0) {
    reason = 'Front de roche prioritaire détecté à proximité';
  } else if (bestTask === 'dig' && localDigPheromone > 2) {
    reason = 'Appel de phéromone de forage perçu dans la galerie';
  } else if (bestTask === 'brood' && nearbyUntendedBrood > 0) {
    reason = 'Soins nécessaires aux jeunes larves de la nurserie';
  } else if (bestTask === 'defense' && nearSurfaceOrGate) {
    reason = 'Vigilance et patrouille au seuil de la surface';
  } else if (bestTask === 'build' && inWorkshop) {
    reason = 'Renforcement des parois et travaux d’aménagement';
  } else if (bestTask === 'recycle' && inRecycling) {
    reason = 'Traitement des débris et tri des gravats';
  } else if (bestTask === 'explore') {
    reason = 'Reconnaissance et cartographie des profondeurs';
  }

  return { newActiveTask: bestTask, reason };
}

/**
 * Positive reinforcement: rewards an ant for successful task completion,
 * slightly increasing task affinity and experience, while keeping specialization reversible.
 */
export function recordTaskCompletion(
  ant: Ant,
  task: AntTaskType,
  magnitude: number = 1.0
): void {
  if (!ant.taskExperience) {
    ant.taskExperience = getInitialTaskExperience(ant.caste);
  }
  if (!ant.taskAffinity) {
    ant.taskAffinity = getInitialTaskAffinities(ant.caste);
  }

  // 1. Increase experience in the executed task
  ant.taskExperience[task] = (ant.taskExperience[task] || 0) + Math.round(magnitude * 2);

  // 2. Increase affinity (reinforce specialization through practice)
  const currentAffinity = ant.taskAffinity[task] || 0.4;
  ant.taskAffinity[task] = Number(Math.min(1.0, currentAffinity + 0.015 * magnitude).toFixed(3));

  // 3. Very subtle decay of non-practiced tasks to preserve flexibility and reversibility
  for (const t of ALL_ANT_TASKS) {
    if (t !== task) {
      const prev = ant.taskAffinity[t] || 0.4;
      ant.taskAffinity[t] = Number(Math.max(0.12, prev - 0.001 * magnitude).toFixed(3));
    }
  }

  // 4. Update dominant specialty
  ant.dominantSpecialty = computeDominantSpecialty(ant.taskAffinity, ant.taskExperience);
}
