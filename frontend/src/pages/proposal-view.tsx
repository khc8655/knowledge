import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate('/workspace')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="font-heading text-h1">方案生成</h1>
          <p className="text-muted-foreground text-body-small mt-1">{project?.customer_name || '加载中...'}</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-h2">生成参数</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-body-small font-medium">方案标题</label>
            <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="输入方案标题" className="mt-1" />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleGenerate} disabled={generating || !title.trim()}>
              {generating ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <FileText className="h-4 w-4 mr-1" />}
              生成方案
            </Button>
            {result && (
              <Button variant="outline" onClick={handleExport}>
                <Download className="h-4 w-4 mr-1" /> 导出
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-h2">生成结果</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-meta text-muted-foreground">输出 ID</label>
                <p className="text-body-small font-mono">{String(result.output_id || '')}</p>
              </div>
              <div>
                <label className="text-meta text-muted-foreground">章节数</label>
                <p className="text-body-small">{Array.isArray(result.chapters) ? result.chapters.length : '—'}</p>
              </div>
            </div>
            {result.content_md ? (
              <div className="rounded-md bg-surface-container p-4 font-mono text-body-small whitespace-pre-wrap max-h-[500px] overflow-y-auto">
                {String(result.content_md)}
              </div>
            ) : null}
            {Array.isArray(result.risk_summary) && result.risk_summary.length > 0 && (
              <div className="mt-4">
                <h3 className="text-body-small font-medium mb-2">风险提示</h3>
                <div className="space-y-1">
                  {result.risk_summary.map((r: string, i: number) => (
                    <Badge key={i} variant="warning" className="mr-2">{r}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
