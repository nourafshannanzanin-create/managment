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

export function normalizeAmountValue(value) {
  const normalized = normalizeDigits(value)
    .replace(/[٬،,\s]/g, '')
    .replace(/[٫]/g, '.')
    .replace(/[^\d.]/g, '')
  const [integerPart = '', ...decimalParts] = normalized.split('.')
  const decimals = decimalParts.join('').slice(0, 2)
  return decimals ? `${integerPart || '0'}.${decimals}` : integerPart
}

export function formatAmountInput(value) {
  const normalized = normalizeDigits(value)
  const hasTrailingDecimal = /[.٫]$/.test(normalized)
  const raw = normalizeAmountValue(normalized)
  if (!raw) return ''
  const [integerPart, decimalPart] = raw.split('.')
  const grouped = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(integerPart || 0))
  if (hasTrailingDecimal && decimalPart === undefined) return `${grouped}.`
  return decimalPart !== undefined ? `${grouped}.${decimalPart}` : grouped
}
