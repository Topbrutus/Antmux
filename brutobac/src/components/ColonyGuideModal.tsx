import React from 'react';
import { X, Layers, Gem, Mountain, Sparkles, Compass, Shield } from 'lucide-react';
import { STRATA, ROOM_PRESETS } from '../simulation/grid';
import { RoomType } from '../types/colony';

interface ColonyGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ColonyGuideModal: React.FC<ColonyGuideModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const roomKeys: RoomType[] = [
    'QUEEN',
    'NURSERY',
    'STORAGE',
    'CRYSTAL_VAULT',
    'WORKSHOP',
    'RECYCLING',
    'GUARD_POST',
  ];

  return (
    <div className="fixed inset-0 bg-slate-950/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl text-slate-200 flex flex-col max-h-[85vh]">
        <div className="flex items-start justify-between pb-4 border-b border-slate-800 shrink-0">
          <div>
            <h2 className="text-base font-bold text-white font-['Plus_Jakarta_Sans'] flex items-center gap-2">
              <Compass className="w-4 h-4 text-cyan-400" />
              Guide Géologique & Écosystème BrutoBac
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Comprendre la structure multi-étages, le creusage, les cristaux enfouis et la colonie.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-6 overflow-y-auto pr-1 text-xs">
          {/* Section 1: Cycle de Simulation */}
          <div>
            <h3 className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5" />
              1. Le Cycle : Creuser → Révéler → Exploiter
            </h3>
            <p className="text-slate-300 leading-relaxed">
              Le terrier n’est pas un simple décor mais une matière vivante à excaver. Vous pouvez
              creuser manuellement avec le pinceau ou poser des ordres de fouille pour que vos
              ouvrières forrent les galeries. En descendant dans la roche, vous dévoilez le brouillard
              souterrain et mettez au jour des veines de matière et des cristaux résonants.
            </p>
          </div>

          {/* Section 2: Les 5 Étages Stratigraphiques */}
          <div>
            <h3 className="text-sm font-semibold text-cyan-400 mb-2 flex items-center gap-2">
              <Layers className="w-3.5 h-3.5" />
              2. Les Étages Géologiques Souterrains
            </h3>
            <div className="space-y-2">
              {STRATA.map((stratum) => (
                <div
                  key={stratum.id}
                  className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5 flex items-start justify-between gap-3"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: stratum.themeColor }}
                      />
                      <span className="font-semibold text-white">{stratum.name}</span>
                      <span className="text-[10px] text-slate-400">({stratum.depthLabel})</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">{stratum.description}</p>
                  </div>
                  <span className="text-[10px] font-mono text-amber-300/80 whitespace-nowrap">
                    {stratum.discoveryBonus}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Les Cristaux & Ressources */}
          <div>
            <h3 className="text-sm font-semibold text-cyan-300 mb-2 flex items-center gap-2">
              <Gem className="w-3.5 h-3.5 text-cyan-400" />
              3. Les Ressources Enfouies
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div className="bg-slate-950/50 border border-slate-800 p-2.5 rounded-lg">
                <span className="font-semibold text-cyan-300">Cristaux Bruto</span>
                <p className="text-[11px] text-slate-400 mt-1">
                  Minéraux étincelants logés dans les parois profondes. Ils alimentent la réserve
                  de résonance et permettent les évolutions majeures.
                </p>
              </div>
              <div className="bg-slate-950/50 border border-slate-800 p-2.5 rounded-lg">
                <span className="font-semibold text-amber-300">Matière Brute & Terreau</span>
                <p className="text-[11px] text-slate-400 mt-1">
                  Terre meuble excavée des galeries, utilisée pour tapisser les chambres, nourrir
                  le couvain et façonner de nouveaux aménagements.
                </p>
              </div>
              <div className="bg-slate-950/50 border border-slate-800 p-2.5 rounded-lg">
                <span className="font-semibold text-slate-200">Fragments Minéraux</span>
                <p className="text-[11px] text-slate-400 mt-1">
                  Éclats de schiste et minerais métalliques transformés dans l’atelier en renforts
                  de tunnel et outillage.
                </p>
              </div>
              <div className="bg-slate-950/50 border border-slate-800 p-2.5 rounded-lg">
                <span className="font-semibold text-emerald-300">Bio-Résine</span>
                <p className="text-[11px] text-slate-400 mt-1">
                  Résine d’étayage produite à partir de matière organique pour consolider les parois
                  et élever le niveau des chambres.
                </p>
              </div>
            </div>
          </div>

          {/* Section 4: Typologie des Chambres */}
          <div>
            <h3 className="text-sm font-semibold text-emerald-400 mb-2 flex items-center gap-2">
              <Mountain className="w-3.5 h-3.5" />
              4. Aménagement des Chambres Spécialisées
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {roomKeys.map((k) => {
                const preset = ROOM_PRESETS[k];
                return (
                  <div
                    key={k}
                    className="bg-slate-950/40 border border-slate-800/80 p-2 rounded flex items-start gap-2"
                  >
                    <span
                      className="w-2 h-2 rounded-full mt-1 shrink-0"
                      style={{ backgroundColor: preset.color }}
                    />
                    <div>
                      <span className="font-medium text-white">{preset.name}</span>
                      <p className="text-[10px] text-slate-400">{preset.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-amber-400 text-slate-950 rounded-lg hover:bg-amber-300 transition-colors"
          >
            Compris, retourner au terrier
          </button>
        </div>
      </div>
    </div>
  );
};
