import React, { useState, useEffect } from 'react';
import { AttachmentReference, ChatSession, DocumentRecord, Message, QueryOptions, RetrievedPassage } from '../types';
import { MessageBlock } from '../components/MessageBlock';
import { Composer } from '../components/Composer';
import { SourceDrawer } from '../components/SourceDrawer';
import { DocumentPreviewModal } from '../components/DocumentPreviewModal';
import { streamQueryQA } from '../api';
import { generateSessionTitle } from '../utils/chatHistory';

interface ChatViewProps {
  documents: DocumentRecord[];
  onNavigateToLibrary: () => void;
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSaveSession: (session: ChatSession) => void;
  onUploadFile: (file: File) => Promise<DocumentRecord>;
}

const SAMPLE_QUESTIONS = [
  'What encryption algorithm is used to protect backup archives?',
  'What is the standard hardware bundle and internet stipend for remote work?',
  'What were Acme’s total revenue and operating expenses in Q3 2026?',
  'Under what conditions can PTO carry-over exceed the standard 80-hour ceiling?',
];

export const ChatView: React.FC<ChatViewProps> = ({
  documents,
  onNavigateToLibrary,
  sessions,
  activeSessionId,
  onSaveSession,
  onUploadFile,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [activeContexts, setActiveContexts] = useState<RetrievedPassage[]>([]);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Referenced attachments from the "+" button
  const [attachments, setAttachments] = useState<AttachmentReference[]>([]);

  // Document preview modal state
  const [previewDocId, setPreviewDocId] = useState<string | null>(null);

  // Corpus scoping state
  const [selectedScope, setSelectedScope] = useState<string>('all');

  // Retrieval pipeline options
  const [showOptions, setShowOptions] = useState(false);
  const [options, setOptions] = useState<QueryOptions>({
    hybrid_enabled: true,
    reranker_enabled: true,
    query_transform_strategy: 'none',
    k: 5,
  });

  // Load active session when activeSessionId changes
  useEffect(() => {
    if (activeSessionId) {
      const activeSession = sessions.find((s) => s.id === activeSessionId);
      if (activeSession) {
        setMessages(activeSession.messages);
        setActiveContexts(activeSession.contexts || []);
        setIsDrawerOpen(false);
        return;
      }
    }
    // If no active session or new session triggered
    setMessages([]);
    setActiveContexts([]);
    setIsDrawerOpen(false);
    setAttachments([]);
  }, [activeSessionId, sessions]);

  const handleAddAttachment = (att: AttachmentReference) => {
    if (!attachments.some((a) => a.id === att.id)) {
      setAttachments((prev) => [...prev, att]);
    }
  };

  const handleRemoveAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const handleSend = (question: string) => {
    let effectiveQuestion = question.trim();

    // 1. Incorporate referenced manuscripts
    const referencedDocs = attachments.filter((a) => a.type === 'manuscript' || a.type === 'file_upload');
    if (referencedDocs.length > 0) {
      const docTitles = referencedDocs.map((d) => d.title).join(', ');
      effectiveQuestion = `[Referenced Manuscripts: ${docTitles}] ${effectiveQuestion}`;
    }

    // 2. Incorporate referenced past chats
    const referencedChats = attachments.filter((a) => a.type === 'past_chat');
    if (referencedChats.length > 0) {
      const chatSnippets = referencedChats
        .map((c) => `Context from past session "${c.title}": ${c.snippet || 'None'}`)
        .join('; ');
      effectiveQuestion = `[Prior Findings: ${chatSnippets}]\n\n${effectiveQuestion}`;
    }

    // 3. Incorporate top bar scope filter if not 'all'
    if (selectedScope !== 'all') {
      const targetDoc = documents.find((d) => d.doc_id === selectedScope);
      if (targetDoc) {
        effectiveQuestion = `[Scope: ${targetDoc.filename}] ${effectiveQuestion}`;
      }
    }

    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    const userMessage: Message = {
      id: userMsgId,
      role: 'user',
      content: question,
      attachments: attachments.length > 0 ? [...attachments] : undefined,
    };

    const assistantMessage: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      isStreaming: true,
    };

    const nextMessages = [...messages, userMessage, assistantMessage];
    setMessages(nextMessages);
    setIsStreaming(true);

    const controller = new AbortController();
    setAbortController(controller);

    let accumulatedContent = '';

    streamQueryQA(
      effectiveQuestion,
      options,
      // onToken
      (token: string) => {
        accumulatedContent += token;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: accumulatedContent }
              : m
          )
        );
      },
      // onComplete
      (data) => {
        setIsStreaming(false);
        setAbortController(null);
        const finalMessages = nextMessages.map((m) =>
          m.id === assistantMsgId
            ? {
                ...m,
                content: data.answer,
                citations: data.citations,
                contexts: data.contexts,
                timings: data.timings,
                abstained: data.abstained,
                isStreaming: false,
              }
            : m
        );

        setMessages(finalMessages);

        if (data.contexts && data.contexts.length > 0) {
          setActiveContexts(data.contexts);
          setSelectedIndex(0);
          setIsDrawerOpen(true);
        }

        // Save or update session
        const sessionId = activeSessionId || `session_${Date.now()}`;
        const existingSession = sessions.find((s) => s.id === sessionId);
        const title = existingSession ? existingSession.title : generateSessionTitle(question);

        const updatedSession: ChatSession = {
          id: sessionId,
          title,
          createdAt: existingSession ? existingSession.createdAt : new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          messages: finalMessages,
          contexts: data.contexts || activeContexts,
          referencedDocs: attachments.map((a) => a.title),
        };

        onSaveSession(updatedSession);
        // Clear one-shot attachments after submission
        setAttachments([]);
      },
      // onError
      (err) => {
        setIsStreaming(false);
        setAbortController(null);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: `Error: ${err.message}`,
                  isStreaming: false,
                }
              : m
          )
        );
      },
      controller.signal
    );
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    );
  };

  const handleSubmit = () => {
    if (!input.trim() && attachments.length === 0) return;
    if (isStreaming) return;
    const q = input;
    setInput('');
    handleSend(q);
  };

  const handleCitationClick = (passageIdx: number) => {
    setSelectedIndex(passageIdx);
    setIsDrawerOpen(true);
  };

  // Compute total unique documents retrieved across conversation
  const totalPassagesCount = activeContexts.length;
  const uniqueDocsCount = new Set(activeContexts.map((c) => c.chunk.doc_id)).size;

  return (
    <div className="flex-1 flex flex-col h-full bg-transparent overflow-hidden relative">
      {/* Scope Filter Header & Archival Index Bar */}
      <div className="w-full flex-shrink-0 px-gutter-desktop py-space-sm bg-surface-container-low/85 backdrop-blur-md border-b border-surface-container-high flex items-center justify-between shadow-sm z-10">
        <div className="flex items-center gap-space-sm overflow-x-auto py-0.5 no-scrollbar">
          <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-widest text-outline flex items-center gap-1.5 mr-space-xs font-semibold">
            <span className="material-symbols-outlined text-[15px] text-primary">filter_alt</span>
            Corpus Scope:
          </span>

          <button
            onClick={() => setSelectedScope('all')}
            className={`flex items-center gap-1.5 px-space-md py-1 rounded font-ui-label-md text-ui-label-md transition-all ${
              selectedScope === 'all'
                ? 'bg-primary text-on-primary shadow-sm font-medium'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface-variant'
            }`}
          >
            <span>All Manuscripts</span>
            <span
              className={`px-1.5 py-0.5 rounded-full font-citation-code text-[10px] ${
                selectedScope === 'all'
                  ? 'bg-palette-plum text-palette-peach'
                  : 'bg-surface-container-highest text-on-surface-variant'
              }`}
            >
              {documents.length}
            </span>
          </button>

          {documents.slice(0, 4).map((doc) => {
            const isSelected = selectedScope === doc.doc_id;
            return (
              <button
                key={doc.doc_id}
                onClick={() => setSelectedScope(isSelected ? 'all' : doc.doc_id)}
                className={`flex items-center gap-1.5 px-space-md py-1 rounded font-ui-label-md text-ui-label-md transition-all truncate max-w-[220px] ${
                  isSelected
                    ? 'bg-palette-plum text-palette-peach font-semibold shadow-sm ring-1 ring-palette-rose'
                    : 'bg-surface-container/70 hover:bg-surface-container-high text-on-surface-variant'
                }`}
                title={doc.filename}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    isSelected ? 'bg-palette-coral' : 'bg-primary'
                  }`}
                />
                <span className="truncate">{doc.filename}</span>
              </button>
            );
          })}
        </div>

        <div className="hidden xl:flex items-center gap-space-sm flex-shrink-0">
          <span className="font-citation-code text-citation-code text-outline bg-surface-container-high px-space-sm py-0.5 rounded">
            Ledger #4092-B · {documents.length} registered
          </span>
        </div>
      </div>

      {/* Main Workspace Split: Thread on Left, Source Drawer on Right */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Central Synthesis & Thread Column */}
        <section className="flex-1 flex flex-col h-full min-w-0 bg-transparent relative overflow-hidden">
          {/* Scrollable Ledger Thread Area */}
          <div
            className="flex-1 overflow-y-auto px-gutter-desktop py-space-xl flex flex-col items-center"
            id="threadScrollArea"
          >
            <div className="w-full max-w-[760px] flex flex-col gap-space-xl">
              {/* Telemetry banner if contexts are active */}
              {totalPassagesCount > 0 && (
                <div className="flex items-center justify-between px-space-lg py-space-sm rounded-lg bg-surface-container-low border border-surface-container-high text-on-surface shadow-sm">
                  <div className="flex items-center gap-space-sm">
                    <span className="material-symbols-outlined text-[18px] text-primary">inventory_2</span>
                    <span className="font-ui-label-md text-ui-label-md font-medium text-on-surface">
                      {totalPassagesCount} evidentiary passages retrieved from {uniqueDocsCount} {uniqueDocsCount === 1 ? 'manuscript' : 'manuscripts'}
                    </span>
                  </div>
                  <div className="flex items-center gap-space-xs font-citation-code text-citation-code text-primary font-semibold">
                    <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    <span>SYNTHESIS GROUNDED</span>
                  </div>
                </div>
              )}

              {/* Message List or Empty State */}
              {messages.length === 0 ? (
                <div className="my-auto py-12 flex flex-col items-center text-center max-w-lg mx-auto">
                  <div className="w-14 h-14 rounded-2xl bg-surface-container flex items-center justify-center text-primary shadow-sm mb-space-md ring-1 ring-border">
                    <span className="material-symbols-outlined text-[28px] text-palette-plum">menu_book</span>
                  </div>
                  <h2 className="font-headline-lg text-headline-lg font-normal text-primary">
                    The Reading Desk
                  </h2>
                  <p className="mt-2 text-body-md text-body-md text-on-surface-variant leading-relaxed">
                    Consult your ingested manuscripts with strict lexical and semantic grounding. Every claim is cross-referenced with verbatim source excerpts.
                  </p>

                  {documents.length === 0 ? (
                    <div className="mt-6 p-space-md bg-palette-peach/20 border border-palette-coral/40 rounded-xl text-left max-w-md shadow-sm">
                      <div className="flex items-center gap-2 text-primary font-semibold mb-1">
                        <span className="material-symbols-outlined text-[18px] text-palette-plum">warning</span>
                        <span className="font-ui-label-md text-ui-label-md">No manuscripts indexed yet</span>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">
                        Please{' '}
                        <button
                          onClick={onNavigateToLibrary}
                          className="text-palette-plum hover:text-palette-rose underline font-semibold transition-colors"
                        >
                          ingest your documents in the library
                        </button>{' '}
                        before starting synthesis inquiries.
                      </p>
                    </div>
                  ) : (
                    <div className="mt-8 w-full space-y-2 text-left">
                      <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-widest text-outline px-1">
                        Suggested Inquiries from Indexed Corpus:
                      </span>
                      <div className="space-y-2 pt-1">
                        {SAMPLE_QUESTIONS.map((q) => (
                          <button
                            key={q}
                            onClick={() => {
                              setInput(q);
                              handleSend(q);
                            }}
                            className="w-full text-left p-3.5 bg-surface-container-lowest border border-surface-container-high hover:border-palette-rose/60 hover:bg-surface-container-low rounded-xl transition-all text-on-surface font-body-sm text-body-sm flex items-center justify-between group shadow-sm"
                          >
                            <span className="font-medium text-ink group-hover:text-primary transition-colors">
                              {q}
                            </span>
                            <span className="material-symbols-outlined text-[16px] text-palette-rose opacity-0 group-hover:opacity-100 transition-opacity">
                              arrow_forward
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-6 pb-6">
                  {messages.map((msg) => (
                    <MessageBlock
                      key={msg.id}
                      message={msg}
                      selectedCitationIndex={selectedIndex}
                      onCitationClick={handleCitationClick}
                      onPreviewDocument={(docId) => setPreviewDocId(docId)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Centered Archival Composer Bar */}
          <div className="w-full flex justify-center pb-4 pt-1 px-4 z-20 flex-shrink-0 bg-gradient-to-t from-background via-background/95 to-transparent">
            <Composer
              input={input}
              setInput={setInput}
              onSubmit={handleSubmit}
              isStreaming={isStreaming}
              onCancel={handleStop}
              options={options}
              onOptionsChange={setOptions}
              showOptions={showOptions}
              setShowOptions={setShowOptions}
              activeDocFilter={selectedScope !== 'all' ? selectedScope : null}
              documents={documents}
              sessions={sessions}
              attachments={attachments}
              onAddAttachment={handleAddAttachment}
              onRemoveAttachment={handleRemoveAttachment}
              onUploadFile={onUploadFile}
              onPreviewDocument={(docId) => setPreviewDocId(docId)}
            />
          </div>
        </section>

        {/* Slide-in Evidentiary Source Drawer */}
        <SourceDrawer
          passages={activeContexts}
          selectedIndex={selectedIndex}
          isOpen={isDrawerOpen && activeContexts.length > 0}
          onClose={() => setIsDrawerOpen(false)}
          onSelectIndex={(idx) => setSelectedIndex(idx)}
        />
      </div>

      {/* Manuscript Dossier / Document Preview Modal */}
      <DocumentPreviewModal
        docId={previewDocId}
        onClose={() => setPreviewDocId(null)}
      />
    </div>
  );
};
