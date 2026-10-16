import React, { useState } from 'react';
import { Ant, AntCaste, ALL_ANT_TASKS, TASK_LABELS, AntTaskType } from '../types/colony';
import { getAntInspectionData } from '../simulation/antAgent';
import {
  X,
  Activity,
  Compass,
  Briefcase,
  Zap,
  Target,
  Clock,
  History,
  Shield,
  Pickaxe,
  Gauge,
  ChevronDown,
  ChevronUp,
  Hammer,
  Egg,
  Recycle,
  Sparkles,
  Award,
  GitBranch,
} from 'lucide-react';

function renderTaskIcon(task: AntTaskType, className: string = 'w-3.5 h-3.5') {
  switch (task) {
    case 'dig':
      return <Pickaxe className={className} />;
    case 'carry':
      return <Briefcase className={className} />;
    case 'explore':
      return <Compass className={className} />;
    case 'build':
      return <Hammer className={className} />;
    case 'brood':
      return <Egg className={className} />;
    case 'defense':
      return <Shield className={className} />;
    case 'recycle':
      return <Recycle className={className} />;
    default:
      return <Sparkles className={className} />;
  }
}

interface AntInspectorModalProps {
  ant: Ant | null;
  onClose: () => void;
  onFollowAnt: (ant: Ant) => void;
}

const CASTE_LABELS: Record<AntCaste, { label: string; desc: string; color: string }> = {
  QUEEN: {
    label: 'Reine de la Colonie',
    desc: 'Centre biologique suprême, ponte d’œufs et aura harmonique.',
    color: 'text-amber-400',
  },
  MINER: {
    label: 'Ouvrière Creuseuse',
    desc: 'Excavation des roches dures et détection des filons de cristaux.',
    color: 'text-amber-300',
  },
  CARRIER: {
    label: 'Porteuse de Ressources',
    desc: 'Acheminement rapide des cristaux et matières vers les chambres.',
    color: 'text-cyan-300',
  },
  NURSE: {
    label: 'Nourrice du Couvain',
    desc: 'Incubation, nourrissage des larves et éclosion des nouvelles ouvrières.',
    color: 'text-pink-300',
  },
  BUILDER: {
    label: 'Bâtisseuse & Charpentière',
    desc: 'Renforcement des parois de galerie et construction des aménagements.',
    color: 'text-emerald-300',
  },
  GUARD: {
    label: 'Sentinelle Défensive',
    desc: 'Surveillance des seuils d’entrée et des vibrations profondes.',
    color: 'text-rose-400',
  },
};

