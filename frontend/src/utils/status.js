/** Map workflow status labels to row/badge tone classes. */
export function toneForStatus(status) {
  const label = String(status || '')
  if (!label) return ''
  if (label.includes('رد') || label.includes('لغو') || label.includes('غیرفعال')) return 'is-danger'
  if (label.includes('تایید') || label.includes('فعال') || label.includes('نهایی') || label === 'in' || label === 'ورود') {
    return 'is-success'
  }
  if (
    label.includes('بررسی') ||
    label.includes('انتظار') ||
    label.includes('ارجاع') ||
    label.includes('در حال') ||
    label === 'out' ||
    label === 'خروج'
  ) {
    return 'is-warning'
  }
  return ''
}

/** Class for full table row background by status. */
export function rowToneForStatus(status) {
  const tone = toneForStatus(status)
  if (tone === 'is-success') return 'row-status-success'
  if (tone === 'is-danger') return 'row-status-danger'
  if (tone === 'is-warning') return 'row-status-warning'
  return ''
}
