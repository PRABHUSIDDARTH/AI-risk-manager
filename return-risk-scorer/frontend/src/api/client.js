import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getOrders = (page = 1, limit = 50) =>
  api.get('/orders', { params: { page, limit } }).then(r => r.data)

export const getOrderDetail = (orderId) =>
  api.get(`/orders/${orderId}`).then(r => r.data)

export const scoreSingleOrder = (orderData) =>
  api.post('/score', orderData).then(r => r.data)

/**
 * Stream batch CSV scoring.
 * @param {File} csvFile
 * @param {(row: object) => void} onRow - called for each scored order
 * @param {(summary: object) => void} onSummary - called with the final _summary line
 * @param {(processed: number) => void} onProgress - called with count after each row
 */
export async function runBatch(csvFile, onRow, onSummary, onProgress) {
  const formData = new FormData()
  formData.append('file', csvFile)

  const response = await fetch('/api/batch', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Batch request failed: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let processed = 0

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    // Normalize \r\n → \n so CRLF from uvicorn doesn't leave stray \r on tokens
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    const lines = buffer.split('\n')
    buffer = lines.pop() // keep the (possibly incomplete) last segment
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      try {
        const obj = JSON.parse(trimmed)
        if (obj._summary) {
          onSummary(obj)
        } else {
          processed += 1
          onRow(obj)
          onProgress(processed)
        }
      } catch (e) {
        console.warn('Failed to parse NDJSON line:', trimmed)
      }
    }
  }
  // Flush any remaining buffer content (stream ended without trailing \n)
  const remaining = buffer.trim()
  if (remaining) {
    try {
      const obj = JSON.parse(remaining)
      if (obj._summary) onSummary(obj)
      else { onRow(obj); onProgress(++processed) }
    } catch (_) {}
  }

}
