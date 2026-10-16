import {
  Ant,
  AntCaste,
  ColonyRoom,
  ColonyStats,
  DigTask,
  GroundItem,
  BroodItem,
  ResourceType,
  RoomType,
  QueenFormulaPriority,
  QueenTerminalState,
} from '../types/colony';
import { TerrainCell, TerrainSaveData, TerrainBlock3D } from '../types/terrain';
import {
  generateInitialGrid,
  GridState,
  GRID_WIDTH,
  GRID_HEIGHT,
  revealRadius,
  ROOM_PRESETS,
  saveTerrain,
  loadTerrain,
  getCellInfo,
  getCellById,
  getCell,
  getAccessibleDigFronts,
  classifyBurrowTopology,
  getBurrowStats,
  updateBurrowChambers,
  isDesignatedRoom,
  digHorizontalTunnel,
  digVerticalShaft,
  digOrganicCavity,
  liberateAllRemainingMatter,
  liberateMicroCells,
} from './grid';
import { advanceTerrainFragments, createTerrainFragment } from './fragmentGravity';
import { DigFront, TunnelNode, BurrowStats } from '../types/burrow';
import { PheromoneSignalType, LocalSignalInfo } from '../types/stigmergy';
import { stigmergyEngine } from './stigmergyEngine';
import {
  generateInitialAnts,
  updateAnt,
  createAnt,
  evaluateQueenDigOrders,
  evaluateQueenRoomOrders,
  executeQueenRoomOrder,
  decideQueenRoomOrder,
  getAvailableCavities,
  QueenRoomOrder,
} from './antAI';
import { computeColonyStimuli } from './divisionOfLabour';
import { soundEngine } from '../audio/soundEngine';

export interface ColonyEngineState {
  grid: GridState;
  ants: Ant[];
  digTasks: DigTask[];
  brood: BroodItem[];
  stats: ColonyStats;
  selectedAntId: string | null;
  selectedRoomId: string | null;
  speed: number; // 0 = pause, 1 = normal, 2 = fast, 4 = ultra
  queenTerminal: QueenTerminalState;
}

export interface DigEvent {
  x: number;
  y: number;
  radius: number;
  isManual: boolean;
  isCrystal: boolean;
  liberatedDust?: number;
}

export class ColonyEngine {
  public state: ColonyEngineState;
  public tickCount: number = 0;
  private listeners: Set<() => void> = new Set();
  private digListeners: Set<(event: DigEvent) => void> = new Set();
  private lastUpdate: number = Date.now();
  private digTaskCounter = 1;
  private groundItemCounter = 100;
  private queenEvaluationTimer = 60; // Triggers Queen evaluation on first tick

  constructor(seed: number = 3861) {
    const grid = generateInitialGrid(seed);
    const ants = generateInitialAnts();

    // Initial brood in Nursery
    const nursery = grid.rooms.find((r) => r.type === 'NURSERY');
    const nx = nursery ? nursery.center.x : 24;
    const ny = nursery ? nursery.center.y : 18;

    const initialBrood: BroodItem[] = [];

    // Calculate initial depth
    let maxDugRow = 0;
    for (let y = 0; y < GRID_HEIGHT; y++) {
      for (let x = 0; x < GRID_WIDTH; x++) {
        if (grid.tiles[y][x] === 'AIR' && y > maxDugRow) {
          maxDugRow = y;
        }
      }
    }

    this.state = {
      grid,
      ants,
      digTasks: [],
      brood: initialBrood,
      stats: {
        crystals: 14,
        crystalDust: 0,
        dirt: 45,
        minerals: 12,
        resin: 6,
        totalDugTiles: 138,
        deepestDugMeters: Math.round(maxDugRow * 0.52),
        population: ants.length,
        queenHealth: 100,
        queenMorale: 95,
        resonantEnergy: 24,
      },
      selectedAntId: null,
      selectedRoomId: null,
      speed: 1,
      queenTerminal: {
        connected: false,
        source: 'http://127.0.0.1:8788/api/queen-priorities',
        activeLimit: 3,
        active: [],
        queued: [],
        lastSyncAt: null,
      },
    };

    // Initial stigmergic guidance seeds
    stigmergyEngine.depositSignal(41, 20, 'RETURN', 50);
    stigmergyEngine.depositSignal(24, 18, 'BROOD', 60);
    stigmergyEngine.depositSignal(56, 19, 'RETURN', 50);
    stigmergyEngine.depositSignal(41, 35, 'DIG', 40);
  }

