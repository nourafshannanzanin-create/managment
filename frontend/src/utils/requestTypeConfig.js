export const REQUEST_TYPE_OPTIONS = [
  { value: 'general', label: 'عمومی', icon: 'assignment' },
  { value: 'work_report', label: 'گزارش کار', icon: 'description' },
  { value: 'leave_hourly', label: 'مرخصی ساعتی', icon: 'schedule' },
  { value: 'leave_daily', label: 'مرخصی روزانه', icon: 'event' },
  { value: 'mission', label: 'مأموریت', icon: 'flight_takeoff' },
  { value: 'overtime', label: 'اضافه‌کار', icon: 'more_time' },
  { value: 'remote', label: 'دورکاری', icon: 'home_work' },
  { value: 'purchase', label: 'خرید/تدارکات', icon: 'shopping_cart' },
]

const TYPE_CONFIG = {
  general: {
    titleDefault: '',
    descriptionLabel: 'توضیحات',
    descriptionPlaceholder: 'شرح درخواست را بنویسید...',
    showDeadline: true,
    deadlineLabel: 'تاریخ',
    attachmentHint: 'اختیاری — حداکثر ۸ مگابایت',
    summaryTitle: 'خلاصه درخواست',
  },
  work_report: {
    titleDefault: 'گزارش کار',
    descriptionLabel: 'شرح فعالیت‌ها',
    descriptionPlaceholder: 'کارهای انجام‌شده، دستاوردها و نتایج دوره را بنویسید...',
    showDeadline: false,
    showPeriod: true,
    periodStartLabel: 'از تاریخ گزارش',
    periodEndLabel: 'تا تاریخ گزارش',
    attachmentHint: 'فایل گزارش یا مستندات کار — توصیه می‌شود',
    summaryTitle: 'خلاصه گزارش کار',
    requiresDescription: true,
  },
  leave_hourly: {
    titleDefault: 'مرخصی ساعتی',
    descriptionLabel: 'توضیحات',
    descriptionPlaceholder: 'در صورت نیاز توضیح تکمیلی بنویسید...',
    showDeadline: false,
    attachmentHint: 'اختیاری — حداکثر ۸ مگابایت',
    summaryTitle: 'خلاصه مرخصی',
  },
  leave_daily: {
    titleDefault: 'مرخصی روزانه',
    descriptionLabel: 'توضیحات',
    descriptionPlaceholder: 'در صورت نیاز توضیح تکمیلی بنویسید...',
    showDeadline: false,
    attachmentHint: 'اختیاری — حداکثر ۸ مگابایت',
    summaryTitle: 'خلاصه مرخصی',
  },
  mission: {
    titleDefault: 'مأموریت',
    descriptionLabel: 'هدف مأموریت',
    descriptionPlaceholder: 'محل، هدف و جزئیات مأموریت را بنویسید...',
    showDeadline: false,
    showPeriod: true,
    periodStartLabel: 'شروع مأموریت',
    periodEndLabel: 'پایان مأموریت',
    showLocation: true,
    locationLabel: 'محل / مقصد',
    attachmentHint: 'مدارک مرتبط با مأموریت — اختیاری',
    summaryTitle: 'خلاصه مأموریت',
  },
  overtime: {
    titleDefault: 'اضافه‌کار',
    descriptionLabel: 'دلیل اضافه‌کار',
    descriptionPlaceholder: 'علت و کار انجام‌شده در اضافه‌کار را بنویسید...',
    showDeadline: false,
    showOvertime: true,
    attachmentHint: 'اختیاری — حداکثر ۸ مگابایت',
    summaryTitle: 'خلاصه اضافه‌کار',
  },
  remote: {
    titleDefault: 'دورکاری',
    descriptionLabel: 'توضیحات',
    descriptionPlaceholder: 'برنامه کاری و دلیل دورکاری را بنویسید...',
    showDeadline: false,
    showPeriod: true,
    periodStartLabel: 'از تاریخ',
    periodEndLabel: 'تا تاریخ',
    attachmentHint: 'اختیاری — حداکثر ۸ مگابایت',
    summaryTitle: 'خلاصه دورکاری',
  },
  purchase: {
    titleDefault: 'درخواست خرید',
    descriptionLabel: 'توضیحات تکمیلی',
    descriptionPlaceholder: 'جزئیات بیشتر درباره خرید یا تدارکات...',
    showDeadline: true,
    deadlineLabel: 'مهلت نیاز',
    showPurchase: true,
    attachmentHint: 'پیش‌فاکتور یا مشخصات کالا — توصیه می‌شود',
    summaryTitle: 'خلاصه خرید',
  },
}

export function requestTypeConfig(type) {
  return TYPE_CONFIG[type] || TYPE_CONFIG.general
}

export function buildRequestTypePayload(form) {
  const type = form.requestType || 'general'
  if (type === 'work_report' || type === 'mission' || type === 'remote') {
    return {
      periodStartDate: form.periodStartDate || '',
      periodEndDate: form.periodEndDate || '',
      location: form.location || '',
    }
  }
  if (type === 'overtime') {
    return {
      overtimeDate: form.overtimeDate || '',
      startTime: form.overtimeStartTime || '',
      endTime: form.overtimeEndTime || '',
    }
  }
  if (type === 'purchase') {
    return {
      purchaseItem: form.purchaseItem || '',
      estimatedAmount: form.estimatedAmount || '',
    }
  }
  return {}
}

export function typePayloadSummaryRows(type, payload = {}) {
  const rows = []
  if (!payload || typeof payload !== 'object') return rows

  if (payload.periodStartDate) rows.push({ label: 'از تاریخ', value: payload.periodStartDate })
  if (payload.periodEndDate) rows.push({ label: 'تا تاریخ', value: payload.periodEndDate })
  if (payload.location) rows.push({ label: 'محل / مقصد', value: payload.location })
  if (payload.overtimeDate) rows.push({ label: 'تاریخ', value: payload.overtimeDate })
  if (payload.startTime) rows.push({ label: 'از ساعت', value: payload.startTime })
  if (payload.endTime) rows.push({ label: 'تا ساعت', value: payload.endTime })
  if (payload.purchaseItem) rows.push({ label: 'کالا / خدمت', value: payload.purchaseItem })
  if (payload.estimatedAmount) rows.push({ label: 'مبلغ تقریبی', value: payload.estimatedAmount })

  return rows
}

export function defaultTitleForRequestType(type) {
  return requestTypeConfig(type).titleDefault || ''
}
