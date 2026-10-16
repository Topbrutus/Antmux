import React from 'react';
import { AntCaste, ColonyStats } from '../types/colony';
import { X, Sparkles, Pickaxe, Truck, HeartHandshake, Shield, Wrench } from 'lucide-react';

interface RecruitmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  stats: ColonyStats;
  onRecruit: (caste: AntCaste) => void;
}

interface CasteChoice {
  caste: AntCaste;
  title: string;
  role: string;
  icon: React.ReactNode;
  costDirt: number;
  costMineral: number;
  description: string;
}

export const RecruitmentModal: React.FC<RecruitmentModalProps> = ({
  isOpen,
  onClose,
  stats,
  onRecruit,
}) => {
  if (!isOpen) return null;

  const choices: CasteChoice[] = [
    {
      caste: 'MINER',
      title: 'Ouvrière Creuseuse',
      role: 'Excavation & Forage',
      icon: <Pickaxe className="w-4 h-4 text-amber-400" />,
      costDirt: 10,
      costMineral: 5,
      description: 'Creuse les roches dures, perce les galeries et révèle les cristaux enfouis.',
    },
    {
      caste: 'CARRIER',
      title: 'Porteuse de Ressources',
      role: 'Logistique & Transport',
      icon: <Truck className="w-4 h-4 text-cyan-400" />,
      costDirt: 8,
      costMineral: 4,
      description: 'Ramasse les cristaux et fragments détachés pour les acheminer vers les réserves.',
    },
    {
      caste: 'NURSE',
      title: 'Nourrice du Couvain',
      role: 'Élevage & Éclosion',
      icon: <HeartHandshake className="w-4 h-4 text-pink-400" />,
      costDirt: 12,
      costMineral: 2,
      description: 'Prend soin des œufs royaux dans la nurserie pour faire naître de nouvelles fourmis.',
    },
    {
      caste: 'BUILDER',
      title: 'Bâtisseuse & Charpentière',
      role: 'Consolidation & Aménagement',
      icon: <Wrench className="w-4 h-4 text-emerald-400" />,
      costDirt: 14,
      costMineral: 8,
      description: 'Étaye les tunnels profonds avec de la bio-résine pour éviter les effondrements.',
    },
    {
      caste: 'GUARD',
      title: 'Sentinelle Défensive',
      role: 'Sécurité & Veille',
      icon: <Shield className="w-4 h-4 text-rose-400" />,
      costDirt: 15,
      costMineral: 10,
      description: 'Protège l’entrée de surface et surveille les failles sismiques profondes.',
    },
  ];

  return (
    <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl text-slate-200">
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-base font-bold text-white font-['Plus_Jakarta_Sans'] flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Incubation de Nouvelles Fourmis
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              La Reine active la ponte d'ouvrières spécialisées en utilisant le terreau et les fragments minéraux.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          {choices.map((c) => {
            const canAfford = stats.dirt >= c.costDirt && stats.minerals >= c.costMineral;

            return (
              <div
                key={c.caste}
                className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between gap-4 transition-colors hover:border-slate-700"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {c.icon}
                    <span className="font-semibold text-sm text-white">{c.title}</span>
                    <span className="text-[10px] text-slate-400">· {c.role}</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{c.description}</p>
                  <div className="text-[11px] font-mono text-slate-300">
                    Coût : {c.costDirt} Terreau · {c.costMineral} Fragments
                  </div>
                </div>

                <button
                  onClick={() => {
                    onRecruit(c.caste);
                  }}
                  disabled={!canAfford}
                  className={`px-3.5 py-2 text-xs font-semibold rounded-lg whitespace-nowrap shrink-0 transition-colors ${
                    canAfford
                      ? 'bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold'
                      : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  Incuber
                </button>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Ressources actuelles :{' '}
            <strong className="text-amber-300">{stats.dirt}</strong> Terreau ·{' '}
            <strong className="text-slate-200">{stats.minerals}</strong> Fragments
          </span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};
