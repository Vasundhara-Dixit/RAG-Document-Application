import React from 'react';

interface HeaderProps {
  activeTab: 'chat' | 'library' | 'eval';
  onTabChange: (tab: 'chat' | 'library' | 'eval') => void;
  retrievalLabel?: string;
  onOpenSettings: () => void;
  isGlassEnabled?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  retrievalLabel = 'Hybrid BM25 + Dense RRF + Cross-Encoder',
  onOpenSettings,
  isGlassEnabled = false,
}) => {
  return (
    <header
      className={`fixed top-0 left-[232px] right-0 h-16 z-40 flex items-center justify-between px-gutter-desktop transition-all duration-300 ${
        isGlassEnabled
          ? 'bg-surface/75 backdrop-blur-xl border-b border-white/20 shadow-sm'
          : 'bg-background/95 backdrop-blur-xl border-b border-surface-container-high shadow-sm'
      }`}
    >
      {/* Left: View title & Breadcrumbs */}
      <div className="flex items-center gap-space-md">
        <div className="flex items-center gap-space-xs">
          <span className="font-headline-md text-headline-md text-primary font-normal tracking-tight">
            The Reading Room
          </span>
          <span className="text-outline/60 mx-1">/</span>
          <span className="font-ui-label-lg text-ui-label-lg text-secondary font-medium">
            {activeTab === 'chat' && 'Synthesis Workspace'}
            {activeTab === 'library' && 'Manuscript Index'}
            {activeTab === 'eval' && 'Evaluation Ledger'}
          </span>
        </div>

        {/* View Switcher Tabs */}
        <nav
          className={`hidden md:flex items-center gap-space-sm ml-space-lg p-1 rounded-lg border transition-all ${
            isGlassEnabled
              ? 'bg-white/40 backdrop-blur-md border-white/30'
              : 'bg-surface-container-low border-surface-container-high'
          }`}
        >
          <button
            onClick={() => onTabChange('chat')}
            className={`px-3 py-1 rounded font-ui-label-md text-ui-label-md transition-all ${
              activeTab === 'chat'
                ? 'bg-surface text-primary shadow-sm font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Workspace
          </button>
          <button
            onClick={() => onTabChange('library')}
            className={`px-3 py-1 rounded font-ui-label-md text-ui-label-md transition-all ${
              activeTab === 'library'
                ? 'bg-surface text-primary shadow-sm font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Manuscripts
          </button>
          <button
            onClick={() => onTabChange('eval')}
            className={`px-3 py-1 rounded font-ui-label-md text-ui-label-md transition-all ${
              activeTab === 'eval'
                ? 'bg-surface text-primary shadow-sm font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Evaluation
          </button>
        </nav>
      </div>

      {/* Right: Engine Telemetry & Profile Button */}
      <div className="flex items-center gap-space-md">
        <div
          className={`hidden sm:flex items-center gap-space-xs font-citation-code text-citation-code text-primary px-space-sm py-1.5 rounded-lg shadow-sm border transition-all ${
            isGlassEnabled
              ? 'bg-white/40 backdrop-blur-md border-white/30'
              : 'bg-surface-container-low border-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined text-[16px] text-secondary">verified</span>
          <span className="font-semibold">Engine:</span>
          <span className="text-on-surface-variant">{retrievalLabel}</span>
        </div>

        {/* Palette pill */}
        <div
          className={`hidden lg:flex items-center gap-1.5 px-2 py-1 rounded-full border text-[11px] font-citation-code text-on-surface-variant transition-all ${
            isGlassEnabled
              ? 'bg-white/40 backdrop-blur-md border-white/30'
              : 'bg-surface-container border-surface-container-high'
          }`}
        >
          <div className="flex -space-x-1">
            <span className="w-2.5 h-2.5 rounded-full bg-palette-eggplant" />
            <span className="w-2.5 h-2.5 rounded-full bg-palette-wine" />
            <span className="w-2.5 h-2.5 rounded-full bg-palette-rose" />
            <span className="w-2.5 h-2.5 rounded-full bg-palette-peach" />
          </div>
          <span>Archival Sunset</span>
        </div>

        {/* User Avatar Button (Fourth Picture in request) */}
        <button
          onClick={onOpenSettings}
          className="w-8 h-8 rounded-full bg-primary hover:bg-palette-wine flex items-center justify-center text-white shadow-md ring-2 ring-primary/20 hover:ring-palette-rose/40 transition-all cursor-pointer group"
          title="Profile & Settings (Glass Background, Wallpapers)"
        >
          <span className="material-symbols-outlined text-[18px] group-hover:scale-110 transition-transform">
            person
          </span>
        </button>
      </div>
    </header>
  );
};
