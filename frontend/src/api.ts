import { DocumentRecord, EvalRunRecord, GoldenItem, QueryOptions, QueryResponse } from './types';

const API_BASE = '/v1';

export async function getHealth(): Promise<{ status: string; indexed_chunks: number }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to fetch health status');
  return res.json();
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentRecord> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function deleteDocument(docId: string): Promise<{ status: string; doc_id: string }> {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
  return res.json();
}

export function getDocumentDownloadUrl(docId: string): string {
  return `${API_BASE}/documents/${docId}/download`;
}

export async function previewDocument(docId: string): Promise<{
  doc_id: string;
  filename: string;
  pages: number;
  mime: string;
  checksum: string;
  uploaded_at: string;
  status: string;
  chunks_count: number;
  preview_text: string;
}> {
  const res = await fetch(`${API_BASE}/documents/${docId}/preview`);
  if (!res.ok) throw new Error('Failed to retrieve document preview');
  return res.json();
}

export async function queryQA(
  question: string,
  options?: QueryOptions
): Promise<QueryResponse> {
  const payload = {
    question,
    k: options?.k ?? 5,
    filters: options?.filters,
    hybrid_enabled: options?.hybrid_enabled,
    reranker_enabled: options?.reranker_enabled,
    query_transform_strategy: options?.query_transform_strategy,
  };
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Query execution failed');
  return res.json();
}

export function streamQueryQA(
  question: string,
  options: QueryOptions | undefined,
  onToken: (token: string) => void,
  onComplete: (data: QueryResponse) => void,
  onError: (err: Error) => void,
  signal?: AbortSignal
): void {
  const payload = {
    question,
    k: options?.k ?? 5,
    filters: options?.filters,
    hybrid_enabled: options?.hybrid_enabled,
    reranker_enabled: options?.reranker_enabled,
    query_transform_strategy: options?.query_transform_strategy,
  };
  fetch(`${API_BASE}/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No readable stream available');

      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          const trimmed = event.trim();
          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.slice(6);
            try {
              const data = JSON.parse(jsonStr);
              if (data.done) {
                onComplete(data as QueryResponse);
              } else if (data.token) {
                onToken(data.token);
              }
            } catch (e) {
              console.error('Failed to parse SSE payload:', e, jsonStr);
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    });
}

export async function listGoldenItems(split?: string): Promise<GoldenItem[]> {
  const url = split ? `${API_BASE}/golden?split=${split}` : `${API_BASE}/golden`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch golden items');
  return res.json();
}

export async function triggerEvalRun(split: string = 'train', topK: number = 5): Promise<any> {
  const res = await fetch(`${API_BASE}/eval/run?split=${split}&top_k=${topK}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to trigger eval run');
  return res.json();
}

export async function listEvalRuns(): Promise<EvalRunRecord[]> {
  const res = await fetch(`${API_BASE}/eval/runs`);
  if (!res.ok) throw new Error('Failed to fetch eval runs');
  return res.json();
}

