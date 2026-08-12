/**
 * Position a teleported fixed panel relative to an anchor, keeping it inside the viewport.
 */
export function buildAnchoredPanelStyle(anchorEl, panelEl, options = {}) {
  if (!anchorEl) return {}

  const {
    minWidth = 220,
    preferredWidth,
    gap = 8,
    padding = 12,
    zIndex = 3200,
    matchAnchorWidth = false,
  } = options

  const rect = anchorEl.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const availableWidth = Math.max(160, viewportWidth - padding * 2)

  let width = matchAnchorWidth
    ? rect.width
    : Math.max(rect.width, preferredWidth || minWidth, minWidth)
  width = Math.min(width, availableWidth)

  let left = rect.left
  if (left + width > viewportWidth - padding) {
    left = viewportWidth - padding - width
  }
  if (left < padding) left = padding

  const spaceBelow = viewportHeight - rect.bottom - padding - gap
  const spaceAbove = rect.top - padding - gap
  const placeBelow = spaceBelow >= 180 || spaceBelow >= spaceAbove

  const measuredHeight = panelEl?.offsetHeight || 0
  const maxHeight = Math.max(0, placeBelow ? spaceBelow : spaceAbove)

  let top
  if (placeBelow) {
    top = rect.bottom + gap
  } else {
    const height = measuredHeight > 0 ? Math.min(measuredHeight, maxHeight) : Math.min(280, maxHeight)
    top = rect.top - gap - height
  }

  const viewportMax = Math.max(0, viewportHeight - padding * 2)
  const clampedMaxHeight = Math.min(maxHeight || viewportMax, viewportMax)
  top = Math.min(Math.max(top, padding), Math.max(padding, viewportHeight - padding - clampedMaxHeight))

  return {
    position: 'fixed',
    top: `${Math.round(top)}px`,
    left: `${Math.round(left)}px`,
    right: 'auto',
    bottom: 'auto',
    width: `${Math.round(width)}px`,
    maxWidth: `${availableWidth}px`,
    maxHeight: `${Math.round(clampedMaxHeight)}px`,
    overflowY: 'auto',
    overflowX: 'hidden',
    zIndex: String(zIndex),
  }
}