  public subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  public onDig(listener: (event: DigEvent) => void) {
    this.digListeners.add(listener);
    return () => {
      this.digListeners.delete(listener);
    };
  }

  private notify() {
    this.listeners.forEach((l) => l());
  }

  private emitDig(event: DigEvent) {
    this.digListeners.forEach((l) => l(event));
  }

  public setSpeed(speed: number) {
    this.state.speed = speed;
    this.notify();
  }

  public setQueenFormulaPriorities(priorities: QueenFormulaPriority[]) {
    const activeLimit = 3;
    this.state.queenTerminal = {
      ...this.state.queenTerminal,
      connected: true,
      activeLimit,
      active: priorities.slice(0, activeLimit),
      queued: priorities.slice(activeLimit),
      lastSyncAt: Date.now(),
    };
    const queen = this.state.ants.find((ant) => ant.caste === 'QUEEN');
    if (queen) {
      queen.currentThought = this.state.queenTerminal.active.length
        ? `Terminal royal : ${this.state.queenTerminal.active.length} calculs prioritaires`
        : 'Terminal royal : aucun calcul prioritaire';
    }
    this.notify();
  }

  public setQueenTerminalOffline() {
    if (!this.state.queenTerminal.connected && this.state.queenTerminal.lastSyncAt === null) {
      return;
    }
    this.state.queenTerminal = {
      ...this.state.queenTerminal,
      connected: false,
      active: [],
      queued: [],
    };
    this.notify();
  }

  public setSelectedAnt(id: string | null) {
    this.state.selectedAntId = id;
    this.notify();
  }

  public setSelectedRoom(id: string | null) {
    this.state.selectedRoomId = id;
    this.notify();
  }

