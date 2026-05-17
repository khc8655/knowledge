import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { api, type Project } from '@/lib/api'
import { FileText, Loader2, ArrowLeft, Download } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '@/components/ui/toast'

export default function ProposalViewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { addToast } = useToast()
  const [project, setProject] = useState<Project | null>(null)
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [title, setTitle] = useState('')

  const fetchProject = useCallback(async () => {
    if (!id) return
    try {
      const data = await api.getProject(id)
      setProject(data)
      setTitle(`${data.customer_name} - 售前方案`)
    } catch { /* silent */ }
  }, [id])

  useEffect(() => { fetchProject() }, [fetchProject])

  const handleGenerate = async () => {
    if (!id || !title.trim()) return
    setGenerating(true)
    try {
      const data = await api.generateProposal({ project_id: id, title: title.trim() })
      setResult(data)
      addToast({ title: '方案生成成功', variant: 'success' })
    } catch (e: unknown) {
      addToast({ title: '生成失败', description: e instanceof Error ? e.message : '未知错误', variant: 'destructive' })
    }
    setGenerating(false)
  }

  const handleExport = async () => {
    if (!result?.output_id) return
    try {
      const data = await api.exportOutput(result.output_id as string, 'markdown')
      addToast({ title: '导出成功', description: `版本 v${data.version}`, variant: 'success' })
    } catch (e: unknown) {
      addToast({ title: '导出失败', description: e instanceof Error ? e.message : '未知错误', variant: 'destructive' })
    }
  }

  return (
    <div className="space-y-5 max-w-3xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigate('/workspace')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-[18px] font-semibold">方案生成</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">{project?.customer_name || '加载中...'}</p>
        </div>
      </div>

      <div className="border rounded-lg bg-white p-4 space-y-3">
        <div>
          <label className="text-[12px] font-medium text-muted-foreground">方案标题</label>
          <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="输入方案标题" className="mt-1" />
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={handleGenerate} disabled={generating || !title.trim()}>
            {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5" />}
            生成方案
          </Button>
          {result && (
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-3.5 w-3.5" />
              导出
            </Button>
          )}
        </div>
      </div>

      {result && (
        <div className="border rounded-lg bg-white">
          <div className="px-4 py-3 border-b">
            <h2 className="text-[14px] font-semibold">生成结果</h2>
          </div>
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[12px] text-muted-foreground">输出 ID</label>
                <p className="text-[13px] font-mono">{String(result.output_id || '')}</p>
              </div>
              <div>
                <label className="text-[12px] text-muted-foreground">章节数</label>
                <p className="text-[13px]">{Array.isArray(result.chapters) ? result.chapters.length : '—'}</p>
              </div>
            </div>
            {result.content_md ? (
              <div className="rounded-md bg-muted p-4 font-mono text-[13px] whitespace-pre-wrap max-h-[500px] overflow-y-auto">
                {String(result.content_md)}
              </div>
            ) : null}
            {Array.isArray(result.risk_summary) && result.risk_summary.length > 0 && (
              <div>
                <h3 className="text-[12px] font-medium text-muted-foreground mb-2">风险提示</h3>
                <div className="flex flex-wrap gap-1.5">
                  {result.risk_summary.map((r: string, i: number) => (
                    <Badge key={i} variant="warning">{r}</Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
