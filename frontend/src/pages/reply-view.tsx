import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { MessageSquare, Loader2, AlertCircle, Copy } from 'lucide-react'

export default function ReplyViewPage() {
  const [question, setQuestion] = useState('')
  const [projectId, setProjectId] = useState('default')
  const [tone, setTone] = useState('neutral')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!question.trim()) return
    setGenerating(true)
    setError(null)
    try {
      const data = await api.generateReply({
        customer_question: question.trim(),
        project_id: projectId || 'default',
        tone,
      })
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '生成失败')
    }
    setGenerating(false)
  }

  const handleCopy = () => {
    if (result?.reply_text) {
      navigator.clipboard.writeText(String(result.reply_text))
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-heading text-h1">客户答复</h1>
        <p className="text-muted-foreground text-body-small mt-1">基于证据生成客户回复</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-h2">问题输入</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-body-small font-medium">客户问题</label>
            <textarea
              className="mt-1 w-full h-24 rounded-md border border-input bg-transparent p-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="输入客户的问题..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-body-small font-medium">项目 ID</label>
              <Input value={projectId} onChange={e => setProjectId(e.target.value)} placeholder="default" className="mt-1" />
            </div>
            <div>
              <label className="text-body-small font-medium">语气</label>
              <select className="mt-1 w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm" value={tone} onChange={e => setTone(e.target.value)}>
                <option value="neutral">中性</option>
                <option value="formal">正式</option>
                <option value="friendly">友好</option>
              </select>
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={generating || !question.trim()}>
            {generating ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <MessageSquare className="h-4 w-4 mr-1" />}
            生成答复
          </Button>
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-body-small">
              <AlertCircle className="h-4 w-4 shrink-0" /> {error}
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-h2">生成结果</CardTitle>
              <Button variant="ghost" size="sm" onClick={handleCopy}>
                <Copy className="h-4 w-4 mr-1" /> 复制
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md bg-surface-container p-4 text-body whitespace-pre-wrap">
              {String(result.reply_text || '')}
            </div>
            {result.risk_summary && typeof result.risk_summary === 'object' ? (
              <div className="flex gap-4">
                <div>
                  <label className="text-meta text-muted-foreground">证据数</label>
                  <p className="text-body-small">{String((result.risk_summary as Record<string, unknown>).total_evidence || 0)}</p>
                </div>
                <div>
                  <label className="text-meta text-muted-foreground">平均置信度</label>
                  <p className="text-body-small">{String((result.risk_summary as Record<string, unknown>).avg_confidence || 0)}</p>
                </div>
              </div>
            ) : null}
            {Array.isArray(result.internal_evidence) && result.internal_evidence.length > 0 && (
              <div>
                <label className="text-body-small font-medium">内部证据 (已过滤)</label>
                <div className="space-y-1 mt-1">
                  {(result.internal_evidence as Array<Record<string, unknown>>).map((ev, i) => (
                    <Badge key={i} variant="outline" className="text-meta mr-1">{String(ev.evidence_id || '')}</Badge>
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
