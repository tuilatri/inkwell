import { Link } from 'react-router-dom'

export function AppFooter() {
  return (
    <footer data-testid="app-footer" className="mt-8 border-t border-border px-4 py-5 text-sm text-muted-foreground sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
        <span>© 2026 Inkwell Novel Reader</span>
        <span className="flex items-center gap-3">
          <Link to="/" className="rounded-sm transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Thư viện</Link>
          <span aria-hidden="true">·</span>
          <span>Nội dung từ drafts/Novel · Dùng cá nhân</span>
        </span>
      </div>
    </footer>
  )
}
