import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/shared/empty-state'
import { api, type Template } from '@/lib/api'
import { FileText, Plus, Trash2 } from 'lucide-react'

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(false)
  const [typeFilter, setTypeFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newType, setNewType] = useState('proposal')
  const [newName, setNewName] = useState('')
  const [newPath, setNewPath] = useState('')

  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listTemplates({ template_type: typeFilter || undefined })
      setTemplates(data)
    } catch { /* silent */ }
    setLoading(false)
  }, [typeFilter])

  useEffect(() => { fetchTemplates() }, [fetchTemplates])

  const handleCreate = async () => {
    if (!newName.trim() || !newPath.trim()) return
    try {
      await api.createTemplate({ template_type: newType, name: newName.trim(), file_path: newPath.trim() })
      setNewName('')
      setNewPath('')
      setShowCreate(false)
      fetchTemplates()
    } catch { /* silent */ }
  }

  const handleDelete = async (id: string) => {
    try {
      await api.deleteTemplate(id)
      fetchTemplates()
    } catch { /* silent */ }
  }

  const typeLabels: Record<string, string> = { proposal: '方案', tender: '招标', bom: 'BOM', reply: '答复' }

  return (
    <div className="space-y-5 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[18px] font-semibold">模板管理</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">管理方案、招标、BOM 等模板</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} size="sm">
          <Plus className="h-3.5 w-3.5" />
          新建模板
        </Button>
      </div>

      {showCreate && (
        <div className="border rounded-lg bg-white p-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-[12px] font-medium text-muted-foreground">类型</label>
              <select className="mt-1 w-full h-8 rounded-md border border-border bg-white px-3 text-[13px]" value={newType} onChange={e => setNewType(e.target.value)}>
                <option value="proposal">方案</option>
                <option value="tender">招标</option>
                <option value="bom">BOM</option>
                <option value="reply">答复</option>
              </select>
            </div>
            <div>
              <label className="text-[12px] font-medium text-muted-foreground">名称</label>
              <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="模板名称" className="mt-1" />
            </div>
            <div>
              <label className="text-[12px] font-medium text-muted-foreground">文件路径</label>
              <Input value={newPath} onChange={e => setNewPath(e.target.value)} placeholder="/path/to/template.md" className="mt-1" />
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleCreate} disabled={!newName.trim() || !newPath.trim()}>创建</Button>
            <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>取消</Button>
          </div>
        </div>
      )}

      <div className="flex gap-1.5">
        {['', 'proposal', 'tender', 'bom', 'reply'].map(t => (
          <Badge key={t} variant={typeFilter === t ? 'default' : 'outline'} className="cursor-pointer" onClick={() => setTypeFilter(t)}>
            {t ? typeLabels[t] || t : '全部'}
          </Badge>
        ))}
      </div>

      {templates.length === 0 && !loading ? (
        <EmptyState icon={FileText} title="暂无模板" description="点击「新建模板」添加" />
      ) : (
        <div className="border rounded-lg bg-white divide-y">
          {templates.map(tmpl => (
            <div key={tmpl.id} className="flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors">
              <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-medium truncate">{tmpl.name}</span>
                  <Badge variant="outline">{typeLabels[tmpl.template_type] || tmpl.template_type}</Badge>
                  {tmpl.industry && <Badge variant="secondary">{tmpl.industry}</Badge>}
                  {!tmpl.enabled && <Badge variant="warning">已禁用</Badge>}
                </div>
                <p className="text-[12px] text-muted-foreground mt-0.5 truncate">{tmpl.file_path}</p>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDelete(tmpl.id)} title="删除">
                <Trash2 className="h-3.5 w-3.5 text-destructive" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
