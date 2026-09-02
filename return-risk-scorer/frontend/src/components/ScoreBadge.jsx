export default function ScoreBadge({ score }) {
  const pct = Math.round((score ?? 0) * 100)

  let bg, label
  if (score < 0.35) {
    bg = 'var(--allow-green)'
    label = 'Allow'
  } else if (score < 0.65) {
    bg = 'var(--flag-amber)'
    label = 'Flag'
  } else {
    bg = 'var(--block-red)'
    label = 'Block'
  }

  return (
    <span
      className="mono inline-flex items-center gap-1.5 px-1.5 py-0.5 text-xs font-medium"
      style={{
        backgroundColor: bg,
        color: '#F7F6F3',
        borderRadius: '2px',
        letterSpacing: 0,
      }}
    >
      {label}
      <span style={{ opacity: 0.85 }}>{pct}%</span>
    </span>
  )
}
