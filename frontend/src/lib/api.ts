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

  upload: async (file: File): Promise<UploadedFile> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE}/upload`, { method: 'POST', body: formData })
    if (!res.ok) throw new Error('Upload failed')
    return res.json()
  },

  listFiles: () => request<{ files: UploadedFile[] }>('/files'),

  listCards: (params?: { page?: number; page_size?: number; source_type?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    if (params?.source_type) qs.set('source_type', params.source_type)
    return request<{ total: number; items: Card[] }>(`/cards?${qs}`)
  },
}