  /**
   * Main simulation step called by requestAnimationFrame
   */
  public tick(currentTime: number) {
    if (this.state.speed === 0) {
      this.lastUpdate = currentTime;
      return;
    }

    this.tickCount++;
    this.state.grid.currentTick = this.tickCount;

    const elapsedMs = Math.min(currentTime - this.lastUpdate, 60);
    this.lastUpdate = currentTime;
    const delta = (elapsedMs / 16.66) * this.state.speed;

    const { grid, ants, digTasks, brood, stats } = this.state;

    // 0. Update virtual pheromone evaporation & diffusion
    stigmergyEngine.update(delta);

    // Compute emergent colony stimuli (Bloc 5: Division du travail)
    const colonyStimuli = computeColonyStimuli(grid, digTasks, brood, ants);

    // 1. Update Ants
    for (const ant of ants) {
      updateAnt(
        ant,
        grid.tiles as any,
        grid.revealed,
        grid.hardness,
        grid.rooms,
        grid.groundItems,
        digTasks,
        brood,
        (type, count, x, y) => this.handleResourceMined(type, count, x, y),
        (type, roomId) => this.handleResourceDelivered(type, roomId),
        (x, y) => this.handleNewBrood(x, y),
        delta,
        (x, y) => this.handleCellExcavated(x, y),
        colonyStimuli,
        grid,
        (x, y) => this.addDigTask(x, y),
        (x, y, type) => this.designateRoomAt(x, y, type)
      );
    }

    // Emergent Queen autonomous excavation & room designation:
    // At regular intervals, Queen assesses colony needs, digs fronts and furnishes available cavities
    this.queenEvaluationTimer += delta;
    if (this.queenEvaluationTimer >= 60) {
      this.queenEvaluationTimer = 0;
      if (this.state.digTasks.length < 3) {
        this.evaluateQueenDigOrders(3);
      }
      this.evaluateQueenRoomOrders();
    }

    // 2. Update Brood maturation
    for (let i = brood.length - 1; i >= 0; i--) {
      const item = brood[i];
      if (item.progress >= 100) {
        // Hatch new ant!
        const castes: AntCaste[] = ['MINER', 'CARRIER', 'BUILDER', 'NURSE'];
        const chosenCaste = castes[Math.floor(Math.random() * castes.length)];
        const newAnt = createAnt(chosenCaste, item.x, item.y);
        ants.push(newAnt);
        stats.population = ants.length;
        soundEngine.playQueenPulse();
        brood.splice(i, 1);
      }
    }

    // 3. Resonant energy generation from crystals stored in Crystal Vault
    const crystalRooms = grid.rooms.filter((r) => r.type === 'CRYSTAL_VAULT');
    let crystalRate = 0;
    crystalRooms.forEach((cr) => {
      crystalRate += cr.storedResources.crystal * 0.005 * cr.level * delta;
    });
    if (crystalRate > 0) {
      stats.resonantEnergy = Math.min(999, stats.resonantEnergy + crystalRate);
    }

    // 4. Loose earth & excavated powder falling simulation under gravity:
    // Earth, crystal dust, and mined fragments tumble down through open air
    // until settling onto cavern floors, scattering slightly into natural piles.
    for (const item of grid.groundItems) {
      if (item.isSettled) continue;
      const curX = item.x;
      const curY = item.y;
      const nextY = curY + (item.vy || 0.05) * delta;
      const checkTileY = Math.floor(nextY + 0.45);
      const checkTileX = Math.floor(curX);

      // Check if open air below
      if (
        checkTileY < GRID_HEIGHT &&
        grid.tiles[checkTileY]?.[checkTileX] === 'AIR'
      ) {
        item.vy = Math.min(0.25, (item.vy || 0.05) + 0.025 * delta);
        item.y = nextY;
        // Subtle drift while tumbling down
        item.x = Math.max(1, Math.min(GRID_WIDTH - 2, item.x + Math.sin(item.y * 2.5) * 0.012 * delta));
      } else {
        // Landed on floor or solid tile! Settle and scatter slightly into an organic pile
        item.y = Math.min(GRID_HEIGHT - 1, Math.floor(curY) + 0.65 + (Math.random() - 0.5) * 0.12);
        item.vy = 0;
        item.isSettled = true;
        // Slight horizontal scatter on impact ("la terre peut s'éparpiller un peu")
        const scatter = (Math.random() - 0.5) * 0.42;
        const targetScatterX = Math.max(1, Math.min(GRID_WIDTH - 2, item.x + scatter));
        if (grid.tiles[Math.floor(item.y)]?.[Math.floor(targetScatterX)] === 'AIR') {
          item.x = targetScatterX;
        }
      }
    }

    advanceTerrainFragments(grid.terrainFragments, grid.tiles, delta);

    this.notify();
  }

  private handleCellExcavated(x: number, y: number) {
    const cell = this.state.grid.cells[y]?.[x];
    if (cell) {
      // Libère toute la matière stockée dans les 125 micro-cellules
      const liberated = liberateAllRemainingMatter(cell);

      this.state.grid.terrainFragments.push(
        createTerrainFragment(
          `fragment_${this.tickCount}_${x}_${y}`,
          x + 0.5,
          y,
          cell.material_type,
          liberated.crystalDust,
          this.tickCount + x + y
        )
      );

      cell.excavated = true;
      cell.hardness = 0;
      cell.material_type = y < 7 ? 'SURFACE' : 'NATURAL_CAVITY';
      cell.modified_at_tick = this.tickCount;
      cell.excavated_micro_cells = 125;
      revealRadius(this.state.grid.revealed, x, y, 4, this.state.grid.cells);
      updateBurrowChambers(this.state.grid, this.tickCount);

      // Génère les ressources physiquement libérées sur le sol de la cavité
      if (liberated.crystal > 0) {
        soundEngine.playCrystalChime(1.1);
      }
      for (const item of liberated.items) {
        this.handleResourceMined(item.type, item.count, x, y);
      }

      this.emitDig({
        x,
        y,
        radius: 1,
        isManual: false,
        isCrystal: liberated.crystal > 0,
        liberatedDust: liberated.crystalDust,
      });
    }
  }

