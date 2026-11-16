import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Button } from './button'
import { Skeleton } from './skeleton'
import { Spinner } from './spinner'
import { Typography } from './typography'

describe('form and display primitives', () => {
  it('Button applies the primary variant token classes', () => {
    render(<Button>Hành động</Button>)
    expect(screen.getByRole('button', { name: 'Hành động' }).className).toContain('bg-accent')
  })

  it('Skeleton renders a pulsing placeholder', () => {
    const { container } = render(<Skeleton className="h-10" />)
    expect(container.firstChild).toHaveClass('animate-pulse')
  })

  it('Spinner exposes its loading label', () => {
    render(<Spinner label="Đang tải…" />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Đang tải…')
  })

  it('Typography chapter variant uses the serif face', () => {
    render(<Typography variant="chapter">Chương 1</Typography>)
    expect(screen.getByText('Chương 1')).toHaveClass('font-serif')
  })
})
