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

export interface LLMProfile {
  base_url?: string
  api_key?: string
  model?: string
}

export interface SystemConfig {
  llm_api_key?: string
  llm_base_url?: string
  llm_model?: string
  llm_profiles?: Record<string, LLMProfile>
  embedding_model?: string
  max_section_chars?: number
  max_file_size_mb?: number
  route_learning_enabled?: boolean
  cache_evict_days?: number
  cache_max_entries?: number
}

export interface Project {
  id: string
  customer_name: string
  industry: string
  stage: string
  deployment_type: string
  description: string
  owner: string
  created_at: string
  updated_at: string
  archived_at: string | null
}

export interface TenderRequirement {
  id: string
  requirement_type: string
  raw_text: string
  target_models: string[]
  required_capabilities: string[]
  required_evidence: string[]
}

export interface Template {
  id: string
  template_type: string
  name: string
  industry: string
  deployment_type: string
  file_path: string
  schema_json: string
  enabled: number
  created_at: string
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

  feedback: (card_id: string, feedback: 'positive' | 'negative', query_text?: string) =>
    request('/feedback', {
      method: 'POST',
      body: JSON.stringify({ card_id, feedback, query_text }),
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

  // Projects
  listProjects: (params?: { page?: number; page_size?: number; stage?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    if (params?.stage) qs.set('stage', params.stage)
    return request<{ total: number; page: number; page_size: number; items: Project[] }>(`/projects?${qs}`)
  },

  getProject: (projectId: string) => request<Project>(`/projects/${projectId}`),

  createProject: (data: { customer_name: string; industry?: string; stage?: string; deployment_type?: string; description?: string }) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),

  updateProject: (projectId: string, data: Partial<Project>) =>
    request<Project>(`/projects/${projectId}`, { method: 'PUT', body: JSON.stringify(data) }),

  archiveProject: (projectId: string) =>
    request<{ status: string; id: string }>(`/projects/${projectId}/archive`, { method: 'POST' }),

  // Proposals
  generateProposal: (data: { project_id: string; title: string; customer_context?: string; industry?: string; deployment_type?: string; evidences?: unknown[] }) =>
    request<Record<string, unknown>>('/proposals/generate', { method: 'POST', body: JSON.stringify(data) }),

  // Tender
  analyzeTender: (data: { tender_text: string; project_id?: string }) =>
    request<{ total: number; requirements: TenderRequirement[] }>('/tender/analyze', { method: 'POST', body: JSON.stringify(data) }),

  matchTender: (data: { project_id?: string; requirement_ids?: string[]; candidate_models?: string[] }) =>
    request<{ total: number; results: unknown[] }>('/tender/match', { method: 'POST', body: JSON.stringify(data) }),

  // BOM
  generateBom: (data: { project_id: string; scenario?: string; room_count?: number; deployment_type?: string; required_models?: string[]; budget_limit?: number }) =>
    request<Record<string, unknown>>('/bom/generate', { method: 'POST', body: JSON.stringify(data) }),

  // Reply
  generateReply: (data: { customer_question: string; project_id?: string; keywords?: string[]; tone?: string; max_chars?: number }) =>
    request<Record<string, unknown>>('/reply/generate', { method: 'POST', body: JSON.stringify(data) }),

  // Templates
  listTemplates: (params?: { template_type?: string; industry?: string }) => {
    const qs = new URLSearchParams()
    if (params?.template_type) qs.set('template_type', params.template_type)
    if (params?.industry) qs.set('industry', params.industry)
    return request<Template[]>(`/templates?${qs}`)
  },

  createTemplate: (data: { template_type: string; name: string; industry?: string; deployment_type?: string; file_path: string; schema_json?: string; enabled?: number }) =>
    request<Template>('/templates', { method: 'POST', body: JSON.stringify(data) }),

  updateTemplate: (templateId: string, data: Partial<Template>) =>
    request<Template>(`/templates/${templateId}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteTemplate: (templateId: string) =>
    request<{ status: string; id: string }>(`/templates/${templateId}`, { method: 'DELETE' }),

  // Outputs
  reviewOutput: (outputId: string, action: string) =>
    request<{ status: string; output_id: string }>(`/outputs/${outputId}/review`, { method: 'POST', body: JSON.stringify({ action }) }),

  submitFeedback: (outputId: string, data: { feedback_type: string; target_path?: string; before_text?: string; after_text?: string; comment?: string }) =>
    request<{ status: string; feedback_id: string }>(`/outputs/${outputId}/feedback`, { method: 'POST', body: JSON.stringify(data) }),

  // Evidence
  buildEvidence: (data: { card_ids: string[]; task_type: string; project_id?: string }) =>
    request<{ evidence_pack_id: string; evidences: unknown[]; risk_summary: Record<string, unknown> }>('/evidence/build', { method: 'POST', body: JSON.stringify(data) }),

  getProjectEvidence: (projectId: string) =>
    request<unknown[]>(`/evidence/project/${projectId}`),

  // Export
  exportOutput: (outputId: string, format = 'markdown') =>
    request<{ output_id: string; export_path: string; version: number; format: string }>(`/exports/${outputId}`, { method: 'POST', body: JSON.stringify({ format }) }),
}
