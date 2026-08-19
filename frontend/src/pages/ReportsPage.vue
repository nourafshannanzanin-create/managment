<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import PageHeader from '../components/PageHeader.vue'
import SectionHeading from '../components/SectionHeading.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { formatJalali, formatTehranDateTime, getTodayIso, getTodayJalali, isoToJalali, jalaliToIso, shiftIsoDate } from '../utils/jalali'
import { useWorkflowHub } from '../stores/workflowHub'
import { joinDisplayParts } from '../utils/text'
import { rowToneForStatus, toneForStatus } from '../utils/status'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'

const { exportReport, loadReports, loadTaskingReports, state } = useWorkflowHub()

const activeTab = ref('requests')
const selectedReportRow = ref(null)
const selectedReportType = ref('')
const filters = reactive({ period: 'month', startDate: '', endDate: '', userId: '' })
const attendanceRows = ref([])
const attendanceLoading = ref(false)
const attendanceError = ref('')
const taskingBandFilter = ref('')

const topbarFilter = computed(() => state.filters.reports || { query: '', person: '', startDate: '', endDate: '' })

function matchesTopbar(item, fields = []) {
  const query = String(topbarFilter.value.query || '').trim().toLowerCase()
  const person = String(topbarFilter.value.person || '').trim()
  const start = String(topbarFilter.value.startDate || '').trim()
  const end = String(topbarFilter.value.endDate || '').trim()
  if (query) {
    const hay = fields.map((key) => String(item?.[key] || '')).join(' ').toLowerCase()
    if (!hay.includes(query)) return false
  }
  if (person) {
    const people = [item?.owner, item?.manager, item?.name, item?.user?.name, item?.assignee?.name].filter(Boolean).map(String)
    if (!people.some((name) => name === person || name.includes(person))) return false
  }
  const iso = rowDate(item)
  if (start || end) {
    if (!iso) return activeTab.value === 'users' || activeTab.value === 'tasking'
    const startIso = start.includes('-') && start.length === 10 && Number(start.slice(0, 4)) > 1500 ? start : (start ? jalaliToIso(start) : '')
    const endIso = end.includes('-') && end.length === 10 && Number(end.slice(0, 4)) > 1500 ? end : (end ? jalaliToIso(end) : '')
    if (startIso && iso < startIso) return false
    if (endIso && iso > endIso) return false
  }
  return true
}

const canViewAttendanceReports = computed(() =>
  Boolean(
    state.currentUser.isHq ||
    (state.currentUser.isManager && state.currentUser.menuAccess?.attendance === true),
  ),
)

const tabs = computed(() => {
  const items = [
    { key: 'requests', label: 'درخواست‌ها', icon: 'assignment' },
    { key: 'expenses', label: 'هزینه‌ها', icon: 'payments' },
    { key: 'approvals', label: 'تاییدیه‌ها', icon: 'fact_check' },
    { key: 'users', label: 'کاربران', icon: 'groups' },
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
  if (filters.period === 'week') {
    const [year, month, day] = todayIso.split('-').map(Number)
    const weekday = new Date(Date.UTC(year, month - 1, day)).getUTCDay()
    const mondayOffset = (weekday + 6) % 7
    return { start: shiftIsoDate(todayIso, -mondayOffset), end: todayIso }
  }
  if (filters.period === 'month') return { start: `${todayIso.slice(0, 8)}01`, end: todayIso }
  if (filters.period === 'year') return { start: `${todayIso.slice(0, 4)}-01-01`, end: todayIso }
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
      if (taskingBandFilter.value && item.band !== taskingBandFilter.value) return false
      if (filters.userId && String(item.user?.id) !== String(filters.userId)) return false
      return matchesTopbar(
        {
          ...item,
          name: item.user?.name,
          owner: item.user?.name,
          department: item.user?.department,
        },
        ['name', 'owner', 'department', 'bandLabel'],
      )
    })
  }
  if (activeTab.value === 'attendance') {
    return attendanceRows.value.filter((item) => {
      if (filters.userId && String(item.userId || item.user_id) !== String(filters.userId)) return false
      return matchesTopbar(
        {
          ...item,
          name: item.userName || item.user_name,
          owner: item.userName || item.user_name,
        },
        ['name', 'owner', 'source', 'eventType', 'event_type'],
      )
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
    const user = reportUsers.value.find((row) => String(row.id) === String(filters.userId))
    const matchesUser = !filters.userId || [item.owner, item.manager, item.name].filter(Boolean).includes(user?.name)
    if (!matchesUser || !inPeriod(rowDate(item))) return false
    return matchesTopbar(item, ['title', 'description', 'owner', 'manager', 'name', 'department', 'status', 'type', 'summary', 'id'])
  })
})

