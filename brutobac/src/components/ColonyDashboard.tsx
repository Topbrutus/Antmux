import React from 'react';
import { ColonyStats, ColonyRoom, QueenTerminalState } from '../types/colony';
import { Gem, Mountain, Layers, ShieldCheck, Heart, Sparkles } from 'lucide-react';

interface ColonyDashboardProps {
  stats: ColonyStats;
  rooms?: ColonyRoom[];
  storageCapacity?: number;
  queenTerminal: QueenTerminalState;
  sharedWorld: {
    connected: boolean;
    crystalsProduced: number;
    observationsProcessed: number;
    latestCrystalCount: number;
  };
}

export const ColonyDashboard: React.FC<ColonyDashboardProps> = ({
  stats,
  rooms = [],
  storageCapacity: propStorageCapacity,
  queenTerminal,
  sharedWorld,
}) => {
  // Réserve de poussière de cristal stockée physiquement dans le terrier
  const dustAmount = stats.crystalDust ?? 0;

  // Chambres de stockage dans le terrier (STORAGE et/ou CRYSTAL_VAULT)
  const storageRooms = rooms.filter(
    (r) => r.type === 'STORAGE' || r.type === 'CRYSTAL_VAULT'
  );

  // Capacité totale des chambres de stockage
  const totalStorageCapacity =
    propStorageCapacity ??
    (storageRooms.length > 0
      ? storageRooms.reduce((sum, r) => sum + (r.capacity || 0), 0)
      : (rooms.length > 0
          ? rooms.reduce((sum, r) => sum + (r.capacity || 0), 0)
          : 100));

  const fillPercentage = Math.min(
    100,
    Math.round((dustAmount / Math.max(1, totalStorageCapacity)) * 100)
  );

  const isNearCapacity = fillPercentage >= 90;
  const isHalfFull = fillPercentage >= 50;

  return (
    <div className="bg-slate-900/95 border-b border-slate-800 px-6 py-2.5 text-xs text-slate-300">
      <div className="flex flex-wrap items-center justify-between gap-y-2 gap-x-6 max-w-7xl mx-auto">
        <div className="w-full flex items-center gap-2 text-[10px] text-slate-400">
          <span className={sharedWorld.connected ? 'text-emerald-300' : 'text-rose-300'}>
            {sharedWorld.connected ? 'Univers partagé connecté' : 'Univers partagé hors ligne'}
          </span>
          <span>·</span>
          <span>{sharedWorld.crystalsProduced} cristaux produits</span>
          <span>·</span>
          <span>{sharedWorld.observationsProcessed} observations</span>
          {sharedWorld.latestCrystalCount > 0 && <span>· {sharedWorld.latestCrystalCount} récents</span>}
        </div>
        <div className="w-full flex items-center gap-3 rounded-md border border-cyan-500/20 bg-slate-950/50 px-2.5 py-1.5">
          <span className="font-semibold text-cyan-300">Terminal royal</span>
          <span className={queenTerminal.connected ? 'text-emerald-300' : 'text-rose-300'}>
            {queenTerminal.connected ? 'connecté à 8788' : 'hors ligne'}
          </span>
          <span className="text-slate-500">·</span>
          <span className="text-slate-300">
            {queenTerminal.active.length}/{queenTerminal.activeLimit} calculs actifs
          </span>
          {queenTerminal.queued.length > 0 && (
            <span className="text-amber-300">{queenTerminal.queued.length} en attente</span>
          )}
          <div className="ml-auto flex flex-wrap justify-end gap-1.5 text-[10px]">
            {queenTerminal.active.map((item) => (
              <span key={`on-${item.formulaId}`} className="rounded border border-emerald-500/30 bg-emerald-500/10 px-1.5 py-0.5 text-emerald-200">
                <strong>ON</strong> {item.name}
              </span>
            ))}
            {queenTerminal.queued.map((item) => (
              <span key={`off-${item.formulaId}`} className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-400">
                <strong>OFF</strong> {item.name}
              </span>
            ))}
            {!queenTerminal.active.length && !queenTerminal.queued.length && (
              <span className="text-slate-500">Aucune priorité reçue</span>
            )}
          </div>
        </div>
        {/* Left: Unboxed Resources & Physical Dust Storage Gauge */}
        <div className="flex items-center flex-wrap gap-x-4 gap-y-1.5">
          <div className="flex items-center gap-1.5 text-cyan-300">
            <Gem className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-semibold">Cristaux</span>
            <span className="font-mono tabular-nums text-white font-bold">{stats.crystals}</span>
          </div>

          <span className="text-slate-600 hidden sm:inline" aria-hidden="true">·</span>

          {/* Jauge Réserve de Poussière de Cristal vs Capacité de Stockage */}
          <div
            className="flex items-center gap-2 px-2.5 py-0.5 rounded-md bg-slate-800/60 border border-sky-500/25 shadow-xs transition-colors hover:border-sky-400/40"
            title={`Réserve de poussière de cristal stockée : ${dustAmount} / ${totalStorageCapacity} unités (${fillPercentage}% de la capacité totale des chambres de stockage)`}
          >
            <div className="flex items-center gap-1.5 text-sky-300">
              <Sparkles className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <span className="font-semibold text-slate-200">Poussière</span>
              <span className="font-mono tabular-nums text-white font-bold">
                {dustAmount}
              </span>
              <span className="text-slate-500 font-mono text-[11px]">/</span>
              <span className="font-mono tabular-nums text-sky-400/90 font-medium text-[11px]">
                {totalStorageCapacity}
              </span>
            </div>

            {/* Jauge visuelle de remplissage */}
            <div className="flex items-center gap-1.5 pl-1.5 border-l border-slate-700">
              <div
                className="w-16 sm:w-20 md:w-24 h-2 bg-slate-950 rounded-full overflow-hidden p-[1px] border border-slate-700/80"
                role="progressbar"
                aria-valuenow={dustAmount}
                aria-valuemin={0}
                aria-valuemax={totalStorageCapacity}
                aria-label="Réserve de poussière de cristal stockée"
              >
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    isNearCapacity
                      ? 'bg-gradient-to-r from-amber-500 to-rose-400 shadow-[0_0_8px_rgba(245,158,11,0.6)]'
                      : isHalfFull
                      ? 'bg-gradient-to-r from-sky-500 to-cyan-300 shadow-[0_0_6px_rgba(56,189,248,0.5)]'
                      : 'bg-gradient-to-r from-sky-600 to-sky-400 shadow-[0_0_4px_rgba(56,189,248,0.3)]'
                  }`}
                  style={{ width: `${Math.min(100, Math.max(0, fillPercentage))}%` }}
                />
              </div>
              <span
                className={`font-mono text-[10px] font-semibold tabular-nums min-w-[26px] ${
                  isNearCapacity ? 'text-amber-300' : 'text-sky-300'
                }`}
              >
                {fillPercentage}%
              </span>
            </div>
          </div>

          <span className="text-slate-600 hidden sm:inline" aria-hidden="true">·</span>

          <div className="flex items-center gap-1.5 text-amber-200">
            <Mountain className="w-3.5 h-3.5 text-amber-500" />
            <span className="font-semibold">Matière Brute</span>
            <span className="font-mono tabular-nums text-white font-bold">{stats.dirt}</span>
          </div>

          <span className="text-slate-600 hidden sm:inline" aria-hidden="true">·</span>

          <div className="flex items-center gap-1.5 text-slate-300">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold">Fragments</span>
            <span className="font-mono tabular-nums text-white font-bold">{stats.minerals}</span>
          </div>

          <span className="text-slate-600 hidden sm:inline" aria-hidden="true">·</span>

          <div className="flex items-center gap-1.5 text-emerald-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold">Bio-Résine</span>
            <span className="font-mono tabular-nums text-white font-bold">{stats.resin}</span>
          </div>
        </div>

        {/* Right: Colony Vital Metrics */}
        <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-slate-400">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Résonance</span>
            <span className="font-mono tabular-nums text-purple-300 font-semibold">
              {Math.floor(stats.resonantEnergy)}
            </span>
          </div>

          <span className="text-slate-600 hidden sm:inline" aria-hidden="true">·</span>

          <div className="flex items-center gap-1.5">
            <span>Population</span>
            <span className="font-mono tabular-nums text-slate-200 font-semibold">
              {stats.population} fourmis
            </span>
          </div>

          <span className="text-slate-600 hidden sm:inline" aria-hidden="true">·</span>

          <div className="flex items-center gap-1.5">
            <Heart className="w-3.5 h-3.5 text-rose-400" />
            <span>Reine</span>
            <span className="font-mono tabular-nums text-rose-300 font-semibold">
              {stats.queenHealth}%
            </span>
          </div>

          <span className="text-slate-600 hidden sm:inline" aria-hidden="true">·</span>

          <div className="flex items-center gap-1.5">
            <span>Profondeur</span>
            <span className="font-mono tabular-nums text-amber-400 font-semibold">
              -{stats.deepestDugMeters}m
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
