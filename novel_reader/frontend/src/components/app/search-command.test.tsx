import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiFetch } from '@/api/client'
import { SearchCommand } from './search-command'

vi.mock('@/api/client', () => ({ apiFetch: vi.fn() }))
const mockedFetch = vi.mocked(apiFetch)

describe('predictive search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedFetch.mockResolvedValue([] as never)
  })

  it('does not show the empty state before the user types', async () => {
    render(<SearchCommand open onOpenChange={() => undefined} variantId={null} onPick={() => undefined} />)
    await waitFor(() => expect(mockedFetch).toHaveBeenCalled())
    expect(screen.queryByText('Không tìm thấy kết quả.')).toBeNull()
  })

  it('searches on a short prefix and shows the empty state only after a miss', async () => {
    render(<SearchCommand open onOpenChange={() => undefined} variantId={null} onPick={() => undefined} />)
    const input = screen.getByPlaceholderText('Tìm truyện hoặc chương…')
    fireEvent.change(input, { target: { value: 'wi' } })
    await waitFor(() => expect(mockedFetch).toHaveBeenCalledWith('/api/search?q=wi'))
    await waitFor(() => expect(screen.getByText('Không tìm thấy kết quả.')).toBeInTheDocument())
  })
})
