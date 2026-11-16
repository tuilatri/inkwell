import { BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Empty } from '@/components/ui/empty'

export function EmptyState({ title, description, actionLabel, onAction }: {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}) {
  return (
    <Empty
      icon={<BookOpen className="h-8 w-8" aria-hidden="true" />}
      title={title}
      description={description}
      action={actionLabel && onAction ? <Button size="sm" variant="outline" onClick={onAction}>{actionLabel}</Button> : undefined}
    />
  )
}
