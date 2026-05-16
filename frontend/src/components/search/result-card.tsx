import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SourcePill } from './source-pill'
import { Copy, ExternalLink, ThumbsUp, ThumbsDown } from 'lucide-react'
import type { SearchResult } from '@/lib/api'
import { cn } from '@/lib/utils'

function hitRateColor(rate: number): string {
  if (rate >= 0.85) return 'text-hit-high'
  if (rate >= 0.65) return 'text-hit-medium'
  if (rate >= 0.5) return 'text-hit-low'
  return 'text-muted-foreground'
}

function hitRateLabel(rate: number): string {
  if (rate >= 0.85) return '强命中'
  if (rate >= 0.65) return '较相关'
  if (rate >= 0.5) return '可能相关'
  return '低质量'
}

interface ResultCardProps {
  result: SearchResult
  onCopy: (text: string) => void
  onFeedback: (cardId: string, rating: 'positive' | 'negative') => void
}

export function ResultCard({ result, onCopy, onFeedback }: ResultCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-lg font-heading font-semibold text-muted-foreground">
              #{result.rank}
            </span>
            <div>
              <span className={cn('text-lg font-semibold font-heading', hitRateColor(result.hit_rate))}>
                {Math.round(result.hit_rate * 100)}%
              </span>
              <span className="text-meta text-muted-foreground ml-2">
                {hitRateLabel(result.hit_rate)}
              </span>
            </div>
            <SourcePill
              sourceType={result.source_type}
              fileName={result.source_file}
              path={result.path}
            />
          </div>
        </div>

        <h3 className="font-heading text-h2 mt-3">{result.title}</h3>

        <div className="mt-2 rounded-md bg-surface-container p-3 font-mono text-body-small leading-relaxed whitespace-pre-wrap max-h-[200px] overflow-y-auto">
          {result.body}
        </div>

        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-1">
            {result.intent_tags?.map((tag) => (
              <Badge key={tag} variant="outline" className="text-meta">
                {tag}
              </Badge>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={() => onCopy(result.body)}>
              <Copy className="h-4 w-4" />
              复制原文
            </Button>
            <Button variant="ghost" size="sm">
              <ExternalLink className="h-4 w-4" />
              查看出处
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onFeedback(result.card_id, 'positive')}>
              <ThumbsUp className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onFeedback(result.card_id, 'negative')}>
              <ThumbsDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
