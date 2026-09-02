import { useState, useRef } from 'react'
import { runBatch } from '../api/client'

export default function BatchRunner({ onBatchComplete }) {
  const [file, setFile] = useState(null)
  const [running, setRunning] = useState(false)
  const [processed, setProcessed] = useState(0)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState('')
  const [summary, setSummary] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef(null)
  const resultsRef = useRef([])

  const handleFileChange = (e) => {
    const f = e.target.files?.[0]
    if (f) { setFile(f); setError(''); setSummary(null); setProcessed(0) }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f?.name.endsWith('.csv')) { setFile(f); setError(''); setSummary(null) }
    else setError('File must be a .csv')
  }

  const handleRun = async () => {
    if (!file || running) return
    setRunning(true)
    setProcessed(0)
    setError('')
    setSummary(null)
    resultsRef.current = []

    // Estimate row count for progress bar (header line -1)
    try {
      const peek = await file.slice(0, 65536).text()
      const lineCount = Math.max(0, peek.split('\n').filter(Boolean).length - 1)
      setTotal(lineCount)
    } catch (_) {
      setTotal(0)
    }

    try {
      await runBatch(
        file,                                          // pass the original File directly
        (row) => { resultsRef.current.push(row) },
        (sum) => {
          setSummary(sum)
          // Snapshot the array at the moment summary arrives
          onBatchComplete([...resultsRef.current], sum)
        },
        (count) => setProcessed(count)
      )
    } catch (e) {
      setError(e.message || 'Batch processing failed')
    } finally {
      setRunning(false)
    }
  }


  const progressPct = total > 0 ? Math.min(100, (processed / total) * 100) : 0

  return (
    <div style={{ borderBottom: '1px solid var(--border)', padding: '16px 0 20px' }}>
      {/* Controls row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>

        {/* Dropzone — compact inline version */}
        <div
          onClick={() => fileRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          style={{
            border: `1px ${dragOver ? 'solid' : 'dashed'} ${dragOver ? 'var(--ledger-blue)' : 'var(--border)'}`,
            borderRadius: '2px',
            padding: '7px 14px',
            cursor: 'pointer',
            color: file ? 'var(--ink)' : 'var(--slate)',
            fontSize: '12.5px',
            background: dragOver ? 'rgba(43,76,126,0.04)' : 'transparent',
            minWidth: '220px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <input ref={fileRef} type="file" accept=".csv" style={{ display: 'none' }} onChange={handleFileChange} />
          {/* Upload icon — functional */}
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, color: 'var(--slate)' }}>
            <path d="M8 1v10M4 5l4-4 4 4M2 13h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          {file ? (
            <span>
              <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '11.5px' }}>{file.name}</span>
              <span style={{ color: 'var(--slate)', marginLeft: '6px', fontSize: '11px' }}>
                {(file.size / 1024).toFixed(0)} KB
              </span>
            </span>
          ) : (
            <span>Select a CSV file or drop here</span>
          )}
        </div>

        {/* Run button */}
        <button
          onClick={handleRun}
          disabled={!file || running}
          style={{
            background: !file || running ? 'rgba(91,100,114,0.12)' : 'var(--ledger-blue)',
            color: !file || running ? 'var(--slate)' : '#F7F6F3',
            border: 'none',
            borderRadius: '2px',
            padding: '7px 18px',
            fontFamily: 'IBM Plex Sans, sans-serif',
            fontSize: '12.5px',
            fontWeight: 500,
            cursor: !file || running ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '7px',
            flexShrink: 0,
          }}
        >
          {running ? (
            <>
              <svg style={{ animation: 'spin 0.8s linear infinite', width: '12px', height: '12px' }} viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeDasharray="40" strokeDashoffset="15"/>
              </svg>
              Scoring {processed.toLocaleString()} of {total.toLocaleString()}…
            </>
          ) : 'Run batch'}
        </button>

        {/* Inline progress bar when running */}
        {running && (
          <div style={{ flex: 1, minWidth: '100px', maxWidth: '200px', height: '3px', background: 'var(--border)', borderRadius: '1px' }}>
            <div style={{
              height: '3px',
              width: `${progressPct}%`,
              background: 'var(--ledger-blue)',
              borderRadius: '1px',
              transition: 'width 80ms linear',
            }} />
          </div>
        )}

        {/* Inline summary — appears after completion, no cards */}
        {summary && !running && (
          <span
            className="mono"
            style={{ fontSize: '12px', color: 'var(--slate)', marginLeft: 'auto' }}
          >
            {summary.total.toLocaleString()} scored
            <span style={{ margin: '0 6px', opacity: 0.4 }}>|</span>
            <span style={{ color: 'var(--allow-green)' }}>{summary.allow_count.toLocaleString()} allowed</span>
            <span style={{ margin: '0 6px', opacity: 0.4 }}>|</span>
            <span style={{ color: 'var(--flag-amber)' }}>{summary.flag_count.toLocaleString()} flagged</span>
            <span style={{ margin: '0 6px', opacity: 0.4 }}>|</span>
            <span style={{ color: 'var(--block-red)' }}>{summary.block_count.toLocaleString()} blocked</span>
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div style={{
          marginTop: '10px',
          padding: '7px 12px',
          border: '1px solid var(--block-red)',
          borderRadius: '2px',
          color: 'var(--block-red)',
          fontSize: '12px',
          background: 'rgba(168,50,50,0.05)',
        }}>
          {error}
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
