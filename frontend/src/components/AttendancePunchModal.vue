<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import LocationMapPicker from './LocationMapPicker.vue'
import UserAvatar from './UserAvatar.vue'
import { haversineDistanceMeters, readDeviceLocation } from '../lib/geolocation'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatTehranDateTime, getJalaliMonthLabel, getTodayJalali, shiftJalaliMonth } from '../utils/jalali'

const props = defineProps({
  open: { type: Boolean, default: false },
  token: { type: String, default: '' },
})

const emit = defineEmits(['close'])

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const { state } = useWorkflowHub()

const todayJalali = getTodayJalali()
const activeTab = ref('punch')
const loading = ref(false)
const submitting = ref(false)
const locationBusy = ref(false)
const reportLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const locationHint = ref('')
const note = ref('')
const liveUserLocation = ref(null)
const liveDistanceMeters = ref(null)
const publicPayload = ref({ user: {}, events: [], organization: {}, location: {} })
const reportPayload = ref(null)
const reportJalaliYear = ref(todayJalali.jy)
const reportJalaliMonth = ref(todayJalali.jm)

const fa = (value) => Number(value || 0).toLocaleString('fa-IR')
const faText = (value) => String(value ?? '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[Number(digit)])
const eventLabel = (type) => (type === 'in' ? 'ورود' : 'خروج')
const statusLabel = (type) => (type === 'in' ? 'حاضر' : 'خارج از شیفت')
const eventTone = (type) => (type === 'in' ? 'is-success' : 'is-warning')
const dateTime = (value) => {
  if (!value) return '-'
  return formatTehranDateTime(value)
}

const publicUser = computed(() => publicPayload.value.user || {})
const publicEvents = computed(() => publicPayload.value.events || [])
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
const reportSummary = computed(() => reportPayload.value?.summary || {})
const reportDays = computed(() => reportPayload.value?.days || [])
const reportMonthLabel = computed(() => getJalaliMonthLabel(reportJalaliYear.value, reportJalaliMonth.value))
const reportQuery = computed(
  () =>
    `jalaliYear=${encodeURIComponent(reportJalaliYear.value)}&jalaliMonth=${encodeURIComponent(reportJalaliMonth.value)}`,
)

function shiftReportMonth(delta) {
  const next = shiftJalaliMonth(reportJalaliYear.value, reportJalaliMonth.value, delta)
  reportJalaliYear.value = next.jy
  reportJalaliMonth.value = next.jm
  void loadMonthlyReport()
}

async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || payload.message || 'درخواست ناموفق بود.')
  return payload
}

