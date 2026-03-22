interface WeekSelectorProps {
  weeks: string[]
  selected: string
  onChange: (value: string) => void
}

export default function WeekSelector({ weeks, selected, onChange }: WeekSelectorProps): React.JSX.Element {
  return (
    <select value={selected} onChange={(e) => onChange(e.target.value)}>
      <option value="">주차 선택</option>
      {weeks.map((w) => (
        <option key={w} value={w}>{w}</option>
      ))}
    </select>
  )
}
