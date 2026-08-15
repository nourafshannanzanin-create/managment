const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '')

/** Resolve any avatar field shape to an absolute URL the browser can load. */
export function resolveAvatarUrl(...candidates) {
  for (const candidate of candidates) {
    const raw = String(candidate || '').trim()
    if (!raw) continue
    if (/^https?:\/\//i.test(raw) || raw.startsWith('data:') || raw.startsWith('blob:')) return raw
    if (raw.startsWith('/')) return `${API_ORIGIN}${raw}`
    if (raw.startsWith('media/')) return `${API_ORIGIN}/${raw}`
    return `${API_ORIGIN}/media/${raw.replace(/^\/+/, '')}`
  }
  return ''
}

/** Pick a photo URL from a person/user payload. */
export function personAvatarUrl(person) {
  if (!person || typeof person !== 'object') return ''
  return resolveAvatarUrl(
    person.avatarUrl,
    person.avatar_url,
    person.avatarImage,
    person.avatar_image,
  )
}
