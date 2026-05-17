import { create } from 'zustand'
import { chatApi, type ChatSession, type ChatMessage, type ChatCard } from '@/lib/chat-api'

interface ChatState {
  sessions: ChatSession[]
  currentSessionId: string | null
  messages: ChatMessage[]
  isStreaming: boolean
  streamingThinking: string
  streamingCards: ChatCard[]
  streamingContent: string
  loading: boolean
  _abortController: AbortController | null

  loadSessions: () => Promise<void>
  createSession: () => Promise<string>
  selectSession: (id: string) => Promise<void>
  sendMessage: (content: string, modeOverride?: string) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  archiveSession: (id: string) => Promise<void>
  stopStreaming: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  streamingThinking: '',
  streamingCards: [],
  streamingContent: '',
  loading: false,
  _abortController: null,

  loadSessions: async () => {
    try {
      const data = await chatApi.listSessions()
      set({ sessions: data.items })
    } catch (e) {
      console.error('Failed to load sessions:', e)
    }
  },

  createSession: async () => {
    const session = await chatApi.createSession()
    set((s) => ({ sessions: [session, ...s.sessions], currentSessionId: session.id, messages: [] }))
    return session.id
  },

  selectSession: async (id: string) => {
    set({ loading: true, currentSessionId: id })
    try {
      const data = await chatApi.getSession(id)
      set({ messages: data.messages, loading: false })
    } catch (e) {
      console.error('Failed to load session:', e)
      set({ loading: false })
    }
  },

  sendMessage: async (content: string, modeOverride?: string) => {
    const { currentSessionId, messages } = get()
    if (!currentSessionId || get().isStreaming) return

    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: currentSessionId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    set({
      messages: [...messages, userMsg],
      isStreaming: true,
      streamingThinking: '',
      streamingCards: [],
      streamingContent: '',
    })

    const abortController = new AbortController()
    set({ _abortController: abortController })

    try {
      const resp = await chatApi.sendMessage(currentSessionId, content, modeOverride, abortController.signal)
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`)
      }

      const reader = resp.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7)
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const parsed = JSON.parse(data)
              if (currentEvent === 'thinking') {
                set({ streamingThinking: parsed.detail || '' })
              } else if (currentEvent === 'cards') {
                set({ streamingCards: parsed.cards || [] })
              } else if (currentEvent === 'text') {
                set((s) => ({ streamingContent: s.streamingContent + (parsed.delta || '') }))
              } else if (currentEvent === 'done') {
                // finalize
              }
            } catch { /* ignore parse errors */ }
          }
        }
      }

      // Finalize: create assistant message
      const { streamingContent, streamingCards, streamingThinking } = get()
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        session_id: currentSessionId,
        role: 'assistant',
        content: streamingContent,
        cards: streamingCards,
        thinking_text: streamingThinking,
        created_at: new Date().toISOString(),
      }
      set((s) => ({
        messages: [...s.messages, assistantMsg],
        isStreaming: false,
        streamingThinking: '',
        streamingCards: [],
        streamingContent: '',
        _abortController: null,
      }))

      // Refresh session title if it changed
      get().loadSessions()
    } catch (e: unknown) {
      if (e instanceof Error && e.name === 'AbortError') {
        // User stopped streaming — finalize with what we have
        const { streamingContent, streamingCards } = get()
        if (streamingContent || streamingCards.length > 0) {
          const assistantMsg: ChatMessage = {
            id: `msg-${Date.now()}`,
            session_id: currentSessionId,
            role: 'assistant',
            content: streamingContent,
            cards: streamingCards,
            created_at: new Date().toISOString(),
          }
          set((s) => ({ messages: [...s.messages, assistantMsg] }))
        }
      } else {
        console.error('Stream error:', e)
      }
      set({ isStreaming: false, streamingThinking: '', streamingCards: [], streamingContent: '', _abortController: null })
    }
  },

  deleteSession: async (id: string) => {
    await chatApi.deleteSession(id)
    set((s) => ({
      sessions: s.sessions.filter((x) => x.id !== id),
      currentSessionId: s.currentSessionId === id ? null : s.currentSessionId,
      messages: s.currentSessionId === id ? [] : s.messages,
    }))
  },

  archiveSession: async (id: string) => {
    await chatApi.archiveSession(id)
    set((s) => ({
      sessions: s.sessions.filter((x) => x.id !== id),
      currentSessionId: s.currentSessionId === id ? null : s.currentSessionId,
      messages: s.currentSessionId === id ? [] : s.messages,
    }))
  },

  stopStreaming: () => {
    const { _abortController } = get()
    if (_abortController) {
      _abortController.abort()
    }
    set({ isStreaming: false })
  },
}))
