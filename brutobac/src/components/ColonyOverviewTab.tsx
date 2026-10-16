import React from 'react';
import { Ant, AntCaste } from '../types/colony';
import { Sparkles, Compass, Briefcase, Gem, Activity } from 'lucide-react';

interface ColonyOverviewTabProps {
  ants: Ant[];
  onSelectAnt: (id: string) => void;
  onOpenRecruit: () => void;
}

export const ColonyOverviewTab: React.FC<ColonyOverviewTabProps> = ({
  ants,
  onSelectAnt,
  onOpenRecruit,
}) => {
  const casteCounts = ants.reduce(
    (acc, ant) => {
      acc[ant.caste] = (acc[ant.caste] || 0) + 1;
      return acc;
    },
    {} as Record<AntCaste, number>
  );

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-950 text-slate-200">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-xl font-bold text-white font-['Plus_Jakarta_Sans']">
              Recensement & Castes de la Colonie
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Vue en temps réel des {ants.length} fourmis actives, de leurs occupations et cargaisons.
            </p>
          </div>
          <button
            onClick={onOpenRecruit}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 rounded-lg transition-colors shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Incuber de Nouvelles Ouvrières
          </button>
        </div>

        {/* Caste Distribution Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3">
            <div className="text-[11px] text-amber-400 font-semibold">Reine</div>
            <div className="text-2xl font-bold text-white font-mono mt-1">
              {casteCounts.QUEEN || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Centre biologique</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3">
            <div className="text-[11px] text-amber-300 font-semibold">Creuseuses</div>
            <div className="text-2xl font-bold text-white font-mono mt-1">
              {casteCounts.MINER || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Excavation roche</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3">
            <div className="text-[11px] text-cyan-300 font-semibold">Porteuses</div>
            <div className="text-2xl font-bold text-white font-mono mt-1">
              {casteCounts.CARRIER || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Logistique matières</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3">
            <div className="text-[11px] text-pink-300 font-semibold">Nourrices</div>
            <div className="text-2xl font-bold text-white font-mono mt-1">
              {casteCounts.NURSE || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Soin des larves</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3">
            <div className="text-[11px] text-emerald-300 font-semibold">Bâtisseuses</div>
            <div className="text-2xl font-bold text-white font-mono mt-1">
              {casteCounts.BUILDER || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Étayage galeries</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3">
            <div className="text-[11px] text-rose-400 font-semibold">Sentinelles</div>
            <div className="text-2xl font-bold text-white font-mono mt-1">
              {casteCounts.GUARD || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Sécurité du terrier</div>
          </div>
        </div>

        {/* Live List of Ants */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 text-xs font-semibold text-slate-300">
            Membres de la colonie ({ants.length})
          </div>
          <div className="divide-y divide-slate-800/60 max-h-[500px] overflow-y-auto">
            {ants.map((ant) => (
              <div
                key={ant.id}
                onClick={() => onSelectAnt(ant.id)}
                className="px-4 py-3 flex items-center justify-between gap-4 hover:bg-slate-800/40 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-950 flex items-center justify-center border border-slate-800">
                    <Activity className="w-4 h-4 text-slate-400" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white flex items-center gap-2">
                      {ant.name}
                      <span className="text-[10px] font-normal text-slate-400">
                        ({ant.caste})
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      « {ant.currentThought} »
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6 text-xs text-slate-400">
                  <div className="hidden sm:flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                    <span>
                      {ant.carrying ? (
                        <strong className="text-white font-medium">
                          {ant.carrying.name}
                        </strong>
                      ) : (
                        'Vide'
                      )}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 text-cyan-300">
                    <Gem className="w-3 h-3 text-cyan-400" />
                    <span className="font-mono tabular-nums font-semibold">
                      {ant.crystalsDiscovered}
                    </span>
                  </div>

                  <div className="text-slate-400 font-mono text-[11px]">
                    -{Math.round(ant.y * 0.52)}m
                  </div>

                  <button className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
                    <Compass className="w-3.5 h-3.5" />
                    Suivre
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
