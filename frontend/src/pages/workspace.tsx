import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
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
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-h1">售前工作台</h1>
          <p className="text-muted-foreground text-body-small mt-1">管理售前项目和方案</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="h-4 w-4 mr-1" /> 新建项目
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="p-4 flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-body-small font-medium">客户名称</label>
              <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="输入客户名称" className="mt-1" />
            </div>
            <div className="w-40">
              <label className="text-body-small font-medium">行业</label>
              <Input value={newIndustry} onChange={e => setNewIndustry(e.target.value)} placeholder="如：公安" className="mt-1" />
            </div>
            <Button onClick={handleCreate} disabled={!newName.trim()}>创建</Button>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-2">
        {['', 'draft', 'evidence_ready', 'proposal_sent', 'won', 'lost'].map(s => (
          <Badge key={s} variant={stageFilter === s ? 'default' : 'outline'} className="cursor-pointer" onClick={() => { setStageFilter(s); setPage(1) }}>
            {s ? STAGE_LABELS[s]?.label || s : '全部'}
          </Badge>
        ))}
      </div>

      {projects.length === 0 && !loading ? (
        <EmptyState icon={Briefcase} title="暂无项目" description="点击「新建项目」开始" />
      ) : (
        <div className="space-y-2">
          {projects.map(p => (
            <Card key={p.id} className="cursor-pointer hover:shadow-sm transition-shadow" onClick={() => navigate(`/proposals/${p.id}`)}>
              <CardContent className="p-4 flex items-center gap-4">
                <Briefcase className="h-5 w-5 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-body truncate">{p.customer_name}</span>
                    <Badge variant={STAGE_LABELS[p.stage]?.variant || 'secondary'}>{STAGE_LABELS[p.stage]?.label || p.stage}</Badge>
                    {p.industry && <Badge variant="outline" className="text-meta">{p.industry}</Badge>}
                  </div>
                  <p className="text-meta text-muted-foreground mt-0.5 truncate">{p.description || '暂无描述'}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-meta text-muted-foreground">{p.created_at?.slice(0, 10)}</span>
                  <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); handleArchive(p.id) }} title="归档">
                    <Archive className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {total > 20 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft className="h-4 w-4" /></Button>
          <span className="text-body-small text-muted-foreground leading-8">第 {page} 页</span>
          <Button variant="outline" size="sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}><ChevronRight className="h-4 w-4" /></Button>
        </div>
      )}
    </div>
  )
}
