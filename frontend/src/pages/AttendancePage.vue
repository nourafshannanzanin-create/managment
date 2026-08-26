<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import LocationMapPicker from '../components/LocationMapPicker.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import SectionHeading from '../components/SectionHeading.vue'
import AttendancePeriodBoard from '../components/AttendancePeriodBoard.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { haversineDistanceMeters, readDeviceLocation } from '../lib/geolocation'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatJalali, formatTehranDate, formatTehranDateTime, formatTehranTime, getTehranClock, getTodayIso, getTodayJalali, isoToJalali, jalaliMonthStartIso, jalaliToIso, jalaliWeekStartIso } from '../utils/jalali'
import { exportAttendanceReportPdf } from '../utils/attendancePdfExport'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'

const route = useRoute()
const { state } = useWorkflowHub()
const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const search = ref('')
const statusFilter = ref('all')
const activeTab = ref('dashboard')
const note = ref('')
const dashboard = ref({ summary: {}, users: [], recentEvents: [], organization: {} })
const reportPayload = ref({ summary: {}, rows: [], dailyUserRows: [], users: [], personnelStats: [], dailyStats: [], departments: [] })
const reportFilters = ref({
  q: '',
  start: '',
  end: '',
  userId: '',
  eventType: 'all',
  source: 'all',
  department: '',
  rangeKey: '',
})
const publicPayload = ref({ user: {}, events: [], organization: {}, location: {} })
const isPublic = computed(() => Boolean(route.params.token))
const locationBusy = ref(false)
const locationHint = ref('')
const liveUserLocation = ref(null)
const liveDistanceMeters = ref(null)

const fa = (value) => Number(value || 0).toLocaleString('fa-IR')
const eventLabel = (type) => (type === 'in' ? 'ورود' : 'خروج')
const statusLabel = (type) => (type === 'in' ? 'حاضر' : 'خارج از شیفت')
const eventTone = (type) => (type === 'in' ? 'is-success' : 'is-warning')
const dateTime = (value) => {
  if (!value) return '-'
  return formatTehranDateTime(value)
}
const dateOnly = (value) => {
  if (!value) return '-'
  if (String(value).length === 10 && value.includes('-')) return isoToJalali(value) || value
  return formatTehranDate(value)
}
const timeOnly = (value) => {
  if (!value) return '-'
  if (String(value).length <= 5 && value.includes(':')) return toFaTime(value)
  return formatTehranTime(value)
}
const toFaTime = (value) => String(value || '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[digit] || digit)
const sourceLabel = (source) => (source === 'manager' ? 'ثبت مدیر' : 'لینک پرسنل')
const formatHours = (value) => {
  const hours = Number(value || 0)
  if (!hours) return '۰'
  const whole = Math.floor(hours)
  const minutes = Math.round((hours - whole) * 60)
  if (!minutes) return `${fa(whole)} ساعت`
  return `${fa(whole)}:${fa(String(minutes).padStart(2, '0'))} ساعت`
}
const formatShift = (row) => {
  const minutes = row.shiftMinutes ?? row.shift_minutes
  if (minutes == null) return '-'
  const whole = Math.floor(minutes / 60)
  const rest = Math.round(minutes % 60)
  if (!whole) return `${fa(rest)} دقیقه`
  if (!rest) return `${fa(whole)} ساعت`
  return `${fa(whole)}:${fa(String(rest).padStart(2, '0'))}`
}

const quickRanges = [
  { key: 'today', label: 'امروز' },
  { key: 'week', label: 'این هفته' },
  { key: 'month', label: 'این ماه' },
]

const publicLocation = computed(() => publicPayload.value.location || {})
const workplaceConfigured = computed(() => Boolean(publicLocation.value.configured))
const workplaceRadius = computed(() => publicLocation.value.radiusMeters || publicLocation.value.radius_meters || 20)
const withinRange = computed(() => {
  if (liveDistanceMeters.value == null) return null
  return liveDistanceMeters.value <= Number(workplaceRadius.value)
})
const workplaceMapModel = computed(() => ({
  latitude: publicLocation.value.latitude ?? null,
  longitude: publicLocation.value.longitude ?? null,
  label: publicLocation.value.label || '',
  radiusMeters: workplaceRadius.value,
  provinceId: publicLocation.value.provinceId ?? publicLocation.value.province_id ?? publicPayload.value.organization?.provinceId ?? null,
  provinceName: publicLocation.value.provinceName || publicLocation.value.province_name || publicPayload.value.organization?.provinceName || '',
  cityId: publicLocation.value.cityId ?? publicLocation.value.city_id ?? publicPayload.value.organization?.cityId ?? null,
  cityName: publicLocation.value.cityName || publicLocation.value.city_name || publicPayload.value.organization?.cityName || '',
}))

async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json'
  if (!isPublic.value) headers.Authorization = `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}`
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (response.status === 401 && !isPublic.value) {
    const { handleUnauthorizedSession } = useWorkflowHub()
    handleUnauthorizedSession()
    throw new Error('نشست منقضی شده است')
  }
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || payload.message || 'درخواست ناموفق بود.')
  return payload
}

const filteredUsers = computed(() => {
  const query = search.value.trim().toLowerCase()
  return (dashboard.value.users || []).filter((user) => {
    if (statusFilter.value !== 'all' && user.status !== statusFilter.value) return false
    if (!query) return true
    return [user.name, user.role, user.department, user.phone].some((field) => String(field || '').toLowerCase().includes(query))
  })
})

const publicUser = computed(() => publicPayload.value.user || {})
const publicEvents = computed(() => publicPayload.value.events || [])
const reportSummary = computed(() => reportPayload.value.summary || {})
const reportHighlightStats = computed(() => {
  const summary = reportSummary.value
  return [
    { label: 'کل رویدادها', value: fa(summary.total), note: `نمایش ${fa(summary.displayedRows || reportRows.value.length)} ردیف` },
    { label: 'پرسنل فعال', value: fa(summary.uniqueUsers), note: 'در بازه انتخاب‌شده' },
    { label: 'ورودها', value: fa(summary.checkins), note: 'ثبت ورود' },
    { label: 'خروج‌ها', value: fa(summary.checkouts), note: 'ثبت خروج' },
    { label: 'مجموع ساعات', value: formatHours(summary.totalWorkedHours), note: `میانگین ${formatHours(summary.avgWorkedHoursPerUser)}` },
    { label: 'شیفت باز', value: fa(summary.openShifts), note: 'ورود بدون خروج' },
  ]
})
const reportRows = computed(() => reportPayload.value.rows || [])
const reportUsers = computed(() => reportPayload.value.users || dashboard.value.users || [])
const reportDepartments = computed(() => reportPayload.value.departments || [])
const reportBoardMode = computed(() => {
  const todayIso = getTodayIso()
  const startIso = reportFilters.value.start ? jalaliToIso(reportFilters.value.start) : ''
  const endIso = reportFilters.value.end ? jalaliToIso(reportFilters.value.end) : ''
  if (reportFilters.value.rangeKey === 'today' || (startIso === todayIso && endIso === todayIso)) return 'today'
  return 'period'
})
const reportFilterLabel = computed(() => {
  const parts = []
  if (reportFilters.value.start || reportFilters.value.end) {
    parts.push(`${reportFilters.value.start || '…'} تا ${reportFilters.value.end || '…'}`)
  }
  if (reportFilters.value.userId) {
    const user = reportUsers.value.find((item) => String(item.id) === String(reportFilters.value.userId))
    if (user) parts.push(user.name)
  }
  if (reportFilters.value.department) parts.push(reportFilters.value.department)
  if (reportFilters.value.eventType !== 'all') parts.push(reportFilters.value.eventType === 'in' ? 'فقط ورود' : 'فقط خروج')
  if (reportFilters.value.source !== 'all') parts.push(reportFilters.value.source === 'manager' ? 'ثبت مدیر' : 'لینک پرسنل')
  if (reportFilters.value.q) parts.push(`جستجو: ${reportFilters.value.q}`)
  return parts.length ? parts.join(' · ') : 'همه رویدادهای ثبت‌شده'
})
const attendanceLink = (user) => `${window.location.origin}${user.attendancePath || user.attendance_path || `/attendance/${user.attendanceToken}`}`

