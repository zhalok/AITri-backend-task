import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export interface Option { value: string; label: string }

interface Props {
  value: string
  onChange: (value: string) => void
  options: Option[]
  placeholder?: string
  disabled?: boolean
  className?: string
  ariaLabel?: string
}

/** A small wrapper so every dropdown in the app is configured the same way. */
export function OptionSelect({ value, onChange, options, placeholder, disabled, className, ariaLabel }: Props) {
  return (
    <Select items={options} value={value} onValueChange={(v) => v !== null && onChange(v)} disabled={disabled}>
      <SelectTrigger className={className} aria-label={ariaLabel}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
