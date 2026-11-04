import React from 'react';
import { Citation } from '../types';

interface CitationChipProps {
  citation: Citation;
  active?: boolean;
  onClick: () => void;
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, active, onClick }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded transition-all align-baseline font-citation-code text-citation-code cursor-pointer select-none shadow-sm ${
        active
          ? 'bg-palette-rose text-white ring-2 ring-palette-rose/40 font-semibold'
          : 'bg-palette-peach/35 hover:bg-palette-peach/60 text-primary border border-palette-coral/40 font-medium'
      }`}
      title={`Verify citation in ${citation.filename} (Page ${citation.page})`}
    >
      <span className="font-bold">[{citation.citation_index}]</span>
      <span className="underline decoration-dotted underline-offset-2 truncate max-w-[140px]">
        {citation.filename} · p.{citation.page}
      </span>
    </button>
  );
};
