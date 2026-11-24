import { useEffect, useRef, useState } from 'react'
import { Maximize2, Minimize2 } from 'lucide-react'
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
  const imageRefs = useRef<Array<HTMLImageElement | null>>([])
  const ready = useRef(false)
  const restored = useRef(false)
  const current = Math.max(1, Math.min(pageIndex, pages.length))

  // Keep observer callbacks current without re-subscribing on every render.
  const latest = useRef({ current, onPageChange })
  latest.current = { current, onPageChange }

  function scrollToPage(page: number) {
    imageRefs.current[page - 1]?.scrollIntoView?.({ block: 'center', behavior: 'smooth' })
  }

  // The most-visible image becomes the current page (and is saved as progress).
  useEffect(() => {
    if (pages.length === 0) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (!ready.current) return // don't overwrite the saved page during restore
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        if (visible) {
          const index = Number((visible.target as HTMLElement).dataset.page)
          if (index && index !== latest.current.current) latest.current.onPageChange(index)
        }
      },
      { rootMargin: '-30% 0px -30% 0px', threshold: [0, 0.25, 0.5, 1] },
    )
    imageRefs.current.forEach((image) => image && observer.observe(image))
    return () => observer.disconnect()
  }, [pages])

  // Restore the saved page once the images have laid out (width/height reserve space).
  useEffect(() => {
    if (restored.current || pages.length === 0) return
    restored.current = true
    const frame = requestAnimationFrame(() => {
      scrollToPage(current)
      ready.current = true
    })
    return () => cancelAnimationFrame(frame)
    // Restore once per chapter — `pages` identity changes when the chapter changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pages])

  // Arrow keys jump one image into view; the observer records the new page.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null
      if (target && ['INPUT', 'TEXTAREA'].includes(target.tagName)) return
      if (event.key === 'ArrowRight') { event.preventDefault(); scrollToPage(Math.min(current + 1, pages.length)) }
      if (event.key === 'ArrowLeft') { event.preventDefault(); scrollToPage(Math.max(1, current - 1)) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pages.length, current])

  if (pages.length === 0) return <Spinner label="Đang tải trang…" />

  return (
    <div className="rise-in space-y-3">
      <div className="flex items-center justify-center gap-3 text-sm">
        <span className="tabular" aria-live="polite">{current} / {pages.length}</span>
        <Button variant="ghost" size="icon" aria-label={zoomed ? 'Vừa màn hình' : 'Phóng to'} onClick={() => setZoomed((value) => !value)}>
          {zoomed ? <Minimize2 className="h-4 w-4" aria-hidden="true" /> : <Maximize2 className="h-4 w-4" aria-hidden="true" />}
        </Button>
      </div>
      <div className="space-y-2 rounded-lg border border-border bg-card/40 p-2">
        {pages.map((page, index) => (
          <img
            key={page.index}
            ref={(element) => { imageRefs.current[index] = element }}
            data-page={index + 1}
            src={page.url}
            alt={`Trang ${index + 1}`}
            width={800}
            height={1200}
            loading="lazy"
            className={cn('mx-auto h-auto rounded-md', zoomed ? 'max-w-none' : 'max-w-full')}
          />
        ))}
      </div>
    </div>
  )
}
