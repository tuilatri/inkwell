import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { VirtualChapterList } from '@/components/app/virtual-chapter-list'
import type { Chapter } from '@/types'

export function MobileChapterSheet({ chapters, filter, onFilter, onSelect, open, onOpenChange }: {
  chapters: Chapter[]
  filter: string
  onFilter: (value: string) => void
  onSelect: (id: number) => void
  open?: boolean
  onOpenChange?: (open: boolean) => void
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right">
        <SheetTitle>Danh sách chương</SheetTitle>
        <div className="px-4">
          <input
            aria-label="Lọc chương"
            placeholder='VD: 128'
            value={filter}
            onChange={(e) => onFilter(e.target.value)}
            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          />
        </div>
        <VirtualChapterList chapters={chapters} filter={filter} onSelect={onSelect} className="m-4 h-[calc(100vh-9rem)]" />
      </SheetContent>
    </Sheet>
  )
}
