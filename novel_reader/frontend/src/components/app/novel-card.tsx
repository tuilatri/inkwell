import { BookText, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function NovelCard({ title, kind = 'novel', chapterCount, active, onOpen }: { title: string; kind?: 'novel' | 'manga'; chapterCount?: number; active?: boolean; onOpen: () => void }) {
  return (
    <Card className={cn('card-hover rise-in', active ? 'border-accent/60' : undefined)}>
      <CardHeader className="flex-row items-center justify-between gap-3 space-y-0">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted text-accent">
            <BookText className="h-4 w-4" aria-hidden="true" />
          </span>
          <CardTitle className="truncate text-base">{title}</CardTitle>
        </div>
        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-sm text-muted-foreground">
          Bộ truyện
          <Badge variant="secondary" className={cn('text-[10px] font-medium', kind === 'manga' && 'border-accent/40 bg-accent/10 text-accent')}>
            {kind === 'manga' ? 'Manhwa' : 'Novel'}
          </Badge>
        </span>
        {chapterCount !== undefined && <Badge variant="secondary" className="tabular">{chapterCount} chương</Badge>}
      </CardContent>
      <CardContent className="pt-0">
        <Button variant="outline" size="sm" className="w-full" onClick={onOpen}>Mở truyện</Button>
      </CardContent>
    </Card>
  )
}
