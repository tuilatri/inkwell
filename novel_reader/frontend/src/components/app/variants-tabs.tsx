import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { Variant } from '@/types'

export function VariantsTabs({ variants, value, onChange }: { variants: Variant[]; value: string; onChange: (lang: string) => void }) {
  const sorted = [...variants].sort((a, b) => (a.lang === 'vi' ? -1 : b.lang === 'vi' ? 1 : a.lang.localeCompare(b.lang)))
  return (
    <Tabs value={value} onValueChange={onChange}>
      <TabsList aria-label="Ngôn ngữ">
        {sorted.map((variant) => (
          <TabsTrigger key={variant.id} value={variant.lang}>{variant.lang.toUpperCase()}</TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  )
}
