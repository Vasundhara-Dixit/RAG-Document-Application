import React, { useEffect, useRef, useState } from 'react';
import { AttachmentReference, ChatSession, DocumentRecord, QueryOptions } from '../types';
import { getDocumentDownloadUrl } from '../api';

interface ComposerProps {
  input: string;
  setInput: (value: string) => void;
  onSubmit: () => void;
  isStreaming: boolean;
  onCancel: () => void;
  options: QueryOptions;
  onOptionsChange: (opts: QueryOptions) => void;
  showOptions: boolean;
  setShowOptions: (val: boolean) => void;
  activeDocFilter: string | null;
  documents: DocumentRecord[];
  sessions: ChatSession[];
  attachments: AttachmentReference[];
  onAddAttachment: (att: AttachmentReference) => void;
  onRemoveAttachment: (id: string) => void;
  onUploadFile: (file: File) => Promise<DocumentRecord>;
  onPreviewDocument: (docId: string) => void;
}

export const Composer: React.FC<ComposerProps> = ({
  input,
  setInput,
  onSubmit,
  isStreaming,
  onCancel,
  options,
  onOptionsChange,
  showOptions,
  setShowOptions,
  activeDocFilter,
  documents,
  sessions,
  attachments,
  onAddAttachment,
  onRemoveAttachment,
  onUploadFile,
  onPreviewDocument,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [attachSubmenu, setAttachSubmenu] = useState<'root' | 'manuscripts' | 'chats'>('root');
  const [isUploadingAttachment, setIsUploadingAttachment] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Inline "@" Mention state
  const [mentionActive, setMentionActive] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionIndex, setMentionIndex] = useState(0);

  // Filtered documents for "@" mention
  const filteredMentionDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  // Global '/' hotkey to focus composer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === '/' &&
        document.activeElement?.tagName !== 'INPUT' &&
        document.activeElement?.tagName !== 'TEXTAREA'
      ) {
        e.preventDefault();
        textareaRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close attach menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowAttachMenu(false);
        setAttachSubmenu('root');
      }
    };
    if (showAttachMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showAttachMenu]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInput(val);

    const cursor = e.target.selectionStart || 0;
    const textBefore = val.slice(0, cursor);
    const atMatch = textBefore.match(/@([a-zA-Z0-9_\.-]*)$/);

    if (atMatch) {
      setMentionActive(true);
      setMentionQuery(atMatch[1]);
      setMentionIndex(0);
    } else {
      setMentionActive(false);
    }
  };

  const handleSelectMention = (doc: DocumentRecord) => {
    // Attach manuscript
    onAddAttachment({
      type: 'manuscript',
      id: doc.doc_id,
      title: doc.filename,
    });

    // Strip the @query from input
    if (textareaRef.current) {
      const cursor = textareaRef.current.selectionStart || 0;
      const textBefore = input.slice(0, cursor);
      const textAfter = input.slice(cursor);
      const cleanedBefore = textBefore.replace(/@([a-zA-Z0-9_\.-]*)$/, '');
      const nextInput = `${cleanedBefore}${textAfter}`;
      setInput(nextInput);
    }

    setMentionActive(false);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Handle "@" mention dropdown keyboard navigation
    if (mentionActive && filteredMentionDocs.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setMentionIndex((prev) => (prev + 1) % filteredMentionDocs.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setMentionIndex((prev) => (prev - 1 + filteredMentionDocs.length) % filteredMentionDocs.length);
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        handleSelectMention(filteredMentionDocs[mentionIndex]);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setMentionActive(false);
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming && (input.trim() || attachments.length > 0)) {
        onSubmit();
      }
    } else if (e.key === 'Escape' && isStreaming) {
      e.preventDefault();
      onCancel();
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setShowAttachMenu(false);
    setAttachSubmenu('root');
    setIsUploadingAttachment(true);
    try {
      const doc = await onUploadFile(file);
      onAddAttachment({
        type: 'file_upload',
        id: doc.doc_id,
        title: file.name,
      });
    } catch (err: any) {
      alert(`Attachment upload failed: ${err.message || err}`);
    } finally {
      setIsUploadingAttachment(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const getFormatColor = (filename: string) => {
    const ext = filename.split('.').pop()?.toUpperCase() || 'TXT';
    if (ext === 'PDF') return 'text-red-700 bg-red-500/15';
    if (ext === 'DOCX') return 'text-blue-700 bg-blue-500/15';
    if (ext === 'MD') return 'text-purple-700 bg-purple-500/15';
    return 'text-amber-700 bg-amber-500/15';
  };

  return (
    <div className="w-full max-w-[760px] mx-auto flex flex-col gap-space-xs pointer-events-auto relative">
      {/* Hidden file input for "+" button */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.md,.txt"
        className="hidden"
        onChange={(e) => handleFileUpload(e.target.files)}
      />

      {/* Floating "@" Mention Autocomplete Menu */}
      {mentionActive && (
        <div className="absolute bottom-full left-0 mb-2 w-80 rounded-xl bg-surface-container-lowest border border-surface-container-high shadow-2xl p-1.5 z-50 flex flex-col gap-0.5 animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="px-2.5 py-1 flex items-center justify-between border-b border-surface-container-high mb-1">
            <span className="font-ui-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px] text-palette-plum">alternate_email</span>
              <span>Reference Manuscript</span>
            </span>
            <span className="font-citation-code text-[10px] text-outline">
              {filteredMentionDocs.length} matching
            </span>
          </div>

          <div className="max-h-52 overflow-y-auto space-y-0.5">
            {filteredMentionDocs.length === 0 ? (
              <div className="p-3 text-center text-xs text-outline italic">
                No matching manuscripts found for &ldquo;{mentionQuery}&rdquo;
              </div>
            ) : (
              filteredMentionDocs.map((doc, idx) => (
                <div
                  key={doc.doc_id}
                  onClick={() => handleSelectMention(doc)}
                  className={`w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                    mentionIndex === idx
                      ? 'bg-palette-peach/30 text-palette-plum font-semibold'
                      : 'hover:bg-surface-container-low text-on-surface'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate min-w-0">
                    <span
                      className={`px-1.5 py-0.5 rounded font-citation-code text-[10px] font-bold ${getFormatColor(
                        doc.filename
                      )}`}
                    >
                      {doc.filename.split('.').pop()?.toUpperCase()}
                    </span>
                    <span className="text-xs truncate">{doc.filename}</span>
                  </div>
                  <span className="font-citation-code text-[10px] text-outline shrink-0 ml-2">
                    {doc.pages} p.
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="px-2 pt-1 border-t border-surface-container-high text-[10px] text-outline flex items-center justify-between">
            <span>↑↓ to navigate · Enter to reference</span>
            <span>Esc to cancel</span>
          </div>
        </div>
      )}

      {/* Optional Retrieval Parameter Drawer */}
      {showOptions && (
        <div className="p-space-md rounded-xl bg-surface border border-surface-container-high shadow-lg flex flex-col gap-space-sm mb-1 animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="flex items-center justify-between pb-space-xs border-b border-surface-container-high">
            <div className="flex items-center gap-1.5 font-ui-label-sm text-ui-label-sm text-primary uppercase font-bold tracking-wider">
              <span className="material-symbols-outlined text-[16px] text-secondary">tune</span>
              <span>Advanced Retrieval Configuration (Phases 3–6)</span>
            </div>
            <button
              onClick={() => setShowOptions(false)}
              className="text-outline hover:text-on-surface text-ui-label-sm"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-space-md pt-1">
            {/* Retrieval Mode */}
            <div className="flex flex-col gap-1">
              <label className="font-ui-label-sm text-ui-label-sm text-outline uppercase tracking-wider">
                Retrieval Engine
              </label>
              <select
                value={options.hybrid_enabled === false ? 'dense' : 'hybrid'}
                onChange={(e) =>
                  onOptionsChange({
                    ...options,
                    hybrid_enabled: e.target.value === 'hybrid',
                  })
                }
                className="bg-surface-container-low border border-surface-container-high rounded px-2 py-1 font-ui-label-md text-ui-label-md text-on-surface focus:outline-none focus:border-primary"
              >
                <option value="hybrid">Hybrid (BM25 + Dense RRF)</option>
                <option value="dense">Dense Only (FAISS)</option>
              </select>
            </div>

            {/* Cross-Encoder Reranker */}
            <div className="flex flex-col gap-1">
              <label className="font-ui-label-sm text-ui-label-sm text-outline uppercase tracking-wider">
                Cross-Encoder Rerank
              </label>
              <select
                value={options.reranker_enabled === false ? 'off' : 'on'}
                onChange={(e) =>
                  onOptionsChange({
                    ...options,
                    reranker_enabled: e.target.value === 'on',
                  })
                }
                className="bg-surface-container-low border border-surface-container-high rounded px-2 py-1 font-ui-label-md text-ui-label-md text-on-surface focus:outline-none focus:border-primary"
              >
                <option value="on">Enabled (Top-50 → 5)</option>
                <option value="off">Disabled</option>
              </select>
            </div>

            {/* Query Transformation */}
            <div className="flex flex-col gap-1">
              <label className="font-ui-label-sm text-ui-label-sm text-outline uppercase tracking-wider">
                Query Transformation
              </label>
              <select
                value={options.query_transform_strategy || 'none'}
                onChange={(e) =>
                  onOptionsChange({
                    ...options,
                    query_transform_strategy: e.target.value,
                  })
                }
                className="bg-surface-container-low border border-surface-container-high rounded px-2 py-1 font-ui-label-md text-ui-label-md text-on-surface focus:outline-none focus:border-primary"
              >
                <option value="none">None (Standard)</option>
                <option value="hyde">HyDE (Hypothetical Doc)</option>
                <option value="multi_query">Multi-Query Expansion</option>
                <option value="step_back">Step-Back Prompting</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Main Composer Box */}
      <div className="rounded-xl bg-surface/90 backdrop-blur-xl border border-surface-container-high shadow-2xl flex flex-col p-space-sm transition-all focus-within:ring-2 focus-within:ring-primary focus-within:border-primary relative">
        {/* ChatGPT-Style Referenced Attachment Cards Bar */}
        {(attachments.length > 0 || isUploadingAttachment) && (
          <div className="flex flex-wrap items-center gap-2 pb-2.5 px-1 border-b border-surface-container-high mb-1.5">
            {attachments.map((att) => (
              <div
                key={att.id}
                className="inline-flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-surface-container-lowest border border-surface-container-high font-citation-code text-xs text-on-surface shadow-sm hover:shadow transition-all group"
              >
                <span
                  className={`px-1.5 py-0.5 rounded font-citation-code text-[10px] font-bold ${getFormatColor(
                    att.title
                  )}`}
                >
                  {att.title.split('.').pop()?.toUpperCase()}
                </span>
                <span className="font-medium truncate max-w-[170px] text-on-surface font-sans" title={att.title}>
                  {att.title}
                </span>

                {/* Preview and Re-download actions */}
                <div className="flex items-center gap-0.5 border-l border-surface-container-high pl-1 ml-0.5">
                  <button
                    type="button"
                    onClick={() => onPreviewDocument(att.id)}
                    className="p-1 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors"
                    title="Preview manuscript content"
                  >
                    <span className="material-symbols-outlined text-[15px]">visibility</span>
                  </button>
                  <a
                    href={getDocumentDownloadUrl(att.id)}
                    download={att.title}
                    className="p-1 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors"
                    title="Download original file"
                  >
                    <span className="material-symbols-outlined text-[15px]">download</span>
                  </a>
                  <button
                    type="button"
                    onClick={() => onRemoveAttachment(att.id)}
                    className="p-1 rounded hover:bg-palette-rose/10 text-outline hover:text-palette-rose transition-colors"
                    title="Remove reference"
                  >
                    <span className="material-symbols-outlined text-[15px]">close</span>
                  </button>
                </div>
              </div>
            ))}

            {isUploadingAttachment && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-container font-citation-code text-[11px] text-primary">
                <span className="material-symbols-outlined text-[15px] animate-spin">progress_activity</span>
                <span>Ingesting document...</span>
              </span>
            )}
          </div>
        )}

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={
            activeDocFilter
              ? `Ask question scoped to ${activeDocFilter} (type @ to reference, / to focus)...`
              : 'Ask a question across indexed documents (type @ to reference files, / to focus)...'
          }
          rows={2}
          disabled={isStreaming}
          className="w-full bg-transparent px-space-sm py-1 font-body-md text-body-md text-on-surface placeholder:text-outline placeholder:italic focus:outline-none resize-none disabled:opacity-50"
        />

        {/* Footer toolbar */}
        <div className="flex items-center justify-between pt-space-xs px-space-xs border-t border-surface-container-high/60 mt-1">
          <div className="flex items-center gap-space-sm relative">
            {/* The Prominent "+" Action Button */}
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => {
                  setShowAttachMenu(!showAttachMenu);
                  setAttachSubmenu('root');
                }}
                className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
                  showAttachMenu
                    ? 'bg-palette-plum text-palette-peach shadow-sm ring-2 ring-palette-rose/40'
                    : 'bg-surface-container hover:bg-surface-container-high text-palette-plum hover:text-palette-rose'
                }`}
                title="Add files or reference past chats (+ or @)"
              >
                <span className="material-symbols-outlined text-[19px] font-bold">add</span>
              </button>

              {/* Popover Action Menu */}
              {showAttachMenu && (
                <div className="absolute bottom-9 left-0 w-64 rounded-xl bg-surface-container-lowest border border-surface-container-high shadow-2xl p-1.5 z-50 flex flex-col gap-0.5 animate-in fade-in slide-in-from-bottom-2 duration-150">
                  {attachSubmenu === 'root' && (
                    <>
                      <div className="px-2.5 py-1.5 font-ui-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold border-b border-surface-container-high mb-1">
                        Add &amp; Reference Context
                      </div>

                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-surface-container-low flex items-center gap-2.5 text-on-surface font-ui-label-md text-ui-label-md transition-colors cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-[18px] text-palette-plum">upload_file</span>
                        <div className="flex flex-col">
                          <span className="font-medium">Upload New Manuscript</span>
                          <span className="text-[10px] text-outline">PDF, DOCX, MD, TXT</span>
                        </div>
                      </button>

                      <button
                        type="button"
                        onClick={() => setAttachSubmenu('manuscripts')}
                        className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-surface-container-low flex items-center justify-between text-on-surface font-ui-label-md text-ui-label-md transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="material-symbols-outlined text-[18px] text-primary">description</span>
                          <span className="font-medium">Reference Manuscript (@)</span>
                        </div>
                        <span className="material-symbols-outlined text-[16px] text-outline">chevron_right</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setAttachSubmenu('chats')}
                        className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-surface-container-low flex items-center justify-between text-on-surface font-ui-label-md text-ui-label-md transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="material-symbols-outlined text-[18px] text-palette-rose">forum</span>
                          <span className="font-medium">Reference Past Chat</span>
                        </div>
                        <span className="material-symbols-outlined text-[16px] text-outline">chevron_right</span>
                      </button>
                    </>
                  )}

                  {attachSubmenu === 'manuscripts' && (
                    <div className="flex flex-col max-h-56 overflow-y-auto">
                      <div className="flex items-center justify-between px-2 py-1 border-b border-surface-container-high mb-1">
                        <button
                          type="button"
                          onClick={() => setAttachSubmenu('root')}
                          className="flex items-center gap-1 font-ui-label-sm text-[11px] text-outline hover:text-on-surface font-semibold"
                        >
                          <span className="material-symbols-outlined text-[14px]">chevron_left</span>
                          <span>Manuscripts</span>
                        </button>
                        <span className="font-citation-code text-[10px] text-outline">{documents.length} available</span>
                      </div>

                      {documents.length === 0 ? (
                        <div className="p-3 text-center text-xs text-outline italic">No manuscripts indexed yet</div>
                      ) : (
                        documents.map((doc) => (
                          <button
                            key={doc.doc_id}
                            type="button"
                            onClick={() => {
                              onAddAttachment({
                                type: 'manuscript',
                                id: doc.doc_id,
                                title: doc.filename,
                              });
                              setShowAttachMenu(false);
                            }}
                            className="w-full text-left px-2 py-1.5 rounded hover:bg-surface-container-low flex items-center gap-2 text-on-surface text-xs truncate transition-colors cursor-pointer"
                          >
                            <span className="material-symbols-outlined text-[15px] text-primary shrink-0">description</span>
                            <span className="truncate">{doc.filename}</span>
                          </button>
                        ))
                      )}
                    </div>
                  )}

                  {attachSubmenu === 'chats' && (
                    <div className="flex flex-col max-h-56 overflow-y-auto">
                      <div className="flex items-center justify-between px-2 py-1 border-b border-surface-container-high mb-1">
                        <button
                          type="button"
                          onClick={() => setAttachSubmenu('root')}
                          className="flex items-center gap-1 font-ui-label-sm text-[11px] text-outline hover:text-on-surface font-semibold"
                        >
                          <span className="material-symbols-outlined text-[14px]">chevron_left</span>
                          <span>Past Inquiries</span>
                        </button>
                        <span className="font-citation-code text-[10px] text-outline">{sessions.length} chats</span>
                      </div>

                      {sessions.length === 0 ? (
                        <div className="p-3 text-center text-xs text-outline italic">No past chat sessions saved</div>
                      ) : (
                        sessions.map((ses) => (
                          <button
                            key={ses.id}
                            type="button"
                            onClick={() => {
                              const lastAnswer = ses.messages.filter((m) => m.role === 'assistant').pop()?.content;
                              onAddAttachment({
                                type: 'past_chat',
                                id: ses.id,
                                title: ses.title,
                                snippet: lastAnswer ? lastAnswer.slice(0, 150) : undefined,
                              });
                              setShowAttachMenu(false);
                            }}
                            className="w-full text-left px-2 py-1.5 rounded hover:bg-surface-container-low flex items-center gap-2 text-on-surface text-xs truncate transition-colors cursor-pointer"
                          >
                            <span className="material-symbols-outlined text-[15px] text-palette-rose shrink-0">forum</span>
                            <div className="flex flex-col truncate">
                              <span className="truncate font-medium">{ses.title}</span>
                              <span className="text-[10px] text-outline">
                                {new Date(ses.updatedAt).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                              </span>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Retrieval Tuning Button */}
            <button
              type="button"
              onClick={() => setShowOptions(!showOptions)}
              className="px-2 py-1 rounded bg-surface-container hover:bg-surface-container-high border border-surface-container-high flex items-center gap-1.5 font-citation-code text-citation-code text-primary transition-colors cursor-pointer"
              title="Tune retrieval parameters"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-palette-rose" />
              <span>
                {options.hybrid_enabled !== false ? 'Hybrid+RRF' : 'Dense'}{' '}
                {options.reranker_enabled !== false && '+ Rerank'}
                {options.query_transform_strategy && options.query_transform_strategy !== 'none' && ` (${options.query_transform_strategy})`}
              </span>
              <span className="material-symbols-outlined text-[14px]">expand_more</span>
            </button>

            {activeDocFilter && (
              <div className="flex items-center gap-1 font-citation-code text-citation-code px-2 py-0.5 rounded bg-palette-peach/30 border border-palette-coral/30 text-primary truncate max-w-[160px]">
                <span className="material-symbols-outlined text-[12px] text-secondary">filter_alt</span>
                <span className="truncate">{activeDocFilter}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-space-xs">
            {isStreaming ? (
              <button
                type="button"
                onClick={onCancel}
                className="px-space-md py-1.5 rounded-lg bg-palette-rose hover:bg-palette-plum text-white font-ui-label-md text-ui-label-md flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                <span>Halt (Esc)</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={onSubmit}
                disabled={!input.trim() && attachments.length === 0}
                className="px-space-md py-1.5 rounded-lg bg-primary hover:bg-palette-wine text-white disabled:opacity-40 disabled:pointer-events-none font-ui-label-md text-ui-label-md flex items-center gap-1 transition-all shadow-sm font-semibold cursor-pointer"
              >
                <span>Submit Inquiry</span>
                <span className="material-symbols-outlined text-[16px]">arrow_upward</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Scholarly Hotkey Ribbon with @ mention hint */}
      <div className="flex items-center justify-center gap-space-md font-citation-code text-citation-code text-outline py-0.5">
        <span className="flex items-center gap-1">
          <kbd className="px-1 py-0.5 rounded bg-surface-container-high text-on-surface font-mono text-[10px]">@</kbd>
          reference file
        </span>
        <span>·</span>
        <span className="flex items-center gap-1">
          <kbd className="px-1 py-0.5 rounded bg-surface-container-high text-on-surface font-mono text-[10px]">Alt</kbd>
          +
          <kbd className="px-1 py-0.5 rounded bg-surface-container-high text-on-surface font-mono text-[10px]">↑/↓</kbd>
          citations
        </span>
        <span>·</span>
        <span className="flex items-center gap-1">
          <kbd className="px-1 py-0.5 rounded bg-surface-container-high text-on-surface font-mono text-[10px]">/</kbd>
          focus
        </span>
      </div>
    </div>
  );
};
