import { useAppStore } from '@/stores/app'
import { Button } from '@/components/ui/button'
import { RefreshCw, Sparkles } from 'lucide-react'
import { useEffect } from 'react'

export function TopBar() {
  const { health, fetchHealth } = useAppStore()

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[52px] flex items-center justify-between border-b bg-white/80 backdrop-blur-sm px-5">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <h1 className="text-[15px] font-semibold text-foreground">知识库助手</h1>
        </div>
        {health && (
          <span className={`inline-block h-2 w-2 rounded-full ${health.status === 'healthy' ? 'bg-success' : 'bg-destructive'}`} />
        )}
      </div>
      <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg hover:bg-muted" onClick={fetchHealth} title="刷新状态">
        <RefreshCw className="h-4 w-4" />
      </Button>
    </header>
  )
}
