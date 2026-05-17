import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useChatStore } from '@/stores/chat'
import { SessionSidebar } from '@/components/chat/session-sidebar'
import { MessageList } from '@/components/chat/message-list'
import { ChatInput } from '@/components/chat/chat-input'

export default function ChatPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const {
    messages, isStreaming, streamingThinking, streamingCards, streamingContent, loading,
    selectSession, sendMessage, createSession, stopStreaming,
  } = useChatStore()

  useEffect(() => {
    if (sessionId) {
      selectSession(sessionId)
    }
  }, [sessionId])

  const handleSend = async (content: string) => {
    if (!sessionId) {
      const id = await createSession()
      navigate(`/chat/${id}`)
      // Wait for state update then send
      setTimeout(() => useChatStore.getState().sendMessage(content), 100)
      return
    }
    sendMessage(content)
  }

  return (
    <div className="flex h-[calc(100vh-48px)] -m-5">
      <SessionSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <MessageList
          messages={messages}
          isStreaming={isStreaming}
          streamingThinking={streamingThinking}
          streamingCards={streamingCards}
          streamingContent={streamingContent}
        />
        <ChatInput
          onSend={handleSend}
          onStop={stopStreaming}
          isStreaming={isStreaming}
          disabled={loading}
        />
      </div>
    </div>
  )
}
