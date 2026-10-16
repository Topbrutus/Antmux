import React, { useRef, useEffect, useState, useCallback } from 'react';
import { ColonyEngineState, colonyEngine } from '../simulation/colonyEngine';
import { GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, STRATA, ROOM_PRESETS, getStratumAtRow } from '../simulation/grid';
import { getVolumeSliceTiles } from '../simulation/volume3d';
import { ActiveTool, Ant, RoomType } from '../types/colony';
import { Layers, Box, Eye, ChevronUp, ChevronDown, Sparkles } from 'lucide-react';
import { TerrainShaderRenderer } from '../rendering/terrainShaderRenderer';

interface SoilParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  alpha: number;
  decay: number;
  gravity: number;
  drag?: number;
  sparkle?: boolean;
  kind?: 'falling_earth_powder' | 'crumb' | 'dust_puff' | 'ceiling_trickle' | 'footstep_puff' | 'trail_wisp' | 'crystal_sparkle' | 'warmth_spore';
  wobblePhase?: number;
  wobbleSpeed?: number;
  bounces?: number;
  isSettled?: boolean;
}

function getSoilColorsForDepth(depthRow: number, isCrystal: boolean = false): string[] {
  if (isCrystal || depthRow >= 85) {
    return ['#38bdf8', '#7dd3fc', '#bae6fd', '#0284c7', '#64748b'];
  }
  if (depthRow <= 28) {
    // Humus / Upper Soil
    return ['#8a5e3a', '#a16207', '#78350f', '#5c3a21', '#92400e'];
  }
  if (depthRow <= 55) {
    // Clay / Dense
    return ['#b46738', '#c2410c', '#9a3412', '#7c2d12', '#d97706'];
  }
  if (depthRow <= 84) {
    // Mineral / Rock
    return ['#64748b', '#94a3b8', '#475569', '#334155', '#cbd5e1'];
  }
  // Deep Abyssal
  return ['#1e1b4b', '#38bdf8', '#818cf8', '#6366f1', '#0f172a'];
}

interface SubterraneanCanvasProps {
  engineState: ColonyEngineState;
  activeTool: ActiveTool;
  selectedRoomType: RoomType;
  brushRadius: number;
  onManualDig: (x: number, y: number, radius: number, z: number) => void;
  onDesignateDig: (x: number, y: number) => void;
  onDesignateRoom: (x: number, y: number, type: RoomType) => void;
  onSelectAnt: (id: string | null) => void;
  onSelectRoom: (id: string | null) => void;
  onSelectCell?: (coords: { x: number; y: number } | null) => void;
  selectedCellCoords?: { x: number; y: number } | null;
  focusedDepth?: number;
}

