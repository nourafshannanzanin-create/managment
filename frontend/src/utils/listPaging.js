/** Shared list page size for tables/cards across the app. */
export const LIST_PAGE_SIZE = 50

export function createCollectionPaging() {
  return {
    total: 0,
    loaded: 0,
    hasMore: false,
    loading: false,
  }
}

export function createCollectionPagingMap(sections = []) {
  return Object.fromEntries(sections.map((section) => [section, createCollectionPaging()]))
}
