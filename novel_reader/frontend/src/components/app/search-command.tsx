import { useEffect, useState } from 'react'
import { apiFetch } from '@/api/client'
import { CommandDialog, CommandEmpty, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import type { SearchHit } from '@/types'

export function SearchCommand({ open, onOpenChange, variantId, onPick }: {
  open: boolean
  onOpenChange: (open: boolean) => void
  variantId: number | null
  onPick: (chapterId: number) => void
}) {
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<SearchHit[]>([])

  useEffect(() => {
    if (query.trim().length < 2) { setHits([]); return }
    let cancelled = false
    const timer = window.setTimeout(async () => {
      try {
        const params = new URLSearchParams({ q: query.trim() })
        if (variantId) params.set('variant_id', String(variantId))
        const result = await apiFetch<SearchHit[]>(`/api/search?${params}`)
        if (!cancelled) setHits(result)
      } catch {
        if (!cancelled) setHits([])
      }
    }, 250)
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [query, variantId])

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput value={query} onValueChange={setQuery} placeholder="Tìm truyện hoặc chương…" aria-label="Tìm kiếm" />
      <CommandList>
        <CommandEmpty>Không tìm thấy kết quả.</CommandEmpty>
        {hits.map((hit) => (
          <CommandItem key={hit.chapter_id} value={`${hit.novel_title} ${hit.chapter_title} ${hit.snippet}`} onSelect={() => { onPick(hit.chapter_id); onOpenChange(false) }}>
            <span className="truncate">{hit.novel_title} · {hit.lang.toUpperCase()} · {hit.chapter_title}</span>
          </CommandItem>
        ))}
      </CommandList>
    </CommandDialog>
  )
}
