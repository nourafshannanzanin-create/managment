import { ostan, shahr } from 'iran-cities-json'

const IRAN_CENTER = {
  latitude: 32.4279,
  longitude: 53.688,
  zoom: 5,
}

const provinceCenters = {
  1: { latitude: 38.08, longitude: 46.29, zoom: 10 },
  2: { latitude: 37.55, longitude: 45.07, zoom: 10 },
  3: { latitude: 38.25, longitude: 48.29, zoom: 10 },
  4: { latitude: 32.65, longitude: 51.67, zoom: 10 },
  5: { latitude: 35.84, longitude: 50.94, zoom: 10 },
  6: { latitude: 33.64, longitude: 46.42, zoom: 10 },
  7: { latitude: 28.92, longitude: 50.84, zoom: 10 },
  8: { latitude: 35.69, longitude: 51.39, zoom: 11 },
  9: { latitude: 32.33, longitude: 50.86, zoom: 10 },
  10: { latitude: 32.86, longitude: 59.22, zoom: 10 },
  11: { latitude: 36.3, longitude: 59.6, zoom: 10 },
  12: { latitude: 37.47, longitude: 57.33, zoom: 10 },
  13: { latitude: 31.32, longitude: 48.68, zoom: 10 },
  14: { latitude: 36.68, longitude: 48.49, zoom: 10 },
  15: { latitude: 35.57, longitude: 53.39, zoom: 10 },
  16: { latitude: 29.5, longitude: 60.86, zoom: 10 },
  17: { latitude: 29.59, longitude: 52.58, zoom: 10 },
  18: { latitude: 36.27, longitude: 50.0, zoom: 10 },
  19: { latitude: 34.64, longitude: 50.88, zoom: 11 },
  20: { latitude: 35.31, longitude: 46.99, zoom: 10 },
  21: { latitude: 30.28, longitude: 57.08, zoom: 10 },
  22: { latitude: 34.31, longitude: 47.07, zoom: 10 },
  23: { latitude: 30.67, longitude: 51.59, zoom: 10 },
  24: { latitude: 36.84, longitude: 54.43, zoom: 10 },
  25: { latitude: 37.28, longitude: 49.59, zoom: 10 },
  26: { latitude: 33.49, longitude: 48.35, zoom: 10 },
  27: { latitude: 36.56, longitude: 53.06, zoom: 10 },
  28: { latitude: 34.09, longitude: 49.69, zoom: 10 },
  29: { latitude: 27.19, longitude: 56.28, zoom: 10 },
  30: { latitude: 34.8, longitude: 48.51, zoom: 10 },
  31: { latitude: 31.9, longitude: 54.36, zoom: 10 },
}

const cityCenterOverrides = {
  '1:تبریز': { latitude: 38.08, longitude: 46.29, zoom: 12 },
  '2:ارومیه': { latitude: 37.55, longitude: 45.07, zoom: 12 },
  '3:اردبیل': { latitude: 38.25, longitude: 48.29, zoom: 12 },
  '4:اصفهان': { latitude: 32.65, longitude: 51.67, zoom: 12 },
  '5:کرج': { latitude: 35.84, longitude: 50.94, zoom: 12 },
  '7:بوشهر': { latitude: 28.92, longitude: 50.84, zoom: 12 },
  '8:تهران': { latitude: 35.6892, longitude: 51.389, zoom: 12 },
  '8:اسلامشهر': { latitude: 35.56, longitude: 51.23, zoom: 12 },
  '8:پردیس': { latitude: 35.74, longitude: 51.82, zoom: 12 },
  '8:پاکدشت': { latitude: 35.48, longitude: 51.68, zoom: 12 },
  '8:ورامین': { latitude: 35.32, longitude: 51.65, zoom: 12 },
  '8:شهریار': { latitude: 35.66, longitude: 51.06, zoom: 12 },
  '11:مشهد': { latitude: 36.3, longitude: 59.6, zoom: 12 },
  '13:اهواز': { latitude: 31.32, longitude: 48.68, zoom: 12 },
  '17:شیراز': { latitude: 29.59, longitude: 52.58, zoom: 12 },
  '19:قم': { latitude: 34.64, longitude: 50.88, zoom: 12 },
  '21:کرمان': { latitude: 30.28, longitude: 57.08, zoom: 12 },
  '22:کرمانشاه': { latitude: 34.31, longitude: 47.07, zoom: 12 },
  '24:گرگان': { latitude: 36.84, longitude: 54.43, zoom: 12 },
  '25:رشت': { latitude: 37.28, longitude: 49.59, zoom: 12 },
  '27:ساری': { latitude: 36.56, longitude: 53.06, zoom: 12 },
  '29:بندرعباس': { latitude: 27.19, longitude: 56.28, zoom: 12 },
  '30:همدان': { latitude: 34.8, longitude: 48.51, zoom: 12 },
  '31:یزد': { latitude: 31.9, longitude: 54.36, zoom: 12 },
}

export const provinces = [...ostan].sort((a, b) => a.name.localeCompare(b.name, 'fa'))

export const cities = shahr
  .map((city) => ({
    id: city.id,
    name: city.name,
    provinceId: city.ostan,
  }))
  .sort((a, b) => a.name.localeCompare(b.name, 'fa'))

export const getCitiesByProvinceId = (provinceId) =>
  cities.filter((city) => city.provinceId === Number(provinceId))

export const getProvinceMapCenter = (provinceId) =>
  provinceCenters[Number(provinceId)] || IRAN_CENTER

export const getCityMapCenter = (cityId) => {
  const city = cities.find((item) => item.id === Number(cityId))
  if (!city) return IRAN_CENTER
  return cityCenterOverrides[`${city.provinceId}:${city.name}`] || getProvinceMapCenter(city.provinceId)
}

export const getCityMapCenterByName = (provinceName, cityName) => {
  const province = provinces.find((item) => item.name === String(provinceName || '').trim())
  if (!province) return IRAN_CENTER
  const city = getCitiesByProvinceId(province.id).find((item) => item.name === String(cityName || '').trim())
  if (city) return getCityMapCenter(city.id)
  return getProvinceMapCenter(province.id)
}

export const resolveMapCenter = ({
  latitude = null,
  longitude = null,
  cityId = null,
  provinceId = null,
  cityName = '',
  provinceName = '',
  zoom = 15,
} = {}) => {
  const lat = Number(latitude)
  const lng = Number(longitude)
  if (Number.isFinite(lat) && Number.isFinite(lng) && lat >= 20 && lat <= 42 && lng >= 40 && lng <= 66) {
    return { latitude: lat, longitude: lng, zoom }
  }
  if (cityId) return getCityMapCenter(cityId)
  if (provinceId) return getProvinceMapCenter(provinceId)
  if (cityName || provinceName) return getCityMapCenterByName(provinceName, cityName)
  return IRAN_CENTER
}

export const getIranMapCenter = () => IRAN_CENTER
