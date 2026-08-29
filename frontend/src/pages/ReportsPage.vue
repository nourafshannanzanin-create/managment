<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import PageHeader from '../components/PageHeader.vue'
import SectionHeading from '../components/SectionHeading.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import AttendancePeriodBoard from '../components/AttendancePeriodBoard.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { formatJalali, formatTehranDateTime, getTodayIso, getTodayJalali, isoToJalali, jalaliMonthStartIso, jalaliToIso, jalaliWeekStartIso, jalaliYearStartIso } from '../utils/jalali'
import { formatDurationFa, toPersianDigits } from '../utils/duration'
import { exportAttendanceReportPdf } from '../utils/attendancePdfExport'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatMoneyWithUnit } from '../utils/amount'
import { joinDisplayParts } from '../utils/text'
import { rowToneForStatus, toneForStatus } from '../utils/status'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'

const { exportReport, loadReports, loadTaskingReports, state, updatePageFilter } = useWorkflowHub()

function formatReportMoney(value) {
  if (value === null || value === undefined || value === '' || value === '-') return '-'
  return formatMoneyWithUnit(value)
}

const activeTab = ref('requests')
const selectedReportRow = ref(null)
const selectedReportType = ref('')
const selectedTaskingPerson = ref(null)
const filters = reactive({ period: 'month', startDate: '', endDate: '', userId: '' })
const attendanceRows = ref([])
const attendanceLoading = ref(false)
const attendanceError = ref('')

const topbarFilter = computed(() => state.filters.reports || { query: '', person: '', startDate: '', endDate: '' })

/** Page person select is the only person filter on reports. */
const effectiveUserId = computed(() => (filters.userId ? String(filters.userId) : ''))

const effectiveUserName = computed(() => {
  if (!filters.userId) return ''
  const matched = (state.users || []).find((user) => String(user.id) === String(filters.userId))
  return matched?.name || ''
})

function matchesTopbar(item, fields = []) {
  const query = String(topbarFilter.value.query || '').trim().toLowerCase()
  if (!query) return true
  const hay = fields.map((key) => String(item?.[key] || '')).join(' ').toLowerCase()
  return hay.includes(query)
}

function selectPeriod(key) {
  filters.period = key
  if (key !== 'custom') {
    filters.startDate = ''
    filters.endDate = ''
  }
}

const canViewAttendanceReports = computed(() =>
  Boolean(
    state.currentUser.isHq ||
    (
      state.currentUser.canAccessAttendance !== false &&
      state.currentUser.menuAccess?.attendance === true &&
      (state.currentUser.isManager || state.currentUser.canViewReports)
    ),
  ),
)

const tabs = computed(() => {
  const items = [
    { key: 'requests', label: 'درخواست‌ها', icon: 'assignment' },
    { key: 'expenses', label: 'هزینه‌ها', icon: 'payments' },
    { key: 'approvals', label: 'تاییدیه‌ها', icon: 'fact_check' },
    { key: 'tasking', label: 'تسکینگ', icon: 'task_alt' },
  ]
  if (canViewAttendanceReports.value) {
    items.push({ key: 'attendance', label: 'ورود و خروج', icon: 'badge' })
  }
  return items
})

const periods = [
  { key: 'today', label: 'امروز' },
  { key: 'week', label: 'این هفته' },
  { key: 'month', label: 'این ماه' },
  { key: 'year', label: 'امسال' },
  { key: 'custom', label: 'دلخواه' },
]

const reportUsers = computed(() => state.users || [])

function periodIsoRange() {
  const todayIso = getTodayIso()
  if (filters.period === 'today') return { start: todayIso, end: todayIso }
  if (filters.period === 'week') return { start: jalaliWeekStartIso(todayIso), end: todayIso }
  if (filters.period === 'month') return { start: jalaliMonthStartIso(todayIso), end: todayIso }
  if (filters.period === 'year') return { start: jalaliYearStartIso(todayIso), end: todayIso }
  if (filters.period === 'custom') {
    return {
      start: filters.startDate ? jalaliToIso(filters.startDate) : '',
      end: filters.endDate ? jalaliToIso(filters.endDate) : '',
    }
  }
  return { start: todayIso, end: todayIso }
}

function rowDate(item) {
  if (activeTab.value === 'requests') return item.createdAtIso || item.deadlineIso || ''
  if (activeTab.value === 'expenses') return item.createdAtIso || ''
  if (activeTab.value === 'users') return item.financeUpdatedAtIso || item.joinedAtIso || ''
  if (activeTab.value === 'attendance') return item.eventDate || ''
  return item.uploadedAtIso || ''
}

function inPeriod(isoDate) {
  if (!isoDate) return activeTab.value === 'users'
  const day = String(isoDate).slice(0, 10)
  const { start, end } = periodIsoRange()
  if (start && day < start) return false
  if (end && day > end) return false
  return true
}

function eventLabel(type) {
  return type === 'in' ? 'ورود' : 'خروج'
}

function sourceLabel(source) {
  return source === 'manager' ? 'ثبت مدیر' : 'لینک پرسنل'
}

function dateTime(value) {
  if (!value) return '-'
  return formatTehranDateTime(value)
}

function attendanceStatus(row) {
  return eventLabel(row.eventType || row.event_type)
}

function rowStatusValue(row) {
  if (activeTab.value === 'attendance') return attendanceStatus(row)
  if (activeTab.value === 'users') return row.status || ''
  return row.status || ''
}

const activeRows = computed(() => {
  if (activeTab.value === 'tasking') {
    const rows = state.tasking.reports?.users || []
    return rows.filter((item) => {
      if (effectiveUserId.value && String(item.user?.id) !== effectiveUserId.value) return false
      return true
    })
  }
  if (activeTab.value === 'attendance') {
    const query = String(topbarFilter.value.query || '').trim().toLowerCase()
    return attendanceRows.value.filter((item) => {
      if (effectiveUserId.value && String(item.userId || item.user_id) !== effectiveUserId.value) return false
      if (effectiveUserName.value) {
        const name = String(item.userName || item.user_name || '')
        if (name !== effectiveUserName.value && !name.includes(effectiveUserName.value)) return false
      }
      if (query) {
        const name = String(item.userName || item.user_name || '')
        const hay = [name, item.userRole, item.userDepartment, item.note, item.eventType, item.event_type].join(' ').toLowerCase()
        if (!hay.includes(query)) return false
      }
      return true
    })
  }
  const rows = activeTab.value === 'requests'
    ? state.requests
    : activeTab.value === 'expenses'
      ? state.expenses
      : activeTab.value === 'users'
        ? state.users
        : state.approvals
  return rows.filter((item) => {
    const userName = effectiveUserName.value
    const matchesUser = !userName || [item.owner, item.manager, item.name].filter(Boolean).includes(userName)
    if (!matchesUser || !inPeriod(rowDate(item))) return false
    return matchesTopbar(item, ['title', 'description', 'owner', 'manager', 'name', 'department', 'status', 'type', 'summary', 'id'])
  })
})