  private handleResourceMined(type: ResourceType, count: number, x: number, y: number) {
    const itemNames: Record<ResourceType, string> = {
      crystal: 'Cristal Bruto-Lumineux',
      crystal_dust: 'Poussière de cristal',
      dirt: 'Motte de terreau',
      mineral: 'Fragment minéral',
      resin: 'Goutte de bio-résine',
      egg: 'Œuf royal',
    };
    const itemColors: Record<ResourceType, string> = {
      crystal: '#38bdf8',
      crystal_dust: '#7dd3fc',
      dirt: '#8a5e3a',
      mineral: '#cbd5e1',
      resin: '#10b981',
      egg: '#fef08a',
    };

    for (let i = 0; i < count; i++) {
      const offsetX = (Math.random() - 0.5) * 0.8;
      const offsetY = (Math.random() - 0.5) * 0.8;
      this.state.grid.groundItems.push({
        id: `drop_${this.groundItemCounter++}`,
        x: Math.max(0, Math.min(GRID_WIDTH - 1, x + offsetX)),
        y: Math.max(0, Math.min(GRID_HEIGHT - 1, y + offsetY)),
        type,
        color: itemColors[type],
        name: itemNames[type],
        createdAt: Date.now(),
        vy: 0.04 + Math.random() * 0.06,
        isSettled: false,
      });
    }

    this.state.stats.totalDugTiles++;
    const currentMeters = Math.round(y * 0.52);
    if (currentMeters > this.state.stats.deepestDugMeters) {
      this.state.stats.deepestDugMeters = currentMeters;
    }
  }

  private handleResourceDelivered(type: ResourceType, roomId: string) {
    const room = this.state.grid.rooms.find((r) => r.id === roomId);
    if (room) {
      if (type === 'crystal') {
        room.storedResources.crystal++;
        this.state.stats.crystals++;
        this.state.stats.resonantEnergy += 2;
      } else if (type === 'crystal_dust') {
        room.storedResources.crystalDust = (room.storedResources.crystalDust || 0) + 1;
        this.state.stats.crystalDust = (this.state.stats.crystalDust || 0) + 1;
        this.state.stats.resonantEnergy += 0.5;
      } else if (type === 'dirt') {
        room.storedResources.dirt++;
        this.state.stats.dirt++;
      } else if (type === 'mineral') {
        room.storedResources.mineral++;
        this.state.stats.minerals++;
      } else if (type === 'resin') {
        room.storedResources.resin++;
        this.state.stats.resin++;
      }
    }
  }

  private handleNewBrood(x: number, y: number) {
    this.state.brood.push({
      id: `brood_${Date.now() % 100000}`,
      type: 'egg',
      x,
      y,
      progress: 0,
    });
  }

  /**
   * Direct manual excavation by player cursor
   */
  public manualDig(centerX: number, centerY: number, radius = 1) {
    const { grid } = this.state;
    let dugCount = 0;

    for (let dy = -radius; dy <= radius; dy++) {
      for (let dx = -radius; dx <= radius; dx++) {
        const x = centerX + dx;
        const y = centerY + dy;
        if (x >= 0 && x < GRID_WIDTH && y >= 7 && y < GRID_HEIGHT) {
          if (dx * dx + dy * dy <= radius * radius) {
            const oldType = grid.tiles[y][x];
            if (oldType !== 'AIR' && oldType !== 'SURFACE_AIR') {
              grid.tiles[y][x] = 'AIR';
              grid.hardness[y][x] = 0;

              // Update persistent deterministic cell state
              const cell = grid.cells[y]?.[x];
              if (cell && !cell.excavated) {
                // Libère la matière pré-stockée dans la roche (aucune création arbitraire)
                const liberated = liberateAllRemainingMatter(cell);

                cell.excavated = true;
                cell.hardness = 0;
                cell.material_type = y < 7 ? 'SURFACE' : 'NATURAL_CAVITY';
                cell.modified_at_tick = this.tickCount;
                cell.excavated_micro_cells = 125;

                revealRadius(grid.revealed, x, y, 4, grid.cells);

                // Remove dig tasks if any
                const taskIdx = this.state.digTasks.findIndex((t) => t.x === x && t.y === y);
                if (taskIdx >= 0) this.state.digTasks.splice(taskIdx, 1);

                if (liberated.crystal > 0) {
                  soundEngine.playCrystalChime();
                }
                for (const item of liberated.items) {
                  this.handleResourceMined(item.type, item.count, x, y);
                }
                dugCount++;
              }
            }
          }
        }
      }
    }

    if (dugCount > 0) {
      updateBurrowChambers(this.state.grid, this.tickCount);
      soundEngine.playDig(true);
      this.emitDig({
        x: centerX,
        y: centerY,
        radius,
        isManual: true,
        isCrystal: centerY >= 85,
      });
      this.notify();
    }
  }

