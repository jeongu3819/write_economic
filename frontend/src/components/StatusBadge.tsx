interface StatusBadgeProps {
  status: string
}

interface BadgeConfig {
  label: string
  className: string
}

export default function StatusBadge({ status }: StatusBadgeProps): React.JSX.Element {
  const config: Record<string, BadgeConfig> = {
    pending: { label: '대기', className: 'badge-medium' },
    running: { label: '실행 중', className: 'badge-both' },
    completed: { label: '완료', className: 'badge-low' },
    failed: { label: '실패', className: 'badge-high' },
    draft: { label: '초안', className: 'badge-both' },
    archived: { label: '보관', className: 'badge-medium' },
  }

  const c = config[status] || { label: status, className: '' }

  return <span className={`badge ${c.className}`}>{c.label}</span>
}
