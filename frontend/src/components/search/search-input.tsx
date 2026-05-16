import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, Loader2 } from 'lucide-react'

interface SearchInputProps {
  onSearch: (query: string) => void
  loading?: boolean
  placeholder?: string
}

export function SearchInput({ onSearch, loading, placeholder = '输入问题，例如：AE800 的价格是多少' }: SearchInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim()) onSearch(value.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="h-12 text-base flex-1"
      />
      <Button type="submit" size="lg" disabled={loading || !value.trim()}>
        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5" />}
        查询
      </Button>
    </form>
  )
}
