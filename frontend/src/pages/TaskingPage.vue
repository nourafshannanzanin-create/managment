<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import IconlyIcon from '../components/base/IconlyIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import TaskComposerModal from '../components/TaskComposerModal.vue'
import TaskDetailModal from '../components/TaskDetailModal.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatDurationFa, formatDurationRatioFa } from '../utils/duration'
import { isoToJalali } from '../utils/jalali'
import { toneForStatus } from '../utils/status'

const {
  state,
  modalState,
  loadTaskingDashboard,
  loadTaskDetail,
  openTaskComposer,
  closeTaskComposer,
  closeTaskDetail,
  startTask,
  pauseTask,
  acceptTask,
  rejectTask,
  submitTaskReview,
} = useWorkflowHub()

const mainTab = ref('mine')
const subTab = ref('upcoming')
const query = ref('')
const timerTick = ref(0)
let timerHandle = null
let pollHandle = null

onMounted(async () => {
  await loadTaskingDashboard(true)
  timerHandle = window.setInterval(() => {
    timerTick.value += 1
  }, 1000)
  // Soft poll only — sidebar already refreshes badges; avoid double hard reloads.
  pollHandle = window.setInterval(() => {
    if (document.visibilityState === 'hidden') return
    void loadTaskingDashboard(true, '', { soft: true }).catch(() => {})
  }, 60000)
})

onUnmounted(() => {
  if (timerHandle) window.clearInterval(timerHandle)
  if (pollHandle) window.clearInterval(pollHandle)
})

watch(mainTab, (tab) => {
  if (tab === 'mine') subTab.value = 'upcoming'
  if (tab === 'assignments') subTab.value = 'pending'
  if (tab === 'supervise') subTab.value = 'all'
  if (tab === 'mentions') subTab.value = 'unread'
})

const capacity = computed(() => state.tasking.capacity || {})
const progressBaseMinutes = computed(() => {
  const fromApi = Number(capacity.value.progressBaseMinutes || 0)
  if (fromApi > 0) return fromApi
  const planned = Number(capacity.value.plannedMinutes || 0)
  if (planned > 0) return planned
  const target = Number(capacity.value.targetMinutes || 0)
  if (target > 0) return target
  return Number(capacity.value.effectiveWorkMinutes || 0)
})
const liveActualMinutes = computed(() => {
  void timerTick.value
  const closed = Number(capacity.value.timerClosedMinutes)
  const hasClosed = Number.isFinite(closed) && closed >= 0 && capacity.value.timerClosedMinutes != null
  const active = state.tasking.activeTimer
  if (hasClosed) {
    let seconds = closed * 60
    if (active?.startedAt) {
      const started = new Date(active.startedAt).getTime()
      if (Number.isFinite(started)) {
        seconds += Math.max(0, Math.floor((Date.now() - started) / 1000))
      }
    }
    return Math.max(0, Math.floor(seconds / 60))
  }
  // Fallback while older payloads lack timerClosedMinutes
  let mins = Number(capacity.value.actualMinutes || 0)
  if (active?.startedAt) {
    const started = new Date(active.startedAt).getTime()
    const liveSec = Number.isFinite(started) ? Math.max(0, Math.floor((Date.now() - started) / 1000)) : 0
    const apiActive = Number(capacity.value.timerActiveSeconds || 0)
    if (liveSec > apiActive) mins += Math.floor((liveSec - apiActive) / 60)
  }
  return Math.max(0, mins)
})
const donePercent = computed(() => {
  const actual = liveActualMinutes.value
  const base = progressBaseMinutes.value
  if (base <= 0) return actual > 0 ? 100 : 0
  return Math.min(100, Math.round((actual / base) * 100))
})
const doneBarWidth = computed(() => `${donePercent.value}%`)
const capacityPercent = computed(() => donePercent.value)
const capacityTone = computed(() => {
  const pct = donePercent.value
  if (pct >= 100) return 'is-success'
  if (pct >= 70) return 'is-success'
  if (pct >= 40) return 'is-warning'
  return 'is-idle'
})
const capacityRingStyle = computed(() => {
  const pct = capacityPercent.value
  const color =
    capacityTone.value === 'is-danger'
      ? '#dc2626'
      : capacityTone.value === 'is-warning'
        ? '#d97706'
        : capacityTone.value === 'is-success'
          ? '#16a34a'
          : '#34908b'
  return {
    background: `conic-gradient(${color} ${pct * 3.6}deg, rgba(52, 144, 139, 0.12) 0deg)`,
  }
})

