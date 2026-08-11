export function readDeviceLocation(options = {}) {
  const {
    enableHighAccuracy = true,
    timeout = 20000,
    maximumAge = 0,
  } = options

  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('مرورگر شما از موقعیت مکانی پشتیبانی نمی‌کند.'))
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
        const messages = {
          1: 'دسترسی به موقعیت مکانی رد شد. لطفاً اجازه دسترسی موقعیت را فعال کنید.',
          2: 'موقعیت مکانی در دسترس نیست.',
          3: 'دریافت موقعیت مکانی بیش از حد طول کشید.',
        }
        reject(new Error(messages[error?.code] || 'دریافت موقعیت مکانی ناموفق بود.'))
      },
      { enableHighAccuracy, timeout, maximumAge },
    )
  })
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
