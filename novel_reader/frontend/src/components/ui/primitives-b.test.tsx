import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Tabs, TabsList, TabsTrigger } from './tabs'
import { Slider } from './slider'
import { CommandDialog, CommandInput, CommandItem, CommandList } from './command'
import { Sheet, SheetContent, SheetTitle } from './sheet'
import { Toaster } from './sonner'

describe('navigation and overlay primitives', () => {
  it('Tabs marks the active trigger', () => {
    render(
      <Tabs defaultValue="vi">
        <TabsList><TabsTrigger value="vi">VI</TabsTrigger><TabsTrigger value="en">EN</TabsTrigger></TabsList>
      </Tabs>,
    )
    expect(screen.getByRole('tab', { name: 'VI' })).toHaveAttribute('data-state', 'active')
  })

  it('Slider accepts a value and change handler', () => {
    const onValueChange = vi.fn()
    render(<Slider aria-label="Cỡ chữ" min={14} max={24} value={[17]} onValueChange={onValueChange} />)
    expect(screen.getByRole('slider')).toHaveAttribute('aria-valuenow', '17')
  })

  it('CommandDialog renders its search input', () => {
    render(
      <CommandDialog open onOpenChange={() => undefined}>
        <CommandInput placeholder="Tìm chương…" />
        <CommandList><CommandItem value="a">Chương 1</CommandItem></CommandList>
      </CommandDialog>,
    )
    expect(screen.getByPlaceholderText('Tìm chương…')).toBeInTheDocument()
  })

  it('Sheet renders its title when open', () => {
    render(<Sheet open onOpenChange={() => undefined}><SheetContent><SheetTitle>Chương</SheetTitle></SheetContent></Sheet>)
    expect(screen.getByText('Chương')).toBeInTheDocument()
  })

  it('Toaster mounts without crashing', () => {
    const { container } = render(<Toaster />)
    expect(container).toBeInTheDocument()
  })
})
