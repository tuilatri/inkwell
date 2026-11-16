import { useEffect, useState } from 'react'
import { Progress } from '@/components/ui/progress'

export function ReadingProgress({ enabled }: { enabled: boolean }) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!enabled) return
    function update() {
      const doc = document.documentElement
      const max = doc.scrollHeight - window.innerHeight
      setValue(max > 0 ? Math.min(100, Math.max(0, (window.scrollY / max) * 100)) : 0)
    }
    update()
    window.addEventListener('scroll', update, { passive: true })
    return () => window.removeEventListener('scroll', update)
  }, [enabled])

  return (
    <div className="sticky top-[57px] z-10 -mb-1.5 px-4 sm:px-6" aria-label="Tiến độ đọc">
      <Progress value={value} />
    </div>
  )
}
