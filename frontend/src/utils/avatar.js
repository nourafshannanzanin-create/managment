const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const MEDIA_URL = String(import.meta.env.VITE_MEDIA_URL || '/uploads/').trim() || '/uploads/'

function normalizeMediaPrefix() {
  let media = MEDIA_URL
  if (!media.startsWith('/')) media = `/${media}`
  if (!media.endsWith('/')) media = `${media}/`
  return media
}

export function resolveApiOrigin() {
  const base = String(API_BASE_URL || '').trim()
  if (!base || base.startsWith('/')) {
    if (typeof window !== 'undefined' && window.location?.origin) {
      return window.location.origin
    }
    return ''
  }
  try {
    return new URL(base).origin
  } catch {
    return base.replace(/\/api\/v1\/?$/, '')
  }
}

/** Resolve any avatar field shape to a browser-loadable URL. */
export function resolveAvatarUrl(...candidates) {
  const origin = resolveApiOrigin()
  const mediaPrefix = normalizeMediaPrefix()

  for (const candidate of candidates) {
    const raw = String(candidate || '').trim()
    if (!raw) continue
    if (/^https?:\/\//i.test(raw) || raw.startsWith('data:') || raw.startsWith('blob:')) return raw

    let path = raw.replace(/\\/g, '/')
    if (path.startsWith('/')) {
      return origin ? `${origin}${path}` : path
    }
    if (path.startsWith('uploads/')) path = path.slice('uploads/'.length)
    if (path.startsWith('media/')) path = path.slice('media/'.length)
    const absolutePath = `${mediaPrefix}${path.replace(/^\/+/, '')}`
    return origin ? `${origin}${absolutePath}` : absolutePath
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
