import { useState } from 'react'
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
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-[18px] font-semibold">BOM 配置</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">根据项目需求生成设备清单</p>
      </div>

      <div className="border rounded-lg bg-white p-4 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[12px] font-medium text-muted-foreground">项目 ID</label>
            <Input value={projectId} onChange={e => setProjectId(e.target.value)} placeholder="输入项目 ID" className="mt-1" />
          </div>
          <div>
            <label className="text-[12px] font-medium text-muted-foreground">场景描述</label>
            <Input value={scenario} onChange={e => setScenario(e.target.value)} placeholder="如：大型会议室" className="mt-1" />
          </div>
          <div>
            <label className="text-[12px] font-medium text-muted-foreground">房间数量</label>
            <Input type="number" value={roomCount} onChange={e => setRoomCount(parseInt(e.target.value) || 1)} min={1} className="mt-1" />
          </div>
          <div>
            <label className="text-[12px] font-medium text-muted-foreground">部署类型</label>
            <select className="mt-1 w-full h-8 rounded-md border border-border bg-white px-3 text-[13px]" value={deploymentType} onChange={e => setDeploymentType(e.target.value)}>
              <option value="on-prem">本地部署</option>
              <option value="cloud">云端部署</option>
              <option value="hybrid">混合部署</option>
            </select>
          </div>
        </div>
        <Button size="sm" onClick={handleGenerate} disabled={generating || !projectId.trim()}>
          {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Package className="h-3.5 w-3.5" />}
          生成 BOM
        </Button>
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-[13px]">
            <AlertCircle className="h-4 w-4 shrink-0" /> {error}
          </div>
        )}
      </div>

      {result && (
        <div className="border rounded-lg bg-white p-4">
          <h2 className="text-[14px] font-semibold mb-3">BOM 结果</h2>
          <div className="grid grid-cols-3 gap-4 mb-4">
            {result.total_items !== undefined && (
              <div>
                <label className="text-[12px] text-muted-foreground">总项数</label>
                <p className="text-[20px] font-semibold">{String(result.total_items)}</p>
              </div>
            )}
            {result.total_price !== undefined && (
              <div>
                <label className="text-[12px] text-muted-foreground">总价</label>
                <p className="text-[20px] font-semibold">¥{String(result.total_price)}</p>
              </div>
            )}
            {result.output_id ? (
              <div>
                <label className="text-[12px] text-muted-foreground">输出 ID</label>
                <p className="text-[13px] font-mono">{String(result.output_id)}</p>
              </div>
            ) : null}
          </div>
          {result.content_md ? (
            <div className="rounded-md bg-muted p-4 font-mono text-[13px] whitespace-pre-wrap max-h-[500px] overflow-y-auto">
              {String(result.content_md)}
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