function minutesLabel(value) {
  return formatDurationFa(value)
}

function shamsiDateLabel(iso) {
  if (!iso) return 'امروز'
  return isoToJalali(String(iso).slice(0, 10)) || iso
}

const displayDate = computed(() => shamsiDateLabel(state.tasking.date))

const remainingTargetMinutes = computed(() =>
  Math.max(0, Number(capacity.value.targetMinutes || 0) - Number(capacity.value.plannedMinutes || 0)),
)
const metricCards = computed(() => [
  {
    key: 'today',
    label: 'کارهای امروز',
    value: String(state.tasking.stats.todayCount || 0),
    hint: 'برنامه روز جاری',
    icon: 'assignment',
    tone: 'is-info',
  },
  {
    key: 'remaining',
    label: 'باقی‌مانده هدف',
    value: minutesLabel(state.tasking.stats.remainingMinutes ?? remainingTargetMinutes.value),
    hint: 'تا رسیدن به ظرفیت هدف',
    icon: 'schedule',
    tone: capacityTone.value === 'is-danger' ? 'is-danger' : 'is-warning',
  },
  {
    key: 'action',
    label: 'نیازمند اقدام',
    value: String(state.tasking.stats.needsAction || 0),
    hint: 'پذیرش، بررسی یا پیگیری',
    icon: 'pending_actions',
    tone: Number(state.tasking.stats.needsAction || 0) > 0 ? 'is-warning' : 'is-idle',
  },
  {
    key: 'done',
    label: 'تکمیل امروز',
    value: String(state.tasking.stats.completedToday || 0),
    hint: 'بسته و تأییدشده',
    icon: 'verified',
    tone: 'is-success',
  },
])

const counts = computed(() => state.tasking.counts || {})

const upcomingPool = computed(() => {
  const mine = state.tasking.mine || {}
  const map = new Map()
  const hidden = new Set(['completed', 'cancelled', 'pending_review', 'pending_acceptance', 'draft'])
  ;[...(mine.today || []), ...(mine.upcoming || []), ...(mine.inProgress || [])].forEach((task) => {
    if (!task?.id) return
    const status = String(task.status || '').toLowerCase()
    if (hidden.has(status)) return
    map.set(task.id, task)
  })
  return [...map.values()]
})

const weekdayFa = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه', 'یکشنبه']

function taskDayKey(task) {
  const raw = String(task?.focusDate || task?.dueAt || task?.allocations?.[0]?.workDate || state.tasking.date || '').slice(0, 10)
  return raw || 'بدون تاریخ'
}

function dayHeading(iso) {
  if (!iso || iso === 'بدون تاریخ') return 'بدون تاریخ'
  const d = new Date(`${iso}T12:00:00`)
  if (Number.isNaN(d.getTime())) return shamsiDateLabel(iso)
  const name = weekdayFa[(d.getDay() + 6) % 7]
  return `${name} ${shamsiDateLabel(iso)}`
}

const upcomingGroups = computed(() => {
  const groups = new Map()
  upcomingPool.value.forEach((task) => {
    const key = taskDayKey(task)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(task)
  })
  return [...groups.entries()]
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
    .map(([date, tasks]) => ({
      date,
      label: dayHeading(date),
      tasks: tasks.sort((x, y) => {
        const pr = Number(y.priorityScore || 0) - Number(x.priorityScore || 0)
        if (pr) return pr
        return String(x.dueAt || '').localeCompare(String(y.dueAt || ''))
      }),
    }))
})

const mineSubTabs = computed(() => [
  { key: 'upcoming', label: 'پیش‌رو', count: upcomingPool.value.length },
  { key: 'pendingReview', label: 'در انتظار بررسی', count: counts.value.mine?.pendingReview },
  { key: 'changesRequested', label: 'برگشتی', count: counts.value.mine?.changesRequested },
  { key: 'closed', label: 'بسته شده', count: counts.value.mine?.closed },
])

const assignmentSubTabs = computed(() => [
  { key: 'pending', label: 'ارجاع به من', count: counts.value.assignments?.pending },
  { key: 'outboundReview', label: 'نیازمند تایید من', count: counts.value.assignments?.outboundReview },
  { key: 'outbound', label: 'ارجاع داده‌شده', count: counts.value.assignments?.outbound },
])

