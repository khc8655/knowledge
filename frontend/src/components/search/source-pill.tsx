import { Badge } from '@/components/ui/badge'
import { FileSpreadsheet, FileText, FileImage, File, FileCheck } from 'lucide-react'

const sourceConfig: Record<string, { label: string; variant: string; icon: React.ElementType }> = {
  excel: { label: 'Excel', variant: 'success', icon: FileSpreadsheet },
  word: { label: 'Word', variant: 'default', icon: FileText },
  markdown: { label: 'Markdown', variant: 'secondary', icon: FileText },
  txt: { label: 'TXT', variant: 'secondary', icon: File },
  ppt: { label: 'PPT', variant: 'warning', icon: FileImage },
  report: { label: '检测报告', variant: 'processing', icon: FileCheck },
}

interface SourcePillProps {
  sourceType: string
  fileName?: string
  path?: string
  className?: string
}

export function SourcePill({ sourceType, fileName, path, className }: SourcePillProps) {
  const config = sourceConfig[sourceType] || { label: sourceType, variant: 'secondary', icon: File }
  const Icon = config.icon

  return (
    <Badge variant={config.variant as 'default' | 'secondary' | 'success' | 'warning' | 'processing'} className={className}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
      {fileName && <span className="ml-1 opacity-70">· {fileName}</span>}
      {path && <span className="ml-1 opacity-70">· {path}</span>}
    </Badge>
  )
}
