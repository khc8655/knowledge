import { useEffect, useRef, useState } from 'react'
import type { ChatMessage, ChatCard } from '@/lib/chat-api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api } from '@/lib/api'
import { Copy, FileText, Table, Presentation, Loader2, ThumbsUp, ThumbsDown, ExternalLink } from 'lucide-react'

interface Props {
  messages: ChatMessage[]
  isStreaming: boolean
  streamingThinking: string
  streamingCards: ChatCard[]
  streamingContent: string
}

const sourceIcons: Record<string, typeof FileText> = {
  word: FileText,
  excel: Table,
  ppt: Presentation,
  markdown: FileText,
  txt: FileText,
}

const sourceLabels: Record<string, string> = {
  word: 'Word',
  excel: 'Excel',
  ppt: 'PPT',
  markdown: 'Markdown',
  txt: '文本',
}

function InlineCard({ card }: { card: ChatCard }) {
  const [expanded, setExpanded] = useState(false)
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null)
  const Icon = sourceIcons[card.source_type] || FileText
  const hitColor = card.hit_rate >= 0.85 ? 'text-green-600' : card.hit_rate >= 0.65 ? 'text-foreground' : 'text-muted-foreground'

  const handleFeedback = async (type: 'positive' | 'negative') => {
    setFeedback(type)
    try {
      await api.feedback(card.card_id, type)
    } catch { /* silent */ }
  }

  return (
    <>
      <Card className="hover:shadow-md transition-all duration-200 cursor-pointer group border-border/50 rounded-xl" onClick={() => setExpanded(true)}>
        <CardContent className="p-3.5 flex gap-3">
          {/* Left: meta */}
          <div className="flex flex-col items-center gap-1 shrink-0 w-14">
            <Icon className="h-4 w-4 text-muted-foreground" />
            <Badge variant="outline" className="text-[10px] px-1 py-0">
              {sourceLabels[card.source_type] || card.source_type}
            </Badge>
            {card.brand && (
              <Badge variant="secondary" className="text-[10px] px-1 py-0">
                {card.brand}
              </Badge>
            )}
            <span className={`text-xs font-mono ${hitColor}`}>
              {(card.hit_rate * 100).toFixed(0)}%
            </span>
          </div>

          {/* Center: content */}
          <div className="flex-1 min-w-0 space-y-1.5">
            <p className="text-[13px] font-medium leading-snug">{card.title}</p>
            <div className="h-24 overflow-y-auto text-xs text-muted-foreground leading-relaxed bg-muted/30 rounded p-2">
              {card.body}
            </div>
          </div>

          {/* Right: actions */}
          <div className="flex flex-col items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(card.body) }}
              title="复制"
            >
              <Copy className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant={feedback === 'positive' ? 'default' : 'ghost'}
              size="icon"
              className="h-7 w-7"
              onClick={(e) => { e.stopPropagation(); handleFeedback('positive') }}
              title="有用"
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant={feedback === 'negative' ? 'destructive' : 'ghost'}
              size="icon"
              className="h-7 w-7"
              onClick={(e) => { e.stopPropagation(); handleFeedback('negative') }}
              title="不相关"
            >
              <ThumbsDown className="h-3.5 w-3.5" />
            </Button>
            <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity mt-auto" />
          </div>
        </CardContent>
      </Card>

      {/* Expanded dialog */}
      <Dialog open={expanded} onOpenChange={setExpanded}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-base flex items-center gap-2">
              <Icon className="h-4 w-4" />
              {card.title}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline">{sourceLabels[card.source_type] || card.source_type}</Badge>
              {card.brand && <Badge variant="secondary">{card.brand}</Badge>}
              <span>来源: {card.doc_file}</span>
              <span className={`font-mono ${hitColor}`}>命中率: {(card.hit_rate * 100).toFixed(0)}%</span>
            </div>
            <div className="text-sm leading-relaxed whitespace-pre-wrap bg-muted/30 rounded-lg p-4">
              {card.body}
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => navigator.clipboard.writeText(card.body)}>
                <Copy className="h-3.5 w-3.5 mr-1.5" /> 复制内容
              </Button>
              <div className="ml-auto flex gap-1">
                <Button
                  variant={feedback === 'positive' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleFeedback('positive')}
                >
                  <ThumbsUp className="h-3.5 w-3.5 mr-1.5" /> 有用
                </Button>
                <Button
                  variant={feedback === 'negative' ? 'destructive' : 'outline'}
                  size="sm"
                  onClick={() => handleFeedback('negative')}
                >
                  <ThumbsDown className="h-3.5 w-3.5 mr-1.5" /> 不相关
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}

function ThinkingIndicator({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{text || '思考中...'}</span>
    </div>
  )
}

function MessageCards({ cards }: { cards: ChatCard[] }) {
  return (
    <div className="space-y-2">
      {cards.map((card) => (
        <InlineCard key={card.card_id} card={card} />
      ))}
    </div>
  )
}

export function MessageList({ messages, isStreaming, streamingThinking, streamingCards, streamingContent }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent, streamingCards])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center py-24">
            <div className="w-14 h-14 rounded-2xl bg-primary flex items-center justify-center mx-auto mb-5 shadow-lg shadow-primary/20">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-foreground mb-2">知识库助手</h2>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">输入问题查询知识库，或让我帮你生成方案、BOM清单、客户回复等</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={msg.role === 'user' ? 'flex justify-end' : ''}>
            {msg.role === 'user' ? (
              <div className="bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[80%] text-sm shadow-sm">
                {msg.content}
              </div>
            ) : (
              <div className="space-y-3 w-full">
                {msg.cards && msg.cards.length > 0 && (
                  <MessageCards cards={msg.cards} />
                )}
                {msg.intent && msg.intent !== 'general' && (
                  <Badge variant="outline" className="text-xs">{msg.intent}</Badge>
                )}
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
              </div>
            )}
          </div>
        ))}

        {/* Streaming state */}
        {isStreaming && (
          <div className="space-y-3 w-full">
            {streamingThinking && <ThinkingIndicator text={streamingThinking} />}
            {streamingCards.length > 0 && (
              <MessageCards cards={streamingCards} />
            )}
            {streamingContent && (
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{streamingContent}</div>
            )}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
