import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/shared/empty-state'
import { api, type Card as CardType, type CardStats } from '@/lib/api'
import { Layers, Search, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function CardsPage() {
  const [cards, setCards] = useState<CardType[]>([])
  const [stats, setStats] = useState<CardStats | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [sourceFilter, setSourceFilter] = useState<string>('')
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

      {/* Search */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="搜索卡片标题或内容..." className="pl-9" />
        </div>
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
              </div>

              {selectedCard.intent_tags && (
                <div>
                  <label className="text-meta text-muted-foreground">标签</label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(Array.isArray(selectedCard.intent_tags) ? selectedCard.intent_tags : selectedCard.intent_tags.split(',')).filter(Boolean).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-meta">{String(tag).trim()}</Badge>
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