export const SubterraneanCanvas: React.FC<SubterraneanCanvasProps> = ({
  engineState,
  activeTool,
  selectedRoomType,
  brushRadius,
  onManualDig,
  onDesignateDig,
  onDesignateRoom,
  onSelectAnt,
  onSelectRoom,
  onSelectCell,
  selectedCellCoords,
  focusedDepth,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const shaderCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const terrainShaderRef = useRef<TerrainShaderRenderer | null>(null);
  const [useProceduralShaders, setUseProceduralShaders] = useState<boolean>(true);
  const [isShaderSupported, setIsShaderSupported] = useState<boolean>(true);

  // Initialize WebGL Procedural Terrain Shader Renderer
  useEffect(() => {
    if (shaderCanvasRef.current && !terrainShaderRef.current) {
      const renderer = new TerrainShaderRenderer({ worldSeed: engineState.grid.worldSeed });
      const success = renderer.init(shaderCanvasRef.current, engineState.grid.worldSeed);
      if (success) {
        terrainShaderRef.current = renderer;
        setIsShaderSupported(true);
      } else {
        setIsShaderSupported(false);
      }
    }
    return () => {
      terrainShaderRef.current?.destroy();
      terrainShaderRef.current = null;
    };
  }, [engineState.grid.worldSeed]);

  // Camera viewport state (world pixel coordinates)
  const [camera, setCamera] = useState({
    x: (GRID_WIDTH * TILE_SIZE) / 2,
    y: 41 * TILE_SIZE,
    zoom: 1.1,
  });

  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isInteracting, setIsInteracting] = useState(false);
  const [hoverTile, setHoverTile] = useState<{ x: number; y: number } | null>(null);

  // Volumetric scan: the camera starts inside the terrain at the central slice.
  const [depthViewMode, setDepthViewMode] = useState<'volume' | 'single'>('volume');
  const [selectedZLayer, setSelectedZLayer] = useState<number>(41);
  const [volumeOpacity, setVolumeOpacity] = useState<number>(0.75); // 0.2 to 1.0 opacity strength
  const [isDepthPanelCollapsed, setIsDepthPanelCollapsed] = useState<boolean>(false);
  const scanRadius = Math.max(2, Math.min(14, Math.round(3 + (1.35 - camera.zoom) * 12)));

  // Sync depth layer with focusedDepth if provided
  useEffect(() => {
    if (focusedDepth !== undefined) {
      setSelectedZLayer(Math.max(0, Math.min(83, Math.round(focusedDepth))));
    }
  }, [focusedDepth]);

  // Dust motes for subterranean atmosphere
  const dustMotesRef = useRef<Array<{ x: number; y: number; vx: number; vy: number; size: number; alpha: number }>>([]);
  // Dynamic soil, chipping, footstep puffs, crumbling trickles & crystal sparkles
  const dynamicParticlesRef = useRef<SoilParticle[]>([]);

  useEffect(() => {
    // Atmospheric and deep mineral dust motes placed across excavated cavities and deep veins
    const upperExcavated: Array<{ x: number; y: number }> = [];
    const deepExcavated: Array<{ x: number; y: number }> = [];
    const { tiles } = engineState.grid;

    for (let y = 7; y < GRID_HEIGHT; y++) {
      for (let x = 0; x < GRID_WIDTH; x++) {
        if (tiles[y]?.[x] === 'AIR') {
          if (y >= 56) {
            deepExcavated.push({ x, y });
          } else {
            upperExcavated.push({ x, y });
          }
        }
      }
    }

    // Generate 140 motes: abundant deep mineral & crystal dust particles in deep zones
    dustMotesRef.current = Array.from({ length: 140 }, (_, i) => {
      let coord: { x: number; y: number };
      const isDeepMote = i >= 40; // 100 motes allocated to deeper subterranean strata
      if (isDeepMote && deepExcavated.length > 0) {
        coord = deepExcavated[i % deepExcavated.length];
      } else if (upperExcavated.length > 0) {
        coord = upperExcavated[i % upperExcavated.length];
      } else {
        coord = { x: 41, y: 15 + (i % 60) };
      }

      return {
        x: (coord.x + Math.random()) * TILE_SIZE,
        y: (coord.y + Math.random()) * TILE_SIZE,
        vx: (Math.random() - 0.5) * (isDeepMote ? 0.09 : 0.14),
        vy: -0.04 + (Math.random() - 0.5) * 0.10, // Gentle upward subterranean draft
        size: isDeepMote ? 0.8 + Math.random() * 2.4 : 0.7 + Math.random() * 1.6,
        alpha: isDeepMote ? 0.25 + Math.random() * 0.45 : 0.14 + Math.random() * 0.24,
      };
    });
  }, []);

  const spawnDigBurst = useCallback(
    (
      gridX: number,
      gridY: number,
      radius: number = 1,
      isManual: boolean = true,
      isCrystalHint: boolean = false,
      liberatedDust: number = 0
    ) => {
      if (gridX < 0 || gridX >= GRID_WIDTH || gridY < 7 || gridY >= GRID_HEIGHT) return;
      const tile = engineState.grid.tiles[gridY]?.[gridX];
      const isCrystal = isCrystalHint || tile === 'VEIN_CRYSTAL' || gridY >= 85 || liberatedDust > 0;
      const colors = getSoilColorsForDepth(gridY, isCrystal);
      const count = isManual ? 14 + radius * 8 : 10;

      // 1. Cascading soil crumbs (chipped sediment arcing outward)
      for (let i = 0; i < count; i++) {
        if (dynamicParticlesRef.current.length >= 380) break;
        const angle = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 1.6;
        const speed = 0.8 + Math.random() * (isManual ? 3.0 : 2.2);
        const offset = (Math.random() * radius * 0.7) * TILE_SIZE;
        const px = (gridX + 0.5) * TILE_SIZE + Math.cos(angle) * offset;
        const py = (gridY + 0.5) * TILE_SIZE + Math.sin(angle) * offset;

        dynamicParticlesRef.current.push({
          x: px,
          y: py,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 0.6,
          size: 0.8 + Math.random() * 2.2,
          color: colors[Math.floor(Math.random() * colors.length)],
          alpha: 0.8 + Math.random() * 0.2,
          decay: 0.012 + Math.random() * 0.015,
          gravity: 0.08 + Math.random() * 0.04,
          drag: 0.96,
          sparkle: isCrystal && Math.random() < 0.45,
          kind: 'crumb',
        });
      }

      // 2. Soft billowing soil dust clouds
      const puffCount = isManual ? 4 + radius * 2 : 3;
      for (let i = 0; i < puffCount; i++) {
        if (dynamicParticlesRef.current.length >= 380) break;
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.2 + Math.random() * 0.7;
        dynamicParticlesRef.current.push({
          x: (gridX + 0.5) * TILE_SIZE + (Math.random() - 0.5) * 6,
          y: (gridY + 0.5) * TILE_SIZE + (Math.random() - 0.5) * 6,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 0.1,
          size: 2.0 + Math.random() * 2.5,
          color: colors[0],
          alpha: 0.24 + Math.random() * 0.16,
          decay: 0.007 + Math.random() * 0.008,
          gravity: -0.004,
          drag: 0.93,
          kind: 'dust_puff',
          wobblePhase: Math.random() * Math.PI * 2,
          wobbleSpeed: 0.04,
        });
      }

      // 3. Sparkling crystalline micro-facets in crystal strata or crystal dust zones
      if (isCrystal) {
        const sparkleCount = 4 + (liberatedDust > 0 ? 6 : 2);
        for (let i = 0; i < sparkleCount; i++) {
          if (dynamicParticlesRef.current.length >= 380) break;
          const angle = Math.random() * Math.PI * 2;
          const speed = 0.5 + Math.random() * 1.8;
          dynamicParticlesRef.current.push({
            x: (gridX + 0.5) * TILE_SIZE + (Math.random() - 0.5) * 8,
            y: (gridY + 0.5) * TILE_SIZE + (Math.random() - 0.5) * 8,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed - 0.5,
            size: 1.2 + Math.random() * 1.8,
            color: Math.random() < 0.6 ? '#7dd3fc' : '#38bdf8',
            alpha: 0.85 + Math.random() * 0.15,
            decay: 0.014 + Math.random() * 0.015,
            gravity: 0.02,
            sparkle: true,
            kind: 'crystal_sparkle',
          });
        }
      }

      // 4. Subtle ceiling trickle directly above excavation if solid rock above
      if (gridY > 7 && engineState.grid.tiles[gridY - 1]?.[gridX] !== 'AIR') {
        const trickleCount = 2 + Math.floor(Math.random() * 2);
        for (let i = 0; i < trickleCount; i++) {
          if (dynamicParticlesRef.current.length >= 400) break;
          dynamicParticlesRef.current.push({
            x: gridX * TILE_SIZE + Math.random() * TILE_SIZE,
            y: (gridY - 0.1) * TILE_SIZE,
            vx: (Math.random() - 0.5) * 0.25,
            vy: 0.3 + Math.random() * 0.5,
            size: 0.7 + Math.random() * 1.2,
            color: colors[Math.floor(Math.random() * colors.length)],
            alpha: 0.55 + Math.random() * 0.3,
            decay: 0.014 + Math.random() * 0.012,
            gravity: 0.08,
            drag: 0.98,
            kind: 'ceiling_trickle',
          });
        }
      }

      // 5. Shower of fine falling earth powder ("tomber en poudre comme de la terre")
      const powderCount = isManual ? 14 + radius * 6 : 8;
      for (let i = 0; i < powderCount; i++) {
        if (dynamicParticlesRef.current.length >= 420) break;
        const px = (gridX + 0.5) * TILE_SIZE + (Math.random() - 0.5) * 7;
        const py = (gridY + 0.5) * TILE_SIZE + (Math.random() - 0.5) * 7;
        dynamicParticlesRef.current.push({
          x: px,
          y: py,
          vx: (Math.random() - 0.5) * 0.9,
          vy: 0.3 + Math.random() * 0.8,
          size: 1.0 + Math.random() * 1.5,
          color: colors[Math.floor(Math.random() * colors.length)],
          alpha: 0.85 + Math.random() * 0.15,
          decay: 0.007 + Math.random() * 0.007,
          gravity: 0.14 + Math.random() * 0.06,
          drag: 0.97,
          wobblePhase: Math.random() * Math.PI * 2,
          wobbleSpeed: 0.06,
          kind: 'falling_earth_powder',
        });
      }
    },
    [engineState.grid.tiles]
  );

  // Subscribe to excavation events from colony engine (worker ants or manual digging)
  useEffect(() => {
    const unsubDig = colonyEngine.onDig((event) => {
      spawnDigBurst(event.x, event.y, event.radius, event.isManual, event.isCrystal, event.liberatedDust);
    });
    return () => unsubDig();
  }, [spawnDigBurst]);

  // Smooth jump to focused depth if requested
  useEffect(() => {
    if (focusedDepth !== undefined) {
      setCamera((prev) => ({
        ...prev,
        y: focusedDepth * TILE_SIZE,
      }));
    }
  }, [focusedDepth]);

  // Convert screen coordinates to world grid coordinates
  const screenToWorld = useCallback(
    (screenX: number, screenY: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return { gridX: 0, gridY: 0, worldX: 0, worldY: 0 };
      const rect = canvas.getBoundingClientRect();
      const clientX = screenX - rect.left;
      const clientY = screenY - rect.top;

      const worldX = (clientX - rect.width / 2) / camera.zoom + camera.x;
      const worldY = (clientY - rect.height / 2) / camera.zoom + camera.y;

      const gridX = Math.floor(worldX / TILE_SIZE);
      const gridY = Math.floor(worldY / TILE_SIZE);

      return { gridX, gridY, worldX, worldY };
    },
    [camera]
  );

  // Mouse wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    setCamera((prev) => ({
      ...prev,
      zoom: Math.max(0.4, Math.min(2.5, prev.zoom * zoomFactor)),
    }));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
      // Middle click or Shift+Left click to pan
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
      return;
    }

    if (e.button === 0) {
      const { gridX, gridY, worldX, worldY } = screenToWorld(e.clientX, e.clientY);

      // Check if clicked directly on an ant
      if (activeTool === 'INSPECT_ANT') {
        const clickedAnt = engineState.ants.find((ant) => {
          const antPx = ant.x * TILE_SIZE + TILE_SIZE / 2;
          const antPy = ant.y * TILE_SIZE + TILE_SIZE / 2;
          return Math.hypot(worldX - antPx, worldY - antPy) < 14;
        });

        if (clickedAnt) {
          onSelectAnt(clickedAnt.id);
          onSelectRoom(null);
          onSelectCell?.(null);
          return;
        }

        // Check if clicked in a room
        const clickedRoom = engineState.grid.rooms.find((room) =>
          room.tiles.some((t) => t.x === gridX && t.y === gridY)
        );
        if (clickedRoom) {
          onSelectRoom(clickedRoom.id);
          onSelectAnt(null);
          onSelectCell?.(null);
          return;
        }

        // If clicked on a subterranean cell
        if (gridX >= 0 && gridX < GRID_WIDTH && gridY >= 7 && gridY < GRID_HEIGHT) {
          onSelectCell?.({ x: gridX, y: gridY });
          onSelectAnt(null);
          onSelectRoom(null);
          return;
        }

        onSelectAnt(null);
        onSelectRoom(null);
        onSelectCell?.(null);
      } else if (activeTool === 'DIG_MANUAL') {
        setIsInteracting(true);
        spawnDigBurst(gridX, gridY, brushRadius);
        onManualDig(gridX, gridY, brushRadius, selectedZLayer);
      } else if (activeTool === 'DESIGNATE_DIG') {
        setIsInteracting(true);
        onDesignateDig(gridX, gridY);
      } else if (activeTool === 'DESIGNATE_ROOM') {
        onDesignateRoom(gridX, gridY, selectedRoomType);
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const { gridX, gridY } = screenToWorld(e.clientX, e.clientY);
    setHoverTile({ x: gridX, y: gridY });

    if (isDragging) {
      const dx = (e.clientX - dragStart.x) / camera.zoom;
      const dy = (e.clientY - dragStart.y) / camera.zoom;
      setCamera((prev) => ({
        ...prev,
        x: Math.max(0, Math.min(GRID_WIDTH * TILE_SIZE, prev.x - dx)),
        y: Math.max(0, Math.min(GRID_HEIGHT * TILE_SIZE, prev.y - dy)),
      }));
      setDragStart({ x: e.clientX, y: e.clientY });
    } else if (isInteracting) {
      if (activeTool === 'DIG_MANUAL') {
        spawnDigBurst(gridX, gridY, brushRadius);
        onManualDig(gridX, gridY, brushRadius, selectedZLayer);
      } else if (activeTool === 'DESIGNATE_DIG') {
        onDesignateDig(gridX, gridY);
      }
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsInteracting(false);
  };

  // Main Render Loop
  useEffect(() => {
    let animationFrameId: number;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    const render = () => {
      // High-DPI / Retina Resolution scaling
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const clientW = canvas.clientWidth;
      const clientH = canvas.clientHeight;
      if (canvas.width !== Math.floor(clientW * dpr) || canvas.height !== Math.floor(clientH * dpr)) {
        canvas.width = Math.floor(clientW * dpr);
        canvas.height = Math.floor(clientH * dpr);
      }

      // 1. Render WebGL Procedural Soil Shaders on background canvas
      const shaderActive = useProceduralShaders && isShaderSupported && !!terrainShaderRef.current;
      if (shaderActive && shaderCanvasRef.current && terrainShaderRef.current) {
        terrainShaderRef.current.updateGridData(
          engineState.grid.cells || engineState.grid.tiles,
          engineState.grid.revealed,
          engineState.grid.hardness
        );
        terrainShaderRef.current.render(
          shaderCanvasRef.current,
          camera,
          dpr,
          depthViewMode,
          selectedZLayer,
          volumeOpacity,
          engineState.grid.worldSeed
        );
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      if (shaderActive) {
        ctx.clearRect(0, 0, clientW, clientH);
      } else {
        ctx.fillStyle = '#07080d';
        ctx.fillRect(0, 0, clientW, clientH);
      }

      // Camera transformation
      ctx.translate(clientW / 2, clientH / 2);
      ctx.scale(camera.zoom, camera.zoom);
      ctx.translate(-camera.x, -camera.y);

      const { grid, ants, digTasks, brood } = engineState;
      const renderTiles = getVolumeSliceTiles(grid.volume, selectedZLayer, grid.tiles);

      // 1. Draw Geological Strata Background & Atmospheric Surface
      for (const stratum of STRATA) {
        const sy = stratum.startRow * TILE_SIZE;
        const sh = (stratum.endRow - stratum.startRow + 1) * TILE_SIZE;

        if (stratum.id === 0) {
          // Atmospheric daylight sky gradient with aerial haze
          const skyGrad = ctx.createLinearGradient(0, 0, 0, sy + sh);
          skyGrad.addColorStop(0, '#3b82f6');
          skyGrad.addColorStop(0.35, '#60a5fa');
          skyGrad.addColorStop(0.75, '#93c5fd');
          skyGrad.addColorStop(0.95, '#bfdbfe');
          skyGrad.addColorStop(1, '#86efac');
          ctx.fillStyle = skyGrad;
          ctx.fillRect(0, sy, GRID_WIDTH * TILE_SIZE, sh);

          // Distant soft cumulus cloud silhouettes
          ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
          ctx.beginPath();
          ctx.ellipse(18 * TILE_SIZE, 3 * TILE_SIZE, 36, 12, 0, 0, Math.PI * 2);
          ctx.ellipse(23 * TILE_SIZE, 2.5 * TILE_SIZE, 28, 10, 0, 0, Math.PI * 2);
          ctx.ellipse(65 * TILE_SIZE, 3.5 * TILE_SIZE, 42, 14, 0, 0, Math.PI * 2);
          ctx.ellipse(72 * TILE_SIZE, 3 * TILE_SIZE, 30, 11, 0, 0, Math.PI * 2);
          ctx.fill();

          // Organic fertile topsoil crust line
          const soilCrustGrad = ctx.createLinearGradient(0, (stratum.endRow - 0.8) * TILE_SIZE, 0, stratum.endRow * TILE_SIZE);
          soilCrustGrad.addColorStop(0, '#15803d');
          soilCrustGrad.addColorStop(0.5, '#4d7c0f');
          soilCrustGrad.addColorStop(1, '#78350f');
          ctx.fillStyle = soilCrustGrad;
          ctx.fillRect(0, (stratum.endRow - 0.8) * TILE_SIZE, GRID_WIDTH * TILE_SIZE, TILE_SIZE);

          // Animated Procedural Grass Blades swaying gently with wind
          const grassTime = Date.now() * 0.0024;
          for (let gx = 0; gx < GRID_WIDTH * TILE_SIZE; gx += 3.5) {
            const wind = Math.sin(grassTime + gx * 0.035) * 2.6;
            const bladeHeight = 5 + (Math.sin(gx * 73) + 1) * 3.5;
            const basePy = (stratum.endRow - 0.3) * TILE_SIZE;

            ctx.strokeStyle = gx % 7 === 0 ? '#86efac' : gx % 4 === 0 ? '#4ade80' : '#22c55e';
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(gx, basePy);
            ctx.quadraticCurveTo(gx + wind * 0.45, basePy - bladeHeight * 0.6, gx + wind, basePy - bladeHeight);
            ctx.stroke();

            // Tiny morning flower dew drops on occasional tips
            if (gx % 28 === 0) {
              ctx.fillStyle = '#ffffff';
              ctx.beginPath();
              ctx.arc(gx + wind, basePy - bladeHeight, 0.8, 0, Math.PI * 2);
              ctx.fill();
            }
          }

          // Ant Mound crater entrance: textured stratified dome
          const moundCenterX = 41.5 * TILE_SIZE;
          const moundBaseY = stratum.endRow * TILE_SIZE;
          const moundGrad = ctx.createRadialGradient(
            moundCenterX,
            moundBaseY - 14,
            4,
            moundCenterX,
            moundBaseY,
            46
          );
          moundGrad.addColorStop(0, '#92400e');
          moundGrad.addColorStop(0.6, '#78350f');
          moundGrad.addColorStop(1, '#451a03');

          ctx.fillStyle = moundGrad;
          ctx.beginPath();
          ctx.moveTo((41 - 5.5) * TILE_SIZE, moundBaseY);
          ctx.quadraticCurveTo(moundCenterX, moundBaseY - 4.2 * TILE_SIZE, (42 + 5.5) * TILE_SIZE, moundBaseY);
          ctx.fill();

          // Organic crumbly pebble specks on ant mound
          ctx.fillStyle = 'rgba(255, 255, 255, 0.12)';
          for (let pi = -4; pi <= 4; pi++) {
            const pxPos = moundCenterX + pi * 8 + (Math.sin(pi * 17) * 4);
            const pyPos = moundBaseY - 12 + Math.abs(pi) * 2;
            ctx.fillRect(pxPos, pyPos, 1.8, 1.4);
          }

          // Dark burrow mouth shadow arch
          ctx.fillStyle = '#0d0805';
          ctx.beginPath();
          ctx.ellipse(moundCenterX, moundBaseY - 4, 12, 6, 0, 0, Math.PI * 2);
          ctx.fill();

          // Crepuscular sunbeams filtering down into the entrance shaft
          ctx.save();
          ctx.globalCompositeOperation = 'lighter';
          const sunbeam = ctx.createLinearGradient(moundCenterX - 15, 0, moundCenterX + 25, 22 * TILE_SIZE);
          sunbeam.addColorStop(0, 'rgba(254, 240, 138, 0.22)');
          sunbeam.addColorStop(0.35, 'rgba(253, 224, 71, 0.1)');
          sunbeam.addColorStop(0.85, 'rgba(251, 191, 36, 0.03)');
          sunbeam.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = sunbeam;
          ctx.beginPath();
          ctx.moveTo(moundCenterX - 16, 0);
          ctx.lineTo(moundCenterX + 16, 0);
          ctx.lineTo(moundCenterX + 36, 22 * TILE_SIZE);
          ctx.lineTo(moundCenterX - 28, 22 * TILE_SIZE);
          ctx.closePath();
          ctx.fill();
          ctx.restore();
        } else if (!shaderActive) {
          // Underground Strata base colors with rich organic geological depth
          const stratumColors: Record<number, [string, string]> = {
            1: ['#54361e', '#3d2412'], // Humus: warm rich dark loam
            2: ['#7c3d12', '#542308'], // Dense Clay: deep terracotta ochre
            3: ['#282e3f', '#1c2130'], // Slate & Rock: cool stratified mineral slate
            4: ['#111a2f', '#090f1d'], // Deep Crystal Slate: dark midnight basalt
            5: ['#0c0a17', '#050409'], // Abyssal Bedrock: pitch volcanic obsidian
          };

          const [c1, c2] = stratumColors[stratum.id] || ['#262626', '#171717'];
          const grad = ctx.createLinearGradient(0, sy, 0, sy + sh);
          grad.addColorStop(0, c1);
          grad.addColorStop(1, c2);
          ctx.fillStyle = grad;
          ctx.fillRect(0, sy, GRID_WIDTH * TILE_SIZE, sh);

          // High-definition geological striations with organic wave variation
          ctx.strokeStyle = stratum.id >= 4 ? 'rgba(56, 189, 248, 0.04)' : 'rgba(255, 255, 255, 0.035)';
          ctx.lineWidth = 1;
          for (let row = stratum.startRow; row <= stratum.endRow; row += 2) {
            ctx.beginPath();
            ctx.moveTo(0, row * TILE_SIZE + Math.sin(row * 1.7) * 3);
            ctx.lineTo(GRID_WIDTH * TILE_SIZE, row * TILE_SIZE + Math.cos(row * 1.3) * 3);
            ctx.stroke();
          }

          // Embedded mineral flecks and micro-fossils inside deep strata
          if (stratum.id === 3 || stratum.id === 4) {
            ctx.fillStyle = 'rgba(203, 213, 225, 0.08)';
            for (let fx = 10; fx < GRID_WIDTH * TILE_SIZE; fx += 32) {
              const fy = sy + ((fx * 37) % (sh - 8)) + 4;
              ctx.fillRect(fx, fy, 2, 1.5);
            }
          }
        }
      }

      // 2. Draw Tiles (Air, Veins, Crystals, Rock)
      const visibleMinX = Math.max(0, Math.floor((camera.x - clientW / (2 * camera.zoom)) / TILE_SIZE) - 1);
      const visibleMaxX = Math.min(GRID_WIDTH - 1, Math.ceil((camera.x + clientW / (2 * camera.zoom)) / TILE_SIZE) + 1);
      const visibleMinY = Math.max(0, Math.floor((camera.y - clientH / (2 * camera.zoom)) / TILE_SIZE) - 1);
      const visibleMaxY = Math.min(GRID_HEIGHT - 1, Math.ceil((camera.y + clientH / (2 * camera.zoom)) / TILE_SIZE) + 1);

      if (depthViewMode === 'volume' && scanRadius > 0) {
        for (let sliceOffset = scanRadius; sliceOffset >= -scanRadius; sliceOffset--) {
          if (sliceOffset === 0) continue;
          const sliceZ = selectedZLayer + sliceOffset;
          if (sliceZ < 0 || sliceZ >= grid.volume.depth) continue;
          const sliceTiles = getVolumeSliceTiles(grid.volume, sliceZ, grid.tiles);
          const depthRatio = Math.abs(sliceOffset) / scanRadius;
          ctx.save();
          ctx.globalAlpha = 0.06 + (1 - depthRatio) * 0.12;
          ctx.translate(sliceOffset * 3.2, sliceOffset * 1.35);
          for (let y = visibleMinY; y <= visibleMaxY; y++) {
            for (let x = visibleMinX; x <= visibleMaxX; x++) {
              if (sliceTiles[y]?.[x] !== 'AIR') continue;
              ctx.fillStyle = '#05070d';
              ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
              ctx.strokeStyle = 'rgba(56, 189, 248, 0.28)';
              ctx.strokeRect(x * TILE_SIZE + 0.5, y * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
            }
          }
          ctx.restore();
        }
      }

      for (let y = visibleMinY; y <= visibleMaxY; y++) {
        for (let x = visibleMinX; x <= visibleMaxX; x++) {
          const tile = renderTiles[y]?.[x] ?? 'DIRT_HUMUS';
          const isRevealed = grid.revealed[y][x];
          const px = x * TILE_SIZE;
          const py = y * TILE_SIZE;
          const currentStratum = getStratumAtRow(y);

          if (tile === 'AIR') {
            // Check neighbor walkability to render organic connected gallery contours
            const isUpAir = y > 0 && grid.tiles[y - 1]?.[x] === 'AIR';
            const isDownAir = y < GRID_HEIGHT - 1 && grid.tiles[y + 1]?.[x] === 'AIR';
            const isLeftAir = x > 0 && grid.tiles[y]?.[x - 1] === 'AIR';
            const isRightAir = x < GRID_WIDTH - 1 && grid.tiles[y]?.[x + 1] === 'AIR';

            const isUpLeftAir = y > 0 && x > 0 && grid.tiles[y - 1]?.[x - 1] === 'AIR';
            const isUpRightAir = y > 0 && x < GRID_WIDTH - 1 && grid.tiles[y - 1]?.[x + 1] === 'AIR';
            const isDownLeftAir = y < GRID_HEIGHT - 1 && x > 0 && grid.tiles[y + 1]?.[x - 1] === 'AIR';
            const isDownRightAir = y < GRID_HEIGHT - 1 && x < GRID_WIDTH - 1 && grid.tiles[y + 1]?.[x + 1] === 'AIR';

            if (!shaderActive) {
              // 1. Excavated tunnel base cavity: rich dark subterranean void
              ctx.fillStyle = '#17110c';
              ctx.fillRect(px, py, TILE_SIZE, TILE_SIZE);

            // Get stratum base earth color for natural rounded rock fillets
            const currentStratum = getStratumAtRow(y);
            const stratumColor =
              currentStratum.id === 1
                ? '#52341e'
                : currentStratum.id === 2
                ? '#6e3615'
                : currentStratum.id === 3
                ? '#2b303e'
                : currentStratum.id === 4
                ? '#101728'
                : '#0b0914';

            // 2. Organic corner fillets: round convex corners bordering rock
            const filletR = 4;
            // Top-left outer corner
            if (!isUpAir && !isLeftAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px, py);
              ctx.lineTo(px + filletR, py);
              ctx.quadraticCurveTo(px + 1, py + 1, px, py + filletR);
              ctx.closePath();
              ctx.fill();
            }
            // Top-right outer corner
            if (!isUpAir && !isRightAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px + TILE_SIZE, py);
              ctx.lineTo(px + TILE_SIZE - filletR, py);
              ctx.quadraticCurveTo(px + TILE_SIZE - 1, py + 1, px + TILE_SIZE, py + filletR);
              ctx.closePath();
              ctx.fill();
            }
            // Bottom-left outer corner
            if (!isDownAir && !isLeftAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px, py + TILE_SIZE);
              ctx.lineTo(px + filletR, py + TILE_SIZE);
              ctx.quadraticCurveTo(px + 1, py + TILE_SIZE - 1, px, py + TILE_SIZE - filletR);
              ctx.closePath();
              ctx.fill();
            }
            // Bottom-right outer corner
            if (!isDownAir && !isRightAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px + TILE_SIZE, py + TILE_SIZE);
              ctx.lineTo(px + TILE_SIZE - filletR, py + TILE_SIZE);
              ctx.quadraticCurveTo(px + TILE_SIZE - 1, py + TILE_SIZE - 1, px + TILE_SIZE, py + TILE_SIZE - filletR);
              ctx.closePath();
              ctx.fill();
            }

            // 3. Concave inner corner rounding (where both orthogonal neighbors are air, but diagonal is rock)
            if (isUpAir && isLeftAir && !isUpLeftAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px, py);
              ctx.lineTo(px + 3, py);
              ctx.quadraticCurveTo(px + 1, py + 1, px, py + 3);
              ctx.closePath();
              ctx.fill();
            }
            if (isUpAir && isRightAir && !isUpRightAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px + TILE_SIZE, py);
              ctx.lineTo(px + TILE_SIZE - 3, py);
              ctx.quadraticCurveTo(px + TILE_SIZE - 1, py + 1, px + TILE_SIZE, py + 3);
              ctx.closePath();
              ctx.fill();
            }
            if (isDownAir && isLeftAir && !isDownLeftAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px, py + TILE_SIZE);
              ctx.lineTo(px + 3, py + TILE_SIZE);
              ctx.quadraticCurveTo(px + 1, py + TILE_SIZE - 1, px, py + TILE_SIZE - 3);
              ctx.closePath();
              ctx.fill();
            }
            if (isDownAir && isRightAir && !isDownRightAir) {
              ctx.fillStyle = stratumColor;
              ctx.beginPath();
              ctx.moveTo(px + TILE_SIZE, py + TILE_SIZE);
              ctx.lineTo(px + TILE_SIZE - 3, py + TILE_SIZE);
              ctx.quadraticCurveTo(px + TILE_SIZE - 1, py + TILE_SIZE - 1, px + TILE_SIZE, py + TILE_SIZE - 3);
              ctx.closePath();
              ctx.fill();
            }

            // 4. Subtle cavern depth shadows along solid rock edges
            if (!isUpAir) {
              ctx.fillStyle = 'rgba(8, 5, 3, 0.55)';
              ctx.fillRect(px, py, TILE_SIZE, 2.5);
            }
            if (!isDownAir) {
              ctx.fillStyle = 'rgba(70, 42, 23, 0.45)'; // packed soil floor
              ctx.fillRect(px, py + TILE_SIZE - 2, TILE_SIZE, 2);
            }
            if (!isLeftAir) {
              ctx.fillStyle = 'rgba(8, 5, 3, 0.35)';
              ctx.fillRect(px, py, 2, TILE_SIZE);
            }
            if (!isRightAir) {
              ctx.fillStyle = 'rgba(8, 5, 3, 0.35)';
              ctx.fillRect(px + TILE_SIZE - 2, py, 2, TILE_SIZE);
            }

            // 5. Subtle natural loam texture specks
            const speck = (x * 17 + y * 31) % 9;
            if (speck === 0) {
              ctx.fillStyle = 'rgba(255, 255, 255, 0.035)';
              ctx.fillRect(px + 5, py + 5, 2, 2);
            }
          }
        } else {
          if (!shaderActive) {
            // ==========================================
            // SOLID EARTH & ROCK TILE (STRATA 1..5)
            // Enhanced graphical textures, details, and scratching
            // ==========================================
            const currentStratum = getStratumAtRow(y);
            const isBorderingAir =
              (y > 0 && grid.tiles[y - 1]?.[x] === 'AIR') ||
              (y < GRID_HEIGHT - 1 && grid.tiles[y + 1]?.[x] === 'AIR') ||
              (x > 0 && grid.tiles[y]?.[x - 1] === 'AIR') ||
              (x < GRID_WIDTH - 1 && grid.tiles[y]?.[x + 1] === 'AIR');

            // Draw organic solid rock/earth texturing
            if (isBorderingAir) {
              // 1. Subtle rock block face relief & edge bevel highlight
              ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
              ctx.fillRect(px, py, TILE_SIZE, 1);
              ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
              ctx.fillRect(px, py + TILE_SIZE - 1.5, TILE_SIZE, 1.5);

              // 2. Stratum-specific organic textures
              if (currentStratum.id === 1) {
                // Humus / Loam: organic sediment clods & fine rootlets
                const loamHash = (x * 37 + y * 53) % 7;
                if (loamHash === 0) {
                  ctx.fillStyle = '#3a2010';
                  ctx.fillRect(px + 4, py + 5, 2.5, 2);
                  ctx.fillStyle = '#6e4727';
                  ctx.fillRect(px + 6, py + 6, 1.5, 1.5);
                }
                // Dangling fine rootlet peeking into tunnel below
                if (y < GRID_HEIGHT - 1 && grid.tiles[y + 1]?.[x] === 'AIR' && (x * 19 + y * 31) % 5 === 0) {
                  ctx.strokeStyle = '#92400e';
                  ctx.lineWidth = 0.8;
                  ctx.beginPath();
                  ctx.moveTo(px + 4, py + TILE_SIZE);
                  ctx.quadraticCurveTo(px + 5, py + TILE_SIZE + 3, px + 3.5, py + TILE_SIZE + 5);
                  ctx.stroke();
                }
              } else if (currentStratum.id === 2) {
                // Dense Clay: terracotta fissures and silt streaks
                if ((x * 13 + y * 29) % 6 === 0) {
                  ctx.strokeStyle = '#c2410c55';
                  ctx.lineWidth = 0.8;
                  ctx.beginPath();
                  ctx.moveTo(px + 2, py + 3);
                  ctx.lineTo(px + 8, py + 9);
                  ctx.lineTo(px + 12, py + 8);
                  ctx.stroke();
                }
              } else if (currentStratum.id === 3) {
                // Slate & Stone: stratified fracture cleavage and quartz mica flecks
                if ((x * 23 + y * 41) % 5 === 0) {
                  ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
                  ctx.lineWidth = 0.7;
                  ctx.beginPath();
                  ctx.moveTo(px + 1, py + 7);
                  ctx.lineTo(px + TILE_SIZE - 2, py + 6);
                  ctx.stroke();
                }
                if ((x * 47 + y * 19) % 11 === 0) {
                  ctx.fillStyle = '#cbd5e1';
                  ctx.fillRect(px + 5, py + 8, 1.5, 1.5);
                }
              } else if (currentStratum.id >= 4) {
                // Abyssal & Crystal Bedrock: bioluminescent micro-veins
                const pulse = Math.sin(Date.now() * 0.002 + x * 0.6 + y) * 0.3 + 0.7;
                ctx.strokeStyle = currentStratum.id === 5 ? `rgba(168, 85, 247, ${0.25 * pulse})` : `rgba(56, 189, 248, ${0.3 * pulse})`;
                ctx.lineWidth = 0.8;
                ctx.beginPath();
                ctx.moveTo(px + 3, py + 2);
                ctx.lineTo(px + 7, py + 8);
                ctx.lineTo(px + 11, py + 6);
                ctx.stroke();
              }
            }
          }

          // 3. Draw specialized resource veins embedded in the strata
            if (tile === 'VEIN_CRYSTAL') {
              if (isRevealed) {
                // High-fidelity Multi-spire 3D Crystal Geode Cluster
                const pulse = Math.sin(Date.now() * 0.003 + x * 0.5 + y) * 0.25 + 0.85;
                const isAmethyst = y > 90;
                const coreColor = isAmethyst ? '#c084fc' : '#38bdf8';
                const lightFacetColor = isAmethyst ? '#f3e8ff' : '#e0f2fe';
                const glowColor = isAmethyst ? '#a855f7' : '#06b6d4';

                ctx.shadowColor = glowColor;
                ctx.shadowBlur = 10 * pulse;

                // 1. Left secondary crystal spire
                ctx.fillStyle = isAmethyst ? '#9333ea' : '#0284c7';
                ctx.beginPath();
                ctx.moveTo(px + 4, py + 4);
                ctx.lineTo(px + 8, py + 10);
                ctx.lineTo(px + 2, py + 13);
                ctx.closePath();
                ctx.fill();

                // 2. Right auxiliary crystal spire
                ctx.fillStyle = isAmethyst ? '#a855f7' : '#0ea5e9';
                ctx.beginPath();
                ctx.moveTo(px + TILE_SIZE - 3, py + 5);
                ctx.lineTo(px + TILE_SIZE - 1, py + 12);
                ctx.lineTo(px + TILE_SIZE - 7, py + 11);
                ctx.closePath();
                ctx.fill();

                // 3. Main towering central crystal prism
                ctx.fillStyle = coreColor;
                ctx.beginPath();
                ctx.moveTo(px + TILE_SIZE / 2, py + 1.2);
                ctx.lineTo(px + TILE_SIZE - 2.8, py + TILE_SIZE * 0.52);
                ctx.lineTo(px + TILE_SIZE / 2, py + TILE_SIZE - 1.2);
                ctx.lineTo(px + 2.8, py + TILE_SIZE * 0.52);
                ctx.closePath();
                ctx.fill();

                // Bright right refractive facet
                ctx.fillStyle = lightFacetColor;
                ctx.beginPath();
                ctx.moveTo(px + TILE_SIZE / 2, py + 1.2);
                ctx.lineTo(px + TILE_SIZE - 2.8, py + TILE_SIZE * 0.52);
                ctx.lineTo(px + TILE_SIZE / 2, py + TILE_SIZE - 1.2);
                ctx.closePath();
                ctx.fill();

                // Specular diamond sparkle flare dancing on the crystal tip
                const flarePhase = Math.sin(Date.now() * 0.004 + x * 3 + y * 7);
                if (flarePhase > 0.15) {
                  drawDiamondFlare(
                    ctx,
                    px + TILE_SIZE / 2,
                    py + 1.6,
                    3.8 * flarePhase,
                    Date.now() * 0.003,
                    flarePhase
                  );
                }

                ctx.shadowBlur = 0;
              } else {
                ctx.fillStyle = 'rgba(6, 182, 212, 0.22)';
                ctx.fillRect(px + 3, py + 3, TILE_SIZE - 6, TILE_SIZE - 6);
              }
            } else if (tile === 'VEIN_MINERAL') {
              if (isRevealed) {
                // Multi-faceted metallic mineral ore nugget
                ctx.fillStyle = '#64748b';
                ctx.beginPath();
                ctx.moveTo(px + 3, py + 5);
                ctx.lineTo(px + 7, py + 2);
                ctx.lineTo(px + 12, py + 4);
                ctx.lineTo(px + 13, py + 10);
                ctx.lineTo(px + 8, py + 13);
                ctx.lineTo(px + 3, py + 10);
                ctx.closePath();
                ctx.fill();

                // Specular pyrite metallic sheen
                ctx.fillStyle = '#f1f5f9';
                ctx.beginPath();
                ctx.moveTo(px + 6, py + 3);
                ctx.lineTo(px + 9, py + 4);
                ctx.lineTo(px + 7, py + 7);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = '#e2e8f0';
                ctx.fillRect(px + 4, py + 8, 2, 2);
              }
            } else if (tile === 'VEIN_ORGANIC') {
              if (isRevealed) {
                // Translucent glowing amber bio-resin droplet
                const resinGlow = ctx.createRadialGradient(
                  px + TILE_SIZE / 2 - 1,
                  py + TILE_SIZE / 2 - 1,
                  1,
                  px + TILE_SIZE / 2,
                  py + TILE_SIZE / 2,
                  6
                );
                resinGlow.addColorStop(0, '#fef08a');
                resinGlow.addColorStop(0.5, '#d97706');
                resinGlow.addColorStop(1, '#92400e');
                ctx.fillStyle = resinGlow;
                ctx.beginPath();
                ctx.arc(px + TILE_SIZE / 2, py + TILE_SIZE / 2, 4.5, 0, Math.PI * 2);
                ctx.fill();
                // Specular glare reflection
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.beginPath();
                ctx.arc(px + TILE_SIZE / 2 - 1.5, py + TILE_SIZE / 2 - 1.5, 1.2, 0, Math.PI * 2);
                ctx.fill();
              }
            } else if (tile === 'VEIN_FOSSIL') {
              if (isRevealed) {
                // Fossil spiral ammonite shell imprint
                ctx.strokeStyle = '#fef08a';
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                const cx = px + TILE_SIZE / 2;
                const cy = py + TILE_SIZE / 2;
                for (let a = 0; a < Math.PI * 3.5; a += 0.3) {
                  const r = 0.8 + a * 1.1;
                  const fx = cx + Math.cos(a) * r;
                  const fy = cy + Math.sin(a) * r;
                  if (a === 0) ctx.moveTo(fx, fy);
                  else ctx.lineTo(fx, fy);
                }
                ctx.stroke();
              }
            }

            // ==========================================
            // 4. SCRATCHING SYSTEM ("LES BLOCS VONT SE GRATTER")
            // Progressive mandible scratches, claw gouges, fissures, and flaking crumbs
            // ==========================================
            const diggingAnt = engineState.ants.find(
              (a) => a.state === 'DIGGING' && a.targetTile?.x === x && a.targetTile?.y === y
            );
            const digTask = engineState.digTasks.find((t) => t.x === x && t.y === y);
            const currentHardness = engineState.grid.hardness[y]?.[x];
            const isBeingScratched = Boolean(
              diggingAnt || (digTask && digTask.progress > 0) || (currentHardness !== undefined && currentHardness < 0.98)
            );

            if (isBeingScratched) {
              const digProgress = diggingAnt
                ? Math.min(1.0, (diggingAnt.actionTimer * 0.08) + Math.max(0, 1.0 - (currentHardness ?? 0.5)))
                : Math.max(0.2, 1.0 - (currentHardness ?? 0.5));

              // High-frequency impact vibration when ant mandibles scrape against the rock
              const jitterX = diggingAnt ? Math.sin(Date.now() * 0.05 + x * 9 + y * 7) * 0.7 : 0;
              const jitterY = diggingAnt ? Math.cos(Date.now() * 0.05 + x * 9 + y * 7) * 0.7 : 0;

              ctx.save();
              ctx.translate(jitterX, jitterY);

              // A. Deep dark carved scratch shadow furrows
              ctx.strokeStyle = 'rgba(15, 8, 4, 0.85)';
              ctx.lineWidth = 1.6;
              ctx.beginPath();
              // Diagonal claw gouge 1
              ctx.moveTo(px + 2.5, py + 4);
              ctx.lineTo(px + TILE_SIZE - 3.5, py + TILE_SIZE - 4.5);
              // Diagonal claw gouge 2
              ctx.moveTo(px + 5, py + 2.5);
              ctx.lineTo(px + TILE_SIZE - 2, py + TILE_SIZE - 7);
              if (digProgress > 0.35) {
                // Secondary cross-scratch
                ctx.moveTo(px + TILE_SIZE - 3, py + 3.5);
                ctx.lineTo(px + 3.5, py + TILE_SIZE - 3.5);
              }
              if (digProgress > 0.65) {
                // Heavy chipped stress fracture
                ctx.moveTo(px + 7, py + 2);
                ctx.lineTo(px + 8, py + 8);
                ctx.lineTo(px + 13, py + 9);
              }
              ctx.stroke();

              // B. Bright powdered chalk/stone incision highlights (powder crushed under mandibles)
              const powderScratchColor = currentStratum.id >= 4 ? 'rgba(186, 230, 253, 0.85)' : 'rgba(255, 255, 255, 0.65)';
              ctx.strokeStyle = powderScratchColor;
              ctx.lineWidth = 0.9;
              ctx.beginPath();
              ctx.moveTo(px + 3, py + 4.5);
              ctx.lineTo(px + TILE_SIZE - 3, py + TILE_SIZE - 4);
              ctx.moveTo(px + 5.5, py + 3);
              ctx.lineTo(px + TILE_SIZE - 1.5, py + TILE_SIZE - 6.5);
              if (digProgress > 0.35) {
                ctx.moveTo(px + TILE_SIZE - 2.5, py + 4);
                ctx.lineTo(px + 4, py + TILE_SIZE - 3);
              }
              ctx.stroke();

              // C. Chipped edge corner notch where earth flakes away
              ctx.fillStyle = currentStratum.id >= 4 ? '#38bdf8' : '#78350f';
              ctx.beginPath();
              ctx.moveTo(px + 1, py + 1);
              ctx.lineTo(px + 4, py + 1);
              ctx.lineTo(px + 1, py + 4);
              ctx.closePath();
              ctx.fill();

              // D. Dynamic Mandible Contact Spark & Powder Ring at point of scraping
              if (diggingAnt) {
                const antHeadX = diggingAnt.x * TILE_SIZE + TILE_SIZE / 2;
                const antHeadY = diggingAnt.y * TILE_SIZE + TILE_SIZE / 2;
                const blockCenterX = px + TILE_SIZE / 2;
                const blockCenterY = py + TILE_SIZE / 2;
                // Point of contact between ant and block surface
                const contactX = blockCenterX + (antHeadX - blockCenterX) * 0.45;
                const contactY = blockCenterY + (antHeadY - blockCenterY) * 0.45;

                // Bright chipping impact spark
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(contactX, contactY, 1.4, 0, Math.PI * 2);
                ctx.fill();

                // Surrounding powdery micro-crumb halo
                ctx.fillStyle = currentStratum.id >= 4 ? 'rgba(56, 189, 248, 0.7)' : 'rgba(245, 158, 11, 0.7)';
                ctx.beginPath();
                ctx.arc(contactX + (Math.random() - 0.5) * 3, contactY + (Math.random() - 0.5) * 3, 1.0, 0, Math.PI * 2);
                ctx.arc(contactX + (Math.random() - 0.5) * 4, contactY + (Math.random() - 0.5) * 4, 0.8, 0, Math.PI * 2);
                ctx.fill();
              }

              ctx.restore();
            }
          }

          // Fog of War / Unexplored earth veil
          if (!isRevealed && y >= 7) {
            ctx.fillStyle = 'rgba(5, 5, 8, 0.85)';
            ctx.fillRect(px, py, TILE_SIZE, TILE_SIZE);
          }

          // Depth-based rendering overlay (2.5D Volume vs Single Depth Layer)
          if (depthViewMode === 'single') {
            const depthDiff = Math.abs(y - selectedZLayer);
            if (depthDiff > 0.5) {
              const dimFactor = Math.min(0.88, 0.35 + depthDiff * 0.14);
              ctx.fillStyle = `rgba(4, 6, 12, ${dimFactor.toFixed(3)})`;
              ctx.fillRect(px, py, TILE_SIZE, TILE_SIZE);
            } else {
              // Highlight the focused layer slice
              ctx.strokeStyle = 'rgba(251, 191, 36, 0.45)';
              ctx.lineWidth = 1;
              ctx.strokeRect(px + 0.5, py + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
            }
          } else {
            // Entire volume depth-based opacity overlay
            const depthRatio = Math.max(0, Math.min(1, (y - 7) / 84));
            const depthOpacity = depthRatio * 0.38 * volumeOpacity;
            if (depthOpacity > 0.02) {
              ctx.fillStyle = `rgba(3, 4, 8, ${depthOpacity.toFixed(3)})`;
              ctx.fillRect(px, py, TILE_SIZE, TILE_SIZE);
            }
          }
        }
      }

      // 3. Draw the actual cross-section: cavities close when their volume slice ends.
      ctx.save();
      for (let y = 7; y < GRID_HEIGHT; y++) {
        for (let x = 0; x < GRID_WIDTH; x++) {
          if (grid.tiles[y]?.[x] === 'AIR' && renderTiles[y]?.[x] !== 'AIR') {
            const colors = getSoilColorsForDepth(y, y >= 85);
            ctx.fillStyle = colors[(x * 7 + y * 11 + selectedZLayer) % colors.length];
            ctx.globalAlpha = 0.92;
            ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
          }
        }
      }
      ctx.restore();

      // 3. Draw Room Designations & Ambient Tint (Integrated into real excavated geometry)
      if (depthViewMode === 'volume' && scanRadius > 0) {
        ctx.save();
        ctx.lineWidth = 1;
        for (let sliceOffset = scanRadius; sliceOffset >= -scanRadius; sliceOffset--) {
          if (sliceOffset === 0) continue;
          const sliceZ = selectedZLayer + sliceOffset;
          if (sliceZ < 0 || sliceZ > 83) continue;
          const depthRatio = Math.abs(sliceOffset) / scanRadius;
          const offsetX = sliceOffset * 3.2;
          const offsetY = sliceOffset * 1.35;
          const sliceAlpha = 0.035 + (1 - depthRatio) * 0.12;

          for (const room of grid.rooms) {
            const validTiles = room.tiles.filter(
              (t) => t.x >= 0 && t.x < GRID_WIDTH && t.y >= 7 && t.y < GRID_HEIGHT && renderTiles[t.y]?.[t.x] === 'AIR'
            );
            if (validTiles.length === 0) continue;
            ctx.fillStyle = `${room.color}${Math.round(sliceAlpha * 255).toString(16).padStart(2, '0')}`;
            for (const tile of validTiles) {
              ctx.fillRect(tile.x * TILE_SIZE + offsetX, tile.y * TILE_SIZE + offsetY, TILE_SIZE, TILE_SIZE);
            }
            ctx.strokeStyle = `${room.color}${Math.round((sliceAlpha + 0.08) * 255).toString(16).padStart(2, '0')}`;
            const roomX = room.bounds.minX * TILE_SIZE + offsetX;
            const roomY = room.bounds.minY * TILE_SIZE + offsetY;
            const roomW = (room.bounds.maxX - room.bounds.minX + 1) * TILE_SIZE;
            const roomH = (room.bounds.maxY - room.bounds.minY + 1) * TILE_SIZE;
            ctx.strokeRect(roomX, roomY, roomW, roomH);
          }
        }
        ctx.restore();
      }

      for (const room of grid.rooms) {
        // Only consider tiles that are genuinely excavated
        const validTiles = room.tiles.filter(
          (t) => t.x >= 0 && t.x < GRID_WIDTH && t.y >= 7 && t.y < GRID_HEIGHT && renderTiles[t.y]?.[t.x] === 'AIR'
        );
        if (validTiles.length === 0) continue;

        const tileSet = new Set(validTiles.map((t) => `${t.x},${t.y}`));
        const cx = room.center.x * TILE_SIZE + TILE_SIZE / 2;
        const cy = room.center.y * TILE_SIZE + TILE_SIZE / 2;

        // Specific organic treatment for Queen's Royal Chamber
        if (room.type === 'QUEEN') {
          // Warm royal amber aura radiating across the excavated chamber
          const royalGlow = ctx.createRadialGradient(cx, cy, 4, cx, cy, 68);
          royalGlow.addColorStop(0, 'rgba(245, 158, 11, 0.28)');
          royalGlow.addColorStop(0.5, 'rgba(217, 119, 6, 0.16)');
          royalGlow.addColorStop(1, 'rgba(180, 83, 9, 0.04)');
          ctx.fillStyle = royalGlow;
          for (const t of validTiles) {
            ctx.fillRect(t.x * TILE_SIZE, t.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
          }

          // Subterranean royal dais / nesting pedestal in the heart of the chamber
          ctx.save();
          ctx.beginPath();
          ctx.ellipse(cx, cy + 3, 15, 8, 0, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(245, 158, 11, 0.22)';
          ctx.fill();
          ctx.strokeStyle = 'rgba(245, 158, 11, 0.55)';
          ctx.lineWidth = 1.2;
          ctx.stroke();

          // Delicate royal insignia watermark engraved into the stone
          ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(cx - 6, cy - 2);
          ctx.lineTo(cx - 3, cy + 2);
          ctx.lineTo(cx, cy - 4);
          ctx.lineTo(cx + 3, cy + 2);
          ctx.lineTo(cx + 6, cy - 2);
          ctx.stroke();
          ctx.restore();
        } else {
          // Ambient tint for other specialized chambers
          ctx.fillStyle = `${room.color}16`;
          for (const t of validTiles) {
            ctx.fillRect(t.x * TILE_SIZE, t.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
          }
        }

        // Trace borders strictly along the perimeter of excavated room tiles
        ctx.strokeStyle = `${room.color}99`;
        ctx.lineWidth = 1.5;
        for (const t of validTiles) {
          const tx = t.x * TILE_SIZE;
          const ty = t.y * TILE_SIZE;

          if (!tileSet.has(`${t.x},${t.y - 1}`)) {
            ctx.beginPath();
            ctx.moveTo(tx, ty);
            ctx.lineTo(tx + TILE_SIZE, ty);
            ctx.stroke();
          }
          if (!tileSet.has(`${t.x},${t.y + 1}`)) {
            ctx.beginPath();
            ctx.moveTo(tx, ty + TILE_SIZE);
            ctx.lineTo(tx + TILE_SIZE, ty + TILE_SIZE);
            ctx.stroke();
          }
          if (!tileSet.has(`${t.x - 1},${t.y}`)) {
            ctx.beginPath();
            ctx.moveTo(tx, ty);
            ctx.lineTo(tx, ty + TILE_SIZE);
            ctx.stroke();
          }
          if (!tileSet.has(`${t.x + 1},${t.y}`)) {
            ctx.beginPath();
            ctx.moveTo(tx + TILE_SIZE, ty);
            ctx.lineTo(tx + TILE_SIZE, ty + TILE_SIZE);
            ctx.stroke();
          }
        }

        // Integrated Chamber plaque: positioned within the vault ceiling arch
        const labelY = Math.max(room.bounds.minY * TILE_SIZE + 3, cy - 18);
        ctx.save();
        ctx.font = 'bold 9px "Plus Jakarta Sans", sans-serif';
        const labelText = room.type === 'QUEEN' ? `👑 ${room.name}` : room.name;
        const textWidth = ctx.measureText(labelText).width;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
        ctx.strokeStyle = `${room.color}55`;
        ctx.lineWidth = 1;
        const badgeX = cx - textWidth / 2 - 5;
        const badgeY = labelY - 11;
        const badgeW = textWidth + 10;
        const badgeH = 13;

        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 3);
        } else {
          ctx.rect(badgeX, badgeY, badgeW, badgeH);
        }
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = room.color;
        ctx.textAlign = 'center';
        ctx.fillText(labelText, cx, labelY - 1);
        ctx.restore();

        if (room.type === 'QUEEN' && room.hasCommandTerminal) {
          const terminalPosition = room.commandTerminalPosition ?? { x: room.center.x + 1, y: room.center.y };
          const terminalX = terminalPosition.x * TILE_SIZE + 2;
          const terminalY = terminalPosition.y * TILE_SIZE + 2;
          const terminalW = TILE_SIZE - 4;
          const terminalH = TILE_SIZE - 4;
          const active = engineState.queenTerminal.active;
          const queued = engineState.queenTerminal.queued;

          ctx.save();
          ctx.fillStyle = 'rgba(8, 47, 73, 0.95)';
          ctx.strokeStyle = engineState.queenTerminal.connected ? '#22d3ee' : '#64748b';
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          if (ctx.roundRect) ctx.roundRect(terminalX, terminalY, terminalW, terminalH, 3);
          else ctx.rect(terminalX, terminalY, terminalW, terminalH);
          ctx.fill();
          ctx.stroke();
          ctx.fillStyle = engineState.queenTerminal.connected ? '#67e8f9' : '#94a3b8';
          ctx.fillRect(terminalX + 4, terminalY + 4, terminalW - 8, 3);
          ctx.font = 'bold 7px "JetBrains Mono", monospace';
          ctx.textAlign = 'center';
          ctx.fillText(`${active.length}/3`, terminalX + terminalW / 2, terminalY + terminalH - 4);
          ctx.restore();

          ctx.save();
          ctx.font = 'bold 8px "JetBrains Mono", monospace';
          ctx.textAlign = 'left';
          ctx.fillStyle = 'rgba(8, 15, 30, 0.9)';
          ctx.fillRect(terminalX + TILE_SIZE + 3, terminalY - 2, 58, 13 + Math.min(3, active.length + queued.length) * 7);
          ctx.fillStyle = '#67e8f9';
          ctx.fillText('TERMINAL ROYAL', terminalX + TILE_SIZE + 7, terminalY + 7);
          active.slice(0, 3).forEach((item, index) => {
            ctx.fillStyle = '#4ade80';
            ctx.fillText(`ON ${index + 1}`, terminalX + TILE_SIZE + 7, terminalY + 16 + index * 7);
          });
          queued.slice(0, 3).forEach((item, index) => {
            ctx.fillStyle = '#94a3b8';
            ctx.fillText(`OFF ${index + 4}`, terminalX + TILE_SIZE + 7, terminalY + 16 + (active.length + index) * 7);
          });
          ctx.restore();
        }
      }

      // 4. Draw Dig Tasks (Dotted pickaxe icons / crosshairs)
      for (const task of digTasks) {
        const tx = task.x * TILE_SIZE;
        const ty = task.y * TILE_SIZE;
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([2, 2]);
        ctx.strokeRect(tx + 1, ty + 1, TILE_SIZE - 2, TILE_SIZE - 2);
        ctx.setLineDash([]);

        // Animated miner icon
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(tx + TILE_SIZE / 2 - 1, ty + 3, 2, TILE_SIZE - 6);
        ctx.fillRect(tx + 3, ty + TILE_SIZE / 2 - 1, TILE_SIZE - 6, 2);
      }

      // Draw Accessible Dig Frontlines when DESIGNATE_DIG tool is active
      if (activeTool === 'DESIGNATE_DIG') {
        const fronts = colonyEngine.getAccessibleDigFronts();
        ctx.strokeStyle = 'rgba(251, 191, 36, 0.45)';
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 2]);
        for (const f of fronts) {
          if (f.x >= visibleMinX && f.x <= visibleMaxX && f.y >= visibleMinY && f.y <= visibleMaxY) {
            ctx.strokeRect(f.x * TILE_SIZE + 0.5, f.y * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
          }
        }
        ctx.setLineDash([]);
      }

      // 5. Draw Brood in Nursery (Eggs, Larvae, Cocoons)
      for (const b of brood) {
        const bx = b.x * TILE_SIZE + TILE_SIZE / 2;
        const by = b.y * TILE_SIZE + TILE_SIZE / 2;

        if (b.type === 'egg') {
          ctx.fillStyle = '#fef08a';
          ctx.beginPath();
          ctx.ellipse(bx, by, 3, 4.5, 0.3, 0, Math.PI * 2);
          ctx.fill();
        } else if (b.type === 'larva') {
          ctx.fillStyle = '#f1f5f9';
          ctx.beginPath();
          ctx.ellipse(bx, by, 4, 6, 0.4, 0, Math.PI * 2);
          ctx.fill();
          // Segments
          ctx.strokeStyle = '#cbd5e1';
          ctx.lineWidth = 1;
          ctx.stroke();
        } else {
          // Cocoon
          ctx.fillStyle = '#fed7aa';
          ctx.beginPath();
          ctx.ellipse(bx, by, 4, 7, 0, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 6. Draw Ground Items (Resources waiting for haulers)
      for (const item of grid.groundItems) {
        const ix = item.x * TILE_SIZE + TILE_SIZE / 2;
        const iy = item.y * TILE_SIZE + TILE_SIZE / 2;

        ctx.fillStyle = item.color;
        if (item.type === 'crystal') {
          ctx.shadowColor = item.color;
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.moveTo(ix, iy - 4);
          ctx.lineTo(ix + 3.5, iy);
          ctx.lineTo(ix, iy + 4);
          ctx.lineTo(ix - 3.5, iy);
          ctx.closePath();
          ctx.fill();
          ctx.shadowBlur = 0;
        } else if (item.type === 'crystal_dust') {
          // Poussière de cristal étincelante sur le sol de la cavité
          ctx.shadowColor = '#38bdf8';
          ctx.shadowBlur = 6;
          ctx.fillStyle = '#7dd3fc';
          ctx.beginPath();
          ctx.arc(ix - 2.5, iy + 1.2, 1.4, 0, Math.PI * 2);
          ctx.arc(ix + 2.2, iy - 1.2, 1.3, 0, Math.PI * 2);
          ctx.arc(ix - 0.5, iy - 2, 1.1, 0, Math.PI * 2);
          ctx.arc(ix + 1, iy + 2, 1.2, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(ix - 0.5, iy - 0.5, 1.5, 1.5);
          ctx.shadowBlur = 0;
        } else {
          ctx.beginPath();
          ctx.arc(ix, iy, 3.5, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 6b. Dynamic Subterranean Bioluminescence & Ambient Cavern Lighting Pass
      const viewPxMinX = (visibleMinX - 1) * TILE_SIZE;
      const viewPxMaxX = (visibleMaxX + 2) * TILE_SIZE;
      const viewPxMinY = (visibleMinY - 1) * TILE_SIZE;
      const viewPxMaxY = (visibleMaxY + 2) * TILE_SIZE;

      ctx.save();
      ctx.globalCompositeOperation = 'lighter';

      // A. Queen's Royal Chamber Heart & Biological Aura
      const queen = ants.find((a) => a.caste === 'QUEEN');
      const qx = queen ? queen.x * TILE_SIZE + TILE_SIZE / 2 : 41 * TILE_SIZE;
      const qy = queen ? queen.y * TILE_SIZE + TILE_SIZE / 2 : 20 * TILE_SIZE;
      const qPulse = Math.sin(Date.now() * 0.0035) * 0.15 + 0.85;
      const qGlowRad = 85 * qPulse;

      if (
        qx + qGlowRad >= viewPxMinX &&
        qx - qGlowRad <= viewPxMaxX &&
        qy + qGlowRad >= viewPxMinY &&
        qy - qGlowRad <= viewPxMaxY
      ) {
        const qLightGrad = ctx.createRadialGradient(qx, qy, 4, qx, qy, qGlowRad);
        qLightGrad.addColorStop(0, 'rgba(251, 191, 36, 0.32)');
        qLightGrad.addColorStop(0.45, 'rgba(217, 119, 6, 0.14)');
        qLightGrad.addColorStop(1, 'rgba(180, 83, 9, 0)');
        ctx.fillStyle = qLightGrad;
        ctx.beginPath();
        ctx.arc(qx, qy, qGlowRad, 0, Math.PI * 2);
        ctx.fill();
      }

      // B. Ambient Luminescence from Revealed Crystal Veins
      for (let y = visibleMinY; y <= visibleMaxY; y++) {
        for (let x = visibleMinX; x <= visibleMaxX; x++) {
          if (grid.tiles[y]?.[x] === 'VEIN_CRYSTAL' && grid.revealed[y]?.[x]) {
            const cpx = x * TILE_SIZE + TILE_SIZE / 2;
            const cpy = y * TILE_SIZE + TILE_SIZE / 2;
            const isDeep = y >= 85;
            const cPulse = Math.sin(Date.now() * 0.003 + x * 0.8 + y * 0.5) * 0.18 + 0.82;
            const cRad = 36 * cPulse;

            const cLight = ctx.createRadialGradient(cpx, cpy, 2, cpx, cpy, cRad);
            cLight.addColorStop(0, isDeep ? 'rgba(192, 132, 252, 0.38)' : 'rgba(56, 189, 248, 0.40)');
            cLight.addColorStop(0.55, isDeep ? 'rgba(147, 51, 234, 0.14)' : 'rgba(6, 182, 212, 0.15)');
            cLight.addColorStop(1, 'rgba(0, 0, 0, 0)');
            ctx.fillStyle = cLight;
            ctx.beginPath();
            ctx.arc(cpx, cpy, cRad, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }

      // C. Mobile Bioluminescent Lantern Glow from Ants Carrying Crystals or Crystal Dust
      for (const ant of ants) {
        if (ant.carrying && (ant.carrying.type === 'crystal' || ant.carrying.type === 'crystal_dust')) {
          const apx = ant.x * TILE_SIZE + TILE_SIZE / 2;
          const apy = ant.y * TILE_SIZE + TILE_SIZE / 2;
          if (apx >= viewPxMinX && apx <= viewPxMaxX && apy >= viewPxMinY && apy <= viewPxMaxY) {
            const cLight = ctx.createRadialGradient(apx, apy, 2, apx, apy, 30);
            cLight.addColorStop(0, 'rgba(125, 211, 252, 0.32)');
            cLight.addColorStop(0.6, 'rgba(56, 189, 248, 0.10)');
            cLight.addColorStop(1, 'rgba(0, 0, 0, 0)');
            ctx.fillStyle = cLight;
            ctx.beginPath();
            ctx.arc(apx, apy, 30, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }

      // D. Sacred Glow in Crystal Vaults and Incubation Warmth in Nurseries
      for (const room of grid.rooms) {
        if (room.type === 'CRYSTAL_VAULT') {
          const cx = room.center.x * TILE_SIZE + TILE_SIZE / 2;
          const cy = room.center.y * TILE_SIZE + TILE_SIZE / 2;
          const vLight = ctx.createRadialGradient(cx, cy, 6, cx, cy, 65);
          vLight.addColorStop(0, 'rgba(6, 182, 212, 0.28)');
          vLight.addColorStop(0.6, 'rgba(8, 145, 178, 0.10)');
          vLight.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = vLight;
          ctx.beginPath();
          ctx.arc(cx, cy, 65, 0, Math.PI * 2);
          ctx.fill();
        } else if (room.type === 'NURSERY') {
          const cx = room.center.x * TILE_SIZE + TILE_SIZE / 2;
          const cy = room.center.y * TILE_SIZE + TILE_SIZE / 2;
          const nLight = ctx.createRadialGradient(cx, cy, 6, cx, cy, 55);
          nLight.addColorStop(0, 'rgba(244, 114, 182, 0.20)');
          nLight.addColorStop(0.6, 'rgba(219, 39, 119, 0.08)');
          nLight.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = nLight;
          ctx.beginPath();
          ctx.arc(cx, cy, 55, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      ctx.restore();

      // 7. Draw Ants & Generate Ambient Soil Micro-Particles
      for (const ant of ants) {
        const isSelected = ant.id === engineState.selectedAntId;
        ctx.save();
        if (depthViewMode === 'single') {
          const depthDiff = Math.abs(ant.y - selectedZLayer);
          const antAlpha = Math.max(0.12, 1.0 - Math.min(0.88, depthDiff * 0.22));
          ctx.globalAlpha = antAlpha;
        } else {
          const depthRatio = Math.max(0, Math.min(1, (ant.y - 7) / 84));
          const antAlpha = Math.max(0.45, 1.0 - depthRatio * 0.35 * volumeOpacity);
          ctx.globalAlpha = antAlpha;
        }
        drawAnt(ctx, ant, isSelected);
        ctx.restore();

        // A. Subtle soil chipping, crumb cascades & sparkling fragments when ants are actively digging
        if (ant.state === 'DIGGING' && ant.targetTile) {
          if (Math.random() < 0.65 && dynamicParticlesRef.current.length < 360) {
            const targetPx = (ant.targetTile.x + 0.5) * TILE_SIZE;
            const targetPy = (ant.targetTile.y + 0.5) * TILE_SIZE;
            const antPx = (ant.x + 0.5) * TILE_SIZE;
            const antPy = (ant.y + 0.5) * TILE_SIZE;

            const contactX = antPx + (targetPx - antPx) * 0.55 + (Math.random() - 0.5) * 4;
            const contactY = antPy + (targetPy - antPy) * 0.55 + (Math.random() - 0.5) * 4;

            const tile = grid.tiles[ant.targetTile.y]?.[ant.targetTile.x];
            const isCrystal = tile === 'VEIN_CRYSTAL' || ant.targetTile.y >= 85;
            const colors = getSoilColorsForDepth(ant.targetTile.y, isCrystal);

            const angle = Math.atan2(antPy - targetPy, antPx - targetPx) + (Math.random() - 0.5) * 1.3;
            const speed = 0.6 + Math.random() * 1.6;

            dynamicParticlesRef.current.push({
              x: contactX,
              y: contactY,
              vx: Math.cos(angle) * speed,
              vy: Math.sin(angle) * speed - 0.45,
              size: 0.8 + Math.random() * 1.8,
              color: colors[Math.floor(Math.random() * colors.length)],
              alpha: 0.75 + Math.random() * 0.25,
              decay: 0.02 + Math.random() * 0.025,
              gravity: 0.06,
              drag: 0.96,
              sparkle: isCrystal && Math.random() < 0.5,
              kind: 'crumb',
            });
          }

          // Occasional ceiling soil trickle when mining beneath rock ceiling
          if (
            Math.random() < 0.12 &&
            ant.targetTile.y > 7 &&
            grid.tiles[ant.targetTile.y - 1]?.[ant.targetTile.x] !== 'AIR' &&
            dynamicParticlesRef.current.length < 360
          ) {
            const colors = getSoilColorsForDepth(ant.targetTile.y);
            dynamicParticlesRef.current.push({
              x: ant.targetTile.x * TILE_SIZE + Math.random() * TILE_SIZE,
              y: (ant.targetTile.y - 0.1) * TILE_SIZE,
              vx: (Math.random() - 0.5) * 0.2,
              vy: 0.25 + Math.random() * 0.4,
              size: 0.7 + Math.random() * 1.0,
              color: colors[0],
              alpha: 0.45 + Math.random() * 0.25,
              decay: 0.016,
              gravity: 0.07,
              drag: 0.98,
              kind: 'ceiling_trickle',
            });
          }
        } else if (
          (ant.state === 'CARRYING' || ant.state === 'MOVING_TO_DIG' || ant.state === 'WANDERING') &&
          (Math.abs(ant.vx) > 0.005 || Math.abs(ant.vy) > 0.005)
        ) {
          // B. Subtle footstep soil dust puff kicked up when ants scurry along corridors
          if (Math.random() < 0.16 && dynamicParticlesRef.current.length < 360) {
            const antPx = (ant.x + 0.5) * TILE_SIZE;
            const antPy = (ant.y + 0.5) * TILE_SIZE + 2.5;
            const depthRow = Math.max(7, Math.floor(ant.y));
            const isCrystal =
              depthRow >= 85 ||
              Boolean(ant.carrying && (ant.carrying.type === 'crystal' || ant.carrying.type === 'crystal_dust'));
            const colors = getSoilColorsForDepth(depthRow, isCrystal);

            dynamicParticlesRef.current.push({
              x: antPx + (Math.random() - 0.5) * 3,
              y: antPy + (Math.random() - 0.5) * 2,
              vx: -ant.vx * 0.25 + (Math.random() - 0.5) * 0.35,
              vy: -ant.vy * 0.25 - 0.15,
              size: 0.9 + Math.random() * 1.4,
              color: colors[0],
              alpha: 0.28 + Math.random() * 0.15,
              decay: 0.015 + Math.random() * 0.015,
              gravity: -0.006,
              drag: 0.94,
              sparkle: isCrystal && Math.random() < 0.3,
              kind: 'footstep_puff',
            });
          }

          // C. Luminous trail wisps when carrying crystals or crystal dust
          if (
            ant.carrying &&
            (ant.carrying.type === 'crystal' || ant.carrying.type === 'crystal_dust') &&
            Math.random() < 0.24 &&
            dynamicParticlesRef.current.length < 360
          ) {
            const antPx = (ant.x + 0.5) * TILE_SIZE;
            const antPy = (ant.y + 0.5) * TILE_SIZE;
            dynamicParticlesRef.current.push({
              x: antPx - ant.vx * 3 + (Math.random() - 0.5) * 3,
              y: antPy - ant.vy * 3 + (Math.random() - 0.5) * 3,
              vx: -ant.vx * 0.15 + (Math.random() - 0.5) * 0.2,
              vy: -0.22 - Math.random() * 0.2,
              size: 1.0 + Math.random() * 1.6,
              color: ant.carrying.type === 'crystal' ? '#38bdf8' : '#7dd3fc',
              alpha: 0.7 + Math.random() * 0.2,
              decay: 0.018 + Math.random() * 0.015,
              gravity: -0.006,
              sparkle: true,
              kind: 'crystal_sparkle',
            });
          }
        }

        // D. Warm ascending bio-spores in Nurse / Queen chambers
        if (
          (ant.caste === 'QUEEN' || ant.caste === 'NURSE') &&
          Math.random() < 0.06 &&
          dynamicParticlesRef.current.length < 360
        ) {
          const antPx = (ant.x + 0.5) * TILE_SIZE;
          const antPy = (ant.y + 0.5) * TILE_SIZE;
          dynamicParticlesRef.current.push({
            x: antPx + (Math.random() - 0.5) * 8,
            y: antPy + (Math.random() - 0.5) * 6,
            vx: (Math.random() - 0.5) * 0.2,
            vy: -0.2 - Math.random() * 0.25,
            size: 1.2 + Math.random() * 1.4,
            color: ant.caste === 'QUEEN' ? 'rgba(245, 158, 11, 0.45)' : 'rgba(192, 132, 252, 0.4)',
            alpha: 0.4 + Math.random() * 0.2,
            decay: 0.012,
            gravity: -0.005,
            drag: 0.96,
            wobblePhase: Math.random() * Math.PI * 2,
            wobbleSpeed: 0.05,
            kind: 'warmth_spore',
          });
        }
      }

      // 8. Update & Draw Dynamic Soil Particles (Chipping, dust puffs, crumbling crumbs, crystal sparkles)
      for (let i = dynamicParticlesRef.current.length - 1; i >= 0; i--) {
        const p = dynamicParticlesRef.current[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += p.gravity;
        if (p.drag) p.vx *= p.drag;
        else p.vx *= 0.96;

        if (p.wobbleSpeed) {
          p.wobblePhase = (p.wobblePhase || 0) + p.wobbleSpeed;
          p.vx += Math.sin(p.wobblePhase) * 0.025;
        }

        if (p.kind === 'dust_puff') {
          p.size += 0.035; // gentle cloud expansion
        }

        p.alpha -= p.decay;

        if (p.alpha <= 0) {
          dynamicParticlesRef.current.splice(i, 1);
          continue;
        }

        // Viewport culling for high-performance 60fps rendering
        if (p.x < viewPxMinX || p.x > viewPxMaxX || p.y < viewPxMinY || p.y > viewPxMaxY) {
          continue;
        }

        ctx.save();
        ctx.globalAlpha = Math.max(0, Math.min(1, p.alpha));
        ctx.fillStyle = p.color;

        if (p.sparkle) {
          ctx.shadowColor = p.color;
          ctx.shadowBlur = 5;
          const half = p.size / 2;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y - half * 1.4);
          ctx.lineTo(p.x + half * 1.4, p.y);
          ctx.lineTo(p.x, p.y + half * 1.4);
          ctx.lineTo(p.x - half * 1.4, p.y);
          ctx.closePath();
          ctx.fill();
        } else if (p.kind === 'dust_puff') {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      // 8b. Draw Atmospheric Floating Dust Motes (Stratum-illuminated subterranean haze inside cavities)
      for (const mote of dustMotesRef.current) {
        mote.x += mote.vx;
        mote.y += mote.vy;
        if (mote.x < 0) mote.x = GRID_WIDTH * TILE_SIZE;
        if (mote.x > GRID_WIDTH * TILE_SIZE) mote.x = 0;
        if (mote.y < 8 * TILE_SIZE) mote.y = (GRID_HEIGHT - 5) * TILE_SIZE;
        if (mote.y > (GRID_HEIGHT - 5) * TILE_SIZE) mote.y = 8 * TILE_SIZE;

        // Viewport culling
        if (mote.x < viewPxMinX || mote.x > viewPxMaxX || mote.y < viewPxMinY || mote.y > viewPxMaxY) {
          continue;
        }

        const row = Math.floor(mote.y / TILE_SIZE);
        const col = Math.floor(mote.x / TILE_SIZE);
        const inAir = grid.tiles[row]?.[col] === 'AIR';
        const alphaMultiplier = inAir ? 1.3 : 0.4;

        if (row >= 85) {
          // Deep bioluminescent crystal dust (cyan & amethyst facets with subtle glow)
          const isAmethyst = row >= 96;
          const dustColor = isAmethyst ? '192, 132, 252' : '125, 211, 252';
          ctx.save();
          ctx.fillStyle = `rgba(${dustColor}, ${mote.alpha * 1.35 * alphaMultiplier})`;
          ctx.shadowColor = `rgba(${dustColor}, 0.75)`;
          ctx.shadowBlur = 4.5;
          // Diamond facet shape for crystalline motes
          const half = mote.size * 0.95;
          ctx.beginPath();
          ctx.moveTo(mote.x, mote.y - half * 1.5);
          ctx.lineTo(mote.x + half * 1.5, mote.y);
          ctx.lineTo(mote.x, mote.y + half * 1.5);
          ctx.lineTo(mote.x - half * 1.5, mote.y);
          ctx.closePath();
          ctx.fill();
          ctx.restore();
        } else if (row >= 56) {
          // Mid-depth gold pyrite and quartz mica mineral dust
          ctx.save();
          const isGold = (row + col) % 3 === 0;
          const dustColor = isGold ? '245, 158, 11' : '203, 213, 225';
          ctx.fillStyle = `rgba(${dustColor}, ${mote.alpha * 1.15 * alphaMultiplier})`;
          ctx.shadowColor = `rgba(${dustColor}, 0.55)`;
          ctx.shadowBlur = 3;
          ctx.beginPath();
          ctx.arc(mote.x, mote.y, mote.size, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        } else if (row >= 29) {
          ctx.fillStyle = `rgba(194, 65, 12, ${mote.alpha * 0.9 * alphaMultiplier})`;
          ctx.beginPath();
          ctx.arc(mote.x, mote.y, mote.size, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.fillStyle = `rgba(180, 130, 80, ${mote.alpha * alphaMultiplier})`;
          ctx.beginPath();
          ctx.arc(mote.x, mote.y, mote.size, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 9. Tool Cursor Hover Indicator
      if (hoverTile && hoverTile.y >= 7 && hoverTile.y < GRID_HEIGHT) {
        const hx = hoverTile.x * TILE_SIZE;
        const hy = hoverTile.y * TILE_SIZE;

        if (activeTool === 'DIG_MANUAL') {
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 2;
          const r = brushRadius * TILE_SIZE;
          ctx.strokeRect(hx - r + TILE_SIZE / 2, hy - r + TILE_SIZE / 2, r * 2, r * 2);
        } else if (activeTool === 'DESIGNATE_DIG') {
          ctx.strokeStyle = '#f59e0b';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(hx, hy, TILE_SIZE, TILE_SIZE);
        } else if (activeTool === 'DESIGNATE_ROOM') {
          const preset = ROOM_PRESETS[selectedRoomType];
          ctx.strokeStyle = preset.color;
          ctx.lineWidth = 2;
          ctx.strokeRect(hx, hy, TILE_SIZE, TILE_SIZE);
        }
      }

      // 10. Selected Cell Focus Frame
      if (selectedCellCoords) {
        const sx = selectedCellCoords.x * TILE_SIZE;
        const sy = selectedCellCoords.y * TILE_SIZE;
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2;
        ctx.strokeRect(sx, sy, TILE_SIZE, TILE_SIZE);
        ctx.fillStyle = 'rgba(56, 189, 248, 0.15)';
        ctx.fillRect(sx, sy, TILE_SIZE, TILE_SIZE);
      }

      // 11. Volumetric depth-based opacity atmospheric overlay or Single Layer Slice Guideline
      if (depthViewMode === 'volume') {
        const topY = 7 * TILE_SIZE;
        const botY = GRID_HEIGHT * TILE_SIZE;
        const grad = ctx.createLinearGradient(0, topY, 0, botY);
        // Depth gradient: warm golden earth hue -> cold tectonic slate -> deep abyssal darkness
        grad.addColorStop(0, `rgba(251, 191, 36, ${0.03 * volumeOpacity})`);
        grad.addColorStop(0.18, `rgba(180, 83, 9, ${0.04 * volumeOpacity})`);
        grad.addColorStop(0.45, `rgba(15, 23, 42, ${0.12 * volumeOpacity})`);
        grad.addColorStop(0.75, `rgba(10, 15, 30, ${0.24 * volumeOpacity})`);
        grad.addColorStop(1.0, `rgba(3, 7, 18, ${0.42 * volumeOpacity})`);
        ctx.fillStyle = grad;
        ctx.fillRect(
          visibleMinX * TILE_SIZE,
          Math.max(topY, visibleMinY * TILE_SIZE),
          (visibleMaxX - visibleMinX + 1) * TILE_SIZE,
          Math.min(botY, (visibleMaxY + 1) * TILE_SIZE) - Math.max(topY, visibleMinY * TILE_SIZE)
        );
      } else if (depthViewMode === 'single' && selectedZLayer >= visibleMinY && selectedZLayer <= visibleMaxY) {
        // Glowing horizontal depth layer guideline
        const lineY = selectedZLayer * TILE_SIZE;
        ctx.save();
        ctx.strokeStyle = 'rgba(251, 191, 36, 0.75)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(visibleMinX * TILE_SIZE, lineY);
        ctx.lineTo((visibleMaxX + 1) * TILE_SIZE, lineY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label on left edge
        ctx.fillStyle = '#f59e0b';
        ctx.font = 'bold 10px "Plus Jakarta Sans", sans-serif';
        ctx.fillText(
          `Couche z = ${selectedZLayer} (-${Math.max(0, Math.round((selectedZLayer - 7) * 0.52))}m)`,
          visibleMinX * TILE_SIZE + 6,
          lineY - 4
        );
        ctx.restore();
      }

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animationFrameId);
  }, [engineState, camera, activeTool, selectedRoomType, brushRadius, hoverTile, depthViewMode, selectedZLayer, volumeOpacity, useProceduralShaders, isShaderSupported]);

  const setScanLayer = (delta: number) => {
    const nextLayer = Math.max(0, Math.min(83, selectedZLayer + delta));
    setSelectedZLayer(nextLayer);
  };

  return (
    <div className="relative w-full h-full select-none overflow-hidden bg-slate-950">
      {/* Background WebGL Procedural Soil Shaders Layer */}
      <canvas
        ref={shaderCanvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />
      {/* Foreground Interactive 2D Simulation Layer */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full block cursor-crosshair"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      />

      {/* Depth ruler / Stratum indicator bar on left */}
      <div className="absolute top-4 left-4 flex flex-col gap-1.5 pointer-events-none">
        <div className="bg-slate-900/90 border border-slate-700/60 rounded-md px-2.5 py-1.5 shadow-md">
          <div className="text-[11px] font-semibold text-slate-200">
            Étage actuel :{' '}
            <span className="text-amber-400">
              {Math.max(0, Math.round(((camera.y / TILE_SIZE) - 7) * 0.52))} m de profondeur
            </span>
          </div>
          <div className="text-[10px] text-slate-400">
            {STRATA.find(
              (s) =>
                camera.y / TILE_SIZE >= s.startRow &&
                camera.y / TILE_SIZE <= s.endRow
            )?.name || 'Sous-sol'}
          </div>
          <div className="text-[9px] font-mono text-cyan-400/90 mt-0.5">
            {depthViewMode === 'single'
              ? `Mode Couche Unique (z=${selectedZLayer})`
              : `Mode Scan volumétrique (Opacité ${Math.round(volumeOpacity * 100)}%)`}
          </div>
          <div className="text-[9px] font-mono text-emerald-400/90 mt-0.5 flex items-center gap-1">
            <span>
              {useProceduralShaders && isShaderSupported
                ? 'Shaders Procéduraux GLSL (Argile · Roche · Minéral · Cristal)'
                : 'Rendu 2D Classique'}
            </span>
          </div>
        </div>
      </div>

      {/* 2.5D Depth Visualization Toggle & Controls Overlay */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-2 bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-xl p-2.5 shadow-xl w-72 sm:w-80 text-xs">
        {/* Toggle Header */}
        <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-2">
          <div className="flex items-center gap-1.5 text-slate-200 font-semibold text-[11px]">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Coupe 3D du volume</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {depthViewMode === 'single' ? `z = ${selectedZLayer}` : `Scan Z=${selectedZLayer}`}
            </span>
            <button
              onClick={() => setIsDepthPanelCollapsed(!isDepthPanelCollapsed)}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title={isDepthPanelCollapsed ? 'Développer le panneau' : 'Réduire le panneau'}
            >
              {isDepthPanelCollapsed ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronUp className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>

        {/* Procedural Shader Toggle */}
        <button
          onClick={() => setUseProceduralShaders(!useProceduralShaders)}
          className={`w-full px-2.5 py-1.5 rounded-lg border text-[11px] font-semibold flex items-center justify-between transition-colors ${
            useProceduralShaders && isShaderSupported
              ? 'bg-emerald-950/70 border-emerald-700/60 text-emerald-300'
              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
          title="Activer ou désactiver les fragment shaders procéduraux WebGL pour l'argile, la roche et les minéraux"
        >
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>Textures Procédurales (Shaders)</span>
          </div>
          <span
            className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
              useProceduralShaders && isShaderSupported
                ? 'bg-emerald-900/80 text-emerald-200'
                : 'bg-slate-800 text-slate-400'
            }`}
          >
            {useProceduralShaders && isShaderSupported ? 'ACTIF (GLSL)' : 'OFF'}
          </span>
        </button>

        {/* Visual Mode Switcher Tabs */}
        <div className="grid grid-cols-2 gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setDepthViewMode('single')}
            className={`px-2 py-1.5 rounded-md text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-all ${
              depthViewMode === 'single'
                ? 'bg-amber-400 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
            title="Isoler et visualiser une couche de profondeur unique (z=0 à 84)"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Couche (z=0..84)</span>
          </button>
          <button
            onClick={() => setDepthViewMode('volume')}
            className={`px-2 py-1.5 rounded-md text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-all ${
              depthViewMode === 'volume'
                ? 'bg-cyan-500 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
            title="Scanner les tranches voisines autour de la couche centrale"
          >
            <Box className="w-3.5 h-3.5" />
            <span>Scan volumétrique</span>
          </button>
          </div>

          {depthViewMode === 'volume' && !isDepthPanelCollapsed && (
            <div className="rounded-lg border border-cyan-900/60 bg-cyan-950/20 px-2.5 py-2 text-[10px] text-cyan-200">
              <div className="flex items-center justify-between font-mono">
                <span>Position caméra</span>
                <span className="font-bold">Z={selectedZLayer}</span>
              </div>
              <div className="mt-1 flex items-center justify-between text-slate-400">
                <span>Profondeur du bac</span>
                <span className="font-mono text-cyan-300">±{scanRadius} couches</span>
              </div>
              <div className="mt-1 text-[9px] text-slate-500">Le zoom arrière révèle davantage de tranches.</div>
            </div>
          )}

          {/* Expanded Controls based on Mode */}
        {!isDepthPanelCollapsed && (
          <div className="pt-1">
            {depthViewMode === 'single' ? (
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Couche observée :</span>
                  <span className="font-mono font-bold text-amber-300">
                    z = {selectedZLayer}{' '}
                    <span className="text-slate-500 text-[10px] font-normal">
                      (-{Math.max(0, Math.round((selectedZLayer - 7) * 0.52))}m)
                    </span>
                  </span>
                </div>

                {/* Slider with step buttons */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      const nextZ = Math.max(0, selectedZLayer - 1);
                      setSelectedZLayer(nextZ);
                      setCamera((prev) => ({ ...prev, y: Math.max(7, nextZ) * TILE_SIZE }));
                    }}
                    className="w-6 h-6 flex items-center justify-center rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition-colors"
                    title="Couche précédente"
                  >
                    -
                  </button>
                  <input
                    type="range"
                    min={0}
                    max={83}
                    value={selectedZLayer}
                    onChange={(e) => {
                      const nextZ = Number(e.target.value);
                      setSelectedZLayer(nextZ);
                      setCamera((prev) => ({ ...prev, y: Math.max(7, nextZ) * TILE_SIZE }));
                    }}
                    className="flex-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
                    title={`Sélectionner la couche z (${selectedZLayer}/83)`}
                  />
                  <button
                    onClick={() => {
                      const nextZ = Math.min(83, selectedZLayer + 1);
                      setSelectedZLayer(nextZ);
                      setCamera((prev) => ({ ...prev, y: Math.max(7, nextZ) * TILE_SIZE }));
                    }}
                    className="w-6 h-6 flex items-center justify-center rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition-colors"
                    title="Couche suivante"
                  >
                    +
                  </button>
                </div>

                {/* Quick Stratum Presets */}
                <div className="flex items-center justify-between gap-1 pt-1 text-[9px] font-mono">
                  {[
                    { label: 'Surface', z: 0 },
                    { label: 'Reine', z: 20 },
                    { label: 'Argile', z: 40 },
                    { label: 'Cristaux', z: 70 },
                    { label: 'Fond', z: 83 },
                  ].map((preset) => (
                    <button
                      key={preset.z}
                      onClick={() => {
                        setSelectedZLayer(preset.z);
                        setCamera((prev) => ({ ...prev, y: Math.max(7, preset.z) * TILE_SIZE }));
                      }}
                      className={`px-1.5 py-0.5 rounded transition-colors ${
                        selectedZLayer === preset.z
                          ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40'
                          : 'bg-slate-950/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Eye className="w-3 h-3 text-cyan-400" />
                    Opacité de profondeur :
                  </span>
                  <span className="font-mono font-bold text-cyan-300">
                    {Math.round(volumeOpacity * 100)}%
                  </span>
                </div>

                <input
                  type="range"
                  min={0.2}
                  max={1.0}
                  step={0.05}
                  value={volumeOpacity}
                  onChange={(e) => setVolumeOpacity(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                  title={`Opacité volumétrique : ${Math.round(volumeOpacity * 100)}%`}
                />

                <div className="text-[10px] text-slate-400 leading-tight">
                  Superposition volumétrique intégrale (z=0 à 83) avec assombrissement et atténuation optique selon la profondeur.
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation Quick-Jump shortcuts */}
      <div className="absolute bottom-4 left-4 flex items-center gap-1.5 bg-slate-900/85 backdrop-blur-sm border border-slate-800 rounded-lg p-1 shadow-lg">
        <button
          onClick={() => setCamera((prev) => ({ ...prev, y: 7 * TILE_SIZE }))}
          className="px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded transition-colors whitespace-nowrap"
        >
          Surface (0m)
        </button>
        <span className="text-slate-600">·</span>
        <button
          onClick={() => setCamera((prev) => ({ ...prev, y: 20 * TILE_SIZE }))}
          className="px-2.5 py-1 text-xs font-medium text-amber-300 hover:text-white hover:bg-slate-800 rounded transition-colors whitespace-nowrap"
        >
          Reine (-7m)
        </button>
        <span className="text-slate-600">·</span>
        <button
          onClick={() => setCamera((prev) => ({ ...prev, y: 40 * TILE_SIZE }))}
          className="px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded transition-colors whitespace-nowrap"
        >
          Argile (-17m)
        </button>
        <span className="text-slate-600">·</span>
        <button
          onClick={() => setCamera((prev) => ({ ...prev, y: 70 * TILE_SIZE }))}
          className="px-2.5 py-1 text-xs font-medium text-cyan-300 hover:text-white hover:bg-slate-800 rounded transition-colors whitespace-nowrap"
        >
          Cristaux (-33m)
        </button>
        <span className="text-slate-600">·</span>
        <button
          onClick={() => setCamera((prev) => ({ ...prev, y: 112 * TILE_SIZE }))}
          className="px-2.5 py-1 text-xs font-medium text-purple-300 hover:text-white hover:bg-slate-800 rounded transition-colors whitespace-nowrap"
        >
          Abîme (-55m)
        </button>
      </div>

      {/* Camera depth controls: move through the 84 sections of the volume */}
      <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1.5 bg-slate-900/95 backdrop-blur-sm border border-cyan-900/70 rounded-lg px-2 py-1 shadow-lg">
        <button
          onClick={() => setScanLayer(-1)}
          disabled={selectedZLayer === 0}
          className="px-2 h-7 rounded text-cyan-200 hover:bg-cyan-950 disabled:opacity-30 disabled:cursor-not-allowed font-mono text-[9px] font-bold"
          title="Reculer la caméra d'une section"
        >
          ← RECULER
        </button>
        <div className="min-w-32 text-center font-mono text-[10px] leading-tight">
          <div className="text-cyan-300 font-bold">CAMÉRA Z={selectedZLayer}/83</div>
          <div className="text-slate-500">coupe 3D · 84 sections</div>
        </div>
        <button
          onClick={() => setScanLayer(1)}
          disabled={selectedZLayer === 83}
          className="px-2 h-7 rounded text-cyan-200 hover:bg-cyan-950 disabled:opacity-30 disabled:cursor-not-allowed font-mono text-[9px] font-bold"
          title="Entrer la caméra d'une section"
        >
          ENTRER →
        </button>
      </div>

      {/* Zoom control buttons */}
      <div className="absolute bottom-4 right-4 flex items-center gap-1 bg-slate-900/85 backdrop-blur-sm border border-slate-800 rounded-lg p-1 shadow-lg">
        <button
          onClick={() => setCamera((prev) => ({ ...prev, zoom: Math.min(2.5, prev.zoom * 1.25) }))}
          className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 rounded transition-colors text-sm font-semibold"
          title="Zoom avant"
        >
          +
        </button>
        <button
          onClick={() => setCamera((prev) => ({ ...prev, zoom: Math.max(0.4, prev.zoom * 0.8) }))}
          className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-800 rounded transition-colors text-sm font-semibold"
          title="Zoom arrière"
        >
          -
        </button>
        <button
          onClick={() =>
            setCamera({
              x: (GRID_WIDTH * TILE_SIZE) / 2,
              y: 41 * TILE_SIZE,
              zoom: 1.1,
            })
          }
          className="px-2 h-7 flex items-center justify-center text-xs text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
          title="Recentrer la vue"
        >
          Recentrer
        </button>
      </div>
    </div>
  );
};

/**
 * Draws a multi-point crystalline diamond sparkle star.
 */
function drawDiamondFlare(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  size: number,
  angle: number,
  alpha: number,
  color: string = '#ffffff'
) {
  if (alpha <= 0.02) return;
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(angle);
  ctx.globalAlpha = Math.max(0, Math.min(1, alpha));
  ctx.fillStyle = color;

  // 4-point acute diamond flare
  ctx.beginPath();
  ctx.moveTo(0, -size);
  ctx.quadraticCurveTo(size * 0.12, -size * 0.12, size, 0);
  ctx.quadraticCurveTo(size * 0.12, size * 0.12, 0, size);
  ctx.quadraticCurveTo(-size * 0.12, size * 0.12, -size, 0);
  ctx.quadraticCurveTo(-size * 0.12, -size * 0.12, 0, -size);
  ctx.closePath();
  ctx.fill();

  // Core bright sparkle dot
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.arc(0, 0, size * 0.28, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

/**
 * Draws a high-fidelity anatomical ant with realistic biological alternating tripod gait,
 * jointed legs (coxa, femur, tibia, tarsus), specular chitin reflections, and caste morphology.
 */
function drawAnt(ctx: CanvasRenderingContext2D, ant: Ant, isSelected: boolean) {
  const px = ant.x * TILE_SIZE + TILE_SIZE / 2;
  const py = ant.y * TILE_SIZE + TILE_SIZE / 2;

  ctx.save();
  ctx.translate(px, py);
  ctx.rotate(ant.angle);

  const baseScale = ant.caste === 'QUEEN' ? 1.6 : ant.caste === 'GUARD' ? 1.25 : 0.96;
  const scale = baseScale * (ant.size || 1.0);
  ctx.scale(scale, scale);

  // Selection highlight aura with pulsing ring
  if (isSelected) {
    const pulseRing = Math.sin(Date.now() * 0.006) * 2 + 15;
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(0, 0, pulseRing, 0, Math.PI * 2);
    ctx.stroke();

    // Small rotating compass ticks
    const rot = Date.now() * 0.002;
    for (let i = 0; i < 4; i++) {
      const a = rot + (i * Math.PI) / 2;
      ctx.fillStyle = '#38bdf8';
      ctx.beginPath();
      ctx.arc(Math.cos(a) * pulseRing, Math.sin(a) * pulseRing, 1.4, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Caste chitin coloration
  let bodyColor = '#24140e'; // Deep glossy chitin
  let thoraxColor = '#381e15';
  let gasterColor = '#180d09';
  let gasterStripeColor = 'rgba(255, 255, 255, 0.18)';
  let highlightColor = 'rgba(255, 255, 255, 0.45)';

  if (ant.caste === 'QUEEN') {
    bodyColor = '#6b2d07';
    thoraxColor = '#9a3412';
    gasterColor = '#c2410c';
    gasterStripeColor = 'rgba(254, 240, 138, 0.6)';
    highlightColor = 'rgba(254, 240, 138, 0.75)';

    // Queen radiant royal biological aura
    const qPulse = Math.sin(Date.now() * 0.004) * 0.2 + 0.8;
    ctx.shadowColor = '#f59e0b';
    ctx.shadowBlur = 14 * qPulse;
  } else if (ant.caste === 'GUARD') {
    bodyColor = '#090d16';
    thoraxColor = '#1e293b';
    gasterColor = '#020617';
    gasterStripeColor = 'rgba(239, 68, 68, 0.35)';
    highlightColor = 'rgba(148, 163, 184, 0.45)';
  } else if (ant.caste === 'NURSE') {
    thoraxColor = '#581c87';
    bodyColor = '#2e1065';
    gasterColor = '#1e1b4b';
    gasterStripeColor = 'rgba(232, 121, 249, 0.4)';
    highlightColor = 'rgba(245, 208, 254, 0.5)';
  } else if (ant.caste === 'MINER') {
    bodyColor = '#3f2214';
    thoraxColor = '#572b16';
    gasterColor = '#27130b';
  } else if (ant.caste === 'BUILDER') {
    thoraxColor = '#065f46';
    gasterStripeColor = 'rgba(52, 211, 153, 0.35)';
  }

  // 1. Jointed Legs with Biological Alternating Tripod Gait (Coxa -> Femur -> Tibia -> Tarsus)
  // Group A: Left front (L1), Right middle (R2), Left hind (L3)
  // Group B: Right front (R1), Left middle (L2), Right hind (R3)
  const isMoving = Math.abs(ant.vx) > 0.001 || Math.abs(ant.vy) > 0.001 || ant.state === 'DIGGING';
  const phase = isMoving ? ant.legPhase : 0;
  const swingA = Math.sin(phase) * 2.8;
  const swingB = -swingA;

  ctx.strokeStyle = bodyColor;
  ctx.lineWidth = 1.1;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  const drawJointedLeg = (
    coxaX: number,
    coxaY: number,
    swing: number,
    side: 1 | -1,
    reachX: number,
    reachY: number
  ) => {
    const kneeX = coxaX + reachX * 0.45 + swing * 0.4;
    const kneeY = coxaY + (reachY * 0.55 + swing * 0.35) * side;
    const footX = coxaX + reachX + swing;
    const footY = coxaY + reachY * side;

    ctx.beginPath();
    ctx.moveTo(coxaX, coxaY * side);
    ctx.lineTo(kneeX, kneeY);
    ctx.lineTo(footX, footY);
    ctx.stroke();

    // Tiny tarsal claw highlight
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.beginPath();
    ctx.arc(footX, footY, 0.6, 0, Math.PI * 2);
    ctx.fill();
  };

  // Front legs (reaching forward and outward)
  drawJointedLeg(1.5, -1.8, swingA, 1, 4.2, -6.0);
  drawJointedLeg(1.5, 1.8, swingB, -1, 4.2, -6.0);

  // Middle legs (reaching outward and slightly backward)
  drawJointedLeg(-0.8, -1.8, swingB, 1, -1.2, -7.2);
  drawJointedLeg(-0.8, 1.8, swingA, -1, -1.2, -7.2);

  // Hind legs (reaching long and backward)
  drawJointedLeg(-3.2, -1.8, swingA, 1, -5.8, -6.4);
  drawJointedLeg(-3.2, 1.8, swingB, -1, -5.8, -6.4);

  // 2. Abdomen (Gaster) - Anatomical segmented teardrop with dorsal gloss
  const gasterLen = ant.caste === 'QUEEN' ? 7.6 : 4.8;
  const gasterWid = ant.caste === 'QUEEN' ? 4.8 : 3.2;

  ctx.save();
  ctx.fillStyle = gasterColor;
  ctx.beginPath();
  ctx.ellipse(-6.5, 0, gasterLen, gasterWid, 0, 0, Math.PI * 2);
  ctx.fill();

  // Visible chitin abdominal segments (tergites)
  ctx.strokeStyle = gasterStripeColor;
  ctx.lineWidth = 0.9;
  const stripeOffsets = ant.caste === 'QUEEN' ? [-9.2, -7.2, -5.2, -3.2] : [-8.2, -6.5, -4.8];
  for (const sx of stripeOffsets) {
    const curHalfWid = Math.sqrt(Math.max(0, 1 - Math.pow((sx + 6.5) / gasterLen, 2))) * gasterWid;
    ctx.beginPath();
    ctx.moveTo(sx, -curHalfWid * 0.85);
    ctx.lineTo(sx, curHalfWid * 0.85);
    ctx.stroke();
  }

  // Curved dorsal specular highlight on gaster
  const gasterGloss = ctx.createLinearGradient(-6.5, -gasterWid, -6.5, gasterWid);
  gasterGloss.addColorStop(0, highlightColor);
  gasterGloss.addColorStop(0.35, 'rgba(255, 255, 255, 0.05)');
  gasterGloss.addColorStop(1, 'rgba(0, 0, 0, 0.45)');
  ctx.fillStyle = gasterGloss;
  ctx.beginPath();
  ctx.ellipse(-6.5, -gasterWid * 0.35, gasterLen * 0.75, gasterWid * 0.38, 0, 0, Math.PI * 2);
  ctx.fill();

  // Queen royal heart pulsation glow
  if (ant.caste === 'QUEEN') {
    const heartPulse = Math.sin(Date.now() * 0.007) * 0.5 + 0.5;
    ctx.fillStyle = `rgba(251, 191, 36, ${0.45 * heartPulse})`;
    ctx.beginPath();
    ctx.arc(-6.5, 0, 2.2, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();

  // 3. Petiole & Post-Petiole (The delicate biological ant waist nodes)
  ctx.fillStyle = bodyColor;
  ctx.beginPath();
  ctx.arc(-3.0, 0, 1.2, 0, Math.PI * 2);
  ctx.arc(-2.0, 0, 1.1, 0, Math.PI * 2);
  ctx.fill();

  // 4. Thorax (Mesosoma) - Anatomical sculpted segments (Pronotum + Propodeum)
  ctx.save();
  ctx.fillStyle = thoraxColor;
  ctx.beginPath();
  ctx.ellipse(-0.3, 0, 3.2, 2.1, 0, 0, Math.PI * 2);
  ctx.fill();

  // Pronotum curved specular highlight
  const thoraxGloss = ctx.createLinearGradient(-0.3, -2.1, -0.3, 2.1);
  thoraxGloss.addColorStop(0, highlightColor);
  thoraxGloss.addColorStop(0.5, 'rgba(255, 255, 255, 0)');
  thoraxGloss.addColorStop(1, 'rgba(0, 0, 0, 0.4)');
  ctx.fillStyle = thoraxGloss;
  ctx.beginPath();
  ctx.ellipse(-0.3, -0.7, 2.4, 0.9, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // 5. Head (Head Capsule) - Sculpted heart/shield shape with compound eyes
  ctx.save();
  ctx.fillStyle = bodyColor;
  const headRadiusX = ant.caste === 'GUARD' ? 3.4 : 2.7;
  const headRadiusY = ant.caste === 'GUARD' ? 3.0 : 2.3;

  ctx.beginPath();
  ctx.ellipse(3.8, 0, headRadiusX, headRadiusY, 0, 0, Math.PI * 2);
  ctx.fill();

  // Shiny forehead specular dot
  ctx.fillStyle = highlightColor;
  ctx.beginPath();
  ctx.arc(3.6, -0.8, 0.7, 0, Math.PI * 2);
  ctx.fill();

  // Compound Eyes with glossy corneal specular glint
  ctx.fillStyle = '#050505';
  ctx.beginPath();
  ctx.ellipse(4.4, -1.4, 0.8, 0.65, 0.2, 0, Math.PI * 2);
  ctx.ellipse(4.4, 1.4, 0.8, 0.65, -0.2, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.arc(4.6, -1.5, 0.25, 0, Math.PI * 2);
  ctx.arc(4.6, 1.3, 0.25, 0, Math.PI * 2);
  ctx.fill();

  // Queen Crown Insignia
  if (ant.caste === 'QUEEN') {
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    ctx.moveTo(2.6, -1.5);
    ctx.lineTo(3.2, -0.5);
    ctx.lineTo(2.4, 0);
    ctx.lineTo(3.2, 0.5);
    ctx.lineTo(2.6, 1.5);
    ctx.stroke();
  }
  ctx.restore();

  // 6. Antennae (Articulated Scape and Flagellum with active sensory twitch)
  ctx.strokeStyle = bodyColor;
  ctx.lineWidth = 0.9;
  ctx.lineCap = 'round';
  const antTwitch = ant.antennaeWiggle;

  // Left antenna
  ctx.beginPath();
  ctx.moveTo(5.2, -0.8);
  ctx.lineTo(6.8, -2.4); // Scape
  ctx.lineTo(9.2 + antTwitch, -3.8); // Flagellum tip
  ctx.stroke();

  // Right antenna
  ctx.beginPath();
  ctx.moveTo(5.2, 0.8);
  ctx.lineTo(6.8, 2.4); // Scape
  ctx.lineTo(9.2 - antTwitch, 3.8); // Flagellum tip
  ctx.stroke();

  // 7. Mandibles (Pincers) - Articulated with bite motion when digging
  const isBiting = ant.state === 'DIGGING' && Math.sin(Date.now() * 0.02) > 0.3;
  const mandOpen = isBiting ? 0.7 : ant.carrying ? 0.9 : 0.3;
  const mandColor = ant.caste === 'GUARD' ? '#ef4444' : '#5c2b14';

  ctx.strokeStyle = mandColor;
  ctx.lineWidth = ant.caste === 'GUARD' ? 1.4 : 1.1;
  ctx.beginPath();
  // Left mandible blade
  ctx.moveTo(5.8, -0.6);
  ctx.lineTo(7.4 + (ant.caste === 'GUARD' ? 1.0 : 0), -mandOpen);
  // Right mandible blade
  ctx.moveTo(5.8, 0.6);
  ctx.lineTo(7.4 + (ant.caste === 'GUARD' ? 1.0 : 0), mandOpen);
  ctx.stroke();

  // 8. Carried Item (Realistic 3D geometry with dynamic lighting & specular highlights)
  if (ant.carrying) {
    const item = ant.carrying;
    ctx.save();

    if (item.type === 'crystal') {
      // 3D Faceted Crystal Gem held proudly over the head
      ctx.shadowColor = item.color;
      ctx.shadowBlur = 9;

      // Outer crystal body
      ctx.fillStyle = item.color;
      ctx.beginPath();
      ctx.moveTo(7.5, -5.0);
      ctx.lineTo(12.5, 0);
      ctx.lineTo(7.5, 5.0);
      ctx.lineTo(3.5, 0);
      ctx.closePath();
      ctx.fill();

      // Sharp light facet
      ctx.fillStyle = '#e0f2fe';
      ctx.beginPath();
      ctx.moveTo(7.5, -5.0);
      ctx.lineTo(12.5, 0);
      ctx.lineTo(7.5, 0);
      ctx.closePath();
      ctx.fill();

      // Specular diamond sparkle flare
      drawDiamondFlare(ctx, 9.5, -1.0, 3.2, Date.now() * 0.003, 0.95);

      ctx.shadowBlur = 0;
    } else if (item.type === 'crystal_dust') {
      // Sparkling micro-crystal dust cluster
      ctx.shadowColor = '#38bdf8';
      ctx.shadowBlur = 6;
      ctx.fillStyle = '#7dd3fc';
      ctx.beginPath();
      ctx.arc(6.5, -1.8, 1.4, 0, Math.PI * 2);
      ctx.arc(8.5, 1.0, 1.3, 0, Math.PI * 2);
      ctx.arc(6.0, 1.6, 1.1, 0, Math.PI * 2);
      ctx.fill();
      drawDiamondFlare(ctx, 7.5, 0, 2.5, Date.now() * 0.004, 0.9);
      ctx.shadowBlur = 0;
    } else if (item.type === 'resin') {
      // Translucent glossy amber resin sphere with refraction
      const resinGrad = ctx.createRadialGradient(6.5, -1.2, 0.5, 7.5, 0, 4.0);
      resinGrad.addColorStop(0, '#fef08a');
      resinGrad.addColorStop(0.5, '#d97706');
      resinGrad.addColorStop(1, '#78350f');
      ctx.fillStyle = resinGrad;
      ctx.beginPath();
      ctx.arc(7.5, 0, 3.8, 0, Math.PI * 2);
      ctx.fill();

      // Specular reflection ring
      ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
      ctx.beginPath();
      ctx.arc(6.2, -1.2, 1.2, 0, Math.PI * 2);
      ctx.fill();
    } else if (item.type === 'mineral') {
      // Angular metallic ore chunk with specular facets
      ctx.fillStyle = '#475569';
      ctx.beginPath();
      ctx.moveTo(5.5, -3.2);
      ctx.lineTo(9.8, -2.5);
      ctx.lineTo(10.5, 2.5);
      ctx.lineTo(6.5, 3.5);
      ctx.lineTo(4.5, 0.5);
      ctx.closePath();
      ctx.fill();

      // Silver mica metallic sheen
      ctx.fillStyle = '#cbd5e1';
      ctx.beginPath();
      ctx.moveTo(6.5, -2.5);
      ctx.lineTo(9.5, -2.0);
      ctx.lineTo(8.0, 0.5);
      ctx.closePath();
      ctx.fill();
    } else {
      // Textured organic soil clod
      ctx.fillStyle = '#78350f';
      ctx.beginPath();
      ctx.arc(7.0, 0, 3.8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#451a03';
      ctx.beginPath();
      ctx.arc(6.2, 1.2, 1.8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#92400e';
      ctx.beginPath();
      ctx.arc(8.0, -1.2, 1.4, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }

  ctx.restore();
}
