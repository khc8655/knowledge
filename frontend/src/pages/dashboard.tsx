import { useEffect } from 'react'
import { useAppStore } from '@/stores/app'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatusBadge } from '@/components/shared/status-badge'
import { useNavigate } from 'react-router-dom'
import { Search, Layers, FileText, Activity } from 'lucide-react'

export default function DashboardPage() {
  const { health, fetchHealth } = useAppStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  const checks = health?.checks || {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-h1">仪表盘</h1>
          <p className="text-muted-foreground text-body-small mt-1">
            系统状态总览
          </p>
        </div>
        <StatusBadge
          status={health?.status === 'healthy' ? 'healthy' : 'failed'}
          label={health?.status === 'healthy' ? '系统正常' : '系统异常'}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/cards')}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">卡片总数</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">{(checks as Record<string, unknown>).cards_count as string ?? '—'}</div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/search')}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">查询</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">—</div>
            <p className="text-meta text-muted-foreground">点击开始查询</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">待处理任务</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">
              {((checks as Record<string, unknown>).jobs_pending as number ?? 0) + ((checks as Record<string, unknown>).jobs_running as number ?? 0)}
            </div>
            <p className="text-meta text-muted-foreground">
              失败: {(checks as Record<string, unknown>).jobs_failed as number ?? 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">证据包</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">{(checks as Record<string, unknown>).evidence_count as string ?? '—'}</div>
            <p className="text-meta text-muted-foreground">
              检测报告: {(checks as Record<string, unknown>).report_evidence_count as number ?? 0}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
