import { useEffect, useMemo, useRef } from 'react'
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

export function VirtualChapterList({ chapters, filter = '', onSelect, activeId, className }: {
  chapters: Chapter[]
  filter?: string
  onSelect: (id: number) => void
  activeId?: number
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

  // Reveal the chapter currently being read when the list mounts (e.g. the
  // mobile Sheet opens) or when the reader navigates to another chapter.
  useEffect(() => {
    if (activeId == null || items.length === 0) return
    const index = items.findIndex((chapter) => chapter.id === activeId)
    if (index < 0) return // filtered out — nothing to locate
    const frame = requestAnimationFrame(() => virtualizer.scrollToIndex(index, { align: 'center' }))
    return () => cancelAnimationFrame(frame)
  }, [activeId, items, virtualizer])

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
          {rows.map(({ chapter, start, size: rowSize }) => {
            const active = chapter.id === activeId
            return (
            <button
              key={chapter.id}
              type="button"
              onClick={() => onSelect(chapter.id)}
              data-testid={`chapter-row-${chapter.id}`}
              aria-current={active ? 'location' : undefined}
              className={cn(
                'absolute left-0 top-0 flex w-full items-center gap-3 border-b border-border/60 px-4 text-left text-sm transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
                active && 'bg-accent/10 font-semibold text-accent',
              )}
              style={{ height: rowSize, transform: `translateY(${start}px)` }}
            >
              <span className="tabular w-12 shrink-0 text-muted-foreground">{chapter.number ?? '—'}</span>
              <span className="min-w-0 flex-1 truncate font-medium">{chapter.title}</span>
              {chapter.kind === 'images' && (
                <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">tranh</span>
              )}
              <Bookmark
                role="img"
                aria-label={chapter.visited ? 'Đã đọc' : 'Chưa đọc'}
                className={cn(
                  'sticky right-0 z-10 ml-auto h-4 w-4 shrink-0 bg-card/95 pl-0.5',
                  chapter.visited ? 'fill-accent text-accent' : 'text-muted-foreground',
                )}
              />
            </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
