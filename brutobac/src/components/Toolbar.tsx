import React from 'react';
import { ActiveTool, RoomType } from '../types/colony';
import { ROOM_PRESETS } from '../simulation/grid';
import {
  Pickaxe,
  Brush,
  Compass,
  Play,
  Pause,
  FastForward,
  Building2,
  ChevronDown,
  Radio,
} from 'lucide-react';
import {
  PheromoneSignalType,
  ALL_PHEROMONE_SIGNALS,
  PHEROMONE_METADATA,
} from '../types/stigmergy';

interface ToolbarProps {
  activeTool: ActiveTool;
  onSelectTool: (tool: ActiveTool) => void;
  selectedRoomType: RoomType;
  onSelectRoomType: (type: RoomType) => void;
  brushRadius: number;
  onSetBrushRadius: (r: number) => void;
  speed: number;
  onSetSpeed: (speed: number) => void;
  pendingTasksCount: number;
  onDesignateAllFronts?: () => void;
  activePheromone?: PheromoneSignalType | 'NONE';
  onSelectPheromone?: (signal: PheromoneSignalType | 'NONE') => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  activeTool,
  onSelectTool,
  selectedRoomType,
  onSelectRoomType,
  brushRadius,
  onSetBrushRadius,
  speed,
  onSetSpeed,
  pendingTasksCount,
  onDesignateAllFronts,
  activePheromone,
  onSelectPheromone,
}) => {
  const roomTypes: RoomType[] = [
    'CRYSTAL_VAULT',
    'STORAGE',
    'NURSERY',
    'WORKSHOP',
    'RECYCLING',
    'GUARD_POST',
    'QUEEN',
  ];

  return (
    <div className="bg-slate-900 border-t border-slate-800 px-4 py-2.5 z-20 shrink-0">
      <div className="flex flex-wrap items-center justify-between gap-3 max-w-7xl mx-auto">
        {/* Left: Interactive Tool Selection Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-950/70 border border-slate-800 rounded-lg">
          <button
            onClick={() => onSelectTool('INSPECT_ANT')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
              activeTool === 'INSPECT_ANT'
                ? 'bg-slate-800 text-cyan-300 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            Inspecter / Suivre
          </button>

          <button
            onClick={() => onSelectTool('DIG_MANUAL')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
              activeTool === 'DIG_MANUAL'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Brush className="w-3.5 h-3.5" />
            Creusage Manuel
          </button>

          <button
            onClick={() => onSelectTool('DESIGNATE_DIG')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
              activeTool === 'DESIGNATE_DIG'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Pickaxe className="w-3.5 h-3.5" />
            Ordre de Fouille
            {pendingTasksCount > 0 && (
              <span className="font-mono text-[10px] text-amber-400 font-bold ml-0.5">
                ({pendingTasksCount})
              </span>
            )}
          </button>

          <button
            onClick={() => onSelectTool('DESIGNATE_ROOM')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
              activeTool === 'DESIGNATE_ROOM'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            Aménager Salle
          </button>
        </div>

        {/* Center: Contextual Tool Options */}
        <div className="flex items-center gap-3">
          {activeTool === 'DIG_MANUAL' && (
            <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950/60 px-2.5 py-1 rounded-md border border-slate-800">
              <span className="text-slate-400">Rayon d’excavation :</span>
              <button
                onClick={() => onSetBrushRadius(1)}
                className={`px-2 py-0.5 rounded text-xs font-mono ${
                  brushRadius === 1
                    ? 'bg-amber-400 text-slate-950 font-bold'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                1x
              </button>
              <button
                onClick={() => onSetBrushRadius(2)}
                className={`px-2 py-0.5 rounded text-xs font-mono ${
                  brushRadius === 2
                    ? 'bg-amber-400 text-slate-950 font-bold'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                2x
              </button>
              <button
                onClick={() => onSetBrushRadius(3)}
                className={`px-2 py-0.5 rounded text-xs font-mono ${
                  brushRadius === 3
                    ? 'bg-amber-400 text-slate-950 font-bold'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                3x
              </button>
            </div>
          )}

          {activeTool === 'DESIGNATE_ROOM' && (
            <div className="flex items-center gap-2 text-xs bg-slate-950/60 px-2.5 py-1 rounded-md border border-slate-800">
              <span className="text-slate-400">Type de chambre :</span>
              <div className="relative inline-block">
                <select
                  value={selectedRoomType}
                  onChange={(e) => onSelectRoomType(e.target.value as RoomType)}
                  aria-label="Sélectionner le type de chambre à aménager"
                  className="appearance-none bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded px-2.5 py-1 pr-6 font-medium focus:outline-none focus:border-amber-400 cursor-pointer"
                >
                  {roomTypes.map((t) => (
                    <option key={t} value={t}>
                      {ROOM_PRESETS[t].name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3 h-3 text-slate-400 absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>
          )}

          {activeTool === 'DESIGNATE_DIG' && (
            <div className="flex items-center gap-2 text-xs bg-slate-950/60 px-2.5 py-1 rounded-md border border-slate-800">
              <span className="text-amber-300 font-medium hidden sm:inline">Fronts accessibles</span>
              {onDesignateAllFronts && (
                <button
                  onClick={onDesignateAllFronts}
                  className="px-2 py-0.5 rounded text-xs bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 transition-colors font-medium cursor-pointer"
                >
                  Désigner les fronts
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right: Simulation Speed Buttons */}
        <div className="flex items-center gap-1 p-1 bg-slate-950/70 border border-slate-800 rounded-lg">
          <button
            onClick={() => onSetSpeed(speed === 0 ? 1 : 0)}
            className={`p-1.5 rounded transition-colors ${
              speed === 0
                ? 'bg-rose-500/20 text-rose-300'
                : 'text-slate-400 hover:text-white'
            }`}
            title={speed === 0 ? 'Reprendre (Lecture)' : 'Pause'}
          >
            {speed === 0 ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={() => onSetSpeed(1)}
            className={`px-2 py-1 text-xs font-mono font-medium rounded transition-colors ${
              speed === 1
                ? 'bg-slate-800 text-white font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            1x
          </button>

          <button
            onClick={() => onSetSpeed(2)}
            className={`px-2 py-1 text-xs font-mono font-medium rounded transition-colors ${
              speed === 2
                ? 'bg-slate-800 text-white font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            2x
          </button>

          <button
            onClick={() => onSetSpeed(4)}
            className={`flex items-center gap-0.5 px-2 py-1 text-xs font-mono font-medium rounded transition-colors ${
              speed === 4
                ? 'bg-amber-400 text-slate-950 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FastForward className="w-3 h-3" />
            4x
          </button>
        </div>
      </div>
    </div>
  );
};
