const CLOSED_REQUEST_STATUSES = new Set(['approved', 'rejected', 'closed'])
const CLOSED_EXPENSE_STATUSES = new Set(['approved', 'rejected'])
const CLOSED_APPROVAL_STATUSES = new Set(['approved', 'rejected', 'archived'])

function statusValueOf(item) {
  return String(item?.statusValue || item?.status_value || '').trim().toLowerCase()
}

function statusLabelOf(item) {
  return String(item?.status || '').trim()
}

/** True when item is still waiting for approval (not approved/rejected/closed). */
export function isPendingWorkflowItem(item, kind = 'generic') {
  const value = statusValueOf(item)
  const label = statusLabelOf(item)

  if (kind === 'request') {
    if (value && CLOSED_REQUEST_STATUSES.has(value)) return false
    return value === 'submitted' || value === 'under_review' || label.includes('انتظار') || label.includes('بررسی')
  }

  if (kind === 'expense') {
    if (value && CLOSED_EXPENSE_STATUSES.has(value)) return false
    return value === 'pending' || value === 'under_review' || value === 'needs_document' || label.includes('انتظار') || label.includes('بررسی')
  }

  if (kind === 'approval') {
    if (value && CLOSED_APPROVAL_STATUSES.has(value)) return false
    if (item?.bucket === 'pending') return true
    return value === 'pending' || value === 'waiting_signature' || label.includes('انتظار') || label.includes('امضا') || label.includes('بررسی')
  }

  if (value && [...CLOSED_REQUEST_STATUSES, ...CLOSED_EXPENSE_STATUSES, ...CLOSED_APPROVAL_STATUSES].includes(value)) {
    return false
  }
  return label.includes('انتظار') || label.includes('بررسی') || label.includes('امضا')
}

/** Map workflow status labels to row/badge tone classes. */
export function toneForStatus(status) {
  const label = String(status || '')
  if (!label) return ''
  if (label.includes('رد') || label.includes('لغو') || label.includes('غیرفعال') || label.includes('مسدود')) return 'is-danger'
  if (
    label.includes('تایید') ||
    label.includes('تکمیل') ||
    label.includes('فعال') ||
    label.includes('نهایی') ||
    label.includes('پذیرفته') ||
    label === 'in' ||
    label === 'ورود'
  ) {
    return 'is-success'
  }
  if (
    label.includes('بررسی') ||
    label.includes('انتظار') ||
    label.includes('ارجاع') ||
    label.includes('در حال') ||
    label.includes('متوقف') ||
    label.includes('اصلاح') ||
    label.includes('پذیرش') ||
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
