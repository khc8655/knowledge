import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api, type TenderRequirement } from '@/lib/api'
import { FileSearch, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'

export default function TenderViewPage() {
  const [tenderText, setTenderText] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [matching, setMatching] = useState(false)
  const [requirements, setRequirements] = useState<TenderRequirement[]>([])
  const [matchResults, setMatchResults] = useState<unknown[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!tenderText.trim()) return
    setAnalyzing(true)
    setError(null)
    try {
      const data = await api.analyzeTender({ tender_text: tenderText.trim() })
      setRequirements(data.requirements)
      setMatchResults(null)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '分析失败')
    }
    setAnalyzing(false)
  }

  const handleMatch = async () => {
    if (requirements.length === 0) return
    setMatching(true)
    try {
      const data = await api.matchTender({ requirement_ids: requirements.map(r => r.id) })
      setMatchResults(data.results)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '匹配失败')
    }
    setMatching(false)
  }

  const typeLabel = (t: string) => {
    const map: Record<string, string> = { mandatory: '强制', optional: '可选', preference: '偏好' }
    return map[t] || t
  }

  return (
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-[18px] font-semibold">招标匹配</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">分析招标文件要求，匹配产品和证据</p>
      </div>

      <div className="border rounded-lg bg-white p-4 space-y-3">
        <div>
          <label className="text-[12px] font-medium text-muted-foreground">招标文件内容</label>
          <textarea
            className="mt-1 w-full h-36 rounded-md border border-border bg-white p-3 text-[13px] placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
            value={tenderText}
            onChange={e => setTenderText(e.target.value)}
            placeholder="粘贴招标文件内容..."
          />
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={handleAnalyze} disabled={analyzing || !tenderText.trim()}>
            {analyzing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileSearch className="h-3.5 w-3.5" />}
            分析要求
          </Button>
          {requirements.length > 0 && (
            <Button variant="outline" size="sm" onClick={handleMatch} disabled={matching}>
              {matching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
              匹配产品
            </Button>
          )}
        </div>
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-[13px]">
            <AlertCircle className="h-4 w-4 shrink-0" /> {error}
          </div>
        )}
      </div>

      {requirements.length > 0 && (
        <div className="border rounded-lg bg-white p-4">
          <h2 className="text-[14px] font-semibold mb-3">分析结果 ({requirements.length} 条要求)</h2>
          <div className="space-y-2">
            {requirements.map((req) => (
              <div key={req.id} className="border rounded-md p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={req.requirement_type === 'mandatory' ? 'destructive' : req.requirement_type === 'preference' ? 'warning' : 'secondary'}>
                    {typeLabel(req.requirement_type)}
                  </Badge>
                  {req.target_models?.length > 0 && req.target_models.map(m => (
                    <Badge key={m} variant="outline">{m}</Badge>
                  ))}
                </div>
                <p className="text-[13px]">{req.raw_text}</p>
                {req.required_capabilities?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {req.required_capabilities.map(c => <Badge key={c} variant="secondary">{c}</Badge>)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {matchResults && (
        <div className="border rounded-lg bg-white p-4">
          <h2 className="text-[14px] font-semibold mb-3">匹配结果</h2>
          <div className="rounded-md bg-muted p-4 font-mono text-[13px] whitespace-pre-wrap max-h-[400px] overflow-y-auto">
            {JSON.stringify(matchResults, null, 2)}
          </div>
        </div>
      )}
    </div>
  )
}
