import { Typography } from '@/components/ui/typography'
import { cn } from '@/lib/utils'

export function ReaderView({ text, fontSize, lineHeight, className }: {
  text: string
  fontSize: number
  lineHeight: number
  className?: string
}) {
  return (
    <article
      className={cn('mx-auto max-w-[70ch] rounded-lg border border-border bg-card px-5 py-8 sm:px-10 sm:py-12', className)}
      style={{ ['--reader-size' as string]: `${fontSize}px`, ['--reader-leading' as string]: String(lineHeight) }}
      data-testid="reader-view"
    >
      <Typography variant="chapter" className="whitespace-pre-wrap" style={{ fontSize: 'var(--reader-size)', lineHeight: 'var(--reader-leading)' }}>
        {text}
      </Typography>
    </article>
  )
}
