const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const seenEventIds = new Map()
const SEEN_EVENT_TTL_MS = 5 * 60 * 1000
const HIDDEN_CLOSE_MS = 2 * 60 * 1000

let sharedSource = null
let sharedToken = ''
let refCount = 0
let hiddenCloseTimer = null
let visibilityBound = false
/** @type {Map<string, Set<EventListener>>} */
const sharedListeners = new Map()

function liveUrl(token) {
  const base = API_BASE_URL.replace(/\/$/, '')
  const url = new URL(`${base}/live/events`, window.location.origin)
  url.searchParams.set('token', token)
  return url.toString()
}

function clearHiddenCloseTimer() {
  if (hiddenCloseTimer) {
    window.clearTimeout(hiddenCloseTimer)
    hiddenCloseTimer = null
  }
}

function fanOut(type, event) {
  const bucket = sharedListeners.get(type)
  if (!bucket) return
  for (const listener of bucket) {
    try {
      listener(event)
    } catch {
      // keep other consumers alive
    }
  }
}

function bindSourceEvents(source) {
  source.addEventListener('open', (event) => fanOut('open', event))
  source.addEventListener('message', (event) => fanOut('message', event))
  source.addEventListener('error', (event) => fanOut('error', event))
}

function destroySharedSocket() {
  if (!sharedSource) return
  try {
    sharedSource.close()
  } catch {
    // ignore
  }
  sharedSource = null
}

function openSharedSocket(token) {
  destroySharedSocket()
  sharedToken = token
  sharedSource = new EventSource(liveUrl(token), { withCredentials: true })
  bindSourceEvents(sharedSource)
  return sharedSource
}

function ensureVisibilityHook() {
  if (visibilityBound || typeof document === 'undefined') return
  visibilityBound = true
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      clearHiddenCloseTimer()
      if (refCount > 0 && sharedToken && (!sharedSource || sharedSource.readyState === EventSource.CLOSED)) {
        openSharedSocket(sharedToken)
      }
      return
    }
    if (refCount <= 0 || !sharedSource) return
    clearHiddenCloseTimer()
    hiddenCloseTimer = window.setTimeout(() => {
      if (document.visibilityState === 'hidden') {
        destroySharedSocket()
      }
    }, HIDDEN_CLOSE_MS)
  })
}

function acquireShared(token) {
  if (typeof window === 'undefined' || typeof EventSource === 'undefined') return null
  const value = String(token || '').trim()
  if (!value) return null

  ensureVisibilityHook()
  clearHiddenCloseTimer()

  if (sharedSource && sharedToken === value && sharedSource.readyState !== EventSource.CLOSED) {
    refCount += 1
    return sharedSource
  }

  const preserve = sharedToken === value ? Math.max(refCount, 0) : 0
  openSharedSocket(value)
  refCount = preserve + 1
  return sharedSource
}

function releaseShared() {
  refCount = Math.max(0, refCount - 1)
  if (refCount > 0) return
  clearHiddenCloseTimer()
  destroySharedSocket()
  sharedToken = ''
  sharedListeners.clear()
}

/**
 * One EventSource per browser tab (ref-counted). Calling close() on the
 * returned handle only releases this consumer — the socket stays open while
 * other pages still hold a reference.
 */
export function createLiveEventSource(token) {
  const source = acquireShared(token)
  if (!source) return null

  let released = false
  /** @type {Array<[string, EventListener]>} */
  const owned = []

  return {
    addEventListener(type, listener) {
      if (!sharedListeners.has(type)) sharedListeners.set(type, new Set())
      sharedListeners.get(type).add(listener)
      owned.push([type, listener])
    },
    removeEventListener(type, listener) {
      sharedListeners.get(type)?.delete(listener)
    },
    close() {
      if (released) return
      released = true
      for (const [type, listener] of owned) {
        sharedListeners.get(type)?.delete(listener)
      }
      owned.length = 0
      releaseShared()
    },
  }
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