  /**
   * Player or Queen designates an order to dig a tile for the miner ants.
   * Returns the created DigTask or null if invalid / already exists.
   */
  public addDigTask(x: number, y: number): DigTask | null {
    if (x < 0 || x >= GRID_WIDTH || y < 7 || y >= GRID_HEIGHT) return null;
    const tile = this.state.grid.tiles[y][x];
    if (tile === 'AIR' || tile === 'SURFACE_AIR') return null;

    // Check if task already exists
    const exists = this.state.digTasks.some((t) => t.x === x && t.y === y);
    if (!exists) {
      const task: DigTask = {
        id: `task_${this.digTaskCounter++}`,
        x,
        y,
        progress: 0,
      };
      this.state.digTasks.push(task);
      soundEngine.playDig();
      this.notify();
      return task;
    }
    return null;
  }

  /**
   * Clears all active dig tasks (useful for test/reset scenarios)
   */
  public clearDigTasks(): void {
    this.state.digTasks = [];
    this.notify();
  }

  /**
   * Convert dug cavity into a specialized chamber
   */
  public designateRoomAt(centerX: number, centerY: number, roomType: RoomType): ColonyRoom | null {
    const { grid } = this.state;
    if (centerX < 0 || centerX >= GRID_WIDTH || centerY < 0 || centerY >= GRID_HEIGHT) return null;
    if (grid.tiles[centerY][centerX] !== 'AIR') return null;

    // Flood fill contiguous AIR tiles
    // Check if clicked tile is already part of an existing room
    const existingRoom = grid.rooms.find((r) =>
      r.tiles.some((t) => t.x === centerX && t.y === centerY)
    );

    // If already a designated room, re-designate / change room type cleanly while preserving stable room_id
    if (existingRoom && isDesignatedRoom(existingRoom)) {
      const preset = ROOM_PRESETS[roomType];
      existingRoom.type = roomType;
      existingRoom.room_function = roomType;
      existingRoom.name = `${preset.name} ${existingRoom.id.replace(/^room_/, '')}`;
      existingRoom.color = preset.color;
      existingRoom.isDesignated = true;
      for (const t of existingRoom.tiles) {
        if (grid.cells[t.y]?.[t.x]) {
          grid.cells[t.y][t.x].room_id = existingRoom.id;
        }
      }
      soundEngine.playRoomFormed();
      this.setSelectedRoom(existingRoom.id);
      this.notify();
      return existingRoom;
    }

    // Otherwise, collect other designated tiles so we don't bleed into existing designated rooms
    const otherDesignatedTiles = new Set<string>();
    for (const r of grid.rooms) {
      if (isDesignatedRoom(r) && r !== existingRoom) {
        for (const t of r.tiles) {
          otherDesignatedTiles.add(`${t.x},${t.y}`);
        }
      }
    }

    const visited = new Set<string>();
    const queue = [{ x: centerX, y: centerY }];
    const roomTiles: Array<{ x: number; y: number }> = [];

    let minX = centerX;
    let maxX = centerX;
    let minY = centerY;
    let maxY = centerY;

    while (queue.length > 0 && roomTiles.length < 120) {
      const cur = queue.shift()!;
      const key = `${cur.x},${cur.y}`;
      if (visited.has(key)) continue;
      visited.add(key);

      if (
        cur.x >= 0 &&
        cur.x < GRID_WIDTH &&
        cur.y >= 7 &&
        cur.y < GRID_HEIGHT &&
        grid.tiles[cur.y][cur.x] === 'AIR' &&
        !otherDesignatedTiles.has(key)
      ) {
        roomTiles.push(cur);
        minX = Math.min(minX, cur.x);
        maxX = Math.max(maxX, cur.x);
        minY = Math.min(minY, cur.y);
        maxY = Math.max(maxY, cur.y);

        const neighbors = [
          { x: cur.x + 1, y: cur.y },
          { x: cur.x - 1, y: cur.y },
          { x: cur.x, y: cur.y + 1 },
          { x: cur.x, y: cur.y - 1 },
        ];

        for (const n of neighbors) {
          if (!visited.has(`${n.x},${n.y}`) && !otherDesignatedTiles.has(`${n.x},${n.y}`)) {
            queue.push(n);
          }
        }
      }
    }

    if (roomTiles.length < 4) return null;

    // Remove any overlapping unassigned automatic cavities (type === 'NONE') so they don't conflict
    const roomTileSet = new Set(roomTiles.map((t) => `${t.x},${t.y}`));
    grid.rooms = grid.rooms.filter(
      (r) => isDesignatedRoom(r) || !r.tiles.some((t) => roomTileSet.has(`${t.x},${t.y}`))
    );

    const preset = ROOM_PRESETS[roomType];
    const stableRoomId = existingRoom?.id || `room_${roomType.toLowerCase()}_${minX}_${minY}`;
    const roomIndex = grid.rooms.filter((r) => r.type === roomType).length + 1;

    // Calculate tunnel entrances
    const entrances: Array<{ x: number; y: number }> = [];
    for (const t of roomTiles) {
      const neighbors = [
        { x: t.x + 1, y: t.y },
        { x: t.x - 1, y: t.y },
        { x: t.x, y: t.y + 1 },
        { x: t.x, y: t.y - 1 },
      ];
      for (const n of neighbors) {
        if (
          n.x >= 0 &&
          n.x < GRID_WIDTH &&
          n.y >= 0 &&
          n.y < GRID_HEIGHT &&
          grid.tiles[n.y]?.[n.x] === 'AIR' &&
          !roomTileSet.has(`${n.x},${n.y}`)
        ) {
          entrances.push({ x: t.x, y: t.y });
          break;
        }
      }
    }

    const newRoom: ColonyRoom = {
      id: stableRoomId,
      type: roomType,
      room_function: roomType,
      isDesignated: true,
      name: `${preset.name} ${roomIndex}`,
      color: preset.color,
      tiles: roomTiles,
      bounds: { minX, maxX, minY, maxY },
      center: {
        x: Math.round((minX + maxX) / 2),
        y: Math.round((minY + maxY) / 2),
      },
      level: 1,
      storedResources: { crystal: 0, dirt: 0, mineral: 0, resin: 0 },
      capacity: roomTiles.length * 5,
      entrances,
      createdAtTick: this.tickCount,
    };

    // Link cells strictly to stable room_id
    for (const t of roomTiles) {
      if (grid.cells[t.y]?.[t.x]) {
        grid.cells[t.y][t.x].room_id = stableRoomId;
      }
    }

    grid.rooms.push(newRoom);
    soundEngine.playRoomFormed();
    this.setSelectedRoom(stableRoomId);
    this.notify();
    return newRoom;
  }

