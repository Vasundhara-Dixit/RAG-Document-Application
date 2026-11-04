export type DocumentStatus = 'queued' | 'parsing' | 'indexing' | 'ready' | 'failed';

export interface DocumentRecord {
  doc_id: string;
  filename: string;
  mime: string;
  pages: number;
  checksum: string;
  uploaded_at: string;
  status: DocumentStatus;
  error_message?: string;
  tags: string[];
}

export interface Citation {
  citation_index: number;
  doc_id: string;
  filename: string;
  page: number;
  snippet: string;
  chunk_id: string;
}

export interface ChunkRecord {
  chunk_id: string;
  doc_id: string;
  idx: number;
  text: string;
  token_count: number;
  page_start: number;
  page_end: number;
  char_start: number;
  char_end: number;
  section_title?: string;
  embedding_model: string;
  config_hash: string;
}

export interface RetrievedPassage {
  chunk: ChunkRecord;
  score: number;
  rank: number;
}

export interface TimingBreakdown {
  retrieval_ms: number;
  generation_ms: number;
  total_ms: number;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  contexts: RetrievedPassage[];
  timings: TimingBreakdown;
  trace_id: string;
  abstained: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  contexts?: RetrievedPassage[];
  timings?: TimingBreakdown;
  abstained?: boolean;
  isStreaming?: boolean;
  attachments?: AttachmentReference[];
}

export interface EvalMetrics {
  hit_at_1: number;
  hit_at_3: number;
  hit_at_5: number;
  hit_at_10: number;
  mrr: number;
  faithfulness?: number;
  correctness?: number;
  completeness?: number;
}

export interface EvalRunRecord {
  run_id: string;
  config_hash: string;
  dataset_version: string;
  split?: string;
  metrics: EvalMetrics;
  latency_p50_ms: number;
  latency_p95_ms: number;
  cost_usd: number;
  timestamp: string;
  notes?: string;
}

export interface GoldenItem {
  id: string;
  question: string;
  reference_answer: string;
  doc_id: string;
  page: number;
  type: string;
  split: string;
  version: string;
}

export interface QueryOptions {
  k?: number;
  filters?: Record<string, any>;
  hybrid_enabled?: boolean;
  reranker_enabled?: boolean;
  query_transform_strategy?: string;
}

export interface AttachmentReference {
  type: 'file_upload' | 'manuscript' | 'past_chat';
  id: string;
  title: string;
  snippet?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
  contexts: RetrievedPassage[];
  referencedDocs?: string[];
}

export interface BackgroundSettings {
  glassEnabled: boolean;
  wallpaperUrl: string | null;
  blurIntensity: 'low' | 'medium' | 'high';
  overlayOpacity: number;
}



