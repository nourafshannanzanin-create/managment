<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import IconlyIcon from '../components/base/IconlyIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import TaskComposerModal from '../components/TaskComposerModal.vue'
import TaskDetailModal from '../components/TaskDetailModal.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatDurationFa, formatDurationRatioFa } from '../utils/duration'
import { formatJalali, getTodayJalali, getTodayIso, isoToJalali, jalaliToIso, shiftIsoDate } from '../utils/jalali'
import { createLiveEventSource, parseLiveEvent } from '../utils/live'
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
const superviseOwnerId = ref('')
const superviseDateJalali = ref(formatJalali(getTodayJalali()))
const timerTick = ref(0)
let timerHandle = null
let pollHandle = null
let taskingLiveStream = null
let taskingLiveRefreshTimer = null
let superviseReloadTimer = null

function syncSuperviseDateFromState() {
  const iso = String(state.tasking.date || '').slice(0, 10)
  superviseDateJalali.value = iso ? (isoToJalali(iso) || formatJalali(getTodayJalali())) : formatJalali(getTodayJalali())
}

async function reloadSuperviseDashboard() {
  if (mainTab.value !== 'supervise') return
  const iso = jalaliToIso(superviseDateJalali.value) || ''
  if (iso) state.tasking.date = iso
  await loadTaskingDashboard(true, iso, { superviseOwnerId: superviseOwnerId.value })
}

function scheduleSuperviseReload() {
  if (superviseReloadTimer) window.clearTimeout(superviseReloadTimer)
  superviseReloadTimer = window.setTimeout(() => {
    void reloadSuperviseDashboard()
  }, 220)
}

function currentDashboardRefreshOptions() {
  const iso =
    mainTab.value === 'supervise'
      ? (jalaliToIso(superviseDateJalali.value) || state.tasking.date || '')
      : (state.tasking.date || '')
  const options = { soft: true }
  if (mainTab.value === 'supervise') options.superviseOwnerId = superviseOwnerId.value
  return { iso, options }
}

function refreshCurrentTaskingDashboard() {
  if (document.visibilityState === 'hidden') return
  const { iso, options } = currentDashboardRefreshOptions()
  void loadTaskingDashboard(true, iso, options).catch(() => {})
}

function stopTaskingLive() {
  if (pollHandle) {
    window.clearInterval(pollHandle)
    pollHandle = null
  }
  if (taskingLiveRefreshTimer) {
    window.clearTimeout(taskingLiveRefreshTimer)
    taskingLiveRefreshTimer = null
  }
  taskingLiveStream?.close()
  taskingLiveStream = null
}

function startTaskingLive() {
  stopTaskingLive()
  taskingLiveStream = createLiveEventSource(state.authToken)
  taskingLiveStream?.addEventListener('open', refreshCurrentTaskingDashboard)
  taskingLiveStream?.addEventListener('message', (event) => {
    const payload = parseLiveEvent(event.data)
    if (!payload?.type || !String(payload.type).startsWith('task.')) return
    if (taskingLiveRefreshTimer) window.clearTimeout(taskingLiveRefreshTimer)
    taskingLiveRefreshTimer = window.setTimeout(refreshCurrentTaskingDashboard, 350)
  })
  pollHandle = window.setInterval(refreshCurrentTaskingDashboard, 60000)
}

onMounted(async () => {
  await loadTaskingDashboard(true)
  timerHandle = window.setInterval(() => {
    timerTick.value += 1
  }, 1000)
  startTaskingLive()
})

onUnmounted(() => {
  if (timerHandle) window.clearInterval(timerHandle)
  stopTaskingLive()
  if (superviseReloadTimer) window.clearTimeout(superviseReloadTimer)
})

watch(mainTab, (tab) => {
  if (tab === 'mine') subTab.value = 'upcoming'
  if (tab === 'assignments') subTab.value = 'pending'
  if (tab === 'supervise') {
    subTab.value = 'all'
    syncSuperviseDateFromState()
    scheduleSuperviseReload()
  }
  if (tab === 'mentions') subTab.value = 'unread'
})

watch(superviseOwnerId, () => {
  if (mainTab.value !== 'supervise') return
  scheduleSuperviseReload()
})

watch(superviseDateJalali, () => {
  if (mainTab.value !== 'supervise') return
  const iso = jalaliToIso(superviseDateJalali.value) || ''
  if (iso) state.tasking.date = iso
  scheduleSuperviseReload()
})

const isSuperviseView = computed(() => mainTab.value === 'supervise')

function minutesLabel(value) {
  return formatDurationFa(value)
}

function shamsiDateLabel(iso) {
  if (!iso) return 'امروز'
  return isoToJalali(String(iso).slice(0, 10)) || iso
}

function taskOwnerId(task) {
  return Number(task?.assignee?.id || task?.owner?.id || 0)
}

