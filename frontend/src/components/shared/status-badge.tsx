import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  status: 'healthy' | 'processing' | 'warning' | 'failed' | 'stale'
  label?: string
  className?: string
}

const statusStyles: Record<string, { dot: string; text: string }> = {
  healthy: { dot: 'bg-success', text: 'text-success' },
  processing: { dot: 'bg-foreground animate-pulse', text: 'text-foreground' },
  warning: { dot: 'bg-warning', text: 'text-warning' },
  failed: { dot: 'bg-destructive', text: 'text-destructive' },
  stale: { dot: 'bg-muted-foreground', text: 'text-muted-foreground' },
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const style = statusStyles[status] || statusStyles.stale
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-[12px]', className)}>
      <span className={cn('h-1.5 w-1.5 rounded-full', style.dot)} />
      {label && <span className={style.text}>{label}</span>}
    </span>
  )
}
