<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import LocationMapPicker from '../components/LocationMapPicker.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import SectionHeading from '../components/SectionHeading.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { haversineDistanceMeters, readDeviceLocation } from '../lib/geolocation'
import { formatJalali, getTodayJalali, gregorianToJalali, isoToJalali, jalaliToIso } from '../utils/jalali'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'

const route = useRoute()
const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const search = ref('')
const statusFilter = ref('all')
const activeTab = ref('dashboard')
const note = ref('')
const dashboard = ref({ summary: {}, users: [], recentEvents: [], organization: {} })
const reportPayload = ref({ summary: {}, rows: [], users: [], personnelStats: [], dailyStats: [], departments: [] })
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
const reportViewMode = ref('table')
const expandedReportRowId = ref(null)
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
  return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
const dateOnly = (value) => {
  if (!value) return '-'
  if (String(value).length === 10 && value.includes('-')) return isoToJalali(value) || value
  return new Intl.DateTimeFormat('fa-IR-u-ca-persian', { dateStyle: 'medium' }).format(new Date(value))
}
const timeOnly = (value) => {
  if (!value) return '-'
  if (String(value).length <= 5 && value.includes(':')) return toFaTime(value)
  return new Intl.DateTimeFormat('fa-IR-u-ca-persian', { timeStyle: 'short' }).format(new Date(value))
}
const toFaTime = (value) => String(value || '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[digit] || digit)
const sourceLabel = (source) => (source === 'manager' ? 'ثبت مدیر' : 'لینک پرسنل')
const gpsLabel = (row) => {
  if (!row.hasGps) return 'بدون GPS'
  if (row.withinRadius === true) return `داخل محدوده · ${fa(Math.round(row.distanceMeters ?? row.distance_meters ?? 0))}m`
  if (row.withinRadius === false) return `خارج محدوده · ${fa(Math.round(row.distanceMeters ?? row.distance_meters ?? 0))}m`
  return row.coordinatesLabel || 'دارای GPS'
}
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
  { key: 'yesterday', label: 'دیروز' },
  { key: 'week', label: '۷ روز اخیر' },
  { key: 'month', label: '۳۰ روز اخیر' },
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
const reportPersonnelStats = computed(() => reportPayload.value.personnelStats || reportPayload.value.personnel_stats || [])
const reportDailyStats = computed(() => reportPayload.value.dailyStats || reportPayload.value.daily_stats || [])
const reportDepartments = computed(() => reportPayload.value.departments || [])
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
  expandedReportRowId.value = null
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
    reportPayload.value = await apiFetch(`/attendance/reports${query ? `?${query}` : ''}`)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'reports' && !reportRows.value.length) await loadReports()
}

function jalaliFromDate(date) {
  return formatJalali(gregorianToJalali(date.getFullYear(), date.getMonth() + 1, date.getDate()))
}

function applyQuickRange(key) {
  const today = new Date()
  const end = jalaliFromDate(today)
  let startDate = new Date(today)
  if (key === 'today') {
    reportFilters.value.rangeKey = key
    reportFilters.value.start = end
    reportFilters.value.end = end
    void loadReports()
    return
  }
  if (key === 'yesterday') {
    startDate.setDate(startDate.getDate() - 1)
    const day = jalaliFromDate(startDate)
    reportFilters.value.rangeKey = key
    reportFilters.value.start = day
    reportFilters.value.end = day
    void loadReports()
    return
  }
  if (key === 'week') startDate.setDate(startDate.getDate() - 6)
  if (key === 'month') startDate.setDate(startDate.getDate() - 29)
  reportFilters.value.rangeKey = key
  reportFilters.value.start = jalaliFromDate(startDate)
  reportFilters.value.end = end
  void loadReports()
}

function resetReportFilters() {
  reportFilters.value = { q: '', start: '', end: '', userId: '', eventType: 'all', source: 'all', department: '', rangeKey: '' }
  void loadReports()
}

