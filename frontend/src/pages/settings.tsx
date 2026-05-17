import { useState, useEffect, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { EmptyState } from '@/components/shared/empty-state'
import { api, type SystemConfig, type LLMProfile, type UploadedDocument, type IndexStatus, type Job } from '@/lib/api'
import { useAppStore } from '@/stores/app'
import {
  Save, Loader2, CheckCircle2, Plus, Trash2, ArrowLeft,
  Upload, FileText, RefreshCw, AlertCircle, Database,
  Cpu, FileSearch, Sparkles, Layers, Activity, Settings, Palette,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useNavigate } from 'react-router-dom'

const PROFILE_LABELS: Record<string, string> = {
  default: '默认',
  annotation: '语义标注',
  generation: '内容生成',
  reply: '客户回复',
}

const PROFILE_DESCRIPTIONS: Record<string, string> = {
  default: '其他任务的兜底配置',
  annotation: '知识卡片语义标注（批量，要求快且便宜）',
  generation: '方案/BOM 等结构化内容生成（要求质量高）',
  reply: '客户问题回复（要求平衡速度与质量）',
}

const ACCEPTED_TYPES = ['.txt', '.md', '.docx', '.xlsx', '.pptx', '.pdf']
const MAX_SIZE_MB = 50

const settingsSections = [
  {
    label: '概览',
    items: [
      { id: 'system', label: '系统状态', icon: Activity },
    ],
  },
  {
    label: '知识库',
    items: [
      { id: 'documents', label: '文档管理', icon: FileText },
      { id: 'indexes', label: '索引管理', icon: Database },
    ],
  },
  {
    label: '配置',
    items: [
      { id: 'llm', label: 'LLM 模型', icon: Cpu },
      { id: 'processing', label: '处理参数', icon: Settings },
      { id: 'cache', label: '缓存配置', icon: Layers },
      { id: 'appearance', label: '外观', icon: Palette },
    ],
  },
]

export default function SettingsPage() {
  const navigate = useNavigate()
  const [activeSection, setActiveSection] = useState('system')

  return (
    <div className="flex gap-6 max-w-5xl mx-auto px-4 py-6">
      {/* Left sidebar navigation */}
      <div className="w-[180px] shrink-0">
        <nav className="sticky top-[64px] space-y-4">
          <Button variant="ghost" size="sm" className="w-full justify-start gap-2 mb-2" onClick={() => navigate('/')}>
            <ArrowLeft className="h-3.5 w-3.5" />
            返回对话
          </Button>

          {settingsSections.map((section) => (
            <div key={section.label}>
              <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider px-2 mb-1">
                {section.label}
              </div>
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveSection(item.id)}
                    className={cn(
                      'w-full text-left px-2.5 py-1.5 rounded-md text-[13px] font-medium transition-colors cursor-pointer flex items-center gap-2',
                      activeSection === item.id
                        ? 'bg-muted text-foreground'
                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                    )}
                  >
                    <item.icon className="h-3.5 w-3.5" />
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* Right content area */}
      <div className="flex-1 min-w-0">
        {activeSection === 'system' && <SystemSection />}
        {activeSection === 'documents' && <DocumentsSection />}
        {activeSection === 'indexes' && <IndexesSection />}
        {activeSection === 'llm' && <LLMSection />}
        {activeSection === 'processing' && <ProcessingSection />}
        {activeSection === 'cache' && <CacheSection />}
        {activeSection === 'appearance' && <AppearanceSection />}
      </div>
    </div>
  )
}


/* ── System Status ── */

function SystemSection() {
  const { health, fetchHealth } = useAppStore()

  useEffect(() => { fetchHealth() }, [fetchHealth])

  const checks = (health?.checks || {}) as Record<string, unknown>

  const stats = [
    { label: '卡片总数', value: String(checks.cards_count ?? '—'), icon: Layers },
    { label: '待处理任务', value: String((checks.jobs_pending as number ?? 0) + (checks.jobs_running as number ?? 0)), icon: Activity, sub: `失败: ${checks.jobs_failed ?? 0}` },
    { label: '证据包', value: String(checks.evidence_count ?? '—'), icon: FileText },
    { label: '系统状态', value: health?.status === 'healthy' ? '正常' : '异常', icon: CheckCircle2 },
  ]

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-[15px] font-semibold">系统状态</h2>
        <p className="text-[13px] text-muted-foreground mt-0.5">系统运行状态总览</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="border rounded-lg bg-white p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[12px] font-medium text-muted-foreground">{stat.label}</span>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="text-[20px] font-semibold">{stat.value}</div>
            {stat.sub && <p className="text-[12px] text-muted-foreground mt-0.5">{stat.sub}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}


/* ── Documents ── */

function DocumentsSection() {
  const [documents, setDocuments] = useState<UploadedDocument[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listDocuments({ page, page_size: 20 })
      setDocuments(data.items)
      setTotal(data.total)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [page])

  useEffect(() => { fetchDocuments() }, [fetchDocuments])

  const handleFiles = async (files: FileList | File[]) => {
    setError(null); setSuccess(null)
    for (const file of Array.from(files)) {
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        setError(`${file.name} 超过 ${MAX_SIZE_MB}MB 限制`); continue
      }
      setUploading(true)
      try {
        const result = await api.uploadFile(file)
        setSuccess(`${file.name} 上传成功，创建 ${result.jobs_created} 个处理任务`)
        fetchDocuments()
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : `${file.name} 上传失败`)
      }
    }
    setUploading(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files)
  }

  const statusBadge = (s: string) => {
    const map: Record<string, { label: string; variant: 'success' | 'warning' | 'destructive' | 'processing' | 'secondary' }> = {
      completed: { label: '已完成', variant: 'success' },
      processing: { label: '处理中', variant: 'processing' },
      pending: { label: '等待中', variant: 'warning' },
      failed: { label: '失败', variant: 'destructive' },
    }
    const cfg = map[s] || { label: s, variant: 'secondary' as const }
    return <Badge variant={cfg.variant}>{cfg.label}</Badge>
  }

  const fileTypeLabel = (t: string) => {
    const map: Record<string, string> = { txt: 'TXT', md: 'Markdown', docx: 'Word', xlsx: 'Excel', pptx: 'PPT', pdf: 'PDF' }
    return map[t] || t
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-[15px] font-semibold">文档管理</h2>
        <p className="text-[13px] text-muted-foreground mt-0.5">支持 {ACCEPTED_TYPES.join(' ')} 格式，最大 {MAX_SIZE_MB}MB</p>
      </div>

      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer',
          dragging ? 'border-foreground bg-muted' : 'border-border hover:border-muted-foreground/50'
        )}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" multiple accept={ACCEPTED_TYPES.join(',')} className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)} />
        <Upload className="h-6 w-6 mx-auto text-muted-foreground/50 mb-2" />
        <p className="text-[13px] font-medium">拖拽文件到此处，或点击选择</p>
        {uploading && <Loader2 className="h-4 w-4 animate-spin mx-auto mt-2 text-muted-foreground" />}
      </div>

      {error && <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-[13px]"><AlertCircle className="h-4 w-4 shrink-0" />{error}</div>}
      {success && <div className="flex items-center gap-2 p-3 rounded-md bg-green-50 text-green-700 text-[13px]"><CheckCircle2 className="h-4 w-4 shrink-0" />{success}</div>}

      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[14px] font-semibold">已上传文档 ({total})</h3>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchDocuments}><RefreshCw className="h-3.5 w-3.5" /></Button>
        </div>
        {documents.length === 0 && !loading ? (
          <EmptyState icon={FileText} title="暂无文档" description="上传文档开始构建知识库" />
        ) : (
          <div className="border rounded-lg bg-white divide-y">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors">
                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium truncate">{doc.filename}</span>
                    <Badge variant="outline">{fileTypeLabel(doc.file_type)}</Badge>
                    {statusBadge(doc.pipeline_status)}
                  </div>
                  <div className="text-[12px] text-muted-foreground mt-0.5">
                    {(doc.file_size / 1024).toFixed(1)} KB · {doc.cards_count} 张卡片 · {doc.created_at?.slice(0, 16)}
                  </div>
                </div>
                <div className="flex items-center gap-0.5">
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => api.reprocessDocument(doc.id).then(fetchDocuments)} title="重新处理">
                    <RefreshCw className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => api.deleteDocument(doc.id).then(fetchDocuments)} title="删除">
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
        {total > 20 && (
          <div className="flex justify-center gap-2 mt-4">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
            <span className="text-[13px] text-muted-foreground leading-8">第 {page} 页</span>
            <Button variant="outline" size="sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}>下一页</Button>
          </div>
        )}
      </div>
    </div>
  )
}


