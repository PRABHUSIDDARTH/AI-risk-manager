import { useState, useCallback } from 'react'
import BatchRunner from './components/BatchRunner'
import OrderTable from './components/OrderTable'
import OrderDetailModal from './components/OrderDetailModal'
import { getOrderDetail } from './api/client'

export default function App() {
  const [orders, setOrders] = useState([])
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [animateTable, setAnimateTable] = useState(false)

  const handleBatchComplete = useCallback((rows, summary) => {
    setAnimateTable(true)
    setOrders(rows.filter(r => !r.error))
    setStats(summary)
    // Reset animation flag after rows have all staggered in
    setTimeout(() => setAnimateTable(false), rows.length * 35 + 200)
  }, [])

  const handleSelectOrder = useCallback(async (order) => {
    setSelectedOrder(order)
    try {
      const detail = await getOrderDetail(order.order_id)
      setSelectedOrder(detail)
    } catch {
      // use partial row data if detail fetch fails
    }
  }, [])

  const totalScored = stats?.total ?? orders.length
  const allowCount  = stats?.allow_count ?? orders.filter(o => o.action === 'allow').length
  const flagCount   = stats?.flag_count  ?? orders.filter(o => o.action === 'flag_for_verification').length
  const blockCount  = stats?.block_count ?? orders.filter(o => o.action === 'block_cod').length
  const avgScore    = stats?.avg_score
    ? `${(stats.avg_score * 100).toFixed(1)}%`
    : orders.length > 0
      ? `${(orders.reduce((s, o) => s + (o.score || 0), 0) / orders.length * 100).toFixed(1)}%`
      : null

  const hasData = orders.length > 0 || loading

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--paper)',
      color: 'var(--ink)',
      fontFamily: 'IBM Plex Sans, sans-serif',
    }}>

      {/* ── Header ─────────────────────────────────────────────────── */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--paper)',
        position: 'sticky', top: 0, zIndex: 40,
      }}>
        <div style={{
          maxWidth: '1400px', margin: '0 auto',
          padding: '0 24px',
          height: '44px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          {/* Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '1px',
              backgroundColor: 'var(--ledger-blue)',
            }} />
            <span style={{
              fontFamily: 'IBM Plex Sans, sans-serif',
              fontWeight: 600,
              fontSize: '13px',
              color: 'var(--ink)',
              letterSpacing: '-0.01em',
            }}>
              Risk operations console
            </span>
            <span style={{
              width: '1px', height: '14px',
              background: 'var(--border)',
              display: 'inline-block',
            }} />
            <span style={{
              fontFamily: 'IBM Plex Mono, monospace',
              fontSize: '11px',
              color: 'var(--slate)',
            }}>
              Return mitigation engine
            </span>
          </div>

          {/* Operational Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11px',
              color: 'var(--slate)',
              fontFamily: 'IBM Plex Mono, monospace',
            }}>
              <span style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: 'var(--allow-green)',
                display: 'inline-block',
              }} />
              Connected
            </span>
            <span style={{
              border: '1px solid var(--border)',
              borderRadius: '2px',
              padding: '2px 8px',
              fontSize: '11px',
              fontFamily: 'IBM Plex Mono, monospace',
              color: 'var(--slate)',
            }}>
              Model: GBC-v1
            </span>
            <span style={{
              border: '1px solid var(--border)',
              borderRadius: '2px',
              padding: '2px 8px',
              fontSize: '11px',
              fontFamily: 'IBM Plex Mono, monospace',
              color: 'var(--slate)',
            }}>
              Threshold: 0.30
            </span>
          </div>
        </div>
      </header>

      {/* ── Main content ───────────────────────────────────────────── */}
      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px 48px' }}>

        {/* Batch runner */}
        <BatchRunner onBatchComplete={handleBatchComplete} />

        {/* Summary strip — shown only when there's data */}
        {(hasData || stats) && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 0',
            borderBottom: '1px solid var(--border)',
            marginBottom: 0,
          }}>
            <span
              className="mono"
              style={{ fontSize: '12px', color: 'var(--slate)' }}
            >
              {totalScored.toLocaleString()} scored
              <span style={{ margin: '0 8px', opacity: 0.35 }}>|</span>
              <span style={{ color: 'var(--allow-green)' }}>{allowCount.toLocaleString()} allowed</span>
              <span style={{ margin: '0 8px', opacity: 0.35 }}>|</span>
              <span style={{ color: 'var(--flag-amber)' }}>{flagCount.toLocaleString()} flagged</span>
              <span style={{ margin: '0 8px', opacity: 0.35 }}>|</span>
              <span style={{ color: 'var(--block-red)' }}>{blockCount.toLocaleString()} blocked</span>
              {avgScore && (
                <>
                  <span style={{ margin: '0 8px', opacity: 0.35 }}>|</span>
                  <span>avg {avgScore}</span>
                </>
              )}
            </span>
          </div>
        )}

        {/* Order table — full width, no card wrapper */}
        <OrderTable
          orders={orders}
          onSelectOrder={handleSelectOrder}
          loading={loading}
          animate={animateTable}
        />

      </main>

      {/* Detail modal */}
      <OrderDetailModal
        order={selectedOrder}
        onClose={() => setSelectedOrder(null)}
      />
    </div>
  )
}
