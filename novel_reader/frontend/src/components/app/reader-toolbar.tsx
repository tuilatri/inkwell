import { ArrowLeft, List, Minus, Plus, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { Chapter } from '@/types'

export function ReaderToolbar({ chapter, fontSize, lineHeight, onFontSize, onLineHeight, onBack, onToggleList, onSearch }: {
  chapter: Chapter | null
  fontSize: number
  lineHeight: number
  onFontSize: (value: number) => void
  onLineHeight: (value: number) => void
  onBack: () => void
  onToggleList: () => void
  onSearch: () => void
}) {
  return (
    <div className="sticky top-16 z-20 flex flex-wrap items-center gap-3 border-b border-border bg-background/95 px-4 py-3 backdrop-blur-sm sm:px-6">
      <Button variant="ghost" size="icon" onClick={onBack} aria-label="Quay lại">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
      </Button>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{chapter ? `${chapter.number ?? ''} ${chapter.title}` : 'Đang tải…'}</p>
      </div>
      <div className="hidden items-center gap-3 sm:flex">
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex w-28 items-center gap-2">
              <Minus className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
              <Slider aria-label="Cỡ chữ" min={14} max={24} step={1} value={[fontSize]} onValueChange={([v]) => onFontSize(v)} />
              <Plus className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
            </div>
          </TooltipTrigger>
          <TooltipContent>Cỡ chữ {fontSize}px</TooltipContent>
        </Tooltip>
        <div className="flex w-24 items-center gap-2" title={`Giãn dòng ${lineHeight}`}>
          <span className="text-xs text-muted-foreground">↕</span>
          <Slider aria-label="Giãn dòng" min={1.5} max={2.4} step={0.1} value={[lineHeight]} onValueChange={([v]) => onLineHeight(v)} />
        </div>
      </div>
      <Button variant="ghost" size="icon" onClick={onSearch} aria-label="Mở tìm kiếm">
        <Search className="h-4 w-4" aria-hidden="true" />
      </Button>
      <Button variant="outline" size="sm" onClick={onToggleList} aria-label="Danh sách chương">
        <List className="h-4 w-4 sm:mr-2" aria-hidden="true" />
        <span className="hidden sm:inline">Chương</span>
      </Button>
    </div>
  )
}