const superviseSubTabs = computed(() => [
  { key: 'all', label: 'همه تیم', count: counts.value.supervise?.all },
  { key: 'pendingReview', label: 'نیازمند بررسی', count: counts.value.supervise?.pendingReview },
  { key: 'inProgress', label: 'در حال انجام', count: counts.value.supervise?.inProgress },
  { key: 'overdue', label: 'تأخیرها', count: counts.value.supervise?.overdue },
  { key: 'completed', label: 'تکمیل‌شده', count: counts.value.supervise?.completed },
])

const mentionSubTabs = computed(() => [
  { key: 'unread', label: 'خوانده‌نشده', count: counts.value.mentions || state.tasking.stats?.unreadMentions },
  { key: 'all', label: 'همه منشن‌ها', count: counts.value.mentionsAll || counts.value.mentions },
])

const currentSubTabs = computed(() => {
  if (mainTab.value === 'assignments') return assignmentSubTabs.value
  if (mainTab.value === 'supervise') return superviseSubTabs.value
  if (mainTab.value === 'mentions') return mentionSubTabs.value
  return mineSubTabs.value
})

const currentTasks = computed(() => {
  if (mainTab.value === 'mine' && subTab.value === 'upcoming') return upcomingPool.value
  const source =
    mainTab.value === 'assignments'
      ? state.tasking.assignments
      : mainTab.value === 'supervise'
        ? state.tasking.supervise
        : mainTab.value === 'mentions'
          ? state.tasking.mentions
          : state.tasking.mine
  const rows = source?.[subTab.value] || []
  const q = query.value.trim().toLowerCase()
  if (!q) return rows
  return rows.filter((item) =>
    `${item.title} ${item.code} ${item.assignee?.name || ''}`.toLowerCase().includes(q),
  )
})

const showGroupedUpcoming = computed(() => mainTab.value === 'mine' && subTab.value === 'upcoming' && !query.value.trim())

