import { useAppStore } from '@/stores/app'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PanelLeftClose, PanelLeftOpen, Upload, RefreshCw } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export function TopBar() {
  const { health, fetchHealth, sidebarCollapsed, toggleSidebar } = useAppStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  const statusColor = health?.status === 'healthy' ? 'success' : 'destructive'

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[56px] flex items-center justify-between border-b bg-surface-container-lowest px-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={toggleSidebar}>
          {sidebarCollapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
        </Button>
        <h1 className="font-heading text-lg font-semibold">知识库平台</h1>
        {health && (
          <Badge variant={statusColor as 'success' | 'destructive'} className="ml-2">
            {health.status === 'healthy' ? '正常' : '异常'}
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => navigate('/upload')}>
          <Upload className="h-4 w-4" />
          上传
        </Button>
        <Button variant="ghost" size="icon" onClick={fetchHealth}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
