# Frontend Phase 2: Knowledge Management Pages

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 4 knowledge management pages: Upload (drag-and-drop), Cards (list/detail/edit), Indexes (status/rebuild), Settings (config editor).

**Architecture:** Each page is a standalone React component using the API client from Phase 1. New API endpoints are added to `api.ts`. Components follow the Stitch design system tokens.

**Tech Stack:** React 19, TypeScript, TailwindCSS 4, shadcn/ui, Zustand, Lucide icons

---

## File Structure

**Modified files:**
- `frontend/src/lib/api.ts` — Add upload, card, index, config, job API functions
- `frontend/src/app.tsx` — Replace placeholder routes with real pages

**New files:**
- `frontend/src/pages/upload.tsx` — Upload page with dropzone and file list
- `frontend/src/pages/cards.tsx` — Card list with filters and detail drawer
- `frontend/src/pages/indexes.tsx` — Index status and rebuild controls
- `frontend/src/pages/settings.tsx` — System config editor

---

### Task 1: Extend API Client

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add new types and API functions**

Add to `api.ts` after existing types:

```typescript
export interface UploadedDocument {
  id: number
  filename: string
  file_type: string
  file_size: number
  sha256: string
  cards_count: number
  pipeline_status: string
  is_current: number
  created_at: string
}

export interface CardDetail {
  id: string
  doc_file: string
  source_type: string
  title: string
  body: string
  path: string
  keywords: string
  intent_tags: string
  quality_tier: string
  hit_count: number
  miss_count: number
  char_count: number
  created_at: string
  updated_at: string
}

export interface CardStats {
  total: number
  by_source_type: Record<string, number>
  by_quality_tier: Record<string, number>
}

export interface IndexStatus {
  index_builds: { index_bm25: number; index_vector: number; index_fts5: number }
  pending_jobs: number
}

export interface Job {
  id: number
  job_type: string
  status: string
  progress: number
  total_items: number
  error_message: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface SystemConfig {
  llm_api_key?: string
  llm_base_url?: string
  llm_model?: string
  embedding_model?: string
  max_section_chars?: number
  max_file_size_mb?: number
  route_learning_enabled?: boolean
  cache_evict_days?: number
  cache_max_entries?: number
}
```

Add to `api` object:

```typescript
// Upload
uploadFile: async (file: File, forceOverwrite = false): Promise<{ status: string; file_id: number; filename: string; file_type: string; jobs_created: number }> => {
  const formData = new FormData()
  formData.append('file', file)
  if (forceOverwrite) formData.append('force_overwrite', 'true')
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: formData })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.json()
},

listDocuments: (params?: { page?: number; page_size?: number; file_type?: string }) => {
  const qs = new URLSearchParams()
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  if (params?.file_type) qs.set('file_type', params.file_type)
  return request<{ total: number; page: number; page_size: number; items: UploadedDocument[] }>(`/upload/documents?${qs}`)
},

deleteDocument: (docId: number) =>
  request<{ status: string; id: number }>(`/upload/documents/${docId}`, { method: 'DELETE' }),

reprocessDocument: (docId: number) =>
  request<{ status: string; document_id: number; jobs_created: number }>(`/upload/documents/${docId}/reprocess`, { method: 'POST' }),

// Cards
getCardStats: () => request<CardStats>('/cards/stats'),

getCard: (cardId: string) => request<CardDetail>(`/cards/${cardId}`),

updateCard: (cardId: string, data: { title?: string; body?: string; tags?: string; keywords?: string }) =>
  request<{ status: string; id: string }>(`/cards/${cardId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

deleteCard: (cardId: string) =>
  request<{ status: string; id: string }>(`/cards/${cardId}`, { method: 'DELETE' }),

// Indexes
getIndexStatus: () => request<IndexStatus>('/indexes/status'),

rebuildIndex: (indexType: string) =>
  request<{ status: string; index_type: string; job_ids: number[] }>(`/indexes/rebuild/${indexType}`, { method: 'POST' }),

annotateCards: (scope = 'all') =>
  request<{ status: string; job_id: number }>(`/indexes/annotate?scope=${scope}`, { method: 'POST' }),

// Jobs
listJobs: (params?: { status?: string; type?: string; page?: number; page_size?: number }) => {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.type) qs.set('type', params.type)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  return request<{ total: number; page: number; page_size: number; items: Job[] }>(`/jobs?${qs}`)
},

