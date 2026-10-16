import React from 'react';
import { ColonyRoom } from '../types/colony';
import { ROOM_PRESETS } from '../simulation/grid';
import { X, ArrowUpCircle, Boxes, Gem, Mountain, Layers, ShieldCheck } from 'lucide-react';

interface RoomManagerModalProps {
  room: ColonyRoom | null;
  canUpgrade: boolean;
  onClose: () => void;
  onUpgrade: (roomId: string) => void;
}

export const RoomManagerModal: React.FC<RoomManagerModalProps> = ({
  room,
  canUpgrade,
  onClose,
  onUpgrade,
}) => {
  if (!room) return null;

  const preset = ROOM_PRESETS[room.type];
  const upgradeCostResin = 4 * room.level;
  const upgradeCostCrystals = 2 * room.level;

  return (
    <div className="absolute top-16 right-6 w-84 bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-xl p-4 shadow-2xl z-30 text-slate-200">
      <div className="flex items-start justify-between pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: room.color }}
            />
            <h3 className="text-sm font-bold text-white font-['Plus_Jakarta_Sans']">
              {room.name}
            </h3>
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            Niveau {room.level} · Superficie : {room.tiles.length} blocs
          </div>
          {room.hasCommandTerminal && (
            <div className="mt-1 text-[11px] font-semibold text-cyan-300">
              Terminal de commandement de la Reine
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-md transition-colors"
          title="Fermer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="py-3 space-y-3 text-xs">
        <p className="text-slate-400 leading-relaxed">{preset.description}</p>

        {/* Resources stored in room */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Boxes className="w-3.5 h-3.5 text-amber-400" />
              Ressources stockées
            </span>
            <span className="font-mono text-[10px] text-slate-400">
              Capacité : {room.capacity}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between bg-slate-900/80 p-1.5 rounded">
              <span className="flex items-center gap-1 text-cyan-300">
                <Gem className="w-3 h-3 text-cyan-400" />
                Cristaux :
              </span>
              <span className="font-mono tabular-nums font-bold text-white">
                {room.storedResources.crystal}
              </span>
            </div>

            <div className="flex items-center justify-between bg-slate-900/80 p-1.5 rounded">
              <span className="flex items-center gap-1 text-amber-200">
                <Mountain className="w-3 h-3 text-amber-500" />
                Terreau :
              </span>
              <span className="font-mono tabular-nums font-bold text-white">
                {room.storedResources.dirt}
              </span>
            </div>

            <div className="flex items-center justify-between bg-slate-900/80 p-1.5 rounded">
              <span className="flex items-center gap-1 text-slate-300">
                <Layers className="w-3 h-3 text-slate-400" />
                Fragments :
              </span>
              <span className="font-mono tabular-nums font-bold text-white">
                {room.storedResources.mineral}
              </span>
            </div>

            <div className="flex items-center justify-between bg-slate-900/80 p-1.5 rounded">
              <span className="flex items-center gap-1 text-emerald-300">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                Bio-Résine :
              </span>
              <span className="font-mono tabular-nums font-bold text-white">
                {room.storedResources.resin}
              </span>
            </div>
          </div>
        </div>

        {/* Upgrade block */}
        <div className="bg-slate-950/40 border border-slate-800 rounded-lg p-2.5">
          <div className="flex items-center justify-between mb-1.5 text-slate-300">
            <span className="font-semibold text-[11px]">Améliorer la chambre</span>
            <span className="font-mono text-[10px] text-amber-400">
              Vers Niveau {room.level + 1}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mb-2">
            Coût : {upgradeCostResin} Bio-Résine · {upgradeCostCrystals} Cristaux
          </div>
          <button
            onClick={() => onUpgrade(room.id)}
            disabled={!canUpgrade}
            className={`w-full flex items-center justify-center gap-1.5 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              canUpgrade
                ? 'bg-amber-400 hover:bg-amber-300 text-slate-950'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            <ArrowUpCircle className="w-3.5 h-3.5" />
            Améliorer l'infrastructure
          </button>
        </div>
      </div>
    </div>
  );
};
