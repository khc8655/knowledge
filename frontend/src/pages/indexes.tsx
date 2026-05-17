import { useState, useEffect, useCallback } from 'react'
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
    if (s === 'completed') return <CheckCircle2 className="h-3.5 w-3.5 text-success" />
    if (s === 'processing') return <Loader2 className="h-3.5 w-3.5 text-muted-foreground animate-spin" />
    if (s === 'failed') return <AlertCircle className="h-3.5 w-3.5 text-destructive" />
    return <span className="h-2 w-2 rounded-full bg-muted-foreground/30" />
  }

  return (
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-[18px] font-semibold">索引管理</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">
          管理检索索引和语义标注
        </p>
      </div>

      {/* Index status cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {indexCards.map(({ key, label, icon: Icon, desc }) => (
          <div key={key} className="border rounded-lg bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <Icon className="h-4 w-4 text-muted-foreground" />
              <span className="text-[13px] font-medium">{label}</span>
            </div>
            <div className="text-[20px] font-semibold">
              {status?.index_builds?.[`index_${key}` as keyof typeof status.index_builds] ?? '—'}
            </div>
            <p className="text-[12px] text-muted-foreground mt-1">{desc}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3 w-full"
              disabled={rebuilding === key}
              onClick={() => handleRebuild(key)}
            >
              {rebuilding === key ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
              重建
            </Button>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={rebuilding === 'all'}
          onClick={() => handleRebuild('all')}
        >
          {rebuilding === 'all' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          重建全部索引
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={annotating}
          onClick={handleAnnotate}
        >
          {annotating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
          语义标注 (未标注)
        </Button>
      </div>

      {/* Recent jobs */}
      <div>
        <h2 className="text-[14px] font-semibold mb-3">最近任务</h2>
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
                    <Badge variant={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'destructive' : job.status === 'processing' ? 'processing' : 'secondary'}>
                      {job.status}
                    </Badge>
                  </div>
                  {job.status === 'processing' && job.total_items > 0 && (
                    <Progress value={job.progress} max={job.total_items} className="mt-1 h-1" />
                  )}
                  {job.error_message && (
                    <p className="text-[12px] text-destructive mt-0.5 truncate">{job.error_message}</p>
                  )}
                </div>
                <span className="text-[12px] text-muted-foreground shrink-0">
                  {job.created_at?.slice(11, 19)}
                </span>
                {job.status === 'failed' && (
                  <Button variant="ghost" size="sm" onClick={() => api.retryJob(job.id).then(fetchJobs)}>
                    重试
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
