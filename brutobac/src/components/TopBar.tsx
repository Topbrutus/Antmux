import React from 'react';
import { Volume2, VolumeX, Sparkles, BookOpen } from 'lucide-react';
import { soundEngine } from '../audio/soundEngine';

interface TopBarProps {
  onOpenGuide: () => void;
  onOpenRecruitment: () => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  onOpenGuide,
  onOpenRecruitment,
  soundEnabled,
  onToggleSound,
  activeTab,
  onTabChange,
}) => {
  return (
    <header className="flex items-center justify-between gap-8 px-6 py-3.5 bg-slate-900 border-b border-slate-800 text-slate-100 z-20 shrink-0">
      {/* Zone 1: Single text element wordmark */}
      <div className="flex items-center gap-3">
        <span className="text-lg font-extrabold tracking-tight text-white whitespace-nowrap shrink-0 font-['Plus_Jakarta_Sans']">
          BrutoBac
        </span>
        <span className="hidden sm:inline-block text-xs text-slate-400 font-normal">
          Terrier Multi-Étages
        </span>
      </div>

      {/* Zone 2: 4–5 clean single-line navigation links */}
      <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
        <button
          onClick={() => onTabChange('terrier')}
          className={`hover:text-white transition-colors whitespace-nowrap shrink-0 ${
            activeTab === 'terrier' ? 'text-amber-400 font-semibold' : ''
          }`}
        >
          Coupe Souterraine
        </button>
        <button
          onClick={() => onTabChange('colonie')}
          className={`hover:text-white transition-colors whitespace-nowrap shrink-0 ${
            activeTab === 'colonie' ? 'text-amber-400 font-semibold' : ''
          }`}
        >
          Castes & Population
        </button>
        <button
          onClick={() => onTabChange('salles')}
          className={`hover:text-white transition-colors whitespace-nowrap shrink-0 ${
            activeTab === 'salles' ? 'text-amber-400 font-semibold' : ''
          }`}
        >
          Chambres & Étages
        </button>
        <button
          onClick={onOpenGuide}
          className="flex items-center gap-1.5 hover:text-white transition-colors whitespace-nowrap shrink-0 text-slate-400"
        >
          <BookOpen className="w-3.5 h-3.5" />
          Guide Géologique
        </button>
      </nav>

      {/* Zone 3: 1 primary action + sound toggle */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={onToggleSound}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          title={soundEnabled ? 'Désactiver le son' : 'Activer le son'}
          aria-label={soundEnabled ? 'Désactiver le son' : 'Activer le son'}
        >
          {soundEnabled ? (
            <Volume2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <VolumeX className="w-4 h-4 text-slate-500" />
          )}
        </button>

        <button
          onClick={onOpenRecruitment}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-slate-900 bg-amber-400 hover:bg-amber-300 rounded-lg transition-colors whitespace-nowrap shrink-0 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5" />
          Incuber Fourmis
        </button>
      </div>
    </header>
  );
};
