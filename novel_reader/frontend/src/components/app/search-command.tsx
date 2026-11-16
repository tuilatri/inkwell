import { useEffect, useState, type ReactNode } from 'react'
import { apiFetch } from '@/api/client'
import { CommandDialog, CommandEmpty, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Spinner } from '@/components/ui/spinner'
import type { SearchHit } from '@/types'

function highlight(text: string, query: string): ReactNode {
  const needle = query.trim().toLowerCase()
  if (!needle) return text
  const at = text.toLowerCase().indexOf(needle)
  if (at < 0) return text
  return (
    <>
      {text.slice(0, at)}
      <mark className="rounded bg-accent/20 px-0.5 text-accent">{text.slice(at, at + needle.length)}</mark>
      {text.slice(at + needle.length)}
    </>
  )
}

export function SearchCommand({ open, onOpenChange, variantId, onPick }: {
  open: boolean
  onOpenChange: (open: boolean) => void
  variantId: number | null
  onPick: (chapterId: number) => void
}) {
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<SearchHit[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) {
      setQuery('')
      setHits([])
      setError('')
      return
    }
    let cancelled = false
    setLoading(true)
    const timer = window.setTimeout(async () => {
      try {
        const params = new URLSearchParams()
        if (query.trim()) params.set('q', query.trim())
        if (variantId) params.set('variant_id', String(variantId))
        // Empty query = suggestions; single characters are valid prefix searches.
        const result = await apiFetch<SearchHit[]>(`/api/search?${params}`)
        if (!cancelled) { setHits(result); setError('') }
      } catch {
        if (!cancelled) { setHits([]); setError('Không thể tải kết quả. Thử lại sau.') }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 180)
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [open, query, variantId])

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput value={query} onValueChange={setQuery} placeholder="Tìm truyện hoặc chương…" aria-label="Tìm kiếm" />
      <CommandList>
        {loading && <div className="flex justify-center py-6"><Spinner label="Đang tìm…" /></div>}
        {!loading && !query.trim() && hits.length > 0 && (
          <p className="px-3 py-1.5 text-[11px] uppercase tracking-wider text-muted-foreground">Gợi ý</p>
        )}
        {!loading && hits.map((hit) => (
          <CommandItem
            key={hit.chapter_id}
            value={`${hit.novel_title} ${hit.chapter_title} ${hit.snippet}`}
            onSelect={() => { onPick(hit.chapter_id); onOpenChange(false) }}
            className="gap-2"
          >
            <span className="min-w-0 flex-1 truncate">
              {highlight(hit.novel_title, query)} · {hit.lang.toUpperCase()} · {highlight(hit.chapter_title, query)}
            </span>
            <span className="max-w-[38%] shrink-0 truncate text-xs text-muted-foreground">{hit.snippet.slice(0, 60)}</span>
          </CommandItem>
        ))}
        {!loading && query.trim() && hits.length === 0 && <CommandEmpty>Không tìm thấy kết quả.</CommandEmpty>}
        {!loading && error && <p className="px-3 py-3 text-sm text-destructive">{error}</p>}
      </CommandList>
    </CommandDialog>
  )
}
