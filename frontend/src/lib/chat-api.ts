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

export interface ChatSession {
  id: string
  title: string
  mode: string
  status: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  intent?: string
  cards?: ChatCard[]
  thinking_text?: string
  created_at: string
}

export interface ChatCard {
  card_id: string
  title: string
  body: string
  doc_file: string
  source_type: string
  brand?: string
  hit_rate: number
}

export const chatApi = {
  createSession: (data?: { title?: string; mode?: string }) =>
    request<ChatSession>('/chat/sessions', { method: 'POST', body: JSON.stringify(data || {}) }),

  listSessions: (status = 'active') =>
    request<{ items: ChatSession[]; total: number }>(`/chat/sessions?status=${status}`),

  getSession: (id: string) =>
    request<ChatSession & { messages: ChatMessage[] }>(`/chat/sessions/${id}`),

  updateSession: (id: string, data: Partial<ChatSession>) =>
    request<ChatSession>(`/chat/sessions/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  deleteSession: (id: string) =>
    request(`/chat/sessions/${id}`, { method: 'DELETE' }),

  archiveSession: (id: string) =>
    request(`/chat/sessions/${id}/archive`, { method: 'POST' }),

  sendMessage: (sessionId: string, content: string, modeOverride?: string, signal?: AbortSignal) =>
    fetch(`${BASE}/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, mode_override: modeOverride }),
      signal,
    }),
}
