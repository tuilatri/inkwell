import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { apiFetch } from '@/api/client'
import { LoginForm } from './login-form'

vi.mock('@/api/client', () => ({ apiFetch: vi.fn() }))
vi.mocked(apiFetch).mockResolvedValue({} as never)

describe('LoginForm password toggle', () => {
  it('shows and hides the password with an accessible control', () => {
    render(<LoginForm />)
    const input = screen.getByLabelText('Mật khẩu')
    expect(input).toHaveAttribute('type', 'password')

    fireEvent.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }))
    expect(input).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: 'Ẩn mật khẩu' })).toHaveAttribute('aria-pressed', 'true')

    fireEvent.click(screen.getByRole('button', { name: 'Ẩn mật khẩu' }))
    expect(input).toHaveAttribute('type', 'password')
  })
})
