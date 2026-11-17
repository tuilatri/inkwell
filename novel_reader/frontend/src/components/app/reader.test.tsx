import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { KeyboardShortcuts } from './keyboard-shortcuts'
import { ReaderView } from './reader-view'
import { filterChapters, VirtualChapterList } from './virtual-chapter-list'
import type { Chapter } from '@/types'

const many: Chapter[] = Array.from({ length: 1700 }, (_, i) => ({ id: i + 1, number: i + 1, title: `Ch.${i + 1}` }))

describe('Reader redesign', () => {
  it('virtualizes a 1.700-chapter list into a bounded DOM', () => {
    render(<VirtualChapterList chapters={many} onSelect={() => undefined} />)
    expect(screen.getByTestId('chapter-list').querySelectorAll('button').length).toBeLessThan(60)
  })

  it('filters by chapter number', () => {
    expect(filterChapters(many, '128').map((chapter) => chapter.number)).toEqual([128])
  })

  it('renders chapter text with reader typography variables', () => {
    render(<ReaderView text="Chương 1 nội dung" fontSize={19} lineHeight={2} />)
    const view = screen.getByTestId('reader-view')
    expect(view.style.getPropertyValue('--reader-size')).toBe('19px')
    expect(screen.getByText('Chương 1 nội dung')).toHaveClass('font-serif')
  })

  it('maps J/K and arrow keys to navigation callbacks', () => {
    const onPrev = vi.fn()
    const onNext = vi.fn()
    render(<KeyboardShortcuts onPrev={onPrev} onNext={onNext} onToggleList={vi.fn()} />)
    fireEvent.keyDown(window, { key: 'j' })
    fireEvent.keyDown(window, { key: 'ArrowLeft' })
    expect(onNext).toHaveBeenCalledTimes(1)
    expect(onPrev).toHaveBeenCalledTimes(1)
  })

  it('uses one horizontal scrollport, truncates names and pins the bookmark', () => {
    const chapters: Chapter[] = [{
      id: 1,
      number: 624,
      title: 'Chương 624 - Ngoại truyện - Đoạn kết quả rất dài không bị cắt',
      visited: true,
    }]
    render(<VirtualChapterList chapters={chapters} onSelect={() => undefined} />)
    const list = screen.getByTestId('chapter-list')
    expect(list).toHaveClass('overflow-auto')
    expect(list.querySelector('.min-w-\\[46rem\\]')).not.toBeNull() // one wide inner surface

    const row = screen.getByTestId('chapter-row-1')
    expect(row).not.toHaveClass('overflow-x-auto')
    expect(screen.getByText(chapters[0].title)).toHaveClass('truncate')
    expect(screen.getByRole('img', { name: 'Đã đọc' })).toHaveClass('sticky', 'fill-accent')
  })
})
