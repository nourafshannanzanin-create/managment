const FIELD_LABELS = {
  title: 'عنوان',
  description: 'توضیحات',
  manager: 'ارجاع گیرنده',
  managerAssigneeIds: 'مدیران ارجاعی',
  employeeAssigneeIds: 'کارمندان ارجاعی',
  amount: 'مبلغ',
  expenseDate: 'تاریخ هزینه',
  fullName: 'نام کامل',
  username: 'نام کاربری',
  email: 'ایمیل',
  password: 'رمز عبور',
  file: 'فایل',
  assigneeIds: 'دریافت کننده',
  signatureData: 'امضا',
  organizationName: 'نام سازمان',
}

const FIELD_PATTERNS = [
  [/عنوان/, 'title'],
  [/شرح|توضیح/, 'description'],
  [/مدیر|ارجاع|گیرنده/, 'manager'],
  [/مبلغ|هزینه/, 'amount'],
  [/نام کامل|نام و نام خانوادگی/, 'fullName'],
  [/نام کاربری|username/i, 'username'],
  [/ایمیل/, 'email'],
  [/رمز عبور/, 'password'],
  [/فایل|پیوست|سند/, 'file'],
  [/امضا/, 'signatureData'],
  [/سازمان|مجموعه/, 'organizationName'],
]

const AUTH_CREDENTIAL_RE =
  /نام کاربری\s*\/\s*ایمیل یا رمز عبور نادرست|رمز عبور نادرست|ورود ناموفق|اطلاعات ورود نادرست/

function isAuthCredentialMessage(message = '') {
  return AUTH_CREDENTIAL_RE.test(String(message || ''))
}

function normalizeFieldErrors(rawFields = {}) {
  if (Array.isArray(rawFields)) {
    return rawFields.map((item) => ({
      field: item.field || item.key || '',
      label: item.label || FIELD_LABELS[item.field || item.key] || item.field || item.key || 'فیلد',
      message: item.message || item.detail || 'این مقدار را بررسی کنید.',
    }))
  }

  return Object.entries(rawFields || {}).map(([field, value]) => ({
    field,
    label: FIELD_LABELS[field] || field,
    message: Array.isArray(value) ? value.join('، ') : String(value || 'این مقدار را بررسی کنید.'),
  }))
}

function inferFields(message = '') {
  const text = String(message || '')
  if (!text || isAuthCredentialMessage(text)) return []

  return FIELD_PATTERNS
    .filter(([pattern]) => pattern.test(text))
    .map(([, field]) => ({
      field,
      label: FIELD_LABELS[field] || field,
      message: text,
    }))
}

function titleForStatus(status, message = '') {
  if (status === 401) {
    if (isAuthCredentialMessage(message)) return 'ورود ناموفق'
    return 'نیاز به ورود مجدد'
  }
  if (status === 403) return 'دسترسی کافی نیست'
  if (status === 404) return 'موردی پیدا نشد'
  if (status === 409) return 'تداخل در اطلاعات'
  if (status === 422) return 'اطلاعات فرم نیاز به اصلاح دارد'
  if (status >= 500) return 'خطای داخلی سامانه'
  return 'خطا در انجام عملیات'
}

function suggestionForStatus(status, fields = [], message = '') {
  if (isAuthCredentialMessage(message) || (status === 401 && !fields.length)) {
    return 'نام کاربری/ایمیل و رمز عبور را بررسی کنید و دوباره تلاش کنید.'
  }
  if (fields.length) return 'فیلدهای مشخص شده را اصلاح کنید و دوباره ثبت کنید.'
  if (status === 401) return 'دوباره وارد سامانه شوید.'
  if (status === 403) return 'اگر این دسترسی لازم است، از مدیر سامانه درخواست دسترسی کنید.'
  if (status === 404) return 'صفحه را تازه سازی کنید و دوباره تلاش کنید.'
  if (status === 409) return 'اطلاعات تکراری یا وضعیت قبلی را بررسی کنید.'
  if (status >= 500) return 'چند لحظه بعد دوباره تلاش کنید؛ اگر تکرار شد با پشتیبانی تماس بگیرید.'
  return 'اطلاعات وارد شده را بررسی کنید و دوباره تلاش کنید.'
}

function resolveFields(payloadFields, message, status) {
  const explicit = normalizeFieldErrors(payloadFields || {})
  if (explicit.length) return explicit
  // Never invent field errors for auth failures / 401 responses.
  if (status === 401 || isAuthCredentialMessage(message)) return []
  return inferFields(message)
}

export class AppError extends Error {
  constructor({ message, title = '', status = 0, fields = [], suggestion = '', payload = null } = {}) {
    super(message || 'خطا در انجام عملیات')
    this.name = 'AppError'
    this.title = title || titleForStatus(status, message)
    this.status = status
    this.fields = normalizeFieldErrors(fields)
    this.suggestion = suggestion || suggestionForStatus(status, this.fields, message)
    this.payload = payload
  }
}

export function createValidationError(message, fields = []) {
  return new AppError({
    status: 422,
    title: 'اطلاعات فرم کامل نیست',
    message,
    fields,
  })
}

export function normalizeError(error, fallback = 'خطا در انجام عملیات') {
  if (error instanceof AppError) return error
  const message = error?.message || fallback
  const status = error?.status || 0
  const fields = resolveFields(error?.fields, message, status)
  return new AppError({
    title: error?.title || titleForStatus(status, message),
    message,
    status,
    fields,
    suggestion: error?.suggestion || suggestionForStatus(status, fields, message),
    payload: error?.payload || null,
  })
}

export function appErrorFromResponse(payload = {}, status = 0, fallback = '') {
  const detail = payload.detail || payload.message || fallback || `Request failed: ${status}`
  const fields = resolveFields(payload.fields || payload.errors, detail, status)
  return new AppError({
    title: payload.title || titleForStatus(status, detail),
    message: detail,
    status,
    fields,
    suggestion: payload.suggestion || suggestionForStatus(status, fields, detail),
    payload,
  })
}

export function hasFieldError(error, field) {
  return Boolean(error?.fields?.some((item) => item.field === field))
}
