import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { apiFetch } from '@/api/client'
import { AppFooter } from '@/components/app/app-footer'
import { AppHeader } from '@/components/app/app-header'
import { ChapterFilter } from '@/components/app/chapter-filter'
import { ErrorState } from '@/components/app/error-state'
import { KeyboardShortcuts } from '@/components/app/keyboard-shortcuts'
import { MangaReader } from '@/components/app/manga-reader'
import { MobileChapterSheet } from '@/components/app/mobile-chapter-sheet'
import { ReaderToolbar } from '@/components/app/reader-toolbar'
import { ReaderView } from '@/components/app/reader-view'
import { SearchCommand } from '@/components/app/search-command'
import { VirtualChapterList } from '@/components/app/virtual-chapter-list'
import { Spinner } from '@/components/ui/spinner'
import type { Chapter, Novel, Page, Progress, Variant } from '@/types'

function scrollPercent(top: number): number {
  const max = document.documentElement.scrollHeight - window.innerHeight
  return max > 0 ? Math.min(100, Math.max(0, (top / max) * 100)) : 0
}

async function loadChapters(chapterId: number): Promise<Chapter[]> {
  const novels = await apiFetch<Novel[]>('/api/novels')
  for (const novel of novels) {
    const variants = await apiFetch<Variant[]>(`/api/novels/${novel.id}/variants`)
    for (const variant of variants) {
      const chapters = await apiFetch<Chapter[]>(`/api/variants/${variant.id}/chapters`)
      if (chapters.some((chapter) => chapter.id === chapterId)) return chapters
    }
  }
  return []
}

