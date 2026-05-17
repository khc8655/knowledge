import { useState } from 'react'
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
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-[18px] font-semibold">客户答复</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">基于证据生成客户回复</p>
      </div>

      <div className="border rounded-lg bg-white p-4 space-y-3">
        <div>
          <label className="text-[12px] font-medium text-muted-foreground">客户问题</label>
          <textarea
            className="mt-1 w-full h-24 rounded-md border border-border bg-white p-3 text-[13px] placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="输入客户的问题..."
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[12px] font-medium text-muted-foreground">项目 ID</label>
            <Input value={projectId} onChange={e => setProjectId(e.target.value)} placeholder="default" className="mt-1" />
          </div>
          <div>
            <label className="text-[12px] font-medium text-muted-foreground">语气</label>
            <select className="mt-1 w-full h-8 rounded-md border border-border bg-white px-3 text-[13px]" value={tone} onChange={e => setTone(e.target.value)}>
              <option value="neutral">中性</option>
              <option value="formal">正式</option>
              <option value="friendly">友好</option>
            </select>
          </div>
        </div>
        <Button size="sm" onClick={handleGenerate} disabled={generating || !question.trim()}>
          {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <MessageSquare className="h-3.5 w-3.5" />}
          生成答复
        </Button>
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-[13px]">
            <AlertCircle className="h-4 w-4 shrink-0" /> {error}
          </div>
        )}
      </div>

      {result && (
        <div className="border rounded-lg bg-white">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <h2 className="text-[14px] font-semibold">生成结果</h2>
            <Button variant="ghost" size="sm" onClick={handleCopy}>
              <Copy className="h-3.5 w-3.5" />
              复制
            </Button>
          </div>
          <div className="p-4 space-y-4">
            <div className="rounded-md bg-muted p-4 text-[13px] whitespace-pre-wrap">
              {String(result.reply_text || '')}
            </div>
            {result.risk_summary && typeof result.risk_summary === 'object' ? (
              <div className="flex gap-4">
                <div>
                  <label className="text-[12px] text-muted-foreground">证据数</label>
                  <p className="text-[13px]">{String((result.risk_summary as Record<string, unknown>).total_evidence || 0)}</p>
                </div>
                <div>
                  <label className="text-[12px] text-muted-foreground">平均置信度</label>
                  <p className="text-[13px]">{String((result.risk_summary as Record<string, unknown>).avg_confidence || 0)}</p>
                </div>
              </div>
            ) : null}
            {Array.isArray(result.internal_evidence) && result.internal_evidence.length > 0 && (
              <div>
                <label className="text-[12px] font-medium text-muted-foreground">内部证据 (已过滤)</label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {(result.internal_evidence as Array<Record<string, unknown>>).map((ev, i) => (
                    <Badge key={i} variant="outline">{String(ev.evidence_id || '')}</Badge>
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
