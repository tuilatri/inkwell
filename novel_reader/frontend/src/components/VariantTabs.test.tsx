import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Variant } from '../types'
import VariantTabs from './VariantTabs'

const variants: Variant[] = [
  { id: 1, lang: 'en' },
  { id: 2, lang: 'vi' },
]

describe('VariantTabs', () => {
  it('shows VI first and selects it by default', () => {
    render(<VariantTabs variants={variants} value="vi" onChange={vi.fn()} />)
    const tabs = screen.getAllByRole('tab')
    expect(tabs[0].textContent).toBe('VI')
    expect(screen.getByRole('tab', { name: 'VI' }).getAttribute('aria-selected')).toBe('true')
  })

  it('reports a language change', () => {
    const onChange = vi.fn()
    render(<VariantTabs variants={variants} value="vi" onChange={onChange} />)
    fireEvent.click(screen.getByRole('tab', { name: 'EN' }))
    expect(onChange).toHaveBeenCalledWith('en')
  })
})
