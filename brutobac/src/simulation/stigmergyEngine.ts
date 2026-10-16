import {
  PheromoneSignalType,
  ALL_PHEROMONE_SIGNALS,
  LocalSignalInfo,
  PHEROMONE_METADATA,
} from '../types/stigmergy';
import { Ant } from '../types/colony';
import { GRID_WIDTH, GRID_HEIGHT } from './grid';

export class StigmergyEngine {
  private signals: Map<PheromoneSignalType, Float32Array>;
  private readonly totalCells = GRID_WIDTH * GRID_HEIGHT;

  constructor() {
    this.signals = new Map();
    for (const type of ALL_PHEROMONE_SIGNALS) {
      this.signals.set(type, new Float32Array(this.totalCells));
    }
  }

  private getIndex(x: number, y: number): number {
    return y * GRID_WIDTH + x;
  }

  /**
   * Depositing a pheromone signal on a cell (reinforces existing concentration up to 100)
   */
  public depositSignal(
    x: number,
    y: number,
    type: PheromoneSignalType,
    amount: number
  ): number {
    if (x < 0 || x >= GRID_WIDTH || y < 0 || y >= GRID_HEIGHT) {
      return 0;
    }

    const field = this.signals.get(type);
    if (!field) return 0;

    const idx = this.getIndex(x, y);
    const current = field[idx];
    const updated = Math.min(100.0, current + amount);
    field[idx] = updated;
    return updated;
  }

  /**
   * Retrieves numerical intensity of a signal at given coordinates [0, 100]
   */
  public getSignal(x: number, y: number, type: PheromoneSignalType): number {
    if (x < 0 || x >= GRID_WIDTH || y < 0 || y >= GRID_HEIGHT) {
      return 0;
    }
    const field = this.signals.get(type);
    if (!field) return 0;
    return field[this.getIndex(x, y)];
  }

  /**
   * Evaporates and diffuses signals across the terrain over time.
   * Decreases intensity at each tick: intensity = Math.max(0, intensity - evaporation_rate)
   */
  public update(delta: number): void {
    for (const type of ALL_PHEROMONE_SIGNALS) {
      const field = this.signals.get(type)!;
      const meta = PHEROMONE_METADATA[type];
      const decayPerTick = meta.evaporationRate * 0.04 * delta;

      for (let i = 0; i < this.totalCells; i++) {
        if (field[i] > 0) {
          field[i] = Math.max(0, field[i] - decayPerTick);
          if (field[i] < 0.1) {
            field[i] = 0; // Prune imperceptible signals
          }
        }
      }
    }
  }

  /**
   * Reads all virtual signals detected locally around an individual ant.
   * An ant does NOT see the whole map — only signals within its sensory perimeter!
   */
  public getLocalSignals(
    ant: Ant,
    typeFilter?: PheromoneSignalType,
    radius?: number
  ): LocalSignalInfo[] {
    const r = radius ?? ant.perceptionRadius ?? 4;
    const rSq = r * r;
    const cx = Math.round(ant.x);
    const cy = Math.round(ant.y);

    const minX = Math.max(0, cx - r);
    const maxX = Math.min(GRID_WIDTH - 1, cx + r);
    const minY = Math.max(0, cy - r);
    const maxY = Math.min(GRID_HEIGHT - 1, cy + r);

    const results: LocalSignalInfo[] = [];
    const signalsToCheck = typeFilter ? [typeFilter] : ALL_PHEROMONE_SIGNALS;

    for (let y = minY; y <= maxY; y++) {
      for (let x = minX; x <= maxX; x++) {
        const dx = x - ant.x;
        const dy = y - ant.y;
        const distSq = dx * dx + dy * dy;

        if (distSq <= rSq) {
          const idx = this.getIndex(x, y);
          const distance = Math.sqrt(distSq);
          const relativeAngle = Math.atan2(dy, dx);

          for (const sType of signalsToCheck) {
            const field = this.signals.get(sType)!;
            const intensity = field[idx];

            if (intensity > 0.5) {
              results.push({
                x,
                y,
                signalType: sType,
                intensity,
                distance,
                relativeAngle,
              });
            }
          }
        }
      }
    }

    // Sort by descending intensity
    results.sort((a, b) => b.intensity - a.intensity);
    return results;
  }

  /**
   * Returns the neighboring walkable tile that has the strongest concentration of a signal.
   * Allows ants to follow stigmergic trails naturally!
   */
  public getStrongestSignalNeighbor(
    ant: Ant,
    signalType: PheromoneSignalType,
    isWalkable: (x: number, y: number) => boolean
  ): { x: number; y: number; intensity: number } | null {
    const curX = Math.round(ant.x);
    const curY = Math.round(ant.y);

    const neighbors = [
      { x: curX + 1, y: curY },
      { x: curX - 1, y: curY },
      { x: curX, y: curY + 1 },
      { x: curX, y: curY - 1 },
    ];

    let best: { x: number; y: number; intensity: number } | null = null;
    let highestIntensity = 0.5; // Threshold below which signal is ignored

    for (const n of neighbors) {
      if (n.x >= 0 && n.x < GRID_WIDTH && n.y >= 0 && n.y < GRID_HEIGHT) {
        if (isWalkable(n.x, n.y)) {
          const intensity = this.getSignal(n.x, n.y, signalType);
          if (intensity > highestIntensity) {
            highestIntensity = intensity;
            best = { x: n.x, y: n.y, intensity };
          }
        }
      }
    }

    return best;
  }

  /**
   * Returns raw intensity array for rendering heatmaps
   */
  public getRawSignalField(type: PheromoneSignalType): Float32Array {
    return this.signals.get(type)!;
  }

  /**
   * Serializes current non-zero signals for persistent storage
   */
  public serialize(): Record<string, number> {
    const serialized: Record<string, number> = {};
    for (const type of ALL_PHEROMONE_SIGNALS) {
      const field = this.signals.get(type)!;
      for (let i = 0; i < this.totalCells; i++) {
        if (field[i] > 1.0) {
          const x = i % GRID_WIDTH;
          const y = Math.floor(i / GRID_WIDTH);
          serialized[`${type}_${x}_${y}`] = Number(field[i].toFixed(1));
        }
      }
    }
    return serialized;
  }

  /**
   * Restores signals from serialized representation
   */
  public deserialize(data: Record<string, number>): void {
    this.clearAll();
    for (const [key, value] of Object.entries(data)) {
      const parts = key.split('_');
      if (parts.length === 3) {
        const type = parts[0] as PheromoneSignalType;
        const x = parseInt(parts[1], 10);
        const y = parseInt(parts[2], 10);
        if (this.signals.has(type)) {
          this.depositSignal(x, y, type, value);
        }
      }
    }
  }

  /**
   * Clears all signals
   */
  public clearAll(): void {
    for (const type of ALL_PHEROMONE_SIGNALS) {
      this.signals.get(type)!.fill(0);
    }
  }
}

export const stigmergyEngine = new StigmergyEngine();
