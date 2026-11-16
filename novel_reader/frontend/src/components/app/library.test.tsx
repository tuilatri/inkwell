import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TooltipProvider } from '@/components/ui/tooltip'
import Library from '@/pages/Library'
import { apiFetch } from '@/api/client'

vi.mock('@/api/client', () => ({ apiFetch: vi.fn() }))

const mockedFetch = vi.mocked(apiFetch)

describe('Library redesign', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedFetch.mockImplementation(async (path: string) => {
      if (path === '/api/novels') {
        return [
          { id: 1, title: 'My_Sexy_College_Friends' },
          { id: 2, title: 'Real_Man' },
          { id: 3, title: 'Solo_Farming_In_The_Tower' },
          { id: 4, title: 'Wireless_Onahole' },
        ] as never
      }
      if (path === '/api/novels/1/variants') {
        return [{ id: 11, lang: 'vi' }, { id: 12, lang: 'en' }] as never
      }
      if (path === '/api/variants/11/chapters') {
        return [{ id: 101, number: 1, title: 'Ch.1' }] as never
      }
      return [] as never
    })
  })

  it('shows skeletons first, then novel names only (no covers)', async () => {
    render(<TooltipProvider><MemoryRouter><Library /></MemoryRouter></TooltipProvider>)
    expect(document.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
    await waitFor(() => expect(screen.getByText('Real_Man')).toBeInTheDocument())
    expect(screen.getByText('Wireless_Onahole')).toBeInTheDocument()
    expect(document.querySelector('img')).toBeNull()
  })

  it('defaults to VI and clears the previous novel state on switch', async () => {
    render(<TooltipProvider><MemoryRouter><Library /></MemoryRouter></TooltipProvider>)
    fireEvent.click((await screen.findAllByRole('button', { name: 'Mở truyện' }))[0])
    await waitFor(() => expect(screen.getByRole('tab', { name: 'VI' })).toHaveAttribute('data-state', 'active'))
    // The filter input only renders once chapters for the selected variant arrive.
    await waitFor(() => expect(screen.getByPlaceholderText('Lọc chương,VD: 128')).toBeInTheDocument())
  })
})
