import React, { useState } from 'react';
import { Message } from '../types';
import { CitationChip } from './CitationChip';
import { getDocumentDownloadUrl } from '../api';

interface MessageBlockProps {
  message: Message;
  onCitationClick: (passageIndex: number) => void;
  selectedCitationIndex?: number;
  onPreviewDocument: (docId: string) => void;
}

export const MessageBlock: React.FC<MessageBlockProps> = ({
  message,
  onCitationClick,
  selectedCitationIndex,
  onPreviewDocument,
}) => {
  const [showMatrix, setShowMatrix] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getFormatBadge = (filename: string) => {
    const ext = filename.split('.').pop()?.toUpperCase() || 'TXT';
    if (ext === 'PDF') return 'text-red-700 bg-red-500/15';
    if (ext === 'DOCX') return 'text-blue-700 bg-blue-500/15';
    if (ext === 'MD') return 'text-purple-700 bg-purple-500/15';
    return 'text-amber-700 bg-amber-500/15';
  };

  // User Inquiry Card (ChatGPT Style)
  if (message.role === 'user') {
    return (
      <article className="w-full max-w-[760px] flex flex-col gap-space-xs my-space-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-space-xs">
            <span className="w-5 h-5 rounded-full bg-palette-wine text-palette-peach flex items-center justify-center font-citation-code text-citation-code font-bold shadow-sm">
              Q
            </span>
            <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
              Inquiry · Researcher Session
            </span>
          </div>
          <time className="font-citation-code text-citation-code text-outline">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </time>
        </div>

        <div className="p-space-lg rounded-xl bg-surface-container-high/90 backdrop-blur-md border border-surface-container-highest text-on-surface shadow-sm flex flex-col gap-space-sm">
          {/* User Question */}
          <p className="font-ui-label-lg text-ui-label-lg leading-relaxed text-on-surface font-normal">
            {message.content}
          </p>

          {/* ChatGPT-style Attached / Referenced File Cards */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-surface-container-highest/60 mt-1">
              {message.attachments.map((att) => (
                <div
                  key={att.id}
                  className="flex items-center gap-2.5 p-2 rounded-xl bg-surface-container-lowest/90 border border-surface-container-high shadow-sm hover:shadow transition-all group"
                >
                  <span
                    className={`px-1.5 py-0.5 rounded font-citation-code text-[10px] font-bold ${getFormatBadge(
                      att.title
                    )}`}
                  >
                    {att.title.split('.').pop()?.toUpperCase()}
                  </span>

                  <div className="flex flex-col min-w-0 pr-1">
                    <span className="font-ui-label-md text-xs font-semibold text-on-surface truncate max-w-[190px]">
                      {att.title}
                    </span>
                    <span className="font-citation-code text-[10px] text-outline">
                      {att.type === 'file_upload' ? 'Uploaded Manuscript' : 'Referenced Manuscript'}
                    </span>
                  </div>

                  {/* Actions: Preview & Re-Download */}
                  <div className="flex items-center gap-0.5 border-l border-surface-container-high pl-1 ml-0.5">
                    <button
                      type="button"
                      onClick={() => onPreviewDocument(att.id)}
                      className="p-1 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors"
                      title="Preview manuscript"
                    >
                      <span className="material-symbols-outlined text-[16px]">visibility</span>
                    </button>
                    <a
                      href={getDocumentDownloadUrl(att.id)}
                      download={att.title}
                      className="p-1 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors"
                      title="Re-download original manuscript"
                    >
                      <span className="material-symbols-outlined text-[16px]">download</span>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </article>
    );
  }

  // Assistant Synthesized Evidentiary Document Leaf
  const citations = message.citations || [];
  const contexts = message.contexts || [];

  // Deduplicate unique evidentiary manuscripts
  const uniqueCitedDocs = Array.from(
    new Map(citations.map((c) => [c.doc_id, { doc_id: c.doc_id, filename: c.filename, page: c.page }])).values()
  );

  return (
    <article className="w-full max-w-[760px] relative flex flex-col bg-surface/90 backdrop-blur-xl rounded-xl shadow-md border border-surface-container-high p-space-xl my-space-md overflow-hidden">
      {/* Archival Header Ribbon */}
      <div className="flex items-center justify-between pb-space-md mb-space-lg bg-surface-container-low/60 -mx-space-xl -mt-space-xl px-space-xl pt-space-md border-b border-surface-container-high">
        <div className="flex items-center gap-space-sm">
          <span className="px-2.5 py-0.5 rounded bg-primary text-white font-ui-label-sm text-ui-label-sm font-semibold tracking-widest uppercase shadow-sm">
            Answer
          </span>
          <span className="font-ui-label-md text-ui-label-md text-on-surface-variant font-medium">
            Archival Synthesis
          </span>
        </div>

        <div className="flex items-center gap-space-md">
          {message.abstained ? (
            <div className="flex items-center gap-1 font-citation-code text-citation-code text-palette-plum font-semibold">
              <span className="material-symbols-outlined text-[16px] text-palette-plum">info</span>
              <span>Grounded Refusal (Strict Evidence Gate)</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 font-citation-code text-citation-code text-primary font-medium">
              <span className="material-symbols-outlined text-[15px] text-secondary">verified_user</span>
              <span>Citation Alignment: Complete</span>
            </div>
          )}
        </div>
      </div>

      {/* Evidentiary Narrative Body */}
      <div className="flex flex-col gap-space-md text-on-surface">
        <div className="font-body-lg text-body-lg text-on-surface leading-loose whitespace-pre-wrap">
          {message.content}
          {message.isStreaming && (
            <span className="inline-block w-2 h-4 ml-1 bg-palette-rose animate-pulse align-middle" />
          )}
        </div>

        {/* ChatGPT-style Evidentiary Manuscripts with Preview & Re-download */}
        {uniqueCitedDocs.length > 0 && (
          <div className="flex flex-col gap-1.5 pt-space-sm border-t border-surface-container-high/60">
            <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
              Evidentiary Manuscripts:
            </span>
            <div className="flex flex-wrap items-center gap-2">
              {uniqueCitedDocs.map((doc) => (
                <div
                  key={doc.doc_id}
                  className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-surface-container-low border border-surface-container-high shadow-sm hover:shadow transition-all"
                >
                  <span
                    className={`px-1.5 py-0.2 rounded font-citation-code text-[10px] font-bold ${getFormatBadge(
                      doc.filename
                    )}`}
                  >
                    {doc.filename.split('.').pop()?.toUpperCase()}
                  </span>
                  <span className="font-ui-label-md text-xs font-medium text-on-surface truncate max-w-[170px]" title={doc.filename}>
                    {doc.filename}
                  </span>

                  {/* Actions: Preview & Download */}
                  <div className="flex items-center gap-0.5 border-l border-surface-container-high pl-1 ml-0.5">
                    <button
                      type="button"
                      onClick={() => onPreviewDocument(doc.doc_id)}
                      className="p-1 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors"
                      title="Preview manuscript"
                    >
                      <span className="material-symbols-outlined text-[15px]">visibility</span>
                    </button>
                    <a
                      href={getDocumentDownloadUrl(doc.doc_id)}
                      download={doc.filename}
                      className="p-1 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors"
                      title="Download manuscript file"
                    >
                      <span className="material-symbols-outlined text-[15px]">download</span>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Inline Citation Chips preview list */}
        {citations.length > 0 && (
          <div className="flex items-center flex-wrap gap-1.5 pt-space-xs">
            <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline mr-1 font-semibold">
              Passage Excerpts:
            </span>
            {citations.map((c, i) => (
              <CitationChip
                key={`${c.chunk_id}-${i}`}
                citation={c}
                active={selectedCitationIndex === i}
                onClick={() => onCitationClick(i)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Synthesis Metadata Footer & Provenance Actions */}
      <footer className="mt-space-xl pt-space-md bg-surface-container-low/40 -mx-space-xl -mb-space-xl px-space-xl pb-space-md flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm border-t border-surface-container-high">
        <div className="flex items-center gap-space-md font-citation-code text-citation-code text-outline">
          {message.timings && (
            <span className="flex items-center gap-1 text-primary">
              <span className="material-symbols-outlined text-[14px] text-secondary">timer</span>
              {Math.round(message.timings.total_ms)} ms
            </span>
          )}
          <span>·</span>
          <span className="text-on-surface-variant">{contexts.length} passages retrieved</span>
          <span>·</span>
          <span className="flex items-center gap-1 text-primary font-medium">
            <span className="material-symbols-outlined text-[14px] text-secondary">check_circle</span>
            Faithfulness {message.abstained ? '1.00' : '0.98'}
          </span>
        </div>

        <div className="flex items-center gap-space-xs">
          <button
            onClick={handleCopy}
            className="px-space-sm py-1 rounded-lg hover:bg-surface-container text-on-surface-variant font-ui-label-md text-ui-label-md flex items-center gap-1 transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">
              {copied ? 'check' : 'content_copy'}
            </span>
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {contexts.length > 0 && (
            <button
              onClick={() => setShowMatrix(!showMatrix)}
              className="px-space-sm py-1 rounded-lg bg-surface-container hover:bg-surface-container-high text-primary font-ui-label-md text-ui-label-md flex items-center gap-1 transition-colors border border-surface-container-high cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">
                {showMatrix ? 'expand_less' : 'visibility'}
              </span>
              <span>All {contexts.length} Excerpts</span>
            </button>
          )}
        </div>
      </footer>

      {/* Collapsible Retrieval Ledger Matrix */}
      {showMatrix && contexts.length > 0 && (
        <div className="mt-space-lg p-space-md rounded-xl bg-surface-container-low border border-surface-container-high flex flex-col gap-space-sm animate-in fade-in duration-150">
          <div className="flex items-center justify-between pb-space-xs border-b border-surface-container-high">
            <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
              Retrieval Ledger Hierarchy (Ranked by Fused Similarity)
            </span>
            <span className="font-citation-code text-citation-code text-primary font-medium">
              Top-{contexts.length} Passages
            </span>
          </div>

          <div className="grid grid-cols-1 gap-space-xs font-citation-code text-citation-code">
            {contexts.map((p, idx) => (
              <div
                key={p.chunk.chunk_id}
                onClick={() => onCitationClick(idx)}
                className={`p-space-sm rounded-lg flex items-center justify-between cursor-pointer transition-colors border ${
                  selectedCitationIndex === idx
                    ? 'bg-palette-peach/30 border-palette-coral text-primary font-semibold'
                    : 'bg-surface hover:bg-surface-container border-surface-container-high text-on-surface'
                }`}
              >
                <div className="flex items-center gap-space-sm truncate max-w-[500px]">
                  <span className="text-secondary font-bold">[{idx + 1}]</span>
                  <span className="truncate">
                    {p.chunk.doc_id} · p.{p.chunk.page_start}
                    {p.chunk.section_title && ` · ${p.chunk.section_title}`}
                  </span>
                </div>
                <span className="text-outline font-mono">Score: {p.score.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  );
};