function hoursLabel(minutes) {
  return formatDurationFa(minutes, { empty: '۰ دقیقه' })
}

function taskingSummary(row) {
  const target = Math.max(0, Number(row.targetMinutes || 0))
  const actual = Math.max(0, Number(row.actualMinutes || 0))
  const deficit = Math.max(0, target - actual)
  const overtime = Math.max(0, actual - target)
  let statusKey = 'ok'
  let statusLabel = 'در هدف'
  if (deficit > 0) {
    statusKey = 'deficit'
    statusLabel = 'کسری'
  } else if (overtime > 0) {
    statusKey = 'overtime'
    statusLabel = 'اضافه‌کار'
  }
  const days = (row.days || []).map((day) => ({
    date: day.date,
    dateLabel: day.date ? isoToJalali(String(day.date).slice(0, 10)) : '-',
    target: Math.max(0, Number(day.targetMinutes || 0)),
    actual: Math.max(0, Number(day.actualMinutes || 0)),
    deficit: Math.max(0, Number(day.deficitMinutes || 0)),
    overtime: Math.max(0, Number(day.overtimeMinutes || 0)),
    utilization: Math.max(0, Number(day.utilizationPercent || 0)),
    status: day.status || 'empty',
    statusLabel: day.statusLabel || 'بدون داده',
  }))
  return {
    target,
    actual,
    deficit,
    overtime,
    statusKey,
    statusLabel,
    utilization: Math.max(0, Number(row.utilizationPercent || 0)),
    days,
  }
}

function departmentLabel(value) {
  if (!value) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'object') return value.name || value.title || value.label || ''
  return String(value)
}

const taskingSummaries = computed(() =>
  activeRows.value.map((row) => {
    const summary = taskingSummary(row)
    const { days: dayBreakdown, ...metrics } = summary
    const daysCount = Math.max(
      0,
      Number(row.effectiveDays ?? row.effective_days) || dayBreakdown.length || 0,
    )
    return {
      id: row.user?.id || row.id,
      name: row.user?.name || 'بدون نام',
      department: departmentLabel(row.user?.department),
      ...metrics,
      daysCount,
      dayBreakdown,
      raw: row,
    }
  }),
)

const taskingTotals = computed(() => {
  const rows = taskingSummaries.value
  const target = rows.reduce((sum, row) => sum + row.target, 0)
  const actual = rows.reduce((sum, row) => sum + row.actual, 0)
  return {
    people: rows.length,
    target,
    actual,
    deficit: Math.max(0, target - actual),
    overtime: Math.max(0, actual - target),
  }
})

const taskingLoading = computed(() => Boolean(state.tasking.reportsLoading))

const selectedTaskingDetail = computed(() => selectedTaskingPerson.value)

const taskingProgressPercent = computed(() => {
  const row = selectedTaskingDetail.value
  if (!row || !row.target) return 0
  return Math.min(100, Math.round((row.actual / row.target) * 100))
})

const taskingPeriodLabel = computed(() => {
  const item = periods.find((entry) => entry.key === filters.period)
  return item?.label || 'بازه انتخاب‌شده'
})

function openTaskingDetail(row) {
  selectedTaskingPerson.value = row
}

function closeTaskingDetail() {
  selectedTaskingPerson.value = null
}

async function refreshTaskingReports() {
  const range = periodIsoRange()
  await loadTaskingReports({
    start: range.start,
    end: range.end,
    userId: effectiveUserId.value || '',
  })
}

const selectedTabMeta = computed(() => tabs.value.find((item) => item.key === selectedReportType.value) || tabs.value[0])

const selectedDetailTitle = computed(() => {
  const row = selectedReportRow.value
  if (!row) return ''
  if (selectedReportType.value === 'attendance') return row.userName || 'رویداد ورود و خروج'
  return row.title || row.description || row.name || row.id || 'جزئیات گزارش'
})

const selectedDetailSubtitle = computed(() => {
  const row = selectedReportRow.value
  if (!row) return ''
  if (selectedReportType.value === 'expenses') return joinDisplayParts([row.owner, row.department, row.submittedAt], ' / ')
  if (selectedReportType.value === 'approvals') return joinDisplayParts([row.owner, row.type, row.uploadedAt], ' / ')
  if (selectedReportType.value === 'users') return joinDisplayParts([row.role, row.department, row.financeUpdatedAt || row.joinedAt], ' / ')
  if (selectedReportType.value === 'attendance') {
    return joinDisplayParts([
      eventLabel(row.eventType || row.event_type),
      row.userDepartment || row.userRole,
      dateTime(row.eventAt || row.event_at),
    ], ' / ')
  }
  return joinDisplayParts([row.owner, row.manager, row.createdAt], ' / ')
})

const selectedPrimaryMetrics = computed(() => {
  const row = selectedReportRow.value
  if (!row) return []
  if (selectedReportType.value === 'expenses') {
    return [
      { label: 'مبلغ', value: row.amount || '-', icon: 'payments' },
      { label: 'وضعیت', value: row.status || '-', icon: 'verified' },
      { label: 'واحد', value: row.department || '-', icon: 'apartment' },
    ]
  }
  if (selectedReportType.value === 'approvals') {
    return [
      { label: 'ریسک', value: row.risk || '-', icon: 'warning' },
      { label: 'وضعیت', value: row.status || '-', icon: 'fact_check' },
      { label: 'نوع سند', value: row.type || '-', icon: 'description' },
    ]
  }
  if (selectedReportType.value === 'users') {
    return [
      { label: 'پاداش', value: formatReportMoney(row.bonusAmount), icon: 'award_star' },
      { label: 'جریمه', value: formatReportMoney(row.penaltyAmount), icon: 'gavel' },
      { label: 'خالص', value: formatReportMoney(row.netAdjustment), icon: 'balance' },
    ]
  }
  if (selectedReportType.value === 'attendance') {
    return [
      { label: 'نوع', value: eventLabel(row.eventType || row.event_type), icon: 'badge' },
      { label: 'منبع', value: sourceLabel(row.source), icon: 'link' },
      { label: 'فاصله', value: row.distanceMeters != null ? `${Math.round(row.distanceMeters)} متر` : '-', icon: 'place' },
    ]
  }
  return [
    { label: 'اولویت', value: row.priority || '-', icon: 'priority_high' },
    { label: 'وضعیت', value: row.status || '-', icon: 'verified' },
    { label: 'واحد', value: row.department || '-', icon: 'apartment' },
  ]
})