  /**
   * Summon or incubate a new ant manually with resource cost
   */
  public recruitAnt(caste: AntCaste): boolean {
    const costDirt = 10;
    const costMineral = 5;

    if (this.state.stats.dirt < costDirt || this.state.stats.minerals < costMineral) {
      return false;
    }

    this.state.stats.dirt -= costDirt;
    this.state.stats.minerals -= costMineral;

    const queenRoom = this.state.grid.rooms.find((r) => r.type === 'QUEEN');
    const spawnX = queenRoom ? queenRoom.center.x : 41;
    const spawnY = queenRoom ? queenRoom.center.y : 20;

    const ant = createAnt(caste, spawnX, spawnY);
    this.state.ants.push(ant);
    this.state.stats.population = this.state.ants.length;
    soundEngine.playQueenPulse();
    this.notify();
    return true;
  }

  /**
   * Upgrade room level to boost storage capacity and resonance
   */
  public upgradeRoom(roomId: string): boolean {
    const room = this.state.grid.rooms.find((r) => r.id === roomId);
    if (!room) return false;

    const costResin = 4 * room.level;
    const costCrystals = 2 * room.level;

    if (this.state.stats.resin < costResin || this.state.stats.crystals < costCrystals) {
      return false;
    }

    this.state.stats.resin -= costResin;
    this.state.stats.crystals -= costCrystals;
    room.level++;
    room.capacity = Math.round(room.capacity * 1.5);
    soundEngine.playRoomFormed();
    this.notify();
    return true;
  }