async function loadDashboard() {
  loading.value = true
  errorMessage.value = ''
  try {
    dashboard.value = await apiFetch('/attendance/dashboard')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function loadReports() {
  loading.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams()
    if (reportFilters.value.q) params.set('q', reportFilters.value.q)
    const startIso = reportFilters.value.start ? jalaliToIso(reportFilters.value.start) : ''
    const endIso = reportFilters.value.end ? jalaliToIso(reportFilters.value.end) : ''
    if (startIso) params.set('start', startIso)
    if (endIso) params.set('end', endIso)
    if (reportFilters.value.userId) params.set('userId', reportFilters.value.userId)
    if (reportFilters.value.eventType !== 'all') params.set('eventType', reportFilters.value.eventType)
    if (reportFilters.value.source !== 'all') params.set('source', reportFilters.value.source)
    if (reportFilters.value.department) params.set('department', reportFilters.value.department)
    const query = params.toString()
    const payload = await apiFetch(`/attendance/reports${query ? `?${query}` : ''}`)
    const rows = payload.rows || []
    reportPayload.value = {
      ...payload,
      rows: rows.length
        ? rows
        : (payload.dailyUserRows || payload.daily_user_rows || []).flatMap((day) => day.events || []),
    }
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'reports') {
    if (!reportFilters.value.rangeKey) {
      applyQuickRange('today')
      return
    }
    await loadReports()
  }
}

function applyQuickRange(key) {
  const todayIso = getTodayIso()
  const todayJalali = formatJalali(getTodayJalali())
  reportFilters.value.rangeKey = key
  if (key === 'today') {
    reportFilters.value.start = todayJalali
    reportFilters.value.end = todayJalali
  } else if (key === 'week') {
    reportFilters.value.start = isoToJalali(jalaliWeekStartIso(todayIso))
    reportFilters.value.end = todayJalali
  } else if (key === 'month') {
    reportFilters.value.start = isoToJalali(jalaliMonthStartIso(todayIso))
    reportFilters.value.end = todayJalali
  }
  // Keep person / department / other filters — only the date window changes.
  void loadReports()
}

function onManualReportDateChange() {
  reportFilters.value.rangeKey = ''
}

function onReportPersonChange() {
  void loadReports()
}

function resetReportFilters() {
  reportFilters.value = { q: '', start: '', end: '', userId: '', eventType: 'all', source: 'all', department: '', rangeKey: '' }
  void loadReports()
}

function exportReportsCsv() {
  if (!reportRows.value.length) return
  const headers = [
    'ردیف', 'نام', 'سمت', 'بخش', 'موبایل', 'نوع', 'منبع', 'تاریخ', 'ساعت', 'مدت شیفت', 'GPS', 'فاصله(متر)', 'مختصات', 'یادداشت', 'ثبت سیستم',
  ]
  const lines = reportRows.value.map((row) => [
    row.row,
    row.userName,
    row.userRole || '',
    row.userDepartment || '',
    row.userPhone || '',
    eventLabel(row.eventType),
    sourceLabel(row.source),
    row.eventDate ? isoToJalali(row.eventDate) : dateOnly(row.eventAt),
    row.eventTime || timeOnly(row.eventAt),
    formatShift(row),
    row.hasGps ? (row.withinRadius ? 'داخل محدوده' : row.withinRadius === false ? 'خارج محدوده' : 'دارای GPS') : 'بدون GPS',
    row.distanceMeters ?? row.distance_meters ?? '',
    row.coordinatesLabel || '',
    (row.note || '').replace(/\n/g, ' '),
    dateTime(row.createdAt),
  ].map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
  const csv = `\uFEFF${headers.join(',')}\n${lines.join('\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `attendance-report-${formatJalali(getTodayJalali())}.csv`
  link.click()
  URL.revokeObjectURL(url)
  successMessage.value = 'فایل CSV گزارش دانلود شد.'
}

function exportReportsPdf() {
  if (!reportRows.value.length) return
  const ok = exportAttendanceReportPdf({
    events: reportRows.value,
    title: 'گزارش ورود و خروج',
    subtitle: reportFilterLabel.value,
    organizationName: dashboard.value.organization?.name || state.currentUser.organization || 'کارنومند',
  })
  successMessage.value = ok
    ? 'پیش‌نمایش PDF باز شد؛ از پنجره چاپ، ذخیره به‌صورت PDF را انتخاب کنید.'
    : 'باز کردن پنجره PDF ناموفق بود. اجازه پاپ‌آپ را بررسی کنید.'
}

async function refreshLiveLocation() {
  if (!workplaceConfigured.value) return
  locationBusy.value = true
  try {
    const coords = await readDeviceLocation({ forceRefresh: true, maximumAge: 0 })
    liveUserLocation.value = coords
    if (publicLocation.value.latitude != null && publicLocation.value.longitude != null) {
      liveDistanceMeters.value = haversineDistanceMeters(
        publicLocation.value.latitude,
        publicLocation.value.longitude,
        coords.latitude,
        coords.longitude,
      )
      locationHint.value = withinRange.value
        ? `داخل محدوده مجاز هستید · فاصله حدود ${fa(Math.round(liveDistanceMeters.value))} متر`
        : `خارج از محدوده · فاصله حدود ${fa(Math.round(liveDistanceMeters.value))} متر از ${fa(workplaceRadius.value)} متر مجاز`
    }
  } catch (error) {
    locationHint.value = error.message
  } finally {
    locationBusy.value = false
  }
}

async function loadPublic() {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  locationHint.value = ''
  try {
    publicPayload.value = await apiFetch(`/attendance/public/${route.params.token}`)
    if (!workplaceConfigured.value) {
      locationHint.value = 'لوکیشن محل کار توسط مدیر مجموعه تنظیم نشده است.'
    } else {
      locationHint.value = `برای ثبت ورود/خروج باید در شعاع ${fa(workplaceRadius.value)} متری محل کار باشید. ابتدا دکمه «اجازه موقعیت» را بزنید.`
      // iOS Safari only prompts geolocation after a user gesture — do not auto-request here.
    }
  } catch (error) {
    errorMessage.value = error.message
    publicPayload.value = { user: {}, events: [], organization: {}, location: {} }
  } finally {
    loading.value = false
  }
}

async function submitManagerEvent(user, eventType) {
  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    dashboard.value = await apiFetch('/attendance/events', {
      method: 'POST',
      body: JSON.stringify({
        userId: user.id,
        eventType,
        eventAt: `${getTodayIso()}T${getTehranClock()}:00`,
      }),
    })
    successMessage.value = eventType === 'in' ? 'ورود ثبت شد.' : 'خروج ثبت شد.'
    if (activeTab.value === 'reports') await loadReports()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

async function submitPublicEvent(eventType) {
  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    if (!workplaceConfigured.value) {
      throw new Error('لوکیشن محل کار توسط مدیر مجموعه تنظیم نشده است.')
    }
    // Reuse recent location when possible to avoid repeated GPS prompts.
    let coords = liveUserLocation.value
    const ageMs = coords?.capturedAt ? Date.now() - coords.capturedAt : Infinity
    if (!coords || ageMs > 120000) {
      locationBusy.value = true
      coords = await readDeviceLocation({ maximumAge: 120000, enableHighAccuracy: false })
      liveUserLocation.value = coords
    }
    if (publicLocation.value.latitude != null && publicLocation.value.longitude != null) {
      liveDistanceMeters.value = haversineDistanceMeters(
        publicLocation.value.latitude,
        publicLocation.value.longitude,
        coords.latitude,
        coords.longitude,
      )
    }
    publicPayload.value = await apiFetch(`/attendance/public/${route.params.token}`, {
      method: 'POST',
      body: JSON.stringify({
        eventType,
        note: note.value,
        latitude: coords.latitude,
        longitude: coords.longitude,
      }),
    })
    const lastEvent = (publicPayload.value.events || [])[0]
    const distance = lastEvent?.distanceMeters ?? lastEvent?.distance_meters ?? liveDistanceMeters.value
    const distanceText = distance != null ? ` · فاصله ${fa(Math.round(distance))} متر` : ''
    successMessage.value = `${eventLabel(eventType)} با موفقیت ثبت شد${distanceText}.`
    note.value = ''
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
    locationBusy.value = false
  }
}

async function copyLink(user) {
  await navigator.clipboard.writeText(attendanceLink(user))
  successMessage.value = 'لینک ورود و خروج کپی شد.'
}

watch(
  () => state.liveSync?.tick,
  () => {
    if (isPublic.value) return
    if (activeTab.value === 'reports') void loadReports()
    else void loadDashboard()
  },
)

onMounted(() => {
  if (isPublic.value) void loadPublic()
  else void loadDashboard()
})
</script>

<template>
  <section v-if="!isPublic" class="page-shell attendance-page">
    <section class="attendance-hero">
      <div>
        <span class="page-eyebrow">Attendance Control</span>
        <h1>ورود و خروج پرسنل</h1>
      </div>
      <div class="attendance-summary">
        <article class="attendance-summary-tile is-present-summary">
          <span class="attendance-summary-icon" aria-hidden="true">
            <IconlyIcon name="groups" decorative />
          </span>
          <div class="attendance-summary-body">
            <span>حاضر</span>
            <strong>{{ fa(dashboard.summary?.presentCount) }}</strong>
            <small>در شیفت</small>
          </div>
        </article>
        <article class="attendance-summary-tile is-away-summary">
          <span class="attendance-summary-icon" aria-hidden="true">
            <IconlyIcon name="logout" decorative />
          </span>
          <div class="attendance-summary-body">
            <span>خارج</span>
            <strong>{{ fa(dashboard.summary?.absentCount) }}</strong>
            <small>خارج از شیفت</small>
          </div>
        </article>
        <article class="attendance-summary-tile is-hours-summary">
          <span class="attendance-summary-icon" aria-hidden="true">
            <IconlyIcon name="graph" decorative />
          </span>
          <div class="attendance-summary-body">
            <span>ساعت امروز</span>
            <strong>{{ formatHours(dashboard.summary?.todayWorkedHours) }}</strong>
            <small>مجموع کارکرد</small>
          </div>
        </article>
      </div>
    </section>

    <div v-if="errorMessage" class="attendance-alert is-danger">{{ errorMessage }}</div>
    <div v-if="successMessage" class="attendance-alert is-success">{{ successMessage }}</div>

    <section class="attendance-tabs">
      <button :class="['attendance-tab', activeTab === 'dashboard' && 'is-active']" type="button" @click="switchTab('dashboard')">
        <IconlyIcon name="space_dashboard" decorative />
        <span>داشبورد</span>
      </button>
      <button :class="['attendance-tab', activeTab === 'reports' && 'is-active']" type="button" @click="switchTab('reports')">
        <IconlyIcon name="table_chart" decorative />
        <span>گزارشات</span>
      </button>
    </section>

    <template v-if="activeTab === 'dashboard'">
    <section class="attendance-toolbar attendance-toolbar-modern">
      <label class="search-shell search-shell-wide">
        <IconlyIcon name="search" decorative />
        <input v-model="search" type="text" placeholder="جستجو در نام، سمت، بخش یا موبایل..." />
      </label>
      <label class="field-shell attendance-status-field">
        <span>وضعیت</span>
        <select v-model="statusFilter">
          <option value="all">همه</option>
          <option value="in">حاضر</option>
          <option value="out">خارج از شیفت</option>
        </select>
      </label>
      <button class="action-btn tone-soft attendance-refresh-btn" type="button" @click="loadDashboard">
        <IconlyIcon name="refresh" decorative />
        <span>بروزرسانی</span>
      </button>
    </section>

    <section class="attendance-layout">
      <div class="attendance-users">
        <article
          v-for="user in filteredUsers"
          :key="user.id"
          :class="['attendance-staff-card', user.status === 'in' ? 'is-present' : 'is-away']"
        >
          <div class="attendance-staff-banner" aria-hidden="true" />

          <header class="attendance-staff-head">
            <div class="attendance-staff-identity">
              <UserAvatar
                :name="user.name"
                :avatar="user.avatar"
                :avatar-url="user.avatarUrl || user.avatar_url"
                size="md"
              />
              <div class="attendance-staff-copy">
                <strong>{{ user.name }}</strong>
                <small>{{ user.role }} · {{ user.department }}</small>
              </div>
            </div>
            <span :class="['attendance-staff-status', eventTone(user.status)]">
              <span class="attendance-staff-status-dot" aria-hidden="true" />
              {{ statusLabel(user.status) }}
            </span>
          </header>

          <section class="attendance-staff-stats" aria-label="خلاصه امروز">
            <article class="attendance-staff-stat is-events">
              <span class="attendance-staff-stat-icon" aria-hidden="true">
                <IconlyIcon name="fingerprint" decorative />
              </span>
              <div class="attendance-staff-stat-body">
                <span>ثبت امروز</span>
                <strong>{{ fa(user.todayEventsCount) }}</strong>
                <small>ورود / خروج</small>
              </div>
            </article>
            <article class="attendance-staff-stat is-hours">
              <span class="attendance-staff-stat-icon" aria-hidden="true">
                <IconlyIcon name="graph" decorative />
              </span>
              <div class="attendance-staff-stat-body">
                <span>ساعت امروز</span>
                <strong>{{ formatHours(user.todayWorkedHours) }}</strong>
                <small>کارکرد خالص</small>
              </div>
            </article>
          </section>

          <div class="attendance-staff-linkbar">
            <div class="attendance-staff-link-copy">
              <span>لینک اختصاصی پرسنل</span>
              <code class="attendance-staff-link" :title="attendanceLink(user)">{{ attendanceLink(user) }}</code>
            </div>
            <button class="attendance-staff-icon-btn" type="button" title="کپی لینک" @click="copyLink(user)">
              <IconlyIcon name="content_copy" decorative />
            </button>
            <a class="attendance-staff-icon-btn" title="باز کردن لینک" :href="attendanceLink(user)" target="_blank" rel="noreferrer">
              <IconlyIcon name="open_in_new" decorative />
            </a>
          </div>

          <footer class="attendance-staff-footer">
            <div class="attendance-staff-actions">
              <button
                class="attendance-staff-punch is-in"
                type="button"
                :disabled="submitting || user.status === 'in'"
                @click="submitManagerEvent(user, 'in')"
              >
                <IconlyIcon name="login" decorative />
                <span>ثبت ورود</span>
              </button>
              <button
                class="attendance-staff-punch is-out"
                type="button"
                :disabled="submitting || user.status !== 'in'"
                @click="submitManagerEvent(user, 'out')"
              >
                <IconlyIcon name="logout" decorative />
                <span>ثبت خروج</span>
              </button>
            </div>
          </footer>
        </article>
      </div>

      <aside class="surface-block attendance-feed">
        <div class="section-label-row">
          <SectionHeading
            title="آخرین رویدادها"
            description="ورود و خروج‌های اخیر پرسنل برای پایش سریع وضعیت حضور."
          />
        </div>
        <article v-for="event in dashboard.recentEvents || []" :key="event.id" class="attendance-feed-row">
          <span :class="['feed-dot', event.eventType]"></span>
          <div>
            <strong>{{ event.userName }}</strong>
            <small>{{ eventLabel(event.eventType) }} · {{ dateTime(event.eventAt) }}</small>
          </div>
        </article>
        <div v-if="!loading && !(dashboard.recentEvents || []).length" class="empty-state-inline">هنوز رویدادی ثبت نشده است.</div>
      </aside>
    </section>
    </template>

    <template v-else>
      <section class="attendance-report-panel">
        <section class="report-hero">
          <div>
            <span class="page-eyebrow">Attendance Reports</span>
            <h2>گزارشات ورود و خروج</h2>
            <p>{{ reportFilterLabel }}</p>
          </div>
          <div class="report-hero-actions">
            <button class="action-btn tone-soft" type="button" :disabled="loading" @click="loadReports">
              <IconlyIcon name="refresh" decorative />
              <span>بروزرسانی</span>
            </button>
            <button class="action-btn tone-soft" type="button" :disabled="!reportRows.length" @click="exportReportsCsv">
              <IconlyIcon name="download" decorative />
              <span>خروجی CSV</span>
            </button>
            <button class="action-btn tone-primary" type="button" :disabled="!reportRows.length" @click="exportReportsPdf">
              <IconlyIcon name="picture_as_pdf" decorative />
              <span>خروجی PDF</span>
            </button>
          </div>
        </section>

        <div class="report-range-bar">
          <button
            v-for="range in quickRanges"
            :key="range.key"
            :class="['report-range-chip', reportFilters.rangeKey === range.key && 'is-active']"
            type="button"
            @click="applyQuickRange(range.key)"
          >
            {{ range.label }}
          </button>
        </div>

        <div class="report-filter-grid">
          <label class="search-shell search-shell-wide">
            <IconlyIcon name="search" decorative />
            <input v-model="reportFilters.q" type="text" placeholder="جستجو در نام، سمت، بخش، موبایل یا یادداشت..." @keyup.enter="loadReports" />
          </label>
          <label class="field-shell">
            <span>از تاریخ</span>
            <ShamsiDatePicker v-model="reportFilters.start" model-type="jalali" placeholder="1405/04/01" @update:model-value="onManualReportDateChange" />
          </label>
          <label class="field-shell">
            <span>تا تاریخ</span>
            <ShamsiDatePicker v-model="reportFilters.end" model-type="jalali" placeholder="1405/04/31" @update:model-value="onManualReportDateChange" />
          </label>
          <label class="field-shell">
            <span>پرسنل</span>
            <select v-model="reportFilters.userId" @change="onReportPersonChange">
              <option value="">همه پرسنل</option>
              <option v-for="user in reportUsers" :key="user.id" :value="user.id">{{ user.name }}</option>
            </select>
          </label>
          <label class="field-shell">
            <span>بخش</span>
            <select v-model="reportFilters.department">
              <option value="">همه بخش‌ها</option>
              <option v-for="department in reportDepartments" :key="department" :value="department">{{ department }}</option>
            </select>
          </label>
          <label class="field-shell">
            <span>نوع رویداد</span>
            <select v-model="reportFilters.eventType">
              <option value="all">همه</option>
              <option value="in">ورود</option>
              <option value="out">خروج</option>
            </select>
          </label>
          <label class="field-shell">
            <span>منبع ثبت</span>
            <select v-model="reportFilters.source">
              <option value="all">همه</option>
              <option value="link">لینک پرسنل</option>
              <option value="manager">ثبت مدیر</option>
            </select>
          </label>
          <button class="action-btn tone-primary" type="button" @click="loadReports">
            <IconlyIcon name="manage_search" decorative />
            <span>اعمال فیلتر</span>
          </button>
          <button class="action-btn tone-soft" type="button" @click="resetReportFilters">
            <IconlyIcon name="filter_alt_off" decorative />
            <span>حذف فیلتر</span>
          </button>
        </div>

        <div class="report-summary-grid report-summary-grid-wide">
          <article v-for="item in reportHighlightStats" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.note }}</small>
          </article>
        </div>

        <div v-if="reportSummary.truncated || reportSummary.statsTruncated" class="attendance-alert is-info report-truncation-note">
          <template v-if="reportSummary.truncated">جدول تا {{ fa(reportSummary.displayedRows || 500) }} رویداد آخر نمایش داده می‌شود.</template>
          <template v-if="reportSummary.statsTruncated"> آمار تجمیعی بر اساس {{ fa(reportSummary.statsSampleSize || 5000) }} رویداد اول محاسبه شده است.</template>
        </div>

        <AttendancePeriodBoard
          :events="reportRows"
          :mode="reportBoardMode"
          :loading="loading"
          :can-edit-times="true"
          @updated="loadReports"
        />
      </section>
    </template>
  </section>

  <main v-else class="attendance-public" dir="rtl">
    <div class="attendance-public-inner">
      <section class="attendance-public-card">
        <div v-if="loading && !publicUser.id" class="attendance-public-loading">
          <span class="attendance-public-spinner" aria-hidden="true"></span>
          در حال بارگذاری لینک ورود و خروج…
        </div>

        <template v-else-if="errorMessage && !publicUser.id">
          <div class="attendance-alert is-danger">{{ errorMessage }}</div>
          <p class="attendance-public-hint">اگر لینک را از مدیر دریافت کرده‌اید، دوباره امتحان کنید یا لینک تازه بخواهید.</p>
        </template>

        <template v-else>
          <header class="attendance-public-head">
            <div class="attendance-public-identity">
              <UserAvatar
                :name="publicUser.name"
                :avatar="publicUser.avatar"
                :avatar-url="publicUser.avatarUrl || publicUser.avatar_url"
                size="lg"
              />
              <div>
                <span class="page-eyebrow">ثبت ورود و خروج</span>
                <h1>{{ publicUser.name || 'پرسنل' }}</h1>
                <p>
                  {{ publicPayload.organization?.name || 'سازمان' }}
                  <template v-if="publicUser.department"> · {{ publicUser.department }}</template>
                </p>
              </div>
            </div>
            <span :class="['status-badge status-badge-lg', eventTone(publicUser.status)]">{{ statusLabel(publicUser.status) }}</span>
          </header>

          <div class="public-quick-stats">
            <article class="is-events">
              <span class="public-quick-stat-icon" aria-hidden="true">
                <IconlyIcon name="fingerprint" decorative />
              </span>
              <div>
                <span>ثبت امروز</span>
                <strong>{{ fa(publicUser.todayEventsCount) }}</strong>
                <small>ورود / خروج</small>
              </div>
            </article>
            <article class="is-hours">
              <span class="public-quick-stat-icon" aria-hidden="true">
                <IconlyIcon name="graph" decorative />
              </span>
              <div>
                <span>ساعت امروز</span>
                <strong>{{ formatHours(publicUser.todayWorkedHours) }}</strong>
                <small>کارکرد خالص</small>
              </div>
            </article>
          </div>

          <div v-if="errorMessage" class="attendance-alert is-danger">{{ errorMessage }}</div>
          <div v-if="successMessage" class="attendance-alert is-success">{{ successMessage }}</div>
          <div
            v-if="locationHint"
            :class="[
              'attendance-alert location-status-card',
              !workplaceConfigured ? 'is-warning' : withinRange === false ? 'is-danger' : withinRange ? 'is-success' : 'is-info',
            ]"
          >
            {{ locationHint }}
          </div>

          <div v-if="workplaceConfigured" class="public-map-block">
            <LocationMapPicker
              :model-value="workplaceMapModel"
              mode="viewer"
              height="280px"
              :can-edit="false"
              :show-radius="true"
              :user-location="liveUserLocation"
            />
            <button class="action-btn tone-primary public-locate-btn" type="button" :disabled="locationBusy || submitting" @click="refreshLiveLocation">
              <IconlyIcon name="profile" decorative />
              <span>{{ locationBusy ? 'در حال دریافت موقعیت...' : (liveUserLocation ? 'بروزرسانی موقعیت من' : 'اجازه موقعیت و یافتن من') }}</span>
            </button>
          </div>

          <div v-if="publicUser.id" class="attendance-public-dock">
            <div class="attendance-punch-grid">
              <button
                class="attendance-punch-btn is-in"
                type="button"
                :disabled="submitting || !workplaceConfigured || publicUser.status === 'in'"
                @click="submitPublicEvent('in')"
              >
                <span class="attendance-punch-glow" aria-hidden="true" />
                <span class="attendance-punch-icon">
                  <IconlyIcon name="login" size="xl" decorative />
                </span>
                <span class="attendance-punch-copy">
                  <strong>{{ submitting && publicUser.status !== 'in' ? 'در حال ثبت...' : 'ثبت ورود' }}</strong>
                  <small>{{ publicUser.status === 'in' ? 'الان حاضر هستید' : 'شروع شیفت کاری' }}</small>
                </span>
              </button>
              <button
                class="attendance-punch-btn is-out"
                type="button"
                :disabled="submitting || !workplaceConfigured || publicUser.status !== 'in'"
                @click="submitPublicEvent('out')"
              >
                <span class="attendance-punch-glow" aria-hidden="true" />
                <span class="attendance-punch-icon">
                  <IconlyIcon name="logout" size="xl" decorative />
                </span>
                <span class="attendance-punch-copy">
                  <strong>{{ submitting && publicUser.status === 'in' ? 'در حال ثبت...' : 'ثبت خروج' }}</strong>
                  <small>{{ publicUser.status === 'in' ? 'پایان شیفت کاری' : 'ابتدا ورود ثبت کنید' }}</small>
                </span>
              </button>
            </div>
          </div>

          <label class="public-note">
            <span>یادداشت (اختیاری)</span>
            <textarea v-model="note" rows="2" placeholder="مثلا شروع شیفت عصر یا خروج برای ماموریت کوتاه"></textarea>
          </label>

          <div class="public-timeline">
            <h2 class="public-timeline-title">رویدادهای امروز</h2>
            <p v-if="!publicEvents.length" class="attendance-public-hint">هنوز رویدادی برای امروز ثبت نشده است.</p>
            <article v-for="event in publicEvents" :key="event.id">
              <span :class="['feed-dot', event.eventType || event.event_type]"></span>
              <div>
                <strong>{{ eventLabel(event.eventType || event.event_type) }}</strong>
                <small>{{ dateTime(event.eventAt || event.event_at) }}</small>
                <small
                  v-if="(event.distanceMeters ?? event.distance_meters) != null"
                  class="public-event-note"
                >
                  فاصله از محل کار: {{ fa(Math.round(event.distanceMeters ?? event.distance_meters)) }} متر
                </small>
                <small v-if="event.note" class="public-event-note">{{ event.note }}</small>
              </div>
            </article>
          </div>
        </template>
      </section>
    </div>
  </main>
</template>

<style scoped>
.attendance-page {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.attendance-hero {
  display: grid;
  grid-template-columns: minmax(160px, 0.75fr) minmax(0, 1.35fr);
  gap: 16px;
  padding: 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(228, 244, 242, 0.92), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(52, 144, 139, 0.14);
  box-shadow: none;
  min-width: 0;
}

.attendance-hero > div { min-width: 0; }

.attendance-hero h1 {
  margin: 8px 0 0;
  color: var(--primary);
  font-size: clamp(1.35rem, 3vw, 2rem);
  line-height: 1.35;
  overflow-wrap: break-word;
}

.attendance-summary,
.public-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  min-width: 0;
}

.attendance-summary-tile,
.public-stats article {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  min-width: 0;
  min-height: 92px;
  padding: 14px 14px 14px 12px;
  border-radius: 18px;
  background: rgba(52, 144, 139, 0.06);
  border: 1px solid rgba(52, 144, 139, 0.12);
  box-shadow: none;
  overflow: hidden;
}

.attendance-summary-tile::after {
  content: '';
  position: absolute;
  inset-inline-start: 0;
  top: 16px;
  bottom: 16px;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg, #34908b, #1f5c59);
}

.attendance-summary-tile.is-present-summary {
  background: rgba(31, 138, 112, 0.08);
  border-color: rgba(31, 138, 112, 0.16);
}

.attendance-summary-tile.is-present-summary::after {
  background: linear-gradient(180deg, #2bb89a, #1f8a70);
}

.attendance-summary-tile.is-away-summary {
  background: rgba(200, 115, 42, 0.08);
  border-color: rgba(200, 115, 42, 0.16);
}

.attendance-summary-tile.is-away-summary::after {
  background: linear-gradient(180deg, #e0a35d, #c8732a);
}

.attendance-summary-tile.is-hours-summary {
  background:
    radial-gradient(circle at 100% 0%, rgba(52, 144, 139, 0.18), transparent 46%),
    linear-gradient(160deg, #ffffff 0%, #eaf6f5 100%);
}

.attendance-summary-icon {
  width: 44px;
  height: 44px;
  display: inline-grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(31, 92, 89, 0.08);
  color: #1f5c59;
  box-shadow: none;
}

.attendance-summary-tile.is-present-summary .attendance-summary-icon {
  background: rgba(31, 138, 112, 0.14);
  color: #145f52;
}

.attendance-summary-tile.is-away-summary .attendance-summary-icon {
  background: rgba(200, 115, 42, 0.14);
  color: #8a4b12;
}

.attendance-summary-body {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.attendance-summary-body span,
.public-stats span {
  display: block;
  color: #5f7a76;
  font-size: 12px;
  font-weight: 750;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendance-summary-body strong,
.public-stats strong {
  display: block;
  color: #123735;
  font-size: clamp(1.25rem, 2.6vw, 1.7rem);
  font-weight: 900;
  line-height: 1.15;
  letter-spacing: -0.03em;
  overflow-wrap: anywhere;
}

.attendance-summary-body small {
  display: block;
  color: #7a9490;
  font-size: 10px;
  font-weight: 650;
}

.attendance-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 4px;
  border-radius: 14px;
  background: rgba(52, 144, 139, 0.08);
  border: 1px solid rgba(52, 144, 139, 0.1);
  box-shadow: none;
  max-width: 420px;
}

.attendance-tab {
  min-height: 42px;
  min-width: 0;
  padding: 0 14px;
  border: 0;
  border-radius: 11px;
  background: transparent;
  color: #45605c;
  font: inherit;
  font-weight: 750;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: none;
}

.attendance-tab span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendance-tab.is-active {
  color: #fff;
  background: var(--button-primary-bg, #34908B);
  border-color: transparent;
}

.attendance-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(150px, 200px) auto;
  gap: 12px;
  align-items: stretch;
  min-width: 0;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  background: rgba(52, 144, 139, 0.04);
  box-shadow: none;
}

.attendance-toolbar > * { min-width: 0; }

.attendance-toolbar .search-shell,
.attendance-toolbar .field-shell {
  min-height: 52px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(255, 255, 255, 0.94);
}

.attendance-toolbar .attendance-refresh-btn {
  min-height: 52px;
  padding-inline: 16px;
  white-space: nowrap;
}
.attendance-report-panel { display: grid; gap: 14px; min-width: 0; }

.report-filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
  align-items: stretch;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(247, 251, 250, 0.9);
  box-shadow: none;
}

.report-filter-grid > * { min-width: 0; }
.report-filter-grid .search-shell-wide { grid-column: 1 / -1; }

.report-filter-grid .field-shell,
.report-filter-grid .search-shell {
  min-height: 44px;
  padding: 7px 10px;
  border-radius: 12px;
  box-shadow: none;
}

.report-filter-grid .field-shell span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-filter-grid input,
.report-filter-grid select {
  width: 100%;
  min-width: 0;
}

.report-filter-grid .action-btn {
  min-height: 52px;
  width: 100%;
  justify-content: center;
}

.report-summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.report-summary-grid article {
  min-width: 0;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--line);
}

.report-summary-grid span {
  display: block;
  color: var(--muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-summary-grid strong {
  display: block;
  margin-top: 8px;
  color: var(--primary);
  font-size: clamp(1.05rem, 2.5vw, 1.4rem);
  overflow-wrap: anywhere;
}

.report-summary-grid article small {
  display: block;
  margin-top: 6px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.5;
}

.report-summary-grid-wide {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.report-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(220, 239, 236, 0.95), rgba(255, 255, 255, 0.92));
  border: 1px solid var(--line);
}

.report-hero h2 {
  margin: 8px 0 6px;
  color: var(--primary);
  font-size: clamp(1.25rem, 3vw, 1.75rem);
}

.report-hero p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
  font-size: 0.92rem;
}

.report-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex: 0 0 auto;
}

.report-range-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.report-range-chip {
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.82);
  color: var(--primary);
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.report-range-chip.is-active {
  background: var(--button-primary-bg, #34908B);
  border-color: transparent;
  color: #fff;
}

.report-truncation-note {
  font-size: 0.88rem;
  line-height: 1.65;
}

.report-view-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.report-view-tab {
  min-height: 42px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.78);
  color: var(--primary);
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.report-view-tab.is-active {
  background: var(--button-primary-bg, #34908B);
  border-color: transparent;
  color: #fff;
}

.report-table-subtitle {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.report-cell-sub {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.4;
}

.report-gps-pill {
  display: inline-flex;
  align-items: center;
  max-width: 180px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(36, 59, 107, 0.06);
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
  white-space: normal;
}

.report-gps-pill.is-ok {
  background: var(--success-soft);
  color: var(--success);
}

.report-gps-pill.is-bad {
  background: var(--danger-soft);
  color: var(--danger);
}

.report-gps-pill.is-muted {
  background: rgba(36, 59, 107, 0.05);
  color: var(--muted);
}

.report-note-cell {
  max-width: 180px;
  white-space: normal;
  line-height: 1.5;
  font-size: 12px;
}

.report-expand-btn {
  width: 34px;
  height: 34px;
}

.report-row-detail td {
  background: rgba(220, 239, 236, 0.35);
  padding-top: 0;
}

.report-detail-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  padding: 4px 0 8px;
}

.report-detail-grid article {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--line);
}

.report-detail-grid span {
  display: block;
  color: var(--muted);
  font-size: 11px;
}

.report-detail-grid strong {
  display: block;
  margin-top: 6px;
  color: var(--primary);
  font-size: 13px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.report-detail-wide {
  grid-column: 1 / -1;
}

.attendance-report-table-detailed {
  min-width: 1100px;
}

.report-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.report-event-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--line);
}

.report-event-card.card-tone-in {
  border-color: rgba(52, 144, 139, 0.24);
  background: linear-gradient(180deg, rgba(236, 250, 245, 0.98), rgba(255, 255, 255, 0.94));
}

.report-event-card.card-tone-out {
  border-color: rgba(245, 158, 11, 0.24);
  background: linear-gradient(180deg, rgba(255, 248, 232, 0.98), rgba(255, 255, 255, 0.94));
}

.report-event-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.report-event-card-head strong {
  display: block;
  color: var(--primary);
}

.report-event-card-head small {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
}

.report-event-card-meta {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
}

.report-event-card-meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.report-event-card-note {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(36, 59, 107, 0.04);
  color: var(--text);
  font-size: 12px;
  line-height: 1.6;
}

.report-event-card-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(36, 59, 107, 0.08);
}

.report-event-card-foot small {
  color: var(--muted);
  font-size: 11px;
}

.report-table-card { display: grid; gap: 14px; min-width: 0; }
.report-table-head { align-items: center; }

.table-count {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: rgba(36, 59, 107, 0.08);
  color: var(--primary);
  font-weight: 800;
  font-size: 12px;
}

.attendance-table-wrap {
  overflow: auto;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.56);
  -webkit-overflow-scrolling: touch;
}

.attendance-report-table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
}

.attendance-report-table th,
.attendance-report-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(36, 59, 107, 0.08);
  text-align: right;
  vertical-align: middle;
}

.attendance-report-table th {
  color: var(--muted);
  font-size: 12px;
  background: rgba(216, 175, 140, 0.16);
  white-space: nowrap;
}

.attendance-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 340px);
  gap: 16px;
  align-items: start;
  min-width: 0;
}

.attendance-users {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  min-width: 0;
}

.attendance-staff-card {
  position: relative;
  display: grid;
  gap: 14px;
  min-width: 0;
  padding: 0;
  border-radius: 22px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(52, 144, 139, 0.12);
  box-shadow: none;
  backdrop-filter: blur(8px);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.attendance-staff-card:hover {
  border-color: rgba(52, 144, 139, 0.22);
  background: rgba(255, 255, 255, 0.82);
}

.attendance-staff-banner {
  height: 6px;
  background: linear-gradient(90deg, #9bb5b1, #c5d4d1);
}

.attendance-staff-card.is-present .attendance-staff-banner {
  background: linear-gradient(90deg, #1f8a70, #34908b 55%, #2bb89a);
}

.attendance-staff-card.is-away .attendance-staff-banner {
  background: linear-gradient(90deg, #c8732a, #e0a35d 60%, #f0c48a);
}

.attendance-staff-head,
.attendance-staff-stats,
.attendance-staff-linkbar,
.attendance-staff-footer {
  padding-inline: 16px;
}

.attendance-staff-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-top: 14px;
}

.attendance-staff-identity {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.attendance-staff-copy {
  min-width: 0;
  display: grid;
  gap: 3px;
}

.attendance-staff-copy strong,
.attendance-staff-copy small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendance-staff-copy strong {
  color: #152523;
  font-size: 1.02rem;
  font-weight: 800;
}

.attendance-staff-copy small {
  color: #5f7a76;
  font-size: 12px;
  font-weight: 600;
}

.attendance-staff-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.attendance-staff-status.is-success {
  background: rgba(31, 138, 112, 0.12);
  color: #145f52;
  border: 1px solid rgba(31, 138, 112, 0.2);
}

.attendance-staff-status.is-warning {
  background: rgba(200, 115, 42, 0.12);
  color: #8a4b12;
  border: 1px solid rgba(200, 115, 42, 0.22);
}

.attendance-staff-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.attendance-staff-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.attendance-staff-stat {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  min-width: 0;
  min-height: 86px;
  padding: 12px;
  border-radius: 18px;
  background: rgba(52, 144, 139, 0.06);
  border: 1px solid rgba(52, 144, 139, 0.1);
  box-shadow: none;
  overflow: hidden;
}

.attendance-staff-stat.is-events {
  background: rgba(31, 138, 112, 0.08);
  border-color: rgba(31, 138, 112, 0.14);
}

.attendance-staff-stat.is-hours {
  background: rgba(52, 144, 139, 0.08);
  border-color: rgba(52, 144, 139, 0.14);
}

.attendance-staff-stat-icon {
  width: 42px;
  height: 42px;
  display: inline-grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(31, 92, 89, 0.08);
  color: #1f5c59;
  box-shadow: none;
}

.attendance-staff-stat.is-events .attendance-staff-stat-icon {
  background: rgba(31, 138, 112, 0.12);
  color: #145f52;
}

.attendance-staff-stat.is-hours .attendance-staff-stat-icon {
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
}

.attendance-staff-stat-body {
  min-width: 0;
  display: grid;
  gap: 1px;
}

.attendance-staff-stat-body span {
  color: #5f7a76;
  font-size: 11px;
  font-weight: 750;
}

.attendance-staff-stat-body strong {
  color: #123735;
  font-size: clamp(1.15rem, 2.4vw, 1.45rem);
  font-weight: 900;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.attendance-staff-stat-body small {
  color: #7a9490;
  font-size: 10px;
  font-weight: 650;
}

.attendance-staff-linkbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 8px;
  align-items: center;
  padding: 10px 12px;
  margin-inline: 16px;
  border-radius: 14px;
  background: rgba(31, 92, 89, 0.05);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.attendance-staff-link-copy {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.attendance-staff-link-copy > span {
  color: #5f7a76;
  font-size: 10px;
  font-weight: 750;
}

.attendance-staff-link {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: ltr;
  text-align: left;
  color: #2b7874;
  font-size: 11px;
  line-height: 1.4;
}

.attendance-staff-icon-btn {
  width: 34px;
  height: 34px;
  display: inline-grid;
  place-items: center;
  border-radius: 10px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  background: #fff;
  color: #1f5c59;
  cursor: pointer;
  text-decoration: none;
  flex: 0 0 auto;
}

.attendance-staff-icon-btn:hover {
  background: rgba(52, 144, 139, 0.08);
}

.attendance-staff-footer {
  display: grid;
  gap: 10px;
  padding: 0 16px 16px;
}

.attendance-staff-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.attendance-staff-punch {
  min-height: 46px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 14px;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 800;
  cursor: pointer;
  box-shadow: none;
  backdrop-filter: blur(6px);
  transition: background 0.16s ease, border-color 0.16s ease, opacity 0.16s ease;
}

.attendance-staff-punch.is-in {
  background: rgba(43, 184, 154, 0.14);
  border-color: rgba(31, 138, 112, 0.28);
  color: #145f52;
}

.attendance-staff-punch.is-out {
  background: rgba(224, 122, 95, 0.14);
  border-color: rgba(196, 90, 74, 0.28);
  color: #9a3f34;
}

.attendance-staff-punch:hover:not(:disabled) {
  filter: none;
}

.attendance-staff-punch.is-in:hover:not(:disabled) {
  background: rgba(43, 184, 154, 0.22);
  border-color: rgba(31, 138, 112, 0.36);
}

.attendance-staff-punch.is-out:hover:not(:disabled) {
  background: rgba(224, 122, 95, 0.22);
  border-color: rgba(196, 90, 74, 0.36);
}

.attendance-staff-punch:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.attendance-staff-punch.is-in :deep(.iconly-shell) {
  --iconly-filter: brightness(0) saturate(100%) invert(32%) sepia(28%) saturate(1200%) hue-rotate(128deg) brightness(92%) contrast(92%);
  font-size: 16px;
  color: #145f52;
}

.attendance-staff-punch.is-out :deep(.iconly-shell) {
  --iconly-filter: brightness(0) saturate(100%) invert(38%) sepia(42%) saturate(900%) hue-rotate(330deg) brightness(95%) contrast(92%);
  font-size: 16px;
  color: #9a3f34;
}

.status-badge {
  max-width: 100%;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 750;
  white-space: nowrap;
}

.report-time-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-time-edit input {
  min-width: 0;
  flex: 1;
  min-height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  padding: 0 10px;
}

.daily-events-list {
  display: grid;
  gap: 10px;
}

.daily-event-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid rgba(52, 144, 139, 0.1);
}

.daily-event-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.attendance-feed { display: grid; gap: 10px; min-width: 0; }

.attendance-feed-row,
.public-timeline article {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--line);
}

.attendance-feed-row strong,
.attendance-feed-row small,
.public-timeline strong,
.public-timeline small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendance-feed-row small,
.public-timeline small { color: var(--muted); }

.feed-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--warning);
}

.feed-dot.in { background: var(--success); }

.attendance-alert {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  overflow-wrap: break-word;
}

.attendance-alert.is-danger { background: var(--danger-soft); color: var(--danger); }
.attendance-alert.is-success { background: var(--success-soft); color: var(--success); }
.attendance-alert.is-warning { background: var(--warning-soft); color: var(--warning); }
.attendance-alert.is-info { background: rgba(52, 144, 139, 0.12); color: var(--primary); }
.status-badge.is-success { background: var(--success-soft); color: var(--success); }
.status-badge.is-warning { background: var(--warning-soft); color: var(--warning); }

.attendance-public {
  --bg: rgb(230, 242, 239);
  --primary: #34908B;
  --primary-strong: #2b7874;
  --primary-container: #dcefec;
  --on-primary: #ffffff;
  --on-primary-container: #1f5c59;
  --surface: #f3f9f7;
  --surface-strong: #f7fbfa;
  --surface-soft: #dcefec;
  --surface-muted: #d5ebe8;
  --surface-container-low: #e4f4f2;
  --surface-container-high: #d5ebe8;
  --text: #152523;
  --muted: #45605c;
  --line: #b7cbc7;
  --line-strong: #5f7a76;
  --danger: #c45a4a;
  --danger-soft: rgba(196, 90, 74, 0.12);
  --success: #1f7a72;
  --success-soft: rgba(31, 122, 114, 0.12);
  --warning: #b07a12;
  --warning-soft: rgba(176, 122, 18, 0.14);
  --button-primary-bg: #34908B;
  --button-primary-hover: #2b7874;
  --button-danger-bg: #c45a4a;
  --public-dock-height: 0px;
  min-height: 100%;
  min-height: 100dvh;
  width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  padding:
    max(12px, env(safe-area-inset-top))
    max(12px, env(safe-area-inset-right))
    calc(max(16px, env(safe-area-inset-bottom)) + var(--public-dock-height))
    max(12px, env(safe-area-inset-left));
  background:
    radial-gradient(circle at 14% 16%, rgba(52, 144, 139, 0.22), transparent 40%),
    radial-gradient(circle at 86% 10%, rgba(31, 92, 89, 0.12), transparent 34%),
    linear-gradient(180deg, #e6f2ef 0%, #f3f9f7 48%, #dcefec 100%);
  color: var(--text);
}

.attendance-public-inner {
  flex: 1 1 auto;
  width: min(760px, 100%);
  margin: 0 auto;
  min-width: 0;
}

.attendance-public-card {
  width: 100%;
  display: grid;
  gap: 14px;
  padding: clamp(16px, 4vw, 24px);
  border-radius: clamp(16px, 4vw, 22px);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(52, 144, 139, 0.12);
  box-shadow: none;
  min-width: 0;
  backdrop-filter: blur(10px);
}

.attendance-public-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}

.attendance-public-identity {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.attendance-public-identity > div {
  min-width: 0;
}

.attendance-public-head h1 {
  margin: 6px 0 4px;
  color: var(--primary);
  font-size: clamp(1.2rem, 4.8vw, 1.85rem);
  line-height: 1.35;
  overflow-wrap: break-word;
}

.attendance-public-head p {
  margin: 0;
  color: var(--muted);
  font-size: clamp(0.82rem, 3.2vw, 0.95rem);
  line-height: 1.6;
  overflow-wrap: break-word;
}

.status-badge-lg {
  flex: 0 0 auto;
  padding: 8px 14px;
  font-size: 12px;
}

.attendance-public-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 180px;
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
  text-align: center;
}

.attendance-public-spinner {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid rgba(52, 144, 139, 0.2);
  border-top-color: var(--primary);
  animation: attendance-public-spin 0.8s linear infinite;
}

@keyframes attendance-public-spin {
  to { transform: rotate(360deg); }
}

.attendance-public-hint {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
  font-size: 0.92rem;
}

.public-quick-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.public-quick-stats article {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  min-width: 0;
  min-height: 92px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(52, 144, 139, 0.06);
  border: 1px solid rgba(52, 144, 139, 0.12);
  box-shadow: none;
  overflow: hidden;
  text-align: start;
}

.public-quick-stats article.is-events {
  background: rgba(31, 138, 112, 0.08);
  border-color: rgba(31, 138, 112, 0.14);
}

.public-quick-stats article.is-hours {
  background: rgba(52, 144, 139, 0.08);
  border-color: rgba(52, 144, 139, 0.14);
}

.public-quick-stat-icon {
  width: 44px;
  height: 44px;
  display: inline-grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(31, 92, 89, 0.08);
  color: #1f5c59;
}

.public-quick-stats article > div {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.public-quick-stats span {
  display: block;
  color: #5f7a76;
  font-size: 12px;
  font-weight: 750;
}

.public-quick-stats strong {
  display: block;
  color: #123735;
  font-size: clamp(1.2rem, 4vw, 1.55rem);
  line-height: 1.2;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.public-quick-stats small {
  display: block;
  color: #7a9490;
  font-size: 10px;
  font-weight: 650;
}

.location-status-card {
  font-size: 0.92rem;
  line-height: 1.65;
}

.public-map-block {
  display: grid;
  gap: 10px;
}

.public-map-block :deep(.location-map-stage) {
  min-height: clamp(200px, 34vh, 280px) !important;
  border-radius: 16px;
}

.public-map-block :deep(.location-map-hint) {
  top: 8px;
  right: 8px;
  left: 8px;
  padding: 8px 10px;
}

.public-map-block :deep(.location-map-hint strong) {
  font-size: 0.78rem;
}

.public-locate-btn {
  width: 100%;
  min-height: 48px;
  justify-content: center;
  border-radius: 14px;
}

.attendance-public-dock {
  display: grid;
  gap: 0;
}

.attendance-public-dock .attendance-punch-grid {
  width: 100%;
}

.attendance-punch-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.attendance-punch-btn {
  position: relative;
  isolation: isolate;
  min-height: 118px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 10px;
  padding: 18px 12px;
  border-radius: 22px;
  border: 1px solid transparent;
  cursor: pointer;
  font: inherit;
  text-align: center;
  overflow: hidden;
  box-shadow: none;
  backdrop-filter: blur(8px);
  transition: background 180ms ease, border-color 180ms ease, opacity 180ms ease;
  -webkit-tap-highlight-color: transparent;
}

.attendance-punch-glow {
  display: none;
}

.attendance-punch-icon {
  position: relative;
  z-index: 1;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: none;
}

.attendance-punch-copy {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 4px;
  justify-items: center;
}

.attendance-punch-btn:hover:not(:disabled) {
  transform: none;
}

.attendance-punch-btn:active:not(:disabled) {
  transform: none;
}

.attendance-punch-btn strong {
  font-size: clamp(0.98rem, 3.6vw, 1.12rem);
  font-weight: 800;
  letter-spacing: -0.01em;
}

.attendance-punch-btn small {
  font-size: 0.78rem;
  line-height: 1.45;
  font-weight: 600;
}

.attendance-punch-btn.is-in {
  background: rgba(43, 184, 154, 0.14);
  border-color: rgba(31, 138, 112, 0.28);
  color: #145f52;
}

.attendance-punch-btn.is-in .attendance-punch-icon {
  background: rgba(31, 138, 112, 0.12);
  border-color: rgba(31, 138, 112, 0.2);
}

.attendance-punch-btn.is-in small {
  color: rgba(20, 95, 82, 0.72);
}

.attendance-punch-btn.is-out {
  background: rgba(224, 122, 95, 0.14);
  border-color: rgba(196, 90, 74, 0.28);
  color: #9a3f34;
}

.attendance-punch-btn.is-out .attendance-punch-icon {
  background: rgba(196, 90, 74, 0.12);
  border-color: rgba(196, 90, 74, 0.2);
}

.attendance-punch-btn.is-out small {
  color: rgba(154, 63, 52, 0.72);
}

.attendance-punch-btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
  filter: grayscale(0.18);
  transform: none;
}

.attendance-punch-btn.is-in :deep(.iconly-shell) {
  --iconly-filter: brightness(0) saturate(100%) invert(32%) sepia(28%) saturate(1200%) hue-rotate(128deg) brightness(92%) contrast(92%);
  font-size: clamp(22px, 5.5vw, 26px);
  color: #145f52;
}

.attendance-punch-btn.is-out :deep(.iconly-shell) {
  --iconly-filter: brightness(0) saturate(100%) invert(38%) sepia(42%) saturate(900%) hue-rotate(330deg) brightness(95%) contrast(92%);
  font-size: clamp(22px, 5.5vw, 26px);
  color: #9a3f34;
}

.public-note { display: grid; gap: 8px; min-width: 0; }
.public-note span { color: var(--muted); font-weight: 800; font-size: 0.88rem; }

.public-note textarea {
  width: 100%;
  min-height: 76px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--surface-container-low);
  border: 1px solid var(--line);
  resize: vertical;
  box-sizing: border-box;
  color: var(--text);
  font: inherit;
  font-size: 16px;
}

.public-note textarea:focus {
  outline: 2px solid rgba(52, 144, 139, 0.28);
  border-color: var(--primary);
}

.public-timeline { display: grid; gap: 10px; }
.public-timeline-title {
  margin: 0;
  font-size: 0.95rem;
  color: var(--primary);
}

.attendance-public .public-timeline article {
  background: var(--surface);
  border-color: var(--line);
}

.public-event-note {
  margin-top: 4px;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.5;
}

@media (min-width: 761px) {
  .attendance-public {
    --public-dock-height: 0px;
    justify-content: center;
    padding-bottom: max(24px, env(safe-area-inset-bottom));
  }

  .attendance-punch-btn {
    min-height: 148px;
    padding: 22px 16px;
    gap: 12px;
  }

  .attendance-punch-icon {
    width: 58px;
    height: 58px;
    border-radius: 18px;
  }
}

@media (max-width: 760px) {
  .attendance-public {
    --public-dock-height: 118px;
    padding-top: max(8px, env(safe-area-inset-top));
    padding-inline: max(10px, env(safe-area-inset-right)) max(10px, env(safe-area-inset-left));
  }

  .attendance-public-card {
    padding: 14px;
    gap: 12px;
    border-radius: 18px;
    padding-bottom: calc(14px + var(--public-dock-height));
  }

  .attendance-public-head {
    flex-direction: column;
    align-items: stretch;
  }

  .status-badge-lg {
    align-self: flex-start;
  }

  .attendance-public-dock {
    position: fixed;
    inset-inline: 0;
    bottom: 0;
    z-index: 120;
    padding:
      10px max(12px, env(safe-area-inset-right))
      calc(10px + env(safe-area-inset-bottom))
      max(12px, env(safe-area-inset-left));
    background: linear-gradient(180deg, rgba(230, 242, 239, 0) 0%, rgba(230, 242, 239, 0.88) 24%, rgba(243, 249, 247, 0.98) 100%);
    backdrop-filter: blur(14px);
    border-top: 1px solid rgba(183, 203, 199, 0.75);
  }

  .attendance-public-dock .attendance-punch-grid {
    width: min(760px, calc(100vw - 24px));
    margin: 0 auto;
  }

  .attendance-punch-grid {
    grid-template-columns: 1fr 1fr;
  }

  .attendance-punch-btn {
    min-height: 88px;
  }
}

@media (max-width: 380px) {
  .attendance-public-identity {
    align-items: flex-start;
  }

  .public-quick-stats {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1100px) {
  .attendance-hero,
  .attendance-layout { grid-template-columns: 1fr; }
  .report-summary-grid,
  .report-summary-grid-wide { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .report-hero { flex-direction: column; }
  .report-detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .report-cards-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .report-view-tab { flex: 0 0 auto; width: auto; white-space: nowrap; }
  .attendance-tab { flex: 0 0 auto; width: auto; white-space: nowrap; }
}

@media (max-width: 760px) {
  .attendance-hero { padding: 16px; }
  .attendance-toolbar { grid-template-columns: 1fr; }
  .attendance-users,
  .report-summary-grid,
  .report-summary-grid-wide { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .attendance-tab { flex: 1 1 calc(50% - 5px); }
  .attendance-staff-actions { grid-template-columns: 1fr 1fr; }
  .report-hero-actions { width: 100%; }
  .report-hero-actions .action-btn { flex: 1 1 calc(50% - 4px); }
  .report-view-tab { flex: 0 0 auto; width: auto; text-align: center; white-space: nowrap; }
  .report-detail-grid { grid-template-columns: 1fr; }
}

@media (max-width: 560px) {
  .attendance-summary,
  .attendance-users,
  .report-summary-grid,
  .report-summary-grid-wide { grid-template-columns: 1fr; }

  .attendance-staff-actions { grid-template-columns: 1fr; }
}

.attendance-tabs,
.report-view-tabs,
.report-range-bar {
  overflow-x: auto;
  flex-wrap: nowrap;
  scrollbar-width: none;
}

.attendance-tabs::-webkit-scrollbar,
.report-view-tabs::-webkit-scrollbar,
.report-range-bar::-webkit-scrollbar {
  display: none;
}
</style>

<style>
/* Attendance cards & summaries — unscoped locks beat jade flat overrides */
#app .app-shell:not(.is-auth-route) .attendance-hero {
  display: grid !important;
  gap: 18px !important;
  padding: 22px !important;
  border-radius: 24px !important;
  background: rgba(52, 144, 139, 0.06) !important;
  background-image: none !important;
  border: 1px solid rgba(52, 144, 139, 0.12) !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 12px !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary-tile {
  position: relative !important;
  display: grid !important;
  grid-template-columns: auto minmax(0, 1fr) !important;
  align-items: center !important;
  gap: 12px !important;
  min-height: 92px !important;
  padding: 14px 14px 14px 12px !important;
  border-radius: 18px !important;
  background: rgba(52, 144, 139, 0.06) !important;
  background-image: none !important;
  border: 1px solid rgba(52, 144, 139, 0.12) !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary-tile.is-present-summary {
  background: rgba(31, 138, 112, 0.08) !important;
  background-image: none !important;
  border-color: rgba(31, 138, 112, 0.16) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary-tile.is-away-summary {
  background: rgba(200, 115, 42, 0.08) !important;
  background-image: none !important;
  border-color: rgba(200, 115, 42, 0.16) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary-icon {
  width: 44px !important;
  height: 44px !important;
  display: inline-grid !important;
  place-items: center !important;
  border-radius: 14px !important;
  background: rgba(31, 92, 89, 0.08) !important;
  color: #1f5c59 !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary-body span,
#app .app-shell:not(.is-auth-route) .attendance-summary-body small,
#app .app-shell:not(.is-auth-route) .attendance-staff-stat-body span,
#app .app-shell:not(.is-auth-route) .attendance-staff-stat-body small,
#app .app-shell:not(.is-auth-route) .attendance-staff-link-copy > span {
  color: #5f7a76 !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary-body strong,
#app .app-shell:not(.is-auth-route) .attendance-staff-stat-body strong {
  color: #123735 !important;
  font-weight: 900 !important;
  letter-spacing: -0.02em !important;
}

#app .app-shell:not(.is-auth-route) .attendance-summary-body strong {
  font-size: clamp(1.25rem, 2.6vw, 1.7rem) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-card {
  position: relative !important;
  display: grid !important;
  gap: 14px !important;
  padding: 0 !important;
  border-radius: 22px !important;
  overflow: hidden !important;
  background: rgba(255, 255, 255, 0.72) !important;
  background-image: none !important;
  border: 1px solid rgba(52, 144, 139, 0.12) !important;
  box-shadow: none !important;
  backdrop-filter: blur(8px) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-banner {
  display: block !important;
  height: 6px !important;
  background: linear-gradient(90deg, #9bb5b1, #c5d4d1) !important;
  background-image: linear-gradient(90deg, #9bb5b1, #c5d4d1) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-card.is-present .attendance-staff-banner {
  background: linear-gradient(90deg, #1f8a70, #34908b 55%, #2bb89a) !important;
  background-image: linear-gradient(90deg, #1f8a70, #34908b 55%, #2bb89a) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-card.is-away .attendance-staff-banner {
  background: linear-gradient(90deg, #c8732a, #e0a35d 60%, #f0c48a) !important;
  background-image: linear-gradient(90deg, #c8732a, #e0a35d 60%, #f0c48a) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-stats {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 10px !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-stat {
  display: grid !important;
  grid-template-columns: auto minmax(0, 1fr) !important;
  align-items: center !important;
  gap: 10px !important;
  min-height: 86px !important;
  padding: 12px !important;
  border-radius: 18px !important;
  background: rgba(52, 144, 139, 0.06) !important;
  background-image: none !important;
  border: 1px solid rgba(52, 144, 139, 0.1) !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-stat.is-events {
  background: rgba(31, 138, 112, 0.08) !important;
  background-image: none !important;
  border-color: rgba(31, 138, 112, 0.14) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-stat.is-hours {
  background: rgba(52, 144, 139, 0.08) !important;
  background-image: none !important;
  border-color: rgba(52, 144, 139, 0.14) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-stat-icon {
  width: 42px !important;
  height: 42px !important;
  display: inline-grid !important;
  place-items: center !important;
  border-radius: 14px !important;
  background: rgba(31, 92, 89, 0.08) !important;
  color: #1f5c59 !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-stat-body strong {
  font-size: clamp(1.15rem, 2.4vw, 1.45rem) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-status.is-success {
  background: rgba(31, 138, 112, 0.12) !important;
  color: #145f52 !important;
  border: 1px solid rgba(31, 138, 112, 0.2) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-status.is-warning {
  background: rgba(200, 115, 42, 0.12) !important;
  color: #8a4b12 !important;
  border: 1px solid rgba(200, 115, 42, 0.22) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-linkbar {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) auto auto !important;
  gap: 8px !important;
  align-items: center !important;
  padding: 10px 12px !important;
  margin-inline: 16px !important;
  border-radius: 14px !important;
  background: rgba(31, 92, 89, 0.05) !important;
  border: 1px solid rgba(52, 144, 139, 0.12) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-in {
  background: rgba(43, 184, 154, 0.14) !important;
  background-image: none !important;
  border: 1px solid rgba(31, 138, 112, 0.28) !important;
  color: #145f52 !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-out {
  background: rgba(224, 122, 95, 0.14) !important;
  background-image: none !important;
  border: 1px solid rgba(196, 90, 74, 0.28) !important;
  color: #9a3f34 !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-in,
#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-in span {
  color: #145f52 !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-out,
#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-out span {
  color: #9a3f34 !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-in .iconly-shell,
#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-in .iconly-img {
  --iconly-filter: brightness(0) saturate(100%) invert(32%) sepia(28%) saturate(1200%) hue-rotate(128deg) brightness(92%) contrast(92%) !important;
  filter: brightness(0) saturate(100%) invert(32%) sepia(28%) saturate(1200%) hue-rotate(128deg) brightness(92%) contrast(92%) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-out .iconly-shell,
#app .app-shell:not(.is-auth-route) .attendance-staff-punch.is-out .iconly-img {
  --iconly-filter: brightness(0) saturate(100%) invert(38%) sepia(42%) saturate(900%) hue-rotate(330deg) brightness(95%) contrast(92%) !important;
  filter: brightness(0) saturate(100%) invert(38%) sepia(42%) saturate(900%) hue-rotate(330deg) brightness(95%) contrast(92%) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-in {
  background: rgba(43, 184, 154, 0.14) !important;
  background-image: none !important;
  border-color: rgba(31, 138, 112, 0.28) !important;
  color: #145f52 !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-out {
  background: rgba(224, 122, 95, 0.14) !important;
  background-image: none !important;
  border-color: rgba(196, 90, 74, 0.28) !important;
  color: #9a3f34 !important;
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-in :where(span, strong, small) {
  color: #145f52 !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-out :where(span, strong, small) {
  color: #9a3f34 !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-in small {
  color: rgba(20, 95, 82, 0.72) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-out small {
  color: rgba(154, 63, 52, 0.72) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-in .iconly-shell,
#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-in .iconly-img {
  --iconly-filter: brightness(0) saturate(100%) invert(32%) sepia(28%) saturate(1200%) hue-rotate(128deg) brightness(92%) contrast(92%) !important;
  filter: brightness(0) saturate(100%) invert(32%) sepia(28%) saturate(1200%) hue-rotate(128deg) brightness(92%) contrast(92%) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-out .iconly-shell,
#app .app-shell:not(.is-auth-route) .attendance-punch-btn.is-out .iconly-img {
  --iconly-filter: brightness(0) saturate(100%) invert(38%) sepia(42%) saturate(900%) hue-rotate(330deg) brightness(95%) contrast(92%) !important;
  filter: brightness(0) saturate(100%) invert(38%) sepia(42%) saturate(900%) hue-rotate(330deg) brightness(95%) contrast(92%) !important;
}

#app .app-shell:not(.is-auth-route) .attendance-punch-icon {
  box-shadow: none !important;
}

#app .app-shell:not(.is-auth-route) .attendance-staff-time input {
  min-height: 44px !important;
  border-radius: 12px !important;
  border: 1px solid rgba(52, 144, 139, 0.16) !important;
  background: #f7fbfa !important;
}

@media (max-width: 720px) {
  #app .app-shell:not(.is-auth-route) .attendance-summary {
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 8px !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-summary-tile {
    padding: 10px 8px !important;
    min-height: 0 !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-summary-icon {
    display: none !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-summary-body span,
  #app .app-shell:not(.is-auth-route) .attendance-summary-body small {
    font-size: 0.65rem !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-summary-body strong {
    font-size: 0.95rem !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-toolbar {
    grid-template-columns: minmax(0, 1fr) auto auto !important;
    gap: 8px !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-toolbar .search-shell-wide {
    grid-column: 1 / -1 !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-staff-footer {
    grid-template-columns: 1fr !important;
  }

  #app .app-shell:not(.is-auth-route) .attendance-staff-actions {
    grid-template-columns: 1fr 1fr !important;
  }

  #app .app-shell:not(.is-auth-route) .report-filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 8px !important;
  }

  #app .app-shell:not(.is-auth-route) .report-filter-grid .search-shell-wide {
    grid-column: 1 / -1 !important;
  }
}
</style>
