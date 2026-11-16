import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '@/api/client'
import { AppHeader } from '@/components/app/app-header'
import { ChapterFilter } from '@/components/app/chapter-filter'
import { EmptyState } from '@/components/app/empty-state'
import { ErrorState } from '@/components/app/error-state'
import { NovelCard } from '@/components/app/novel-card'
import { SearchCommand } from '@/components/app/search-command'
import { VariantsTabs } from '@/components/app/variants-tabs'
import { VirtualChapterList } from '@/components/app/virtual-chapter-list'
import { Skeleton } from '@/components/ui/skeleton'
import { Typography } from '@/components/ui/typography'
import type { Chapter, Novel, Variant } from '@/types'

export default function Library() {
  const navigate = useNavigate()
  const [novels, setNovels] = useState<Novel[]>([])
  const [selected, setSelected] = useState<Novel | null>(null)
  const [variants, setVariants] = useState<Variant[]>([])
  const [lang, setLang] = useState('vi')
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchOpen, setSearchOpen] = useState(false)

  useEffect(() => {
    apiFetch<Novel[]>('/api/novels')
      .then(setNovels)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

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
    if (!selected) return
    setVariants([])
    setChapters([])
    setLang('vi')
    setError('')
    apiFetch<Variant[]>(`/api/novels/${selected.id}/variants`)
      .then((items) => {
        setVariants(items)
        if (!items.some((item) => item.lang === 'vi')) setLang(items[0]?.lang ?? 'vi')
      })
      .catch((e) => setError(String(e)))
  }, [selected])

  useEffect(() => {
    const variant = variants.find((item) => item.lang === lang)
    if (!variant) return
    apiFetch<Chapter[]>(`/api/variants/${variant.id}/chapters`)
      .then(setChapters)
      .catch((e) => setError(String(e)))
  }, [variants, lang])

  const activeVariant = variants.find((item) => item.lang === lang) ?? null

  return (
    <div className="min-h-svh">
      <AppHeader onOpenSearch={() => setSearchOpen(true)} />
      <main className="mx-auto grid max-w-6xl gap-6 p-4 sm:p-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <section className="space-y-4">
          <div>
            <Typography variant="heading" as="h1">Thư viện</Typography>
            <Typography variant="caption">Chọn một bộ truyện để bắt đầu đọc.</Typography>
          </div>
          {error && <ErrorState message={error} />}
          {loading ? (
            <div className="grid gap-3 sm:grid-cols-2">{[1, 2, 3, 4].map((n) => <Skeleton key={n} className="h-40" />)}</div>
          ) : novels.length === 0 ? (
            <EmptyState title="Chưa có truyện" description="Đặt file text vào drafts/Novel/ rồi bấm Rescan trong API." />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {novels.map((novel) => (
                <NovelCard key={novel.id} title={novel.title} active={selected?.id === novel.id} onOpen={() => setSelected(novel)} />
              ))}
            </div>
          )}
        </section>

        <section className="space-y-4">
          {selected ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <Typography variant="heading" as="h2">{selected.title}</Typography>
                <VariantsTabs variants={variants} value={lang} onChange={setLang} />
              </div>
              {chapters.length === 0 ? (
                <Skeleton className="h-64" />
              ) : (
                <>
                  <ChapterFilter value={filter} onChange={setFilter} />
                  <VirtualChapterList chapters={chapters} filter={filter} onSelect={(id) => navigate(`/read/${id}`)} />
                </>
              )}
            </>
          ) : (
            <div className="hidden h-full min-h-64 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground lg:flex">
              Chọn một bộ truyện ở bên trái
            </div>
          )}
        </section>
      </main>
      <SearchCommand
        open={searchOpen}
        onOpenChange={setSearchOpen}
        variantId={activeVariant?.id ?? null}
        onPick={(id) => navigate(`/read/${id}`)}
      />
    </div>
  )
}
