import React from 'react';
import { ChatSession } from '../types';

interface NavRailProps {
  activeTab: 'chat' | 'library' | 'eval';
  onTabChange: (tab: 'chat' | 'library' | 'eval') => void;
  documentCount: number;
  chunkCount: number;
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onOpenSettings: () => void;
  isGlassEnabled?: boolean;
  archivistName?: string;
}

export const NavRail: React.FC<NavRailProps> = ({
  activeTab,
  onTabChange,
  documentCount,
  chunkCount,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onOpenSettings,
  isGlassEnabled = false,
  archivistName = 'Archivist Desk',
}) => {
  return (
    <aside
      className={`fixed left-0 top-0 h-full w-[232px] z-50 flex flex-col justify-between select-none transition-all duration-300 ${
        isGlassEnabled
          ? 'bg-sidebar/85 backdrop-blur-2xl border-r border-white/10 shadow-[0_4px_30px_rgba(76,29,61,0.4)]'
          : 'bg-sidebar border-r border-sidebar-border shadow-[0_4px_24px_rgba(76,29,61,0.25)]'
      }`}
    >
      {/* Top Header & Navigation Links */}
      <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
        {/* Emblem & Branding */}
        <div
          className={`p-space-lg flex items-start gap-space-sm border-b flex-shrink-0 transition-all ${
            isGlassEnabled
              ? 'bg-sidebar-surface/70 border-white/10'
              : 'bg-sidebar-surface border-sidebar-border'
          }`}
        >
          <div className="w-8 h-8 rounded bg-palette-plum flex items-center justify-center flex-shrink-0 text-palette-peach shadow-sm">
            <span className="material-symbols-outlined text-[20px]">local_library</span>
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-headline-md text-headline-md text-palette-peach tracking-tight truncate leading-tight font-normal">
              The Reading Room
            </span>
            <span className="font-ui-label-sm text-ui-label-sm text-palette-coral uppercase tracking-wider font-semibold">
              Archival Q&amp;A
            </span>
          </div>
        </div>

        {/* New Inquiry Action Button */}
        <div className="p-space-md pb-0 flex-shrink-0">
          <button
            onClick={() => {
              onNewSession();
              onTabChange('chat');
            }}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-palette-plum hover:bg-palette-wine text-palette-peach font-ui-label-md text-ui-label-md font-semibold transition-all shadow-md group border border-palette-rose/30 cursor-pointer"
            title="Start a new synthesis inquiry"
          >
            <span className="material-symbols-outlined text-[18px] group-hover:rotate-90 transition-transform">add</span>
            <span>New Inquiry</span>
          </button>
        </div>

        {/* Section Header */}
        <div className="px-space-md py-space-xs mt-space-sm flex-shrink-0">
          <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-widest text-sidebar-muted px-space-sm">
            Corpus Index
          </span>
        </div>

        {/* Primary Views Navigation */}
        <nav className="flex flex-col gap-space-xs px-space-md flex-shrink-0">
          <button
            onClick={() => onTabChange('chat')}
            className={`flex items-center justify-between px-space-md py-space-sm rounded-lg font-ui-label-lg text-ui-label-lg transition-all ${
              activeTab === 'chat'
                ? 'bg-palette-wine text-white shadow-md font-semibold'
                : 'text-sidebar-muted hover:bg-sidebar-surface hover:text-palette-peach'
            }`}
          >
            <div className="flex items-center gap-space-sm">
              <span className={`material-symbols-outlined text-[18px] ${activeTab === 'chat' ? 'text-palette-peach' : ''}`}>
                forum
              </span>
              <span>Workspace</span>
            </div>
            <span
              className={`h-2 w-2 rounded-full ${
                activeTab === 'chat' ? 'bg-palette-coral shadow-[0_0_8px_#FB9590]' : 'bg-transparent'
              }`}
            />
          </button>

          <button
            onClick={() => onTabChange('library')}
            className={`flex items-center justify-between px-space-md py-space-sm rounded-lg font-ui-label-lg text-ui-label-lg transition-all ${
              activeTab === 'library'
                ? 'bg-palette-wine text-white shadow-md font-semibold'
                : 'text-sidebar-muted hover:bg-sidebar-surface hover:text-palette-peach'
            }`}
          >
            <div className="flex items-center gap-space-sm">
              <span className={`material-symbols-outlined text-[18px] ${activeTab === 'library' ? 'text-palette-peach' : ''}`}>
                auto_stories
              </span>
              <span>Library</span>
            </div>
            <span className="font-citation-code text-citation-code px-1.5 py-0.5 rounded bg-sidebar-surface text-palette-peach">
              {documentCount} docs
            </span>
          </button>

          <button
            onClick={() => onTabChange('eval')}
            className={`flex items-center justify-between px-space-md py-space-sm rounded-lg font-ui-label-lg text-ui-label-lg transition-all ${
              activeTab === 'eval'
                ? 'bg-palette-wine text-white shadow-md font-semibold'
                : 'text-sidebar-muted hover:bg-sidebar-surface hover:text-palette-peach'
            }`}
          >
            <div className="flex items-center gap-space-sm">
              <span className={`material-symbols-outlined text-[18px] ${activeTab === 'eval' ? 'text-palette-peach' : ''}`}>
                analytics
              </span>
              <span>Eval Lab</span>
            </div>
            <span className="font-citation-code text-citation-code px-1.5 py-0.5 rounded bg-sidebar-surface text-palette-coral font-medium">
              Runs
            </span>
          </button>
        </nav>

        {/* Chat History Section */}
        <div
          className={`flex-1 flex flex-col min-h-0 mt-space-md border-t px-space-md pt-space-xs transition-all ${
            isGlassEnabled ? 'border-white/10' : 'border-sidebar-border'
          }`}
        >
          <div className="flex items-center justify-between py-1 px-1">
            <span className="font-ui-label-sm text-[11px] uppercase tracking-wider text-sidebar-muted font-semibold flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">history</span>
              <span>Past Inquiries ({sessions.length})</span>
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-sidebar-scrollbar mt-1">
            {sessions.length === 0 ? (
              <div className="p-3 text-center text-sidebar-muted/70 font-body-sm text-[12px] italic">
                Inquiries are archived here automatically.
              </div>
            ) : (
              sessions.map((ses) => {
                const isActive = activeSessionId === ses.id && activeTab === 'chat';
                return (
                  <div
                    key={ses.id}
                    onClick={() => {
                      onSelectSession(ses.id);
                      onTabChange('chat');
                    }}
                    className={`group flex items-center justify-between px-2.5 py-1.5 rounded-lg cursor-pointer transition-all ${
                      isActive
                        ? 'bg-palette-plum text-palette-peach font-semibold shadow-sm'
                        : 'text-sidebar-muted hover:bg-sidebar-surface hover:text-palette-peach'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className={`material-symbols-outlined text-[15px] shrink-0 ${isActive ? 'text-palette-peach' : 'text-sidebar-muted'}`}>
                        chat_bubble_outline
                      </span>
                      <span className="font-ui-label-md text-[12px] truncate" title={ses.title}>
                        {ses.title}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(ses.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-palette-rose transition-opacity text-sidebar-muted"
                      title="Delete chat session"
                    >
                      <span className="material-symbols-outlined text-[14px]">delete</span>
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Bottom Status & Archivist Desk */}
      <div
        className={`p-space-md flex flex-col gap-space-sm border-t flex-shrink-0 transition-all ${
          isGlassEnabled
            ? 'bg-sidebar-surface/70 border-white/10'
            : 'bg-sidebar-surface border-sidebar-border'
        }`}
      >
        {/* Status Card */}
        <div
          className={`p-space-sm rounded border flex flex-col gap-space-xs transition-all ${
            isGlassEnabled
              ? 'bg-sidebar/80 border-white/10'
              : 'bg-sidebar border-sidebar-border'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="font-ui-label-sm text-ui-label-sm text-sidebar-muted uppercase tracking-wider">
              Engine Status
            </span>
            <span className="flex items-center gap-1.5 font-citation-code text-citation-code text-palette-coral font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-palette-coral animate-pulse" />
              Ready
            </span>
          </div>
          <div className="font-citation-code text-citation-code text-sidebar-muted truncate">
            {documentCount} docs · {chunkCount} chunks
          </div>
        </div>

        {/* Quick Toolbar */}
        <div className="flex items-center justify-between pt-space-xs px-space-xs">
          <div className="flex items-center gap-1 font-citation-code text-citation-code text-sidebar-muted">
            <span className="px-1.5 py-0.5 rounded bg-sidebar text-palette-peach font-mono text-[10px]">?</span>
            <span>Help</span>
          </div>
          <div className="flex items-center gap-1 font-citation-code text-citation-code text-sidebar-muted">
            <span className="px-1.5 py-0.5 rounded bg-sidebar text-palette-peach font-mono text-[10px]">/</span>
            <span>Focus</span>
          </div>
          <button
            onClick={onOpenSettings}
            className="w-6 h-6 rounded-full bg-sidebar hover:bg-sidebar-surface flex items-center justify-center text-palette-coral hover:text-palette-peach transition-colors cursor-pointer"
            title="Appearance & Settings"
          >
            <span className="material-symbols-outlined text-[14px]">tune</span>
          </button>
        </div>

        {/* User Identity / Profile Option (Third Picture in request) */}
        <button
          onClick={onOpenSettings}
          className="flex items-center justify-between pt-space-xs border-t border-sidebar-border/60 hover:bg-sidebar/40 p-1.5 rounded-lg transition-all text-left group cursor-pointer w-full"
          title="Click to open Archivist Settings & Wallpaper"
        >
          <div className="flex items-center gap-space-sm min-w-0">
            <div className="w-7 h-7 rounded-full bg-palette-rose group-hover:bg-palette-plum flex items-center justify-center flex-shrink-0 text-white shadow-sm transition-colors">
              <span className="material-symbols-outlined text-[15px]">person</span>
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-ui-label-sm text-ui-label-sm text-palette-peach truncate font-semibold group-hover:text-white transition-colors">
                {archivistName}
              </span>
              <span className="font-citation-code text-citation-code text-sidebar-muted truncate">
                Corpus Ledger A-1
              </span>
            </div>
          </div>
          <span className="material-symbols-outlined text-[16px] text-sidebar-muted group-hover:text-palette-peach group-hover:rotate-45 transition-all">
            settings
          </span>
        </button>
      </div>
    </aside>
  );
};
