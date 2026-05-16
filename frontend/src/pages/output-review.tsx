import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { CheckCircle2, Download, Loader2, AlertCircle, ArrowRight } from 'lucide-react'

const STATUS_FLOW = ['draft', 'evidence_checked', 'human_reviewed', 'exported', 'archived']
const STATUS_LABELS: Record<string, { label: string; variant: 'default' | 'secondary' | 'success' | 'warning' | 'processing' }> = {
  draft: { label: '草稿', variant: 'secondary' },
  evidence_checked: { label: '证据已核', variant: 'processing' },
  human_reviewed: { label: '人工审核', variant: 'default' },
  exported: { label: '已导出', variant: 'success' },
  archived: { label: '已归档', variant: 'warning' },
}

export default function OutputReviewPage() {
  const [outputId, setOutputId] = useState('')
  const [currentStatus, setCurrentStatus] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleReview = async (action: string) => {
    if (!outputId.trim()) return
    setError(null)
    try {
      const data = await api.reviewOutput(outputId.trim(), action)
      setCurrentStatus(data.status)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '操作失败')
    }
  }

  const handleExport = async () => {
    if (!outputId.trim()) return
    setExporting(true)
    setError(null)
    try {
      const data = await api.exportOutput(outputId.trim(), 'markdown')
      setResult(data)
      setCurrentStatus('exported')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '导出失败')
    }
    setExporting(false)
  }

  const nextAction = currentStatus ? STATUS_FLOW[STATUS_FLOW.indexOf(currentStatus) + 1] : null
  const actionMap: Record<string, string> = {
    evidence_checked: 'mark_evidence_checked',
    human_reviewed: 'mark_human_reviewed',
    exported: 'mark_exported',
    archived: 'mark_archived',
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-heading text-h1">输出审核</h1>
        <p className="text-muted-foreground text-body-small mt-1">审核和导出方案、招标等输出</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-h2">审核操作</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-body-small font-medium">输出 ID</label>
            <Input value={outputId} onChange={e => setOutputId(e.target.value)} placeholder="输入输出 ID" className="mt-1" />
          </div>

          {/* Status flow visualization */}
          <div className="flex items-center gap-1">
            {STATUS_FLOW.map((s, i) => (
              <div key={s} className="flex items-center gap-1">
                <Badge variant={currentStatus === s ? STATUS_LABELS[s].variant : 'outline'}>
                  {STATUS_LABELS[s].label}
                </Badge>
                {i < STATUS_FLOW.length - 1 && <ArrowRight className="h-3 w-3 text-muted-foreground" />}
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            {nextAction && (
              <Button onClick={() => handleReview(actionMap[nextAction])} disabled={!outputId.trim()}>
                <CheckCircle2 className="h-4 w-4 mr-1" />
                推进到: {STATUS_LABELS[nextAction]?.label}
              </Button>
            )}
            <Button variant="outline" onClick={handleExport} disabled={exporting || !outputId.trim()}>
              {exporting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Download className="h-4 w-4 mr-1" />}
              导出
            </Button>
          </div>

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
            <CardTitle className="text-h2">操作结果</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md bg-surface-container p-4 font-mono text-body-small whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
