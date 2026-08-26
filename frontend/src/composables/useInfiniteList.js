import { computed, ref, unref, watch } from 'vue'

import { LIST_PAGE_SIZE } from '../utils/listPaging'

/**
 * Progressive list rendering + optional remote "load more".
 * - Always reveals at most `pageSize` more rows at a time.
 * - If local source is exhausted and `hasMoreRemote` is true, calls `onLoadMore`.
 */
export function useInfiniteList(source, options = {}) {
  const pageSize = Number(options.pageSize) || LIST_PAGE_SIZE
  const visibleCount = ref(pageSize)
  const loadingMore = ref(false)

  function reset() {
    visibleCount.value = pageSize
  }

  watch(
    () => {
      if (options.resetKey === undefined) return null
      return unref(options.resetKey)
    },
    () => {
      reset()
    },
  )

  const sourceList = computed(() => {
    const list = unref(source)
    return Array.isArray(list) ? list : []
  })

  const items = computed(() => sourceList.value.slice(0, visibleCount.value))

  const hasMoreLocal = computed(() => sourceList.value.length > visibleCount.value)
  const hasMoreRemote = computed(() => Boolean(unref(options.hasMoreRemote)))
  const hasMore = computed(() => hasMoreLocal.value || hasMoreRemote.value)

  async function loadMore() {
    if (loadingMore.value) return false
    if (hasMoreLocal.value) {
      visibleCount.value += pageSize
      return true
    }
    if (!hasMoreRemote.value || typeof options.onLoadMore !== 'function') return false

    loadingMore.value = true
    try {
      const before = sourceList.value.length
      await options.onLoadMore()
      const after = sourceList.value.length
      // Reveal newly appended remote rows (or keep showing what we have).
      visibleCount.value = Math.max(visibleCount.value + pageSize, after)
      return after > before || hasMoreRemote.value
    } finally {
      loadingMore.value = false
    }
  }

  return {
    items,
    hasMore,
    loadingMore,
    loadMore,
    reset,
    visibleCount,
    pageSize,
  }
}
