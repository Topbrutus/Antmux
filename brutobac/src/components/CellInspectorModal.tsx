import React, { useState } from 'react';
import { TerrainCell } from '../types/terrain';
import { ConcentrationType } from '../types/terrain';
import { X, Gem, Sparkles, Mountain, Layers, ShieldCheck, CheckCircle2, Pickaxe } from 'lucide-react';

interface CellInspectorModalProps {
  cell: TerrainCell | null;
  onClose: () => void;
  onDig?: (x: number, y: number) => void;
}

export const CellInspectorModal: React.FC<CellInspectorModalProps> = ({ cell, onClose, onDig }) => {
  const [selectedZ, setSelectedZ] = useState<number>(2); // Center slice (Z=2) by default
  const [hoveredMicro, setHoveredMicro] = useState<{
    subX: number;
    subY: number;
    subZ: number;
    dust: number;
    crystal: number;
    mineral: number;
    dirt: number;
    resin: number;
    excavated: boolean;
  } | null>(null);

  if (!cell) return null;

  const concentrationLabels: Record<ConcentrationType, { name: string; color: string; bg: string; border: string }> = {
    rare_geode: {
      name: '💎 Géode Abyssale Rare',
      color: 'text-purple-300',
      bg: 'bg-purple-950/80',
      border: 'border-purple-600/50',
    },
    rich_zone: {
      name: '🌌 Zone Très Riche',
      color: 'text-sky-300',
      bg: 'bg-sky-950/80',
      border: 'border-sky-500/50',
    },
    vein: {
      name: '⚡ Filon / Veine Cristalline',
      color: 'text-cyan-300',
      bg: 'bg-cyan-950/80',
      border: 'border-cyan-500/50',
    },
    cluster: {
      name: '🔮 Amas Géologique',
      color: 'text-indigo-300',
      bg: 'bg-indigo-950/80',
      border: 'border-indigo-500/50',
    },
    small_pocket: {
      name: '🔹 Petite Poche',
      color: 'text-emerald-300',
      bg: 'bg-emerald-950/80',
      border: 'border-emerald-500/50',
    },
    isolated_crystal: {
      name: '💠 Cristal Isolé',
      color: 'text-blue-300',
      bg: 'bg-blue-950/80',
      border: 'border-blue-500/50',
    },
    diffuse: {
      name: '🪨 Matrice Minérale Diffuse',
      color: 'text-slate-300',
      bg: 'bg-slate-900/80',
      border: 'border-slate-700',
    },
  };

  const conc = cell.concentration_type ? concentrationLabels[cell.concentration_type] : concentrationLabels.diffuse;

  // Filter 5x5 micro-cells for the selected Z depth slice
  const zSlice = cell.micro_cells
    ? cell.micro_cells.filter((m) => m.subZ === selectedZ)
    : [];

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-slate-900/98 border-l border-slate-800 shadow-2xl z-40 flex flex-col backdrop-blur-md">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Analyseur Géologique & Micro-Cellules
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {/* Cell Coordinates & Depth */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/80 border border-slate-800">
          <div>
            <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Coordonnées</div>
            <div className="font-mono text-sm font-bold text-white">
              X: {cell.x} · Y: {cell.y}
            </div>
          </div>
          <div className="text-right">
            <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Profondeur</div>
            <div className="font-mono text-sm font-bold text-amber-400">
              -{cell.depth}m
            </div>
          </div>
        </div>

        {/* Formation & Concentration Type */}
        <div className={`p-3 rounded-lg border ${conc.border} ${conc.bg}`}>
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-1">
            Formation Géologique Naturelle
          </div>
          <div className={`text-sm font-bold ${conc.color}`}>
            {conc.name}
          </div>
          <div className="text-[11px] text-slate-300 mt-1">
            Matériau : <span className="font-mono text-white">{cell.material_type}</span> · Dureté :{' '}
            <span className="font-mono text-white">{cell.hardness.toFixed(2)}</span>
          </div>
        </div>

        {/* State: Solid vs Excavated */}
        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-1.5">
            État de la Matière
          </div>
          {cell.excavated ? (
            <div className="flex items-center gap-2 text-emerald-400 font-medium">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>EXCAVÉE — Matière libérée dans la cavité</span>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-300 font-medium">
                <div className="w-2 h-2 rounded-full bg-amber-400" />
                <span>SOLIDE — Contenu caché dans la roche</span>
              </div>
              {onDig && (
                <button
                  onClick={() => onDig(cell.x, cell.y)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 font-semibold"
                >
                  <Pickaxe className="w-3 h-3" />
                  Creuser
                </button>
              )}
            </div>
          )}
        </div>

        {/* Cell Stored Matter Inventory */}
        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
            Inventaire de Matière Pré-Distribuée (Total Cellule)
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-cyan-300">
                <Gem className="w-3.5 h-3.5 text-cyan-400" />
                <span>Cristaux purs</span>
              </div>
              <span className="font-mono font-bold text-white text-sm">
                {cell.crystal_amount}
              </span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-sky-300">
                <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                <span>Poussière</span>
              </div>
              <span className="font-mono font-bold text-white text-sm">
                {cell.crystal_dust_amount}
              </span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-slate-300">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                <span>Fragments</span>
              </div>
              <span className="font-mono font-bold text-white text-sm">
                {cell.mineral_amount}
              </span>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-amber-300">
                <Mountain className="w-3.5 h-3.5 text-amber-500" />
                <span>Terre brute</span>
              </div>
              <span className="font-mono font-bold text-white text-sm">
                {cell.dirt_amount}
              </span>
            </div>
          </div>

          {cell.resin_amount > 0 && (
            <div className="flex items-center justify-between p-2 rounded bg-emerald-950/40 border border-emerald-800/50">
              <div className="flex items-center gap-1.5 text-emerald-300">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Bio-Résine organique</span>
              </div>
              <span className="font-mono font-bold text-emerald-200 text-sm">
                {cell.resin_amount}
              </span>
            </div>
          )}
        </div>

        {/* 5 × 5 × 5 Micro-Cells Matrix Visualizer */}
        <div className="p-3 rounded-lg bg-slate-950/90 border border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Structure 5 × 5 × 5 (125 micro-cellules)
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[10px] text-slate-400">Coupe Z:</span>
              {[0, 1, 2, 3, 4].map((z) => (
                <button
                  key={z}
                  onClick={() => setSelectedZ(z)}
                  className={`w-5 h-5 rounded text-[10px] font-mono font-bold transition-colors ${
                    selectedZ === z
                      ? 'bg-cyan-500 text-slate-950 shadow-sm'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {z}
                </button>
              ))}
            </div>
          </div>

          {/* 5x5 subgrid of current Z-slice */}
          <div className="grid grid-cols-5 gap-1.5 p-2 rounded-lg bg-slate-900/90 border border-slate-800 max-w-[240px] mx-auto">
            {zSlice.map((m) => {
              const hasCrystal = m.crystal_amount > 0;
              const hasDust = m.crystal_dust_amount > 0;
              const hasMineral = m.mineral_amount > 0;
              const hasResin = m.resin_amount > 0;

              let bg = 'bg-slate-800/80';
              let border = 'border-slate-700/50';
              if (hasCrystal) {
                bg = 'bg-cyan-500';
                border = 'border-cyan-300 shadow-sm shadow-cyan-500/50';
              } else if (hasDust) {
                bg = 'bg-sky-400/80';
                border = 'border-sky-300 shadow-sm shadow-sky-400/40';
              } else if (hasMineral) {
                bg = 'bg-slate-400';
                border = 'border-slate-300';
              } else if (hasResin) {
                bg = 'bg-emerald-500';
                border = 'border-emerald-300';
              }

              return (
                <div
                  key={m.index}
                  onMouseEnter={() =>
                    setHoveredMicro({
                      subX: m.subX,
                      subY: m.subY,
                      subZ: m.subZ,
                      dust: m.crystal_dust_amount,
                      crystal: m.crystal_amount,
                      mineral: m.mineral_amount,
                      dirt: m.dirt_amount,
                      resin: m.resin_amount,
                      excavated: m.excavated,
                    })
                  }
                  className={`aspect-square rounded flex items-center justify-center border cursor-pointer transition-transform hover:scale-110 ${bg} ${border}`}
                  title={`Micro-cell (${m.subX},${m.subY},${m.subZ})`}
                >
                  {hasCrystal && <Gem className="w-2.5 h-2.5 text-slate-950" />}
                  {!hasCrystal && hasDust && (
                    <span className="text-[9px] font-bold text-slate-950">
                      {m.crystal_dust_amount}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Micro-cell hover inspection */}
          <div className="p-2 rounded bg-slate-900 border border-slate-800/80 text-[11px] min-h-[38px] flex items-center justify-between">
            {hoveredMicro ? (
              <div className="w-full flex items-center justify-between text-slate-300">
                <span className="font-mono text-cyan-300">
                  Micro ({hoveredMicro.subX}, {hoveredMicro.subY}, {hoveredMicro.subZ})
                </span>
                <span className="font-mono text-white">
                  {hoveredMicro.crystal > 0 && `💎 ${hoveredMicro.crystal} `}
                  {hoveredMicro.dust > 0 && `✨ ${hoveredMicro.dust}p `}
                  {hoveredMicro.mineral > 0 && `🪨 ${hoveredMicro.mineral}m `}
                  {hoveredMicro.dirt > 0 && `⛰️ ${hoveredMicro.dirt}t `}
                  {hoveredMicro.resin > 0 && `💧 ${hoveredMicro.resin}r`}
                  {hoveredMicro.crystal === 0 &&
                    hoveredMicro.dust === 0 &&
                    hoveredMicro.mineral === 0 &&
                    hoveredMicro.dirt === 0 &&
                    hoveredMicro.resin === 0 &&
                    'Matrice stérile'}
                </span>
              </div>
            ) : (
              <span className="text-slate-500 italic">
                Survolez une micro-cellule pour examiner son contenu
              </span>
            )}
          </div>
        </div>

        {/* Strict Conservation Validation */}
        <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-[11px] text-emerald-300 flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Conservation Absolue de Matière</div>
            <div className="text-slate-400 text-[10px] mt-0.5">
              La matière est pré-attribuée par le générateur déterministe. Le creusage ne crée
              rien ex nihilo : il libère physiquement les ressources dans la cavité.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
