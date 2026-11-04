import React, { useEffect, useState } from 'react';
import { getDocumentDownloadUrl, previewDocument } from '../api';

interface DocumentPreviewModalProps {
  docId: string | null;
  onClose: () => void;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  docId,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<{
    doc_id: string;
    filename: string;
    pages: number;
    mime: string;
    checksum: string;
    uploaded_at: string;
    status: string;
    chunks_count: number;
    preview_text: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!docId) {
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);
    previewDocument(docId)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load preview');
        setLoading(false);
      });
  }, [docId]);

  if (!docId) return null;

  const handleCopy = () => {
    if (data?.preview_text) {
      navigator.clipboard.writeText(data.preview_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getFormatBadge = (filename: string) => {
    const ext = filename.split('.').pop()?.toUpperCase() || 'TXT';
    const colorMap: Record<string, string> = {
      PDF: 'bg-red-500/15 text-red-700 border-red-500/30',
      DOCX: 'bg-blue-500/15 text-blue-700 border-blue-500/30',
      MD: 'bg-purple-500/15 text-purple-700 border-purple-500/30',
      TXT: 'bg-amber-500/15 text-amber-700 border-amber-500/30',
    };
    return colorMap[ext] || 'bg-palette-peach/30 text-palette-plum border-palette-coral/30';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-palette-eggplant/50 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-4xl max-h-[85vh] bg-surface-container-lowest border border-surface-container-high rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-space-xl py-space-lg border-b border-surface-container-high bg-surface-container-low/60 flex-shrink-0">
          <div className="flex items-center gap-space-sm min-w-0">
            <div className="w-10 h-10 rounded-xl bg-palette-plum text-palette-peach flex items-center justify-center shrink-0 shadow-sm">
              <span className="material-symbols-outlined text-[24px]">description</span>
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-headline-md text-headline-md text-primary font-normal leading-tight truncate">
                  {data?.filename || 'Loading Manuscript...'}
                </h3>
                {data && (
                  <span
                    className={`px-2 py-0.5 rounded font-citation-code text-[11px] font-semibold border ${getFormatBadge(
                      data.filename
                    )}`}
                  >
                    {data.filename.split('.').pop()?.toUpperCase()}
                  </span>
                )}
              </div>
              {data && (
                <span className="font-citation-code text-citation-code text-outline truncate mt-0.5">
                  Extent: {data.pages} p. · {data.chunks_count} retrieval chunks · SHA-256: {data.checksum.slice(0, 16)}…
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-space-sm shrink-0">
            {data && (
              <a
                href={getDocumentDownloadUrl(data.doc_id)}
                download={data.filename}
                className="flex items-center gap-1.5 px-space-md py-2 rounded-lg bg-palette-plum hover:bg-palette-wine text-palette-peach font-ui-label-md text-ui-label-md font-semibold transition-all shadow-sm"
                title="Download original manuscript file"
              >
                <span className="material-symbols-outlined text-[18px]">download</span>
                <span>Download File</span>
              </a>
            )}

            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-surface-container flex items-center justify-center text-outline hover:text-on-surface transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between px-space-xl py-2 border-b border-surface-container-high bg-surface-container-low/30 flex-shrink-0">
          <div className="relative w-72">
            <span className="material-symbols-outlined text-[16px] text-outline absolute left-2.5 top-1/2 -translate-y-1/2">
              search
            </span>
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Find in manuscript text..."
              className="w-full bg-surface-container-lowest border border-surface-container-high pl-8 pr-3 py-1 rounded-lg text-xs font-body-sm text-on-surface focus:outline-none"
            />
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-on-surface-variant hover:text-primary transition-colors px-2 py-1 rounded hover:bg-surface-container"
          >
            <span className="material-symbols-outlined text-[16px]">
              {copied ? 'check' : 'content_copy'}
            </span>
            <span>{copied ? 'Copied' : 'Copy All Text'}</span>
          </button>
        </div>

        {/* Content Preview Window */}
        <div className="flex-1 overflow-y-auto p-space-xl font-body-md text-body-md text-on-surface leading-relaxed">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-outline">
              <span className="material-symbols-outlined text-[32px] animate-spin text-palette-plum">
                progress_activity
              </span>
              <span>Loading manuscript preview...</span>
            </div>
          ) : error ? (
            <div className="p-space-lg rounded-xl bg-palette-rose/10 border border-palette-rose/40 text-palette-rose flex items-center gap-3">
              <span className="material-symbols-outlined text-[24px]">error</span>
              <span>{error}</span>
            </div>
          ) : (
            <div className="whitespace-pre-wrap font-sans text-sm leading-relaxed max-w-none">
              {data?.preview_text}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-space-xl py-space-sm border-t border-surface-container-high bg-surface-container-low/50 flex-shrink-0">
          <span className="font-citation-code text-citation-code text-outline">
            Full cryptographic audit trail · Immutable storage
          </span>
          <button
            onClick={onClose}
            className="px-space-md py-1.5 rounded-lg font-ui-label-md text-ui-label-md text-on-surface hover:bg-surface-container transition-colors"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
};