function toggleReportRow(rowId) {
  expandedReportRowId.value = expandedReportRowId.value === rowId ? null : rowId
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

async function refreshLiveLocation() {
  if (!workplaceConfigured.value) return
  locationBusy.value = true
  try {
    const coords = await readDeviceLocation()
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
      locationHint.value = `برای ثبت ورود/خروج باید در شعاع ${fa(workplaceRadius.value)} متری محل کار باشید.`
      await refreshLiveLocation()
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
  try {
    dashboard.value = await apiFetch('/attendance/events', {
      method: 'POST',
      body: JSON.stringify({ userId: user.id, eventType }),
    })
    if (activeTab.value === 'reports') await loadReports()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

async function submitPublicEvent(eventType) {
  submitting.value = true
  locationBusy.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    if (!workplaceConfigured.value) {
      throw new Error('لوکیشن محل کار توسط مدیر مجموعه تنظیم نشده است.')
    }
    const coords = await readDeviceLocation()
    liveUserLocation.value = coords
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

onMounted(() => {
  if (window.matchMedia('(max-width: 760px)').matches) {
    reportViewMode.value = 'cards'
  }
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
        <article>
          <span>حاضر</span>
          <strong>{{ fa(dashboard.summary?.presentCount) }}</strong>
        </article>
        <article>
          <span>خارج</span>
          <strong>{{ fa(dashboard.summary?.absentCount) }}</strong>
        </article>
        <article>
          <span>ساعت امروز</span>
          <strong>{{ fa(dashboard.summary?.todayWorkedHours) }}</strong>
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
        <article v-for="user in filteredUsers" :key="user.id" class="attendance-user-card">
          <div class="attendance-user-head">
            <UserAvatar
              :name="user.name"
              :avatar="user.avatar"
              :avatar-url="user.avatarUrl || user.avatar_url"
              size="md"
            />
            <div class="attendance-user-identity">
              <strong>{{ user.name }}</strong>
              <small>{{ user.role }} · {{ user.department }}</small>
            </div>
            <div class="attendance-user-tools">
              <span :class="['status-badge', eventTone(user.status)]">{{ statusLabel(user.status) }}</span>
              <button class="icon-btn" type="button" title="کپی لینک" @click="copyLink(user)">
                <IconlyIcon name="content_copy" decorative />
              </button>
              <a class="icon-btn" title="باز کردن لینک" :href="attendanceLink(user)" target="_blank" rel="noreferrer">
                <IconlyIcon name="open_in_new" decorative />
              </a>
            </div>
          </div>
          <div class="attendance-mini-grid">
            <span>ثبت امروز <b>{{ fa(user.todayEventsCount) }}</b></span>
            <span>ساعت امروز <b>{{ fa(user.todayWorkedHours) }}</b></span>
          </div>
          <code class="attendance-link">{{ attendanceLink(user) }}</code>
          <div class="attendance-actions">
            <button class="action-btn tone-primary" type="button" :disabled="submitting || user.status === 'in'" @click="submitManagerEvent(user, 'in')">
              <IconlyIcon name="login" decorative />
              <span>ثبت ورود</span>
            </button>
            <button class="action-btn tone-soft" type="button" :disabled="submitting || user.status !== 'in'" @click="submitManagerEvent(user, 'out')">
              <IconlyIcon name="logout" decorative />
              <span>ثبت خروج</span>
            </button>
          </div>
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
            <button class="action-btn tone-primary" type="button" :disabled="!reportRows.length" @click="exportReportsCsv">
              <IconlyIcon name="download" decorative />
              <span>خروجی CSV</span>
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
            <ShamsiDatePicker v-model="reportFilters.start" model-type="jalali" placeholder="1405/04/01" />
          </label>
          <label class="field-shell">
            <span>تا تاریخ</span>
            <ShamsiDatePicker v-model="reportFilters.end" model-type="jalali" placeholder="1405/04/31" />
          </label>
          <label class="field-shell">
            <span>پرسنل</span>
            <select v-model="reportFilters.userId">
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

        <div class="report-view-tabs">
          <button :class="['report-view-tab', reportViewMode === 'table' && 'is-active']" type="button" @click="reportViewMode = 'table'">جدول جزئیات</button>
          <button :class="['report-view-tab', reportViewMode === 'cards' && 'is-active']" type="button" @click="reportViewMode = 'cards'">کارت موبایل</button>
          <button :class="['report-view-tab', reportViewMode === 'personnel' && 'is-active']" type="button" @click="reportViewMode = 'personnel'">آمار پرسنل</button>
          <button :class="['report-view-tab', reportViewMode === 'daily' && 'is-active']" type="button" @click="reportViewMode = 'daily'">آمار روزانه</button>
        </div>

        <section v-if="reportViewMode === 'table'" class="surface-block report-table-card">
          <div class="section-label-row report-table-head">
            <div>
              <h3>جدول جزئیات رویدادها</h3>
              <p class="report-table-subtitle">تمام جزئیات: زمان، GPS، فاصله، مدت شیفت، منبع ثبت و یادداشت</p>
            </div>
            <span class="table-count">{{ fa(reportRows.length) }} / {{ fa(reportSummary.total) }}</span>
          </div>

          <div class="attendance-table-wrap">
            <table class="attendance-report-table attendance-report-table-detailed">
              <thead>
                <tr>
                  <th>#</th>
                  <th>پرسنل</th>
                  <th>سمت / بخش</th>
                  <th>نوع</th>
                  <th>منبع</th>
                  <th>تاریخ</th>
                  <th>ساعت</th>
                  <th>مدت شیفت</th>
                  <th>موقعیت</th>
                  <th>یادداشت</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <template v-for="row in reportRows" :key="row.id">
                  <tr :class="['report-row', expandedReportRowId === row.id && 'is-expanded']">
                    <td>{{ fa(row.row) }}</td>
                    <td>
                      <strong>{{ row.userName }}</strong>
                      <small v-if="row.userPhone" class="report-cell-sub">{{ row.userPhone }}</small>
                    </td>
                    <td>
                      <span>{{ row.userRole || '-' }}</span>
                      <small class="report-cell-sub">{{ row.userDepartment || '-' }}</small>
                    </td>
                    <td><span :class="['status-badge', eventTone(row.eventType)]">{{ eventLabel(row.eventType) }}</span></td>
                    <td>{{ sourceLabel(row.source) }}</td>
                    <td>{{ dateOnly(row.eventDate || row.eventAt) }}</td>
                    <td>{{ timeOnly(row.eventTime || row.eventAt) }}</td>
                    <td>{{ formatShift(row) }}</td>
                    <td>
                      <span :class="['report-gps-pill', row.withinRadius === true && 'is-ok', row.withinRadius === false && 'is-bad', !row.hasGps && 'is-muted']">
                        {{ gpsLabel(row) }}
                      </span>
                    </td>
                    <td class="report-note-cell">{{ row.note || '-' }}</td>
                    <td>
                      <button class="icon-btn report-expand-btn" type="button" :title="expandedReportRowId === row.id ? 'بستن' : 'جزئیات'" @click="toggleReportRow(row.id)">
                        <IconlyIcon :name="expandedReportRowId === row.id ? 'expand_less' : 'expand_more'" decorative />
                      </button>
                    </td>
                  </tr>
                  <tr v-if="expandedReportRowId === row.id" class="report-row-detail">
                    <td colspan="11">
                      <div class="report-detail-grid">
                        <article><span>شناسه رویداد</span><strong>{{ fa(row.id) }}</strong></article>
                        <article><span>موبایل</span><strong>{{ row.userPhone || '-' }}</strong></article>
                        <article><span>ثبت سیستم</span><strong>{{ dateTime(row.createdAt) }}</strong></article>
                        <article><span>زمان کامل</span><strong>{{ dateTime(row.eventAt) }}</strong></article>
                        <article><span>منبع</span><strong>{{ sourceLabel(row.source) }}</strong></article>
                        <article><span>مدت شیفت</span><strong>{{ formatShift(row) }}</strong></article>
                        <article><span>فاصله</span><strong>{{ row.distanceMeters != null ? `${fa(Math.round(row.distanceMeters))} متر` : '-' }}</strong></article>
                        <article><span>مختصات</span><strong dir="ltr">{{ row.coordinatesLabel || '-' }}</strong></article>
                        <article class="report-detail-wide"><span>یادداشت</span><strong>{{ row.note || '—' }}</strong></article>
                      </div>
                    </td>
                  </tr>
                </template>
                <tr v-if="!reportRows.length && !loading">
                  <td colspan="11">گزارشی برای این فیلترها پیدا نشد.</td>
                </tr>
                <tr v-if="loading">
                  <td colspan="11">در حال بارگذاری گزارش…</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-else-if="reportViewMode === 'cards'" class="report-cards-grid">
          <article v-for="row in reportRows" :key="row.id" :class="['report-event-card', `card-tone-${row.eventType}`]">
            <div class="report-event-card-head">
              <div>
                <strong>{{ row.userName }}</strong>
                <small>{{ row.userRole }} · {{ row.userDepartment }}</small>
              </div>
              <span :class="['status-badge', eventTone(row.eventType)]">{{ eventLabel(row.eventType) }}</span>
            </div>
            <div class="report-event-card-meta">
              <span><IconlyIcon name="calendar" decorative /> {{ dateOnly(row.eventDate || row.eventAt) }} · {{ timeOnly(row.eventTime || row.eventAt) }}</span>
              <span><IconlyIcon name="login" decorative /> {{ sourceLabel(row.source) }}</span>
              <span v-if="row.shiftMinutes != null"><IconlyIcon name="schedule" decorative /> مدت: {{ formatShift(row) }}</span>
              <span :class="['report-gps-pill', row.withinRadius === true && 'is-ok', row.withinRadius === false && 'is-bad']">{{ gpsLabel(row) }}</span>
            </div>
            <p v-if="row.note" class="report-event-card-note">{{ row.note }}</p>
            <div class="report-event-card-foot">
              <small v-if="row.userPhone">📱 {{ row.userPhone }}</small>
              <small v-if="row.coordinatesLabel" dir="ltr">📍 {{ row.coordinatesLabel }}</small>
              <small>ثبت: {{ dateTime(row.createdAt) }}</small>
            </div>
          </article>
          <p v-if="!reportRows.length && !loading" class="attendance-public-hint">گزارشی برای این فیلترها پیدا نشد.</p>
        </section>

        <section v-else-if="reportViewMode === 'personnel'" class="surface-block report-table-card">
          <div class="section-label-row report-table-head">
            <div>
              <h3>آمار تجمیعی پرسنل</h3>
              <p class="report-table-subtitle">ورود، خروج، ساعات کار، GPS و آخرین وضعیت هر نفر</p>
            </div>
            <span class="table-count">{{ fa(reportPersonnelStats.length) }} نفر</span>
          </div>
          <div class="attendance-table-wrap desktop-data-table">
            <table class="attendance-report-table">
              <thead>
                <tr>
                  <th>پرسنل</th>
                  <th>بخش</th>
                  <th>موبایل</th>
                  <th>کل رویداد</th>
                  <th>ورود</th>
                  <th>خروج</th>
                  <th>ساعات کار</th>
                  <th>لینک / مدیر</th>
                  <th>GPS</th>
                  <th>آخرین رویداد</th>
                  <th>وضعیت</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="person in reportPersonnelStats" :key="person.userId">
                  <td><strong>{{ person.userName }}</strong><small class="report-cell-sub">{{ person.userRole || '-' }}</small></td>
                  <td>{{ person.userDepartment || '-' }}</td>
                  <td>{{ person.userPhone || '-' }}</td>
                  <td>{{ fa(person.totalEvents) }}</td>
                  <td>{{ fa(person.checkins) }}</td>
                  <td>{{ fa(person.checkouts) }}</td>
                  <td>{{ formatHours(person.workedHours) }}</td>
                  <td>{{ fa(person.linkEvents) }} / {{ fa(person.managerEvents) }}</td>
                  <td>{{ fa(person.withGps) }}</td>
                  <td>{{ eventLabel(person.lastEventType) }} · {{ dateTime(person.lastEventAt) }}</td>
                  <td><span :class="['status-badge', eventTone(person.currentStatus)]">{{ statusLabel(person.currentStatus) }}</span></td>
                </tr>
                <tr v-if="!reportPersonnelStats.length && !loading"><td colspan="11">آمار پرسنلی برای این فیلترها موجود نیست.</td></tr>
              </tbody>
            </table>
          </div>

          <div class="mobile-data-cards report-cards-grid">
            <article
              v-for="person in reportPersonnelStats"
              :key="`person-card-${person.userId}`"
              class="report-event-card"
            >
              <div class="report-event-card-head">
                <div>
                  <strong>{{ person.userName }}</strong>
                  <small>{{ person.userRole || '-' }} · {{ person.userDepartment || '-' }}</small>
                </div>
                <span :class="['status-badge', eventTone(person.currentStatus)]">{{ statusLabel(person.currentStatus) }}</span>
              </div>
              <div class="report-event-card-meta">
                <span>رویداد: {{ fa(person.totalEvents) }} · ورود {{ fa(person.checkins) }} · خروج {{ fa(person.checkouts) }}</span>
                <span>ساعات: {{ formatHours(person.workedHours) }}</span>
                <span>آخرین: {{ eventLabel(person.lastEventType) }} · {{ dateTime(person.lastEventAt) }}</span>
              </div>
            </article>
            <p v-if="!reportPersonnelStats.length && !loading" class="attendance-public-hint">آمار پرسنلی برای این فیلترها موجود نیست.</p>
          </div>
        </section>

        <section v-else class="surface-block report-table-card">
          <div class="section-label-row report-table-head">
            <div>
              <h3>آمار روزانه</h3>
              <p class="report-table-subtitle">تفکیک روزانه رویدادها، پرسنل حاضر و ساعات کار</p>
            </div>
            <span class="table-count">{{ fa(reportDailyStats.length) }} روز</span>
          </div>
          <div class="attendance-table-wrap desktop-data-table">
            <table class="attendance-report-table">
              <thead>
                <tr>
                  <th>تاریخ</th>
                  <th>کل رویداد</th>
                  <th>ورود</th>
                  <th>خروج</th>
                  <th>پرسنل</th>
                  <th>ساعات کار</th>
                  <th>لینک</th>
                  <th>مدیر</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="day in reportDailyStats" :key="day.date">
                  <td><strong>{{ dateOnly(day.date) }}</strong></td>
                  <td>{{ fa(day.totalEvents) }}</td>
                  <td>{{ fa(day.checkins) }}</td>
                  <td>{{ fa(day.checkouts) }}</td>
                  <td>{{ fa(day.uniqueUsers) }}</td>
                  <td>{{ formatHours(day.workedHours) }}</td>
                  <td>{{ fa(day.linkEvents) }}</td>
                  <td>{{ fa(day.managerEvents) }}</td>
                </tr>
                <tr v-if="!reportDailyStats.length && !loading"><td colspan="8">آمار روزانه برای این فیلترها موجود نیست.</td></tr>
              </tbody>
            </table>
          </div>

          <div class="mobile-data-cards report-cards-grid">
            <article v-for="day in reportDailyStats" :key="`day-card-${day.date}`" class="report-event-card">
              <div class="report-event-card-head">
                <div>
                  <strong>{{ dateOnly(day.date) }}</strong>
                  <small>{{ fa(day.uniqueUsers) }} پرسنل · {{ fa(day.totalEvents) }} رویداد</small>
                </div>
              </div>
              <div class="report-event-card-meta">
                <span>ورود {{ fa(day.checkins) }} · خروج {{ fa(day.checkouts) }}</span>
                <span>ساعات: {{ formatHours(day.workedHours) }}</span>
              </div>
            </article>
            <p v-if="!reportDailyStats.length && !loading" class="attendance-public-hint">آمار روزانه برای این فیلترها موجود نیست.</p>
          </div>
        </section>
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
            <article>
              <span>ثبت امروز</span>
              <strong>{{ fa(publicUser.todayEventsCount) }}</strong>
            </article>
            <article>
              <span>ساعت امروز</span>
              <strong>{{ fa(publicUser.todayWorkedHours) }}</strong>
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
            <button class="action-btn tone-soft public-locate-btn" type="button" :disabled="locationBusy || submitting" @click="refreshLiveLocation">
              <IconlyIcon name="profile" decorative />
              <span>{{ locationBusy ? 'در حال دریافت موقعیت...' : 'بروزرسانی موقعیت من' }}</span>
            </button>
          </div>

          <div v-if="publicUser.id" class="attendance-public-dock">
            <div class="attendance-punch-grid">
              <button
                class="attendance-punch-btn is-in"
                type="button"
                :disabled="submitting || locationBusy || !workplaceConfigured || publicUser.status === 'in'"
                @click="submitPublicEvent('in')"
              >
                <IconlyIcon name="login" size="xl" decorative />
                <strong>{{ locationBusy && publicUser.status !== 'in' ? 'در حال بررسی...' : 'ثبت ورود' }}</strong>
                <small>{{ publicUser.status === 'in' ? 'الان حاضر هستید' : 'شروع شیفت' }}</small>
              </button>
              <button
                class="attendance-punch-btn is-out"
                type="button"
                :disabled="submitting || locationBusy || !workplaceConfigured || publicUser.status !== 'in'"
                @click="submitPublicEvent('out')"
              >
                <IconlyIcon name="logout" size="xl" decorative />
                <strong>{{ locationBusy && publicUser.status === 'in' ? 'در حال بررسی...' : 'ثبت خروج' }}</strong>
                <small>{{ publicUser.status === 'in' ? 'پایان شیفت' : 'ابتدا ورود ثبت کنید' }}</small>
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
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 18px;
  padding: 24px;
  border-radius: 12px;
  background: var(--surface, #fff);
  border: 1px solid var(--line);
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
.attendance-mini-grid,
.public-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  min-width: 0;
}

.attendance-summary article,
.attendance-mini-grid span,
.public-stats article {
  min-width: 0;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid var(--line);
}

.attendance-summary span,
.public-stats span {
  display: block;
  color: var(--muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendance-summary strong,
.public-stats strong {
  display: block;
  margin-top: 8px;
  color: var(--primary);
  font-size: clamp(1.1rem, 3vw, 1.5rem);
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.attendance-tabs { display: flex; flex-wrap: wrap; gap: 10px; }

.attendance-tab {
  min-height: 44px;
  min-width: 0;
  padding: 0 14px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--primary);
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid var(--line);
  cursor: pointer;
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
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 251, 250, 0.92));
  box-shadow: 0 10px 28px rgba(31, 92, 89, 0.06);
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
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
  align-items: stretch;
}

.report-filter-grid > * { min-width: 0; }
.report-filter-grid .search-shell-wide { grid-column: 1 / -1; }

.report-filter-grid .field-shell,
.report-filter-grid .search-shell {
  min-height: 52px;
  padding: 9px 12px;
  border-radius: 14px;
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
  gap: 14px;
  min-width: 0;
}

.attendance-user-card {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
}

.attendance-user-head {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-areas:
    "avatar identity"
    "tools tools";
  gap: 10px 12px;
  align-items: center;
  min-width: 0;
}

.attendance-user-head :deep(.user-avatar-face) {
  grid-area: avatar;
  flex-shrink: 0;
}

.attendance-user-identity {
  grid-area: identity;
  min-width: 0;
  display: grid;
  gap: 2px;
}

.attendance-user-tools {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.attendance-user-tools .icon-btn {
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
}

.attendance-user-head strong,
.attendance-user-head small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendance-user-identity strong,
.attendance-user-identity small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendance-user-head small { color: var(--muted); }

.status-badge {
  max-width: 100%;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 750;
  white-space: nowrap;
}

.attendance-mini-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.attendance-mini-grid span { overflow: hidden; }
.attendance-mini-grid b {
  display: block;
  margin-top: 6px;
  color: var(--primary);
  overflow-wrap: anywhere;
}

.attendance-link {
  display: block;
  max-width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(36, 59, 107, 0.05);
  color: var(--primary);
  direction: ltr;
  text-align: left;
  overflow-wrap: anywhere;
  word-break: break-word;
  font-size: 11px;
  line-height: 1.5;
}

.attendance-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.attendance-actions .action-btn {
  width: 100%;
  min-width: 0;
  justify-content: center;
}

.attendance-actions .action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  background: rgba(247, 251, 250, 0.94);
  border: 1px solid var(--line);
  box-shadow: 0 18px 40px rgba(31, 92, 89, 0.1);
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
  gap: 10px;
}

.public-quick-stats article {
  min-width: 0;
  padding: 14px 12px;
  border-radius: 16px;
  background: var(--primary-container);
  border: 1px solid var(--line);
  text-align: center;
}

.public-quick-stats span {
  display: block;
  color: var(--muted);
  font-size: 12px;
}

.public-quick-stats strong {
  display: block;
  margin-top: 6px;
  color: var(--on-primary-container);
  font-size: clamp(1.15rem, 4vw, 1.45rem);
  line-height: 1.2;
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
  gap: 10px;
}

.attendance-punch-btn {
  min-height: 96px;
  display: grid;
  place-items: center;
  gap: 4px;
  padding: 14px 10px;
  border-radius: 16px;
  border: 1px solid transparent;
  color: #fff;
  cursor: pointer;
  font: inherit;
  text-align: center;
  transition: transform 140ms ease, opacity 140ms ease;
  -webkit-tap-highlight-color: transparent;
}

.attendance-punch-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.attendance-punch-btn strong {
  font-size: clamp(0.95rem, 3.6vw, 1.05rem);
}

.attendance-punch-btn small {
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.76rem;
  line-height: 1.4;
}

.attendance-punch-btn.is-in {
  background: var(--button-primary-bg);
  border-color: var(--primary-strong);
  box-shadow: 0 10px 24px rgba(52, 144, 139, 0.28);
}

.attendance-punch-btn.is-out {
  background: var(--button-danger-bg);
  border-color: #a8483c;
  box-shadow: 0 10px 24px rgba(196, 90, 74, 0.22);
}

.attendance-punch-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.attendance-punch-btn :deep(.iconly-shell) {
  --iconly-filter: brightness(0) saturate(100%) invert(100%);
  font-size: clamp(24px, 6vw, 28px);
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
    min-height: 132px;
    padding: 18px 14px;
    gap: 6px;
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
  .attendance-actions { grid-template-columns: 1fr 1fr; }
  .report-hero-actions { width: 100%; }
  .report-hero-actions .action-btn { flex: 1 1 calc(50% - 4px); }
  .report-view-tab { flex: 0 0 auto; width: auto; text-align: center; white-space: nowrap; }
  .report-detail-grid { grid-template-columns: 1fr; }
}

@media (max-width: 560px) {
  .attendance-summary,
  .attendance-users,
  .report-summary-grid,
  .report-summary-grid-wide { grid-template-columns: repeat(2, minmax(0, 1fr)); }

  .attendance-actions { grid-template-columns: 1fr 1fr; }
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
