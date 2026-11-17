import { useMemo, useRef } from 'react'
import { Bookmark } from 'lucide-react'
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
    estimateSize: () => 52,
    overscan: 8,
  })

  const measured = virtualizer.getVirtualItems()
  // Zero-height containers (e.g. jsdom or a hidden panel) report no virtual
  // items; render a bounded first page so rows are never blank.
  const rows = measured.length
    ? measured.map((row) => ({ chapter: items[row.index], start: row.start, size: row.size }))
    : items.slice(0, 12).map((chapter, index) => ({ chapter, start: index * 52, size: 52 }))

  return (
    <div
      ref={parentRef}
      data-testid="chapter-list"
      className={cn('h-[60vh] overflow-auto rounded-lg border border-border bg-card/40', className)}
    >
      {items.length === 0 ? (
        <p className="p-6 text-center text-sm text-muted-foreground">Không có chương phù hợp.</p>
      ) : (
        // One wide inner surface = ONE horizontal scrollbar for the whole list.
        <div
          className="relative w-full min-w-[46rem]"
          style={{ height: Math.max(virtualizer.getTotalSize(), rows.length * 52) }}
        >
          {rows.map(({ chapter, start, size: rowSize }) => (
            <button
              key={chapter.id}
              type="button"
              onClick={() => onSelect(chapter.id)}
              data-testid={`chapter-row-${chapter.id}`}
              className="absolute left-0 top-0 flex w-full items-center gap-3 border-b border-border/60 px-4 text-left text-sm transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
              style={{ height: rowSize, transform: `translateY(${start}px)` }}
            >
              <span className="tabular w-12 shrink-0 text-muted-foreground">{chapter.number ?? '—'}</span>
              <span className="min-w-0 flex-1 truncate font-medium">{chapter.title}</span>
              <Bookmark
                role="img"
                aria-label={chapter.visited ? 'Đã đọc' : 'Chưa đọc'}
                className={cn(
                  'sticky right-0 z-10 ml-auto h-4 w-4 shrink-0 bg-card/95 pl-0.5',
                  chapter.visited ? 'fill-accent text-accent' : 'text-muted-foreground',
                )}
              />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
