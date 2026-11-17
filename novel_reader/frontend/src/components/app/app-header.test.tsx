import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AppHeader } from './app-header'

describe('AppHeader composition', () => {
  it('wires the three-dot button as the dropdown trigger (aria-haspopup)', () => {
    render(
      <TooltipProvider>
        <MemoryRouter><AppHeader onOpenSearch={() => undefined} /></MemoryRouter>
      </TooltipProvider>,
    )
    // Regression guard: TooltipTrigger must not wrap the DropdownMenu root,
    // otherwise Radix cannot attach the trigger props to this button.
    const account = screen.getByRole('button', { name: 'Tài khoản' })
    expect(account).toHaveAttribute('aria-haspopup', 'menu')
    expect(account).toHaveAttribute('aria-expanded', 'false')
  })

  it('hides account controls on the minimal login header', () => {
    render(
      <TooltipProvider>
        <MemoryRouter><AppHeader minimal /></MemoryRouter>
      </TooltipProvider>,
    )
    expect(screen.queryByRole('button', { name: 'Tài khoản' })).toBeNull()
  })
})
