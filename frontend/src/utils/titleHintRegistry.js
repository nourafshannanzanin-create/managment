let activeCloser = null

export function claimTitleHint(closer) {
  if (typeof closer !== 'function') return
  if (activeCloser && activeCloser !== closer) {
    try {
      activeCloser()
    } catch {
      /* ignore stale closer */
    }
  }
  activeCloser = closer
}

export function releaseTitleHint(closer) {
  if (activeCloser === closer) activeCloser = null
}
