/**
 * Deterministic Pseudo-Random Number Generator (Mulberry32 algorithm)
 * Produces identical sequences for any given seed without using Math.random().
 */
export class DeterministicRNG {
  private state: number;
  private readonly initialSeed: number;

  constructor(seed: number) {
    this.initialSeed = Math.floor(seed);
    this.state = this.initialSeed >>> 0;
  }

  public getSeed(): number {
    return this.initialSeed;
  }

  /**
   * Returns a deterministic float in [0, 1)
   */
  public nextFloat(): number {
    this.state = (this.state + 0x6d2b79f5) | 0;
    let t = Math.imul(this.state ^ (this.state >>> 15), 1 | this.state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /**
   * Returns a deterministic integer in [min, max] inclusive
   */
  public nextInt(min: number, max: number): number {
    if (min >= max) return min;
    const f = this.nextFloat();
    return Math.floor(min + f * (max - min + 1));
  }

  /**
   * Returns a deterministic float in [min, max)
   */
  public nextRange(min: number, max: number): number {
    return min + this.nextFloat() * (max - min);
  }

  /**
   * Returns true with the given probability [0, 1]
   */
  public nextBool(probability: number = 0.5): boolean {
    return this.nextFloat() < probability;
  }
}
