const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const seenEventIds = new Map()
const SEEN_EVENT_TTL_MS = 5 * 60 * 1000

export function createLiveEventSource(token) {
  if (typeof window === 'undefined' || typeof EventSource === 'undefined') return null
  const value = String(token || '').trim()
  if (!value) return null

  const base = API_BASE_URL.replace(/\/$/, '')
  const url = new URL(`${base}/live/events`, window.location.origin)
  url.searchParams.set('token', value)
  return new EventSource(url.toString(), { withCredentials: true })
}

export function parseLiveEvent(raw) {
  try {
    const payload = JSON.parse(raw)
    if (!payload?.id) return payload
    const now = Date.now()
    for (const [id, seenAt] of seenEventIds) {
      if (now - seenAt > SEEN_EVENT_TTL_MS) seenEventIds.delete(id)
    }
    if (seenEventIds.has(payload.id)) return null
    seenEventIds.set(payload.id, now)
    return payload
  } catch {
    return null
  }
}
