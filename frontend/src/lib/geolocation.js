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

/**
 * iOS Safari: high-accuracy first requests often hang or never prompt unless
 * triggered by a user gesture. Prefer a quick low-accuracy/cached read, then refine.
 */
export async function readDeviceLocation(options = {}) {
  const {
    enableHighAccuracy = null,
    timeout = 18000,
    maximumAge = 60000,
    allowQuickFallback = true,
  } = options

  if (typeof navigator !== 'undefined' && navigator.permissions?.query) {
    try {
      const status = await navigator.permissions.query({ name: 'geolocation' })
      if (status.state === 'denied') {
        throw mapGeolocationError({ code: 1 })
      }
    } catch (error) {
      // Safari may not support Permissions API for geolocation; ignore query failures.
      if (error?.code === 1) throw error
    }
  }

  if (enableHighAccuracy === true || enableHighAccuracy === false) {
    return getCurrentPositionOnce({ enableHighAccuracy, timeout, maximumAge })
  }

  if (!allowQuickFallback) {
    return getCurrentPositionOnce({ enableHighAccuracy: true, timeout, maximumAge: 0 })
  }

  try {
    // Fast path that usually triggers the iOS prompt reliably.
    return await getCurrentPositionOnce({
      enableHighAccuracy: false,
      timeout: Math.min(timeout, 12000),
      maximumAge,
    })
  } catch (error) {
    if (Number(error?.code) === 1) throw error
    return getCurrentPositionOnce({
      enableHighAccuracy: true,
      timeout: Math.max(timeout, 20000),
      maximumAge: 0,
    })
  }
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
