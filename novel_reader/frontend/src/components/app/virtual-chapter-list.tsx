import { useMemo, useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { cn } from '@/lib/utils'
import type { Chapter } from '@/types'

export function filterChapters(chapters: Chapter[], filter: string): Chapter[] {
  const needle = filter.trim().toLowerCase()
  if (!needle) return chapters
  // A numeric query means an exact chapter number — "128" should not match 1128.
  if (/^\d+$/.test(needle)) return chapters.filter((c) => String(c.number ?? '') === needle)
  return chapters.filter((c) =>
    String(c.number ?? '').includes(needle) || c.title.toLowerCase().includes(needle),
  )
}

export function VirtualChapterList({ chapters, filter = '', onSelect, className }: {
  chapters: Chapter[]
  filter?: string
  onSelect: (id: number) => void
  className?: string
}) {
  const parentRef = useRef<HTMLDivElement>(null)
  const items = useMemo(() => filterChapters(chapters, filter), [chapters, filter])

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 46,
    overscan: 8,
  })

  return (
    <div ref={parentRef} data-testid="chapter-list" className={cn('h-[60vh] overflow-auto rounded-lg border border-border bg-card/40', className)}>
      {items.length === 0 ? (
        <p className="p-6 text-center text-sm text-muted-foreground">Không có chương phù hợp.</p>
      ) : (
        <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
          {virtualizer.getVirtualItems().map((row) => {
            const chapter = items[row.index]
            return (
              <button
                key={chapter.id}
                type="button"
                onClick={() => onSelect(chapter.id)}
                className="absolute left-0 top-0 flex w-full items-center gap-3 border-b border-border/60 px-4 text-left text-sm transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                style={{ height: row.size, transform: `translateY(${row.start}px)` }}
              >
                <span className="tabular w-14 shrink-0 text-muted-foreground">{chapter.number ?? '—'}</span>
                <span className="truncate">{chapter.title}</span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
