import { BookOpen, LogOut, Search } from 'lucide-react'
import { toast } from 'sonner'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Kbd } from '@/components/ui/kbd'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function AppHeader({ onOpenSearch, minimal = false }: { onOpenSearch?: () => void; minimal?: boolean }) {
  async function logout() {
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' })
      window.location.assign('/login')
    } catch {
      toast.error('Không thể đăng xuất')
    }
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border bg-background/90 px-4 backdrop-blur-sm sm:px-6">
      <Link to="/" className="flex items-center gap-2.5 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <BookOpen className="h-5 w-5" aria-hidden="true" />
        </span>
        <span className="font-semibold tracking-[-0.02em]">Inkwell Novel Reader</span>
      </Link>
      {!minimal && (
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onOpenSearch} aria-label="Mở tìm kiếm">
            <Search className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Tìm chương</span>
            <Kbd className="hidden sm:inline-flex">⌘K</Kbd>
          </Button>
          <Tooltip>
            <TooltipTrigger asChild>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="Tài khoản">···</Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onSelect={logout} className="text-destructive">
                    <LogOut className="mr-2 h-4 w-4" aria-hidden="true" /> Đăng xuất
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TooltipTrigger>
            <TooltipContent>Tài khoản</TooltipContent>
          </Tooltip>
        </div>
      )}
    </header>
  )
}