export default function Reader() {
  const { chapterId } = useParams()
  const navigate = useNavigate()
  const [chapter, setChapter] = useState<Chapter | null>(null)
  const [text, setText] = useState('')
  const [pages, setPages] = useState<Page[]>([])
  const [mangaPage, setMangaPage] = useState(1)
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [error, setError] = useState('')
  const [fontSize, setFontSize] = useState(17)
  const [lineHeight, setLineHeight] = useState(1.9)
  const [filter, setFilter] = useState('')
  const [listOpen, setListOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [progress, setProgress] = useState(0)

  const isManga = chapter?.kind === 'images'
  const pendingRestore = useRef<number | null>(null)
  const restored = useRef(false)
  const suppressSave = useRef(false)
  const timer = useRef<number | undefined>(undefined)
  const toasted = useRef(false)

  function saveProgress(chapter_id: number, scroll_pos: number, page_index: number | null) {
    void apiFetch('/api/progress', {
      method: 'PUT',
      body: JSON.stringify({ chapter_id, scroll_pos, page_index }),
    }).then(() => {
      if (!toasted.current) { toast.success('Vị trí đọc đã được lưu'); toasted.current = true }
    }).catch(() => undefined)
  }

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setSearchOpen(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    if (!chapterId) return
    const id = Number(chapterId)
    restored.current = false
    suppressSave.current = true
    toasted.current = false
    pendingRestore.current = null
    setChapter(null)
    setText('')
    setPages([])
    setMangaPage(1)
    setChapters([])

    apiFetch<Chapter>(`/api/chapters/${id}`).then(setChapter).catch((e) => setError(String(e)))
    apiFetch<Progress>(`/api/progress/${id}`)
      .then((saved) => { pendingRestore.current = saved.scroll_pos; setMangaPage(saved.page_index ?? 1) })
      .catch(() => { pendingRestore.current = 0 })
    loadChapters(id).then(setChapters).catch(() => undefined)
  }, [chapterId])

  // Text content loads only for text chapters; pages only for manga chapters.
  useEffect(() => {
    if (!chapter || isManga || text) return
    const id = chapter.id
    apiFetch<string>(`/api/chapters/${id}/content`)
      .then(setText)
      .catch((e) => { setError(String(e)); suppressSave.current = false })
  }, [chapter, isManga, text])

  useEffect(() => {
    if (isManga && chapter && pages.length === 0) {
      apiFetch<Page[]>(`/api/chapters/${chapter.id}/pages`)
        .then(setPages)
        .catch((e) => { setError(String(e)); suppressSave.current = false })
    }
  }, [isManga, chapter, pages.length])

  useEffect(() => {
    if (!text || isManga || pendingRestore.current === null || restored.current) return
    const target = pendingRestore.current
    restored.current = true
    requestAnimationFrame(() => {
      window.scrollTo({ top: target })
      setProgress(scrollPercent(target))
      window.setTimeout(() => { suppressSave.current = false }, 300)
    })
  }, [text, isManga])

  useEffect(() => {
    if (isManga) return
    function onScroll() {
      if (!restored.current || suppressSave.current || !chapterId) return
      setProgress(scrollPercent(window.scrollY))
      window.clearTimeout(timer.current)
      timer.current = window.setTimeout(() => {
        saveProgress(Number(chapterId), window.scrollY, null)
      }, 1000)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.clearTimeout(timer.current)
    }
  }, [chapterId, isManga])

  function changePage(next: number) {
    setMangaPage(next)
    setProgress(pages.length ? (next / pages.length) * 100 : 0)
    if (chapterId) saveProgress(Number(chapterId), 0, next)
  }

  useEffect(() => {
    if (!isManga) return
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null
      if (target && ['INPUT', 'TEXTAREA'].includes(target.tagName)) return
      if (event.key === 'ArrowRight') { event.preventDefault(); setMangaPage((value) => Math.min(pages.length, value + 1)) }
      if (event.key === 'ArrowLeft') { event.preventDefault(); setMangaPage((value) => Math.max(1, value - 1)) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isManga, pages.length])

  const index = chapters.findIndex((item) => item.id === Number(chapterId))
  const prev = index > 0 ? chapters[index - 1] : undefined
  const next = index >= 0 && index < chapters.length - 1 ? chapters[index + 1] : undefined

  return (
    <div className="flex min-h-svh flex-col">
      <AppHeader onOpenSearch={() => setSearchOpen(true)} />
      <ReaderToolbar
        chapter={chapter}
        progress={progress}
        onPrev={prev ? () => navigate(`/read/${prev.id}`) : undefined}
        onNext={next ? () => navigate(`/read/${next.id}`) : undefined}
        fontSize={fontSize}
        lineHeight={lineHeight}
        onFontSize={setFontSize}
        onLineHeight={setLineHeight}
        onBack={() => navigate(-1)}
        onToggleList={() => setListOpen((value) => !value)}
        onSearch={() => setSearchOpen(true)}
      />
      {error && <div className="mx-auto max-w-6xl px-4 pt-4"><ErrorState message={error} /></div>}
      <div className="mx-auto grid max-w-6xl gap-6 p-4 sm:p-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-w-0 space-y-4">
          {!chapter ? <Spinner />
            : isManga ? <MangaReader pages={pages} pageIndex={mangaPage} onPageChange={changePage} />
            : !text ? <Spinner />
            : <ReaderView text={text} fontSize={fontSize} lineHeight={lineHeight} />}
          <div className="flex items-center justify-between gap-3">
            <button type="button" disabled={!prev} className="rounded-md border border-border px-3 py-2 text-sm disabled:opacity-40" onClick={() => prev && navigate(`/read/${prev.id}`)}>← Chương trước</button>
            <button type="button" disabled={!next} className="rounded-md border border-border px-3 py-2 text-sm disabled:opacity-40" onClick={() => next && navigate(`/read/${next.id}`)}>Chương sau →</button>
          </div>
        </div>
        <aside className="hidden space-y-3 lg:block">
          <ChapterFilter value={filter} onChange={setFilter} />
          <VirtualChapterList chapters={chapters} filter={filter} activeId={chapter?.id ?? (chapterId ? Number(chapterId) : undefined)} onSelect={(id) => navigate(`/read/${id}`)} className="h-[calc(100vh-9rem)]" />
        </aside>
      </div>
      <MobileChapterSheet chapters={chapters} filter={filter} onFilter={setFilter} activeId={chapter?.id ?? (chapterId ? Number(chapterId) : undefined)} onSelect={(id) => { setListOpen(false); navigate(`/read/${id}`) }} open={listOpen} onOpenChange={setListOpen} />
      <KeyboardShortcuts
        onPrev={() => prev && navigate(`/read/${prev.id}`)}
        onNext={() => next && navigate(`/read/${next.id}`)}
        onToggleList={() => setListOpen((value) => !value)}
      />
      <SearchCommand
        open={searchOpen}
        onOpenChange={setSearchOpen}
        variantId={null}
        onPick={(id) => navigate(`/read/${id}`)}
      />
      <AppFooter />
    </div>
  )
}