const selectedDetailFields = computed(() => {
  const row = selectedReportRow.value
  if (!row) return []
  if (selectedReportType.value === 'expenses') {
    return [
      { label: 'کد', value: row.id },
      { label: 'ثبت‌کننده', value: row.owner },
      { label: 'تاریخ ثبت', value: row.submittedAt || row.createdAt },
      { label: 'واحد', value: row.department },
      { label: 'وضعیت', value: row.status },
      { label: 'مبلغ', value: row.amount },
      { label: 'شرح', value: row.description, wide: true },
    ]
  }
  if (selectedReportType.value === 'approvals') {
    return [
      { label: 'کد', value: row.id },
      { label: 'عنوان', value: row.title },
      { label: 'ثبت‌کننده', value: row.owner },
      { label: 'نوع', value: row.type },
      { label: 'واحد', value: row.department },
      { label: 'ریسک', value: row.risk },
      { label: 'وضعیت', value: row.status },
      { label: 'تاریخ بارگذاری', value: row.uploadedAt },
    ]
  }
  if (selectedReportType.value === 'users') {
    return [
      { label: 'شناسه', value: row.id },
      { label: 'نام', value: row.name },
      { label: 'نام کاربری', value: row.username },
      { label: 'نقش', value: row.role },
      { label: 'عنوان شغلی', value: row.jobTitle },
      { label: 'واحد', value: row.department },
      { label: 'مدیر مستقیم', value: row.manager },
      { label: 'وضعیت', value: row.status },
      { label: 'تاریخ عضویت', value: row.joinedAt },
      { label: 'آخرین بروزرسانی مالی', value: row.financeUpdatedAt || '-' },
      { label: 'پاداش', value: formatReportMoney(row.bonusAmount) },
      { label: 'جریمه', value: formatReportMoney(row.penaltyAmount) },
      { label: 'خالص پاداش/جریمه', value: formatReportMoney(row.netAdjustment) },
    ]
  }
  if (selectedReportType.value === 'attendance') {
    return [
      { label: 'پرسنل', value: row.userName },
      { label: 'سمت', value: row.userRole || '-' },
      { label: 'بخش', value: row.userDepartment || '-' },
      { label: 'موبایل', value: row.userPhone || '-' },
      { label: 'نوع', value: eventLabel(row.eventType || row.event_type) },
      { label: 'منبع', value: sourceLabel(row.source) },
      { label: 'تاریخ', value: row.eventDate ? isoToJalali(row.eventDate) : '-' },
      { label: 'ساعت', value: row.eventTime || '-' },
      { label: 'مختصات', value: row.coordinatesLabel || '-' },
      { label: 'یادداشت', value: row.note || '-', wide: true },
    ]
  }
  return [
    { label: 'کد', value: row.id },
    { label: 'عنوان', value: row.title },
    { label: 'ثبت‌کننده', value: row.owner },
    { label: 'مدیر', value: row.manager },
    { label: 'واحد', value: row.department },
    { label: 'اولویت', value: row.priority },
    { label: 'وضعیت', value: row.status },
    { label: 'تاریخ ثبت', value: row.createdAt },
  ]
})

function decisionText(item) {
  if (activeTab.value === 'users') return formatReportMoney(item.netAdjustment)
  if (activeTab.value === 'attendance') return sourceLabel(item.source)
  const decisions = item.decisions || []
  return decisions.length ? decisions.map((row) => `${row.approver}: ${row.statusLabel}`).join(' | ') : '-'
}

function openReportDetails(row) {
  selectedReportType.value = activeTab.value
  selectedReportRow.value = row
}

function closeReportDetails() {
  selectedReportRow.value = null
  selectedReportType.value = ''
}

function rowFileUrl(row = selectedReportRow.value) {
  if (!row) return ''
  if (selectedReportType.value === 'users' || selectedReportType.value === 'attendance') return ''
  return row.invoiceUrl || row.previewUrl || row.downloadUrl || ''
}

async function loadAttendanceReports() {
  if (!canViewAttendanceReports.value) return
  attendanceLoading.value = true
  attendanceError.value = ''
  try {
    const range = periodIsoRange()
    const params = new URLSearchParams()
    if (range.start) params.set('start', range.start)
    if (range.end) params.set('end', range.end)
    if (effectiveUserId.value) params.set('userId', effectiveUserId.value)
    const response = await fetch(`${API_BASE_URL}/attendance/reports?${params.toString()}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}` },
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(payload.detail || payload.message || 'بارگذاری گزارش ورود و خروج ناموفق بود.')
    const rows = payload.rows || []
    if (rows.length) {
      attendanceRows.value = rows
    } else {
      const daily = payload.dailyUserRows || payload.daily_user_rows || []
      attendanceRows.value = daily.flatMap((day) => day.events || [])
    }
  } catch (error) {
    attendanceError.value = error.message || 'بارگذاری گزارش ورود و خروج ناموفق بود.'
  } finally {
    attendanceLoading.value = false
  }
}

