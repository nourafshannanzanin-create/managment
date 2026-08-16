export function formatBadgeCount(value) {
  const count = Number(value || 0)
  if (!Number.isFinite(count) || count <= 0) return ''
  if (count > 99) return '۹۹+'
  return Math.floor(count).toLocaleString('fa-IR')
}
