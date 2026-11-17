import type { ComponentPropsWithoutRef, ElementType } from 'react'
import { cn } from '@/lib/utils'

type Variant = 'display' | 'heading' | 'body' | 'caption' | 'chapter'

const styles: Record<Variant, string> = {
  display: 'text-3xl font-semibold tracking-[-0.03em] text-foreground',
  heading: 'text-xl font-semibold tracking-[-0.02em] text-foreground',
  body: 'text-[15px] leading-7 text-foreground',
  caption: 'text-sm text-muted-foreground',
  chapter: 'font-serif text-[1.0625rem] leading-[1.9] text-foreground',
}

export function Typography({
  variant = 'body',
  as,
  className,
  ...props
}: ComponentPropsWithoutRef<'p'> & { variant?: Variant; as?: ElementType }) {
  const Comp = as ?? 'p'
  return <Comp className={cn(styles[variant], className)} {...props} />
}
