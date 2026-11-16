import { useEffect } from 'react'

export function KeyboardShortcuts({ onPrev, onNext, onToggleList }: {
  onPrev: () => void
  onNext: () => void
  onToggleList: () => void
}) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null
      if (target && ['INPUT', 'TEXTAREA'].includes(target.tagName)) return
      if (event.key === 'j' || event.key === 'ArrowRight') { event.preventDefault(); onNext() }
      else if (event.key === 'k' || event.key === 'ArrowLeft') { event.preventDefault(); onPrev() }
      else if (event.key === 'l') { event.preventDefault(); onToggleList() }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onPrev, onNext, onToggleList])
  return null
}
