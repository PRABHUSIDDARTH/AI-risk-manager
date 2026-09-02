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
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{
              fontFamily: 'IBM Plex Mono, monospace',
              fontWeight: 500,
              fontSize: '13px',
              color: 'var(--ledger-blue)',
              letterSpacing: '-0.02em',
            }}>
              RP
            </span>
            <span style={{
              width: '1px', height: '16px',
              background: 'var(--border)',
              display: 'inline-block',
            }} />
            <span style={{ fontSize: '13.5px', fontWeight: 500, color: 'var(--ink)' }}>
              Return risk scorer
            </span>
          </div>

          {/* Meta tags */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              border: '1px solid var(--border)',
              borderRadius: '2px',
              padding: '2px 8px',
              fontSize: '11px',
              color: 'var(--slate)',
            }}>
              Razorpay Buildathon 2026
            </span>
            <span style={{
              border: '1px solid var(--border)',
              borderRadius: '2px',
              padding: '2px 8px',
              fontSize: '11px',
              color: 'var(--slate)',
            }}>
              AI Risk Manager
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