function taskMatchesSuperviseDate(task, isoDate) {
  if (!isoDate) return true
  const allocations = Array.isArray(task?.allocations) ? task.allocations : []
  if (allocations.some((row) => String(row.workDate || row.work_date || '').slice(0, 10) === isoDate)) return true
  if (Number(task.todayPlannedMinutes || 0) > 0) return true
  const due = String(task.dueAt || '').slice(0, 10)
  if (due === isoDate) return true
  if (task.overdue) return true
  const completed = String(task.completedAt || '').slice(0, 10)
  if (completed === isoDate) return true
  const status = String(task.status || '').toLowerCase()
  if (status === 'pending_review' || status === 'changes_requested') return true
  if (['in_progress', 'paused', 'scheduled', 'upcoming'].includes(status)) {
    return allocations.some((row) => String(row.workDate || row.work_date || '').slice(0, 10) >= isoDate) || !allocations.length
  }
  return false
}

function applySuperviseFilters(tasks) {
  let rows = Array.isArray(tasks) ? [...tasks] : []
  const ownerId = Number(superviseOwnerId.value || 0)
  const isoDate = String(jalaliToIso(superviseDateJalali.value) || state.tasking.date || '').slice(0, 10)
  if (ownerId) rows = rows.filter((item) => taskOwnerId(item) === ownerId)
  if (isoDate) rows = rows.filter((item) => taskMatchesSuperviseDate(item, isoDate))
  const q = query.value.trim().toLowerCase()
  if (q) {
    rows = rows.filter((item) =>
      `${item.title} ${item.code} ${item.assignee?.name || ''}`.toLowerCase().includes(q),
    )
  }
  return rows
}

function bucketSuperviseTasks(tasks) {
  const rows = Array.isArray(tasks) ? tasks : []
  return {
    all: rows,
    pendingReview: rows.filter((item) => String(item.status || '').toLowerCase() === 'pending_review'),
    inProgress: rows.filter((item) =>
      ['in_progress', 'paused', 'scheduled', 'upcoming'].includes(String(item.status || '').toLowerCase()),
    ),
    overdue: rows.filter((item) => Boolean(item.overdue)),
    completed: rows.filter((item) => String(item.status || '').toLowerCase() === 'completed'),
  }
}

const allSuperviseTasks = computed(() => {
  const buckets = state.tasking.supervise || {}
  const map = new Map()
  Object.values(buckets).forEach((list) => {
    if (!Array.isArray(list)) return
    list.forEach((task) => {
      if (task?.id) map.set(task.id, task)
    })
  })
  return [...map.values()]
})

const filteredSuperviseBuckets = computed(() => bucketSuperviseTasks(applySuperviseFilters(allSuperviseTasks.value)))

const viewTeamCapacity = computed(() => {
  const tasks = filteredSuperviseBuckets.value.all || []
  const planned = tasks.reduce((sum, item) => sum + Number(item.todayPlannedMinutes || 0), 0)
  const actual = tasks.reduce((sum, item) => sum + Number(item.actualMinutes || 0), 0)
  const progressBase = Math.max(planned, actual, 1)
  const donePercent = Math.min(100, Math.round((actual / progressBase) * 100))
  return {
    bandLabel: superviseOwnerId.value ? 'ظرفیت کارمند انتخاب‌شده' : 'خلاصه تیم (فیلتر فعال)',
    plannedMinutes: planned,
    actualMinutes: actual,
    targetMinutes: planned,
    effectiveWorkMinutes: planned,
    progressBaseMinutes: progressBase,
    remainingTargetMinutes: Math.max(0, planned - actual),
    timerClosedMinutes: actual,
    timerActiveSeconds: 0,
    donePercent,
  }
})

const capacity = computed(() => {
  if (!isSuperviseView.value) return state.tasking.capacity || {}

  const teamCap = viewTeamCapacity.value
  const apiCap = state.tasking.superviseFocus?.capacity
  if (superviseOwnerId.value && apiCap) {
    const planned = teamCap.plannedMinutes
    const actual = Number(apiCap.actualMinutes || 0)
    const target = Number(apiCap.targetMinutes || 0)
    const progressBase = Math.max(Number(apiCap.progressBaseMinutes || 0), target, planned, actual, 1)
    const progressDenominator = target > 0 ? target : progressBase
    const donePercent = Math.min(100, Math.round((actual / progressDenominator) * 100))
    return {
      ...apiCap,
      plannedMinutes: planned,
      targetMinutes: target || planned,
      progressBaseMinutes: progressBase,
      remainingTargetMinutes: Math.max(0, (target || planned) - planned),
      donePercent,
      bandLabel: apiCap.bandLabel || teamCap.bandLabel,
    }
  }
  return teamCap
})
const targetDurationMinutes = computed(() => {
  const cap = capacity.value
  const target = Number(cap.targetMinutes || 0)
  if (target > 0) return target
  return Number(cap.effectiveWorkMinutes || 0)
})