function formatElapsed(task) {
  void timerTick.value
  if (!task?.activeTimer?.startedAt) return ''
  const accumulated = Number(task.activeTimer.accumulatedSeconds || 0)
  const started = new Date(task.activeTimer.startedAt).getTime()
  const seconds = accumulated + Math.max(0, Math.floor((Date.now() - started) / 1000))
  const hh = String(Math.floor(seconds / 3600)).padStart(2, '0')
  const mm = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0')
  const ss = String(seconds % 60).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

function miniCount(value) {
  const n = Number(value || 0)
  return n > 0 ? n : 0
}

function isCompletedTask(task) {
  return String(task?.status || '').toLowerCase() === 'completed'
}

function taskPlannedMinutes(task) {
  return Number(task?.estimatedMinutes || task?.todayPlannedMinutes || 0)
}

function taskTimerMinutes(task) {
  void timerTick.value
  let minutes = Number(task?.actualMinutes || 0)
  if (task?.activeTimer?.startedAt) {
    const accumulated = Number(task.activeTimer.accumulatedSeconds || 0)
    const started = new Date(task.activeTimer.startedAt).getTime()
    const live = accumulated + Math.max(0, Math.floor((Date.now() - started) / 1000))
    minutes = Math.max(minutes, Math.floor(live / 60))
  }
  return minutes
}

async function shiftDate(delta) {
  const base = state.tasking.date ? new Date(`${state.tasking.date}T12:00:00`) : new Date()
  base.setDate(base.getDate() + delta)
  const iso = base.toISOString().slice(0, 10)
  state.tasking.date = iso
  await loadTaskingDashboard(true, iso)
}

async function goToday() {
  state.tasking.date = ''
  await loadTaskingDashboard(true)
}

async function openTask(task) {
  await loadTaskDetail(task.id)
}

function quickAccept(task) {
  void openTask(task)
}

function quickStart(task, stopOther = false) {
  if (task?.status === 'changes_requested') {
    void openTask(task)
    return
  }
  void startTask(task.id, stopOther)
}
</script>

<template>
  <section class="page-shell enterprise-page tasking-page">
    <PageHeader
      title="تسکینگ"
      description="برنامه روزانه، زمان اجرا و وضعیت کارهای شما"
    >
      <template #actions>
        <div class="tasking-header-actions">
          <div class="date-nav">
            <button class="icon-btn date-nav-btn" type="button" aria-label="روز قبل" @click="shiftDate(-1)">
              &lt;
            </button>
            <button class="action-btn tone-soft" type="button" @click="goToday">امروز</button>
            <button class="icon-btn date-nav-btn" type="button" aria-label="روز بعد" @click="shiftDate(1)">
              &gt;
            </button>
            <strong>{{ displayDate }}</strong>
          </div>
          <button class="action-btn tone-primary" type="button" @click="openTaskComposer">
            <IconlyIcon name="plus" decorative />
            <span>تسک جدید</span>
          </button>
        </div>
      </template>
    </PageHeader>

    <section v-if="state.tasking.activeTimer" class="active-timer-banner">
      <IconlyIcon name="timer" decorative />
      <div>
        <strong>{{ state.tasking.activeTimer.taskTitle }}</strong>
        <small>تایمر فعال</small>
      </div>
      <span>{{ formatElapsed({ activeTimer: state.tasking.activeTimer }) }}</span>
    </section>

    <section class="capacity-hero" :class="capacityTone">
      <div class="capacity-hero-main">
        <div class="capacity-ring-wrap">
          <div class="capacity-ring" :style="capacityRingStyle">
            <div class="capacity-ring-core">
              <strong>{{ donePercent }}٪</strong>
              <small>انجام‌شده</small>
            </div>
          </div>
        </div>
        <div class="capacity-copy">
          <p class="capacity-eyebrow">ظرفیت امروز</p>
          <h3>{{ capacity.bandLabel || 'بدون برنامه' }}</h3>
          <p class="capacity-lede">درصد و نوار پیشرفت فقط از مجموع تایمرهای امروز نسبت به برنامهٔ روز ساخته می‌شود.</p>
          <div class="capacity-bars">
            <div class="capacity-bar-row">
              <div class="capacity-bar-meta">
                <span>برنامه‌ریزی‌شده</span>
                <strong>{{ formatDurationRatioFa(capacity.plannedMinutes, capacity.targetMinutes) }}</strong>
              </div>
              <div class="capacity-track is-animated">
                <span
                  class="is-planned"
                  :style="{ width: `${Math.min(100, capacity.targetMinutes ? (Number(capacity.plannedMinutes || 0) / Number(capacity.targetMinutes)) * 100 : 0)}%` }"
                ></span>
              </div>
            </div>
            <div class="capacity-bar-row">
              <div class="capacity-bar-meta">
                <span>کارکرد تایمر</span>
                <strong>{{ formatDurationRatioFa(liveActualMinutes, progressBaseMinutes) }}</strong>
              </div>
              <div class="capacity-track is-animated">
                <span class="is-actual" :style="{ width: doneBarWidth }"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="capacity-stat-strip">
        <article>
          <small>ساعت کاری مؤثر</small>
          <strong>{{ minutesLabel(capacity.effectiveWorkMinutes) }}</strong>
        </article>
        <article>
          <small>ظرفیت هدف</small>
          <strong>{{ minutesLabel(capacity.targetMinutes) }}</strong>
        </article>
        <article>
          <small>برنامه‌ریزی‌شده</small>
          <strong>{{ minutesLabel(capacity.plannedMinutes) }}</strong>
        </article>
        <article>
          <small>کارکرد تایمر</small>
          <strong>{{ minutesLabel(liveActualMinutes) }}</strong>
        </article>
      </div>
    </section>

    <section class="tasking-metric-grid">
      <article v-for="card in metricCards" :key="card.key" class="tasking-metric-card" :class="card.tone">
        <div class="tasking-metric-topline">
          <span class="tasking-metric-accent"></span>
          <IconlyIcon :name="card.icon" decorative />
        </div>
        <span class="tasking-metric-label">{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.hint }}</small>
      </article>
    </section>

    <section class="surface-block">
      <div class="tasking-toolbar">
        <div class="chip-row tab-strip">
          <button type="button" :class="['chip-btn', mainTab === 'mine' && 'is-active']" @click="mainTab = 'mine'">
            کارهای من
            <span v-if="miniCount(state.tasking.stats.mineCount)" class="nav-link-badge is-mini">{{ miniCount(state.tasking.stats.mineCount) }}</span>
          </button>
          <button type="button" :class="['chip-btn', mainTab === 'assignments' && 'is-active']" @click="mainTab = 'assignments'">
            ارجاع‌ها
            <span v-if="miniCount(state.tasking.stats.assignmentCount)" class="nav-link-badge is-mini">{{ miniCount(state.tasking.stats.assignmentCount) }}</span>
          </button>
          <button type="button" :class="['chip-btn', mainTab === 'supervise' && 'is-active']" @click="mainTab = 'supervise'">
            نظارت
            <span v-if="miniCount(state.tasking.stats.superviseCount)" class="nav-link-badge is-mini">{{ miniCount(state.tasking.stats.superviseCount) }}</span>
          </button>
          <button type="button" :class="['chip-btn', mainTab === 'mentions' && 'is-active']" @click="mainTab = 'mentions'">
            منشن
            <span v-if="miniCount(state.tasking.stats.unreadMentions || state.tasking.counts?.mentions)" class="nav-link-badge is-mini">{{ miniCount(state.tasking.stats.unreadMentions || state.tasking.counts?.mentions) }}</span>
          </button>
        </div>
        <label class="search-shell compact-search">
          <IconlyIcon name="search" decorative />
          <input v-model="query" type="search" placeholder="جستجوی عنوان، کد یا مسئول" />
        </label>
      </div>

      <div class="chip-row tab-strip subtab-strip">
        <button
          v-for="item in currentSubTabs"
          :key="item.key"
          type="button"
          :class="['chip-btn', subTab === item.key && 'is-active']"
          @click="subTab = item.key"
        >
          {{ item.label }}
          <span v-if="miniCount(item.count)" class="nav-link-badge is-mini">{{ miniCount(item.count) }}</span>
        </button>
      </div>

      <div v-if="state.tasking.loading && !state.tasking.loaded" class="empty-copy">در حال بارگذاری...</div>

      <div v-else-if="showGroupedUpcoming ? !upcomingGroups.length : !currentTasks.length" class="empty-state-card">
        <strong>موردی برای نمایش نیست</strong>
        <p v-if="mainTab === 'mine' && subTab === 'upcoming'">هنوز تسکی برای پیش‌رو ندارید.</p>
        <p v-else-if="mainTab === 'assignments'">ارجاع جدیدی برای نمایش نیست.</p>
        <p v-else>در این فیلتر تسکی وجود ندارد.</p>
        <button v-if="mainTab === 'mine'" class="action-btn tone-primary" type="button" @click="openTaskComposer">افزودن تسک</button>
      </div>

      <div v-else-if="showGroupedUpcoming" class="task-day-groups">
        <section v-for="group in upcomingGroups" :key="group.date" class="task-day-group">
          <header class="task-day-heading">
            <strong>{{ group.label }}</strong>
            <span>{{ group.tasks.length }} تسک</span>
          </header>
          <div class="task-card-grid">
            <article
              v-for="task in group.tasks"
              :key="task.id"
              class="task-card"
              :class="toneForStatus(task.statusLabel)"
              @click="openTask(task)"
            >
              <div class="task-card-top">
                <span class="priority-dot" :data-priority="task.priority" :title="task.priorityLabel"></span>
                <div class="task-card-copy">
                  <small>{{ task.code }}</small>
                  <strong>{{ task.title }}</strong>
                </div>
                <span :class="['status-badge', toneForStatus(task.statusLabel)]">{{ task.statusLabel }}</span>
              </div>
              <div class="task-card-meta">
                <span class="task-time-chip is-planned">برنامه {{ minutesLabel(taskPlannedMinutes(task)) }}</span>
                <span
                  v-if="isCompletedTask(task) || taskTimerMinutes(task) > 0 || task.activeTimer"
                  class="task-time-chip is-timer"
                >
                  {{ isCompletedTask(task) ? 'پایان تایمر' : 'تایمر' }} {{ minutesLabel(taskTimerMinutes(task)) }}
                </span>
                <span v-if="task.todayPlannedMinutes && !isCompletedTask(task)" class="task-time-chip is-today">امروز {{ minutesLabel(task.todayPlannedMinutes) }}</span>
                <span v-if="task.assignee?.name">{{ task.assignee.name }}</span>
              </div>
              <div class="task-card-footer" @click.stop>
                <div class="task-people">
                  <UserAvatar :person="task.assignee" :name="task.assignee?.name" size="sm" />
                  <small>{{ task.priorityLabel }}</small>
                </div>
                <div class="task-card-actions">
                  <button v-if="task.canAccept" class="action-btn tone-primary" type="button" @click="quickAccept(task)">پذیرش</button>
                  <button v-if="task.canReject" class="action-btn tone-soft" type="button" @click="rejectTask(task.id, 'رد ارجاع')">رد</button>
                  <button v-if="task.canStart" class="action-btn tone-primary" type="button" @click="quickStart(task)">شروع</button>
                  <button v-if="task.canPause" class="action-btn tone-soft" type="button" @click="pauseTask(task.id)">توقف</button>
                  <button v-if="task.canComplete || task.canSubmitReview" class="action-btn tone-primary" type="button" @click="submitTaskReview(task.id)">پایان</button>
                  <span v-if="task.activeTimer" class="timer-readout">{{ formatElapsed(task) }}</span>
                </div>
              </div>
            </article>
          </div>
        </section>
      </div>

      <div v-else class="task-card-grid">
        <article
          v-for="task in currentTasks"
          :key="task.id"
          class="task-card"
          :class="toneForStatus(task.statusLabel)"
          @click="openTask(task)"
        >
          <div class="task-card-top">
            <span class="priority-dot" :data-priority="task.priority" :title="task.priorityLabel"></span>
            <div class="task-card-copy">
              <small>{{ task.code }}</small>
              <strong>{{ task.title }}</strong>
            </div>
            <span :class="['status-badge', toneForStatus(task.statusLabel)]">{{ task.statusLabel }}</span>
          </div>

          <div class="task-card-meta">
            <span class="task-time-chip is-planned">برنامه {{ minutesLabel(taskPlannedMinutes(task)) }}</span>
            <span
              v-if="isCompletedTask(task) || taskTimerMinutes(task) > 0 || task.activeTimer"
              class="task-time-chip is-timer"
            >
              {{ isCompletedTask(task) ? 'پایان تایمر' : 'تایمر' }} {{ minutesLabel(taskTimerMinutes(task)) }}
            </span>
            <span v-if="task.todayPlannedMinutes && !isCompletedTask(task)" class="task-time-chip is-today">امروز {{ minutesLabel(task.todayPlannedMinutes) }}</span>
            <span v-if="task.spillover" class="spill-badge">ادامه فردا</span>
            <span v-if="task.dueAt">ددلاین دارد</span>
          </div>

          <div class="task-card-footer">
            <div class="assignee-mini" v-if="task.assignee">
              <UserAvatar :person="task.assignee" :name="task.assignee.name" size="sm" />
              <small>{{ task.assignee.name }}</small>
            </div>
            <div class="task-card-actions" @click.stop>
              <button v-if="task.canAccept" class="action-btn tone-primary" type="button" @click="quickAccept(task)">پذیرش</button>
              <button v-if="task.canReject" class="action-btn tone-soft" type="button" @click="rejectTask(task.id, 'رد ارجاع')">رد</button>
              <button v-if="task.canStart && task.status !== 'in_progress'" class="action-btn tone-primary" type="button" @click="quickStart(task, true)">شروع</button>
              <button v-if="task.canPause" class="action-btn tone-soft" type="button" @click="pauseTask(task.id)">توقف</button>
              <button v-if="task.canComplete || task.canSubmitReview" class="action-btn tone-soft" type="button" @click="submitTaskReview(task.id)">پایان</button>
              <strong v-if="task.activeTimer" class="timer-readout">{{ formatElapsed(task) }}</strong>
            </div>
          </div>
        </article>
      </div>
    </section>

    <TaskComposerModal :open="modalState.taskComposer" @close="closeTaskComposer" />
    <TaskDetailModal
      :open="modalState.taskDetail"
      :task="state.tasking.selectedTask"
      @close="closeTaskDetail"
      @changed="loadTaskingDashboard(true, '', { soft: true })"
    />
  </section>
