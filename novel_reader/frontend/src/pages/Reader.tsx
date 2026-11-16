import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiFetch } from '../api/client'
import type { Chapter, Progress } from '../types'

export default function Reader() {
  const { chapterId } = useParams()
  const navigate = useNavigate()
  const [chapter, setChapter] = useState<Chapter | null>(null)
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const timer = useRef<number | undefined>(undefined)
  const pendingRestore = useRef<number | null>(null)
  const restored = useRef(false)
  const suppressSave = useRef(false)

  useEffect(() => {
    if (!chapterId) return
    const id = Number(chapterId)
    restored.current = false
    suppressSave.current = true
    pendingRestore.current = null
    setChapter(null)
    setText('')
    apiFetch<Chapter>(`/api/chapters/${id}`).then(setChapter).catch((e) => setError(String(e)))
    apiFetch<Progress>(`/api/progress/${id}`)
      .then((progress) => { pendingRestore.current = progress.scroll_pos })
      .catch(() => { pendingRestore.current = 0 })
    apiFetch<string>(`/api/chapters/${id}/content`)
      .then(setText)
      .catch((e) => { setError(String(e)); suppressSave.current = false })
  }, [chapterId])

  // Restore only after the chapter text is in the DOM; otherwise the browser
  // clamps scrollTo to the short pre-render page and saves 0 over real progress.
  useEffect(() => {
    if (!text || pendingRestore.current === null || restored.current) return
    const target = pendingRestore.current
    restored.current = true
    requestAnimationFrame(() => {
      window.scrollTo({ top: target })
      window.setTimeout(() => { suppressSave.current = false }, 300)
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
        }).catch(() => undefined)
      }, 1000)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.clearTimeout(timer.current)
    }
  }, [chapterId])

  return (
    <main className="container">
      <header className="row" style={{ justifyContent: 'space-between' }}>
        <button type="button" onClick={() => navigate(-1)}>← Back</button>
        <h2>{chapter ? `${chapter.number ?? ''} ${chapter.title}` : 'Loading…'}</h2>
      </header>
      {error && <p className="error">{error}</p>}
      <article className="card reader-text">{text}</article>
    </main>
  )
}