function resolveWorkedDurationSeconds(cap, activeTimer, nowMs = Date.now()) {
  if (!cap) return 0
  const closedMinutesRaw = cap.timerClosedMinutes
  const hasClosedBaseline = closedMinutesRaw != null && closedMinutesRaw !== '' && Number.isFinite(Number(closedMinutesRaw))

  if (activeTimer?.startedAt) {
    const started = new Date(activeTimer.startedAt).getTime()
    if (Number.isFinite(started)) {
      const activeElapsed = Math.max(0, Math.floor((nowMs - started) / 1000))
      if (hasClosedBaseline) {
        return Math.max(0, Number(closedMinutesRaw) * 60 + activeElapsed)
      }
      const baselineSeconds = Math.max(0, Number(cap.actualMinutes || 0) * 60)
      const apiActiveSeconds = Math.max(0, Number(cap.timerActiveSeconds || 0))
      return Math.max(0, baselineSeconds + Math.max(0, activeElapsed - apiActiveSeconds))
    }
  }

  if (hasClosedBaseline) {
    return Math.max(0, Number(closedMinutesRaw) * 60 + Number(cap.timerActiveSeconds || 0))
  }
  return Math.max(0, Number(cap.actualMinutes || 0) * 60)
}

const workedDurationSeconds = computed(() => {
  void timerTick.value
  if (isSuperviseView.value) {
    return Math.max(0, Number(capacity.value.actualMinutes || 0) * 60)
  }
  return resolveWorkedDurationSeconds(capacity.value, state.tasking.activeTimer)
})

const targetDurationSeconds = computed(() => Math.max(0, targetDurationMinutes.value * 60))

const progressPercent = computed(() => {
  const target = targetDurationSeconds.value
  const worked = workedDurationSeconds.value
  if (target <= 0) return worked > 0 ? 100 : 0
  return Math.min(100, Math.max(0, (worked / target) * 100))
})

const progressPercentDisplay = computed(() => Math.round(progressPercent.value))
const workedDurationMinutes = computed(() => Math.floor(workedDurationSeconds.value / 60))
const progressBarWidth = computed(() => `${progressPercent.value}%`)

const plannedProgressPercent = computed(() => {
  const target = Number(capacity.value.targetMinutes || 0)
  const planned = Number(capacity.value.plannedMinutes || 0)
  if (target <= 0) return planned > 0 ? 100 : 0
  return Math.min(100, Math.max(0, (planned / target) * 100))
})
const plannedBarWidth = computed(() => `${plannedProgressPercent.value}%`)

const capacityAccent = computed(() => {
  const pct = progressPercentDisplay.value
  if (pct >= 100) return 'is-complete'
  if (pct >= 70) return 'is-good'
  if (pct >= 40) return 'is-mid'
  if (pct > 0) return 'is-started'
  return 'is-idle'
})
const capacityRingStyle = computed(() => {
  const pct = Math.min(100, Math.max(0, progressPercent.value))
  const fill = '#16a34a'
  const track = '#e2e8f0'
  if (pct <= 0) {
    return { background: track }
  }
  return {
    background: `conic-gradient(from -90deg, ${fill} 0%, ${fill} ${pct}%, ${track} ${pct}%, ${track} 100%)`,
  }
})
const capacityHeadline = computed(() => {
  if (isSuperviseView.value && selectedSuperviseUser.value) return selectedSuperviseUser.value.name
  if (isSuperviseView.value) return capacity.value.bandLabel || 'نمای کلی تیم'
  return capacity.value.bandLabel || 'بدون برنامه'
})
const capacitySubtitle = computed(() => {
  if (isSuperviseView.value) return 'پیشرفت بر اساس کارمند و تاریخ انتخاب‌شده'
  return `${minutesLabel(workedDurationMinutes.value)} از ${minutesLabel(targetDurationMinutes.value)} کارکرد ثبت شده`
})

const displayDate = computed(() => {
  if (isSuperviseView.value) return shamsiDateLabel(jalaliToIso(superviseDateJalali.value) || state.tasking.date)
  return shamsiDateLabel(state.tasking.date)
})

const superviseStats = computed(() => {
  const buckets = filteredSuperviseBuckets.value
  return {
    todayCount: buckets.all.filter((item) => Number(item.todayPlannedMinutes || 0) > 0).length,
    remainingMinutes: capacity.value.remainingTargetMinutes ?? viewTeamCapacity.value.remainingTargetMinutes,
    needsAction: buckets.pendingReview.length + buckets.overdue.length,
    completedToday: buckets.completed.length,
  }
})

const selectedSuperviseUser = computed(() => {
  const ownerId = Number(superviseOwnerId.value || 0)
  if (!ownerId) return null
  return (
    state.tasking.superviseFocus?.user
    || superviseEmployeeOptions.value.find((item) => Number(item.id) === ownerId)
    || null
  )
})

const superviseFilterLabel = computed(() => {
  const dateLabel = shamsiDateLabel(jalaliToIso(superviseDateJalali.value) || state.tasking.date)
  const userLabel = selectedSuperviseUser.value?.name || 'همه کارمندان'
  return `${userLabel} · ${dateLabel}`
})

