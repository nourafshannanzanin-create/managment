<script setup>
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import IconlyIcon from './base/IconlyIcon.vue'
import SectionHeading from './SectionHeading.vue'
import TimePicker from './TimePicker.vue'
import UserAvatar from './UserAvatar.vue'
import {
  buildTodayPairs,
  eventDateOf,
  eventTimeOf,
  groupEventsByPerson,
  groupPersonDays,
} from '../utils/attendanceReport'
import { parseTimeValue, toPersianDigits } from '../utils/duration'
import { formatJalaliLong, gregorianToJalali, persianWeekdayFromIso } from '../utils/jalali'
import { joinDisplayParts } from '../utils/text'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'

const props = defineProps({
  events: { type: Array, default: () => [] },
  mode: { type: String, default: 'period' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  canEditTimes: { type: Boolean, default: true },
})

const emit = defineEmits(['updated'])

const selectedUserId = ref('')
const drafts = reactive({})
const originals = reactive({})
const createDrafts = reactive({})
const savingIds = ref(new Set())
const savingAll = ref(false)
const creatingKey = ref('')
const boardError = ref('')
const boardNotice = ref('')
const modalError = ref('')
const modalNotice = ref('')

const isTodayMode = computed(() => props.mode === 'today')
const people = computed(() => groupEventsByPerson(props.events))
const todayPairs = computed(() => buildTodayPairs(props.events))
const selectedPerson = computed(() => people.value.find((person) => String(person.userId) === String(selectedUserId.value)) || null)
const selectedDays = computed(() => (selectedPerson.value ? groupPersonDays(selectedPerson.value.events) : []))

const dirtyIds = computed(() =>
  Object.keys(drafts).filter((id) => {
    const next = normalizeTime(drafts[id])
    const previous = normalizeTime(originals[id])
    return next && next !== previous
  }),
)

const todaySummary = computed(() => {
  const ins = todayPairs.value.filter((row) => row.inEvent).length
  const outs = todayPairs.value.filter((row) => row.outEvent).length
  const names = new Set(todayPairs.value.map((row) => row.userId))
  return { ins, outs, people: names.size }
})

function fa(value) {
  return toPersianDigits(value ?? 0)
}

function normalizeTime(value) {
  const text = String(value || '').trim()
  if (!text) return ''
  return parseTimeValue(text, '')
}

function sourceLabel(source) {
  return source === 'manager' ? 'ثبت مدیر' : 'لینک پرسنل'
}

function formatHours(minutes) {
  const total = Math.max(0, Number(minutes) || 0)
  if (!total) return '۰'
  const hours = Math.floor(total / 60)
  const rest = total % 60
  if (!hours) return `${fa(rest)} دقیقه`
  if (!rest) return `${fa(hours)} ساعت`
  return `${fa(hours)}:${fa(String(rest).padStart(2, '0'))}`
}

function formatDayTitle(iso) {
  const day = String(iso || '').slice(0, 10)
  const match = day.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  const weekday = persianWeekdayFromIso(day)
  if (!match) return weekday || day
  return joinDisplayParts([weekday, formatJalaliLong(gregorianToJalali(Number(match[1]), Number(match[2]), Number(match[3])))])
}

function personMetaLine(person) {
  return joinDisplayParts([person.userRole, person.userDepartment])
}

function todayIsoDate() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function createDraftKey(userId, eventType, date, pairIndex = 0) {
  return `${userId}:${eventType}:${date}:${pairIndex}`
}

function ensureCreateDraft(key, fallback = '17:00') {
  if (!createDrafts[key]) createDrafts[key] = fallback
  return createDrafts[key]
}

function resetDrafts(person) {
  Object.keys(drafts).forEach((key) => delete drafts[key])
  Object.keys(originals).forEach((key) => delete originals[key])
  if (!person) return
  for (const event of person.events) {
    const time = eventTimeOf(event)
    drafts[event.id] = time
    originals[event.id] = time
  }
}

function openPerson(person) {
  selectedUserId.value = person.userId
  modalError.value = ''
  modalNotice.value = ''
  boardError.value = ''
  resetDrafts(person)
}

function closePerson() {
  if (savingAll.value || savingIds.value.size || creatingKey.value) return
  selectedUserId.value = ''
  modalError.value = ''
  modalNotice.value = ''
  resetDrafts(null)
}

function isDirty(eventId) {
  return normalizeTime(drafts[eventId]) !== normalizeTime(originals[eventId])
}

function isSaving(eventId) {
  return savingIds.value.has(String(eventId))
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}`,
  }
}

async function patchEventTime(eventId, time) {
  const response = await fetch(`${API_BASE_URL}/attendance/events/${eventId}`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify({ time }),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || payload.message || 'ذخیره ساعت ناموفق بود.')
  return payload
}

async function createAttendanceEvent({ userId, eventType, date, time, note = 'ثبت دستی مدیر' }) {
  const normalized = normalizeTime(time)
  if (!normalized) throw new Error('ساعت معتبر وارد کنید.')
  const day = String(date || todayIsoDate()).slice(0, 10)
  const response = await fetch(`${API_BASE_URL}/attendance/events`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      userId,
      eventType,
      eventAt: `${day}T${normalized}:00`,
      note,
    }),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || payload.message || 'ثبت رویداد ناموفق بود.')
  return payload
}

async function saveEvent(event, { notify = true, surface = 'modal' } = {}) {
  const time = normalizeTime(drafts[event.id])
  if (!time) {
    if (surface === 'board') boardError.value = 'ساعت معتبر وارد کنید.'
    else modalError.value = 'ساعت معتبر وارد کنید.'
    return false
  }
  if (!isDirty(event.id)) return true
  const next = new Set(savingIds.value)
  next.add(String(event.id))
  savingIds.value = next
  if (surface === 'board') boardError.value = ''
  else modalError.value = ''
  try {
    await patchEventTime(event.id, time)
    originals[event.id] = time
    drafts[event.id] = time
    if (notify) {
      if (surface === 'board') boardNotice.value = 'ساعت ذخیره شد.'
      else modalNotice.value = 'ساعت ذخیره شد.'
      emit('updated', { eventId: event.id, time })
    }
    return true
  } catch (error) {
    const message = error.message || 'ذخیره ساعت ناموفق بود.'
    if (surface === 'board') boardError.value = message
    else modalError.value = message
    return false
  } finally {
    const done = new Set(savingIds.value)
    done.delete(String(event.id))
    savingIds.value = done
  }
}

async function saveDirtyEvents() {
  if (!selectedPerson.value || !dirtyIds.value.length || savingAll.value) return
  savingAll.value = true
  modalError.value = ''
  modalNotice.value = ''
  const queue = selectedPerson.value.events.filter((event) => isDirty(event.id))
  const failed = []
  for (const event of queue) {
    const ok = await saveEvent(event, { notify: false })
    if (!ok) failed.push(event)
  }
  savingAll.value = false
  if (!failed.length) {
    modalNotice.value = 'همه ساعت‌های تغییر یافته ذخیره شد.'
    emit('updated')
  }
}

async function addMissingPunch({ userId, eventType, date, draftKey, pairIndex = 0 }) {
  if (!props.canEditTimes || creatingKey.value) return
  const key = draftKey || createDraftKey(userId, eventType, date, pairIndex)
  const time = ensureCreateDraft(key, eventType === 'out' ? '17:00' : '08:30')
  creatingKey.value = key
  boardError.value = ''
  modalError.value = ''
  try {
    await createAttendanceEvent({ userId, eventType, date, time })
    delete createDrafts[key]
    if (selectedPerson.value) modalNotice.value = eventType === 'in' ? 'ورود اضافه شد.' : 'خروج اضافه شد.'
    else boardNotice.value = eventType === 'in' ? 'ورود اضافه شد.' : 'خروج اضافه شد.'
    emit('updated')
  } catch (error) {
    const message = error.message || 'ثبت رویداد ناموفق بود.'
    if (selectedPerson.value) modalError.value = message
    else boardError.value = message
  } finally {
    creatingKey.value = ''
  }
}

function syncTodayDrafts() {
  for (const row of todayPairs.value) {
    if (row.inEvent && (drafts[row.inEvent.id] == null || !isDirty(row.inEvent.id))) {
      const time = eventTimeOf(row.inEvent)
      drafts[row.inEvent.id] = time
      originals[row.inEvent.id] = time
    }
    if (row.outEvent && (drafts[row.outEvent.id] == null || !isDirty(row.outEvent.id))) {
      const time = eventTimeOf(row.outEvent)
      drafts[row.outEvent.id] = time
      originals[row.outEvent.id] = time
    }
  }
}

watch(selectedPerson, (person) => {
  if (!person || !selectedUserId.value) return
  for (const event of person.events) {
    if (drafts[event.id] == null || !isDirty(event.id)) {
      const time = eventTimeOf(event)
      drafts[event.id] = time
      originals[event.id] = time
    }
  }
})

watch(todayPairs, () => {
  if (isTodayMode.value) syncTodayDrafts()
}, { immediate: true })

watch(isTodayMode, (today) => {
  if (today) closePerson()
})
</script>

<template>
  <section class="surface-block attendance-board">
    <div class="section-label-row attendance-board-head">
      <SectionHeading
        :title="isTodayMode ? 'ورود و خروج امروز' : 'گزارش پرسنل'"
        :description="isTodayMode
          ? 'ورودها و خروج‌ها روبه‌روی هم در دو ستون نمایش داده می‌شوند.'
          : 'روی هر نام بزنید تا ورود و خروج‌ها با ساعت در مودال باز شود.'"
      />
      <span class="meta-pill">
        {{ isTodayMode ? `${fa(todayPairs.length)} جفت رویداد` : `${fa(people.length)} نفر` }}
      </span>
    </div>

    <div v-if="isTodayMode" class="attendance-today-stats">
      <article>
        <small>ورود</small>
        <strong>{{ fa(todaySummary.ins) }}</strong>
      </article>
      <article>
        <small>خروج</small>
        <strong>{{ fa(todaySummary.outs) }}</strong>
      </article>
      <article>
        <small>پرسنل</small>
        <strong>{{ fa(todaySummary.people) }}</strong>
      </article>
    </div>

    <div v-if="error || boardError" class="attendance-alert is-danger">{{ error || boardError }}</div>
    <div v-else-if="boardNotice" class="attendance-alert is-success">{{ boardNotice }}</div>

    <div v-if="isTodayMode" class="attendance-card-list">
      <article v-for="row in todayPairs" :key="row.id" class="attendance-entry-card">
        <header class="attendance-card-identity">
          <UserAvatar
            :name="row.userName"
            :avatar="row.userAvatar"
            :avatar-url="row.userAvatarUrl || row.avatarUrl"
            size="sm"
          />
          <div class="attendance-card-copy">
            <strong>{{ row.userName }}</strong>
            <small>{{ personMetaLine(row) || '—' }}</small>
          </div>
        </header>
        <div class="attendance-card-punches">
          <div class="punch-slot is-in">
            <span>ورود</span>
            <template v-if="row.inEvent">
              <div class="punch-time-edit">
                <template v-if="canEditTimes">
                  <TimePicker
                    class="pair-time-picker is-inline"
                    :model-value="drafts[row.inEvent.id] || eventTimeOf(row.inEvent)"
                    :minute-step="1"
                    :clearable="false"
                    @update:model-value="drafts[row.inEvent.id] = $event"
                  />
                  <button
                    v-if="isDirty(row.inEvent.id)"
                    class="pair-save-btn is-inline"
                    type="button"
                    :disabled="isSaving(row.inEvent.id)"
                    @click="saveEvent(row.inEvent, { surface: 'board' })"
                  >
                    {{ isSaving(row.inEvent.id) ? '…' : 'ذخیره' }}
                  </button>
                </template>
                <time v-else>{{ fa(eventTimeOf(row.inEvent) || '—') }}</time>
              </div>
            </template>
            <div v-else class="punch-empty">
              <em>ثبت نشده</em>
              <div v-if="canEditTimes" class="punch-add">
                <TimePicker
                  class="pair-time-picker is-inline"
                  :model-value="createDrafts[createDraftKey(row.userId, 'in', todayIsoDate())] || '08:30'"
                  :minute-step="1"
                  :clearable="false"
                  @update:model-value="createDrafts[createDraftKey(row.userId, 'in', todayIsoDate())] = $event"
                />
                <button
                  class="pair-add-btn"
                  type="button"
                  :disabled="creatingKey === createDraftKey(row.userId, 'in', todayIsoDate())"
                  @click="addMissingPunch({ userId: row.userId, eventType: 'in', date: todayIsoDate() })"
                >
                  افزودن
                </button>
              </div>
            </div>
          </div>
          <div class="punch-slot is-out">
            <span>خروج</span>
            <template v-if="row.outEvent">
              <div class="punch-time-edit">
                <template v-if="canEditTimes">
                  <TimePicker
                    class="pair-time-picker is-inline"
                    :model-value="drafts[row.outEvent.id] || eventTimeOf(row.outEvent)"
                    :minute-step="1"
                    :clearable="false"
                    @update:model-value="drafts[row.outEvent.id] = $event"
                  />
                  <button
                    v-if="isDirty(row.outEvent.id)"
                    class="pair-save-btn is-inline"
                    type="button"
                    :disabled="isSaving(row.outEvent.id)"
                    @click="saveEvent(row.outEvent, { surface: 'board' })"
                  >
                    {{ isSaving(row.outEvent.id) ? '…' : 'ذخیره' }}
                  </button>
                </template>
                <time v-else>{{ fa(eventTimeOf(row.outEvent) || '—') }}</time>
              </div>
            </template>
            <div v-else class="punch-empty is-open">
              <em>ثبت نشده</em>
              <div v-if="canEditTimes && row.inEvent" class="punch-add">
                <TimePicker
                  class="pair-time-picker is-inline"
                  :model-value="createDrafts[createDraftKey(row.userId, 'out', eventDateOf(row.inEvent) || todayIsoDate())] || '17:00'"
                  :minute-step="1"
                  :clearable="false"
                  @update:model-value="createDrafts[createDraftKey(row.userId, 'out', eventDateOf(row.inEvent) || todayIsoDate())] = $event"
                />
                <button
                  class="pair-add-btn"
                  type="button"
                  :disabled="creatingKey === createDraftKey(row.userId, 'out', eventDateOf(row.inEvent) || todayIsoDate())"
                  @click="addMissingPunch({
                    userId: row.userId,
                    eventType: 'out',
                    date: eventDateOf(row.inEvent) || todayIsoDate(),
                  })"
                >
                  افزودن
                </button>
              </div>
            </div>
          </div>
        </div>
      </article>
      <p v-if="!todayPairs.length" class="attendance-empty">
        {{ loading ? 'در حال بارگذاری…' : 'ورود و خروجی برای امروز ثبت نشده است.' }}
      </p>
    </div>

    <div v-else class="attendance-card-list">
      <button
        v-for="person in people"
        :key="person.userId"
        class="attendance-entry-card is-clickable"
        type="button"
        :aria-label="`مشاهده ورود و خروج ${person.userName}`"
        @click="openPerson(person)"
      >
        <header class="attendance-card-identity">
          <UserAvatar
            :name="person.userName"
            :avatar="person.userAvatar"
            :avatar-url="person.userAvatarUrl || person.avatarUrl"
            size="sm"
          />
          <div class="attendance-card-copy">
            <strong>{{ person.userName }}</strong>
            <small>{{ joinDisplayParts([person.userRole, person.userDepartment]) || '—' }}</small>
          </div>
          <span :class="['status-badge', person.hasOpenShift ? 'is-warning' : 'is-success']">
            {{ person.hasOpenShift ? 'شیفت باز' : 'بسته' }}
          </span>
        </header>
        <div class="attendance-card-stats">
          <span><small>روز حضور</small><b>{{ fa(person.presentDays) }}</b></span>
          <span><small>ورود</small><b>{{ fa(person.checkins) }}</b></span>
          <span><small>خروج</small><b>{{ fa(person.checkouts) }}</b></span>
          <span><small>کارکرد</small><b>{{ formatHours(person.workedMinutes) }}</b></span>
        </div>
      </button>
      <p v-if="!people.length" class="attendance-empty">
        {{ loading ? 'در حال بارگذاری…' : 'برای این بازه پرسنلی با رویداد ورود و خروج پیدا نشد.' }}
      </p>
    </div>
  </section>

  <BaseModal :open="!!selectedPerson" size="detail" @close="closePerson">
    <article v-if="selectedPerson" class="attendance-person-modal">
      <header class="attendance-person-hero">
        <UserAvatar
          :name="selectedPerson.userName"
          :avatar="selectedPerson.userAvatar"
          :avatar-url="selectedPerson.userAvatarUrl || selectedPerson.avatarUrl"
          size="lg"
        />
        <div class="attendance-person-title">
          <span class="page-eyebrow">جزئیات ورود و خروج</span>
          <h2>{{ selectedPerson.userName }}</h2>
          <p>{{ personMetaLine(selectedPerson) || '—' }}</p>
        </div>
        <button
          class="attendance-person-close"
          type="button"
          aria-label="بستن"
          title="بستن"
          @click="closePerson"
        >
          <IconlyIcon name="close" decorative />
          <span>بستن</span>
        </button>
      </header>

      <section class="attendance-person-metrics">
        <article>
          <small>روز حضور</small>
          <strong>{{ fa(selectedPerson.presentDays) }}</strong>
        </article>
        <article>
          <small>ورود</small>
          <strong>{{ fa(selectedPerson.checkins) }}</strong>
        </article>
        <article>
          <small>خروج</small>
          <strong>{{ fa(selectedPerson.checkouts) }}</strong>
        </article>
        <article>
          <small>کارکرد</small>
          <strong>{{ formatHours(selectedPerson.workedMinutes) }}</strong>
        </article>
      </section>

      <p v-if="canEditTimes" class="attendance-edit-hint">می‌توانید ساعت‌ها را ویرایش کنید یا ورود/خروج ثبت‌نشده را اضافه کنید.</p>
      <div v-if="modalError" class="attendance-alert is-danger">{{ modalError }}</div>
      <div v-else-if="modalNotice" class="attendance-alert is-success">{{ modalNotice }}</div>

      <section class="attendance-day-list">
        <article v-for="day in selectedDays" :key="day.date" class="attendance-day-card">
          <header class="attendance-day-head">
            <div class="attendance-day-title">
              <strong>{{ formatDayTitle(day.date) }}</strong>
              <small>{{ fa(day.eventCount) }} رویداد · {{ formatHours(day.workedMinutes) }}</small>
            </div>
            <span v-if="day.hasOpenShift" class="status-badge is-warning is-compact">شیفت باز</span>
          </header>

          <div class="attendance-pair-rows">
            <div
              v-for="(pair, index) in day.pairs"
              :key="`${day.date}-${index}`"
              class="attendance-pair-row"
            >
              <div class="pair-cell is-in">
                <span class="pair-cell-label">ورود</span>
                <template v-if="pair.inEvent">
                  <div class="pair-cell-main">
                    <time>{{ fa(eventTimeOf(pair.inEvent)) }}</time>
                    <small>{{ sourceLabel(pair.inEvent.source) }}</small>
                  </div>
                  <TimePicker
                    v-if="canEditTimes"
                    class="pair-time-picker"
                    :model-value="drafts[pair.inEvent.id] || eventTimeOf(pair.inEvent)"
                    :minute-step="1"
                    :clearable="false"
                    @update:model-value="drafts[pair.inEvent.id] = $event"
                  />
                  <p v-if="pair.inEvent.note" class="pair-note">{{ pair.inEvent.note }}</p>
                  <button
                    v-if="canEditTimes && isDirty(pair.inEvent.id)"
                    class="pair-save-btn"
                    type="button"
                    :disabled="isSaving(pair.inEvent.id) || savingAll"
                    @click="saveEvent(pair.inEvent)"
                  >
                    {{ isSaving(pair.inEvent.id) ? '…' : 'ذخیره' }}
                  </button>
                </template>
                <div v-else class="pair-empty">
                  <span>—</span>
                  <div v-if="canEditTimes" class="punch-add">
                    <TimePicker
                      class="pair-time-picker"
                      :model-value="createDrafts[createDraftKey(selectedPerson.userId, 'in', day.date, index)] || '08:30'"
                      :minute-step="1"
                      :clearable="false"
                      @update:model-value="createDrafts[createDraftKey(selectedPerson.userId, 'in', day.date, index)] = $event"
                    />
                    <button
                      class="pair-add-btn"
                      type="button"
                      :disabled="creatingKey === createDraftKey(selectedPerson.userId, 'in', day.date, index)"
                      @click="addMissingPunch({
                        userId: selectedPerson.userId,
                        eventType: 'in',
                        date: day.date,
                        pairIndex: index,
                      })"
                    >
                      افزودن ورود
                    </button>
                  </div>
                </div>
              </div>

              <div class="pair-cell is-out">
                <span class="pair-cell-label">خروج</span>
                <template v-if="pair.outEvent">
                  <div class="pair-cell-main">
                    <time>{{ fa(eventTimeOf(pair.outEvent)) }}</time>
                    <small>{{ sourceLabel(pair.outEvent.source) }}</small>
                  </div>
                  <TimePicker
                    v-if="canEditTimes"
                    class="pair-time-picker"
                    :model-value="drafts[pair.outEvent.id] || eventTimeOf(pair.outEvent)"
                    :minute-step="1"
                    :clearable="false"
                    @update:model-value="drafts[pair.outEvent.id] = $event"
                  />
                  <p v-if="pair.outEvent.note" class="pair-note">{{ pair.outEvent.note }}</p>
                  <button
                    v-if="canEditTimes && isDirty(pair.outEvent.id)"
                    class="pair-save-btn"
                    type="button"
                    :disabled="isSaving(pair.outEvent.id) || savingAll"
                    @click="saveEvent(pair.outEvent)"
                  >
                    {{ isSaving(pair.outEvent.id) ? '…' : 'ذخیره' }}
                  </button>
                </template>
                <div v-else class="pair-empty is-open">
                  <span>—</span>
                  <div v-if="canEditTimes" class="punch-add">
                    <TimePicker
                      class="pair-time-picker"
                      :model-value="createDrafts[createDraftKey(selectedPerson.userId, 'out', day.date, index)] || '17:00'"
                      :minute-step="1"
                      :clearable="false"
                      @update:model-value="createDrafts[createDraftKey(selectedPerson.userId, 'out', day.date, index)] = $event"
                    />
                    <button
                      class="pair-add-btn"
                      type="button"
                      :disabled="creatingKey === createDraftKey(selectedPerson.userId, 'out', day.date, index)"
                      @click="addMissingPunch({
                        userId: selectedPerson.userId,
                        eventType: 'out',
                        date: day.date,
                        pairIndex: index,
                      })"
                    >
                      افزودن خروج
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </article>

        <div v-if="!selectedDays.length" class="empty-state-inline compact-empty">
          <p>رویدادی برای این پرسنل در بازه انتخاب‌شده نیست.</p>
        </div>
      </section>

      <footer class="attendance-person-actions">
        <button class="action-btn tone-soft" type="button" :disabled="savingAll || savingIds.size > 0" @click="closePerson">
          بستن
        </button>
        <button
          v-if="canEditTimes"
          class="action-btn tone-primary"
          type="button"
          :disabled="!dirtyIds.length || savingAll"
          @click="saveDirtyEvents"
        >
          {{ savingAll ? 'در حال ذخیره…' : (dirtyIds.length ? `ذخیره ${fa(dirtyIds.length)} تغییر` : 'تغییری نیست') }}
        </button>
      </footer>
    </article>
  </BaseModal>
</template>

<style scoped>
.attendance-board {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.attendance-board-head {
  align-items: center;
}

.attendance-today-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.attendance-today-stats article {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(228, 244, 242, 0.7);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.attendance-today-stats small {
  display: block;
  color: var(--muted, #45605c);
  font-size: 12px;
  font-weight: 700;
}

.attendance-today-stats strong {
  display: block;
  margin-top: 4px;
  color: var(--primary, #34908B);
  font-size: 1.25rem;
}

.attendance-card-list {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.attendance-entry-card {
  display: grid;
  gap: 12px;
  width: 100%;
  min-width: 0;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  background: #fff;
  text-align: right;
  font: inherit;
  color: inherit;
}

.attendance-entry-card.is-clickable {
  cursor: pointer;
}

.attendance-entry-card.is-clickable:hover,
.attendance-entry-card.is-clickable:focus-visible {
  border-color: rgba(52, 144, 139, 0.32);
  background: #f8fcfb;
  outline: 0;
}

.attendance-card-identity {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.attendance-card-copy {
  min-width: 0;
  overflow: hidden;
}

.attendance-card-copy strong,
.attendance-person-title h2 {
  display: block;
  min-width: 0;
  color: #152523;
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.45;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: normal;
  word-break: keep-all;
}

.attendance-card-copy small {
  display: block;
  margin-top: 2px;
  color: var(--muted, #45605c);
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attendance-card-punches,
.attendance-card-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.attendance-card-stats {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.punch-slot,
.attendance-card-stats span {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(228, 244, 242, 0.7);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.punch-slot.is-out,
.attendance-card-stats span:nth-child(2n) {
  background: rgba(255, 248, 232, 0.65);
  border-color: rgba(176, 122, 18, 0.16);
}

.punch-slot > span,
.attendance-card-stats small {
  color: #5f7a76;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.attendance-card-stats b {
  color: #1f5c59;
  font-size: 0.92rem;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: normal;
  word-break: keep-all;
}

.punch-slot time {
  display: block;
  color: #1f5c59;
  font-size: 1rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.punch-slot.is-out time {
  color: #8a5d0c;
}

.attendance-empty {
  margin: 0;
  padding: 22px 12px;
  border-radius: 14px;
  background: #eef6f4;
  color: #45605c;
  text-align: center;
  font-weight: 700;
}

.punch-cell {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.punch-copy,
.person-identity {
  min-width: 0;
}

.punch-copy strong,
.person-identity strong {
  display: block;
  color: #152523;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow-wrap: normal;
  word-break: keep-all;
}

.punch-copy small,
.person-identity small {
  display: block;
  margin-top: 2px;
  color: var(--muted, #45605c);
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.punch-cell time {
  flex: 0 0 auto;
  min-width: 64px;
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
  font-weight: 800;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.attendance-split-table td.is-out .punch-cell time {
  background: rgba(176, 122, 18, 0.14);
  color: #8a5d0c;
}

.punch-empty {
  min-height: 44px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  border: 1px dashed rgba(36, 59, 107, 0.16);
  color: var(--muted, #45605c);
  font-size: 12px;
  font-weight: 700;
}

.punch-empty.is-open {
  border-color: rgba(176, 122, 18, 0.28);
  color: #8a5d0c;
  background: rgba(255, 248, 232, 0.7);
}

.person-identity {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  align-items: center;
}

.attendance-person-row {
  cursor: pointer;
  outline: 0;
  transition: background-color 140ms ease;
}

.attendance-person-row:hover,
.attendance-person-row:focus-visible {
  background: rgba(52, 144, 139, 0.08);
}

.person-open-cell {
  width: 44px;
  text-align: center;
}

.person-open-btn {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(52, 144, 139, 0.1);
  color: #1f5c59;
  border: 1px solid rgba(52, 144, 139, 0.14);
}

.person-open-btn :deep(.iconly-shell) {
  font-size: 16px;
}

.attendance-person-modal {
  display: grid;
  gap: 12px;
  padding: 2px;
}

.attendance-person-hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.attendance-person-title {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.attendance-person-title h2,
.attendance-person-title p {
  margin: 0;
}

.attendance-person-title h2 {
  font-size: clamp(1.05rem, 2vw, 1.35rem);
  color: var(--primary, #34908B);
  line-height: 1.35;
}

.attendance-person-title p {
  color: var(--muted, #45605c);
  font-size: 12px;
}

.attendance-person-close {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  border-radius: 12px;
  background: #fff;
  color: #1f5c59;
  font: inherit;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  flex: 0 0 auto;
  box-shadow: 0 4px 12px rgba(31, 92, 89, 0.06);
  transition: background 0.15s ease, border-color 0.15s ease;
}

.attendance-person-close:hover {
  background: rgba(52, 144, 139, 0.08);
  border-color: rgba(52, 144, 139, 0.28);
}

.attendance-person-close :deep(.iconly-shell) {
  font-size: 16px;
}

.attendance-person-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.attendance-person-metrics article {
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(228, 244, 242, 0.78);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.attendance-person-metrics small,
.attendance-day-head small {
  display: block;
  color: var(--muted, #45605c);
  font-size: 11px;
}

.attendance-person-metrics strong {
  display: block;
  margin-top: 2px;
  color: #1f5c59;
  font-size: 0.95rem;
}

.attendance-edit-hint {
  margin: 0;
  color: var(--muted, #45605c);
  font-size: 12px;
  line-height: 1.6;
}

.attendance-day-list {
  display: grid;
  gap: 8px;
  max-height: min(48vh, 420px);
  overflow: auto;
  padding-inline: 2px 6px;
}

.attendance-day-card {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.1);
  background: rgba(255, 255, 255, 0.92);
}

.attendance-day-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(52, 144, 139, 0.08);
}

.attendance-day-title {
  min-width: 0;
}

.attendance-day-title strong {
  display: block;
  font-size: 0.88rem;
  color: #1f5c59;
  line-height: 1.4;
}

.attendance-day-title small {
  margin-top: 2px;
}

.status-badge.is-compact {
  padding: 3px 8px;
  font-size: 10px;
  white-space: nowrap;
}

.attendance-pair-rows {
  display: grid;
  gap: 6px;
}

.attendance-pair-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.pair-cell {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 8px;
  border-radius: 10px;
  border: 1px solid rgba(52, 144, 139, 0.1);
  background: rgba(248, 252, 251, 0.95);
}

.pair-cell.is-out {
  background: rgba(255, 251, 244, 0.95);
  border-color: rgba(176, 122, 18, 0.12);
}

.pair-cell-label {
  font-size: 10px;
  font-weight: 800;
  color: var(--muted, #45605c);
  letter-spacing: 0.02em;
}

.pair-cell-main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  min-width: 0;
}

.pair-cell-main time {
  font-weight: 800;
  font-size: 0.9rem;
  color: #1f5c59;
  font-variant-numeric: tabular-nums;
}

.pair-cell.is-out .pair-cell-main time {
  color: #8a5d0c;
}

.pair-cell-main small {
  color: var(--muted, #45605c);
  font-size: 10px;
  white-space: nowrap;
}

.pair-cell :deep(.pair-time-picker .time-picker-trigger) {
  min-height: 32px;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
}

.pair-note {
  margin: 0;
  color: var(--muted, #45605c);
  font-size: 11px;
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pair-empty {
  min-height: 28px;
  display: grid;
  place-items: center;
  color: var(--muted, #45605c);
  font-size: 12px;
  font-weight: 700;
}

.pair-empty.is-open {
  color: #8a5d0c;
}

.pair-save-btn {
  justify-self: start;
  min-height: 28px;
  padding: 0 10px;
  border: 0;
  border-radius: 8px;
  background: var(--button-primary-bg, #34908B);
  color: #fff;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.pair-save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.attendance-person-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.attendance-alert {
  padding: 12px 14px;
  border-radius: 14px;
}

.attendance-alert.is-danger {
  background: var(--danger-soft, rgba(196, 90, 74, 0.12));
  color: var(--danger, #c45a4a);
}

.attendance-alert.is-success {
  background: var(--success-soft, rgba(31, 122, 114, 0.12));
  color: var(--success, #1f7a72);
}

.status-badge.is-success {
  background: var(--success-soft, rgba(31, 122, 114, 0.12));
  color: var(--success, #1f7a72);
}

.status-badge.is-warning {
  background: var(--warning-soft, rgba(176, 122, 18, 0.14));
  color: var(--warning, #b07a12);
}

.punch-time-edit,
.punch-add {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.punch-empty {
  display: grid;
  gap: 8px;
  justify-items: start;
}

.pair-add-btn,
.pair-save-btn.is-inline {
  min-height: 32px;
  padding: 0 10px;
  border: 0;
  border-radius: 10px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
  font: inherit;
  font-size: 0.75rem;
  font-weight: 800;
  cursor: pointer;
}

.pair-add-btn:disabled,
.pair-save-btn.is-inline:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.pair-time-picker.is-inline :deep(.time-picker-trigger) {
  min-height: 32px;
  padding: 4px 8px;
  border-radius: 10px;
}

@media (max-width: 760px) {
  .attendance-person-metrics,
  .attendance-today-stats,
  .attendance-card-punches {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .attendance-card-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .attendance-today-stats article {
    padding: 10px 8px;
    box-shadow: none;
  }

  .attendance-person-hero {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .attendance-person-close {
    grid-column: 1 / -1;
    justify-content: center;
    width: 100%;
  }

  .attendance-person-actions,
  .attendance-person-actions .action-btn {
    width: 100%;
  }

  .attendance-card-identity {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .attendance-card-identity .status-badge {
    margin-inline-start: auto;
    flex: 0 0 auto;
  }

  .punch-time-edit,
  .punch-add {
    width: 100%;
    justify-content: flex-start;
  }

  .pair-time-picker.is-inline {
    flex: 1 1 auto;
    min-width: 0;
  }

  .pair-time-picker.is-inline :deep(.time-picker-trigger) {
    width: 100%;
  }
}

@media (max-width: 560px) {
  .attendance-pair-row {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
/* Keep report/attendance identity text on one line across global overrides. */
#app .app-shell:not(.is-auth-route) .attendance-board .attendance-card-copy,
#app .app-shell:not(.is-auth-route) .attendance-board .attendance-card-copy strong,
#app .app-shell:not(.is-auth-route) .attendance-board .attendance-card-copy small {
  display: block !important;
  min-width: 0 !important;
  max-width: 100% !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  overflow-wrap: normal !important;
  word-break: keep-all !important;
}

#app .app-shell:not(.is-auth-route) .attendance-board .attendance-entry-card {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
}

#app .app-shell:not(.is-auth-route) .attendance-board .attendance-card-identity {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  min-width: 0 !important;
  width: 100% !important;
}

#app .app-shell:not(.is-auth-route) .attendance-board .attendance-card-copy {
  flex: 1 1 auto !important;
}

#app .app-shell:not(.is-auth-route) .attendance-board .attendance-card-stats b,
#app .app-shell:not(.is-auth-route) .attendance-board .punch-slot time {
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
</style>
