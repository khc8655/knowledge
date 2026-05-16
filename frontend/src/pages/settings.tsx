import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { api, type SystemConfig } from '@/lib/api'
import { Save, Loader2, CheckCircle2 } from 'lucide-react'

export default function SettingsPage() {
  const [config, setConfig] = useState<SystemConfig>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const fetchConfig = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getConfig()
      setConfig(data)
    } catch {
      // silent
    }
    setLoading(false)
  }, [])

  useEffect(() => { fetchConfig() }, [fetchConfig])

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    try {
      await api.updateConfig(config)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      // silent
    }
    setSaving(false)
  }

  const update = (key: keyof SystemConfig, value: unknown) => {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return <div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-h1">系统配置</h1>
          <p className="text-muted-foreground text-body-small mt-1">LLM、Embedding、缓存等参数</p>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : saved ? <CheckCircle2 className="h-4 w-4 mr-1" /> : <Save className="h-4 w-4 mr-1" />}
          {saved ? '已保存' : '保存'}
        </Button>
      </div>

      {/* LLM Config */}
      <Card>
        <CardHeader>
          <CardTitle className="text-h2">LLM 配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-body-small font-medium">API Key</label>
            <Input
              type="password"
              value={config.llm_api_key || ''}
              onChange={(e) => update('llm_api_key', e.target.value)}
              placeholder="sk-..."
              className="mt-1"
            />
          </div>
          <div>
            <label className="text-body-small font-medium">Base URL</label>
            <Input
              value={config.llm_base_url || ''}
              onChange={(e) => update('llm_base_url', e.target.value)}
              placeholder="https://api.openai.com/v1"
              className="mt-1"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-body-small font-medium">LLM 模型</label>
              <Input
                value={config.llm_model || ''}
                onChange={(e) => update('llm_model', e.target.value)}
                placeholder="gpt-4o-mini"
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-body-small font-medium">Embedding 模型</label>
              <Input
                value={config.embedding_model || ''}
                onChange={(e) => update('embedding_model', e.target.value)}
                placeholder="text-embedding-3-small"
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Processing Config */}
      <Card>
        <CardHeader>
          <CardTitle className="text-h2">处理参数</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-body-small font-medium">最大分段字符数</label>
              <Input
                type="number"
                value={config.max_section_chars || ''}
                onChange={(e) => update('max_section_chars', parseInt(e.target.value) || undefined)}
                placeholder="1500"
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-body-small font-medium">最大文件大小 (MB)</label>
              <Input
                type="number"
                value={config.max_file_size_mb || ''}
                onChange={(e) => update('max_file_size_mb', parseInt(e.target.value) || undefined)}
                placeholder="50"
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cache Config */}
      <Card>
        <CardHeader>
          <CardTitle className="text-h2">缓存配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-body-small font-medium">缓存清理天数</label>
              <Input
                type="number"
                value={config.cache_evict_days || ''}
                onChange={(e) => update('cache_evict_days', parseInt(e.target.value) || undefined)}
                placeholder="30"
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-body-small font-medium">最大缓存条目</label>
              <Input
                type="number"
                value={config.cache_max_entries || ''}
                onChange={(e) => update('cache_max_entries', parseInt(e.target.value) || undefined)}
                placeholder="1000"
                className="mt-1"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="route-learning"
              checked={config.route_learning_enabled ?? true}
              onChange={(e) => update('route_learning_enabled', e.target.checked)}
              className="h-4 w-4"
            />
            <label htmlFor="route-learning" className="text-body-small">启用路由学习</label>
            <Badge variant="outline" className="text-meta ml-1">实验性</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
