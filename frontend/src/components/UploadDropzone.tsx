import React, { useState, useRef } from 'react';

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
  activeFile?: File | null;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({
  onUpload,
  isUploading,
  activeFile,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [lastUploaded, setLastUploaded] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploadError(null);

    // Validate size (25MB limit)
    if (file.size > 25 * 1024 * 1024) {
      setUploadError('Manuscript exceeds the statutory 25 MB archival limit.');
      return;
    }

    // Validate extension
    const validExts = ['.pdf', '.docx', '.md', '.txt'];
    const lowerName = file.name.toLowerCase();
    const hasValidExt = validExts.some((ext) => lowerName.endsWith(ext));
    if (!hasValidExt) {
      setUploadError('Unsupported format. Please upload PDF, DOCX, Markdown (.md), or Plain Text (.txt).');
      return;
    }

    try {
      await onUpload(file);
      setLastUploaded(file.name);
      setTimeout(() => setLastUploaded(null), 4000);
    } catch (e: any) {
      setUploadError(e.message || 'Archival ingestion failed');
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-stretch">
        {/* Left: Ingestion Dropzone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative min-h-[170px] rounded-xl bg-surface-container-lowest border-2 border-dashed p-space-lg flex flex-col justify-center items-center text-center cursor-pointer transition-all shadow-sm group ${
            isUploading ? 'lg:col-span-7' : 'lg:col-span-12'
          } ${
            isDragOver
              ? 'border-palette-rose bg-palette-peach/10 shadow-md ring-2 ring-palette-rose/20'
              : 'border-surface-container-highest hover:border-palette-plum hover:bg-surface-container-low/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.md,.txt"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />

          <div className="w-12 h-12 rounded-full bg-surface-container flex items-center justify-center mb-space-sm text-primary group-hover:scale-105 group-hover:bg-palette-plum group-hover:text-palette-peach transition-all shadow-sm">
            <span className="material-symbols-outlined text-[24px]">note_add</span>
          </div>

          <div className="flex flex-col gap-1 pointer-events-none">
            <span className="font-headline-md text-[18px] text-on-surface">
              Drag &amp; drop PDF, DOCX, or Markdown files here, or{' '}
              <span className="text-primary underline underline-offset-4 decoration-palette-rose/40 font-medium group-hover:text-palette-plum transition-colors">
                browse filesystem
              </span>
            </span>
            <span className="font-ui-label-sm text-ui-label-sm text-outline tracking-wider uppercase mt-0.5">
              Strictly Ingests: PDF, DOCX, MD, TXT (up to 25 MB per manuscript)
            </span>
          </div>
        </div>

        {/* Right: Active Ingestion Progress Card (Shown when isUploading is true) */}
        {isUploading && (
          <div className="lg:col-span-5 bg-surface-container-lowest border border-surface-container-high rounded-xl p-space-lg shadow-sm flex flex-col justify-between">
            <div className="flex items-start justify-between gap-space-md">
              <div className="flex items-center gap-space-sm min-w-0">
                <div className="w-10 h-10 rounded-lg bg-palette-plum text-palette-peach flex items-center justify-center flex-shrink-0 shadow-sm">
                  <span className="material-symbols-outlined text-[22px]">auto_stories</span>
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-space-xs">
                    <span className="font-ui-label-lg text-ui-label-lg text-on-surface truncate font-semibold">
                      {activeFile?.name || 'Ingesting Manuscript...'}
                    </span>
                    {activeFile && (
                      <span className="font-citation-code text-citation-code text-outline flex-shrink-0">
                        · {(activeFile.size / (1024 * 1024)).toFixed(1)} MB
                      </span>
                    )}
                  </div>
                  <span className="font-citation-code text-citation-code text-primary flex items-center gap-1.5 mt-0.5 font-medium">
                    <span className="inline-block w-2 h-2 rounded-full bg-palette-rose animate-ping" />
                    Parsing, Chunking &amp; Vectorizing (Stage 2/3)
                  </span>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-space-xs mt-space-md">
              <div className="flex items-center justify-between font-citation-code text-citation-code">
                <span className="text-on-surface-variant font-medium">Embedding Semantic Vectors</span>
                <span className="text-primary font-bold">Processing chunks (72%)</span>
              </div>
              <div className="w-full h-2.5 bg-surface-container rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-palette-plum via-palette-rose to-palette-coral rounded-full animate-pulse transition-all duration-700 w-3/4" />
              </div>
              <div className="flex items-center justify-between text-outline font-ui-label-sm text-ui-label-sm pt-0.5">
                <span>Recursive Character Stride</span>
                <span>Writing to FAISS / Chroma</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload Error Alert */}
      {uploadError && (
        <div className="mt-space-md flex items-center gap-space-sm p-space-md bg-palette-rose/10 border border-palette-rose/40 rounded-xl text-xs text-primary shadow-sm">
          <span className="material-symbols-outlined text-[18px] text-palette-rose shrink-0">error</span>
          <span className="font-medium">{uploadError}</span>
        </div>
      )}

      {/* Success Notification Alert */}
      {lastUploaded && (
        <div className="mt-space-md flex items-center gap-space-sm p-space-md bg-palette-peach/30 border border-palette-peach rounded-xl text-xs text-primary shadow-sm">
          <span className="material-symbols-outlined text-[18px] text-palette-plum shrink-0">check_circle</span>
          <span className="font-medium">Manuscript successfully archived and indexed: {lastUploaded}</span>
        </div>
      )}
    </div>
  );
};
