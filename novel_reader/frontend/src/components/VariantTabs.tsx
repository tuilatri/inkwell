import type { Variant } from '../types'

interface Props {
  variants: Variant[]
  value: string
  onChange: (lang: string) => void
}

export default function VariantTabs({ variants, value, onChange }: Props) {
  const sorted = [...variants].sort((a, b) => (a.lang === 'vi' ? -1 : b.lang === 'vi' ? 1 : a.lang.localeCompare(b.lang)))
  return (
    <div className="row" role="tablist" aria-label="Language">
      {sorted.map((variant) => (
        <button
          key={variant.id}
          type="button"
          role="tab"
          aria-selected={variant.lang === value}
          className={variant.lang === value ? 'active' : ''}
          onClick={() => onChange(variant.lang)}
        >
          {variant.lang.toUpperCase()}
        </button>
      ))}
    </div>
  )
}
