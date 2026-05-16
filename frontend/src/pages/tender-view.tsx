import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-heading text-h1">招标匹配</h1>
        <p className="text-muted-foreground text-body-small mt-1">分析招标文件要求，匹配产品和证据</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-h2">招标文件</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            className="w-full h-40 rounded-md border border-input bg-transparent p-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={tenderText}
            onChange={e => setTenderText(e.target.value)}
            placeholder="粘贴招标文件内容..."
          />
          <div className="flex gap-2">
            <Button onClick={handleAnalyze} disabled={analyzing || !tenderText.trim()}>
              {analyzing ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <FileSearch className="h-4 w-4 mr-1" />}
              分析要求
            </Button>
            {requirements.length > 0 && (
              <Button variant="outline" onClick={handleMatch} disabled={matching}>
                {matching ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <CheckCircle2 className="h-4 w-4 mr-1" />}
                匹配产品
              </Button>
            )}
          </div>
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-body-small">
              <AlertCircle className="h-4 w-4 shrink-0" /> {error}
            </div>
          )}
        </CardContent>
      </Card>

      {requirements.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-h2">分析结果 ({requirements.length} 条要求)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {requirements.map((req) => (
                <div key={req.id} className="border rounded-md p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={req.requirement_type === 'mandatory' ? 'destructive' : req.requirement_type === 'preference' ? 'warning' : 'secondary'}>
                      {typeLabel(req.requirement_type)}
                    </Badge>
                    {req.target_models?.length > 0 && req.target_models.map(m => (
                      <Badge key={m} variant="outline" className="text-meta">{m}</Badge>
                    ))}
                  </div>
                  <p className="text-body-small">{req.raw_text}</p>
                  {req.required_capabilities?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {req.required_capabilities.map(c => <Badge key={c} variant="secondary" className="text-meta">{c}</Badge>)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {matchResults && (
        <Card>
          <CardHeader>
            <CardTitle className="text-h2">匹配结果</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md bg-surface-container p-4 font-mono text-body-small whitespace-pre-wrap max-h-[400px] overflow-y-auto">
              {JSON.stringify(matchResults, null, 2)}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
