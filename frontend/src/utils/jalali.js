const PERSIAN_MONTHS = [
  'فروردین',
  'اردیبهشت',
  'خرداد',
  'تیر',
  'مرداد',
  'شهریور',
  'مهر',
  'آبان',
  'آذر',
  'دی',
  'بهمن',
  'اسفند',
]

const PERSIAN_WEEKDAYS = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']

function div(a, b) {
  return Math.floor(a / b)
}

export function normalizeDigits(value) {
  return String(value || '')
    .replace(/[۰-۹]/g, (digit) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(digit)))
}

export function pad(value) {
  return String(value).padStart(2, '0')
}

export function gregorianToJalali(gy, gm, gd) {
  const gdm = [0, 31, (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  let jy
  if (gy > 1600) {
    jy = 979
    gy -= 1600
  } else {
    jy = 0
    gy -= 621
  }

  let gy2 = gm > 2 ? gy + 1 : gy
  let days =
    365 * gy +
    div(gy2 + 3, 4) -
    div(gy2 + 99, 100) +
    div(gy2 + 399, 400) -
    80 +
    gd

  for (let i = 0; i < gm; i += 1) {
    days += gdm[i]
  }

  jy += 33 * div(days, 12053)
  days %= 12053
  jy += 4 * div(days, 1461)
  days %= 1461

  if (days > 365) {
    jy += div(days - 1, 365)
    days = (days - 1) % 365
  }

  const jm = days < 186 ? 1 + div(days, 31) : 7 + div(days - 186, 30)
  const jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30)
  return { jy, jm, jd }
}

export function jalaliToGregorian(jy, jm, jd) {
  let gy
  if (jy > 979) {
    gy = 1600
    jy -= 979
  } else {
    gy = 621
  }

  let days =
    365 * jy +
    div(jy, 33) * 8 +
    div((jy % 33) + 3, 4) +
    78 +
    jd +
    (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186)

  gy += 400 * div(days, 146097)
  days %= 146097

  if (days > 36524) {
    gy += 100 * div(--days, 36524)
    days %= 36524
    if (days >= 365) days += 1
  }

  gy += 4 * div(days, 1461)
  days %= 1461

  if (days > 365) {
    gy += div(days - 1, 365)
    days = (days - 1) % 365
  }

  let gd = days + 1
  const salA = [0, 31, (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  let gm = 0
  for (gm = 1; gm <= 12 && gd > salA[gm]; gm += 1) {
    gd -= salA[gm]
  }

  return { gy, gm, gd }
}

export function formatJalaliSlash({ jy, jm, jd }) {
  return `${pad(jd)} / ${pad(jm)} / ${jy}`
}

export function formatJalali({ jy, jm, jd }) {
  return `${jy}/${pad(jm)}/${pad(jd)}`
}

export function formatGregorianIso({ gy, gm, gd }) {
  return `${gy}-${pad(gm)}-${pad(gd)}`
}

export function parseJalali(value) {
  const normalized = normalizeDigits(value).trim()
  const match = normalized.match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/)
  if (!match) return null

  const jy = Number(match[1])
  const jm = Number(match[2])
  const jd = Number(match[3])
  if (jm < 1 || jm > 12) return null
  const maxDay = getJalaliMonthLength(jy, jm)
  if (jd < 1 || jd > maxDay) return null
  return { jy, jm, jd }
}

export function jalaliToIso(value) {
  const parsed = typeof value === 'string' ? parseJalali(value) : value
  if (!parsed) return ''
  return formatGregorianIso(jalaliToGregorian(parsed.jy, parsed.jm, parsed.jd))
}

export function isoToJalali(value) {
  const normalized = normalizeDigits(value).trim()
  const match = normalized.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) return ''
  return formatJalali(gregorianToJalali(Number(match[1]), Number(match[2]), Number(match[3])))
}

export function getTodayJalali() {
  const now = new Date()
  return gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate())
}

export function getJalaliMonthLength(jy, jm) {
  if (jm <= 6) return 31
  if (jm <= 11) return 30
  return isJalaliLeapYear(jy) ? 30 : 29
}

export function isJalaliLeapYear(jy) {
  const { gy, gm, gd } = jalaliToGregorian(jy + 1, 1, 1)
  const nextYearStart = new Date(gy, gm - 1, gd)
  nextYearStart.setDate(nextYearStart.getDate() - 1)
  const lastDay = gregorianToJalali(nextYearStart.getFullYear(), nextYearStart.getMonth() + 1, nextYearStart.getDate())
  return lastDay.jd === 30
}

export function getJalaliMonthLabel(jy, jm) {
  return `${PERSIAN_MONTHS[jm - 1]} ${jy}`
}

export function getPersianWeekdays() {
  return PERSIAN_WEEKDAYS
}

export function getMonthMatrix(jy, jm) {
  const daysInMonth = getJalaliMonthLength(jy, jm)
  const firstGregorian = jalaliToGregorian(jy, jm, 1)
  const firstDayOfWeek = new Date(firstGregorian.gy, firstGregorian.gm - 1, firstGregorian.gd).getDay()
  const offset = (firstDayOfWeek + 1) % 7
  const cells = []

  for (let i = 0; i < offset; i += 1) {
    cells.push(null)
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push({
      day,
      jalali: { jy, jm, jd: day },
      iso: formatGregorianIso(jalaliToGregorian(jy, jm, day)),
      formatted: formatJalali({ jy, jm, jd: day }),
    })
  }

  while (cells.length % 7 !== 0) {
    cells.push(null)
  }

  const weeks = []
  for (let i = 0; i < cells.length; i += 7) {
    weeks.push(cells.slice(i, i + 7))
  }
  return weeks
}

export function shiftJalaliMonth(jy, jm, delta) {
  let month = jm + delta
  let year = jy

  while (month > 12) {
    month -= 12
    year += 1
  }

  while (month < 1) {
    month += 12
    year -= 1
  }

  return { jy: year, jm: month }
}
