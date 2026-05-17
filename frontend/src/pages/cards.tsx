import { useState, useEffect, useCallback } from 'react'
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
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[18px] font-semibold">卡片管理</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            共 {stats?.total ?? '—'} 张卡片
          </p>
        </div>
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="flex flex-wrap gap-1.5">
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
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input placeholder="搜索卡片标题或内容..." className="pl-9 bg-white" />
      </div>

      {/* Card list + Detail panel */}
      <div className="flex gap-4">
        <div className={cn('flex-1', selectedCard && 'lg:max-w-[60%]')}>
          {cards.length === 0 && !loading ? (
            <EmptyState icon={Layers} title="暂无卡片" description="上传文档后自动生成卡片" />
          ) : (
            <div className="border rounded-lg bg-white divide-y">
              {cards.map((card) => (
                <div
                  key={card.id}
                  className={cn(
                    'px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors',
                    selectedCard?.id === card.id && 'bg-muted'
                  )}
                  onClick={() => setSelectedCard(card)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-medium truncate">{card.title || '无标题'}</span>
                        <Badge variant="outline">{card.source_type}</Badge>
                        {card.quality_tier && (
                          <Badge variant={card.quality_tier === 'high' ? 'success' : card.quality_tier === 'low' ? 'warning' : 'secondary'}>
                            {card.quality_tier}
                          </Badge>
                        )}
                      </div>
                      <p className="text-[12px] text-muted-foreground mt-0.5 truncate">{card.body?.slice(0, 100)}</p>
                    </div>
                    <span className="text-[12px] text-muted-foreground shrink-0">{card.path}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {total > pageSize && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-[12px] text-muted-foreground">
                第 {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} / {total}
              </span>
              <div className="flex gap-1">
                <Button variant="outline" size="icon" className="h-7 w-7" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                  <ChevronLeft className="h-3.5 w-3.5" />
                </Button>
                <Button variant="outline" size="icon" className="h-7 w-7" disabled={page * pageSize >= total} onClick={() => setPage(p => p + 1)}>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selectedCard && (
          <div className="w-[40%] hidden lg:block border rounded-lg bg-white sticky top-[64px] max-h-[calc(100vh-80px)] overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <h3 className="text-[14px] font-semibold">卡片详情</h3>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setSelectedCard(null)}>
                &times;
              </Button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="text-[12px] text-muted-foreground">标题</label>
                <p className="text-[13px] font-medium mt-0.5">{selectedCard.title || '无标题'}</p>
              </div>

              <div>
                <label className="text-[12px] text-muted-foreground">内容</label>
                <div className="mt-1 rounded-md bg-muted p-3 font-mono text-[13px] whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                  {selectedCard.body}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[12px] text-muted-foreground">来源</label>
                  <p className="text-[13px] mt-0.5">{selectedCard.source_type} · {selectedCard.doc_file}</p>
                </div>
                <div>
                  <label className="text-[12px] text-muted-foreground">路径</label>
                  <p className="text-[13px] mt-0.5">{selectedCard.path}</p>
                </div>
                <div>
                  <label className="text-[12px] text-muted-foreground">质量</label>
                  <p className="text-[13px] mt-0.5">{selectedCard.quality_tier || '未评定'}</p>
                </div>
              </div>

              {selectedCard?.intent_tags?.length > 0 && (
                <div>
                  <label className="text-[12px] text-muted-foreground">标签</label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedCard.intent_tags.filter(Boolean).map((tag) => (
                      <Badge key={tag} variant="outline">{tag.trim()}</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-2 border-t">
                <Button variant="destructive" size="sm" onClick={() => handleDelete(selectedCard.id)}>
                  <Trash2 className="h-3.5 w-3.5" />
                  删除
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
