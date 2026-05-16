import { useState } from 'react'
import { SearchInput } from '@/components/search/search-input'
import { ResultCard } from '@/components/search/result-card'
import { EmptyState } from '@/components/shared/empty-state'
import { Badge } from '@/components/ui/badge'
import { api, type QueryResponse } from '@/lib/api'
import { Search, AlertCircle } from 'lucide-react'

const exampleQueries = [
  'AE800 的价格是多少',
  'PE8000 什么时候停产',
  '公安行业怎么推',
  'XE800 与 AE800 接口对比',
  '软件端和硬件端的区别',
]

export default function SearchPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (query: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.query(query)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '查询失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const handleFeedback = async (cardId: string, rating: 'positive' | 'negative') => {
    try {
      await api.feedback(cardId, rating)
    } catch {
      // silent
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="font-heading text-h1">查询</h1>
        <p className="text-muted-foreground text-body-small mt-1">
          输入问题，从知识库中查找原文和出处
        </p>
      </div>

      <SearchInput onSearch={handleSearch} loading={loading} />

      {!result && !loading && !error && (
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((q) => (
            <Badge
              key={q}
              variant="outline"
              className="cursor-pointer hover:bg-accent"
              onClick={() => handleSearch(q)}
            >
              {q}
            </Badge>
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-md bg-destructive/10 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-meta text-muted-foreground">
            <span>路由：{result.route}</span>
            {result.cache_hit && <Badge variant="secondary">缓存命中</Badge>}
            <span>{result.latency_ms}ms</span>
            <span>共 {result.total} 条结果</span>
          </div>

          {result.results.length === 0 ? (
            <EmptyState
              icon={Search}
              title="没有找到匹配结果"
              description="可以尝试换关键词、开启低质量结果，或确认文档是否已上传"
            />
          ) : (
            <div className="space-y-3">
              {result.results.map((r) => (
                <ResultCard
                  key={r.card_id}
                  result={r}
                  onCopy={handleCopy}
                  onFeedback={handleFeedback}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
