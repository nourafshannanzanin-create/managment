const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'
const NESHAN_SERVICE_KEY =
  import.meta.env.VITE_NESHAN_SERVICE_KEY || 'service.679d0dde3d6d42a898f33ecc2a3f2fdd'
const NESHAN_REVERSE_URL =
  import.meta.env.VITE_NESHAN_REVERSE_URL || 'https://api.neshan.org/v5/reverse'

function buildFallbackLabel(latitude, longitude, provinceName = '', cityName = '') {
  const parts = [provinceName, cityName].filter(Boolean)
  if (parts.length) return `${parts.join('، ')}، نقطه ثبت‌شده روی نقشه`
  return `نقطه انتخاب‌شده روی نقشه · ${Number(latitude).toFixed(5)}، ${Number(longitude).toFixed(5)}`
}

function normalizeNeshanPayload(payload = {}, source = 'neshan') {
  const formatted =
    payload.formatted_address ||
    payload.formattedAddress ||
    payload.label ||
    payload.address ||
    ''

  return {
    ok: Boolean(formatted) && String(payload.status || 'OK').toUpperCase() !== 'ERROR' && payload.source !== 'fallback',
    status: payload.status || (formatted ? 'OK' : 'FALLBACK'),
    label: formatted,
    formattedAddress: formatted,
    routeName: payload.route_name || payload.routeName || '',
    routeType: payload.route_type || payload.routeType || '',
    neighbourhood: payload.neighbourhood || '',
    city: payload.city || '',
    state: payload.state || '',
    place: payload.place || '',
    municipalityZone: payload.municipality_zone || payload.municipalityZone || '',
    inTrafficZone: Boolean(payload.in_traffic_zone ?? payload.inTrafficZone),
    inOddEvenZone: Boolean(payload.in_odd_even_zone ?? payload.inOddEvenZone),
    village: payload.village || '',
    county: payload.county || '',
    district: payload.district || '',
    source,
    warning: payload.warning || '',
    raw: payload.raw || payload,
  }
}

async function reverseViaNeshanDirect(latitude, longitude) {
  const url = `${NESHAN_REVERSE_URL}?lat=${encodeURIComponent(latitude)}&lng=${encodeURIComponent(longitude)}`
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Api-Key': NESHAN_SERVICE_KEY,
      Accept: 'application/json',
    },
  })

  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(payload.message || payload.detail || `خطای نشان (${response.status})`)
    error.code = payload.code || response.status
    error.payload = payload
    throw error
  }
  if (String(payload.status || '').toUpperCase() === 'ERROR') {
    const error = new Error(payload.message || 'سرویس نشان پاسخ خطا داد.')
    error.code = payload.code
    error.payload = payload
    throw error
  }
  return payload
}

async function reverseViaBackend(latitude, longitude) {
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  }
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_BASE_URL}/maps/neshan/reverse`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ latitude, longitude, lat: latitude, lng: longitude }),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(payload.detail || payload.message || 'پروکسی آدرس‌یابی بک‌اند ناموفق بود.')
    error.code = response.status
    error.payload = payload
    throw error
  }
  return payload
}

/**
 * Reverse geocode via Neshan v5.
 * Prefer browser→Neshan direct (domain whitelist), then backend proxy, then local fallback.
 */
export async function reverseGeocodeNeshan(latitude, longitude, options = {}) {
  const { provinceName = '', cityName = '' } = options
  const lat = Number(latitude)
  const lng = Number(longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    throw new Error('مختصات برای تبدیل آدرس معتبر نیست.')
  }

  // 1) Direct Neshan from browser — works when domain is whitelisted in Neshan panel
  try {
    const direct = await reverseViaNeshanDirect(lat, lng)
    const normalized = normalizeNeshanPayload(direct, 'neshan-direct')
    if (normalized.label) return normalized
  } catch (directError) {
    // continue to backend / fallback
    if (import.meta.env.DEV) {
      console.warn('[neshan] direct reverse failed:', directError?.message || directError)
    }
  }

  // 2) Backend proxy — useful when server IP is also allowed
  try {
    const proxied = await reverseViaBackend(lat, lng)
    const normalized = normalizeNeshanPayload(proxied, proxied.source === 'neshan' ? 'neshan-backend' : 'fallback')
    if (normalized.ok && normalized.label) return normalized
  } catch (backendError) {
    if (import.meta.env.DEV) {
      console.warn('[neshan] backend reverse failed:', backendError?.message || backendError)
    }
  }

  // 3) Local synthetic label — never break map UX
  const fallbackLabel = buildFallbackLabel(lat, lng, provinceName, cityName)
  return normalizeNeshanPayload(
    {
      status: 'FALLBACK',
      formatted_address: fallbackLabel,
      source: 'fallback',
    },
    'fallback',
  )
}

export function neshanAddressSummary(result) {
  if (!result) return ''
  if (result.label) return result.label
  return [result.state, result.city, result.neighbourhood, result.routeName].filter(Boolean).join('، ')
}