const remainingTargetMinutes = computed(() =>
  Math.max(0, Number(capacity.value.targetMinutes || 0) - Number(capacity.value.plannedMinutes || 0)),
)
const metricCards = computed(() => {
  if (isSuperviseView.value) {
    const stats = superviseStats.value
    const cap = capacity.value
    return [
      {
        key: 'today',
        label: 'کارهای روز',
        value: String(stats.todayCount || 0),
        hint: selectedSuperviseUser.value ? `برنامه ${selectedSuperviseUser.value.name}` : 'برنامه روز فیلترشده',
        icon: 'assignment',
        tone: 'is-info',
      },
      {
        key: 'remaining',
        label: 'باقی‌مانده هدف',
        value: minutesLabel(stats.remainingMinutes ?? cap.remainingTargetMinutes ?? remainingTargetMinutes.value),
        hint: 'تا رسیدن به ظرفیت هدف',
        icon: 'schedule',
        tone: ['is-complete', 'is-good'].includes(capacityAccent.value) ? 'is-success' : 'is-warning',
      },
      {
        key: 'action',
        label: 'نیازمند اقدام',
        value: String(stats.needsAction || 0),
        hint: 'بررسی، تأخیر یا پیگیری',
        icon: 'pending_actions',
        tone: Number(stats.needsAction || 0) > 0 ? 'is-warning' : 'is-idle',
      },
      {
        key: 'done',
        label: 'تکمیل‌شده',
        value: String(stats.completedToday || 0),
        hint: 'بسته و تأییدشده',
        icon: 'verified',
        tone: 'is-success',
      },
    ]
  }
  return [
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
      tone: ['is-complete', 'is-good'].includes(capacityAccent.value) ? 'is-success' : 'is-warning',
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
  ]
})

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
  { key: 'closed', label: 'بسته شده', count: counts.value.mine?.closed, hideBadge: true },
])

const assignmentSubTabs = computed(() => [
  { key: 'pending', label: 'ارجاع به من', count: counts.value.assignments?.pending },
  { key: 'outboundReview', label: 'نیازمند تایید من', count: counts.value.assignments?.outboundReview },
  { key: 'outbound', label: 'ارجاع داده‌شده', count: counts.value.assignments?.outbound, hideBadge: true },
])

const superviseSubTabs = computed(() => {
  const buckets = isSuperviseView.value ? filteredSuperviseBuckets.value : bucketSuperviseTasks(allSuperviseTasks.value)
  return [
    { key: 'all', label: 'همه تیم', count: buckets.all.length },
    { key: 'pendingReview', label: 'نیازمند بررسی', count: buckets.pendingReview.length },
    { key: 'inProgress', label: 'در حال انجام', count: buckets.inProgress.length },
    { key: 'overdue', label: 'تأخیرها', count: buckets.overdue.length },
    { key: 'completed', label: 'تکمیل‌شده', count: buckets.completed.length, hideBadge: true },
  ]
})

const mentionSubTabs = computed(() => [
  { key: 'unread', label: 'خوانده‌نشده', count: counts.value.mentions || state.tasking.stats?.unreadMentions },
  { key: 'all', label: 'همه منشن‌ها', count: counts.value.mentionsAll || counts.value.mentions, hideBadge: true },
])

const currentSubTabs = computed(() => {
  if (mainTab.value === 'assignments') return assignmentSubTabs.value
  if (mainTab.value === 'supervise') return superviseSubTabs.value
  if (mainTab.value === 'mentions') return mentionSubTabs.value
  return mineSubTabs.value
})

const superviseEmployeeOptions = computed(() => {
  const map = new Map()
  const buckets = state.tasking.supervise || {}
  Object.values(buckets).forEach((list) => {
    if (!Array.isArray(list)) return
    list.forEach((task) => {
      const person = task?.assignee || task?.owner
      const id = Number(person?.id || 0)
      const name = String(person?.name || '').trim()
      if (!id || !name || map.has(id)) return
      map.set(id, { id, name })
    })
  })
  ;(state.tasking.assigneeOptions || []).forEach((person) => {
    const id = Number(person?.id || 0)
    const name = String(person?.name || '').trim()
    if (!id || !name || map.has(id)) return
    map.set(id, { id, name })
  })
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name, 'fa'))
})

const currentTasks = computed(() => {
  if (mainTab.value === 'mine' && subTab.value === 'upcoming') return upcomingPool.value
  if (mainTab.value === 'supervise') {
    return filteredSuperviseBuckets.value[subTab.value] || filteredSuperviseBuckets.value.all || []
  }
  const source =
    mainTab.value === 'assignments'
      ? state.tasking.assignments
      : mainTab.value === 'mentions'
        ? state.tasking.mentions
        : state.tasking.mine
  let rows = source?.[subTab.value] || []
  const q = query.value.trim().toLowerCase()
  if (!q) return rows
  return rows.filter((item) =>
    `${item.title} ${item.code} ${item.assignee?.name || ''}`.toLowerCase().includes(q),
  )
})