const taskingKpis = computed(() => state.tasking.reports?.kpi || {})
const taskingDistribution = computed(() => state.tasking.reports?.distribution || {})

async function refreshTaskingReports() {
  const range = periodIsoRange()
  const topStart = topbarFilter.value.startDate
    ? (String(topbarFilter.value.startDate).includes('-') && Number(String(topbarFilter.value.startDate).slice(0, 4)) > 1500
      ? topbarFilter.value.startDate
      : jalaliToIso(topbarFilter.value.startDate))
    : ''
  const topEnd = topbarFilter.value.endDate
    ? (String(topbarFilter.value.endDate).includes('-') && Number(String(topbarFilter.value.endDate).slice(0, 4)) > 1500
      ? topbarFilter.value.endDate
      : jalaliToIso(topbarFilter.value.endDate))
    : ''
  await loadTaskingReports({
    start: topStart || range.start,
    end: topEnd || range.end,
    userId: filters.userId || '',
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
      { label: 'پاداش', value: row.bonusAmount || '-', icon: 'award_star' },
      { label: 'جریمه', value: row.penaltyAmount || '-', icon: 'gavel' },
      { label: 'خالص', value: row.netAdjustment || '-', icon: 'balance' },
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
      { label: 'پاداش', value: row.bonusAmount },
      { label: 'جریمه', value: row.penaltyAmount },
      { label: 'خالص پاداش/جریمه', value: row.netAdjustment },
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
  if (activeTab.value === 'users') return item.netAdjustment || '-'
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
    if (filters.userId) params.set('userId', filters.userId)
    const response = await fetch(`${API_BASE_URL}/attendance/reports?${params.toString()}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}` },
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(payload.detail || payload.message || 'بارگذاری گزارش ورود و خروج ناموفق بود.')
    attendanceRows.value = payload.rows || []
  } catch (error) {
    attendanceError.value = error.message || 'بارگذاری گزارش ورود و خروج ناموفق بود.'
    attendanceRows.value = []
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

function exportActiveTab() {
  if (activeTab.value === 'attendance') {
    exportAttendanceCsv()
    return
  }
  if (activeTab.value === 'tasking') {
    const range = periodIsoRange()
    const params = new URLSearchParams()
    if (range.start) params.set('start', range.start)
    if (range.end) params.set('end', range.end)
    exportReport('', 'csv', `/tasking/reports/export?${params.toString()}`)
    return
  }
  const params = new URLSearchParams({ format: 'csv', period: filters.period })
  if (filters.period === 'custom') {
    if (filters.startDate) params.set('startDate', jalaliToIso(filters.startDate))
    if (filters.endDate) params.set('endDate', jalaliToIso(filters.endDate))
  }
  if (filters.userId) params.set('userId', filters.userId)
  exportReport('', 'csv', `/reports/${activeTab.value}/export?${params.toString()}`)
}

watch(
  () => [
    activeTab.value,
    filters.period,
    filters.startDate,
    filters.endDate,
    filters.userId,
    topbarFilter.value.query,
    topbarFilter.value.person,
    topbarFilter.value.startDate,
    topbarFilter.value.endDate,
  ],
  () => {
    if (activeTab.value === 'attendance') void loadAttendanceReports()
    if (activeTab.value === 'tasking') void refreshTaskingReports()
  },
)

onMounted(() => {
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
      <div class="report-tabs">
        <button v-for="tab in tabs" :key="tab.key" :class="['report-tab', activeTab === tab.key && 'is-active']" type="button" @click="activeTab = tab.key">
          <IconlyIcon :name="tab.icon" decorative />
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <div class="report-filter-grid">
        <div class="chip-row report-period-chips">
          <button v-for="item in periods" :key="item.key" :class="['filter-chip', filters.period === item.key && 'is-active']" type="button" @click="filters.period = item.key">
            {{ item.label }}
          </button>
        </div>
        <label class="report-filter-field">
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
          <span>دانلود جدول</span>
        </button>
      </div>
      <div v-if="activeTab === 'attendance' && attendanceError" class="attendance-alert is-danger">{{ attendanceError }}</div>
    </section>

    <section v-if="activeTab === 'tasking'" class="metric-grid metric-grid-4">
      <article class="metric-card"><small>کاربران فعال</small><strong>{{ taskingKpis.activeUsers || 0 }}</strong></article>
      <article class="metric-card"><small>در محدوده هدف</small><strong>{{ taskingKpis.targetMetUsers || 0 }}</strong></article>
      <article class="metric-card"><small>کمتر از هدف</small><strong>{{ taskingKpis.underTargetUsers || 0 }}</strong></article>
      <article class="metric-card"><small>بیش از ظرفیت</small><strong>{{ taskingKpis.overloadedUsers || 0 }}</strong></article>
    </section>

    <section v-if="activeTab === 'tasking'" class="surface-block">
      <div class="chip-row">
        <button type="button" :class="['filter-chip', !taskingBandFilter && 'is-active']" @click="taskingBandFilter = ''">همه</button>
        <button type="button" :class="['filter-chip', taskingBandFilter === 'under' && 'is-active']" @click="taskingBandFilter = 'under'">کمتر از هدف ({{ taskingDistribution.under || 0 }})</button>
        <button type="button" :class="['filter-chip', taskingBandFilter === 'target' && 'is-active']" @click="taskingBandFilter = 'target'">در هدف ({{ taskingDistribution.target || 0 }})</button>
        <button type="button" :class="['filter-chip', taskingBandFilter === 'high' && 'is-active']" @click="taskingBandFilter = 'high'">بار بالا ({{ taskingDistribution.high || 0 }})</button>
        <button type="button" :class="['filter-chip', taskingBandFilter === 'over' && 'is-active']" @click="taskingBandFilter = 'over'">بیش از ظرفیت ({{ taskingDistribution.over || 0 }})</button>
      </div>
    </section>

    <section class="surface-block report-table-card">
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
            <tr v-else-if="activeTab === 'attendance'"><th>ردیف</th><th>پرسنل</th><th>سمت / بخش</th><th>نوع</th><th>منبع</th><th>تاریخ</th><th>ساعت</th><th>موقعیت</th><th>یادداشت</th></tr>
            <tr v-else-if="activeTab === 'tasking'"><th>نام</th><th>بخش</th><th>برنامه</th><th>هدف</th><th>واقعی</th><th>Utilization</th><th>وضعیت ظرفیت</th><th>تکمیل</th><th>عقب‌افتاده</th></tr>
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
                <td class="cell-mobile-primary">{{ row.title }}</td>
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
                <td class="cell-mobile-primary">{{ row.description }}</td>
                <td class="cell-mobile-hide">{{ row.owner }}</td>
                <td data-label="مبلغ">{{ row.amount }}</td>
                <td class="cell-mobile-hide">{{ row.department }}</td>
                <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(row.status)]">{{ row.status }}</span></td>
                <td data-label="تاریخ">{{ row.submittedAt }}</td>
                <td class="cell-mobile-hide">{{ decisionText(row) }}</td>
              </template>
              <template v-else-if="activeTab === 'approvals'">
                <td>{{ row.id }}</td><td>{{ row.title }}</td><td>{{ row.owner }}</td><td>{{ row.type }}</td><td>{{ row.department }}</td><td>{{ row.risk }}</td>
                <td><span :class="['status-badge', toneForStatus(row.status)]">{{ row.status }}</span></td>
                <td>{{ row.uploadedAt }}</td><td>{{ decisionText(row) }}</td>
              </template>
              <template v-else-if="activeTab === 'attendance'">
                <td>{{ row.row || row.id }}</td>
                <td>{{ row.userName }}</td>
                <td>{{ joinDisplayParts([row.userRole, row.userDepartment]) }}</td>
                <td><span :class="['status-badge', toneForStatus(attendanceStatus(row))]">{{ attendanceStatus(row) }}</span></td>
                <td>{{ sourceLabel(row.source) }}</td>
                <td>{{ row.eventDate ? isoToJalali(row.eventDate) : '-' }}</td>
                <td>{{ row.eventTime || '-' }}</td>
                <td>{{ row.distanceMeters != null ? `${Math.round(row.distanceMeters)} متر` : (row.coordinatesLabel || '-') }}</td>
                <td>{{ row.note || '-' }}</td>
              </template>
              <template v-else-if="activeTab === 'tasking'">
                <td class="cell-mobile-primary">{{ row.user?.name }}</td>
                <td class="cell-mobile-hide">{{ row.user?.department || '-' }}</td>
                <td>{{ row.plannedMinutes }}</td>
                <td>{{ row.targetMinutes }}</td>
                <td>{{ row.actualMinutes }}</td>
                <td data-label="Utilization">{{ row.utilizationPercent }}٪</td>
                <td data-label="وضعیت"><span class="status-badge">{{ row.bandLabel }}</span></td>
                <td>{{ row.completedCount }}</td>
                <td>{{ row.overdueCount }}</td>
              </template>
              <template v-else>
                <td>{{ row.id }}</td><td>{{ row.name }}</td><td>{{ row.username }}</td><td>{{ row.role }}</td><td>{{ row.department }}</td><td>{{ row.manager }}</td><td>{{ row.bonusAmount }}</td><td>{{ row.penaltyAmount }}</td><td>{{ row.netAdjustment }}</td>
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
.reports-page { gap: 16px; }
.report-controls { display: grid; gap: 14px; }
.report-tabs,
.report-filter-grid {
  display: flex;
  align-items: end;
  gap: 10px;
  flex-wrap: wrap;
}
.report-tab {
  min-height: 34px;
  border: 0;
  border-radius: 10px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #1f5c59;
  background: #e4f4f2;
  font-weight: 700;
  font-size: 0.8rem;
  cursor: pointer;
}
.report-tab.is-active {
  color: #fff;
  background: #34908B;
}
.report-period-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 36px;
}
.report-filter-field {
  display: grid;
  grid-template-rows: 18px 36px;
  gap: 6px;
  min-width: 180px;
  margin: 0;
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
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  padding: 0 12px !important;
  border: 0 !important;
  border-radius: 10px !important;
  background: #e4f4f2 !important;
  color: #152523;
  font: inherit;
  font-size: 0.82rem;
}
.report-filter-field :deep(.shamsi-picker),
.report-filter-field :deep(.shamsi-picker-input-wrap) {
  width: 100%;
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
}
.report-filter-field :deep(.shamsi-picker-input-wrap) {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  padding-inline: 12px 36px !important;
  padding-block: 0 !important;
  border-radius: 10px !important;
  background: #e4f4f2 !important;
}
.report-filter-field :deep(.shamsi-picker-input) {
  height: 100% !important;
  min-height: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  line-height: 36px;
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
  height: 36px !important;
  min-height: 36px !important;
  align-self: end;
}
.compact-field { min-width: 190px; margin: 0; }
.report-table-wrap { overflow-x: auto; }
.report-table { width: 100%; min-width: 980px; border-collapse: collapse; }
.report-table th, .report-table td { padding: 12px 10px; border-bottom: 1px solid rgba(38,56,92,.08); text-align: right; vertical-align: top; }
.report-table th { color: #52607a; font-size: 12px; }
.report-table td { color: #203255; line-height: 1.7; }
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
  overflow-wrap: anywhere;
}
.report-detail-title p {
  color: rgba(255, 255, 255, 0.76);
  line-height: 1.9;
  overflow-wrap: anywhere;
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
  overflow-wrap: anywhere;
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
  overflow-wrap: anywhere;
}
.decision-step small {
  margin-top: 4px;
  color: var(--muted);
}
.compact-empty {
  padding: 12px;
}
.report-detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}
@media (max-width: 760px) {
  .report-filter-grid,
  .report-tabs,
  .report-detail-hero {
    display: grid;
    grid-template-columns: 1fr;
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
  .report-detail-hero {
    padding: 18px;
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
