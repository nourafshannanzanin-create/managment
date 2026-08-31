import { reactive } from 'vue'
import { normalizeError } from './errors'

let nextId = 1
const CENTER_LIMIT = 40
const STORAGE_KEY = 'carno.notification.center.v1'

function loadStoredCenter() {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.slice(0, CENTER_LIMIT) : []
  } catch {
    return []
  }
}

function persistCenter() {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(toastState.center.slice(0, CENTER_LIMIT)))
  } catch {
    // ignore quota / private mode
  }
}

export const toastState = reactive({
  items: [],
  center: loadStoredCenter(),
})

function normalizeDuration(value, fallback = 4200) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric <= 0) return fallback
  return numeric
}

function pushToCenter(entry) {
  const item = {
    id: entry.id || (nextId += 1),
    type: entry.type || 'info',
    title: String(entry.title || '').trim(),
    message: String(entry.message || '').trim(),
    createdAt: entry.createdAt || new Date().toISOString(),
    route: entry.route || '',
    read: Boolean(entry.read),
    source: entry.source || 'toast',
  }
  if (!item.message && !item.title) return null
  toastState.center = [item, ...toastState.center.filter((row) => String(row.id) !== String(item.id))].slice(0, CENTER_LIMIT)
  persistCenter()
  return item.id
}

export function pushNotification(message, type = 'info', options = {}) {
  const text = String(message || '').trim()
  const title = String(options.title || '').trim()
  if (!text && !title) return null
  const item = {
    id: nextId += 1,
    type,
    message: text,
    title,
    suggestion: String(options.suggestion || '').trim(),
    fields: Array.isArray(options.fields) ? options.fields : [],
    duration: normalizeDuration(options.duration, type === 'error' ? 5600 : 3600),
  }
  toastState.items.push(item)
  pushToCenter({
    id: item.id,
    type: item.type,
    title: item.title,
    message: item.message,
    route: options.route || '',
    source: 'toast',
  })
  window.setTimeout(() => removeNotification(item.id), item.duration)
  return item.id
}

export function removeNotification(id) {
  toastState.items = toastState.items.filter((item) => item.id !== id)
}

export function notifyAppError(error, fallback = 'خطا در انجام عملیات') {
  const normalized = normalizeError(error, fallback)
  return pushNotification(normalized.message, 'error', {
    title: normalized.title || 'خطا در انجام عملیات',
    suggestion: normalized.suggestion || '',
    fields: normalized.fields || [],
    duration: normalized.status >= 500 ? 6400 : 5200,
  })
}

export function markCenterRead(ids = null) {
  const idSet = ids == null ? null : new Set((Array.isArray(ids) ? ids : [ids]).map((item) => String(item)))
  toastState.center = toastState.center.map((item) => {
    if (idSet && !idSet.has(String(item.id))) return item
    return { ...item, read: true }
  })
  persistCenter()
}

export function clearCenter() {
  toastState.center = []
  persistCenter()
}

export function unreadCenterCount() {
  return toastState.center.filter((item) => !item.read).length
}

export const notifySuccess = (message, options = {}) => pushNotification(message, 'success', options)
export const notifyError = (message, options = {}) => pushNotification(message, 'error', options)
export const notifyWarning = (message, options = {}) => pushNotification(message, 'warning', options)
export const notifyInfo = (message, options = {}) => pushNotification(message, 'info', options)