retryJob: (jobId: number) =>
  request<{ status: string; job_id: number }>(`/jobs/${jobId}/retry`, { method: 'POST' }),

// Config
getConfig: () => request<SystemConfig>('/config'),

updateConfig: (data: Partial<SystemConfig>) =>
  request<{ status: string; config: SystemConfig }>('/config', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
```

- [ ] **Step 2: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/lib/api.ts && git commit -m "feat: extend API client with upload, card, index, config, job endpoints"
```

---

### Task 2: Upload Page

**Files:**
- Create: `frontend/src/pages/upload.tsx`
- Modify: `frontend/src/app.tsx`

- [ ] **Step 1: Create upload.tsx**

```typescript
import { useState, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { EmptyState } from '@/components/shared/empty-state'
import { api, type UploadedDocument } from '@/lib/api'
import { Upload, FileText, Trash2, RefreshCw, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEffect } from 'react'

const ACCEPTED_TYPES = ['.txt', '.md', '.docx', '.xlsx', '.pptx', '.pdf']
const MAX_SIZE_MB = 50

export default function UploadPage() {
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
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  const handleFiles = async (files: FileList | File[]) => {
    setError(null)
    setSuccess(null)
    for (const file of Array.from(files)) {
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        setError(`${file.name} 超过 ${MAX_SIZE_MB}MB 限制`)
        continue
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
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files)
  }

  const handleDelete = async (docId: number) => {
    try {
      await api.deleteDocument(docId)
      fetchDocuments()
    } catch {
      // silent
    }
  }

  const handleReprocess = async (docId: number) => {
    try {
      await api.reprocessDocument(docId)
      fetchDocuments()
    } catch {
      // silent
    }
  }

  const fileTypeLabel = (t: string) => {
    const map: Record<string, string> = { txt: 'TXT', md: 'Markdown', docx: 'Word', xlsx: 'Excel', pptx: 'PPT', pdf: 'PDF' }
    return map[t] || t
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

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-heading text-h1">上传文档</h1>
        <p className="text-muted-foreground text-body-small mt-1">
          支持 {ACCEPTED_TYPES.join(' ')} 格式，最大 {MAX_SIZE_MB}MB
        </p>
      </div>

      {/* Dropzone */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          dragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
        )}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES.join(',')}
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
        <p className="text-body font-medium">拖拽文件到此处，或点击选择</p>
        <p className="text-meta text-muted-foreground mt-1">可同时上传多个文件</p>
        {uploading && <Loader2 className="h-5 w-5 animate-spin mx-auto mt-3 text-primary" />}
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-body-small">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-success/10 text-success text-body-small">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {success}
        </div>
      )}

      {/* Document list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-heading text-h2">已上传文档 ({total})</h2>
          <Button variant="ghost" size="sm" onClick={fetchDocuments}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {documents.length === 0 && !loading ? (
          <EmptyState icon={FileText} title="暂无文档" description="上传文档开始构建知识库" />
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <Card key={doc.id} className="hover:shadow-sm transition-shadow">
                <CardContent className="p-4 flex items-center gap-4">
                  <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-body truncate">{doc.filename}</span>
                      <Badge variant="outline" className="text-meta">{fileTypeLabel(doc.file_type)}</Badge>
                      {statusBadge(doc.pipeline_status)}
                    </div>
                    <div className="text-meta text-muted-foreground mt-0.5">
                      {(doc.file_size / 1024).toFixed(1)} KB · {doc.cards_count} 张卡片 · {doc.created_at?.slice(0, 16)}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" onClick={() => handleReprocess(doc.id)} title="重新处理">
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(doc.id)} title="删除">
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {total > 20 && (
          <div className="flex justify-center gap-2 mt-4">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
            <span className="text-body-small text-muted-foreground leading-8">第 {page} 页</span>
            <Button variant="outline" size="sm" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}>下一页</Button>
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Update app.tsx route**

Replace the upload placeholder route with the real page import.

- [ ] **Step 3: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/pages/upload.tsx frontend/src/app.tsx && git commit -m "feat: add upload page with drag-and-drop and document list"
```

---

### Task 3: Cards Page

**Files:**
- Create: `frontend/src/pages/cards.tsx`
- Modify: `frontend/src/app.tsx`

- [ ] **Step 1: Create cards.tsx**

```typescript
import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/shared/empty-state'
import { api, type Card as CardType, type CardStats } from '@/lib/api'
import { Layers, Search, Trash2, Eye, ChevronLeft, ChevronRight, BarChart3 } from 'lucide-react'

export default function CardsPage() {
  const [cards, setCards] = useState<CardType[]>([])
  const [stats, setStats] = useState<CardStats | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [qualityFilter, setQualityFilter] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [selectedCard, setSelectedCard] = useState<CardType | null>(null)
  const pageSize = 20

  const fetchCards = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listCards({
        page,
        page_size: pageSize,
        source_type: sourceFilter || undefined,
      })
      setCards(data.items)
      setTotal(data.total)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [page, sourceFilter])

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getCardStats()
      setStats(data)
    } catch {
      // silent
    }
  }, [])

  useEffect(() => { fetchCards() }, [fetchCards])
  useEffect(() => { fetchStats() }, [fetchStats])

  const handleDelete = async (cardId: string) => {
    try {
      await api.deleteCard(cardId)
      setSelectedCard(null)
      fetchCards()
      fetchStats()
    } catch {
      // silent
    }
  }

  const sourceTypes = stats ? Object.entries(stats.by_source_type) : []
  const qualityTiers = stats ? Object.entries(stats.by_quality_tier) : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-h1">卡片管理</h1>
          <p className="text-muted-foreground text-body-small mt-1">
            共 {stats?.total ?? '—'} 张卡片
          </p>
        </div>
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="flex flex-wrap gap-2">
          {sourceTypes.map(([type, count]) => (
            <Badge
              key={type}
              variant={sourceFilter === type ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => { setSourceFilter(sourceFilter === type ? '' : type); setPage(1) }}
            >
              {type}: {count}
            </Badge>
          ))}
        </div>
      )}

      {/* Search and filters */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索卡片标题或内容..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <select
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
          value={qualityFilter}
          onChange={(e) => { setQualityFilter(e.target.value); setPage(1) }}
        >
          <option value="">全部质量</option>
          <option value="high">高质量</option>
          <option value="medium">中等</option>
          <option value="low">低质量</option>
        </select>
      </div>

      {/* Card list + Detail panel */}
      <div className="flex gap-4">
        <div className={cn('flex-1 space-y-2', selectedCard && 'lg:max-w-[60%]')}>
          {cards.length === 0 && !loading ? (
            <EmptyState icon={Layers} title="暂无卡片" description="上传文档后自动生成卡片" />
          ) : (
            cards.map((card) => (
              <Card
                key={card.id}
                className={cn(
                  'cursor-pointer hover:shadow-sm transition-shadow',
                  selectedCard?.id === card.id && 'ring-2 ring-primary'
                )}
                onClick={() => setSelectedCard(card)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-body truncate">{card.title || '无标题'}</span>
                        <Badge variant="outline" className="text-meta shrink-0">{card.source_type}</Badge>
                        {card.quality_tier && (
                          <Badge variant={card.quality_tier === 'high' ? 'success' : card.quality_tier === 'low' ? 'warning' : 'secondary'} className="text-meta shrink-0">
                            {card.quality_tier}
                          </Badge>
                        )}
                      </div>
                      <p className="text-meta text-muted-foreground mt-1 truncate">{card.body?.slice(0, 100)}</p>
                    </div>
                    <span className="text-meta text-muted-foreground shrink-0">{card.path}</span>
                  </div>
                </CardContent>
              </Card>
            ))
          )}

          {/* Pagination */}
          {total > pageSize && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-meta text-muted-foreground">
                第 {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} / {total}
              </span>
              <div className="flex gap-1">
                <Button variant="outline" size="icon" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" disabled={page * pageSize >= total} onClick={() => setPage(p => p + 1)}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selectedCard && (
          <Card className="w-[40%] hidden lg:block sticky top-[80px] max-h-[calc(100vh-120px)] overflow-y-auto">
            <CardContent className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-heading text-h2">卡片详情</h3>
                <Button variant="ghost" size="icon" onClick={() => setSelectedCard(null)}>
                  &times;
                </Button>
              </div>

              <div>
                <label className="text-meta text-muted-foreground">标题</label>
                <p className="text-body font-medium">{selectedCard.title || '无标题'}</p>
              </div>

              <div>
                <label className="text-meta text-muted-foreground">内容</label>
                <div className="mt-1 rounded-md bg-surface-container p-3 font-mono text-body-small whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                  {selectedCard.body}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-meta text-muted-foreground">来源</label>
                  <p className="text-body-small">{selectedCard.source_type} · {selectedCard.doc_file}</p>
                </div>
                <div>
                  <label className="text-meta text-muted-foreground">路径</label>
                  <p className="text-body-small">{selectedCard.path}</p>
                </div>
                <div>
                  <label className="text-meta text-muted-foreground">质量</label>
                  <p className="text-body-small">{selectedCard.quality_tier || '未评定'}</p>
                </div>
                <div>
                  <label className="text-meta text-muted-foreground">字符数</label>
                  <p className="text-body-small">{selectedCard.char_count}</p>
                </div>
              </div>

              {selectedCard.intent_tags && (
                <div>
                  <label className="text-meta text-muted-foreground">标签</label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedCard.intent_tags.split(',').filter(Boolean).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-meta">{tag.trim()}</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button variant="destructive" size="sm" onClick={() => handleDelete(selectedCard.id)}>
                  <Trash2 className="h-4 w-4" />
                  删除
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
```

Note: Add `import { cn } from '@/lib/utils'` at top.

- [ ] **Step 2: Update app.tsx route**

Replace the cards placeholder route with the real page import.

- [ ] **Step 3: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/pages/cards.tsx frontend/src/app.tsx && git commit -m "feat: add card management page with list, filter, and detail panel"
```

---

### Task 4: Indexes Page

**Files:**
- Create: `frontend/src/pages/indexes.tsx`
- Modify: `frontend/src/app.tsx`

- [ ] **Step 1: Create indexes.tsx**

```typescript
import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { api, type IndexStatus, type Job } from '@/lib/api'
import { Database, RefreshCw, Cpu, FileSearch, Sparkles, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'

export default function IndexesPage() {
  const [status, setStatus] = useState<IndexStatus | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [rebuilding, setRebuilding] = useState<string | null>(null)
  const [annotating, setAnnotating] = useState(false)

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.getIndexStatus()
      setStatus(data)
    } catch {
      // silent
    }
  }, [])

  const fetchJobs = useCallback(async () => {
    try {
      const data = await api.listJobs({ page_size: 10 })
      setJobs(data.items)
    } catch {
      // silent
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    fetchJobs()
    const interval = setInterval(() => { fetchStatus(); fetchJobs() }, 10000)
    return () => clearInterval(interval)
  }, [fetchStatus, fetchJobs])

  const handleRebuild = async (indexType: string) => {
    setRebuilding(indexType)
    try {
      await api.rebuildIndex(indexType)
      fetchStatus()
      fetchJobs()
    } catch {
      // silent
    }
    setRebuilding(null)
  }

  const handleAnnotate = async () => {
    setAnnotating(true)
    try {
      await api.annotateCards('unannotated')
      fetchJobs()
    } catch {
      // silent
    }
    setAnnotating(false)
  }

  const indexCards = [
    { key: 'bm25', label: 'BM25 索引', icon: FileSearch, desc: '关键词检索，支持中文分词' },
    { key: 'vector', label: '向量索引', icon: Cpu, desc: '语义检索，基于 embedding' },
    { key: 'fts5', label: 'FTS5 全文索引', icon: Database, desc: 'SQLite 全文搜索' },
  ]

  const statusIcon = (s: string) => {
    if (s === 'completed') return <CheckCircle2 className="h-4 w-4 text-success" />
    if (s === 'processing') return <Loader2 className="h-4 w-4 text-processing animate-spin" />
    if (s === 'failed') return <AlertCircle className="h-4 w-4 text-destructive" />
    return <span className="h-4 w-4 rounded-full bg-muted-foreground/30" />
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-heading text-h1">索引管理</h1>
        <p className="text-muted-foreground text-body-small mt-1">
          管理检索索引和语义标注
        </p>
      </div>

      {/* Index status cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {indexCards.map(({ key, label, icon: Icon, desc }) => (
          <Card key={key}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Icon className="h-4 w-4" />
                {label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-heading font-bold">
                {status?.index_builds?.[`index_${key}` as keyof typeof status.index_builds] ?? '—'}
              </div>
              <p className="text-meta text-muted-foreground mt-1">{desc}</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full"
                disabled={rebuilding === key}
                onClick={() => handleRebuild(key)}
              >
                {rebuilding === key ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <RefreshCw className="h-4 w-4 mr-1" />}
                重建
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          variant="default"
          disabled={rebuilding === 'all'}
          onClick={() => handleRebuild('all')}
        >
          {rebuilding === 'all' ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <RefreshCw className="h-4 w-4 mr-1" />}
          重建全部索引
        </Button>
        <Button
          variant="outline"
          disabled={annotating}
          onClick={handleAnnotate}
        >
          {annotating ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
          语义标注 (未标注)
        </Button>
      </div>

      {/* Recent jobs */}
      <div>
        <h2 className="font-heading text-h2 mb-3">最近任务</h2>
        {jobs.length === 0 ? (
          <p className="text-muted-foreground text-body-small">暂无任务</p>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <Card key={job.id}>
                <CardContent className="p-3 flex items-center gap-3">
                  {statusIcon(job.status)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-body-small font-medium">{job.job_type}</span>
                      <Badge variant={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'destructive' : job.status === 'processing' ? 'processing' : 'secondary'}>
                        {job.status}
                      </Badge>
                    </div>
                    {job.status === 'processing' && job.total_items > 0 && (
                      <Progress value={job.progress} max={job.total_items} className="mt-1 h-1" />
                    )}
                    {job.error_message && (
                      <p className="text-meta text-destructive mt-0.5 truncate">{job.error_message}</p>
                    )}
                  </div>
                  <span className="text-meta text-muted-foreground shrink-0">
                    {job.created_at?.slice(11, 19)}
                  </span>
                  {job.status === 'failed' && (
                    <Button variant="ghost" size="sm" onClick={() => api.retryJob(job.id).then(fetchJobs)}>
                      重试
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Update app.tsx route**

Replace the indexes placeholder route with the real page import.

- [ ] **Step 3: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/pages/indexes.tsx frontend/src/app.tsx && git commit -m "feat: add index management page with rebuild and annotation controls"
```

---

### Task 5: Settings Page

**Files:**
- Create: `frontend/src/pages/settings.tsx`
- Modify: `frontend/src/app.tsx`

- [ ] **Step 1: Create settings.tsx**

```typescript
import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { api, type SystemConfig } from '@/lib/api'
import { Settings, Save, Loader2, CheckCircle2 } from 'lucide-react'

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
```

- [ ] **Step 2: Update app.tsx route**

Replace the settings placeholder route with the real page import.

- [ ] **Step 3: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/pages/settings.tsx frontend/src/app.tsx && git commit -m "feat: add settings page with LLM, processing, and cache config"
```

---

### Task 6: Final Verification

- [ ] **Step 1: Full build check**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit && npx vite build`
Expected: Build succeeds

- [ ] **Step 2: Final commit**

```bash
cd /home/jjb/kb-platform && git add frontend/ && git commit -m "feat: frontend phase 2 complete - upload, cards, indexes, settings pages"
```
