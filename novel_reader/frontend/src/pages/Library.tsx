import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../api/client'
import ChapterList from '../components/ChapterList'
import SearchBox from '../components/SearchBox'
import VariantTabs from '../components/VariantTabs'
import type { Chapter, Novel, Variant } from '../types'

export default function Library() {
  const navigate = useNavigate()
  const [novels, setNovels] = useState<Novel[]>([])
  const [selected, setSelected] = useState<Novel | null>(null)
  const [variants, setVariants] = useState<Variant[]>([])
  const [lang, setLang] = useState('vi') // spec default
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    apiFetch<Novel[]>('/api/novels').then(setNovels).catch((e) => setError(String(e)))
  }, [])

  useEffect(() => {
    if (!selected) return
    // Clear the previous novel's data immediately so no stale chapter can be clicked.
    setVariants([])
    setChapters([])
    setLang('vi')
    setError('')
    apiFetch<Variant[]>(`/api/novels/${selected.id}/variants`).then((items) => {
      setVariants(items)
      if (!items.some((item) => item.lang === lang)) setLang(items[0]?.lang ?? 'vi')
    }).catch((e) => setError(String(e)))
  }, [selected])

  useEffect(() => {
    const variant = variants.find((item) => item.lang === lang)
    if (!variant) return
    apiFetch<Chapter[]>(`/api/variants/${variant.id}/chapters`).then(setChapters).catch((e) => setError(String(e)))
  }, [variants, lang])

  const activeVariant = variants.find((item) => item.lang === lang) ?? null

  return (
    <main className="container stack">
      <header className="row" style={{ justifyContent: 'space-between' }}>
        <h1>Inkwell Novel Reader</h1>
        <button type="button" onClick={async () => {
          await apiFetch('/api/auth/logout', { method: 'POST' })
          window.location.assign('/login')
        }}>Log out</button>
      </header>
      {error && <p className="error">{error}</p>}

      <section className="card stack">
        <h2>Library</h2>
        {novels.length === 0 && <p className="muted">No novels found in drafts/Novel/.</p>}
        {novels.map((novel) => (
          <button key={novel.id} type="button" onClick={() => setSelected(novel)}>
            {novel.title}
          </button>
        ))}
      </section>

      {selected && (
        <section className="card stack">
          <h2>{selected.title}</h2>
          <VariantTabs variants={variants} value={lang} onChange={setLang} />
          <ChapterList chapters={chapters} onSelect={(id) => navigate(`/read/${id}`)} />
        </section>
      )}

      <SearchBox variantId={activeVariant?.id ?? null} onPick={(id) => navigate(`/read/${id}`)} />
    </main>
  )
}