const showGroupedUpcoming = computed(() =>
  mainTab.value === 'mine' && subTab.value === 'upcoming' && !query.value.trim() && !superviseOwnerId.value,
)

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
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0
}

function tabBadge(value) {
  const n = miniCount(value)
  return n > 0 ? n.toLocaleString('fa-IR') : ''
}

function shouldShowSubTabBadge(item) {
  if (item?.hideBadge) return false
  return Boolean(tabBadge(item?.count))
}

const mainTabBadges = computed(() => {
  const counts = state.tasking.counts || {}
  const stats = state.tasking.stats || {}
  const superviseCount = isSuperviseView.value
    ? filteredSuperviseBuckets.value.pendingReview.length
      + filteredSuperviseBuckets.value.inProgress.length
      + filteredSuperviseBuckets.value.overdue.length
    : (counts.supervise?.all ?? stats.superviseCount)
  const openMineCount =
    (counts.mine?.today ?? 0)
    + (counts.mine?.upcoming ?? 0)
    + (counts.mine?.inProgress ?? 0)
    + (counts.mine?.pendingReview ?? 0)
    + (counts.mine?.changesRequested ?? 0)
  return {
    mine: tabBadge(counts.mine?.all ?? openMineCount ?? stats.mineCount),
    assignments: tabBadge(counts.assignments?.all ?? stats.assignmentCount),
    supervise: tabBadge(superviseCount),
    mentions: tabBadge(counts.mentions || stats.unreadMentions),
  }
})

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
  if (isSuperviseView.value) {
    const baseIso = jalaliToIso(superviseDateJalali.value) || state.tasking.date || getTodayIso()
    superviseDateJalali.value = isoToJalali(shiftIsoDate(baseIso, delta)) || formatJalali(getTodayJalali())
    return
  }
  const baseIso = state.tasking.date || getTodayIso()
  const iso = shiftIsoDate(baseIso, delta)
  state.tasking.date = iso
  await loadTaskingDashboard(true, iso)
}

async function goToday() {
  if (isSuperviseView.value) {
    superviseDateJalali.value = formatJalali(getTodayJalali())
    return
  }
  state.tasking.date = ''
  await loadTaskingDashboard(true)
}