async function authFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (state.authToken) headers.Authorization = `Bearer ${state.authToken}`
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (options.expectBlob) {
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(payload.detail || payload.message || 'دانلود ناموفق بود.')
    }
    return response.blob()
  }
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || payload.message || 'درخواست ناموفق بود.')
  return payload
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
  if (!props.token) {
    errorMessage.value = 'لینک ورود و خروج برای این کاربر یافت نشد.'
    return
  }
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  locationHint.value = ''
  try {
    publicPayload.value = await apiFetch(`/attendance/public/${props.token}`)
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

async function loadMonthlyReport() {
  reportLoading.value = true
  errorMessage.value = ''
  try {
    reportPayload.value = await authFetch(`/attendance/my-report?${reportQuery.value}`)
  } catch (error) {
    reportPayload.value = null
    errorMessage.value = error.message
  } finally {
    reportLoading.value = false
  }
}

async function downloadReportCsv() {
  try {
    const blob = await authFetch(`/attendance/my-report?${reportQuery.value}&format=csv`, { expectBlob: true })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `attendance-${reportJalaliYear.value}-${reportJalaliMonth.value}.csv`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    errorMessage.value = error.message
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
    publicPayload.value = await apiFetch(`/attendance/public/${props.token}`, {
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

watch(
  () => [props.open, props.token],
  ([isOpen]) => {
    if (!isOpen) return
    activeTab.value = 'punch'
    note.value = ''
    successMessage.value = ''
    errorMessage.value = ''
    liveUserLocation.value = null
    liveDistanceMeters.value = null
    void loadPublic()
  },
)

watch(activeTab, (tab) => {
  if (tab === 'report' && props.open) void loadMonthlyReport()
})
</script>

<template>
  <BaseModal :open="open" size="wide" @close="emit('close')">
    <div class="attendance-punch-modal" dir="rtl">
      <div v-if="loading && !publicUser.id" class="attendance-punch-loading">
        <span class="attendance-punch-spinner" aria-hidden="true"></span>
        در حال بارگذاری ورود و خروج…
      </div>

      <template v-else-if="errorMessage && !publicUser.id && activeTab === 'punch'">
        <div class="modal-headline">
          <p class="page-eyebrow">ورود و خروج</p>
          <h2>ثبت حضور</h2>
        </div>
        <div class="attendance-alert is-danger">{{ errorMessage }}</div>
      </template>

      <template v-else>
        <header class="attendance-punch-head">
          <div class="attendance-punch-identity">
            <UserAvatar
              :name="publicUser.name || publicUser.fullName || publicUser.full_name"
              :avatar="publicUser.avatar"
              :avatar-url="publicUser.avatarUrl || publicUser.avatar_url"
              size="lg"
            />
            <div>
              <span class="page-eyebrow">ثبت ورود و خروج</span>
              <h2>{{ publicUser.name || publicUser.fullName || publicUser.full_name || 'پرسنل' }}</h2>
              <p>
                {{ publicPayload.organization?.name || 'سازمان' }}
                <template v-if="publicUser.department"> · {{ publicUser.department }}</template>
              </p>
            </div>
          </div>
          <span :class="['status-badge status-badge-lg', eventTone(publicUser.status)]">{{ statusLabel(publicUser.status) }}</span>
        </header>

        <div class="chip-row attendance-tabs">
          <button :class="['filter-chip', activeTab === 'punch' && 'is-active']" type="button" @click="activeTab = 'punch'">ورود / خروج</button>
          <button :class="['filter-chip', activeTab === 'report' && 'is-active']" type="button" @click="activeTab = 'report'">گزارش حضور</button>
        </div>

        <template v-if="activeTab === 'punch'">
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
              height="240px"
              :can-edit="false"
              :show-radius="true"
              :user-location="liveUserLocation"
            />
            <button class="action-btn tone-primary public-locate-btn" type="button" :disabled="locationBusy || submitting" @click="refreshLiveLocation">
              <IconlyIcon name="profile" decorative />
              <span>{{ locationBusy ? 'در حال دریافت موقعیت...' : (liveUserLocation ? 'بروزرسانی موقعیت من' : 'اجازه موقعیت و یافتن من') }}</span>
            </button>
          </div>

          <div v-if="publicUser.id" class="attendance-punch-grid">
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

          <label class="public-note">
            <span>یادداشت (اختیاری)</span>
            <textarea v-model="note" rows="2" placeholder="مثلا شروع شیفت عصر یا خروج برای ماموریت کوتاه"></textarea>
          </label>

          <div class="public-timeline">
            <h3 class="public-timeline-title">رویدادهای امروز</h3>
            <p v-if="!publicEvents.length" class="attendance-punch-hint">هنوز رویدادی برای امروز ثبت نشده است.</p>
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

        <template v-else>
          <div class="report-toolbar">
            <div class="report-month-nav">
              <button class="icon-btn report-nav-btn" type="button" aria-label="ماه قبل" :disabled="reportLoading" @click="shiftReportMonth(-1)">‹</button>
              <div class="report-month-label">
                <span>ماه گزارش</span>
                <strong>{{ faText(reportMonthLabel) }}</strong>
              </div>
              <button class="icon-btn report-nav-btn" type="button" aria-label="ماه بعد" :disabled="reportLoading" @click="shiftReportMonth(1)">›</button>
            </div>
            <div class="report-toolbar-actions">
              <button class="action-btn tone-soft" type="button" :disabled="reportLoading" @click="loadMonthlyReport">
                <IconlyIcon name="refresh" decorative />
                <span>{{ reportLoading ? 'در حال بارگذاری...' : 'بروزرسانی' }}</span>
              </button>
              <button class="action-btn tone-primary" type="button" :disabled="reportLoading || !reportPayload" @click="downloadReportCsv">
                <IconlyIcon name="download" decorative />
                <span>دانلود CSV</span>
              </button>
            </div>
          </div>

          <div v-if="errorMessage" class="attendance-alert is-danger">{{ errorMessage }}</div>

          <div class="report-table-wrap">
            <table class="report-table">
              <thead>
                <tr>
                  <th>تاریخ</th>
                  <th>روز</th>
                  <th>ورود/خروج</th>
                  <th>کارکرد</th>
                  <th>مرخصی</th>
                  <th>اضافه‌کار</th>
                  <th>کمبود</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="day in reportDays" :key="day.date">
                  <td class="report-date-cell" dir="ltr">{{ faText(day.jalaliDate || day.date) }}</td>
                  <td>{{ day.weekday || '—' }}</td>
                  <td>
                    <span v-for="punch in day.punches" :key="`${day.date}-${punch.id}`" class="punch-chip">
                      {{ eventLabel(punch.type) }} {{ faText(punch.time) }}
                    </span>
                    <span v-if="!day.punches?.length">—</span>
                  </td>
                  <td>{{ fa(day.workedHours) }}</td>
                  <td>{{ fa(day.leaveHours) }}</td>
                  <td>{{ fa(day.overtimeHours) }}</td>
                  <td>{{ fa(day.shortageHours) }}</td>
                </tr>
              </tbody>
            </table>
            <p v-if="!reportDays.length && !reportLoading" class="attendance-punch-hint">برای این ماه داده‌ای ثبت نشده است.</p>
          </div>

          <footer v-if="reportPayload" class="report-footer">
            <div class="report-footer-title">
              <span>جمع ماه</span>
              <strong>{{ faText(reportMonthLabel) }}</strong>
            </div>
            <div class="report-footer-grid">
              <article><span>کارکرد</span><strong>{{ fa(reportSummary.workedHours) }}</strong></article>
              <article><span>اضافه‌کار</span><strong>{{ fa(reportSummary.overtimeHours) }}</strong></article>
              <article><span>کمبود</span><strong>{{ fa(reportSummary.shortageHours) }}</strong></article>
              <article><span>مرخصی</span><strong>{{ fa(reportSummary.leaveHours) }}</strong></article>
              <article><span>باقیمانده سهمیه</span><strong>{{ fa(reportSummary.leaveRemaining) }}</strong></article>
              <article><span>مرخصی مازاد</span><strong>{{ fa(reportSummary.unpaidLeaveHours) }}</strong></article>
            </div>
          </footer>
        </template>
      </template>
    </div>
  </BaseModal>
</template>

<style scoped>
.attendance-punch-modal {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.attendance-punch-loading {
  display: grid;
  place-items: center;
  gap: 12px;
  min-height: 180px;
  color: var(--muted, #5c6780);
  font-weight: 700;
}

.attendance-punch-spinner {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  border: 3px solid rgba(52, 144, 139, 0.2);
  border-top-color: #34908B;
  animation: attendance-punch-spin 0.8s linear infinite;
}

@keyframes attendance-punch-spin {
  to { transform: rotate(360deg); }
}

.attendance-punch-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.attendance-punch-identity {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.attendance-punch-identity > div {
  min-width: 0;
}

.attendance-punch-identity h2 {
  margin: 4px 0 0;
  font-size: 1.25rem;
  line-height: 1.35;
}

.attendance-punch-identity p {
  margin: 4px 0 0;
  color: var(--muted, #5c6780);
  font-size: 0.88rem;
}

.attendance-tabs {
  flex-wrap: wrap;
}

.public-quick-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.public-quick-stats article {
  padding: 12px;
  border-radius: 14px;
  background: rgba(52, 144, 139, 0.08);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.public-quick-stats span {
  display: block;
  color: var(--muted, #5c6780);
  font-size: 12px;
}

.public-quick-stats strong {
  display: block;
  margin-top: 4px;
  font-size: 1.15rem;
}

.report-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.report-month-nav {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.report-nav-btn {
  width: 34px !important;
  height: 34px !important;
  min-width: 34px !important;
  min-height: 34px !important;
  font-size: 1.35rem !important;
  line-height: 1 !important;
  font-weight: 700 !important;
}

.report-month-label {
  display: grid;
  gap: 2px;
  min-width: 140px;
  text-align: center;
}

.report-month-label span {
  color: var(--muted, #5c6780);
  font-size: 11px;
  font-weight: 700;
}

.report-month-label strong {
  font-size: 1.05rem;
}

.report-toolbar-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
}

.report-table-wrap {
  overflow: auto;
  max-height: min(52vh, 480px);
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 14px;
  background: #fff;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.report-table th,
.report-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(52, 144, 139, 0.1);
  text-align: right;
  white-space: nowrap;
}

.report-table th {
  position: sticky;
  top: 0;
  background: transparent;
  color: #1f5c59;
  font-weight: 800;
  z-index: 1;
}

.report-date-cell {
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  font-weight: 700;
}

.punch-chip {
  display: inline-block;
  margin-inline-start: 4px;
  padding: 2px 6px;
  border-radius: 8px;
  background: rgba(52, 144, 139, 0.1);
  font-size: 0.78rem;
}

.report-footer {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(52, 144, 139, 0.08);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.report-footer-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.report-footer-title span {
  color: var(--muted, #5c6780);
  font-size: 12px;
  font-weight: 700;
}

.report-footer-title strong {
  font-size: 1rem;
}

.report-footer-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}

.report-footer-grid article {
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
}

.report-footer-grid span {
  display: block;
  color: var(--muted, #5c6780);
  font-size: 11px;
}

.report-footer-grid strong {
  display: block;
  margin-top: 4px;
  font-size: 1.05rem;
}

.attendance-punch-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.attendance-punch-btn {
  display: grid;
  gap: 6px;
  justify-items: center;
  padding: 18px 12px;
  border: 0;
  border-radius: 16px;
  color: #fff;
  cursor: pointer;
}

.attendance-punch-btn.is-in {
  background: #1f8a70;
}

.attendance-punch-btn.is-out {
  background: #c2410c;
}

.attendance-punch-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.attendance-punch-btn strong {
  font-size: 1.05rem;
}

.attendance-punch-btn small {
  opacity: 0.9;
}

.public-note,
.public-map-block,
.public-timeline {
  display: grid;
  gap: 8px;
}

.public-note textarea {
  width: 100%;
  min-height: 64px;
  resize: vertical;
}

.public-locate-btn {
  justify-self: start;
}

.public-timeline article {
  display: grid;
  grid-template-columns: 12px 1fr;
  gap: 10px;
  align-items: start;
  padding: 8px 0;
  border-bottom: 1px solid rgba(52, 144, 139, 0.1);
}

.public-timeline-title {
  margin: 0;
  font-size: 1rem;
}

.attendance-punch-hint {
  margin: 0;
  color: var(--muted, #5c6780);
}

.public-event-note {
  display: block;
  color: var(--muted, #5c6780);
}

.feed-dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 999px;
  background: #94a3b8;
}

.feed-dot.in {
  background: #1f8a70;
}

.feed-dot.out {
  background: #c2410c;
}

.attendance-alert {
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 0.9rem;
}

.attendance-alert.is-danger {
  background: rgba(185, 28, 28, 0.08);
  color: #991b1b;
}

.attendance-alert.is-success {
  background: rgba(21, 128, 61, 0.1);
  color: #166534;
}

.attendance-alert.is-warning,
.attendance-alert.is-info {
  background: rgba(161, 98, 7, 0.1);
  color: #92400e;
}

@media (max-width: 920px) {
  .report-footer-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .attendance-punch-grid,
  .public-quick-stats,
  .report-footer-grid {
    grid-template-columns: 1fr;
  }

  .report-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .report-toolbar-actions {
    width: 100%;
  }

  .report-toolbar-actions .action-btn {
    flex: 1;
  }
}
</style>
