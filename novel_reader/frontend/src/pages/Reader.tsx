import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { apiFetch } from '@/api/client'
import { AppFooter } from '@/components/app/app-footer'
import { AppHeader } from '@/components/app/app-header'
import { ChapterFilter } from '@/components/app/chapter-filter'
import { ErrorState } from '@/components/app/error-state'
import { KeyboardShortcuts } from '@/components/app/keyboard-shortcuts'
import { MobileChapterSheet } from '@/components/app/mobile-chapter-sheet'
import { ReaderToolbar } from '@/components/app/reader-toolbar'
import { ReaderView } from '@/components/app/reader-view'
import { SearchCommand } from '@/components/app/search-command'
import { ReadingProgress } from '@/components/app/reading-progress'
import { VirtualChapterList } from '@/components/app/virtual-chapter-list'
import { Spinner } from '@/components/ui/spinner'
import type { Chapter, Novel, Progress, Variant } from '@/types'

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
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [error, setError] = useState('')
  const [fontSize, setFontSize] = useState(17)
  const [lineHeight, setLineHeight] = useState(1.9)
  const [filter, setFilter] = useState('')
  const [listOpen, setListOpen] = useState(false)
  const [ready, setReady] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)

  const pendingRestore = useRef<number | null>(null)
  const restored = useRef(false)
  const suppressSave = useRef(false)
  const timer = useRef<number | undefined>(undefined)
  const toasted = useRef(false)

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
    setReady(false)
    pendingRestore.current = null
    setChapter(null)
    setText('')
    setChapters([])

    apiFetch<Chapter>(`/api/chapters/${id}`).then(setChapter).catch((e) => setError(String(e)))
    apiFetch<Progress>(`/api/progress/${id}`)
      .then((progress) => { pendingRestore.current = progress.scroll_pos })
      .catch(() => { pendingRestore.current = 0 })
    apiFetch<string>(`/api/chapters/${id}/content`)
      .then(setText)
      .catch((e) => { setError(String(e)); suppressSave.current = false })
    loadChapters(id).then(setChapters).catch(() => undefined)
  }, [chapterId])

  // Restore only after text is rendered; otherwise the browser clamps scrollTo
  // on the short pre-render page and the debounce saves 0 over real progress.
  useEffect(() => {
    if (!text || pendingRestore.current === null || restored.current) return
    const target = pendingRestore.current
    restored.current = true
    requestAnimationFrame(() => {
      window.scrollTo({ top: target })
      window.setTimeout(() => { suppressSave.current = false }, 300)
      setReady(true)
    })
  }, [text])

  useEffect(() => {
    function onScroll() {
      if (!restored.current || suppressSave.current || !chapterId) return
      window.clearTimeout(timer.current)
      timer.current = window.setTimeout(() => {
        void apiFetch('/api/progress', {
          method: 'PUT',
          body: JSON.stringify({ chapter_id: Number(chapterId), scroll_pos: window.scrollY }),
        }).then(() => {
          if (!toasted.current) { toast.success('Vị trí đọc đã được lưu'); toasted.current = true }
        }).catch(() => undefined)
      }, 1000)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.clearTimeout(timer.current)
    }
  }, [chapterId])

  const index = chapters.findIndex((item) => item.id === Number(chapterId))
  const prev = index > 0 ? chapters[index - 1] : undefined
  const next = index >= 0 && index < chapters.length - 1 ? chapters[index + 1] : undefined

  return (
    <div className="flex min-h-svh flex-col">
      <AppHeader onOpenSearch={() => setSearchOpen(true)} />
      <ReaderToolbar
        chapter={chapter}
        fontSize={fontSize}
        lineHeight={lineHeight}
        onFontSize={setFontSize}
        onLineHeight={setLineHeight}
        onBack={() => navigate(-1)}
        onToggleList={() => setListOpen((value) => !value)}
        onSearch={() => setSearchOpen(true)}
      />
      <ReadingProgress enabled={ready} />
      {error && <div className="mx-auto max-w-6xl px-4 pt-4"><ErrorState message={error} /></div>}
      <div className="mx-auto grid max-w-6xl gap-6 p-4 sm:p-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-4">
          {!text ? <Spinner /> : <ReaderView text={text} fontSize={fontSize} lineHeight={lineHeight} />}
          <div className="flex items-center justify-between gap-3">
            <button type="button" disabled={!prev} className="rounded-md border border-border px-3 py-2 text-sm disabled:opacity-40" onClick={() => prev && navigate(`/read/${prev.id}`)}>← Chương trước</button>
            <button type="button" disabled={!next} className="rounded-md border border-border px-3 py-2 text-sm disabled:opacity-40" onClick={() => next && navigate(`/read/${next.id}`)}>Chương sau →</button>
          </div>
        </div>
        <aside className="hidden space-y-3 lg:block">
          <ChapterFilter value={filter} onChange={setFilter} />
          <VirtualChapterList chapters={chapters} filter={filter} onSelect={(id) => navigate(`/read/${id}`)} className="h-[calc(100vh-9rem)]" />
        </aside>
      </div>
      <MobileChapterSheet chapters={chapters} filter={filter} onFilter={setFilter} onSelect={(id) => { setListOpen(false); navigate(`/read/${id}`) }} open={listOpen} onOpenChange={setListOpen} />
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
