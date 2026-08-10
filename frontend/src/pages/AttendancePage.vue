<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import SectionHeading from '../components/SectionHeading.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { jalaliToIso } from '../utils/jalali'

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
const reportPayload = ref({ summary: {}, rows: [], users: [] })
const reportFilters = ref({
  q: '',
  start: '',
  end: '',
  userId: '',
  eventType: 'all',
})
const publicPayload = ref({ user: {}, events: [], organization: {} })
const isPublic = computed(() => Boolean(route.params.token))

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
const reportRows = computed(() => reportPayload.value.rows || [])
const reportUsers = computed(() => reportPayload.value.users || dashboard.value.users || [])
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

function resetReportFilters() {
  reportFilters.value = { q: '', start: '', end: '', userId: '', eventType: 'all' }
  void loadReports()
}

async function loadPublic() {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    publicPayload.value = await apiFetch(`/attendance/public/${route.params.token}`)
  } catch (error) {
    errorMessage.value = error.message
    publicPayload.value = { user: {}, events: [], organization: {} }
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
  errorMessage.value = ''
  successMessage.value = ''
  try {
    publicPayload.value = await apiFetch(`/attendance/public/${route.params.token}`, {
      method: 'POST',
      body: JSON.stringify({ eventType, note: note.value }),
    })
    successMessage.value = `${eventLabel(eventType)} با موفقیت ثبت شد.`
    note.value = ''
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

async function copyLink(user) {
  await navigator.clipboard.writeText(attendanceLink(user))
  successMessage.value = 'لینک ورود و خروج کپی شد.'
}

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
    <section class="attendance-toolbar">
      <label class="search-shell search-shell-wide">
        <IconlyIcon name="search" decorative />
        <input v-model="search" type="text" placeholder="جستجو در نام، سمت، بخش یا موبایل..." />
      </label>
      <label class="field-shell">
        <span>وضعیت</span>
        <select v-model="statusFilter">
          <option value="all">همه</option>
          <option value="in">حاضر</option>
          <option value="out">خارج از شیفت</option>
        </select>
      </label>
      <button class="action-btn tone-soft" type="button" @click="loadDashboard">
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
            <div>
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
        <div class="report-filter-grid">
          <label class="search-shell search-shell-wide">
            <IconlyIcon name="search" decorative />
            <input v-model="reportFilters.q" type="text" placeholder="جستجو در نام، سمت، بخش یا یادداشت..." @keyup.enter="loadReports" />
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
            <span>نوع رویداد</span>
            <select v-model="reportFilters.eventType">
              <option value="all">همه</option>
              <option value="in">ورود</option>
              <option value="out">خروج</option>
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

        <div class="report-summary-grid">
          <article><span>کل رویدادها</span><strong>{{ fa(reportSummary.total) }}</strong></article>
          <article><span>ورودها</span><strong>{{ fa(reportSummary.checkins) }}</strong></article>
          <article><span>خروج‌ها</span><strong>{{ fa(reportSummary.checkouts) }}</strong></article>
          <article><span>ثبت با لینک</span><strong>{{ fa(reportSummary.linkEvents) }}</strong></article>
          <article><span>ثبت مدیر</span><strong>{{ fa(reportSummary.managerEvents) }}</strong></article>
        </div>

        <section class="surface-block report-table-card">
          <div class="section-label-row report-table-head">
            <div>
              <h3>جدول گزارشات ورود و خروج</h3>
            </div>
            <span class="table-count">{{ fa(reportRows.length) }} ردیف</span>
          </div>

          <div class="attendance-table-wrap">
            <table class="attendance-report-table">
              <thead>
                <tr>
                  <th>ردیف</th>
                  <th>نام پرسنل</th>
                  <th>سمت</th>
                  <th>بخش</th>
                  <th>نوع</th>
                  <th>منبع ثبت</th>
                  <th>زمان</th>
                  <th>یادداشت</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in reportRows" :key="row.id">
                  <td>{{ fa(row.row) }}</td>
                  <td><strong>{{ row.userName }}</strong></td>
                  <td>{{ row.userRole || '-' }}</td>
                  <td>{{ row.userDepartment || '-' }}</td>
                  <td><span :class="['status-badge', eventTone(row.eventType)]">{{ eventLabel(row.eventType) }}</span></td>
                  <td>{{ row.source === 'manager' ? 'ثبت مدیر' : 'لینک پرسنل' }}</td>
                  <td>{{ dateTime(row.eventAt) }}</td>
                  <td>{{ row.note || '-' }}</td>
                </tr>
                <tr v-if="!reportRows.length">
                  <td colspan="8">گزارشی برای این فیلترها پیدا نشد.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </template>
  </section>

  <main v-else class="attendance-public" dir="rtl">
    <section class="attendance-public-card">
      <div v-if="loading && !publicUser.id" class="attendance-public-loading">
        در حال بارگذاری لینک ورود و خروج…
      </div>

      <template v-else-if="errorMessage && !publicUser.id">
        <div class="attendance-alert is-danger">{{ errorMessage }}</div>
        <p class="attendance-public-hint">اگر لینک را از مدیر دریافت کرده‌اید، دوباره امتحان کنید یا لینک تازه بخواهید.</p>
      </template>

      <template v-else>
        <div class="attendance-public-head">
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
          <span :class="['status-badge', eventTone(publicUser.status)]">{{ statusLabel(publicUser.status) }}</span>
        </div>

        <div v-if="errorMessage" class="attendance-alert is-danger">{{ errorMessage }}</div>
        <div v-if="successMessage" class="attendance-alert is-success">{{ successMessage }}</div>

        <div class="attendance-punch-grid">
          <button
            class="attendance-punch-btn is-in"
            type="button"
            :disabled="submitting || publicUser.status === 'in'"
            @click="submitPublicEvent('in')"
          >
            <IconlyIcon name="login" size="xl" decorative />
            <strong>ثبت ورود</strong>
            <small>{{ publicUser.status === 'in' ? 'الان حاضر هستید' : 'شروع شیفت' }}</small>
          </button>
          <button
            class="attendance-punch-btn is-out"
            type="button"
            :disabled="submitting || publicUser.status !== 'in'"
            @click="submitPublicEvent('out')"
          >
            <IconlyIcon name="logout" size="xl" decorative />
            <strong>ثبت خروج</strong>
            <small>{{ publicUser.status === 'in' ? 'پایان شیفت' : 'ابتدا ورود ثبت کنید' }}</small>
          </button>
        </div>

        <label class="public-note">
          <span>یادداشت (اختیاری)</span>
          <textarea v-model="note" rows="3" placeholder="مثلا شروع شیفت عصر یا خروج برای ماموریت کوتاه"></textarea>
        </label>

        <div class="public-stats">
          <article><span>ثبت امروز</span><strong>{{ fa(publicUser.todayEventsCount) }}</strong></article>
          <article><span>ساعت امروز</span><strong>{{ fa(publicUser.todayWorkedHours) }}</strong></article>
        </div>

        <div class="public-timeline">
          <h2 class="public-timeline-title">رویدادهای امروز</h2>
          <p v-if="!publicEvents.length" class="attendance-public-hint">هنوز رویدادی برای امروز ثبت نشده است.</p>
          <article v-for="event in publicEvents" :key="event.id">
            <span :class="['feed-dot', event.eventType || event.event_type]"></span>
            <div>
              <strong>{{ eventLabel(event.eventType || event.event_type) }}</strong>
              <small>{{ dateTime(event.eventAt || event.event_at) }}</small>
              <small v-if="event.note" class="public-event-note">{{ event.note }}</small>
            </div>
          </article>
        </div>
      </template>
    </section>
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
  grid-template-columns: minmax(0, 1fr) minmax(140px, 200px) auto;
  gap: 12px;
  align-items: stretch;
  min-width: 0;
}

.attendance-toolbar > * { min-width: 0; }
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
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.attendance-avatar {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: #dcefec;
  color: #1f5c59;
  font-weight: 800;
}

.attendance-user-head > div { min-width: 0; }

.attendance-user-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
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
  min-height: 100%;
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 18px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 14% 16%, rgba(52, 144, 139, 0.22), transparent 40%),
    radial-gradient(circle at 86% 10%, rgba(31, 92, 89, 0.12), transparent 34%),
    linear-gradient(180deg, #e6f2ef 0%, #f3f9f7 48%, #dcefec 100%);
  color: var(--text);
}

