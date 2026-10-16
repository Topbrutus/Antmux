/**
 * Module de distribution de la matière, poussière de cristal et cristaux (5 × 5 × 5)
 *
 * Principes stricts :
 * 1. La poussière et les cristaux ne sont JAMAIS créés arbitrairement au creusage.
 * 2. Ils sont pré-distribués lors de la génération du monde selon la world_seed.
 * 3. Chaque cellule macro contient 125 micro-cellules (5 × 5 × 5) ayant chacune leur contenu propre.
 * 4. Concentrations naturelles : poches, amas, veines, zones riches, cristaux isolés, géodes rares.
 * 5. Lors du creusage, la matière stockée dans la roche est LIBÉRÉE dans la cavité.
 * 6. Conservation absolue de la matière : Matière initiale = Matière libérée + Matière restante.
 */

import { MaterialType, MicroCell, ConcentrationType, TerrainCell } from '../types/terrain';
import { ResourceType } from '../types/colony';
import { DeterministicRNG } from './rng';

export interface CellMatterTotals {
  crystalDust: number;
  crystal: number;
  mineral: number;
  dirt: number;
  resin: number;
  concentration: ConcentrationType;
}

export interface LiberatedMatter {
  crystalDust: number;
  crystal: number;
  mineral: number;
  dirt: number;
  resin: number;
  items: Array<{ type: ResourceType; count: number; name: string }>;
}

/**
 * Hash déterministe pour une coordonnée (worldSeed, x, y)
 */
