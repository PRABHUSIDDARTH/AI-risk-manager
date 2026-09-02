import ScoreBadge from './ScoreBadge'

const ACTION_STYLES = {
  allow:                { color: 'var(--allow-green)' },
  flag_for_verification:{ color: 'var(--flag-amber)' },
  block_cod:            { color: 'var(--block-red)' },
}

const ACTION_LABELS = {
  allow:                'Allow',
  flag_for_verification:'Flag for verification',
  block_cod:            'Block COD',
}

const PAYMENT_LABELS = {
  cod:     'COD',
  prepaid: 'Prepaid',
  emi:     'EMI',
}

function SkeletonRow() {
  return (
    <tr style={{ borderBottom: '1px solid var(--border)' }}>
      {Array(8).fill(0).map((_, i) => (
        <td key={i} style={{ padding: '10px 12px' }}>
          <div
            style={{
              height: '11px',
              borderRadius: '2px',
              background: 'rgba(91,100,114,0.1)',
              width: `${50 + (i * 17) % 40}%`,
              animation: 'pulse 1.4s ease-in-out infinite',
            }}
          />
        </td>
      ))}
    </tr>
  )
}

export default function OrderTable({ orders, onSelectOrder, loading, animate }) {
  if (!loading && orders.length === 0) {
    return (
      <div style={{ padding: '40px 16px', color: 'var(--slate)', textAlign: 'center' }}>
        Upload a CSV and run batch analysis to score orders.
      </div>
    )
  }

  const COL_HEADERS = [
    { label: 'Order ID',    align: 'left'  },
    { label: 'Category',    align: 'left'  },
    { label: 'Payment',     align: 'left'  },
    { label: 'Value (₹)',   align: 'right' },
    { label: 'Score',       align: 'right' },
    { label: 'Decision',    align: 'left'  },
    { label: 'Reasoning',   align: 'left'  },
    { label: '',            align: 'left'  },
  ]

  const cellStyle = (align = 'left') => ({
    padding: '9px 12px',
    textAlign: align,
    verticalAlign: 'middle',
    borderBottom: '1px solid var(--border)',
    whiteSpace: 'nowrap',
  })

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {COL_HEADERS.map((h) => (
              <th
                key={h.label}
                style={{
                  padding: '8px 12px',
                  textAlign: h.align,
                  fontFamily: 'IBM Plex Sans, sans-serif',
                  fontWeight: 500,
                  fontSize: '11px',
                  color: 'var(--slate)',
                  letterSpacing: '0.01em',
                  whiteSpace: 'nowrap',
                  position: 'sticky',
                  top: 0,
                  background: 'var(--paper)',
                  borderBottom: '1px solid var(--border)',
                }}
              >
                {h.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading
            ? Array(7).fill(0).map((_, i) => <SkeletonRow key={i} />)
            : orders.map((order, i) => (
              <tr
                key={order.order_id + i}
                className={animate ? 'ledger-row' : ''}
                style={{
                  animationDelay: animate ? `${i * 35}ms` : '0ms',
                  cursor: 'default',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(43,76,126,0.04)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {/* Order ID */}
                <td style={{ ...cellStyle('left'), maxWidth: '130px' }}>
                  <span
                    className="mono"
                    style={{ fontSize: '11.5px', color: 'var(--slate)', letterSpacing: '-0.01em' }}
                    title={order.order_id}
                  >
                    {order.order_id.length > 16
                      ? order.order_id.slice(0, 8) + '…' + order.order_id.slice(-6)
                      : order.order_id}
                  </span>
                </td>

                {/* Category */}
                <td style={{ ...cellStyle('left'), color: 'var(--ink)' }}>
                  {order.category
                    ? order.category.charAt(0).toUpperCase() + order.category.slice(1)
                    : '—'}
                </td>

                {/* Payment */}
                <td style={{ ...cellStyle('left') }}>
                  <span
                    style={{
                      fontFamily: 'IBM Plex Mono, monospace',
                      fontSize: '11px',
                      color: order.payment_method === 'cod' ? 'var(--flag-amber)' : 'var(--slate)',
                      fontWeight: order.payment_method === 'cod' ? 500 : 400,
                    }}
                  >
                    {PAYMENT_LABELS[order.payment_method] ?? order.payment_method}
                  </span>
                </td>

                {/* Value */}
                <td style={{ ...cellStyle('right') }}>
                  <span className="mono" style={{ color: 'var(--ink)', fontSize: '12px' }}>
                    {Number(order.order_value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </span>
                </td>

                {/* Score */}
                <td style={{ ...cellStyle('right') }}>
                  <ScoreBadge score={order.score} />
                </td>

                {/* Decision */}
                <td style={{ ...cellStyle('left') }}>
                  <span style={{ ...ACTION_STYLES[order.action], fontWeight: 500 }}>
                    {ACTION_LABELS[order.action] ?? order.action}
                  </span>
                </td>

                {/* Reasoning */}
                <td style={{ ...cellStyle('left'), maxWidth: '260px', whiteSpace: 'normal' }}>
                  <span
                    style={{ color: 'var(--slate)', lineHeight: 1.4 }}
                    title={order.explanation}
                  >
                    {order.explanation?.length > 85
                      ? order.explanation.slice(0, 85) + '…'
                      : order.explanation}
                  </span>
                </td>

                {/* Details */}
                <td style={{ ...cellStyle('left') }}>
                  <button
                    onClick={() => onSelectOrder(order)}
                    style={{
                      background: 'none',
                      border: '1px solid var(--border)',
                      borderRadius: '2px',
                      color: 'var(--ledger-blue)',
                      fontFamily: 'IBM Plex Sans, sans-serif',
                      fontSize: '11.5px',
                      fontWeight: 500,
                      padding: '3px 8px',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = 'var(--ledger-blue)'
                      e.currentTarget.style.color = '#F7F6F3'
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = 'none'
                      e.currentTarget.style.color = 'var(--ledger-blue)'
                    }}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))
          }
        </tbody>
      </table>
    </div>
  )
}