  /**
   * Inspection helper: returns full cell info by coordinate
   */
  public getCellInfo(x: number, y: number): TerrainCell | null {
    return getCellInfo(this.state.grid.cells, x, y);
  }

  /**
   * Récupère un vrai bloc volumétrique 3D de matière de terrain à la position (x, y, z).
   * Permet de demander getCell(x, y, z) et de recevoir un vrai bloc de terrain.
   */
  public getCell(x: number, y: number, z: number = 0): TerrainBlock3D | null {
    return getCell(x, y, z, this.state.grid);
  }

  /**
   * Inspection helper: returns full cell info by stable cell_id
   */
  public getCellById(cellId: string): TerrainCell | null {
    return getCellById(this.state.grid.cells, cellId);
  }

  /**
   * Persists terrain state into a serializable schema
   */
  public saveTerrain(): TerrainSaveData {
    return saveTerrain(this.state.grid, this.tickCount);
  }

  /**
   * Restores terrain state from serialized schema
   */
  public loadTerrain(saveData: TerrainSaveData): void {
    const newGrid = loadTerrain(saveData);
    this.state.grid = newGrid;
    this.tickCount = saveData.tick;
    this.notify();
  }

  /**
   * Reseeds the terrain world with a deterministic world seed
   */
  public reseedWorld(seed: number): void {
    const newGrid = generateInitialGrid(seed);
    this.state.grid = newGrid;
    this.tickCount = 0;
    this.notify();
  }

  /**
   * Returns all solid cells immediately bordering existing tunnels/chambers (accessible fronts)
   */
  public getAccessibleDigFronts(): DigFront[] {
    return getAccessibleDigFronts(this.state.grid);
  }

  /**
   * Returns topological metrics of the burrow
   */
  public getBurrowStats(): BurrowStats {
    return getBurrowStats(this.state.grid);
  }

  /**
   * Classifies all excavated tiles into tunnel types (culs-de-sac, shafts, bifurcations, intersections)
   */
  public classifyBurrowTopology(): TunnelNode[] {
    return classifyBurrowTopology(this.state.grid);
  }

  /**
   * Designates an accessible front to be excavated by miners
   */
  public designateDigFront(front: DigFront): DigTask | null {
    return this.addDigTask(front.x, front.y);
  }

  /**
   * Queen autonomously evaluates accessible dig fronts and orders excavation
   * if active dig tasks are too low (< threshold).
   */
  public evaluateQueenDigOrders(threshold = 3): DigTask | null {
    const queen = this.state.ants.find((a) => a.caste === 'QUEEN');
    return evaluateQueenDigOrders(
      queen,
      this.state.grid,
      this.state.digTasks,
      (x, y) => this.addDigTask(x, y),
      threshold
    );
  }

