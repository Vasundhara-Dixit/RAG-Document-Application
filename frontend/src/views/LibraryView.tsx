import React, { useState } from 'react';
import { DocumentRecord } from '../types';
import { UploadDropzone } from '../components/UploadDropzone';
import { DocumentPreviewModal } from '../components/DocumentPreviewModal';
import { deleteDocument, uploadDocument, getDocumentDownloadUrl } from '../api';

interface LibraryViewProps {
  documents: DocumentRecord[];
  onRefresh: () => Promise<void>;
}

export const LibraryView: React.FC<LibraryViewProps> = ({
  documents,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortFilter, setSortFilter] = useState<'date' | 'pages' | 'title'>('date');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState<File | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteDoc, setConfirmDeleteDoc] = useState<DocumentRecord | null>(null);
  const [inspectedDoc, setInspectedDoc] = useState<DocumentRecord | null>(null);
  const [previewDocId, setPreviewDocId] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setUploadingFile(file);
    try {
      await uploadDocument(file);
      await onRefresh();
    } finally {
      setIsUploading(false);
      setUploadingFile(null);
    }
  };

  const executeDelete = async (docId: string) => {
    setDeletingId(docId);
    try {
      await deleteDocument(docId);
      await onRefresh();
      setConfirmDeleteDoc(null);
    } catch (e: any) {
      alert(`Deletion failed: ${e.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const handleExportManifest = () => {
    const jsonlContent = documents
      .map((doc) =>
        JSON.stringify({
          doc_id: doc.doc_id,
          filename: doc.filename,
          mime: doc.mime,
          pages: doc.pages,
          checksum: doc.checksum,
          uploaded_at: doc.uploaded_at,
          status: doc.status,
          tags: doc.tags,
        })
      )
      .join('\n');

    const blob = new Blob([jsonlContent], { type: 'application/x-ndjson;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `corpus_manifest_${new Date().toISOString().slice(0, 10)}.jsonl`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Filter and sort documents
  const filteredDocs = documents
    .filter((doc) => {
      const matchesSearch =
        doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.checksum.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.tags?.some((t) => t.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (sortFilter === 'date') {
        return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime();
      }
      if (sortFilter === 'pages') {
        return b.pages - a.pages;
      }
      if (sortFilter === 'title') {
        return a.filename.localeCompare(b.filename);
      }
      return 0;
    });

  // Calculate stats
  const totalPages = documents.reduce((acc, d) => acc + (d.pages || 1), 0);
  const estimatedChunks = totalPages * 8;
  const estimatedMB = (totalPages * 0.12).toFixed(1);

  return (
    <div className="flex-1 overflow-y-auto bg-transparent min-h-screen">
      <div className="max-w-[1280px] w-full mx-auto px-gutter-desktop py-space-xl flex flex-col gap-space-xl">
        {/* Top Ledger Banner: Corpus Library Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-lg pb-space-lg border-b border-surface-container-high">
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center gap-space-sm">
              <span className="font-citation-code text-citation-code text-palette-plum uppercase tracking-widest bg-palette-peach/30 px-2 py-0.5 rounded font-semibold">
                Archive Ledger / A-1
              </span>
              <span className="font-ui-label-sm text-ui-label-sm text-outline">Vol. XXIV</span>
            </div>
            <h1 className="font-headline-xl text-headline-xl text-primary tracking-tight font-normal">
              Corpus Library
            </h1>
            <p className="font-body-md text-body-md text-on-surface-variant">
              {documents.length} manuscripts indexed ·{' '}
              <span className="font-code-md text-code-md text-on-surface font-semibold">
                ~{estimatedChunks.toLocaleString()}
              </span>{' '}
              retrieval chunks ·{' '}
              <span className="font-code-md text-code-md text-on-surface font-semibold">
                ~{estimatedMB} MB
              </span>{' '}
              storage footprint
            </p>
          </div>

          <div className="flex items-center gap-space-md flex-shrink-0">
            <button
              onClick={handleExportManifest}
              disabled={documents.length === 0}
              className="flex items-center gap-space-xs px-space-md py-2.5 rounded-lg bg-surface-container-low text-on-surface font-ui-label-lg text-ui-label-lg shadow-sm hover:bg-surface-container border border-surface-container-high transition-all disabled:opacity-50"
              title="Download JSONL manifest of indexed manuscripts"
            >
              <span className="material-symbols-outlined text-[18px] text-palette-plum">file_download</span>
              <span>Manifest (.jsonl)</span>
            </button>

            <button
              onClick={() => {
                const el = document.getElementById('fileUploadInput');
                if (el) el.click();
              }}
              className="flex items-center gap-space-xs px-space-lg py-2.5 rounded-lg bg-primary text-on-primary font-ui-label-lg text-ui-label-lg shadow hover:bg-palette-wine transition-all"
            >
              <span className="material-symbols-outlined text-[20px]">upload_file</span>
              <span>Upload Documents</span>
            </button>
          </div>
        </div>

        {/* Active Upload & Ingestion Stage */}
        <UploadDropzone
          onUpload={handleUpload}
          isUploading={isUploading}
          activeFile={uploadingFile}
        />

        {/* Corpus Filter Ledger Bar */}
        <div className="bg-surface-container-lowest border border-surface-container-high rounded-xl p-space-md shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-space-md">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[280px]">
            <span className="material-symbols-outlined text-[18px] text-outline absolute left-3 top-1/2 -translate-y-1/2">
              search
            </span>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter by filename, checksum, or tag..."
              className="w-full bg-surface-container-low/50 pl-10 pr-4 py-2 rounded-lg text-on-surface font-body-sm text-body-sm placeholder:italic placeholder:text-outline focus:outline-none focus:bg-surface-container-low border border-surface-container-high transition-colors"
            />
          </div>

          {/* Controls & Filter Dropdowns */}
          <div className="flex items-center gap-space-sm flex-wrap sm:flex-nowrap">
            <div className="flex items-center gap-1.5 bg-surface-container-low/80 px-space-sm py-1.5 rounded-lg border border-surface-container-high">
              <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
                Status:
              </span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-transparent font-ui-label-md text-ui-label-md text-on-surface focus:outline-none cursor-pointer pr-1"
              >
                <option value="all">All statuses ({documents.length})</option>
                <option value="ready">Ready</option>
                <option value="indexing">Indexing</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 bg-surface-container-low/80 px-space-sm py-1.5 rounded-lg border border-surface-container-high">
              <span className="font-ui-label-sm text-ui-label-sm uppercase tracking-wider text-outline font-semibold">
                Sort:
              </span>
              <select
                value={sortFilter}
                onChange={(e) => setSortFilter(e.target.value as any)}
                className="bg-transparent font-ui-label-md text-ui-label-md text-on-surface focus:outline-none cursor-pointer pr-1"
              >
                <option value="date">Date Ingested</option>
                <option value="pages">Extent (Pages)</option>
                <option value="title">Manuscript Title</option>
              </select>
            </div>

            <button
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('all');
                setSortFilter('date');
              }}
              className="px-space-sm py-1.5 text-outline hover:text-on-surface font-ui-label-sm text-ui-label-sm flex items-center gap-1 transition-colors"
            >
              <span className="material-symbols-outlined text-[15px]">refresh</span>
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Document Ledger Table */}
        <div className="bg-surface-container-lowest border border-surface-container-high rounded-xl shadow-sm overflow-hidden flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-high/50 font-ui-label-sm text-ui-label-sm uppercase tracking-widest text-outline border-b border-surface-container-high">
                  <th className="py-space-md px-space-lg font-semibold w-5/12">Manuscript</th>
                  <th className="py-space-md px-space-md font-semibold text-center w-1/12">Format</th>
                  <th className="py-space-md px-space-md font-semibold text-right w-1/12">Extent</th>
                  <th className="py-space-md px-space-md font-semibold text-right w-1/12">Est. Chunks</th>
                  <th className="py-space-md px-space-md font-semibold w-2/12 whitespace-nowrap">Ingested</th>
                  <th className="py-space-md px-space-md font-semibold w-1/12">Status</th>
                  <th className="py-space-md px-space-lg font-semibold text-right w-1/12">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-high font-body-sm text-body-sm text-on-surface">
                {filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-on-surface-variant font-body-md text-body-md">
                      {documents.length === 0
                        ? 'No manuscripts registered in the repository yet. Drag and drop files above to ingest.'
                        : 'No manuscripts match the active filter criteria.'}
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => {
                    const ext = doc.filename.split('.').pop()?.toUpperCase() || 'TXT';
                    const chunksForDoc = doc.pages ? doc.pages * 8 : 8;
                    const formattedDate = new Date(doc.uploaded_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    });

                    return (
                      <tr
                        key={doc.doc_id}
                        className="hover:bg-surface-container-low/60 transition-colors group cursor-pointer"
                        onClick={() => setInspectedDoc(doc)}
                      >
                        {/* Title & Checksum */}
                        <td className="py-space-md px-space-lg">
                          <div className="flex items-center gap-space-sm">
                            <div className="w-8 h-8 rounded-lg bg-surface-container flex items-center justify-center flex-shrink-0 text-palette-plum group-hover:bg-palette-plum group-hover:text-palette-peach transition-colors shadow-sm">
                              <span className="material-symbols-outlined text-[18px]">description</span>
                            </div>
                            <div className="flex flex-col min-w-0">
                              <span className="font-headline-md text-[16px] text-on-surface font-medium truncate group-hover:text-primary transition-colors">
                                {doc.filename}
                              </span>
                              <span className="font-citation-code text-citation-code text-outline truncate">
                                SHA-256: {doc.checksum.slice(0, 12)}…
                              </span>
                            </div>
                          </div>
                        </td>

                        {/* Format Pill */}
                        <td className="py-space-md px-space-md text-center">
                          <span className="font-citation-code text-[11px] font-semibold text-palette-plum bg-palette-peach/40 px-2 py-0.5 rounded uppercase">
                            {ext}
                          </span>
                        </td>

                        {/* Extent */}
                        <td className="py-space-md px-space-md text-right font-code-md text-code-md text-on-surface">
                          {doc.pages} p.
                        </td>

                        {/* Chunks */}
                        <td className="py-space-md px-space-md text-right font-code-md text-code-md text-palette-plum font-semibold">
                          ~{chunksForDoc}
                        </td>

                        {/* Ingested */}
                        <td className="py-space-md px-space-md font-code-md text-code-md text-outline whitespace-nowrap">
                          {formattedDate}
                        </td>

                        {/* Status Badge */}
                        <td className="py-space-md px-space-md">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-citation-code text-[11px] font-medium ${
                              doc.status === 'ready'
                                ? 'bg-primary/10 text-primary'
                                : doc.status === 'failed'
                                ? 'bg-palette-rose/15 text-palette-rose'
                                : 'bg-palette-peach/40 text-palette-plum'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                doc.status === 'ready'
                                  ? 'bg-primary'
                                  : doc.status === 'failed'
                                  ? 'bg-palette-rose'
                                  : 'bg-palette-plum animate-pulse'
                              }`}
                            />
                            {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                          </span>
                        </td>

                        {/* Actions */}
                        <td
                          className="py-space-md px-space-lg text-right"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => setPreviewDocId(doc.doc_id)}
                              className="p-1.5 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors"
                              title="Preview manuscript text"
                            >
                              <span className="material-symbols-outlined text-[18px]">visibility</span>
                            </button>
                            <a
                              href={getDocumentDownloadUrl(doc.doc_id)}
                              download={doc.filename}
                              className="p-1.5 rounded hover:bg-surface-container text-outline hover:text-palette-plum transition-colors inline-flex items-center justify-center"
                              title="Download original file"
                            >
                              <span className="material-symbols-outlined text-[18px]">download</span>
                            </a>
                            <button
                              onClick={() => setInspectedDoc(doc)}
                              className="p-1.5 rounded hover:bg-surface-container text-outline hover:text-primary transition-colors"
                              title="Inspect manuscript metadata"
                            >
                              <span className="material-symbols-outlined text-[18px]">info</span>
                            </button>
                            <button
                              onClick={() => setConfirmDeleteDoc(doc)}
                              disabled={deletingId === doc.doc_id}
                              className="p-1.5 rounded hover:bg-palette-rose/10 text-outline hover:text-palette-rose transition-colors disabled:opacity-50"
                              title="Delete manuscript and purge chunks"
                            >
                              <span className="material-symbols-outlined text-[18px]">delete</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {confirmDeleteDoc && (
        <div className="fixed inset-0 bg-palette-eggplant/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest border border-surface-container-high rounded-xl max-w-md w-full p-space-xl shadow-2xl flex flex-col gap-space-md animate-in fade-in zoom-in-95">
            <div className="flex items-start gap-space-md">
              <div className="w-10 h-10 rounded-full bg-palette-rose/15 text-palette-rose flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[24px]">delete_forever</span>
              </div>
              <div className="flex flex-col min-w-0">
                <h3 className="font-headline-md text-headline-md text-primary font-normal">
                  Purge Manuscript?
                </h3>
                <p className="mt-1 text-body-sm text-body-sm text-on-surface-variant">
                  Are you certain you wish to purge <span className="font-semibold text-on-surface font-sans">“{confirmDeleteDoc.filename}”</span>? All associated semantic chunk vectors and lexical inverted indexes will be permanently deleted.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-space-sm pt-space-sm border-t border-surface-container-high mt-space-sm">
              <button
                onClick={() => setConfirmDeleteDoc(null)}
                className="px-space-md py-2 rounded-lg font-ui-label-md text-ui-label-md text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => executeDelete(confirmDeleteDoc.doc_id)}
                disabled={deletingId === confirmDeleteDoc.doc_id}
                className="px-space-md py-2 rounded-lg font-ui-label-md text-ui-label-md bg-palette-plum text-palette-peach hover:bg-palette-wine transition-colors font-semibold shadow-sm flex items-center gap-1.5"
              >
                {deletingId === confirmDeleteDoc.doc_id ? (
                  <>
                    <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                    <span>Purging...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[16px]">delete</span>
                    <span>Confirm Purge</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manuscript Metadata Inspector Modal */}
      {inspectedDoc && (
        <div className="fixed inset-0 bg-palette-eggplant/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest border border-surface-container-high rounded-xl max-w-lg w-full p-space-xl shadow-2xl flex flex-col gap-space-md animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-space-sm border-b border-surface-container-high">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-[20px] text-palette-plum">description</span>
                <span className="font-headline-md text-headline-md text-primary font-normal">
                  Manuscript Dossier
                </span>
              </div>
              <button
                onClick={() => setInspectedDoc(null)}
                className="w-8 h-8 rounded-lg hover:bg-surface-container flex items-center justify-center text-outline hover:text-on-surface transition-colors"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="flex flex-col gap-space-sm font-citation-code text-citation-code">
              <div className="p-space-sm rounded-lg bg-surface-container-low flex flex-col gap-0.5">
                <span className="font-ui-label-sm text-ui-label-sm uppercase text-outline font-semibold">Title</span>
                <span className="font-headline-md text-[17px] text-on-surface font-medium">{inspectedDoc.filename}</span>
              </div>

              <div className="grid grid-cols-2 gap-space-sm">
                <div className="p-space-sm rounded-lg bg-surface-container-low flex flex-col gap-0.5">
                  <span className="font-ui-label-sm text-ui-label-sm uppercase text-outline font-semibold">Document ID</span>
                  <span className="text-on-surface truncate">{inspectedDoc.doc_id}</span>
                </div>
                <div className="p-space-sm rounded-lg bg-surface-container-low flex flex-col gap-0.5">
                  <span className="font-ui-label-sm text-ui-label-sm uppercase text-outline font-semibold">Extent</span>
                  <span className="text-on-surface">{inspectedDoc.pages} pages</span>
                </div>
              </div>

              <div className="p-space-sm rounded-lg bg-surface-container-low flex flex-col gap-0.5">
                <span className="font-ui-label-sm text-ui-label-sm uppercase text-outline font-semibold">SHA-256 Checksum</span>
                <span className="text-palette-plum select-all break-all">{inspectedDoc.checksum}</span>
              </div>

              <div className="grid grid-cols-2 gap-space-sm">
                <div className="p-space-sm rounded-lg bg-surface-container-low flex flex-col gap-0.5">
                  <span className="font-ui-label-sm text-ui-label-sm uppercase text-outline font-semibold">MIME Format</span>
                  <span className="text-on-surface">{inspectedDoc.mime}</span>
                </div>
                <div className="p-space-sm rounded-lg bg-surface-container-low flex flex-col gap-0.5">
                  <span className="font-ui-label-sm text-ui-label-sm uppercase text-outline font-semibold">Archived Date</span>
                  <span className="text-on-surface">{new Date(inspectedDoc.uploaded_at).toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-space-xs border-t border-surface-container-high">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setPreviewDocId(inspectedDoc.doc_id);
                  }}
                  className="px-3 py-1.5 rounded-lg border border-palette-plum/30 text-palette-plum font-ui-label-md text-ui-label-md hover:bg-palette-plum/10 transition-colors flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">visibility</span>
                  <span>Preview</span>
                </button>
                <a
                  href={getDocumentDownloadUrl(inspectedDoc.doc_id)}
                  download={inspectedDoc.filename}
                  className="px-3 py-1.5 rounded-lg border border-border text-on-surface font-ui-label-md text-ui-label-md hover:bg-surface-container transition-colors inline-flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">download</span>
                  <span>Download</span>
                </a>
              </div>
              <button
                onClick={() => setInspectedDoc(null)}
                className="px-space-md py-2 rounded-lg bg-primary text-on-primary font-ui-label-md text-ui-label-md hover:bg-palette-wine transition-colors"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document Text Preview Modal */}
      <DocumentPreviewModal
        docId={previewDocId}
        onClose={() => setPreviewDocId(null)}
      />
    </div>
  );
};