export function getCellSeed(worldSeed: number, x: number, y: number, salt: number = 0): number {
  let h = (worldSeed ^ (x * 374761393) ^ (y * 668265263) ^ (salt * 1013904223)) | 0;
  h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

/**
 * Calcule les concentrations naturelles (veines, géodes, amas, etc.)
 */
export function detectNaturalConcentration(
  worldSeed: number,
  x: number,
  y: number,
  material: MaterialType
): { type: ConcentrationType; bonusDust: number; bonusCrystals: number } {
  // 1. Surface ou cavités naturelles
  if (y < 7 || material === 'NATURAL_CAVITY') {
    return { type: 'diffuse', bonusDust: 0, bonusCrystals: 0 };
  }

  // 2. Grosses concentrations rares (Géodes Abyssales mythiques dans les profondeurs)
  const distToGeode1 = Math.hypot(x - 22, y - 112);
  const distToGeode2 = Math.hypot(x - 62, y - 114);
  if (distToGeode1 <= 4.2 || distToGeode2 <= 4.8) {
    const geodeRng = new DeterministicRNG(getCellSeed(worldSeed, x, y, 777));
    return {
      type: 'rare_geode',
      bonusDust: geodeRng.nextInt(45, 95),
      bonusCrystals: geodeRng.nextInt(3, 6),
    };
  }

  // Rare géode aléatoire déterminée par seed abyssale
  const deepGeodeSeed = getCellSeed(worldSeed, Math.floor(x / 14), Math.floor(y / 14), 9999);
  if (y >= 105 && deepGeodeSeed % 7 === 0) {
    const centerGeodeX = (Math.floor(x / 14) * 14) + (deepGeodeSeed % 10);
    const centerGeodeY = 108 + ((deepGeodeSeed >>> 4) % 12);
    if (Math.hypot(x - centerGeodeX, y - centerGeodeY) <= 3.5) {
      const gRng = new DeterministicRNG(getCellSeed(worldSeed, x, y, 888));
      return {
        type: 'rare_geode',
        bonusDust: gRng.nextInt(35, 75),
        bonusCrystals: gRng.nextInt(2, 5),
      };
    }
  }

  // 3. Zones très riches (stratum 4 - Noyau Cristallin y=85 à 104)
  if (y >= 85 && y <= 104) {
    const zoneHash = getCellSeed(worldSeed, Math.floor(x / 6), Math.floor(y / 6), 5432);
    if (zoneHash % 4 === 0 || material === 'CRYSTAL_BEARING_ROCK') {
      const zRng = new DeterministicRNG(getCellSeed(worldSeed, x, y, 101));
      return {
        type: 'rich_zone',
        bonusDust: zRng.nextInt(18, 38),
        bonusCrystals: zRng.nextInt(1, 3),
      };
    }
  }

  // 4. Veines (formations serpentines et filons)
  // Veines sinusoïdales traversant les couches 2, 3 et 4
  const veinWave1 = Math.sin(y * 0.18 + (worldSeed % 100) * 0.1) * 8 + 24;
  const veinWave2 = Math.cos(y * 0.14 + (worldSeed % 77) * 0.1) * 10 + 58;
  const isNearVein1 = Math.abs(x - veinWave1) <= 1.8 && y >= 35 && y <= 95;
  const isNearVein2 = Math.abs(x - veinWave2) <= 2.2 && y >= 45 && y <= 110;

  if (material === 'CRYSTAL_BEARING_ROCK' || isNearVein1 || isNearVein2) {
    const vRng = new DeterministicRNG(getCellSeed(worldSeed, x, y, 202));
    return {
      type: 'vein',
      bonusDust: vRng.nextInt(12, 28),
      bonusCrystals: material === 'CRYSTAL_BEARING_ROCK' ? vRng.nextInt(1, 2) : (vRng.nextFloat() < 0.4 ? 1 : 0),
    };
  }

  // 5. Amas (clusters géologiques de 3 à 5 blocs)
  const clusterHash = getCellSeed(worldSeed, Math.floor(x / 4), Math.floor(y / 4), 303);
  if (clusterHash % 6 === 0 && y >= 25) {
    const cRng = new DeterministicRNG(getCellSeed(worldSeed, x, y, 404));
    return {
      type: 'cluster',
      bonusDust: cRng.nextInt(8, 20),
      bonusCrystals: cRng.nextFloat() < 0.5 ? 1 : 0,
    };
  }

  // 6. Petites poches (1 à 2 cellules)
  const pocketHash = getCellSeed(worldSeed, x, y, 505);
  if (pocketHash % 17 === 0 && y >= 14) {
    const pRng = new DeterministicRNG(pocketHash);
    return {
      type: 'small_pocket',
      bonusDust: pRng.nextInt(4, 12),
      bonusCrystals: pRng.nextFloat() < 0.25 ? 1 : 0,
    };
  }

  // 7. Cristaux isolés (nodules solitaires dispersés)
  const isolatedHash = getCellSeed(worldSeed, x, y, 606);
  if (isolatedHash % 47 === 0 && y >= 18) {
    const iRng = new DeterministicRNG(isolatedHash);
    return {
      type: 'isolated_crystal',
      bonusDust: iRng.nextInt(2, 6),
      bonusCrystals: 1,
    };
  }

  // 8. Distribution diffuse standard de fond
  return { type: 'diffuse', bonusDust: 0, bonusCrystals: 0 };
}

/**
 * Calcule la quantité totale de matière stockée dans une macro-cellule (125 micro-cellules)
 */
export function calculateCellMatterTotals(
  worldSeed: number,
  x: number,
  y: number,
  material: MaterialType
): CellMatterTotals {
  if (y < 7 || material === 'NATURAL_CAVITY') {
    return {
      crystalDust: 0,
      crystal: 0,
      mineral: 0,
      dirt: 0,
      resin: 0,
      concentration: 'diffuse',
    };
  }

  const concentration = detectNaturalConcentration(worldSeed, x, y, material);
  const cellRng = new DeterministicRNG(getCellSeed(worldSeed, x, y, 1001));

  let baseDirt = 0;
  let baseMineral = 0;
  let baseResin = 0;
  let baseCrystalDust = 0;
  let baseCrystal = 0;

  // Distribution de base selon la strate géologique
  if (y <= 16) {
    // Terre meuble
    baseDirt = cellRng.nextInt(1, 2);
    baseResin = cellRng.nextFloat() < 0.15 ? 1 : 0;
    baseCrystalDust = cellRng.nextFloat() < 0.1 ? cellRng.nextInt(1, 2) : 0;
  } else if (y <= 28) {
    // Humus
    baseDirt = cellRng.nextInt(1, 3);
    baseResin = cellRng.nextFloat() < 0.25 ? 1 : 0;
    baseMineral = cellRng.nextFloat() < 0.15 ? 1 : 0;
    baseCrystalDust = cellRng.nextFloat() < 0.15 ? cellRng.nextInt(1, 3) : 0;
  } else if (y <= 55) {
    // Argile & Argile compacte
    baseDirt = cellRng.nextInt(1, 2);
    baseMineral = cellRng.nextInt(0, 1);
    baseCrystalDust = cellRng.nextFloat() < 0.25 ? cellRng.nextInt(1, 4) : 0;
  } else if (y <= 84) {
    // Roche & Minéraux
    baseMineral = cellRng.nextInt(1, 2);
    baseDirt = cellRng.nextInt(0, 1);
    baseCrystalDust = cellRng.nextInt(1, 5);
    baseCrystal = cellRng.nextFloat() < 0.08 ? 1 : 0;
  } else if (y <= 104) {
    // Noyau cristallin
    baseMineral = cellRng.nextInt(1, 3);
    baseCrystalDust = cellRng.nextInt(3, 8);
    baseCrystal = cellRng.nextFloat() < 0.2 ? 1 : 0;
  } else {
    // Socle abyssal
    baseMineral = cellRng.nextInt(2, 4);
    baseCrystalDust = cellRng.nextInt(5, 12);
    baseCrystal = cellRng.nextFloat() < 0.3 ? 1 : 0;
  }

  // Matériaux spéciaux explicites
  if (material === 'CRYSTAL_BEARING_ROCK') {
    baseCrystal = Math.max(1, baseCrystal + 1);
    baseCrystalDust += cellRng.nextInt(6, 14);
  } else if (material === 'MINERAL_ROCK') {
    baseMineral += cellRng.nextInt(1, 2);
    baseCrystalDust += cellRng.nextInt(1, 3);
  }

  const totalCrystalDust = baseCrystalDust + concentration.bonusDust;
  const totalCrystal = baseCrystal + concentration.bonusCrystals;
  const totalMineral = baseMineral;
  const totalDirt = baseDirt;
  const totalResin = baseResin;

  return {
    crystalDust: totalCrystalDust,
    crystal: totalCrystal,
    mineral: totalMineral,
    dirt: totalDirt,
    resin: totalResin,
    concentration: concentration.type,
  };
}

/**
 * Génère les 125 micro-cellules (5 × 5 × 5) d'une cellule,
 * en y répartissant de façon déterministe la matière totale.
 */
export function generate5x5x5MicroCells(
  worldSeed: number,
  x: number,
  y: number,
  totals: CellMatterTotals,
  isExcavated: boolean = false
): MicroCell[] {
  const microCells: MicroCell[] = new Array(125);
  const microRng = new DeterministicRNG(getCellSeed(worldSeed, x, y, 7777));

  // Initialisation des 125 micro-cellules
  for (let z = 0; z < 5; z++) {
    for (let sy = 0; sy < 5; sy++) {
      for (let sx = 0; sx < 5; sx++) {
        const index = z * 25 + sy * 5 + sx;
        microCells[index] = {
          index,
          subX: sx,
          subY: sy,
          subZ: z,
          excavated: isExcavated,
          crystal_dust_amount: 0,
          crystal_amount: 0,
          mineral_amount: 0,
          dirt_amount: 0,
          resin_amount: 0,
        };
      }
    }
  }

  if (isExcavated) {
    return microCells;
  }

  // 1. Répartition des cristaux purs (favorise le cœur du volume 5x5x5: subX=2, subY=2, subZ=2)
  let crystalsToPlace = totals.crystal;
  // Trie les micro-cellules par distance croissante au centre pour un regroupement naturel
  const indicesByCenterDist = Array.from({ length: 125 }, (_, i) => i).sort((a, b) => {
    const ax = a % 5 - 2, ay = (Math.floor(a / 5) % 5) - 2, az = Math.floor(a / 25) - 2;
    const bx = b % 5 - 2, by = (Math.floor(b / 5) % 5) - 2, bz = Math.floor(b / 25) - 2;
    return (ax * ax + ay * ay + az * az) - (bx * bx + by * by + bz * bz);
  });

  for (const idx of indicesByCenterDist) {
    if (crystalsToPlace <= 0) break;
    microCells[idx].crystal_amount = 1;
    crystalsToPlace--;
  }

  // 2. Répartition de la poussière de cristal (en chapelet / micro-veines)
  let dustToPlace = totals.crystalDust;
  while (dustToPlace > 0) {
    const targetIdx = microRng.nextInt(0, 124);
    const amount = Math.min(dustToPlace, microRng.nextInt(1, 3));
    microCells[targetIdx].crystal_dust_amount += amount;
    dustToPlace -= amount;
  }

  // 3. Répartition des minéraux
  let mineralToPlace = totals.mineral;
  while (mineralToPlace > 0) {
    const targetIdx = microRng.nextInt(0, 124);
    microCells[targetIdx].mineral_amount += 1;
    mineralToPlace--;
  }

  // 4. Répartition de la terre / matière brute
  let dirtToPlace = totals.dirt;
  while (dirtToPlace > 0) {
    const targetIdx = microRng.nextInt(0, 124);
    microCells[targetIdx].dirt_amount += 1;
    dirtToPlace--;
  }

  // 5. Répartition de la bio-résine
  let resinToPlace = totals.resin;
  while (resinToPlace > 0) {
    const targetIdx = microRng.nextInt(0, 124);
    microCells[targetIdx].resin_amount += 1;
    resinToPlace--;
  }

  return microCells;
}

/**
 * Libère une partie des micro-cellules (par exemple lors de la progression du creusage).
 * La matière qui était cachée dans la roche est physiquement libérée.
 */
export function liberateMicroCells(cell: TerrainCell, countToLiberate: number): LiberatedMatter {
  if (!cell.micro_cells) {
    return { crystalDust: 0, crystal: 0, mineral: 0, dirt: 0, resin: 0, items: [] };
  }

  let dust = 0;
  let crystal = 0;
  let mineral = 0;
  let dirt = 0;
  let resin = 0;

  let liberatedCount = 0;
  for (let i = 0; i < cell.micro_cells.length && liberatedCount < countToLiberate; i++) {
    const mc = cell.micro_cells[i];
    if (!mc.excavated) {
      mc.excavated = true;
      liberatedCount++;

      dust += mc.crystal_dust_amount;
      crystal += mc.crystal_amount;
      mineral += mc.mineral_amount;
      dirt += mc.dirt_amount;
      resin += mc.resin_amount;
    }
  }

  cell.excavated_micro_cells = Math.min(125, cell.excavated_micro_cells + liberatedCount);

  const items: Array<{ type: ResourceType; count: number; name: string }> = [];
  if (crystal > 0) {
    items.push({ type: 'crystal', count: crystal, name: 'Cristal Bruto-Lumineux' });
  }
  if (dust > 0) {
    items.push({ type: 'crystal_dust', count: dust, name: 'Poussière de cristal' });
  }
  if (mineral > 0) {
    items.push({ type: 'mineral', count: mineral, name: 'Fragment minéral' });
  }
  if (dirt > 0) {
    items.push({ type: 'dirt', count: dirt, name: 'Motte de terre meuble' });
  }
  if (resin > 0) {
    items.push({ type: 'resin', count: resin, name: 'Goutte de bio-résine' });
  }

  return { crystalDust: dust, crystal, mineral, dirt, resin, items };
}

/**
 * Libère TOUTE la matière restante de la cellule (lorsque le bloc est entièrement percé).
 * Garantit la conservation intégrale de la matière stockée.
 */
export function liberateAllRemainingMatter(cell: TerrainCell): LiberatedMatter {
  if (!cell.micro_cells) {
    // Fallback si micro_cells non initialisé
    const items: Array<{ type: ResourceType; count: number; name: string }> = [];
    if (cell.crystal_amount > 0) {
      items.push({ type: 'crystal', count: cell.crystal_amount, name: 'Cristal Bruto-Lumineux' });
    }
    if (cell.crystal_dust_amount > 0) {
      items.push({ type: 'crystal_dust', count: cell.crystal_dust_amount, name: 'Poussière de cristal' });
    }
    if (cell.mineral_amount > 0) {
      items.push({ type: 'mineral', count: cell.mineral_amount, name: 'Fragment minéral' });
    }
    if (cell.dirt_amount > 0) {
      items.push({ type: 'dirt', count: cell.dirt_amount, name: 'Motte de terre meuble' });
    }
    if (cell.resin_amount > 0) {
      items.push({ type: 'resin', count: cell.resin_amount, name: 'Goutte de bio-résine' });
    }
    return {
      crystalDust: cell.crystal_dust_amount,
      crystal: cell.crystal_amount,
      mineral: cell.mineral_amount,
      dirt: cell.dirt_amount,
      resin: cell.resin_amount,
      items,
    };
  }

  const unexcavated = cell.micro_cells.filter((mc) => !mc.excavated);
  return liberateMicroCells(cell, unexcavated.length);
}

/**
 * Vérifie que la conservation de matière est strictement respectée
 */
export function verifyCellMatterConservation(cell: TerrainCell): boolean {
  if (!cell.micro_cells) return true;
  let sumDust = 0;
  let sumCrystal = 0;
  let sumMineral = 0;
  let sumDirt = 0;
  let sumResin = 0;

  for (const mc of cell.micro_cells) {
    sumDust += mc.crystal_dust_amount;
    sumCrystal += mc.crystal_amount;
    sumMineral += mc.mineral_amount;
    sumDirt += mc.dirt_amount;
    sumResin += mc.resin_amount;
  }

  return (
    sumDust === cell.crystal_dust_amount &&
    sumCrystal === cell.crystal_amount &&
    sumMineral === cell.mineral_amount &&
    sumDirt === cell.dirt_amount &&
    sumResin === cell.resin_amount
  );
}
