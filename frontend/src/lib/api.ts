const BASE = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// Types
export interface SearchResult {
  rank: number
  card_id: string
  title: string
  body: string
  source_type: string
  source_file: string
  path: string
  hit_rate: number
  intent_tags: string[]
  quality_tier: string
  doc_file: string
}

export interface QueryResponse {
  query: string
  route: string
  cache_hit: boolean
  latency_ms: number
  results: SearchResult[]
  total: number
}

export interface HealthResponse {
  status: string
  version: string
  checks: Record<string, unknown>
  latency_ms: number
}

export interface UploadedFile {
  id: string
  filename: string
  file_type: string
  file_size: number
  cards_count: number
  pipeline_status: string
  created_at: string
}

export interface UploadedDocument {
  id: number
  filename: string
  file_type: string
  file_size: number
  sha256: string
  cards_count: number
  pipeline_status: string
  is_current: number
  created_at: string
}

export interface Card {
  id: string
  title: string
  body: string
  path: string
  source_type: string
  doc_file: string
  quality_tier: string
  intent_tags: string[]
  updated_at: string
}

export interface CardDetail {
  id: string
  doc_file: string
  source_type: string
  title: string
  body: string
  path: string
  keywords: string
  intent_tags: string
  quality_tier: string
  hit_count: number
  miss_count: number
  char_count: number
  created_at: string
  updated_at: string
}

export interface CardStats {
  total: number
  by_source_type: Record<string, number>
  by_quality_tier: Record<string, number>
}

export interface IndexStatus {
  index_builds: { index_bm25: number; index_vector: number; index_fts5: number }
  pending_jobs: number
}

export interface Job {
  id: number
  job_type: string
  status: string
  progress: number
  total_items: number
  error_message: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface SystemConfig {
  llm_api_key?: string
  llm_base_url?: string
  llm_model?: string
  embedding_model?: string
  max_section_chars?: number
  max_file_size_mb?: number
  route_learning_enabled?: boolean
  cache_evict_days?: number
  cache_max_entries?: number
}

// API functions
export const api = {
  health: () => request<HealthResponse>('/health'),

  query: (q: string, opts?: { page?: number; page_size?: number; include_low_quality?: boolean }) =>
    request<QueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify({ query: q, ...opts }),
    }),

  feedback: (card_id: string, rating: 'positive' | 'negative', reason?: string) =>
    request('/feedback', {
      method: 'POST',
      body: JSON.stringify({ card_id, rating, reason }),
    }),

  // Upload
  uploadFile: async (file: File, forceOverwrite = false) => {
    const formData = new FormData()
    formData.append('file', file)
    if (forceOverwrite) formData.append('force_overwrite', 'true')
    const res = await fetch(`${BASE}/upload`, { method: 'POST', body: formData })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(error.detail || `HTTP ${res.status}`)
    }
    return res.json()
  },

  listDocuments: (params?: { page?: number; page_size?: number; file_type?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    if (params?.file_type) qs.set('file_type', params.file_type)
    return request<{ total: number; page: number; page_size: number; items: UploadedDocument[] }>(`/upload/documents?${qs}`)
  },

  deleteDocument: (docId: number) =>
    request<{ status: string; id: number }>(`/upload/documents/${docId}`, { method: 'DELETE' }),

  reprocessDocument: (docId: number) =>
    request<{ status: string; document_id: number; jobs_created: number }>(`/upload/documents/${docId}/reprocess`, { method: 'POST' }),

  // Cards
  listCards: (params?: { page?: number; page_size?: number; source_type?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    if (params?.source_type) qs.set('source_type', params.source_type)
    return request<{ total: number; items: Card[] }>(`/cards?${qs}`)
  },

  getCardStats: () => request<CardStats>('/cards/stats'),

  getCard: (cardId: string) => request<CardDetail>(`/cards/${cardId}`),

  updateCard: (cardId: string, data: { title?: string; body?: string; tags?: string; keywords?: string }) =>
    request<{ status: string; id: string }>(`/cards/${cardId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteCard: (cardId: string) =>
    request<{ status: string; id: string }>(`/cards/${cardId}`, { method: 'DELETE' }),

  // Indexes
  getIndexStatus: () => request<IndexStatus>('/indexes/status'),

  rebuildIndex: (indexType: string) =>
    request<{ status: string; index_type: string; job_ids: number[] }>(`/indexes/rebuild/${indexType}`, { method: 'POST' }),

  annotateCards: (scope = 'all') =>
    request<{ status: string; job_id: number }>(`/indexes/annotate?scope=${scope}`, { method: 'POST' }),

  // Jobs
  listJobs: (params?: { status?: string; type?: string; page?: number; page_size?: number }) => {
    const qs = new URLSearchParams()
    if (params?.status) qs.set('status', params.status)
    if (params?.type) qs.set('type', params.type)
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    return request<{ total: number; page: number; page_size: number; items: Job[] }>(`/jobs?${qs}`)
  },

  retryJob: (jobId: number) =>
    request<{ status: string; job_id: number }>(`/jobs/${jobId}/retry`, { method: 'POST' }),

  // Config
  getConfig: () => request<SystemConfig>('/config'),

  updateConfig: (data: Partial<SystemConfig>) =>
    request<{ status: string; config: SystemConfig }>('/config', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
}