</template>

<style scoped>
.tasking-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.date-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}
.date-nav-btn {
  width: 38px;
  height: 38px;
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
  color: #1f5c59;
  border-radius: 12px;
}
.active-timer-banner,
.capacity-hero {
  display: grid;
  gap: 18px;
  padding: 18px 20px;
  border-radius: 22px;
  background:
    radial-gradient(120% 140% at 100% 0%, rgba(52, 144, 139, 0.14), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #f7fbfa 100%);
  border: 1px solid rgba(52, 144, 139, 0.14);
  box-shadow: 0 14px 36px rgba(31, 92, 89, 0.06);
}
.active-timer-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  background: #eef7f6;
}
.capacity-hero.is-success {
  border-color: rgba(22, 163, 74, 0.28);
  background:
    radial-gradient(120% 140% at 100% 0%, rgba(22, 163, 74, 0.14), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #f4fbf6 100%);
}
.capacity-hero.is-warning {
  border-color: rgba(217, 119, 6, 0.28);
  background:
    radial-gradient(120% 140% at 100% 0%, rgba(217, 119, 6, 0.14), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #fffaf3 100%);
}
.capacity-hero.is-danger {
  border-color: rgba(220, 38, 38, 0.28);
  background:
    radial-gradient(120% 140% at 100% 0%, rgba(220, 38, 38, 0.12), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #fff7f7 100%);
}
.capacity-hero-main {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 20px;
  align-items: center;
}
.capacity-ring-wrap { flex: 0 0 auto; }
.capacity-ring {
  width: 124px;
  height: 124px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  animation: capacity-pulse 2.8s ease-in-out infinite;
}
.capacity-ring-core {
  width: 92px;
  height: 92px;
  border-radius: 50%;
  background: #fff;
  display: grid;
  place-items: center;
  gap: 2px;
  box-shadow: inset 0 0 0 1px rgba(52, 144, 139, 0.08);
}
.capacity-ring-core strong {
  font-size: 1.55rem;
  line-height: 1;
  color: #134e4a;
  font-variant-numeric: tabular-nums;
}
.capacity-ring-core small,
.capacity-eyebrow,
.capacity-lede,
.capacity-stat-strip small,
.tasking-metric-label,
.tasking-metric-card small {
  color: var(--muted, #64748b);
}
.capacity-copy { display: grid; gap: 8px; min-width: 0; }
.capacity-eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.capacity-copy h3 {
  margin: 0;
  font-size: 1.35rem;
  color: #134e4a;
}
.capacity-lede { margin: 0; font-size: 13px; line-height: 1.7; max-width: 42ch; }
.capacity-bars { display: grid; gap: 12px; margin-top: 8px; }
.capacity-bar-row { display: grid; gap: 6px; }
.capacity-bar-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
  font-size: 12px;
  font-weight: 700;
}
.capacity-bar-meta strong {
  text-align: end;
  font-size: 12.5px;
  letter-spacing: -0.01em;
  color: #134e4a;
  font-variant-numeric: tabular-nums;
}
.capacity-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.12);
  overflow: hidden;
}
.capacity-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  min-width: 0;
  transition: width 0.85s cubic-bezier(0.22, 1, 0.36, 1);
}
.capacity-track.is-animated span {
  will-change: width;
}
.capacity-track .is-planned { background: linear-gradient(90deg, #34908b, #5bb8b2); }
.capacity-track .is-actual { background: linear-gradient(90deg, #0f766e, #14b8a6); }
.capacity-ring {
  position: relative;
}
.capacity-ring::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.35);
  pointer-events: none;
}
.task-day-groups {
  display: grid;
  gap: 18px;
}
.task-day-group {
  display: grid;
  gap: 12px;
}
.task-day-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 2px;
  border-bottom: 1px dashed rgba(52, 144, 139, 0.28);
}
.task-day-heading strong {
  font-size: 14px;
  color: #1f5c59;
}
.task-day-heading span {
  font-size: 12px;
  color: #5f7a76;
  font-weight: 700;
}
.capacity-stat-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.capacity-stat-strip article {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(52, 144, 139, 0.1);
  padding: 12px 14px;
  display: grid;
  gap: 6px;
}
.capacity-stat-strip strong {
  font-size: 1.05rem;
  color: #134e4a;
  font-variant-numeric: tabular-nums;
}
.tasking-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.tasking-metric-card {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  padding: 16px;
  background: #fff;
  border: 1px solid rgba(52, 144, 139, 0.12);
  display: grid;
  gap: 8px;
  min-height: 132px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.tasking-metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(31, 92, 89, 0.08);
}
.tasking-metric-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tasking-metric-accent {
  width: 90%;
  height: 30%;
  border-radius: 999px;
  background: #34908b;
}
.tasking-metric-card.is-info .tasking-metric-accent { background: #0284c7; }
.tasking-metric-card.is-warning .tasking-metric-accent { background: #d97706; }
.tasking-metric-card.is-danger .tasking-metric-accent { background: #dc2626; }
.tasking-metric-card.is-success .tasking-metric-accent { background: #16a34a; }
.tasking-metric-card.is-idle .tasking-metric-accent { background: #94a3b8; }
.tasking-metric-label { font-size: 12px; font-weight: 800; }
.tasking-metric-card strong {
  font-size: 1.7rem;
  line-height: 1;
  color: #134e4a;
  font-variant-numeric: tabular-nums;
}
.tasking-metric-card small { font-size: 12px; }
@keyframes capacity-pulse {
  0%, 100% { filter: saturate(1); transform: scale(1); }
  50% { filter: saturate(1.08); transform: scale(1.015); }
}
.tasking-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.chip-row, .tab-strip, .subtab-strip {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding-bottom: 4px;
}
.chip-btn {
  border: 1px solid rgba(52, 144, 139, 0.16);
  background: #f7fbfa;
  border-radius: 999px;
  padding: 8px 12px;
  white-space: nowrap;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.chip-btn.is-active {
  background: #dcefec;
  color: #1f5c59;
}
.nav-link-badge.is-mini {
  min-width: 15px;
  height: 15px;
  padding: 0 4px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  line-height: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #1f7a72;
  color: #fff;
}
.compact-search {
  min-width: min(280px, 100%);
}
.task-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.task-card {
  border: 1px solid rgba(52, 144, 139, 0.12);
  border-radius: 18px;
  padding: 14px;
  background: #fff;
  display: grid;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}
.task-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(40, 110, 105, 0.08);
}
.task-card-top, .task-card-footer, .task-card-meta, .task-card-actions, .assignee-mini {
  display: flex;
  align-items: center;
  gap: 8px;
}
.task-card-top { justify-content: space-between; }
.task-card-copy { min-width: 0; flex: 1; display: grid; gap: 2px; }
.task-card-copy strong, .task-card-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-card-meta {
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 12px;
  gap: 6px;
}
.task-time-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 3px 8px;
  font-weight: 800;
  font-size: 11px;
  line-height: 1.3;
}
.task-time-chip.is-planned {
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
}
.task-time-chip.is-timer {
  background: rgba(15, 118, 110, 0.12);
  color: #0f766e;
}
.task-time-chip.is-today {
  background: rgba(2, 132, 199, 0.1);
  color: #0369a1;
}
.task-card-footer { justify-content: space-between; }
.priority-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #94a3b8;
  flex: 0 0 auto;
}
.priority-dot[data-priority='critical'] { background: #dc2626; }
.priority-dot[data-priority='high'] { background: #ea580c; }
.priority-dot[data-priority='medium'] { background: #ca8a04; }
.priority-dot[data-priority='normal'] { background: #34908b; }
.priority-dot[data-priority='low'] { background: #64748b; }
.spill-badge {
  background: #fff4e5;
  color: #9a3412;
  border-radius: 999px;
  padding: 2px 8px;
  font-weight: 700;
}
.timer-readout {
  font-variant-numeric: tabular-nums;
  color: #1f5c59;
}
.empty-state-card, .empty-copy {
  padding: 28px 16px;
  text-align: center;
  color: var(--muted);
  display: grid;
  gap: 10px;
  justify-items: center;
}
@media (max-width: 920px) {
  .capacity-hero-main,
  .active-timer-banner { grid-template-columns: 1fr; }
  .active-timer-banner { flex-direction: column; align-items: stretch; }
  .capacity-stat-strip,
  .tasking-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .task-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .capacity-hero {
    padding: 14px;
    gap: 12px;
  }
  .capacity-hero-main {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 12px;
    align-items: center;
  }
  .capacity-lede { display: none; }
  .capacity-stat-strip,
  .tasking-metric-grid,
  .task-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 10px;
  }
  .capacity-stat-strip article,
  .tasking-metric-card {
    min-width: 0;
    padding: 12px;
  }
  .task-card-footer { flex-direction: column; align-items: stretch; }
  .task-card-actions { flex-wrap: wrap; }
  .capacity-ring { width: 92px; height: 92px; }
  .capacity-ring-core { width: 68px; height: 68px; }
  .capacity-ring-core strong { font-size: 18px; }
  .date-nav-btn {
    width: 36px;
    height: 36px;
    font-size: 20px;
    font-weight: 800;
    line-height: 1;
    color: #1f5c59;
  }
  .tasking-toolbar {
    display: grid;
    gap: 10px;
  }
  .tab-strip {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .tab-strip .chip-btn {
    justify-content: center;
    width: 100%;
  }
}
</style>
