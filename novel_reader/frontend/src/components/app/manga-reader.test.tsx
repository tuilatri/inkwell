import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MangaReader } from './manga-reader'
import type { Page } from '@/types'

const pages: Page[] = [
  { index: 1, url: '/api/media/1/1' },
  { index: 2, url: '/api/media/1/2' },
]

describe('MangaReader', () => {
  it('shows an N/M counter and navigates pages with buttons', () => {
    const onPageChange = vi.fn()
    render(<MangaReader pages={pages} pageIndex={1} onPageChange={onPageChange} />)
    expect(screen.getByText('1 / 2')).toBeInTheDocument()
    expect(screen.getByAltText('Trang 1')).toHaveAttribute('loading', 'lazy')
    fireEvent.click(screen.getByRole('button', { name: 'Trang sau' }))
    expect(onPageChange).toHaveBeenCalledWith(2)
  })

  it('disables previous on first page', () => {
    render(<MangaReader pages={pages} pageIndex={1} onPageChange={() => undefined} />)
    expect(screen.getByRole('button', { name: 'Trang trước' })).toBeDisabled()
  })
})
