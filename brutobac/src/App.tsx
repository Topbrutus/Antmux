/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import { colonyEngine, ColonyEngineState } from './simulation/colonyEngine';
import { soundEngine } from './audio/soundEngine';
import { ActiveTool, RoomType, AntCaste, QueenFormulaPriority } from './types/colony';
import { TopBar } from './components/TopBar';
import { ColonyDashboard } from './components/ColonyDashboard';
import { Toolbar } from './components/Toolbar';
import { SubterraneanCanvas } from './components/SubterraneanCanvas';
import { AntInspectorModal } from './components/AntInspectorModal';
import { RoomManagerModal } from './components/RoomManagerModal';
import { RecruitmentModal } from './components/RecruitmentModal';
import { ColonyGuideModal } from './components/ColonyGuideModal';
import { ColonyOverviewTab } from './components/ColonyOverviewTab';
import { RoomsOverviewTab } from './components/RoomsOverviewTab';
import { CellInspectorModal } from './components/CellInspectorModal';

export default function App() {
  const [engineState, setEngineState] = useState<ColonyEngineState>(colonyEngine.state);
  const [activeTab, setActiveTab] = useState<'terrier' | 'colonie' | 'salles'>('terrier');
  const [activeTool, setActiveTool] = useState<ActiveTool>('DIG_MANUAL');
  const [selectedRoomType, setSelectedRoomType] = useState<RoomType>('CRYSTAL_VAULT');
  const [brushRadius, setBrushRadius] = useState<number>(1);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(soundEngine.isEnabled());
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(false);
  const [isRecruitOpen, setIsRecruitOpen] = useState<boolean>(false);
  const [focusedDepth, setFocusedDepth] = useState<number | undefined>(undefined);

  const [selectedCellCoords, setSelectedCellCoords] = useState<{ x: number; y: number } | null>(null);

  // Subscribe to simulation state changes
  useEffect(() => {
    const unsubscribe = colonyEngine.subscribe(() => {
      setEngineState({ ...colonyEngine.state });
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    let cancelled = false;
    const syncQueenTerminal = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8788/api/queen-priorities');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        const priorities: QueenFormulaPriority[] = Array.isArray(payload.items)
          ? payload.items.map((item: any) => ({
              formulaId: String(item.formula_id),
              name: String(item.name),
              slot: Number(item.slot),
              priority: Number(item.priority),
            }))
          : [];
        if (!cancelled) colonyEngine.setQueenFormulaPriorities(priorities);
      } catch {
        if (!cancelled) colonyEngine.setQueenTerminalOffline();
      }
    };
    syncQueenTerminal();
    const timer = window.setInterval(syncQueenTerminal, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  // Main game tick animation frame
  useEffect(() => {
    let animId: number;
    const loop = (timestamp: number) => {
      colonyEngine.tick(timestamp);
      animId = requestAnimationFrame(loop);
    };
    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.code === 'Space') {
        e.preventDefault();
        colonyEngine.setSpeed(engineState.speed === 0 ? 1 : 0);
      } else if (e.key === '1') {
        colonyEngine.setSpeed(1);
      } else if (e.key === '2') {
        colonyEngine.setSpeed(2);
      } else if (e.key === '4') {
        colonyEngine.setSpeed(4);
      } else if (e.key === 'd' || e.key === 'D') {
        setActiveTool('DIG_MANUAL');
      } else if (e.key === 'f' || e.key === 'F') {
        setActiveTool('DESIGNATE_DIG');
      } else if (e.key === 'r' || e.key === 'R') {
        setActiveTool('DESIGNATE_ROOM');
      } else if (e.key === 'i' || e.key === 'I') {
        setActiveTool('INSPECT_ANT');
      } else if (e.key === 'm' || e.key === 'M') {
        toggleSound();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [engineState.speed]);

  const toggleSound = () => {
    const nextVal = !soundEnabled;
    soundEngine.setEnabled(nextVal);
    setSoundEnabled(nextVal);
  };

  const handleManualDig = useCallback((x: number, y: number, radius: number) => {
    colonyEngine.manualDig(x, y, radius);
  }, []);

  const handleDesignateDig = useCallback((x: number, y: number) => {
    colonyEngine.addDigTask(x, y);
  }, []);

  const handleDesignateRoom = useCallback((x: number, y: number, type: RoomType) => {
    colonyEngine.designateRoomAt(x, y, type);
  }, []);

  const handleSelectAnt = useCallback((id: string | null) => {
    colonyEngine.setSelectedAnt(id);
    if (id) {
      colonyEngine.setSelectedRoom(null);
      setSelectedCellCoords(null);
    }
  }, []);

  const handleSelectRoom = useCallback((id: string | null) => {
    colonyEngine.setSelectedRoom(id);
    if (id) {
      colonyEngine.setSelectedAnt(null);
      setSelectedCellCoords(null);
    }
  }, []);

  const handleSelectCell = useCallback((coords: { x: number; y: number } | null) => {
    setSelectedCellCoords(coords);
    if (coords) {
      colonyEngine.setSelectedAnt(null);
      colonyEngine.setSelectedRoom(null);
    }
  }, []);

  const handleFollowAnt = (ant: { y: number }) => {
    setFocusedDepth(ant.y);
    setActiveTab('terrier');
  };

  const handleRecruit = (caste: AntCaste) => {
    colonyEngine.recruitAnt(caste);
  };

  const handleUpgradeRoom = (roomId: string) => {
    colonyEngine.upgradeRoom(roomId);
  };

  const canUpgradeRoom = (room: { level: number }) => {
    const costResin = 4 * room.level;
    const costCrystals = 2 * room.level;
    return engineState.stats.resin >= costResin && engineState.stats.crystals >= costCrystals;
  };

  const selectedAnt = engineState.ants.find((a) => a.id === engineState.selectedAntId) || null;
  const selectedRoom = engineState.grid.rooms.find((r) => r.id === engineState.selectedRoomId) || null;
  const selectedCell = selectedCellCoords ? colonyEngine.getCellInfo(selectedCellCoords.x, selectedCellCoords.y) : null;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-['Plus_Jakarta_Sans'] select-none">
      {/* 1. Header (Strict Top Bar Contract) */}
      <TopBar
        onOpenGuide={() => setIsGuideOpen(true)}
        onOpenRecruitment={() => setIsRecruitOpen(true)}
        soundEnabled={soundEnabled}
        onToggleSound={toggleSound}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab as any)}
      />

      {/* 2. Colony Dashboard (Unboxed telemetry & resource counters) */}
      <ColonyDashboard
        stats={engineState.stats}
        rooms={engineState.grid.rooms}
        queenTerminal={engineState.queenTerminal}
      />

      {/* 3. Main Viewport Area */}
      <div className="flex-1 relative overflow-hidden flex flex-col">
        {activeTab === 'terrier' && (
          <>
            <SubterraneanCanvas
              engineState={engineState}
              activeTool={activeTool}
              selectedRoomType={selectedRoomType}
              brushRadius={brushRadius}
              onManualDig={handleManualDig}
              onDesignateDig={handleDesignateDig}
              onDesignateRoom={handleDesignateRoom}
              onSelectAnt={handleSelectAnt}
              onSelectRoom={handleSelectRoom}
              onSelectCell={handleSelectCell}
              selectedCellCoords={selectedCellCoords}
              focusedDepth={focusedDepth}
            />

            {/* Overlays / Inspector Drawer */}
            <AntInspectorModal
              ant={selectedAnt}
              onClose={() => handleSelectAnt(null)}
              onFollowAnt={handleFollowAnt}
            />

            <RoomManagerModal
              room={selectedRoom}
              canUpgrade={selectedRoom ? canUpgradeRoom(selectedRoom) : false}
              onClose={() => handleSelectRoom(null)}
              onUpgrade={handleUpgradeRoom}
            />

            <CellInspectorModal
              cell={selectedCell}
              onClose={() => setSelectedCellCoords(null)}
              onDig={(x, y) => {
                colonyEngine.manualDig(x, y, 0);
                setSelectedCellCoords({ x, y });
              }}
            />
          </>
        )}

        {activeTab === 'colonie' && (
          <ColonyOverviewTab
            ants={engineState.ants}
            onSelectAnt={(id) => {
              const ant = engineState.ants.find((a) => a.id === id);
              if (ant) {
                handleFollowAnt(ant);
                handleSelectAnt(id);
              }
            }}
            onOpenRecruit={() => setIsRecruitOpen(true)}
          />
        )}

        {activeTab === 'salles' && (
          <RoomsOverviewTab
            rooms={engineState.grid.rooms}
            onSelectRoom={(id) => {
              const room = engineState.grid.rooms.find((r) => r.id === id);
              if (room) {
                setFocusedDepth(room.center.y);
                setActiveTab('terrier');
                handleSelectRoom(id);
              }
            }}
            onUpgradeRoom={handleUpgradeRoom}
            canUpgrade={canUpgradeRoom}
          />
        )}
      </div>

      {/* 4. Bottom Toolbar (Visible on Coupe Souterraine) */}
      {activeTab === 'terrier' && (
        <Toolbar
          activeTool={activeTool}
          onSelectTool={setActiveTool}
          selectedRoomType={selectedRoomType}
          onSelectRoomType={setSelectedRoomType}
          brushRadius={brushRadius}
          onSetBrushRadius={setBrushRadius}
          speed={engineState.speed}
          onSetSpeed={(s) => colonyEngine.setSpeed(s)}
          pendingTasksCount={engineState.digTasks.length}
          onDesignateAllFronts={() => colonyEngine.designateAllAccessibleFronts()}
        />
      )}

      {/* 5. Modals */}
      <RecruitmentModal
        isOpen={isRecruitOpen}
        onClose={() => setIsRecruitOpen(false)}
        stats={engineState.stats}
        onRecruit={handleRecruit}
      />

      <ColonyGuideModal isOpen={isGuideOpen} onClose={() => setIsGuideOpen(false)} />
    </div>
  );
}
