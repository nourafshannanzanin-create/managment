import { reactive } from 'vue'

let nextId = 1

export const toastState = reactive({
  items: [],
})

function normalizeDuration(value, fallback = 4200) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric <= 0) return fallback
  return numeric
}

export function pushNotification(message, type = 'info', options = {}) {
  const text = String(message || '').trim()
  if (!text) return null
  const item = {
    id: nextId += 1,
    type,
    message: text,
    title: String(options.title || '').trim(),
    duration: normalizeDuration(options.duration, type === 'error' ? 4800 : 3200),
  }
  toastState.items.push(item)
  window.setTimeout(() => removeNotification(item.id), item.duration)
  return item.id
}

export function removeNotification(id) {
  toastState.items = toastState.items.filter((item) => item.id !== id)
}

export const notifySuccess = (message, options = {}) => pushNotification(message, 'success', options)
export const notifyError = (message, options = {}) => pushNotification(message, 'error', options)
export const notifyWarning = (message, options = {}) => pushNotification(message, 'warning', options)
export const notifyInfo = (message, options = {}) => pushNotification(message, 'info', options)