function exportAttendanceCsv() {
  const headers = ['ردیف', 'نام', 'سمت', 'بخش', 'نوع', 'منبع', 'تاریخ', 'ساعت', 'فاصله', 'مختصات', 'یادداشت']
  const lines = activeRows.value.map((row, index) => [
    index + 1,
    row.userName || '',
    row.userRole || '',
    row.userDepartment || '',
    eventLabel(row.eventType || row.event_type),
    sourceLabel(row.source),
    row.eventDate ? isoToJalali(row.eventDate) : '',
    row.eventTime || '',
    row.distanceMeters ?? '',
    row.coordinatesLabel || '',
    (row.note || '').replace(/\n/g, ' '),
  ].map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
  const csv = `\uFEFF${headers.join(',')}\n${lines.join('\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `attendance-report-${formatJalali(getTodayJalali())}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

function exportAttendancePdf() {
  const periodLabel = periods.find((item) => item.key === filters.period)?.label || ''
  const personLabel = effectiveUserName.value ? ` · ${effectiveUserName.value}` : ''
  exportAttendanceReportPdf({
    events: activeRows.value,
    title: 'گزارش ورود و خروج',
    subtitle: `${periodLabel}${personLabel}`,
    organizationName: state.currentUser.organization || 'کارنومند',
  })
}

function exportActiveTab() {
  if (activeTab.value === 'attendance') {
    exportAttendancePdf()
    return
  }
  if (activeTab.value === 'tasking') {
    const range = periodIsoRange()
    const params = new URLSearchParams()
    if (range.start) params.set('start', range.start)
    if (range.end) params.set('end', range.end)
    if (effectiveUserId.value) params.set('userId', effectiveUserId.value)
    exportReport('', 'csv', `/tasking/reports/export?${params.toString()}`)
    return
  }
  const params = new URLSearchParams({ format: 'csv', period: filters.period })
  if (filters.period === 'custom') {
    if (filters.startDate) params.set('startDate', jalaliToIso(filters.startDate))
    if (filters.endDate) params.set('endDate', jalaliToIso(filters.endDate))
  }
  if (effectiveUserId.value) params.set('userId', effectiveUserId.value)
  exportReport('', 'csv', `/reports/${activeTab.value}/export?${params.toString()}`)
}

watch(
  () => [
    activeTab.value,
    filters.period,
    filters.startDate,
    filters.endDate,
    filters.userId,
    state.liveSync.tick,
  ],
  () => {
    if (activeTab.value === 'attendance') void loadAttendanceReports()
    if (activeTab.value === 'tasking') void refreshTaskingReports()
  },
)

onMounted(() => {
  // Clear any leftover topbar person/date filters from older sessions.
  updatePageFilter('reports', 'person', '')
  updatePageFilter('reports', 'startDate', '')
  updatePageFilter('reports', 'endDate', '')
  updatePageFilter('reports', 'query', '')
  loadReports(true)
  if (activeTab.value === 'attendance') void loadAttendanceReports()
  if (activeTab.value === 'tasking') void refreshTaskingReports()
})
</script>

<template>
  <section v-if="state.currentUser.canViewReports" class="page-shell enterprise-page reports-page">
    <PageHeader
      eyebrow="گزارشات"
      title="گزارش‌های مدیریتی و خروجی‌ها"
      description="نمای تفکیکی گزارش در درخواست‌ها، هزینه‌ها و تاییدها با خروجی مستقیم."
    />

    <section class="surface-block report-controls">
      <div class="report-tabs" role="tablist" aria-label="نوع گزارش">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['report-tab', activeTab === tab.key && 'is-active']"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.key"
          @click="activeTab = tab.key"
        >
          <IconlyIcon :name="tab.icon" decorative />
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <div class="report-toolbar">
        <div class="report-toolbar-block">
          <span class="report-toolbar-label">بازه زمانی</span>
          <div class="chip-row report-period-chips" role="group" aria-label="بازه زمانی">
            <button
              v-for="item in periods"
              :key="item.key"
              :class="['filter-chip', filters.period === item.key && 'is-active']"
              type="button"
              @click="selectPeriod(item.key)"
            >
              {{ item.label }}
            </button>
          </div>
        </div>

        <div class="report-toolbar-row">
          <label class="report-filter-field report-person-field">
            <span class="report-filter-label">شخص</span>
            <select v-model="filters.userId" class="report-filter-control">
              <option value="">همه افراد</option>
              <option v-for="user in reportUsers" :key="user.id" :value="user.id">{{ user.name }}</option>
            </select>
          </label>

          <template v-if="filters.period === 'custom'">
            <label class="report-filter-field">
              <span class="report-filter-label">از تاریخ</span>
              <ShamsiDatePicker v-model="filters.startDate" model-type="jalali" />
            </label>
            <label class="report-filter-field">
              <span class="report-filter-label">تا تاریخ</span>
              <ShamsiDatePicker v-model="filters.endDate" model-type="jalali" />
            </label>
          </template>

          <button class="action-btn tone-primary report-export-btn" type="button" @click="exportActiveTab">
            <IconlyIcon name="download" decorative />
            <span>{{ activeTab === 'attendance' ? 'دانلود PDF' : activeTab === 'tasking' ? 'دانلود CSV' : 'دانلود جدول' }}</span>
          </button>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'tasking'" class="surface-block tasking-summary-panel">
      <div class="section-label-row">
        <SectionHeading
          title="خلاصه تسکینگ"
          description="در این بازه: چقدر باید کار می‌کرد، چقدر کار کرده، کسری یا اضافه‌کار."
        />
        <span class="meta-pill">{{ toPersianDigits(taskingTotals.people) }} نفر</span>
      </div>

      <div class="tasking-total-strip">
        <article>
          <small>باید کار کند</small>
          <strong>{{ hoursLabel(taskingTotals.target) }}</strong>
        </article>
        <article>
          <small>کارکرد واقعی</small>
          <strong>{{ hoursLabel(taskingTotals.actual) }}</strong>
        </article>
        <article class="is-deficit">
          <small>کسری</small>
          <strong>{{ hoursLabel(taskingTotals.deficit) }}</strong>
        </article>
        <article class="is-overtime">
          <small>اضافه‌کار</small>
          <strong>{{ hoursLabel(taskingTotals.overtime) }}</strong>
        </article>
      </div>

      <p v-if="taskingLoading" class="tasking-empty">در حال بارگذاری…</p>
      <p v-else-if="!taskingSummaries.length" class="tasking-empty">برای این بازه داده‌ای نیست.</p>

      <div v-else class="tasking-summary-list">
        <button
          v-for="row in taskingSummaries"
          :key="row.id"
          class="tasking-summary-card"
          :class="`is-${row.statusKey}`"
          type="button"
          @click="openTaskingDetail(row)"
        >
          <header class="tasking-summary-head">
            <div class="tasking-summary-identity">
              <UserAvatar :person="row.raw?.user" :name="row.name" size="md" />
              <div>
                <strong>{{ row.name }}</strong>
                <small>{{ row.department || 'بدون بخش' }} · {{ toPersianDigits(row.daysCount) }} روز کاری</small>
              </div>
            </div>
            <span class="tasking-status-pill">{{ row.statusLabel }}</span>
          </header>

          <div class="tasking-summary-preview">
            <span>باید {{ hoursLabel(row.target) }}</span>
            <i aria-hidden="true" />
            <span>کارکرد {{ hoursLabel(row.actual) }}</span>
            <i aria-hidden="true" />
            <span v-if="row.deficit">کسری {{ hoursLabel(row.deficit) }}</span>
            <span v-else-if="row.overtime">اضافه‌کار {{ hoursLabel(row.overtime) }}</span>
            <span v-else>بدون کسری</span>
          </div>
        </button>
      </div>
    </section>

    <AttendancePeriodBoard
      v-if="activeTab === 'attendance'"
      :events="activeRows"
      :mode="filters.period === 'today' ? 'today' : 'period'"
      :loading="attendanceLoading"
      :error="attendanceError"
      :can-edit-times="true"
      @updated="loadAttendanceReports"
    />

    <section v-else-if="activeTab !== 'tasking'" class="surface-block report-table-card">
      <div class="section-label-row">
        <SectionHeading
          :title="tabs.find((item) => item.key === activeTab)?.label || 'گزارش'"
          :description="`${activeRows.length} ردیف در این خروجی نمایش داده می‌شود.`"
        />
        <span class="meta-pill">{{ activeRows.length }} ردیف</span>
      </div>

      <div class="report-table-wrap">
        <table class="report-table">
          <thead>
            <tr v-if="activeTab === 'requests'"><th>کد</th><th>عنوان</th><th>ثبت‌کننده</th><th>مدیر</th><th>واحد</th><th>وضعیت</th><th>اولویت</th><th>تاریخ</th><th>تصمیم‌ها</th></tr>
            <tr v-else-if="activeTab === 'expenses'"><th>کد</th><th>شرح</th><th>ثبت‌کننده</th><th>مبلغ</th><th>واحد</th><th>وضعیت</th><th>تاریخ</th><th>تصمیم‌ها</th></tr>
            <tr v-else-if="activeTab === 'approvals'"><th>کد</th><th>عنوان</th><th>ثبت‌کننده</th><th>نوع</th><th>واحد</th><th>ریسک</th><th>وضعیت</th><th>تاریخ</th><th>تصمیم‌ها</th></tr>
            <tr v-else><th>شناسه</th><th>نام</th><th>نام کاربری</th><th>نقش</th><th>واحد</th><th>مدیر</th><th>پاداش</th><th>جریمه</th><th>خالص</th></tr>
          </thead>
          <tbody>
            <tr
              v-for="row in activeRows"
              :key="row.id"
              :class="['report-click-row', rowToneForStatus(rowStatusValue(row))]"
              tabindex="0"
              @click="openReportDetails(row)"
              @keydown.enter.prevent="openReportDetails(row)"
              @keydown.space.prevent="openReportDetails(row)"
            >
              <template v-if="activeTab === 'requests'">
                <td class="cell-mobile-hide">{{ row.id }}</td>
                <td class="cell-mobile-primary">
                  <strong>{{ row.title }}</strong>
                  <small>{{ joinDisplayParts([row.owner, row.department]) || '—' }}</small>
                </td>
                <td class="cell-mobile-hide">{{ row.owner }}</td>
                <td class="cell-mobile-hide">{{ row.manager }}</td>
                <td class="cell-mobile-hide">{{ row.department }}</td>
                <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(row.status)]">{{ row.status }}</span></td>
                <td class="cell-mobile-hide">{{ row.priority }}</td>
                <td data-label="تاریخ">{{ row.createdAt }}</td>
                <td class="cell-mobile-hide">{{ decisionText(row) }}</td>
              </template>
              <template v-else-if="activeTab === 'expenses'">
                <td class="cell-mobile-hide">{{ row.id }}</td>
                <td class="cell-mobile-primary">
                  <strong>{{ row.description }}</strong>
                  <small>{{ joinDisplayParts([row.owner, row.department, row.amount]) || '—' }}</small>
                </td>
                <td class="cell-mobile-hide">{{ row.owner }}</td>
                <td data-label="مبلغ">{{ row.amount }}</td>
                <td class="cell-mobile-hide">{{ row.department }}</td>
                <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(row.status)]">{{ row.status }}</span></td>
                <td data-label="تاریخ">{{ row.submittedAt }}</td>
                <td class="cell-mobile-hide">{{ decisionText(row) }}</td>
              </template>
              <template v-else-if="activeTab === 'approvals'">
                <td class="cell-mobile-hide">{{ row.id }}</td>
                <td class="cell-mobile-primary">
                  <strong>{{ row.title }}</strong>
                  <small>{{ joinDisplayParts([row.owner, row.type, row.department]) || '—' }}</small>
                </td>
                <td class="cell-mobile-hide">{{ row.owner }}</td>
                <td class="cell-mobile-hide">{{ row.type }}</td>
                <td class="cell-mobile-hide">{{ row.department }}</td>
                <td class="cell-mobile-hide">{{ row.risk }}</td>
                <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(row.status)]">{{ row.status }}</span></td>
                <td data-label="تاریخ">{{ row.uploadedAt }}</td>
                <td class="cell-mobile-hide">{{ decisionText(row) }}</td>
              </template>
              <template v-else>
                <td class="cell-mobile-hide">{{ row.id }}</td>
                <td class="cell-mobile-primary">
                  <strong>{{ row.name }}</strong>
                  <small>{{ joinDisplayParts([row.role, row.department]) || '—' }}</small>
                </td>
                <td class="cell-mobile-hide">{{ row.username }}</td>
                <td class="cell-mobile-hide">{{ row.role }}</td>
                <td class="cell-mobile-hide">{{ row.department }}</td>
                <td class="cell-mobile-hide">{{ row.manager }}</td>
                <td data-label="پاداش">{{ formatReportMoney(row.bonusAmount) }}</td>
                <td data-label="جریمه">{{ formatReportMoney(row.penaltyAmount) }}</td>
                <td data-label="خالص">{{ formatReportMoney(row.netAdjustment) }}</td>
              </template>
            </tr>
            <tr v-if="!activeRows.length">
              <td :colspan="activeTab === 'expenses' ? 8 : 9" class="table-empty">
                {{ attendanceLoading && activeTab === 'attendance' ? 'در حال بارگذاری…' : 'ردیفی برای این فیلترها پیدا نشد.' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <BaseModal :open="!!selectedTaskingDetail" size="detail" @close="closeTaskingDetail">
      <article v-if="selectedTaskingDetail" class="tasking-detail" :class="`is-${selectedTaskingDetail.statusKey}`">
        <header class="tasking-detail-hero">
          <UserAvatar :person="selectedTaskingDetail.raw?.user" :name="selectedTaskingDetail.name" size="lg" />
          <div class="tasking-detail-copy">
            <span class="tasking-detail-kicker">{{ taskingPeriodLabel }}</span>
            <h2>{{ selectedTaskingDetail.name }}</h2>
            <p>{{ selectedTaskingDetail.department || 'بدون بخش' }} · {{ toPersianDigits(selectedTaskingDetail.daysCount) }} روز کاری</p>
          </div>
          <span class="tasking-detail-status">{{ selectedTaskingDetail.statusLabel }}</span>
        </header>

        <section class="tasking-detail-progress">
          <div class="tasking-detail-progress-labels">
            <span>پیشرفت نسبت به هدف</span>
            <strong>{{ toPersianDigits(taskingProgressPercent) }}٪</strong>
          </div>
          <div class="tasking-detail-track" aria-hidden="true">
            <span :style="{ width: `${taskingProgressPercent}%` }" />
          </div>
          <p class="tasking-detail-progress-note">
            کارکرد {{ hoursLabel(selectedTaskingDetail.actual) }} از هدف {{ hoursLabel(selectedTaskingDetail.target) }}
          </p>
        </section>

        <section class="tasking-detail-metrics">
          <article>
            <small>باید کار کند</small>
            <strong>{{ hoursLabel(selectedTaskingDetail.target) }}</strong>
          </article>
          <article>
            <small>کارکرد واقعی</small>
            <strong>{{ hoursLabel(selectedTaskingDetail.actual) }}</strong>
          </article>
          <article class="is-deficit">
            <small>کسری</small>
            <strong>{{ hoursLabel(selectedTaskingDetail.deficit) }}</strong>
          </article>
          <article class="is-overtime">
            <small>اضافه‌کار</small>
            <strong>{{ hoursLabel(selectedTaskingDetail.overtime) }}</strong>
          </article>
        </section>

        <section class="tasking-day-board">
          <header class="tasking-day-board-head">
            <strong>تفکیک روزبه‌روز</strong>
            <small>رنگ هر روز وضعیت کسری یا رسیدن به هدف را نشان می‌دهد.</small>
          </header>
          <div v-if="selectedTaskingDetail.dayBreakdown?.length" class="tasking-day-list">
            <article
              v-for="day in selectedTaskingDetail.dayBreakdown"
              :key="day.date"
              :class="['tasking-day-card', `is-${day.status}`]"
            >
              <div class="tasking-day-top">
                <strong>{{ day.dateLabel }}</strong>
                <span>{{ day.statusLabel }}</span>
              </div>
              <div class="tasking-day-metrics">
                <span>هدف: {{ hoursLabel(day.target) }}</span>
                <span>کارکرد: {{ hoursLabel(day.actual) }}</span>
                <span v-if="day.deficit">کسری: {{ hoursLabel(day.deficit) }}</span>
                <span v-else-if="day.overtime">اضافه: {{ hoursLabel(day.overtime) }}</span>
                <span v-else>وضعیت: OK</span>
              </div>
              <div class="tasking-day-track" aria-hidden="true">
                <i :style="{ width: `${Math.min(100, day.utilization || 0)}%` }" />
              </div>
            </article>
          </div>
          <p v-else class="tasking-empty">برای این بازه روز کاری ثبت نشده است.</p>
        </section>

        <section class="tasking-detail-side">
          <article>
            <span>تکمیل‌شده</span>
            <b>{{ toPersianDigits(selectedTaskingDetail.raw?.completedCount || 0) }}</b>
          </article>
          <article>
            <span>در انتظار</span>
            <b>{{ toPersianDigits(selectedTaskingDetail.raw?.pendingCount || 0) }}</b>
          </article>
          <article>
            <span>عقب‌افتاده</span>
            <b>{{ toPersianDigits(selectedTaskingDetail.raw?.overdueCount || 0) }}</b>
          </article>
        </section>

        <footer class="tasking-detail-actions">
          <button class="action-btn tone-soft" type="button" @click="closeTaskingDetail">بستن</button>
        </footer>
      </article>
    </BaseModal>

    <BaseModal :open="!!selectedReportRow" size="detail" @close="closeReportDetails">
      <article v-if="selectedReportRow" class="report-detail-modal">
        <header class="report-detail-hero">
          <div class="report-detail-icon">
            <IconlyIcon :name="selectedTabMeta.icon" decorative />
          </div>
          <div class="report-detail-title">
            <span class="page-eyebrow">{{ selectedTabMeta.label }}</span>
            <h2>{{ selectedDetailTitle }}</h2>
            <p>{{ selectedDetailSubtitle }}</p>
          </div>
          <span class="report-detail-code">{{ selectedReportRow.id }}</span>
        </header>

        <section class="report-detail-metrics">
          <article v-for="item in selectedPrimaryMetrics" :key="item.label" class="report-detail-metric">
            <IconlyIcon :name="item.icon" decorative />
            <small>{{ item.label }}</small>
            <strong>{{ item.value }}</strong>
          </article>
        </section>

        <section class="report-detail-grid">
          <article v-for="field in selectedDetailFields" :key="field.label" :class="['report-detail-field', field.wide && 'is-wide']">
            <span>{{ field.label }}</span>
            <strong>{{ field.value || '-' }}</strong>
          </article>
        </section>

        <section v-if="selectedReportType !== 'users' && selectedReportType !== 'attendance'" class="report-detail-decisions">
          <div class="section-label-row">
            <SectionHeading
              title="تصمیمات و گردش تایید"
              description="مسیر تایید، ارجاع و تصمیم‌های ثبت‌شده برای این ردیف گزارش."
            />
            <span class="meta-pill">{{ (selectedReportRow.decisions || []).length }} مورد</span>
          </div>
          <div v-if="(selectedReportRow.decisions || []).length" class="decision-timeline">
            <article v-for="decision in selectedReportRow.decisions" :key="`${decision.approver}-${decision.statusLabel}`" class="decision-step">
              <span class="decision-dot"></span>
              <div>
                <strong>{{ decision.approver || 'نامشخص' }}</strong>
                <small>{{ decision.statusLabel || '-' }}</small>
              </div>
            </article>
          </div>
          <div v-else class="empty-state-inline compact-empty">
            <IconlyIcon name="pending_actions" decorative />
            <p>تصمیمی برای این مورد ثبت نشده است.</p>
          </div>
        </section>

        <footer class="report-detail-actions">
          <a v-if="rowFileUrl()" class="action-btn tone-primary" :href="rowFileUrl()" target="_blank" rel="noreferrer">
            <IconlyIcon name="open_in_new" decorative />
            <span>مشاهده فایل</span>
          </a>
          <button class="action-btn tone-soft" type="button" @click="closeReportDetails">
            <IconlyIcon name="close" decorative />
            <span>بستن</span>
          </button>
        </footer>
      </article>
    </BaseModal>
  </section>

  <section v-else class="page-shell"><article class="access-denied-card"><h2>دسترسی گزارشات ندارید</h2></article></section>
</template>

<style scoped>
.reports-page {
  gap: 16px;
  min-width: 0;
  max-width: 100%;
  overflow-x: clip;
}
.report-controls {
  display: grid;
  gap: 14px;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}
.report-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding-bottom: 2px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.report-tabs::-webkit-scrollbar { display: none; }
.report-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 12px;
  min-width: 0;
  max-width: 100%;
}
.report-toolbar-block {
  display: grid;
  gap: 8px;
  flex: 1 1 220px;
  min-width: 0;
  max-width: 100%;
}
.report-toolbar-label {
  font-size: 11px;
  font-weight: 700;
  color: #45605c;
}
.report-toolbar-row {
  display: flex;
  align-items: end;
  gap: 10px;
  flex-wrap: wrap;
  flex: 1 1 240px;
  min-width: 0;
  max-width: 100%;
}
.report-tab {
  flex: 0 0 auto;
  min-height: 36px;
  border: 0;
  border-radius: 12px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #1f5c59;
  background: #e4f4f2;
  font-weight: 700;
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;
}
.report-tab.is-active {
  color: #fff;
  background: #34908B;
}
.report-period-chips {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  align-items: center;
  min-height: 40px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 2px;
}
.report-period-chips::-webkit-scrollbar { display: none; }
.report-period-chips .filter-chip {
  flex: 0 0 auto;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  white-space: nowrap;
}
.report-filter-field {
  display: grid;
  grid-template-rows: 18px 40px;
  gap: 6px;
  min-width: 0;
  flex: 1 1 140px;
  max-width: 100%;
  margin: 0;
}
.report-person-field {
  flex: 1 1 160px;
  min-width: 0;
}
.report-filter-label {
  display: inline-flex;
  align-items: center;
  height: 18px;
  font-size: 11px;
  font-weight: 700;
  color: #45605c;
}
.report-filter-control {
  box-sizing: border-box;
  width: 100%;
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
  padding: 0 12px !important;
  border: 0 !important;
  border-radius: 12px !important;
  background: #e4f4f2 !important;
  color: #152523;
  font: inherit;
  font-size: 0.86rem;
}
.report-filter-field :deep(.shamsi-picker),
.report-filter-field :deep(.shamsi-picker-input-wrap) {
  width: 100%;
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
}
.report-filter-field :deep(.shamsi-picker-input-wrap) {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  padding-inline: 12px 36px !important;
  padding-block: 0 !important;
  border-radius: 12px !important;
  background: #e4f4f2 !important;
}
.report-filter-field :deep(.shamsi-picker-input) {
  height: 100% !important;
  min-height: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  line-height: 40px;
}
.report-filter-field :deep(.shamsi-picker-toggle) {
  position: absolute;
  inset-inline-end: 5px;
  top: 50%;
  transform: translateY(-50%);
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: #f3f9f7 !important;
}
.report-export-btn {
  flex: 0 1 auto;
  height: 40px !important;
  min-height: 40px !important;
  max-width: 100%;
  border-radius: 12px;
  align-self: end;
  white-space: nowrap;
}
.compact-field { min-width: 190px; margin: 0; }
.report-table-wrap { overflow-x: auto; }
.report-table { width: 100%; min-width: 980px; border-collapse: collapse; }
.report-table th, .report-table td { padding: 12px 10px; border-bottom: 1px solid rgba(38,56,92,.08); text-align: right; vertical-align: top; }
.report-table th { color: #52607a; font-size: 12px; }
.report-table td { color: #203255; line-height: 1.7; }
.report-table td.cell-mobile-primary {
  min-width: 0;
  max-width: 28rem;
}
.report-table td.cell-mobile-primary strong,
.report-table td.cell-mobile-primary small {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow-wrap: normal;
  word-break: keep-all;
}
.report-table td.cell-mobile-primary strong {
  color: #163532;
  font-weight: 800;
  line-height: 1.45;
}
.report-table td.cell-mobile-primary small {
  margin-top: 4px;
  color: #5f7a76;
  font-size: 0.78rem;
  font-weight: 700;
}
.report-click-row {
  cursor: pointer;
  outline: 0;
  transition: background-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}
.report-click-row:hover,
.report-click-row:focus-visible {
  background: rgba(52, 144, 139, 0.08);
  box-shadow: none;
}
.report-detail-modal {
  display: grid;
  gap: 18px;
  padding: 4px;
}
.report-detail-hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: start;
  padding: 22px;
  border-radius: 8px;
  background: var(--surface, #fff);
  color: #fff;
  box-shadow: none;
}
.report-detail-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.report-detail-icon span { font-size: 30px; }
.report-detail-title {
  display: grid;
  gap: 7px;
  min-width: 0;
}
.report-detail-title h2,
.report-detail-title p {
  margin: 0;
}
.report-detail-title h2 {
  font-size: clamp(22px, 2vw, 32px);
  line-height: 1.35;
  overflow-wrap: break-word;
  word-break: normal;
}
.report-detail-title p {
  color: rgba(255, 255, 255, 0.76);
  line-height: 1.9;
  overflow-wrap: break-word;
  word-break: normal;
}
.report-detail-code {
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.14);
  font-weight: 900;
  direction: ltr;
}
.report-detail-metrics,
.report-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.report-detail-metric,
.report-detail-field,
.report-detail-decisions {
  border: 1px solid rgba(38, 56, 92, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: none;
}
.report-detail-metric {
  min-height: 112px;
  display: grid;
  align-content: center;
  gap: 6px;
  padding: 16px;
}
.report-detail-metric span {
  color: var(--primary);
  font-size: 28px;
}
.report-detail-metric small,
.report-detail-field span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}
.report-detail-metric strong,
.report-detail-field strong {
  color: #203255;
  line-height: 1.7;
  overflow-wrap: break-word;
  word-break: normal;
}
.report-detail-field {
  display: grid;
  gap: 7px;
  padding: 14px 16px;
}
.report-detail-field.is-wide {
  grid-column: 1 / -1;
}
.report-detail-decisions {
  display: grid;
  gap: 12px;
  padding: 16px;
}
.decision-timeline {
  display: grid;
  gap: 10px;
}
.decision-step {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: start;
  min-width: 0;
  padding: 12px;
  border-radius: 8px;
  background: rgba(246, 248, 252, 0.9);
}
.decision-dot {
  width: 12px;
  height: 12px;
  margin-top: 7px;
  border-radius: 999px;
  background: var(--primary);
  box-shadow: none;
}
.decision-step strong,
.decision-step small {
  display: block;
  overflow-wrap: break-word;
  word-break: normal;
}
.decision-step small {
  margin-top: 4px;
  color: var(--muted);
}
.compact-empty {
  padding: 12px;
}
.tasking-summary-panel {
  display: grid;
  gap: 14px;
}
.tasking-total-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.tasking-total-strip article {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 14px;
  border-radius: 14px;
  background: #eef6f4;
}
.tasking-total-strip small {
  color: #45605c;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tasking-total-strip strong {
  color: #163532;
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: normal;
  word-break: keep-all;
}
.tasking-total-strip .is-deficit {
  background: #fff1f0;
}
.tasking-total-strip .is-deficit strong {
  color: #b42318;
}
.tasking-total-strip .is-overtime {
  background: #eef6ff;
}
.tasking-total-strip .is-overtime strong {
  color: #175cd3;
}
.tasking-summary-list {
  display: grid;
  gap: 10px;
}
.tasking-summary-card {
  display: grid;
  gap: 12px;
  width: 100%;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: #f8fcfb;
  text-align: right;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background-color 0.18s ease;
}
.tasking-summary-card:hover,
.tasking-summary-card:focus-visible {
  transform: translateY(-1px);
  border-color: rgba(52, 144, 139, 0.28);
  outline: 0;
}
.tasking-summary-card.is-deficit {
  border-color: rgba(180, 35, 24, 0.16);
  background: #fffafa;
}
.tasking-summary-card.is-overtime {
  border-color: rgba(23, 92, 211, 0.14);
  background: #f8fbff;
}
.tasking-summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}
.tasking-summary-identity {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}
.tasking-summary-identity > div {
  min-width: 0;
  flex: 1;
}
.tasking-summary-identity strong {
  display: block;
  color: #163532;
  font-size: 0.98rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: normal;
  word-break: keep-all;
}
.tasking-summary-identity small {
  display: block;
  margin-top: 4px;
  color: #607874;
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tasking-status-pill {
  flex: 0 0 auto;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: #e4f4f2;
  color: #1f5c59;
  font-size: 0.75rem;
  font-weight: 800;
}
.tasking-summary-card.is-deficit .tasking-status-pill {
  background: #fee4e2;
  color: #b42318;
}
.tasking-summary-card.is-overtime .tasking-status-pill {
  background: #d1e9ff;
  color: #175cd3;
}
.tasking-summary-preview {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  color: #45605c;
  font-size: 0.82rem;
  font-weight: 700;
}
.tasking-summary-preview i {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.35);
}
.tasking-empty {
  margin: 0;
  padding: 18px;
  border-radius: 14px;
  background: #eef6f4;
  color: #45605c;
  text-align: center;
  font-weight: 700;
}

.tasking-detail {
  display: grid;
  gap: 16px;
  padding: 4px;
}
.tasking-detail-hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 18px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgba(52, 144, 139, 0.18), transparent 42%),
    linear-gradient(160deg, #f3faf8 0%, #eaf5f3 100%);
}
.tasking-detail.is-deficit .tasking-detail-hero {
  background:
    radial-gradient(circle at top left, rgba(180, 35, 24, 0.12), transparent 42%),
    linear-gradient(160deg, #fff7f6 0%, #ffefed 100%);
}
.tasking-detail.is-overtime .tasking-detail-hero {
  background:
    radial-gradient(circle at top left, rgba(23, 92, 211, 0.12), transparent 42%),
    linear-gradient(160deg, #f5f9ff 0%, #eaf2ff 100%);
}
.tasking-detail-copy {
  min-width: 0;
}
.tasking-detail-kicker {
  display: inline-block;
  margin-bottom: 6px;
  color: #45605c;
  font-size: 0.75rem;
  font-weight: 800;
}
.tasking-detail-copy h2,
.tasking-detail-copy p {
  margin: 0;
}
.tasking-detail-copy h2 {
  color: #163532;
  font-size: 1.35rem;
  line-height: 1.35;
}
.tasking-detail-copy p {
  margin-top: 6px;
  color: #607874;
  font-size: 0.86rem;
}
.tasking-detail-status {
  align-self: start;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.78);
  color: #1f5c59;
  font-size: 0.78rem;
  font-weight: 800;
  box-shadow: inset 0 0 0 1px rgba(52, 144, 139, 0.12);
}
.tasking-detail.is-deficit .tasking-detail-status {
  color: #b42318;
  box-shadow: inset 0 0 0 1px rgba(180, 35, 24, 0.14);
}
.tasking-detail.is-overtime .tasking-detail-status {
  color: #175cd3;
  box-shadow: inset 0 0 0 1px rgba(23, 92, 211, 0.14);
}
.tasking-detail-progress {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid rgba(52, 144, 139, 0.1);
}
.tasking-detail-progress-labels {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #45605c;
  font-size: 0.82rem;
  font-weight: 700;
}
.tasking-detail-progress-labels strong {
  color: #163532;
  font-size: 1rem;
}
.tasking-detail-track {
  height: 10px;
  border-radius: 999px;
  background: #e7f2f0;
  overflow: hidden;
}
.tasking-detail-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #34908b, #4db6b0);
  transition: width 0.28s ease;
}
.tasking-detail.is-deficit .tasking-detail-track span {
  background: linear-gradient(90deg, #f04438, #f97066);
}
.tasking-detail.is-overtime .tasking-detail-track span {
  background: linear-gradient(90deg, #2e90fa, #53b1fd);
}
.tasking-detail-progress-note {
  margin: 0;
  color: #607874;
  font-size: 0.8rem;
  font-weight: 600;
}
.tasking-detail-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.tasking-detail-metrics article {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: #f3faf8;
}
.tasking-detail-metrics small {
  color: #607874;
  font-size: 0.75rem;
  font-weight: 700;
}
.tasking-detail-metrics strong {
  color: #163532;
  font-size: 1.02rem;
  font-weight: 800;
  line-height: 1.45;
}
.tasking-detail-metrics .is-deficit {
  background: #fff1f0;
}
.tasking-detail-metrics .is-deficit strong {
  color: #b42318;
}
.tasking-detail-metrics .is-overtime {
  background: #eef6ff;
}
.tasking-detail-metrics .is-overtime strong {
  color: #175cd3;
}
.tasking-day-board {
  display: grid;
  gap: 12px;
}
.tasking-day-board-head {
  display: grid;
  gap: 4px;
}
.tasking-day-board-head strong {
  color: #163532;
  font-size: 0.95rem;
}
.tasking-day-board-head small {
  color: #607874;
  font-size: 0.78rem;
  font-weight: 600;
}
.tasking-day-list {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
  padding-left: 2px;
}
.tasking-day-card {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid transparent;
}
.tasking-day-card.is-ok {
  background: rgba(22, 163, 74, 0.1);
  border-color: rgba(22, 163, 74, 0.18);
}
.tasking-day-card.is-warn {
  background: rgba(217, 119, 6, 0.12);
  border-color: rgba(217, 119, 6, 0.2);
}
.tasking-day-card.is-bad {
  background: rgba(220, 38, 38, 0.1);
  border-color: rgba(220, 38, 38, 0.18);
}
.tasking-day-card.is-empty {
  background: rgba(100, 116, 139, 0.08);
  border-color: rgba(100, 116, 139, 0.14);
}
.tasking-day-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.tasking-day-top strong {
  color: #163532;
  font-size: 0.9rem;
}
.tasking-day-top span {
  font-size: 0.75rem;
  font-weight: 800;
}
.tasking-day-card.is-ok .tasking-day-top span { color: #15803d; }
.tasking-day-card.is-warn .tasking-day-top span { color: #b45309; }
.tasking-day-card.is-bad .tasking-day-top span { color: #b91c1c; }
.tasking-day-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: #34514d;
  font-size: 0.78rem;
  font-weight: 700;
}
.tasking-day-track {
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.65);
  overflow: hidden;
}
.tasking-day-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: currentColor;
}
.tasking-day-card.is-ok .tasking-day-track i { background: #16a34a; }
.tasking-day-card.is-warn .tasking-day-track i { background: #d97706; }
.tasking-day-card.is-bad .tasking-day-track i { background: #dc2626; }
.tasking-day-card.is-empty .tasking-day-track i { background: #94a3b8; }
.tasking-detail-side {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.tasking-detail-side article {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid rgba(52, 144, 139, 0.1);
  text-align: center;
}
.tasking-detail-side span {
  color: #607874;
  font-size: 0.72rem;
  font-weight: 700;
}
.tasking-detail-side b {
  color: #163532;
  font-size: 1.1rem;
  font-weight: 800;
}
.tasking-detail-actions {
  display: flex;
  justify-content: flex-end;
}
.report-detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}
@media (max-width: 760px) {
  .tasking-total-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .tasking-detail-hero {
    grid-template-columns: auto minmax(0, 1fr);
  }
  .tasking-detail-status {
    grid-column: 1 / -1;
    justify-self: start;
  }
  .tasking-detail-side {
    grid-template-columns: 1fr;
  }
  .report-controls {
    gap: 12px;
    padding: 12px;
  }
  .report-tabs {
    margin: 0 -2px;
    padding-inline: 2px;
  }
  .report-toolbar {
    display: grid;
    gap: 12px;
  }
  .report-toolbar-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
    align-items: end;
  }
  .report-filter-field,
  .report-person-field {
    width: 100%;
    min-width: 0;
    flex: none;
  }
  .report-export-btn {
    width: auto;
    min-width: 0;
    flex: none;
    white-space: nowrap;
  }
  .report-period-chips {
    margin: 0 -2px;
    padding-inline: 2px;
  }
  .tasking-summary-list {
    grid-template-columns: 1fr;
  }
  .tasking-summary-card {
    box-shadow: none;
  }
  .tasking-total-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .tasking-summary-preview {
    flex-wrap: wrap;
    gap: 6px 8px;
    font-size: 0.78rem;
  }
  .tasking-summary-identity strong {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    overflow-wrap: normal;
    word-break: keep-all;
  }
  .report-table {
    min-width: 0;
  }
  .report-table td.cell-mobile-primary {
    max-width: none;
  }
  .report-period-chips .filter-chip {
    min-height: 38px;
    font-size: 0.82rem;
  }
  .report-detail-hero {
    display: grid;
    grid-template-columns: 1fr;
    padding: 18px;
  }
  .report-detail-metrics,
  .report-detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .compact-field,
  .action-btn,
  .report-detail-actions {
    width: 100%;
  }
  .report-detail-actions {
    justify-content: stretch;
  }
}
@media (max-width: 420px) {
  .report-detail-metrics,
  .report-detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
