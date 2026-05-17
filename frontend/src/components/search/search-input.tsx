import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, Loader2 } from 'lucide-react'

interface SearchInputProps {
  onSearch: (query: string) => void
  loading?: boolean
  placeholder?: string
}

export function SearchInput({ onSearch, loading, placeholder = '输入问题搜索知识库...' }: SearchInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim()) onSearch(value.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          className="h-10 pl-9 text-[14px] bg-white"
        />
      </div>
      <Button type="submit" size="default" disabled={loading || !value.trim()} className="h-10 px-5">
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
        查询
      </Button>
    </form>
  )
}
