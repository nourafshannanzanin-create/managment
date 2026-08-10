const DIGIT_MAP = {
  '۰': '0',
  '۱': '1',
  '۲': '2',
  '۳': '3',
  '۴': '4',
  '۵': '5',
  '۶': '6',
  '۷': '7',
  '۸': '8',
  '۹': '9',
  '٠': '0',
  '١': '1',
  '٢': '2',
  '٣': '3',
  '٤': '4',
  '٥': '5',
  '٦': '6',
  '٧': '7',
  '٨': '8',
  '٩': '9',
}

function normalizeDigits(value) {
  return String(value ?? '').replace(/[۰-۹٠-٩]/g, (digit) => DIGIT_MAP[digit] || digit)
}

/** Keep whole-number toman amounts only (no decimals). */
export function normalizeAmountValue(value) {
  const normalized = normalizeDigits(value)
    .replace(/[٬،,\s]/g, '')
    .replace(/[٫.]/g, '')
    .replace(/[^\d]/g, '')
  return normalized.replace(/^0+(?=\d)/, '') || (normalized ? '0' : '')
}

export function formatAmountInput(value) {
  const raw = normalizeAmountValue(value)
  if (!raw) return ''
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(raw))
}

export function formatMoneyDisplay(value) {
  const raw = normalizeAmountValue(value)
  if (!raw) return '0'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(raw))
}
