import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SourcePill } from './source-pill'
import { Copy, ExternalLink, ThumbsUp, ThumbsDown } from 'lucide-react'
import type { SearchResult } from '@/lib/api'
import { cn } from '@/lib/utils'

function hitRateColor(rate: number): string {
  if (rate >= 0.85) return 'text-success'
  if (rate >= 0.65) return 'text-foreground'
  if (rate >= 0.5) return 'text-warning'
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
    <div className="border rounded-lg bg-white p-4 hover:bg-muted/50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-[13px] font-medium text-muted-foreground">
            #{result.rank}
          </span>
          <div>
            <span className={cn('text-[15px] font-semibold', hitRateColor(result.hit_rate))}>
              {Math.round(result.hit_rate * 100)}%
            </span>
            <span className="text-[12px] text-muted-foreground ml-2">
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

      <h3 className="text-[14px] font-semibold mt-3">{result.title}</h3>

      <div className="mt-2 rounded-md bg-muted p-3 font-mono text-[13px] leading-relaxed whitespace-pre-wrap max-h-[200px] overflow-y-auto">
        {result.body}
      </div>

      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-1">
          {result.intent_tags?.map((tag) => (
            <Badge key={tag} variant="outline">
              {tag}
            </Badge>
          ))}
        </div>
        <div className="flex items-center gap-0.5">
          <Button variant="ghost" size="sm" onClick={() => onCopy(result.body)}>
            <Copy className="h-3.5 w-3.5" />
            复制
          </Button>
          <Button variant="ghost" size="sm">
            <ExternalLink className="h-3.5 w-3.5" />
            出处
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onFeedback(result.card_id, 'positive')}>
            <ThumbsUp className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onFeedback(result.card_id, 'negative')}>
            <ThumbsDown className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