.attendance-public-card {
  width: min(760px, 100%);
  display: grid;
  gap: 16px;
  padding: 24px;
  border-radius: 18px;
  background: var(--surface-strong);
  border: 1px solid var(--line);
  box-shadow: 0 18px 40px rgba(31, 92, 89, 0.12);
  min-width: 0;
}

.attendance-public-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
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
  margin: 8px 0 4px;
  color: var(--primary);
  font-size: clamp(1.35rem, 4vw, 2rem);
  overflow-wrap: break-word;
}

.attendance-public-head p { margin: 0; color: var(--muted); }

.attendance-public-loading,
.attendance-public-hint {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.attendance-punch-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.attendance-punch-btn {
  min-height: 132px;
  display: grid;
  place-items: center;
  gap: 6px;
  padding: 18px 14px;
  border-radius: 16px;
  border: 1px solid transparent;
  color: #fff;
  cursor: pointer;
  font: inherit;
  text-align: center;
}

.attendance-punch-btn strong {
  font-size: 1.05rem;
}

.attendance-punch-btn small {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.82rem;
}

.attendance-punch-btn.is-in {
  background: var(--button-primary-bg);
  border-color: var(--primary-strong);
}

.attendance-punch-btn.is-out {
  background: var(--button-danger-bg);
  border-color: #a8483c;
}

.attendance-punch-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.attendance-punch-btn :deep(.iconly-shell) {
  --iconly-filter: brightness(0) saturate(100%) invert(100%);
  font-size: 28px;
}

.public-note { display: grid; gap: 8px; min-width: 0; }
.public-note span { color: var(--muted); font-weight: 800; }

.public-note textarea {
  width: 100%;
  min-height: 92px;
  padding: 14px;
  border-radius: 14px;
  background: var(--surface-container-low);
  border: 1px solid var(--line);
  resize: vertical;
  box-sizing: border-box;
  color: var(--text);
  font: inherit;
}

.public-note textarea:focus {
  outline: 2px solid rgba(52, 144, 139, 0.28);
  border-color: var(--primary);
}

.public-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }

.attendance-public .public-stats article {
  background: var(--primary-container);
  border-color: var(--line);
}

.attendance-public .public-stats strong {
  color: var(--on-primary-container);
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
}

@media (max-width: 1100px) {
  .attendance-hero,
  .attendance-layout { grid-template-columns: 1fr; }
  .report-summary-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 760px) {
  .attendance-hero { padding: 16px; }
  .attendance-toolbar { grid-template-columns: 1fr; }
  .attendance-users,
  .report-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .attendance-tab { flex: 1 1 calc(50% - 5px); }
  .attendance-actions { grid-template-columns: 1fr 1fr; }
  .attendance-public-head { flex-direction: column; }
  .attendance-punch-grid { grid-template-columns: 1fr; }
}

@media (max-width: 560px) {
  .attendance-summary,
  .attendance-users,
  .report-summary-grid { grid-template-columns: 1fr; }

  .attendance-user-head { grid-template-columns: auto minmax(0, 1fr); }
  .attendance-user-tools {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .attendance-actions { grid-template-columns: 1fr 1fr; }
  .attendance-tab { flex: 1 1 100%; }
}
</style>
