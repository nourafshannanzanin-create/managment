const prefetched = new Set()

/** Warm the lazy page chunk so menu clicks feel instant. */
export function prefetchRoute(router, to) {
  if (!router || !to) return
  const key = String(to)
  if (prefetched.has(key)) return
  try {
    const resolved = router.resolve(to)
    const loaders = resolved.matched
      .map((record) => record.components?.default)
      .filter((loader) => typeof loader === 'function')
    if (!loaders.length) {
      prefetched.add(key)
      return
    }
    prefetched.add(key)
    void Promise.all(loaders.map((loader) => Promise.resolve(loader()).catch(() => {})))
  } catch {
    prefetched.delete(key)
  }
}

export function prefetchCommonRoutes(router, paths = []) {
  paths.forEach((path) => prefetchRoute(router, path))
}
