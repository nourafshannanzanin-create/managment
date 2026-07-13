<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
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
  try {
    publicPayload.value = await apiFetch(`/attendance/public/${route.params.token}`)
  } catch (error) {
    errorMessage.value = error.message
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
        <p>کنترل زنده وضعیت نیروها، لینک اختصاصی هر کاربر و ثبت سریع ورود یا خروج مدیر در یک صفحه متصل به دیتابیس.</p>
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
        <span class="material-symbols-outlined">space_dashboard</span>
        <span>داشبورد</span>
      </button>
      <button :class="['attendance-tab', activeTab === 'reports' && 'is-active']" type="button" @click="switchTab('reports')">
        <span class="material-symbols-outlined">table_chart</span>
        <span>گزارشات</span>
      </button>
    </section>

    <template v-if="activeTab === 'dashboard'">
    <section class="attendance-toolbar">
      <label class="search-shell search-shell-wide">
        <span class="material-symbols-outlined">search</span>
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
        <span class="material-symbols-outlined">refresh</span>
        <span>بروزرسانی</span>
      </button>
    </section>

    <section class="attendance-layout">
      <div class="attendance-users">
        <article v-for="user in filteredUsers" :key="user.id" class="attendance-user-card">
          <div class="attendance-user-head">
            <div class="attendance-avatar">{{ user.avatar || user.name?.slice(0, 1) }}</div>
            <div>
              <strong>{{ user.name }}</strong>
              <small>{{ user.role }} · {{ user.department }}</small>
            </div>
            <span :class="['status-badge', eventTone(user.status)]">{{ statusLabel(user.status) }}</span>
          </div>
          <div class="attendance-mini-grid">
            <span>ثبت امروز <b>{{ fa(user.todayEventsCount) }}</b></span>
            <span>ساعت امروز <b>{{ fa(user.todayWorkedHours) }}</b></span>
          </div>
          <code class="attendance-link">{{ attendanceLink(user) }}</code>
          <div class="attendance-actions">
            <button class="action-btn tone-primary" type="button" :disabled="submitting || user.status === 'in'" @click="submitManagerEvent(user, 'in')">
              <span class="material-symbols-outlined">login</span>
              <span>ثبت ورود</span>
            </button>
            <button class="action-btn tone-soft" type="button" :disabled="submitting || user.status !== 'in'" @click="submitManagerEvent(user, 'out')">
              <span class="material-symbols-outlined">logout</span>
              <span>ثبت خروج</span>
            </button>
            <button class="icon-btn" type="button" title="کپی لینک" @click="copyLink(user)">
              <span class="material-symbols-outlined">content_copy</span>
            </button>
            <a class="icon-btn" title="باز کردن لینک" :href="attendanceLink(user)" target="_blank" rel="noreferrer">
              <span class="material-symbols-outlined">open_in_new</span>
            </a>
          </div>
        </article>
      </div>

      <aside class="surface-block attendance-feed">
        <div class="section-label-row">
          <h3>آخرین رویدادها</h3>
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
            <span class="material-symbols-outlined">search</span>
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
            <span class="material-symbols-outlined">manage_search</span>
            <span>اعمال فیلتر</span>
          </button>
          <button class="action-btn tone-soft" type="button" @click="resetReportFilters">
            <span class="material-symbols-outlined">filter_alt_off</span>
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
      <div class="attendance-public-head">
        <div>
          <span class="page-eyebrow">ورود و خروج</span>
          <h1>{{ publicUser.name || 'پرسنل' }}</h1>
          <p>{{ publicPayload.organization?.name || 'سازمان' }} · {{ statusLabel(publicUser.status) }}</p>
        </div>
        <span :class="['status-badge', eventTone(publicUser.status)]">{{ statusLabel(publicUser.status) }}</span>
      </div>

      <div v-if="errorMessage" class="attendance-alert is-danger">{{ errorMessage }}</div>
      <div v-if="successMessage" class="attendance-alert is-success">{{ successMessage }}</div>

      <div class="public-action-grid">
        <button class="public-action is-in" type="button" :disabled="submitting || publicUser.status === 'in'" @click="submitPublicEvent('in')">
          <span class="material-symbols-outlined">login</span>
          <strong>ثبت ورود</strong>
        </button>
        <button class="public-action is-out" type="button" :disabled="submitting || publicUser.status !== 'in'" @click="submitPublicEvent('out')">
          <span class="material-symbols-outlined">logout</span>
          <strong>ثبت خروج</strong>
        </button>
      </div>

      <label class="public-note">
        <span>یادداشت</span>
        <textarea v-model="note" rows="3" placeholder="مثلا شروع شیفت عصر یا خروج برای ماموریت کوتاه"></textarea>
      </label>

      <div class="public-stats">
        <article><span>ثبت امروز</span><strong>{{ fa(publicUser.todayEventsCount) }}</strong></article>
        <article><span>ساعت امروز</span><strong>{{ fa(publicUser.todayWorkedHours) }}</strong></article>
      </div>

      <div class="public-timeline">
        <article v-for="event in publicEvents" :key="event.id">
          <span :class="['feed-dot', event.eventType]"></span>
          <div>
            <strong>{{ eventLabel(event.eventType) }}</strong>
            <small>{{ dateTime(event.eventAt) }}</small>
          </div>
        </article>
      </div>
    </section>
  </main>
</template>

<style scoped>
.attendance-page { gap: 18px; }
.attendance-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 18px;
  padding: 28px;
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(242,247,244,.96));
  border: 1px solid var(--line);
  box-shadow: var(--shadow-strong);
}
.attendance-hero h1 { margin: 8px 0; color: var(--primary); font-size: clamp(28px, 3vw, 44px); }
.attendance-hero p { margin: 0; color: var(--muted); line-height: 1.9; }
.attendance-summary, .attendance-mini-grid, .public-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.attendance-summary article, .attendance-mini-grid span, .public-stats article {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255,255,255,.76);
  border: 1px solid var(--line);
}
.attendance-summary span, .public-stats span { display: block; color: var(--muted); font-size: 12px; }
.attendance-summary strong, .public-stats strong { display: block; margin-top: 8px; color: var(--primary); font-size: 26px; }
.attendance-tabs { display: flex; flex-wrap: wrap; gap: 10px; }
.attendance-tab {
  min-height: 46px;
  padding: 0 16px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--primary);
  background: rgba(255,255,255,.74);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-soft);
  cursor: pointer;
}
.attendance-tab.is-active {
  color: #fff;
  background: linear-gradient(135deg, var(--primary), #287a6e);
}
.attendance-toolbar { display: grid; grid-template-columns: minmax(0, 1fr) 220px auto; gap: 12px; align-items: stretch; }
.attendance-report-panel { display: grid; gap: 14px; }
.report-filter-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1.4fr) repeat(2, minmax(132px, .72fr)) minmax(170px, .9fr) minmax(132px, .7fr) minmax(128px, auto) minmax(118px, auto);
  gap: 10px;
  align-items: stretch;
}
.report-filter-grid > * {
  min-width: 0;
}
.report-filter-grid .search-shell-wide {
  min-width: 0;
}
.report-filter-grid .field-shell,
.report-filter-grid .search-shell {
  min-height: 54px;
  padding: 9px 12px;
  border-radius: 15px;
}
.report-filter-grid .field-shell {
  gap: 5px;
}
.report-filter-grid .field-shell span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}
.report-filter-grid input,
.report-filter-grid select {
  width: 100%;
  min-width: 0;
}
.report-filter-grid .action-btn {
  min-height: 54px;
  padding: 0 12px;
  white-space: nowrap;
}
.report-summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.report-summary-grid article {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255,255,255,.82);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-soft);
}
.report-summary-grid span { display: block; color: var(--muted); font-size: 12px; }
.report-summary-grid strong { display: block; margin-top: 8px; color: var(--primary); font-size: 24px; }
.report-table-card { display: grid; gap: 14px; }
.report-table-head { align-items: center; }
.table-count {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: rgba(36,59,107,.08);
  color: var(--primary);
  font-weight: 800;
  font-size: 12px;
}
.attendance-table-wrap {
  overflow: auto;
  border-radius: 18px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,.56);
}
.attendance-report-table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
}
.attendance-report-table th,
.attendance-report-table td {
  padding: 13px 14px;
  border-bottom: 1px solid rgba(36,59,107,.08);
  text-align: right;
  vertical-align: middle;
  white-space: nowrap;
}
.attendance-report-table th {
  color: var(--muted);
  font-size: 12px;
  background: rgba(216,175,140,.16);
}
.attendance-report-table tbody tr:hover { background: rgba(40,122,110,.06); }
.attendance-layout { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 16px; align-items: start; }
.attendance-users { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.attendance-user-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255,255,255,.88);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-soft);
}
.attendance-user-head { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 12px; align-items: center; }
.attendance-avatar { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 16px; background: linear-gradient(135deg, var(--primary), #287a6e); color: #fff; font-weight: 900; }
.attendance-user-head strong, .attendance-user-head small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attendance-user-head small { color: var(--muted); }
.attendance-mini-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.attendance-mini-grid b { display: block; margin-top: 6px; color: var(--primary); }
.attendance-link { padding: 10px 12px; border-radius: 14px; background: rgba(36,59,107,.05); color: var(--primary); direction: ltr; overflow-wrap: anywhere; }
.attendance-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.attendance-actions .action-btn:disabled, .public-action:disabled { opacity: .5; cursor: not-allowed; }
.attendance-feed { display: grid; gap: 10px; }
.attendance-feed-row, .public-timeline article { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 10px; align-items: center; padding: 12px; border-radius: 16px; background: rgba(255,255,255,.72); border: 1px solid var(--line); }
.attendance-feed-row small, .public-timeline small { display: block; color: var(--muted); }
.feed-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--warning); box-shadow: 0 0 0 6px rgba(140,109,59,.12); }
.feed-dot.in { background: var(--success); box-shadow: 0 0 0 6px rgba(74,107,88,.12); }
.attendance-alert { padding: 12px 14px; border-radius: 16px; border: 1px solid var(--line); }
.attendance-alert.is-danger { background: var(--danger-soft); color: var(--danger); }
.attendance-alert.is-success { background: var(--success-soft); color: var(--success); }
.status-badge.is-success { background: var(--success-soft); color: var(--success); }
.status-badge.is-warning { background: var(--warning-soft); color: var(--warning); }
.attendance-public { min-height: 100vh; display: grid; place-items: center; padding: 18px; background: linear-gradient(135deg, #f7f1eb, #edf6f1); color: var(--text); }
.attendance-public-card { width: min(760px, 100%); display: grid; gap: 16px; padding: 24px; border-radius: 28px; background: rgba(255,255,255,.9); border: 1px solid var(--line); box-shadow: var(--shadow-strong); }
.attendance-public-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.attendance-public-head h1 { margin: 8px 0 4px; color: var(--primary); font-size: clamp(26px, 5vw, 42px); }
.attendance-public-head p { margin: 0; color: var(--muted); }
.public-action-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.public-action { min-height: 132px; display: grid; place-items: center; gap: 8px; border-radius: 22px; color: #fff; box-shadow: var(--shadow-soft); }
.public-action .material-symbols-outlined { font-size: 34px; }
.public-action.is-in { background: linear-gradient(135deg, #287a6e, #2f9f80); }
.public-action.is-out { background: linear-gradient(135deg, #944f54, #c1755d); }
.public-note { display: grid; gap: 8px; }
.public-note span { color: var(--muted); font-weight: 800; }
.public-note textarea { min-height: 92px; padding: 14px; border-radius: 18px; background: rgba(36,59,107,.05); border: 1px solid var(--line); resize: vertical; }
.public-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.public-timeline { display: grid; gap: 10px; }
@media (max-width: 1100px) {
  .attendance-hero, .attendance-layout { grid-template-columns: 1fr; }
  .attendance-users { grid-template-columns: 1fr; }
  .report-filter-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .report-filter-grid .search-shell { grid-column: span 3; }
  .report-summary-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .attendance-hero, .attendance-public-card { padding: 16px; border-radius: 22px; }
  .attendance-toolbar, .attendance-summary, .public-action-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .attendance-toolbar .search-shell { grid-column: 1 / -1; }
  .attendance-user-head, .attendance-public-head { grid-template-columns: 1fr; display: grid; }
  .attendance-tab { flex: 1 1 0; justify-content: center; }
  .report-filter-grid, .report-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .report-filter-grid .search-shell { grid-column: 1 / -1; }
  .report-filter-grid .action-btn { min-width: 0; }
}
@media (max-width: 460px) {
  .report-filter-grid {
    grid-template-columns: 1fr;
  }
  .report-filter-grid .search-shell {
    grid-column: auto;
  }
  .report-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