export const AntInspectorModal: React.FC<AntInspectorModalProps> = ({
  ant,
  onClose,
  onFollowAnt,
}) => {
  const [showHistory, setShowHistory] = useState(false);

  if (!ant) return null;

  const casteInfo = CASTE_LABELS[ant.caste] || {
    label: ant.caste,
    desc: 'Membre de la colonie',
    color: 'text-slate-300',
  };

  const data = getAntInspectionData(ant);

  return (
    <div className="absolute top-16 right-6 w-88 max-h-[85vh] overflow-y-auto bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-xl p-4 shadow-2xl z-30 text-slate-200 font-['Plus_Jakarta_Sans']">
      {/* Header with ant_id and Caste */}
      <div className="flex items-start justify-between pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white">
              {data.name}
            </h3>
            <span className="font-mono text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
              {data.ant_id}
            </span>
          </div>
          <div className="text-xs font-medium mt-0.5 flex items-center gap-2">
            <span className={casteInfo.color}>{casteInfo.label}</span>
            <span className="text-slate-500">·</span>
            <span className="text-slate-400">{data.sizeCategory}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-md transition-colors cursor-pointer"
          title="Fermer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="py-3 space-y-2.5 text-xs">
        {/* Current State & Task */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-2.5 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400 flex items-center gap-1.5 font-medium">
              <Activity className="w-3 h-3 text-cyan-400" />
              État actuel :
            </span>
            <span className="font-semibold text-emerald-400">{data.stateLabel}</span>
          </div>
          <div className="text-[11px] text-slate-300 italic font-mono bg-slate-900/80 p-1.5 rounded border border-slate-800/50">
            « {data.task} »
          </div>
        </div>

        {/* Destination & Coordinates */}
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2 space-y-1">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-slate-400">
              <Target className="w-3 h-3 text-amber-400" />
              Destination :
            </span>
            <span className="font-mono text-slate-200 text-[11px] text-right truncate max-w-[170px]" title={data.destinationLabel}>
              {data.destinationLabel}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-0.5 border-t border-slate-800/40">
            <span>Position actuelle :</span>
            <span className="font-mono text-slate-300">
              X: {data.position.x} · Y: {data.position.y} (-{data.position.depthMeters}m)
            </span>
          </div>
        </div>

        {/* Load & Object Transported */}
        <div className="flex items-center justify-between text-slate-300 py-1.5 px-2 bg-slate-950/40 rounded-lg border border-slate-800/60">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Briefcase className="w-3.5 h-3.5 text-amber-300" />
            Charge transportée :
          </span>
          <span className="font-semibold text-white truncate max-w-[170px]">
            {data.load.color ? (
              <span className="inline-flex items-center gap-1.5">
                <span
                  className="w-2.5 h-2.5 rounded-full inline-block shrink-0"
                  style={{ backgroundColor: data.load.color }}
                />
                <span className="truncate">{data.load.item}</span>
              </span>
            ) : (
              data.load.item
            )}
          </span>
        </div>

        {/* Bloc 5: Division Adaptative du Travail */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Division du Travail
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              Auto-organisation
            </span>
          </div>

          {/* Active Task & Dominant Specialty Badges */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-900/90 border border-slate-700/60 rounded-lg p-2">
              <div className="text-[10px] text-slate-400 font-medium mb-1 flex items-center justify-between">
                <span>Tâche active :</span>
                <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: TASK_LABELS[data.activeTask]?.color || '#38bdf8' }} />
              </div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-white">
                {renderTaskIcon(data.activeTask, 'w-3.5 h-3.5')}
                <span style={{ color: TASK_LABELS[data.activeTask]?.color || '#ffffff' }}>
                  {data.activeTaskLabel}
                </span>
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-700/60 rounded-lg p-2">
              <div className="text-[10px] text-slate-400 font-medium mb-1 flex items-center gap-1">
                <Award className="w-3 h-3 text-amber-400" />
                <span>Spécialité dominante :</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-white">
                {renderTaskIcon(data.dominantSpecialty, 'w-3.5 h-3.5')}
                <span style={{ color: TASK_LABELS[data.dominantSpecialty]?.color || '#ffffff' }}>
                  {data.dominantSpecialtyLabel}
                </span>
              </div>
            </div>
          </div>

          {/* Last Task Switch Reason */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-2 space-y-1">
            <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1.5">
              <GitBranch className="w-3 h-3 text-cyan-400" />
              <span>Dernière réaffectation :</span>
            </div>
            <div className="text-[11px] text-slate-300 italic font-mono pl-4 border-l-2 border-cyan-500/60">
              « {data.lastTaskSwitchReason} »
            </div>
          </div>

          {/* Task Affinities (Response Thresholds) & Experience Table */}
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400">
              <span>Seuils de réponse (Affinités)</span>
              <span>Expérience (XP)</span>
            </div>

            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-0.5">
              {ALL_ANT_TASKS.map((taskKey) => {
                const conf = TASK_LABELS[taskKey];
                const affinityVal = data.taskAffinity[taskKey] ?? 0.4;
                const xpVal = data.taskExperience[taskKey] ?? 0;
                const isActive = data.activeTask === taskKey;

                return (
                  <div
                    key={taskKey}
                    className={`p-1.5 rounded-lg border transition-all ${
                      isActive
                        ? 'bg-slate-900/90 border-slate-600 shadow-sm'
                        : 'bg-slate-950/40 border-slate-800/50 hover:bg-slate-900/50'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <div className="flex items-center gap-1.5">
                        <span style={{ color: conf.color }}>
                          {renderTaskIcon(taskKey, 'w-3 h-3')}
                        </span>
                        <span className={`font-medium ${isActive ? 'text-white font-bold' : 'text-slate-300'}`}>
                          {conf.name}
                        </span>
                        {isActive && (
                          <span className="text-[9px] uppercase px-1 py-0.2 rounded font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                            Active
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] text-slate-400">
                          {Math.round(affinityVal * 100)}%
                        </span>
                        <span className="font-mono text-[10px] px-1 py-0.2 rounded bg-slate-800 text-amber-300 border border-slate-700/60">
                          {xpVal} XP
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-1.5 bg-slate-800/90 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(100, Math.round(affinityVal * 100))}%`,
                          backgroundColor: conf.color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Individual Aptitudes (Force, Vitesse, Creusage, Capacité) */}
        <div>
          <div className="text-[11px] font-semibold text-slate-400 mb-1.5 flex items-center justify-between">
            <span>Aptitudes physiques individuelles :</span>
            <span className="text-[10px] font-mono text-slate-500">
              <Clock className="w-2.5 h-2.5 inline mr-1" />
              Âge: {data.ageFormatted}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            <div className="bg-slate-950/60 border border-slate-800 rounded p-1.5">
              <div className="text-slate-400 text-[10px] flex items-center gap-1">
                <Shield className="w-2.5 h-2.5 text-rose-400" />
                Force physique
              </div>
              <div className="text-sm font-bold text-white font-mono">
                {data.aptitudes.strength} <span className="text-[10px] text-slate-400 font-normal">pts</span>
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800 rounded p-1.5">
              <div className="text-slate-400 text-[10px] flex items-center gap-1">
                <Gauge className="w-2.5 h-2.5 text-cyan-400" />
                Vitesse naturelle
              </div>
              <div className="text-sm font-bold text-white font-mono">
                {Math.round(data.aptitudes.speed * 1000)} <span className="text-[10px] text-slate-400 font-normal">px/t</span>
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800 rounded p-1.5">
              <div className="text-slate-400 text-[10px] flex items-center gap-1">
                <Pickaxe className="w-2.5 h-2.5 text-amber-400" />
                Aptitude creusage
              </div>
              <div className="text-sm font-bold text-amber-300 font-mono">
                {data.aptitudes.digProficiency}x
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800 rounded p-1.5">
              <div className="text-slate-400 text-[10px] flex items-center gap-1">
                <Zap className="w-2.5 h-2.5 text-emerald-400" />
                Capacité portage
              </div>
              <div className="text-sm font-bold text-emerald-300 font-mono">
                {data.aptitudes.carryCapacity} <span className="text-[10px] text-slate-400 font-normal">unités</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Action History */}
        <div className="border border-slate-800 rounded-lg overflow-hidden">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="w-full flex items-center justify-between px-2.5 py-1.5 bg-slate-950/60 hover:bg-slate-950 text-slate-300 font-medium text-[11px] transition-colors cursor-pointer"
          >
            <span className="flex items-center gap-1.5">
              <History className="w-3 h-3 text-cyan-400" />
              Historique récent des actions ({data.recentActions.length})
            </span>
            {showHistory ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showHistory && (
            <div className="p-2 space-y-1.5 bg-slate-950/90 max-h-36 overflow-y-auto">
              {data.recentActions.length === 0 ? (
                <div className="text-slate-500 text-[10px] italic">Aucune action enregistrée</div>
              ) : (
                data.recentActions.map((rec, idx) => (
                  <div key={idx} className="text-[10px] border-b border-slate-800/40 pb-1 last:border-none last:pb-0">
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="font-mono text-cyan-400/90">t+{rec.tick}</span>
                      {rec.location && (
                        <span className="font-mono text-slate-500">
                          ({rec.location.x}, {rec.location.y})
                        </span>
                      )}
                    </div>
                    <div className="text-slate-200 mt-0.5">{rec.action}</div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Camera Center Button */}
      <div className="pt-2 border-t border-slate-800">
        <button
          onClick={() => onFollowAnt(ant)}
          className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors cursor-pointer shadow-sm"
        >
          <Compass className="w-3.5 h-3.5 text-cyan-400" />
          Centrer la caméra sur cette fourmi
        </button>
      </div>
    </div>
  );
};
