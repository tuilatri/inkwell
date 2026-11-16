import { useEffect, useState } from 'react'
import { apiFetch } from '../api/client'
import type { SearchHit } from '../types'

interface Props {
  variantId: number | null
  onPick: (chapterId: number) => void
}

export default function SearchBox({ variantId, onPick }: Props) {
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<SearchHit[]>([])

  useEffect(() => {
    if (query.trim().length < 2) {
      setHits([])
      return
    }
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
    }, 300)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [query, variantId])

  return (
    <section className="card stack">
      <input
        aria-label="Search"
        placeholder="Search chapters ( accents optional )"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {hits.map((hit) => (
        <button key={hit.chapter_id} type="button" onClick={() => onPick(hit.chapter_id)}>
          {hit.novel_title} · {hit.lang.toUpperCase()} · {hit.chapter_title}
          <span className="muted"> — {hit.snippet.slice(0, 80)}</span>
        </button>
      ))}
    </section>
  )
}
