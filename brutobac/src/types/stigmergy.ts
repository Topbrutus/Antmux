export type PheromoneSignalType =
  | 'RETURN'
  | 'RESOURCE'
  | 'CRYSTAL'
  | 'DIG'
  | 'BUILD'
  | 'BROOD'
  | 'DANGER'
  | 'DEFENSE'
  | 'RECYCLE'
  | 'EXPLORE';

export const ALL_PHEROMONE_SIGNALS: PheromoneSignalType[] = [
  'RETURN',
  'RESOURCE',
  'CRYSTAL',
  'DIG',
  'BUILD',
  'BROOD',
  'DANGER',
  'DEFENSE',
  'RECYCLE',
  'EXPLORE',
];

export interface LocalSignalInfo {
  x: number;
  y: number;
  signalType: PheromoneSignalType;
  intensity: number; // 0 to 100
  distance: number;
  relativeAngle: number;
}

export interface PheromoneSignalMetadata {
  name: string;
  color: string;
  description: string;
  evaporationRate: number; // Per second decay
  diffusionRate: number;
}

export const PHEROMONE_METADATA: Record<PheromoneSignalType, PheromoneSignalMetadata> = {
  RETURN: {
    name: 'Piste de Retour (Nid)',
    color: '#10b981', // Emerald
    description: 'Guide les porteuses vers les chambres de stockage et la reine.',
    evaporationRate: 0.8,
    diffusionRate: 0.15,
  },
  RESOURCE: {
    name: 'Gisement de Matière',
    color: '#f59e0b', // Amber
    description: 'Piste olfactive vers les poches de terre, minéraux et résine.',
    evaporationRate: 1.0,
    diffusionRate: 0.12,
  },
  CRYSTAL: {
    name: 'Émanation Cristalline',
    color: '#06b6d4', // Cyan
    description: 'Vibration harmonique indiquant un filon de cristal découvert.',
    evaporationRate: 0.6,
    diffusionRate: 0.1,
  },
  DIG: {
    name: 'Front d’Excavation',
    color: '#eab308', // Yellow
    description: 'Appel aux mineuses pour forer une roche ou un élargissement.',
    evaporationRate: 1.2,
    diffusionRate: 0.08,
  },
  BUILD: {
    name: 'Chantier & Consolidation',
    color: '#14b8a6', // Teal
    description: 'Désignation de parois à étayer ou d’aménagements de chambres.',
    evaporationRate: 0.9,
    diffusionRate: 0.1,
  },
  BROOD: {
    name: 'Aura du Couvain',
    color: '#ec4899', // Pink
    description: 'Odeur maternelle des œufs et larves attirant les nourrices.',
    evaporationRate: 0.5,
    diffusionRate: 0.12,
  },
  DANGER: {
    name: 'Alerte d’Éboulement / Danger',
    color: '#ef4444', // Red
    description: 'Signal de fuite ou de danger prévenant les ouvrières d’une zone.',
    evaporationRate: 1.5,
    diffusionRate: 0.25,
  },
  DEFENSE: {
    name: 'Ralliement Défensif',
    color: '#f43f5e', // Rose
    description: 'Appel aux sentinelles et gardes pour sécuriser un seuil.',
    evaporationRate: 1.1,
    diffusionRate: 0.18,
  },
  RECYCLE: {
    name: 'Dépôt de Débris',
    color: '#84cc16', // Lime
    description: 'Signal guidant le compostage et le tri des fragments usés.',
    evaporationRate: 1.0,
    diffusionRate: 0.1,
  },
  EXPLORE: {
    name: 'Tracé d’Exploration',
    color: '#8b5cf6', // Violet
    description: 'Tracé éclaireur marquant les galeries vierges et passages récents.',
    evaporationRate: 1.4,
    diffusionRate: 0.15,
  },
};
