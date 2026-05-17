import { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/shared/empty-state'
import { api, type UploadedDocument } from '@/lib/api'
import { Upload, FileText, Trash2, RefreshCw, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

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
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-[18px] font-semibold">上传文档</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">
          支持 {ACCEPTED_TYPES.join(' ')} 格式，最大 {MAX_SIZE_MB}MB
        </p>
      </div>

      {/* Dropzone */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          dragging ? 'border-foreground bg-muted' : 'border-border hover:border-muted-foreground/50'
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
        <Upload className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
        <p className="text-[13px] font-medium">拖拽文件到此处，或点击选择</p>
        <p className="text-[12px] text-muted-foreground mt-1">可同时上传多个文件</p>
        {uploading && <Loader2 className="h-4 w-4 animate-spin mx-auto mt-2 text-muted-foreground" />}
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-[13px]">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-success/10 text-success text-[13px]">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {success}
        </div>
      )}

      {/* Document list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[14px] font-semibold">已上传文档 ({total})</h2>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchDocuments}>
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
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
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleReprocess(doc.id)} title="重新处理">
                    <RefreshCw className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDelete(doc.id)} title="删除">
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
