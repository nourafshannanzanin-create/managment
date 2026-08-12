const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'

export function toPersianDigits(value) {
  return String(value ?? '').replace(/\d/g, (digit) => PERSIAN_DIGITS[Number(digit)] || digit)
}

export function formatDurationFa(totalMinutes, { empty = '—', persianDigits = true } = {}) {
  const total = Math.max(0, Math.round(Number(totalMinutes) || 0))
  if (!total) {
    const zero = '0 دقیقه'
    return persianDigits ? toPersianDigits(zero) : zero
  }

  const hours = Math.floor(total / 60)
  const minutes = total % 60
  let label = ''
  if (hours && minutes) label = `${hours} ساعت و ${minutes} دقیقه`
  else if (hours) label = hours === 1 ? '1 ساعت' : `${hours} ساعت`
  else label = minutes === 1 ? '1 دقیقه' : `${minutes} دقیقه`

  return persianDigits ? toPersianDigits(label) : label
}

export function formatDurationRatioFa(usedMinutes, totalMinutes, { persianDigits = true } = {}) {
  const used = formatDurationFa(usedMinutes, { persianDigits })
  const total = formatDurationFa(totalMinutes, { persianDigits })
  return `${used} از ${total}`
}

export function padTimePart(value) {
  return String(Math.max(0, Number(value) || 0)).padStart(2, '0')
}

export function parseTimeValue(value, fallback = '17:00') {
  const text = String(value || '').trim()
  const match = text.match(/^(\d{1,2}):(\d{2})$/)
  if (!match) return fallback
  const hours = Math.min(23, Math.max(0, Number(match[1])))
  const minutes = Math.min(59, Math.max(0, Number(match[2])))
  return `${padTimePart(hours)}:${padTimePart(minutes)}`
}

export function formatTimeDisplay(value, { persianDigits = true } = {}) {
  const parsed = parseTimeValue(value, '')
  if (!parsed) return 'انتخاب ساعت'
  return persianDigits ? toPersianDigits(parsed) : parsed
}
