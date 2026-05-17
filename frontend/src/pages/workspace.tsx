import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/shared/empty-state'
import { api, type Project } from '@/lib/api'
import { Briefcase, Plus, Archive, ChevronLeft, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const STAGE_LABELS: Record<string, { label: string; variant: 'default' | 'secondary' | 'success' | 'warning' | 'processing' }> = {
  draft: { label: '草稿', variant: 'secondary' },
  evidence_ready: { label: '证据就绪', variant: 'processing' },
  proposal_sent: { label: '已发方案', variant: 'default' },
  won: { label: '中标', variant: 'success' },
  lost: { label: '未中标', variant: 'warning' },
}

export default function WorkspacePage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [stageFilter, setStageFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newIndustry, setNewIndustry] = useState('')
  const navigate = useNavigate()

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listProjects({ page, page_size: 20, stage: stageFilter || undefined })
      setProjects(data.items)
      setTotal(data.total)
    } catch { /* silent */ }
    setLoading(false)
  }, [page, stageFilter])

  useEffect(() => { fetchProjects() }, [fetchProjects])

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      await api.createProject({ customer_name: newName.trim(), industry: newIndustry || undefined })
      setNewName('')
      setNewIndustry('')
      setShowCreate(false)
      fetchProjects()
    } catch { /* silent */ }
  }

  const handleArchive = async (id: string) => {
    try {
      await api.archiveProject(id)
      fetchProjects()
    } catch { /* silent */ }
  }

  return (
    <div className="space-y-5 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[18px] font-semibold">售前工作台</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">管理售前项目和方案</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} size="sm">
          <Plus className="h-3.5 w-3.5" />
          新建项目
        </Button>
      </div>

      {showCreate && (
        <div className="border rounded-lg bg-white p-4">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-[12px] font-medium text-muted-foreground">客户名称</label>
              <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="输入客户名称" className="mt-1" />
            </div>
            <div className="w-36">
              <label className="text-[12px] font-medium text-muted-foreground">行业</label>
              <Input value={newIndustry} onChange={e => setNewIndustry(e.target.value)} placeholder="如：公安" className="mt-1" />
            </div>
            <Button size="sm" onClick={handleCreate} disabled={!newName.trim()}>创建</Button>
            <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>取消</Button>
          </div>
        </div>
      )}

      <div className="flex gap-1.5">
        {['', 'draft', 'evidence_ready', 'proposal_sent', 'won', 'lost'].map(s => (
          <Badge key={s} variant={stageFilter === s ? 'default' : 'outline'} className="cursor-pointer" onClick={() => { setStageFilter(s); setPage(1) }}>
            {s ? STAGE_LABELS[s]?.label || s : '全部'}
          </Badge>
        ))}
      </div>

      {projects.length === 0 && !loading ? (
        <EmptyState icon={Briefcase} title="暂无项目" description="点击「新建项目」开始" />
      ) : (
        <div className="border rounded-lg bg-white divide-y">
          {projects.map(p => (
            <div
              key={p.id}
              className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => navigate(`/proposals/${p.id}`)}
            >
              <Briefcase className="h-4 w-4 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-medium truncate">{p.customer_name}</span>
                  <Badge variant={STAGE_LABELS[p.stage]?.variant || 'secondary'}>{STAGE_LABELS[p.stage]?.label || p.stage}</Badge>
                  {p.industry && <Badge variant="outline">{p.industry}</Badge>}
                </div>
                <p className="text-[12px] text-muted-foreground mt-0.5 truncate">{p.description || '暂无描述'}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[12px] text-muted-foreground">{p.created_at?.slice(0, 10)}</span>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={(e) => { e.stopPropagation(); handleArchive(p.id) }} title="归档">
                  <Archive className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {total > 20 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft className="h-3.5 w-3.5" /></Button>
          <span className="text-[13px] text-muted-foreground leading-8">第 {page} 页</span>
          <Button variant="outline" size="sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}><ChevronRight className="h-3.5 w-3.5" /></Button>
        </div>
      )}
    </div>
  )
}
