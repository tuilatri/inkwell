import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, Maximize2, Minimize2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import type { Page } from '@/types'

export function MangaReader({
  pages,
  pageIndex,
  onPageChange,
}: {
  pages: Page[]
  pageIndex: number
  onPageChange: (page: number) => void
}) {
  const [zoomed, setZoomed] = useState(false)
  const viewport = useRef<HTMLDivElement>(null)
  const current = Math.max(1, Math.min(pageIndex, pages.length))
  const page = pages[current - 1]

  useEffect(() => {
    viewport.current?.scrollTo?.({ top: 0 })
  }, [current])

  if (pages.length === 0) return <Spinner label="Đang tải trang…" />

  return (
    <div className="rise-in space-y-3">
      <div className="flex items-center justify-center gap-3 text-sm">
        <Button variant="ghost" size="icon" aria-label="Trang trước" disabled={current <= 1} onClick={() => onPageChange(current - 1)}>
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </Button>
        <span className="tabular" aria-live="polite">{current} / {pages.length}</span>
        <Button variant="ghost" size="icon" aria-label="Trang sau" disabled={current >= pages.length} onClick={() => onPageChange(current + 1)}>
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Button>
        <Button variant="ghost" size="icon" aria-label={zoomed ? 'Vừa màn hình' : 'Phóng to'} onClick={() => setZoomed((value) => !value)}>
          {zoomed ? <Minimize2 className="h-4 w-4" aria-hidden="true" /> : <Maximize2 className="h-4 w-4" aria-hidden="true" />}
        </Button>
      </div>
      <div ref={viewport} className="flex justify-center overflow-auto rounded-lg border border-border bg-card/40 p-2">
        <img
          src={page.url}
          alt={`Trang ${current}`}
          loading="lazy"
          className={cn('h-auto rounded-md', zoomed ? 'max-w-none' : 'max-w-full')}
          onLoad={(event) => {
            const next = pages[current]
            if (next) {
              const preload = new Image()
              preload.src = next.url
            }
            event.currentTarget.decoding = 'async'
          }}
        />
      </div>
    </div>
  )
}