/* ── Indexes ── */

function IndexesSection() {
  const [status, setStatus] = useState<IndexStatus | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [rebuilding, setRebuilding] = useState<string | null>(null)
  const [annotating, setAnnotating] = useState(false)

  const fetchStatus = useCallback(async () => {
    try { setStatus(await api.getIndexStatus()) } catch { /* silent */ }
  }, [])

  const fetchJobs = useCallback(async () => {
    try { setJobs((await api.listJobs({ page_size: 10 })).items) } catch { /* silent */ }
  }, [])

  useEffect(() => {
    fetchStatus(); fetchJobs()
    const interval = setInterval(() => { fetchStatus(); fetchJobs() }, 10000)
    return () => clearInterval(interval)
  }, [fetchStatus, fetchJobs])

  const handleRebuild = async (indexType: string) => {
    setRebuilding(indexType)
    try { await api.rebuildIndex(indexType); fetchStatus(); fetchJobs() } catch { /* silent */ }
    setRebuilding(null)
  }

  const indexCards = [
    { key: 'bm25', label: 'BM25 索引', icon: FileSearch, desc: '关键词检索，支持中文分词' },
    { key: 'vector', label: '向量索引', icon: Cpu, desc: '语义检索，基于 embedding' },
    { key: 'fts5', label: 'FTS5 全文索引', icon: Database, desc: 'SQLite 全文搜索' },
  ]

  const statusIcon = (s: string) => {
    if (s === 'completed') return <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
    if (s === 'processing') return <Loader2 className="h-3.5 w-3.5 text-muted-foreground animate-spin" />
    if (s === 'failed') return <AlertCircle className="h-3.5 w-3.5 text-destructive" />
    return <span className="h-2 w-2 rounded-full bg-muted-foreground/30" />
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-[15px] font-semibold">索引管理</h2>
        <p className="text-[13px] text-muted-foreground mt-0.5">管理检索索引和语义标注</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {indexCards.map(({ key, label, icon: Icon, desc }) => (
          <div key={key} className="border rounded-lg bg-white p-4">
            <div className="flex items-center gap-2 mb-2">
              <Icon className="h-4 w-4 text-muted-foreground" />
              <span className="text-[13px] font-medium">{label}</span>
            </div>
            <div className="text-[20px] font-semibold">
              {status?.index_builds?.[`index_${key}` as keyof typeof status.index_builds] ?? '—'}
            </div>
            <p className="text-[12px] text-muted-foreground mt-1">{desc}</p>
            <Button variant="outline" size="sm" className="mt-3 w-full" disabled={rebuilding === key} onClick={() => handleRebuild(key)}>
              {rebuilding === key ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
              重建
            </Button>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Button size="sm" disabled={rebuilding === 'all'} onClick={() => handleRebuild('all')}>
          {rebuilding === 'all' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          重建全部索引
        </Button>
        <Button variant="outline" size="sm" disabled={annotating} onClick={async () => { setAnnotating(true); try { await api.annotateCards('unannotated'); fetchJobs() } catch {} setAnnotating(false) }}>
          {annotating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
          语义标注 (未标注)
        </Button>
      </div>

      <div>
        <h3 className="text-[14px] font-semibold mb-3">最近任务</h3>
        {jobs.length === 0 ? (
          <p className="text-[13px] text-muted-foreground">暂无任务</p>
        ) : (
          <div className="border rounded-lg bg-white divide-y">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center gap-3 px-4 py-3">
                {statusIcon(job.status)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium">{job.job_type}</span>
                    <Badge variant={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'destructive' : job.status === 'processing' ? 'processing' : 'secondary'}>{job.status}</Badge>
                  </div>
                  {job.status === 'processing' && job.total_items > 0 && <Progress value={job.progress} max={job.total_items} className="mt-1 h-1" />}
                  {job.error_message && <p className="text-[12px] text-destructive mt-0.5 truncate">{job.error_message}</p>}
                </div>
                <span className="text-[12px] text-muted-foreground shrink-0">{job.created_at?.slice(11, 19)}</span>
                {job.status === 'failed' && <Button variant="ghost" size="sm" onClick={() => api.retryJob(job.id).then(fetchJobs)}>重试</Button>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}


/* ── LLM Config ── */

function LLMSection() {
  const [config, setConfig] = useState<SystemConfig>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [newProfileName, setNewProfileName] = useState('')

  const fetchConfig = useCallback(async () => {
    setLoading(true)
    try { setConfig(await api.getConfig()) } catch { /* silent */ }
    setLoading(false)
  }, [])

  useEffect(() => { fetchConfig() }, [fetchConfig])

  const handleSave = async () => {
    setSaving(true); setSaved(false)
    try { await api.updateConfig(config); setSaved(true); setTimeout(() => setSaved(false), 2000) } catch { /* silent */ }
    setSaving(false)
  }

  const updateProfile = (name: string, field: keyof LLMProfile, value: string) => {
    setConfig(prev => ({
      ...prev,
      llm_profiles: { ...prev.llm_profiles, [name]: { ...prev.llm_profiles?.[name], [field]: value } },
    }))
  }

  const addProfile = () => {
    const name = newProfileName.trim()
    if (!name || config.llm_profiles?.[name]) return
    setConfig(prev => ({
      ...prev,
      llm_profiles: { ...prev.llm_profiles, [name]: { base_url: '', api_key: '', model: '' } },
    }))
    setNewProfileName('')
  }

  const removeProfile = (name: string) => {
    if (['default', 'annotation', 'generation', 'reply'].includes(name)) return
    setConfig(prev => {
      const profiles = { ...prev.llm_profiles }; delete profiles[name]
      return { ...prev, llm_profiles: profiles }
    })
  }

  if (loading) return <div className="flex items-center justify-center py-16"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>

  const profiles = config.llm_profiles || {}

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[15px] font-semibold">LLM 模型配置</h2>
          <p className="text-[13px] text-muted-foreground mt-0.5">不同任务可使用不同模型，未配置的任务自动使用「默认」配置</p>
        </div>
        <Button size="sm" onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : saved ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Save className="h-3.5 w-3.5" />}
          {saved ? '已保存' : '保存'}
        </Button>
      </div>

      <div className="space-y-3">
        {Object.keys(profiles).map(name => (
          <div key={name} className="border rounded-lg bg-white">
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <div className="flex items-center gap-2">
                <Badge variant={name === 'default' ? 'default' : 'secondary'}>{PROFILE_LABELS[name] || name}</Badge>
                {PROFILE_DESCRIPTIONS[name] && <span className="text-[12px] text-muted-foreground">{PROFILE_DESCRIPTIONS[name]}</span>}
              </div>
              {!['default', 'annotation', 'generation', 'reply'].includes(name) && (
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => removeProfile(name)}><Trash2 className="h-3.5 w-3.5 text-muted-foreground" /></Button>
              )}
            </div>
            <div className="p-4 grid grid-cols-3 gap-3">
              <div>
                <label className="text-[12px] font-medium text-muted-foreground">Base URL</label>
                <Input value={profiles[name]?.base_url || ''} onChange={(e) => updateProfile(name, 'base_url', e.target.value)} placeholder="https://api.siliconflow.cn/v1" className="mt-1" />
              </div>
              <div>
                <label className="text-[12px] font-medium text-muted-foreground">API Key</label>
                <Input type="password" value={profiles[name]?.api_key || ''} onChange={(e) => updateProfile(name, 'api_key', e.target.value)} placeholder="sk-..." className="mt-1" />
              </div>
              <div>
                <label className="text-[12px] font-medium text-muted-foreground">模型</label>
                <Input value={profiles[name]?.model || ''} onChange={(e) => updateProfile(name, 'model', e.target.value)} placeholder="Qwen/Qwen2.5-7B-Instruct" className="mt-1" />
              </div>
            </div>
          </div>
        ))}

        <div className="flex items-center gap-2">
          <Input value={newProfileName} onChange={(e) => setNewProfileName(e.target.value)} placeholder="自定义 profile 名称" className="flex-1" onKeyDown={(e) => e.key === 'Enter' && addProfile()} />
          <Button variant="outline" size="sm" onClick={addProfile} disabled={!newProfileName.trim()}><Plus className="h-3.5 w-3.5" />添加</Button>
        </div>
      </div>
    </div>
  )
}


/* ── Processing ── */

function ProcessingSection() {
  const [config, setConfig] = useState<SystemConfig>({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => { api.getConfig().then(setConfig).catch(() => {}) }, [])

  const update = (key: keyof SystemConfig, value: unknown) => setConfig(prev => ({ ...prev, [key]: value }))

  const handleSave = async () => {
    setSaving(true); setSaved(false)
    try { await api.updateConfig(config); setSaved(true); setTimeout(() => setSaved(false), 2000) } catch { /* silent */ }
    setSaving(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[15px] font-semibold">处理参数</h2>
          <p className="text-[13px] text-muted-foreground mt-0.5">配置文档处理的参数</p>
        </div>
        <Button size="sm" onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : saved ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Save className="h-3.5 w-3.5" />}
          {saved ? '已保存' : '保存'}
        </Button>
      </div>

      <div className="border rounded-lg bg-white divide-y">
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="text-[13px] font-medium">最大分段字符数</div>
            <div className="text-[12px] text-muted-foreground">单个卡片的最大字符数</div>
          </div>
          <Input type="number" value={config.max_section_chars || ''} onChange={(e) => update('max_section_chars', parseInt(e.target.value) || undefined)} placeholder="1500" className="w-28 text-right" />
        </div>
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="text-[13px] font-medium">最大文件大小</div>
            <div className="text-[12px] text-muted-foreground">上传文件大小限制</div>
          </div>
          <div className="flex items-center gap-2">
            <Input type="number" value={config.max_file_size_mb || ''} onChange={(e) => update('max_file_size_mb', parseInt(e.target.value) || undefined)} placeholder="50" className="w-28 text-right" />
            <span className="text-[12px] text-muted-foreground">MB</span>
          </div>
        </div>
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="text-[13px] font-medium">单次最多返回卡片数</div>
            <div className="text-[12px] text-muted-foreground">对话中每次搜索最多展示的卡片数量</div>
          </div>
          <Input type="number" value={config.max_cards_per_response || ''} onChange={(e) => update('max_cards_per_response', parseInt(e.target.value) || undefined)} placeholder="5" className="w-28 text-right" />
        </div>
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="text-[13px] font-medium">对话历史条数</div>
            <div className="text-[12px] text-muted-foreground">发送给 LLM 的历史消息数</div>
          </div>
          <Input type="number" value={config.chat_history_limit || ''} onChange={(e) => update('chat_history_limit', parseInt(e.target.value) || undefined)} placeholder="10" className="w-28 text-right" />
        </div>
      </div>
    </div>
  )
}


/* ── Cache ── */

function CacheSection() {
  const [config, setConfig] = useState<SystemConfig>({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => { api.getConfig().then(setConfig).catch(() => {}) }, [])

  const update = (key: keyof SystemConfig, value: unknown) => setConfig(prev => ({ ...prev, [key]: value }))

  const handleSave = async () => {
    setSaving(true); setSaved(false)
    try { await api.updateConfig(config); setSaved(true); setTimeout(() => setSaved(false), 2000) } catch { /* silent */ }
    setSaving(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[15px] font-semibold">缓存配置</h2>
          <p className="text-[13px] text-muted-foreground mt-0.5">管理查询缓存和路由学习</p>
        </div>
        <Button size="sm" onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : saved ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Save className="h-3.5 w-3.5" />}
          {saved ? '已保存' : '保存'}
        </Button>
      </div>

      <div className="border rounded-lg bg-white divide-y">
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="text-[13px] font-medium">缓存清理天数</div>
            <div className="text-[12px] text-muted-foreground">超过此天数的缓存将被清理</div>
          </div>
          <Input type="number" value={config.cache_evict_days || ''} onChange={(e) => update('cache_evict_days', parseInt(e.target.value) || undefined)} placeholder="30" className="w-28 text-right" />
        </div>
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="text-[13px] font-medium">最大缓存条目</div>
            <div className="text-[12px] text-muted-foreground">缓存条目上限</div>
          </div>
          <Input type="number" value={config.cache_max_entries || ''} onChange={(e) => update('cache_max_entries', parseInt(e.target.value) || undefined)} placeholder="1000" className="w-28 text-right" />
        </div>
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="text-[13px] font-medium">启用路由学习</div>
            <div className="text-[12px] text-muted-foreground">根据用户反馈自动优化路由</div>
          </div>
          <button
            onClick={() => update('route_learning_enabled', !config.route_learning_enabled)}
            className={cn(
              'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors',
              config.route_learning_enabled ? 'bg-foreground' : 'bg-muted-foreground/30'
            )}
          >
            <span className={cn(
              'pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm transition-transform',
              config.route_learning_enabled ? 'translate-x-4' : 'translate-x-0'
            )} />
          </button>
        </div>
      </div>
    </div>
  )
}


/* ── Appearance ── */

function AppearanceSection() {
  const [theme, setTheme] = useState(() => localStorage.getItem('kb-theme') || 'default')

  const themes = [
    { id: 'default', label: '默认', color: 'bg-gray-900' },
    { id: 'blue', label: '蓝色', color: 'bg-blue-600' },
    { id: 'green', label: '绿色', color: 'bg-emerald-600' },
    { id: 'dark', label: '暗色', color: 'bg-gray-950' },
  ]

  const applyTheme = (t: string) => {
    setTheme(t)
    localStorage.setItem('kb-theme', t)
    document.documentElement.setAttribute('data-theme', t)
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-[15px] font-semibold">外观</h2>
        <p className="text-[13px] text-muted-foreground mt-0.5">选择界面主题配色</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {themes.map((t) => (
          <button
            key={t.id}
            onClick={() => applyTheme(t.id)}
            className={cn(
              'border rounded-lg p-4 text-left transition-all cursor-pointer',
              theme === t.id ? 'border-foreground ring-1 ring-foreground' : 'border-border hover:border-muted-foreground/50'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn('w-8 h-8 rounded-full', t.color)} />
              <div>
                <div className="text-[13px] font-medium">{t.label}</div>
                {theme === t.id && <div className="text-[11px] text-muted-foreground">当前主题</div>}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