  /**
   * Queen autonomously evaluates available unassigned cavities and designates them.
   * Reuses the existing designateRoomAt system identically to manual designation.
   */
  public evaluateQueenRoomOrders(): ColonyRoom | null {
    const queen = this.state.ants.find((a) => a.caste === 'QUEEN');
    const designated = evaluateQueenRoomOrders(
      queen,
      this.state.grid,
      (x, y, type) => this.designateRoomAt(x, y, type)
    );
    if (designated) {
      this.notify();
    }
    return designated;
  }

  /**
   * Executes a structured QueenRoomOrder (used by Queen or future JEV integration)
   */
  public executeQueenRoomOrder(order: QueenRoomOrder): ColonyRoom | null {
    const queen = this.state.ants.find((a) => a.caste === 'QUEEN');
    const designated = executeQueenRoomOrder(
      order,
      this.state.grid,
      (x, y, type) => this.designateRoomAt(x, y, type),
      queen
    );
    if (designated) {
      this.notify();
    }
    return designated;
  }

  /**
   * Returns list of currently unassigned excavated cavities ready to be designated
   */
  public getAvailableCavities(): ColonyRoom[] {
    return getAvailableCavities(this.state.grid);
  }

  /**
   * Returns current Queen room decision if an available cavity exists
   */
  public decideQueenRoomOrder(): QueenRoomOrder | null {
    const queen = this.state.ants.find((a) => a.caste === 'QUEEN');
    return decideQueenRoomOrder(queen, this.state.grid);
  }

  /**
   * Designates all accessible digging fronts at once
   */
  public designateAllAccessibleFronts(): number {
    const fronts = this.getAccessibleDigFronts();
    let added = 0;
    for (const f of fronts) {
      if (!this.state.digTasks.some((t) => t.x === f.x && t.y === f.y)) {
        this.addDigTask(f.x, f.y);
        added++;
      }
    }
    return added;
  }

  /**
   * Carves an organic horizontal tunnel
   */
  public digHorizontal(startX: number, endX: number, y: number): number {
    const count = digHorizontalTunnel(this.state.grid, startX, endX, y, this.tickCount);
    if (count > 0) {
      soundEngine.playDig(true);
      this.notify();
    }
    return count;
  }

  /**
   * Carves an organic vertical shaft / well (puits)
   */
  public digVertical(x: number, startY: number, endY: number, width = 1): number {
    const count = digVerticalShaft(this.state.grid, x, startY, endY, width, this.tickCount);
    if (count > 0) {
      soundEngine.playDig(true);
      this.notify();
    }
    return count;
  }

  /**
   * Carves an organic rounded cavity or chamber
   */
  public digCavity(centerX: number, centerY: number, radiusX = 3, radiusY = 2): number {
    const count = digOrganicCavity(this.state.grid, centerX, centerY, radiusX, radiusY, this.tickCount);
    if (count > 0) {
      soundEngine.playRoomFormed();
      this.notify();
    }
    return count;
  }

  /**
   * Reads virtual pheromone signals in sensory perimeter around an ant
   */
  public getLocalSignals(
    ant: Ant,
    typeFilter?: PheromoneSignalType,
    radius?: number
  ): LocalSignalInfo[] {
    return stigmergyEngine.getLocalSignals(ant, typeFilter, radius);
  }

  /**
   * Depositing a virtual pheromone signal on the terrain
   */
  public depositSignal(
    x: number,
    y: number,
    type: PheromoneSignalType,
    amount: number
  ): number {
    return stigmergyEngine.depositSignal(x, y, type, amount);
  }

  /**
   * Retrieves pheromone concentration at coordinates
   */
  public getSignal(x: number, y: number, type: PheromoneSignalType): number {
    return stigmergyEngine.getSignal(x, y, type);
  }

  /**
   * Clears all virtual pheromone trails
   */
  public clearSignals(): void {
    stigmergyEngine.clearAll();
    this.notify();
  }
}

export const colonyEngine = new ColonyEngine();
export {
  evaluateQueenDigOrders,
  evaluateQueenRoomOrders,
  executeQueenRoomOrder,
  decideQueenRoomOrder,
  getAvailableCavities,
  type QueenRoomOrder,
} from './antAI';
