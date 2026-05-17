import { useAppStore } from '@/stores/app'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import { useEffect } from 'react'

export function TopBar() {
  const { health, fetchHealth } = useAppStore()

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[48px] flex items-center justify-between border-b bg-background px-4">
      <div className="flex items-center gap-2">
        <h1 className="text-[14px] font-semibold">知识库助手</h1>
        {health && (
          <span className={`inline-block h-1.5 w-1.5 rounded-full ${health.status === 'healthy' ? 'bg-success' : 'bg-destructive'}`} />
        )}
      </div>
      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchHealth} title="刷新状态">
        <RefreshCw className="h-3.5 w-3.5" />
      </Button>
    </header>
  )
}
