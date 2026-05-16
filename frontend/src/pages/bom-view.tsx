import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { Package, Loader2, AlertCircle } from 'lucide-react'

export default function BomViewPage() {
  const [projectId, setProjectId] = useState('')
  const [scenario, setScenario] = useState('')
  const [roomCount, setRoomCount] = useState(1)
  const [deploymentType, setDeploymentType] = useState('on-prem')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!projectId.trim()) return
    setGenerating(true)
    setError(null)
    try {
      const data = await api.generateBom({
        project_id: projectId.trim(),
        scenario: scenario || undefined,
        room_count: roomCount,
        deployment_type: deploymentType,
      })
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '生成失败')
    }
    setGenerating(false)
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-heading text-h1">BOM 配置</h1>
        <p className="text-muted-foreground text-body-small mt-1">根据项目需求生成设备清单</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-h2">配置参数</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-body-small font-medium">项目 ID</label>
              <Input value={projectId} onChange={e => setProjectId(e.target.value)} placeholder="输入项目 ID" className="mt-1" />
            </div>
            <div>
              <label className="text-body-small font-medium">场景描述</label>
              <Input value={scenario} onChange={e => setScenario(e.target.value)} placeholder="如：大型会议室" className="mt-1" />
            </div>
            <div>
              <label className="text-body-small font-medium">房间数量</label>
              <Input type="number" value={roomCount} onChange={e => setRoomCount(parseInt(e.target.value) || 1)} min={1} className="mt-1" />
            </div>
            <div>
              <label className="text-body-small font-medium">部署类型</label>
              <select className="mt-1 w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm" value={deploymentType} onChange={e => setDeploymentType(e.target.value)}>
                <option value="on-prem">本地部署</option>
                <option value="cloud">云端部署</option>
                <option value="hybrid">混合部署</option>
              </select>
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={generating || !projectId.trim()}>
            {generating ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Package className="h-4 w-4 mr-1" />}
            生成 BOM
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
            <CardTitle className="text-h2">BOM 结果</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-4">
              {result.total_items !== undefined && (
                <div>
                  <label className="text-meta text-muted-foreground">总项数</label>
                  <p className="text-2xl font-heading font-bold">{String(result.total_items)}</p>
                </div>
              )}
              {result.total_price !== undefined && (
                <div>
                  <label className="text-meta text-muted-foreground">总价</label>
                  <p className="text-2xl font-heading font-bold">¥{String(result.total_price)}</p>
                </div>
              )}
              {result.output_id ? (
                <div>
                  <label className="text-meta text-muted-foreground">输出 ID</label>
                  <p className="text-body-small font-mono">{String(result.output_id)}</p>
                </div>
              ) : null}
            </div>
            {result.content_md ? (
              <div className="rounded-md bg-surface-container p-4 font-mono text-body-small whitespace-pre-wrap max-h-[500px] overflow-y-auto">
                {String(result.content_md)}
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
