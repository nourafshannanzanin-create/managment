const FIELD_LABELS = {
  title: 'عنوان',
  description: 'توضیحات',
  manager: 'ارجاع گیرنده',
  managerAssigneeIds: 'مدیران ارجاعی',
  employeeAssigneeIds: 'کارمندان ارجاعی',
  amount: 'مبلغ',
  expenseDate: 'تاریخ هزینه',
  fullName: 'نام کامل',
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
  [/نام کامل|نام کاربر/, 'fullName'],
  [/ایمیل/, 'email'],
  [/رمز عبور/, 'password'],
  [/فایل|پیوست|سند/, 'file'],
  [/امضا/, 'signatureData'],
  [/سازمان|مجموعه/, 'organizationName'],
]

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
  return FIELD_PATTERNS
    .filter(([pattern]) => pattern.test(message))
    .map(([, field]) => ({
      field,
      label: FIELD_LABELS[field] || field,
      message,
    }))
}

function titleForStatus(status) {
  if (status === 401) return 'نیاز به ورود مجدد'
  if (status === 403) return 'دسترسی کافی نیست'
  if (status === 404) return 'موردی پیدا نشد'
  if (status === 409) return 'تداخل در اطلاعات'
  if (status === 422) return 'اطلاعات فرم نیاز به اصلاح دارد'
  if (status >= 500) return 'خطای داخلی سامانه'
  return 'خطا در انجام عملیات'
}

function suggestionForStatus(status, fields = []) {
  if (fields.length) return 'فیلدهای مشخص شده را اصلاح کنید و دوباره ثبت کنید.'
  if (status === 401) return 'دوباره وارد سامانه شوید.'
  if (status === 403) return 'اگر این دسترسی لازم است، از مدیر سامانه درخواست دسترسی کنید.'
  if (status === 404) return 'صفحه را تازه سازی کنید و دوباره تلاش کنید.'
  if (status === 409) return 'اطلاعات تکراری یا وضعیت قبلی را بررسی کنید.'
  if (status >= 500) return 'چند لحظه بعد دوباره تلاش کنید؛ اگر تکرار شد با پشتیبانی تماس بگیرید.'
  return 'اطلاعات وارد شده را بررسی کنید و دوباره تلاش کنید.'
}

export class AppError extends Error {
  constructor({ message, title = '', status = 0, fields = [], suggestion = '', payload = null } = {}) {
    super(message || 'خطا در انجام عملیات')
    this.name = 'AppError'
    this.title = title || titleForStatus(status)
    this.status = status
    this.fields = normalizeFieldErrors(fields)
    this.suggestion = suggestion || suggestionForStatus(status, this.fields)
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
  const fields = normalizeFieldErrors(error?.fields || inferFields(message))
  return new AppError({
    title: error?.title || titleForStatus(status),
    message,
    status,
    fields,
    suggestion: error?.suggestion || suggestionForStatus(status, fields),
    payload: error?.payload || null,
  })
}

export function appErrorFromResponse(payload = {}, status = 0, fallback = '') {
  const detail = payload.detail || payload.message || fallback || `Request failed: ${status}`
  const fields = normalizeFieldErrors(payload.fields || payload.errors || inferFields(detail))
  return new AppError({
    title: payload.title || titleForStatus(status),
    message: detail,
    status,
    fields,
    suggestion: payload.suggestion || suggestionForStatus(status, fields),
    payload,
  })
}

export function hasFieldError(error, field) {
  return Boolean(error?.fields?.some((item) => item.field === field))
}
