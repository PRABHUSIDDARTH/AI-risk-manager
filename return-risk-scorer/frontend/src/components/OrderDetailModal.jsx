import ScoreBadge from './ScoreBadge'

const ACTION_LABELS = {
  allow:                'Allow',
  flag_for_verification:'Flag for verification',
  block_cod:            'Block COD',
}

const ACTION_COLORS = {
  allow:                'var(--allow-green)',
  flag_for_verification:'var(--flag-amber)',
  block_cod:            'var(--block-red)',
}

const FEATURE_LABELS = {
  order_value:          { label: 'Order value',          fmt: v => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
  num_items:            { label: 'Items',                fmt: v => v },
  category:             { label: 'Category',             fmt: v => v?.charAt(0).toUpperCase() + v?.slice(1) },
  payment_method:       { label: 'Payment method',       fmt: v => v?.charAt(0).toUpperCase() + v?.slice(1) },
  customer_return_rate: { label: 'Customer return rate', fmt: v => `${(Number(v) * 100).toFixed(1)}%` },
  days_to_deliver:      { label: 'Days to deliver',      fmt: v => `${v}` },
  seller_rating:        { label: 'Seller rating',        fmt: v => `${Number(v).toFixed(1)} / 5` },
  is_first_order:       { label: 'First order',          fmt: v => (v === true || v === 'true' || v === 1) ? 'Yes' : 'No' },
  discount_pct:         { label: 'Discount',             fmt: v => `${(Number(v) * 100).toFixed(1)}%` },
  pincode_return_rate:  { label: 'Pincode return rate',  fmt: v => `${(Number(v) * 100).toFixed(1)}%` },
  hour_of_order:        { label: 'Hour of order',        fmt: v => `${v}:00` },
  device_type:          { label: 'Device',               fmt: v => v?.charAt(0).toUpperCase() + v?.slice(1) },
}

export default function OrderDetailModal({ order, onClose }) {
  if (!order) return null
  const features = order.input_features || order
  const scorePct = Math.round((order.score ?? 0) * 100)
  const barColor = order.score < 0.35
    ? 'var(--allow-green)'
    : order.score < 0.65
      ? 'var(--flag-amber)'
      : 'var(--block-red)'

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed', inset: 0, zIndex: 50,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px',
      }}
    >
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute', inset: 0,
          background: 'rgba(18, 21, 28, 0.55)',
        }}
      />

      {/* Panel */}
      <div style={{
        position: 'relative',
        background: 'var(--paper)',
        border: '1px solid var(--border)',
        borderRadius: '3px',
        width: '100%',
        maxWidth: '640px',
        maxHeight: '90vh',
        overflowY: 'auto',
        fontFamily: 'IBM Plex Sans, sans-serif',
      }}>

        {/* Header bar */}
        <div style={{
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
        }}>
          <div>
            <p style={{ fontSize: '11px', color: 'var(--slate)', marginBottom: '4px' }}>
              Order detail
            </p>
            <h2
              className="mono"
              style={{ fontSize: '14px', fontWeight: 500, color: 'var(--ink)', letterSpacing: '-0.02em' }}
            >
              {order.order_id}
            </h2>
            {order.timestamp && (
              <p
                className="mono"
                style={{ fontSize: '11px', color: 'var(--slate)', marginTop: '3px' }}
              >
                {new Date(order.timestamp).toLocaleString('en-IN', {
                  year: 'numeric', month: 'short', day: '2-digit',
                  hour: '2-digit', minute: '2-digit', second: '2-digit',
                })}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: '1px solid var(--border)',
              borderRadius: '2px', padding: '4px 8px',
              color: 'var(--slate)', cursor: 'pointer', fontSize: '13px',
              lineHeight: 1, marginTop: '2px',
            }}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div style={{ padding: '20px' }}>

          {/* Score row */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '24px',
            paddingBottom: '16px',
            borderBottom: '1px solid var(--border)',
            marginBottom: '16px',
          }}>
            {/* Score bar */}
            <div style={{ flex: 1 }}>
              <div style={{
                display: 'flex', alignItems: 'baseline',
                justifyContent: 'space-between', marginBottom: '6px',
              }}>
                <span style={{ fontSize: '11.5px', color: 'var(--slate)' }}>Return risk score</span>
                <ScoreBadge score={order.score} />
              </div>
              {/* Track */}
              <div style={{ height: '4px', background: 'rgba(91,100,114,0.15)', borderRadius: '1px' }}>
                <div style={{
                  height: '4px', width: `${scorePct}%`,
                  background: barColor, borderRadius: '1px',
                  transition: 'width 300ms ease',
                }} />
              </div>
              <div
                className="mono"
                style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: '10px', color: 'var(--slate)', marginTop: '3px', opacity: 0.7,
                }}
              >
                <span>0%</span><span>50%</span><span>100%</span>
              </div>
            </div>

            {/* Decision */}
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <p style={{ fontSize: '11px', color: 'var(--slate)', marginBottom: '5px' }}>Decision</p>
              <span style={{
                display: 'inline-block',
                background: ACTION_COLORS[order.action] ?? 'var(--slate)',
                color: 'var(--paper)',
                borderRadius: '2px',
                padding: '4px 10px',
                fontSize: '12.5px',
                fontWeight: 500,
              }}>
                {ACTION_LABELS[order.action] ?? order.action}
              </span>
            </div>
          </div>

          {/* Reasoning */}
          {order.explanation && (
            <div style={{
              marginBottom: '16px',
              paddingBottom: '16px',
              borderBottom: '1px solid var(--border)',
            }}>
              <p style={{ fontSize: '11px', color: 'var(--slate)', marginBottom: '7px' }}>Reasoning</p>
              <p style={{ fontSize: '13px', color: 'var(--ink)', lineHeight: 1.6 }}>
                {order.explanation}
              </p>
            </div>
          )}

          {/* Features table */}
          <div>
            <p style={{ fontSize: '11px', color: 'var(--slate)', marginBottom: '10px' }}>Order features</p>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
              <tbody>
                {Object.entries(FEATURE_LABELS).map(([key, { label, fmt }], i) =>
                  features[key] !== undefined ? (
                    <tr key={key}>
                      <td style={{
                        padding: '6px 0',
                        color: 'var(--slate)',
                        width: '50%',
                        borderBottom: '1px solid var(--border)',
                        paddingRight: '16px',
                      }}>
                        {label}
                      </td>
                      <td
                        className="mono"
                        style={{
                          padding: '6px 0',
                          color: 'var(--ink)',
                          textAlign: 'right',
                          borderBottom: '1px solid var(--border)',
                          fontWeight: 500,
                          fontSize: '12px',
                        }}
                      >
                        {fmt(features[key])}
                      </td>
                    </tr>
                  ) : null
                )}
              </tbody>
            </table>
          </div>

          {/* Audit footer */}
          <div
            className="mono"
            style={{
              display: 'flex', gap: '20px', alignItems: 'center',
              marginTop: '16px', paddingTop: '12px',
              borderTop: '1px solid var(--border)',
              fontSize: '11px', color: 'var(--slate)',
            }}
          >
            {order.audit_id && <span>Audit #{order.audit_id}</span>}
            {order.model_version && <span>Model: {order.model_version}</span>}
          </div>

        </div>
      </div>
    </div>
  )
}
