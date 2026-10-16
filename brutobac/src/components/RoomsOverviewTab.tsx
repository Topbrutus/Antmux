import React from 'react';
import { ColonyRoom, RoomType } from '../types/colony';
import { ROOM_PRESETS } from '../simulation/grid';
import { Building2, Boxes, Gem, Mountain, Layers, ShieldCheck, ArrowUpCircle } from 'lucide-react';

interface RoomsOverviewTabProps {
  rooms: ColonyRoom[];
  onSelectRoom: (id: string) => void;
  onUpgradeRoom: (id: string) => void;
  canUpgrade: (room: ColonyRoom) => boolean;
}

export const RoomsOverviewTab: React.FC<RoomsOverviewTabProps> = ({
  rooms,
  onSelectRoom,
  onUpgradeRoom,
  canUpgrade,
}) => {
  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-950 text-slate-200">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="pb-4 border-b border-slate-800">
          <h2 className="text-xl font-bold text-white font-['Plus_Jakarta_Sans']">
            Chambres Spécialisées & Aménagements Souterrains
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Gestion des {rooms.length} chambres creusées par la colonie : stockage, niveau et
            capacités de réserve.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rooms.map((room) => {
            const preset = ROOM_PRESETS[room.type];
            const upgradeAllowed = canUpgrade(room);
            const upgradeCostResin = 4 * room.level;
            const upgradeCostCrystals = 2 * room.level;

            return (
              <div
                key={room.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: room.color }}
                      />
                      <h3 className="font-bold text-sm text-white font-['Plus_Jakarta_Sans']">
                        {room.name}
                      </h3>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-300">
                      Niveau {room.level}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                    {preset.description}
                  </p>
                  {room.hasCommandTerminal && (
                    <div className="mt-2 text-[11px] font-semibold text-cyan-300">
                      Terminal de commandement de la Reine
                    </div>
                  )}

                  <div className="mt-3 bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
                    <div className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
                      <span className="flex items-center gap-1">
                        <Boxes className="w-3 h-3 text-amber-400" />
                        Stocks actuels
                      </span>
                      <span className="text-[10px] font-mono">
                        Capacité : {room.capacity}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                      <div className="flex items-center justify-between bg-slate-900/60 p-1 rounded">
                        <span className="text-cyan-300 flex items-center gap-1">
                          <Gem className="w-2.5 h-2.5" />
                          Cristaux :
                        </span>
                        <strong className="font-mono text-white">
                          {room.storedResources.crystal}
                        </strong>
                      </div>

                      <div className="flex items-center justify-between bg-slate-900/60 p-1 rounded">
                        <span className="text-amber-200 flex items-center gap-1">
                          <Mountain className="w-2.5 h-2.5" />
                          Terreau :
                        </span>
                        <strong className="font-mono text-white">
                          {room.storedResources.dirt}
                        </strong>
                      </div>

                      <div className="flex items-center justify-between bg-slate-900/60 p-1 rounded">
                        <span className="text-slate-300 flex items-center gap-1">
                          <Layers className="w-2.5 h-2.5" />
                          Fragments :
                        </span>
                        <strong className="font-mono text-white">
                          {room.storedResources.mineral}
                        </strong>
                      </div>

                      <div className="flex items-center justify-between bg-slate-900/60 p-1 rounded">
                        <span className="text-emerald-300 flex items-center gap-1">
                          <ShieldCheck className="w-2.5 h-2.5" />
                          Résine :
                        </span>
                        <strong className="font-mono text-white">
                          {room.storedResources.resin}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400 mt-2">
                    Profondeur moyenne :{' '}
                    <strong className="text-slate-200 font-mono">
                      -{Math.round(room.center.y * 0.52)} mètres
                    </strong>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
                  <div className="text-[10px] text-slate-400">
                    Coût : {upgradeCostResin} Résine · {upgradeCostCrystals} Cristaux
                  </div>
                  <button
                    onClick={() => onUpgradeRoom(room.id)}
                    disabled={!upgradeAllowed}
                    className={`flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                      upgradeAllowed
                        ? 'bg-amber-400 hover:bg-amber-300 text-slate-950'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    }`}
                  >
                    <ArrowUpCircle className="w-3.5 h-3.5" />
                    Améliorer
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
