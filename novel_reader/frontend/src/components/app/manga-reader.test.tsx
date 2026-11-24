import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MangaReader } from './manga-reader'
import type { Page } from '@/types'

const pages: Page[] = [
  { index: 1, url: '/api/media/1/1' },
  { index: 2, url: '/api/media/1/2' },
]

let notify: ((entries: Array<{ isIntersecting: boolean; intersectionRatio: number; target: HTMLElement }>) => void) | null = null

class ObserverMock {
  constructor(callback: (entries: Array<{ isIntersecting: boolean; intersectionRatio: number; target: HTMLElement }>) => void) {
    notify = callback
  }
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return [] }
}

describe('MangaReader', () => {
  beforeEach(() => vi.stubGlobal('IntersectionObserver', ObserverMock))
  afterEach(() => vi.unstubAllGlobals())

  it('renders every page of the chapter in one lazy-loaded vertical list', () => {
    render(<MangaReader pages={pages} pageIndex={1} onPageChange={() => undefined} />)
    expect(screen.getByText('1 / 2')).toBeInTheDocument()
    expect(screen.getAllByRole('img')).toHaveLength(2)
    for (const image of screen.getAllByRole('img')) {
      expect(image).toHaveAttribute('loading', 'lazy')
      expect(image).toHaveAttribute('width', '800') // reserve layout before load
    }
    expect(screen.queryByRole('button', { name: 'Trang sau' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Trang trước' })).not.toBeInTheDocument()
  })

  it('reports the most-visible image as the current page', async () => {
    const onPageChange = vi.fn()
    render(<MangaReader pages={pages} pageIndex={1} onPageChange={onPageChange} />)
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 30)) }) // flush restore rAF -> ready
    expect(notify).not.toBeNull()
    act(() => {
      notify!([
        { isIntersecting: true, intersectionRatio: 0.2, target: screen.getByAltText('Trang 1') },
        { isIntersecting: true, intersectionRatio: 0.9, target: screen.getByAltText('Trang 2') },
      ])
    })
    await waitFor(() => expect(onPageChange).toHaveBeenCalledWith(2))
  })

  it('keeps zoom and arrow-key navigation without page buttons', async () => {
    const scroll = vi.spyOn(HTMLElement.prototype, 'scrollIntoView').mockImplementation(() => undefined)
    render(<MangaReader pages={pages} pageIndex={1} onPageChange={() => undefined} />)
    fireEvent.click(screen.getByRole('button', { name: 'Phóng to' }))
    expect(screen.getAllByRole('img')[0]).toHaveClass('max-w-none')
    fireEvent.keyDown(window, { key: 'ArrowRight' })
    await waitFor(() => expect(scroll).toHaveBeenCalled())
    scroll.mockRestore()
  })
})
