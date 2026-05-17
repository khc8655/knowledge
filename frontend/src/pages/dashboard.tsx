import { useEffect } from 'react'
import { useAppStore } from '@/stores/app'
import { useNavigate } from 'react-router-dom'
import { Search, Layers, FileText, Activity } from 'lucide-react'

export default function DashboardPage() {
  const { health, fetchHealth } = useAppStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  const checks = health?.checks || {}

  const stats = [
    {
      label: '卡片总数',
      value: (checks as Record<string, unknown>).cards_count as string ?? '—',
      icon: Layers,
      to: '/cards',
    },
    {
      label: '查询',
      value: '—',
      icon: Search,
      to: '/search',
      sub: '点击开始查询',
    },
    {
      label: '待处理任务',
      value: String(((checks as Record<string, unknown>).jobs_pending as number ?? 0) + ((checks as Record<string, unknown>).jobs_running as number ?? 0)),
      icon: Activity,
      sub: `失败: ${(checks as Record<string, unknown>).jobs_failed as number ?? 0}`,
    },
    {
      label: '证据包',
      value: (checks as Record<string, unknown>).evidence_count as string ?? '—',
      icon: FileText,
      sub: `检测报告: ${(checks as Record<string, unknown>).report_evidence_count as number ?? 0}`,
    },
  ]

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h1 className="text-[18px] font-semibold">仪表盘</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">
          系统状态总览
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="border rounded-lg bg-white p-4 hover:bg-muted/50 transition-colors cursor-pointer"
            onClick={() => stat.to && navigate(stat.to)}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-[12px] font-medium text-muted-foreground">{stat.label}</span>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="text-[20px] font-semibold">{stat.value}</div>
            {stat.sub && (
              <p className="text-[12px] text-muted-foreground mt-0.5">{stat.sub}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