async function resetSuperviseFilters() {
  superviseOwnerId.value = ''
  superviseDateJalali.value = formatJalali(getTodayJalali())
  await reloadSuperviseDashboard()
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
      :description="isSuperviseView ? 'نظارت بر کار تیم با فیلتر کارمند و تاریخ' : 'برنامه روزانه، زمان اجرا و وضعیت کارهای شما'"
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
            <span v-if="isSuperviseView" class="supervise-filter-pill">{{ superviseFilterLabel }}</span>
          </div>
          <button class="action-btn tone-primary" type="button" @click="openTaskComposer">
            <IconlyIcon name="plus" decorative />
            <span>تسک جدید</span>
          </button>
        </div>
      </template>
    </PageHeader>

    <section v-if="state.tasking.activeTimer && !isSuperviseView" class="active-timer-banner">
      <IconlyIcon name="timer" decorative />
      <div>
        <strong>{{ state.tasking.activeTimer.taskTitle }}</strong>
        <small>تایمر فعال</small>
      </div>
      <span>{{ formatElapsed({ activeTimer: state.tasking.activeTimer }) }}</span>
    </section>

    <section class="capacity-hero">
      <div class="capacity-hero-grid">
        <div class="capacity-ring-block">
          <div class="capacity-ring" :style="capacityRingStyle">
            <div class="capacity-ring-core">
              <strong>{{ progressPercentDisplay }}</strong>
              <small>درصد</small>
            </div>
          </div>
          <span class="capacity-ring-caption">پیشرفت امروز</span>
        </div>

        <div class="capacity-body">
          <div class="capacity-head">
            <div>
              <p class="capacity-eyebrow">
                {{ isSuperviseView ? 'ظرفیت نظارت' : 'ظرفیت امروز' }}
                <span v-if="isSuperviseView" class="supervise-filter-pill is-inline">{{ superviseFilterLabel }}</span>
              </p>
              <h3>{{ capacityHeadline }}</h3>
              <p class="capacity-subtitle">{{ capacitySubtitle }}</p>
            </div>
          </div>

          <div class="capacity-progress-list">
            <div class="capacity-progress-item">
              <div class="capacity-progress-head">
                <span class="capacity-progress-label">
                  <i class="capacity-dot is-planned"></i>
                  برنامه‌ریزی‌شده
                </span>
                <strong>{{ formatDurationRatioFa(capacity.plannedMinutes, capacity.targetMinutes) }} · {{ Math.round(plannedProgressPercent) }}٪</strong>
              </div>
              <div class="capacity-track">
                <span class="capacity-fill is-planned" :style="{ width: plannedBarWidth }"></span>
              </div>
            </div>
            <div class="capacity-progress-item">
              <div class="capacity-progress-head">
                <span class="capacity-progress-label">
                  <i class="capacity-dot is-actual"></i>
                  کارکرد تایمر
                </span>
                <strong>{{ formatDurationRatioFa(workedDurationMinutes, targetDurationMinutes) }} · {{ progressPercentDisplay }}٪</strong>
              </div>
              <div class="capacity-track">
                <span class="capacity-fill is-actual" :style="{ width: progressBarWidth }"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="capacity-stats">
        <article>
          <small>ساعت مؤثر</small>
          <strong>{{ minutesLabel(capacity.effectiveWorkMinutes) }}</strong>
        </article>
        <article>
          <small>ظرفیت هدف</small>
          <strong>{{ minutesLabel(capacity.targetMinutes) }}</strong>
        </article>
        <article>
          <small>برنامه‌ریزی</small>
          <strong>{{ minutesLabel(capacity.plannedMinutes) }}</strong>
        </article>
        <article :class="capacityAccent">
          <small>کارکرد</small>
          <strong>{{ minutesLabel(workedDurationMinutes) }}</strong>
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
      <div class="tasking-toolbar" :class="{ 'is-supervise': mainTab === 'supervise' }">
        <div class="chip-row tab-strip main-tab-strip">
          <button type="button" :class="['chip-btn', mainTab === 'mine' && 'is-active']" @click="mainTab = 'mine'">
            <span class="chip-btn-label">کارهای من</span>
            <span v-if="mainTabBadges.mine" class="tasking-tab-badge is-main">{{ mainTabBadges.mine }}</span>
          </button>
          <button type="button" :class="['chip-btn', mainTab === 'assignments' && 'is-active']" @click="mainTab = 'assignments'">
            <span class="chip-btn-label">ارجاع‌ها</span>
            <span v-if="mainTabBadges.assignments" class="tasking-tab-badge is-main">{{ mainTabBadges.assignments }}</span>
          </button>
          <button type="button" :class="['chip-btn', mainTab === 'supervise' && 'is-active']" @click="mainTab = 'supervise'">
            <span class="chip-btn-label">نظارت</span>
            <span v-if="mainTabBadges.supervise" class="tasking-tab-badge is-main">{{ mainTabBadges.supervise }}</span>
          </button>
          <button type="button" :class="['chip-btn', mainTab === 'mentions' && 'is-active']" @click="mainTab = 'mentions'">
            <span class="chip-btn-label">منشن</span>
            <span v-if="mainTabBadges.mentions" class="tasking-tab-badge is-main">{{ mainTabBadges.mentions }}</span>
          </button>
        </div>

        <div v-if="mainTab !== 'supervise'" class="tasking-filter-row">
          <label class="search-shell compact-search">
            <IconlyIcon name="search" decorative />
            <input v-model="query" type="search" placeholder="جستجوی عنوان، کد یا مسئول" />
          </label>
        </div>
      </div>

      <section v-if="mainTab === 'supervise'" class="supervise-filters">
        <div class="supervise-filters-grid">
          <label class="supervise-field">
            <span class="supervise-field-label">کارمند</span>
            <select v-model="superviseOwnerId" class="supervise-control">
              <option value="">همه کارمندان</option>
              <option v-for="person in superviseEmployeeOptions" :key="person.id" :value="String(person.id)">
                {{ person.name }}
              </option>
            </select>
          </label>
          <label class="supervise-field">
            <span class="supervise-field-label">تاریخ</span>
            <div class="supervise-control-wrap">
              <ShamsiDatePicker
                v-model="superviseDateJalali"
                model-type="jalali"
                placeholder="انتخاب تاریخ"
              />
            </div>
          </label>
          <label class="supervise-field">
            <span class="supervise-field-label">جستجو</span>
            <span class="search-shell supervise-control supervise-search">
              <IconlyIcon name="search" decorative />
              <input v-model="query" type="search" placeholder="عنوان، کد یا مسئول" />
            </span>
          </label>
          <div class="supervise-field supervise-field-action">
            <span class="supervise-field-label" aria-hidden="true">&nbsp;</span>
            <button class="action-btn tone-soft supervise-control supervise-reset-btn" type="button" @click="resetSuperviseFilters">
              <IconlyIcon name="refresh" decorative />
              <span>پاک‌سازی</span>
            </button>
          </div>
        </div>
      </section>

      <div class="chip-row tab-strip subtab-strip">
        <button
          v-for="item in currentSubTabs"
          :key="item.key"
          type="button"
          :class="['chip-btn', subTab === item.key && 'is-active']"
          @click="subTab = item.key"
        >
          <span class="chip-btn-label">{{ item.label }}</span>
          <span v-if="shouldShowSubTabBadge(item)" class="tasking-tab-badge is-sub">{{ tabBadge(item.count) }}</span>
        </button>
      </div>

      <div v-if="state.tasking.loading && !state.tasking.loaded" class="empty-copy">در حال بارگذاری...</div>

      <div v-else-if="showGroupedUpcoming ? !upcomingGroups.length : !currentTasks.length" class="empty-state-card">
        <strong>موردی برای نمایش نیست</strong>
        <p v-if="mainTab === 'mine' && subTab === 'upcoming'">هنوز تسکی برای پیش‌رو ندارید.</p>
        <p v-else-if="mainTab === 'assignments'">ارجاع جدیدی برای نمایش نیست.</p>
        <p v-else-if="mainTab === 'supervise'">با فیلتر کارمند یا تاریخ، موردی یافت نشد.</p>
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
                <span v-if="task.approvedAt" class="task-time-chip is-approved">تأیید {{ shamsiDateLabel(String(task.approvedAt).slice(0, 10)) }}</span>
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
            <span v-if="task.approvedAt" class="task-time-chip is-approved">تأیید {{ shamsiDateLabel(String(task.approvedAt).slice(0, 10)) }}</span>
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
  flex-wrap: wrap;
}
.supervise-filter-pill {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}
.supervise-filter-pill.is-inline {
  margin-inline-start: 8px;
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
  border-radius: 20px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(31, 92, 89, 0.06);
}
.active-timer-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: #eef7f6;
}
.capacity-hero {
  display: grid;
  gap: 16px;
  padding: 20px;
}
.capacity-hero-grid {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 24px;
  align-items: center;
}
.capacity-ring-block {
  display: grid;
  gap: 8px;
  justify-items: center;
  flex-shrink: 0;
}
.capacity-ring {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  transition: background 0.35s ease;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.04);
}
.capacity-ring-core {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: #fff;
  display: grid;
  place-items: center;
  gap: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.capacity-ring-core strong {
  font-size: 1.75rem;
  line-height: 1;
  color: #134e4a;
  font-variant-numeric: tabular-nums;
  font-weight: 900;
}
.capacity-ring-core small {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  margin-top: 2px;
}
.capacity-ring-caption {
  font-size: 12px;
  font-weight: 800;
  color: #64748b;
}
.capacity-body {
  display: grid;
  gap: 16px;
  min-width: 0;
}
.capacity-head h3 {
  margin: 4px 0 0;
  font-size: 1.25rem;
  color: #134e4a;
  font-weight: 900;
}
.capacity-eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  color: #64748b;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.capacity-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
}
.capacity-progress-list {
  display: grid;
  gap: 14px;
}
.capacity-progress-item {
  display: grid;
  gap: 8px;
}
.capacity-progress-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.capacity-progress-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}
.capacity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.capacity-dot.is-planned { background: #34908b; }
.capacity-dot.is-actual { background: #16a34a; }
.capacity-progress-head strong {
  font-size: 13px;
  font-weight: 800;
  color: #134e4a;
  font-variant-numeric: tabular-nums;
}
.capacity-track {
  height: 12px;
  border-radius: 999px;
  background: #eef2f1;
  overflow: hidden;
  position: relative;
}
.capacity-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  min-width: 0;
  transition: width 0.25s ease;
  will-change: width;
  background: #34908b !important;
}
.capacity-fill.is-planned {
  background: linear-gradient(90deg, #16a34a, #86efac);
}
.capacity-fill.is-actual {
  background: linear-gradient(90deg, #16a34a, #4ade80);
}
.capacity-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  padding-top: 4px;
  border-top: 1px solid rgba(52, 144, 139, 0.08);
}
.capacity-stats article {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafb;
}
.capacity-stats article small {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}
.capacity-stats article strong {
  font-size: 1rem;
  font-weight: 900;
  color: #134e4a;
  font-variant-numeric: tabular-nums;
}
.capacity-stats article.is-started strong { color: #34908b; }
.capacity-stats article.is-mid strong { color: #d97706; }
.capacity-stats article.is-good strong,
.capacity-stats article.is-complete strong { color: #16a34a; }
.capacity-stat-strip small,
.tasking-metric-label,
.tasking-metric-card small {
  color: var(--muted, #64748b);
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
.tasking-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.tasking-toolbar.is-supervise {
  margin-bottom: 10px;
}
.tasking-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: end;
  margin-inline-start: auto;
}
.supervise-filters {
  margin: 0 0 14px;
  padding: 14px;
  border-radius: 16px;
  background: #f7fbfa;
  border: 1px solid rgba(52, 144, 139, 0.14);
}
.supervise-filters-grid {
  display: grid;
  grid-template-columns: minmax(180px, 1.1fr) minmax(170px, 0.95fr) minmax(220px, 1.4fr) auto;
  gap: 12px;
  align-items: start;
}
.supervise-field {
  display: grid;
  grid-template-rows: 18px 44px;
  gap: 6px;
  margin: 0;
  min-width: 0;
  align-content: start;
}
.supervise-field-label {
  display: block;
  height: 18px;
  line-height: 18px;
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  color: var(--muted, #5f7a76);
  white-space: nowrap;
}
.supervise-control,
.supervise-control-wrap,
.supervise-search,
.supervise-reset-btn {
  height: 44px;
  min-height: 44px;
  max-height: 44px;
  width: 100%;
  box-sizing: border-box;
  margin: 0;
}
.supervise-field select.supervise-control {
  display: block;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  background: #fff;
  color: inherit;
  font: inherit;
}
.supervise-control-wrap {
  display: flex;
  align-items: stretch;
}
.supervise-control-wrap :deep(.shamsi-picker),
.supervise-control-wrap :deep(.shamsi-picker-input-wrap) {
  width: 100%;
  height: 44px;
  min-height: 44px;
}
.supervise-control-wrap :deep(.shamsi-picker-input) {
  height: 44px;
  min-height: 44px;
  max-height: 44px;
  box-sizing: border-box;
}
.supervise-search {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  background: #fff;
}
.supervise-search input {
  min-width: 0;
  flex: 1;
  height: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
}
.supervise-field-action {
  min-width: 120px;
}
.supervise-reset-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  padding-inline: 14px;
}
.chip-row, .tab-strip, .subtab-strip {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding-bottom: 4px;
}
.subtab-strip {
  margin-top: 4px;
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
  justify-content: center;
  gap: 8px;
  position: relative;
  min-width: 0;
  isolation: isolate;
}
.chip-btn-label {
  flex: 0 0 auto;
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
}
.chip-btn.is-active {
  background: #dcefec;
  color: #1f5c59;
}
.tasking-tab-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e11d48;
  color: #fff !important;
  font-size: 11px;
  font-weight: 800;
  line-height: 1;
  flex: 0 0 auto;
  box-shadow: 0 0 0 2px #f7fbfa;
}
.chip-btn.is-active .tasking-tab-badge {
  box-shadow: 0 0 0 2px #dcefec;
}
.tasking-tab-badge.is-main {
  position: absolute;
  top: 4px;
  inset-inline-end: 4px;
  z-index: 2;
  pointer-events: none;
}
.main-tab-strip .chip-btn {
  padding-inline: 12px 30px;
}
.tasking-tab-badge.is-sub {
  background: #1f7a72;
  min-width: 16px;
  height: 16px;
  font-size: 10px;
  position: static;
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
.task-time-chip.is-approved {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
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
  .capacity-hero-grid,
  .active-timer-banner { grid-template-columns: 1fr; }
  .active-timer-banner { flex-direction: column; align-items: stretch; }
  .capacity-stats,
  .tasking-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .task-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .capacity-hero {
    padding: 14px;
    gap: 12px;
  }
  .capacity-hero-grid {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 14px;
  }
  .capacity-ring { width: 88px; height: 88px; }
  .capacity-ring-core { width: 66px; height: 66px; }
  .capacity-ring-core strong { font-size: 1.35rem; }
  .capacity-subtitle { display: none; }
  .capacity-stats,
  .tasking-metric-grid,
  .task-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 10px;
  }
  .capacity-stats article,
  .tasking-metric-card {
    min-width: 0;
    padding: 12px;
  }
  .task-card-footer { flex-direction: column; align-items: stretch; }
  .task-card-actions { flex-wrap: wrap; }
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
  .supervise-filters {
    padding: 12px;
    border-radius: 14px;
  }
  .supervise-filters-grid {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    align-items: start;
  }
  .supervise-field:nth-child(3),
  .supervise-field-action {
    grid-column: 1 / -1;
  }
  .supervise-reset-btn {
    width: 100%;
  }
  .main-tab-strip.tab-strip,
  .tab-strip:not(.main-tab-strip) {
    display: flex;
    flex-wrap: nowrap;
    gap: 8px;
    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    padding: 4px 2px 8px;
  }
  .main-tab-strip .chip-btn,
  .tab-strip:not(.main-tab-strip) .chip-btn {
    flex: 0 0 auto;
    width: auto;
    min-width: max-content;
    min-height: 42px;
    padding: 8px 14px;
    border-radius: 999px;
    overflow: visible;
    justify-content: center;
    gap: 8px;
    font-size: 13px;
  }
  .main-tab-strip .chip-btn {
    padding-inline: 14px 28px;
  }
  .main-tab-strip .chip-btn-label,
  .tab-strip:not(.main-tab-strip) .chip-btn-label {
    white-space: nowrap;
    overflow: visible;
    text-overflow: clip;
    flex: 0 0 auto;
    min-width: auto;
    text-align: center;
    line-height: 1.3;
    font-size: 13px;
  }
  .main-tab-strip .tasking-tab-badge.is-main {
    top: 4px;
    inset-inline-end: 4px;
    min-width: 17px;
    height: 17px;
    font-size: 10px;
    padding: 0 4px;
  }
  .tab-strip:not(.main-tab-strip) .tasking-tab-badge.is-sub {
    flex: 0 0 auto;
    min-width: 15px;
    height: 15px;
    font-size: 9px;
  }
}

@media (max-width: 420px) {
  .main-tab-strip .chip-btn,
  .tab-strip:not(.main-tab-strip) .chip-btn {
    min-height: 40px;
    font-size: 12px;
  }
  .supervise-filters-grid {
    grid-template-columns: 1fr;
  }
}
</style>
