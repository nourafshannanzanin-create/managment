export function isGeolocationAvailable() {
  return typeof navigator !== 'undefined' && Boolean(navigator.geolocation)
}

export function isSecureGeolocationContext() {
  if (typeof window === 'undefined') return false
  return Boolean(window.isSecureContext)
}

function mapGeolocationError(error) {
  const code = Number(error?.code)
  if (code === 1) {
    return new Error(
      'دسترسی به موقعیت رد شد. در آیفون: Settings → Safari → Location را روی Allow بگذارید، یا از دکمه «اشتراک‌گذاری موقعیت» دوباره اجازه بدهید.',
    )
  }
  if (code === 2) {
    return new Error('موقعیت مکانی در دسترس نیست. Location Services گوشی را روشن کنید.')
  }
  if (code === 3) {
    return new Error('دریافت موقعیت بیش از حد طول کشید. دوباره امتحان کنید.')
  }
  return new Error(error?.message || 'دریافت موقعیت مکانی ناموفق بود.')
}

function getCurrentPositionOnce(options) {
  return new Promise((resolve, reject) => {
    if (!isGeolocationAvailable()) {
      reject(new Error('مرورگر شما از موقعیت مکانی پشتیبانی نمی‌کند.'))
      return
    }
    if (!isSecureGeolocationContext()) {
      reject(new Error('برای دریافت موقعیت باید سایت با HTTPS باز شده باشد.'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          capturedAt: Date.now(),
        })
      },
      (error) => {
        const mapped = mapGeolocationError(error)
        mapped.code = Number(error?.code) || 0
        reject(mapped)
      },
      options,
    )
  })
}

let cachedLocation = null

/**
 * Prefer a quick cached/low-accuracy read. Avoid double high-accuracy prompts.
 */
export async function readDeviceLocation(options = {}) {
  const {
    enableHighAccuracy = false,
    timeout = 10000,
    maximumAge = 120000,
    allowCached = true,
    forceRefresh = false,
  } = options

  if (allowCached && !forceRefresh && cachedLocation?.capturedAt && Date.now() - cachedLocation.capturedAt < maximumAge) {
    return cachedLocation
  }

  const coords = await getCurrentPositionOnce({
    enableHighAccuracy,
    timeout,
    maximumAge,
  })
  cachedLocation = coords
  return coords
}

export function clearCachedLocation() {
  cachedLocation = null
}

export function haversineDistanceMeters(lat1, lon1, lat2, lon2) {
  const toRad = (value) => (value * Math.PI) / 180
  const earth = 6371000
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
  return 2 * earth * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}
