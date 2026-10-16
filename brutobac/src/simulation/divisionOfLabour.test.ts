/**
 * Automated Test Suite — BLOC 5: DIVISION DU TRAVAIL ADAPTATIVE
 * Validates task affinities, response thresholds, collective stimuli,
 * decentralized task switching, experience accumulation, and reversible specialization.
 */

import {
  getInitialTaskAffinities,
  getInitialTaskExperience,
  computeDominantSpecialty,
  computeColonyStimuli,
  evaluateAntTaskSwitch,
  recordTaskCompletion,
} from './divisionOfLabour';
import { createAnt, generateInitialAnts } from './antAI';
import { generateInitialGrid } from './grid';
import { getAntInspectionData } from './antAgent';
import { ALL_ANT_TASKS, AntTaskType, DigTask, BroodItem, GroundItem } from '../types/colony';

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function runDivisionOfLabourTests() {
  console.log('================================================================');
  console.log('RUNNING DIVISION OF LABOUR SUITE — BLOC 5: DIVISION ADAPTATIVE');
  console.log('================================================================\n');

  // ---------------------------------------------------------------------------
  // TEST 1 — TASK AFFINITIES & RESPONSE THRESHOLDS FOR ALL 7 TASKS
  // ---------------------------------------------------------------------------
  console.log('TEST 1: Verification of task affinities for all 7 tasks...');
  const miner = createAnt('MINER', 41, 20);
  const carrier = createAnt('CARRIER', 41, 20);

  for (const task of ALL_ANT_TASKS) {
    assert(
      typeof miner.taskAffinity[task] === 'number' &&
        miner.taskAffinity[task] >= 0 &&
        miner.taskAffinity[task] <= 1,
      `Task affinity for ${task} must be between 0 and 1`
    );
    assert(
      typeof miner.taskExperience[task] === 'number' && miner.taskExperience[task] >= 0,
      `Task experience for ${task} must be >= 0`
    );
  }

  // Miner has primary inclination towards dig, carrier towards carry
  assert(miner.taskAffinity.dig > miner.taskAffinity.brood, 'Miner should have higher dig affinity than brood');
  assert(carrier.taskAffinity.carry > carrier.taskAffinity.dig, 'Carrier should have higher carry affinity than dig');

  console.log('PASS — TASK_AFFINITIES_VALIDATED (7 tasks present with valid thresholds)\n');

  // ---------------------------------------------------------------------------
  // TEST 2 — COLLECTIVE STIMULI REFLECTING COLONY NEEDS
  // ---------------------------------------------------------------------------
  console.log('TEST 2: Collective stimuli response to colony needs...');
  const grid = generateInitialGrid(3861);
  const ants = generateInitialAnts();

  // Baseline stimuli
  const baseStimuli = computeColonyStimuli(grid, [], [], ants);

  // Spiking dig tasks
  const simulatedDigTasks: DigTask[] = [
    { id: 'dt1', x: 42, y: 30, progress: 0 },
    { id: 'dt2', x: 43, y: 30, progress: 0 },
    { id: 'dt3', x: 44, y: 30, progress: 0 },
    { id: 'dt4', x: 45, y: 30, progress: 0 },
  ];
  const digSpikeStimuli = computeColonyStimuli(grid, simulatedDigTasks, [], ants);
  assert(digSpikeStimuli.dig > baseStimuli.dig, 'Dig stimulus must increase when dig tasks are present');

  // Spiking ground items
  const simulatedGroundItems: GroundItem[] = [
    { id: 'g1', x: 41, y: 22, type: 'crystal', color: '#38bdf8', name: 'Cristal', createdAt: 0 },
    { id: 'g2', x: 41, y: 23, type: 'crystal', color: '#38bdf8', name: 'Cristal', createdAt: 0 },
    { id: 'g3', x: 42, y: 22, type: 'mineral', color: '#cbd5e1', name: 'Mineral', createdAt: 0 },
  ];
  grid.groundItems.push(...simulatedGroundItems);
  const carrySpikeStimuli = computeColonyStimuli(grid, [], [], ants);
  assert(carrySpikeStimuli.carry > baseStimuli.carry, 'Carry stimulus must increase when resources are on ground');

  // Spiking brood items
  const simulatedBrood: BroodItem[] = [
    { id: 'b1', type: 'larva', x: 24, y: 18, progress: 20 },
    { id: 'b2', type: 'egg', x: 25, y: 18, progress: 10 },
  ];
  const broodSpikeStimuli = computeColonyStimuli(grid, [], simulatedBrood, ants);
  assert(broodSpikeStimuli.brood > baseStimuli.brood, 'Brood stimulus must increase when brood is present');

  console.log('PASS — COLLECTIVE_STIMULI_VALIDATED (DIG, CARRY, BROOD react dynamically)\n');

  // ---------------------------------------------------------------------------
  // TEST 3 — DECENTRALIZED ADAPTIVE TASK SWITCHING (NO RIGID PRISON)
  // ---------------------------------------------------------------------------
  console.log('TEST 3: Adaptive task switching based on local and collective stimulus...');
  const flexibleWorker = createAnt('MINER', 41, 20);
  assert(flexibleWorker.activeTask === 'dig', 'Initial active task should be dig');

  // When carry demand is high and resources are right beside the ant
  const highCarryStimuli: Record<AntTaskType, number> = {
    dig: 0.2,
    carry: 0.95,
    explore: 0.2,
    build: 0.2,
    brood: 0.2,
    defense: 0.2,
    recycle: 0.2,
  };

  const decision = evaluateAntTaskSwitch(flexibleWorker, highCarryStimuli, grid, [], []);
  assert(decision !== null, 'Worker ant should evaluate and switch task under high stimulus');
  assert(decision?.newActiveTask === 'carry', 'Miner ant must adaptively switch to carry');
  assert(typeof decision?.reason === 'string' && decision.reason.length > 0, 'Decision must provide a clear reason');

  console.log(`PASS — ADAPTIVE_TASK_SWITCH_VALIDATED (Switched from dig to ${decision?.newActiveTask}: "${decision?.reason}")\n`);

  // ---------------------------------------------------------------------------
  // TEST 4 — PROGRESSIVE SPECIALIZATION & REVERSIBILITY
  // ---------------------------------------------------------------------------
  console.log('TEST 4: Progressive specialization via practice & reversibility...');
  const apprentice = createAnt('CARRIER', 41, 20);
  const initialDigAffinity = apprentice.taskAffinity.dig;
  const initialDigXp = apprentice.taskExperience.dig;

  // Perform digging successfully multiple times
  recordTaskCompletion(apprentice, 'dig', 1.0);
  recordTaskCompletion(apprentice, 'dig', 1.0);
  recordTaskCompletion(apprentice, 'dig', 1.0);

  assert(apprentice.taskExperience.dig > initialDigXp, 'Experience in dig must increase');
  assert(apprentice.taskAffinity.dig > initialDigAffinity, 'Affinity for dig must increase with practice');

  // Verify reversibility: other affinities don't drop to zero (remain flexible)
  for (const t of ALL_ANT_TASKS) {
    assert(apprentice.taskAffinity[t] >= 0.1, `Affinity for ${t} must remain accessible for future adaptation`);
  }

  console.log('PASS — REVERSIBLE_SPECIALIZATION_VALIDATED (Experience gained: +' + (apprentice.taskExperience.dig - initialDigXp) + ' XP, affinities remain flexible)\n');

  // ---------------------------------------------------------------------------
  // TEST 5 — INSPECTION DATA COMPLETENESS FOR BLOC 5
  // ---------------------------------------------------------------------------
  console.log('TEST 5: Complete inspection data for division of labour...');
  const inspected = createAnt('BUILDER', 35, 18);
  inspected.activeTask = 'dig';
  inspected.lastTaskSwitchReason = 'Front de roche prioritaire détecté';
  recordTaskCompletion(inspected, 'dig', 2.0);

  const inspData = getAntInspectionData(inspected);

  assert(inspData.activeTask === 'dig', 'activeTask must be present');
  assert(typeof inspData.activeTaskLabel === 'string' && inspData.activeTaskLabel.length > 0, 'activeTaskLabel must be present');
  assert(typeof inspData.dominantSpecialty === 'string', 'dominantSpecialty must be present');
  assert(typeof inspData.dominantSpecialtyLabel === 'string', 'dominantSpecialtyLabel must be present');
  assert(typeof inspData.taskAffinity === 'object', 'taskAffinity map must be present');
  assert(typeof inspData.taskExperience === 'object', 'taskExperience map must be present');
  assert(inspData.lastTaskSwitchReason === 'Front de roche prioritaire détecté', 'lastTaskSwitchReason must match');

  console.log('PASS — INSPECTION_DATA_BLOC5_VALIDATED\n');

  console.log('================================================================');
  console.log('ALL 5 DIVISION OF LABOUR TESTS PASSED SUCCESSFULLY!');
  console.log('================================================================');
}

runDivisionOfLabourTests();
