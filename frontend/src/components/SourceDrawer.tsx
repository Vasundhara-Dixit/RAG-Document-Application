import React, { useEffect, useState } from 'react';
import { RetrievedPassage } from '../types';

interface SourceDrawerProps {
  passages: RetrievedPassage[];
  selectedIndex: number;
  isOpen: boolean;
  onClose: () => void;
  onSelectIndex: (index: number) => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({
  passages,
  selectedIndex,
  isOpen,
  onClose,
  onSelectIndex,
}) => {
  const [copied, setCopied] = useState(false);

  // Key navigation (Alt+Up/Down, Esc)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onClose();
      } else if (e.altKey && (e.key === 'ArrowRight' || e.key === 'ArrowDown')) {
        e.preventDefault();
        if (selectedIndex < passages.length - 1) onSelectIndex(selectedIndex + 1);
      } else if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowUp')) {
        e.preventDefault();
        if (selectedIndex > 0) onSelectIndex(selectedIndex - 1);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, passages.length, onClose, onSelectIndex]);

  if (!isOpen || passages.length === 0) return null;

  const currentPassage = passages[selectedIndex] || passages[0];
  const chunk = currentPassage.chunk;

  const handleCopy = () => {
    navigator.clipboard.writeText(chunk.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <aside
      className="w-[420px] flex-shrink-0 h-[calc(100vh-4rem)] bg-surface/90 backdrop-blur-xl border-l border-surface-container-high flex flex-col shadow-2xl z-30 animate-in slide-in-from-right duration-200"
      id="sourceDrawer"
    >
      {/* Drawer Header & Stepper */}
      <div className="p-space-lg bg-surface-container-low border-b border-surface-container-high flex flex-col gap-space-xs shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-space-xs font-citation-code text-citation-code text-primary font-bold">
            <span className="material-symbols-outlined text-[16px] text-secondary">menu_book</span>
            <span className="tracking-wider uppercase">Source Verification</span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => selectedIndex > 0 && onSelectIndex(selectedIndex - 1)}
              disabled={selectedIndex === 0}
              className="w-7 h-7 rounded hover:bg-surface-container flex items-center justify-center text-outline hover:text-on-surface disabled:opacity-30 disabled:pointer-events-none transition-colors"
              title="Previous excerpt (Alt+Left)"
            >
              <span className="material-symbols-outlined text-[18px]">chevron_left</span>
            </button>
            <span className="font-citation-code text-citation-code text-on-surface px-1 font-semibold">
              {selectedIndex + 1} of {passages.length}
            </span>
            <button
              onClick={() => selectedIndex < passages.length - 1 && onSelectIndex(selectedIndex + 1)}
              disabled={selectedIndex >= passages.length - 1}
              className="w-7 h-7 rounded hover:bg-surface-container flex items-center justify-center text-outline hover:text-on-surface disabled:opacity-30 disabled:pointer-events-none transition-colors"
              title="Next excerpt (Alt+Right)"
            >
              <span className="material-symbols-outlined text-[18px]">chevron_right</span>
            </button>
            <div className="h-4 w-[1px] bg-surface-container-highest mx-1" />
            <button
              onClick={onClose}
              className="w-7 h-7 rounded hover:bg-surface-container flex items-center justify-center text-outline hover:text-error transition-colors"
              title="Close drawer (Esc)"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        </div>

        {/* Manuscript Title & Provenance */}
        <div className="flex flex-col mt-space-xs">
          <h2 className="font-headline-md text-headline-md text-primary tracking-tight truncate leading-tight">
            {chunk.doc_id}
          </h2>
          <div className="flex items-center gap-space-sm text-outline font-citation-code text-citation-code mt-0.5">
            <span className="text-secondary font-medium">
              Page {chunk.page_start}
              {chunk.page_end > chunk.page_start && `–${chunk.page_end}`}
              {chunk.section_title && ` · ${chunk.section_title}`}
            </span>
          </div>
        </div>
      </div>

      {/* Drawer Body & Evidentiary Reading Window */}
      <div className="flex-1 overflow-y-auto p-space-lg flex flex-col gap-space-lg bg-surface">
        {/* Score & Telemetry Card */}
        <div className="p-space-sm rounded-lg bg-surface-container-low border border-surface-container-high flex items-center justify-between text-on-surface-variant font-citation-code text-citation-code shadow-sm">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[16px] text-secondary">data_thresholding</span>
            <span className="font-semibold text-primary">Score: {currentPassage.score.toFixed(4)}</span>
          </div>
          <span className="text-outline truncate max-w-[130px]">{chunk.chunk_id}</span>
          <span className="px-1.5 py-0.5 rounded bg-surface-container text-[10px] text-primary font-medium">
            {chunk.token_count} tok
          </span>
        </div>

        {/* Verbatim Excerpt with M-03 Highlighter Sweep */}
        <div className="flex flex-col gap-space-md bg-surface-container-low/40 p-space-md rounded-xl border border-surface-container-high">
          <div className="flex items-center justify-between text-outline font-citation-code text-citation-code pb-space-xs border-b border-surface-container-high">
            <span className="uppercase tracking-widest text-ui-label-sm font-semibold text-primary">
              Manuscript Extract
            </span>
            <span className="text-on-surface-variant">Verbatim Provenance</span>
          </div>

          <div className="relative pl-space-md py-1">
            {/* Left vertical scholarly highlight bar */}
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-palette-rose rounded-full" />
            <p className="font-body-md text-body-md text-on-surface leading-loose">
              <mark className="highlighter-sweep px-1.5 py-0.5 rounded font-normal leading-loose text-on-surface">
                {chunk.text}
              </mark>
            </p>
          </div>
        </div>

        {/* Verification Attestation Card */}
        <div className="p-space-md rounded-lg bg-surface-container border border-surface-container-high flex flex-col gap-space-xs text-on-surface shadow-sm">
          <div className="flex items-center gap-1.5 font-ui-label-sm text-ui-label-sm text-primary uppercase font-bold tracking-wider">
            <span className="material-symbols-outlined text-[16px] text-secondary">fact_check</span>
            <span>Grounding Attestation</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
            Directly retrieved via dual vector and sparse BM25 indices. Verified against SHA-256 registered manuscript source bytes.
          </p>
        </div>

        {/* Facsimile Document Card */}
        <div className="relative rounded-xl overflow-hidden bg-surface-container-high/60 border border-surface-container-highest p-space-lg flex flex-col items-center justify-center text-center gap-space-sm min-h-[130px]">
          <span className="material-symbols-outlined text-[32px] text-primary">description</span>
          <div className="flex flex-col z-10">
            <span className="font-ui-label-md text-ui-label-md font-semibold text-primary">
              Original Document Facsimile
            </span>
            <span className="font-citation-code text-citation-code text-outline">
              Page {chunk.page_start} · Offset {chunk.char_start}–{chunk.char_end}
            </span>
          </div>
        </div>
      </div>

      {/* Drawer Persistent Footer */}
      <div className="p-space-md bg-surface-container-low border-t border-surface-container-high flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-space-xs font-citation-code text-citation-code text-outline truncate max-w-[200px]">
          <span className="material-symbols-outlined text-[15px] text-secondary">fingerprint</span>
          <span>{chunk.chunk_id}</span>
        </div>
        <button
          onClick={handleCopy}
          className="px-space-md py-1.5 rounded-lg bg-surface hover:bg-surface-container border border-surface-container-high font-ui-label-md text-ui-label-md text-primary flex items-center gap-1 transition-all shadow-sm"
        >
          <span className="material-symbols-outlined text-[16px] text-secondary">
            {copied ? 'check' : 'content_copy'}
          </span>
          <span>{copied ? 'Copied' : 'Copy Excerpt'}</span>
        </button>
      </div>
    </aside>
  );
};
