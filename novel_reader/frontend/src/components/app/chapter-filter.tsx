import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'

export function ChapterFilter({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <div className="relative">
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
      <Input
        aria-label="Lọc chương"
        placeholder='Lọc chương,VD: 128'
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-9"
      />
    </div>
  )
}
