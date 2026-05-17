import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChatStore } from '@/stores/chat'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Plus, MessageSquare, Archive, Trash2, Settings } from 'lucide-react'

interface Props {
  collapsed?: boolean
}

export function SessionSidebar({ collapsed }: Props) {
  const navigate = useNavigate()
  const {
    sessions, currentSessionId, loading,
    loadSessions, createSession, selectSession, deleteSession, archiveSession,
  } = useChatStore()

  useEffect(() => { loadSessions() }, [])

  const handleNew = async () => {
    const id = await createSession()
    navigate(`/chat/${id}`)
  }

  const handleSelect = (id: string) => {
    selectSession(id)
    navigate(`/chat/${id}`)
  }

  if (collapsed) {
    return (
      <div className="w-[56px] border-r bg-muted/30 flex flex-col items-center py-3 gap-2">
        <Button variant="ghost" size="icon" onClick={handleNew} title="新对话">
          <Plus className="h-4 w-4" />
        </Button>
        <div className="flex-1 overflow-y-auto w-full flex flex-col items-center gap-1">
          {sessions.slice(0, 20).map((s) => (
            <Button
              key={s.id}
              variant={s.id === currentSessionId ? 'secondary' : 'ghost'}
              size="icon"
              className="h-8 w-8"
              onClick={() => handleSelect(s.id)}
              title={s.title}
            >
              <MessageSquare className="h-3.5 w-3.5" />
            </Button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="w-[260px] border-r bg-muted/30 flex flex-col">
      {/* Header */}
      <div className="p-3 border-b">
        <Button variant="outline" className="w-full justify-start gap-2 text-sm" onClick={handleNew}>
          <Plus className="h-4 w-4" /> 新对话
        </Button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {loading && sessions.length === 0 && (
          <div className="text-xs text-muted-foreground p-2">加载中...</div>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            className={cn(
              'group flex items-center gap-2 px-2.5 py-2 rounded-md cursor-pointer text-sm transition-colors',
              s.id === currentSessionId ? 'bg-background shadow-sm' : 'hover:bg-muted'
            )}
            onClick={() => handleSelect(s.id)}
          >
            <MessageSquare className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <span className="flex-1 truncate">{s.title}</span>
            <div className="opacity-0 group-hover:opacity-100 flex gap-0.5">
              <Button
                variant="ghost" size="icon" className="h-6 w-6"
                onClick={(e) => { e.stopPropagation(); archiveSession(s.id) }}
                title="归档"
              >
                <Archive className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost" size="icon" className="h-6 w-6 text-destructive"
                onClick={(e) => { e.stopPropagation(); deleteSession(s.id) }}
                title="删除"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom links */}
      <div className="border-t p-2 space-y-0.5">
        <Button variant="ghost" className="w-full justify-start gap-2 text-sm" onClick={() => navigate('/settings')}>
          <Settings className="h-4 w-4" /> 设置
        </Button>
      </div>
    </div>
  )
}
