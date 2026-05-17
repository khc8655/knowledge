import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  icon?: React.ElementType
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
  className?: string
}

export function EmptyState({ icon: Icon = Inbox, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      <Icon className="h-8 w-8 text-muted-foreground/40 mb-3" />
      <h3 className="text-[14px] font-medium text-foreground">{title}</h3>
      {description && <p className="text-[13px] text-muted-foreground mt-1 max-w-sm">{description}</p>}
      {action && (
        <Button className="mt-3" size="sm" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  )
}
