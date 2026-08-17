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
import { formatJalali, getTodayJalali, isoToJalali, jalaliToIso } from '../utils/jalali'
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

onMounted(async () => {
  await loadTaskingDashboard(true)
  timerHandle = window.setInterval(() => {
    timerTick.value += 1
  }, 1000)
  // Soft poll only — sidebar already refreshes badges; avoid double hard reloads.
  pollHandle = window.setInterval(() => {
    if (document.visibilityState === 'hidden') return
    const iso =
      mainTab.value === 'supervise'
        ? (jalaliToIso(superviseDateJalali.value) || state.tasking.date || '')
        : (state.tasking.date || '')
    const options = { soft: true }
    if (mainTab.value === 'supervise') options.superviseOwnerId = superviseOwnerId.value
    void loadTaskingDashboard(true, iso, options).catch(() => {})
  }, 60000)
})

onUnmounted(() => {
  if (timerHandle) window.clearInterval(timerHandle)
  if (pollHandle) window.clearInterval(pollHandle)
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
    const donePercent = Math.min(100, Math.round((actual / progressBase) * 100))
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
  if (isSuperviseView.value) {
    const cap = capacity.value
    let seconds = Number(cap.timerClosedMinutes || 0) * 60
    seconds += Math.max(0, Number(cap.timerActiveSeconds || 0))
    if (seconds > 0) return Math.max(0, Math.floor(seconds / 60))
    return Math.max(0, Number(cap.actualMinutes || 0))
  }
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
  if (isSuperviseView.value && Number.isFinite(Number(capacity.value.donePercent))) {
    return Math.min(100, Math.max(0, Number(capacity.value.donePercent)))
  }
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
        tone: capacityTone.value === 'is-danger' ? 'is-danger' : 'is-warning',
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
    ? filteredSuperviseBuckets.value.all.length
    : (counts.supervise?.all ?? stats.superviseCount)
  return {
    mine: tabBadge(counts.mine?.all ?? stats.mineCount),
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
    const baseIso = jalaliToIso(superviseDateJalali.value) || state.tasking.date
    const base = baseIso ? new Date(`${baseIso}T12:00:00`) : new Date()
    base.setDate(base.getDate() + delta)
    superviseDateJalali.value = isoToJalali(base.toISOString().slice(0, 10)) || formatJalali(getTodayJalali())
    return
  }
  const base = state.tasking.date ? new Date(`${state.tasking.date}T12:00:00`) : new Date()
  base.setDate(base.getDate() + delta)
  const iso = base.toISOString().slice(0, 10)
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
          <p class="capacity-eyebrow">
            <span>{{ isSuperviseView ? 'ظرفیت نظارت' : 'ظرفیت امروز' }}</span>
            <span v-if="isSuperviseView" class="supervise-filter-pill is-inline">{{ superviseFilterLabel }}</span>
          </p>
          <h3>
            <template v-if="isSuperviseView && selectedSuperviseUser">
              {{ selectedSuperviseUser.name }}
            </template>
            <template v-else-if="isSuperviseView">
              {{ capacity.bandLabel || 'نمای کلی تیم' }}
            </template>
            <template v-else>
              {{ capacity.bandLabel || 'بدون برنامه' }}
            </template>
          </h3>
          <p class="capacity-lede">
            <template v-if="isSuperviseView">
              نمایش داینامیک اطلاعات بر اساس کارمند و تاریخ انتخاب‌شده در تب نظارت.
            </template>
            <template v-else>
              درصد و نوار پیشرفت فقط از مجموع تایمرهای امروز نسبت به برنامهٔ روز ساخته می‌شود.
            </template>
          </p>
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
        <div class="tasking-filter-row">
          <template v-if="mainTab === 'supervise'">
            <label class="field-shell supervise-owner-filter">
              <span>کارمند</span>
              <select v-model="superviseOwnerId">
                <option value="">همه کارمندان</option>
                <option v-for="person in superviseEmployeeOptions" :key="person.id" :value="String(person.id)">
                  {{ person.name }}
                </option>
              </select>
            </label>
            <label class="field-shell supervise-date-filter">
              <span>تاریخ</span>
              <ShamsiDatePicker
                v-model="superviseDateJalali"
                model-type="jalali"
                placeholder="انتخاب تاریخ"
              />
            </label>
            <button class="action-btn tone-soft supervise-reset-btn" type="button" @click="resetSuperviseFilters">
              <IconlyIcon name="refresh" decorative />
              <span>پاک‌سازی فیلتر</span>
            </button>
          </template>
          <label class="search-shell compact-search">
            <IconlyIcon name="search" decorative />
            <input v-model="query" type="search" placeholder="جستجوی عنوان، کد یا مسئول" />
          </label>
        </div>
      </div>

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
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
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
.tasking-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: end;
  margin-inline-start: auto;
}
.supervise-owner-filter,
.supervise-date-filter {
  min-width: 190px;
  margin: 0;
}
.supervise-owner-filter span,
.supervise-date-filter span {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted, #5f7a76);
}
.supervise-owner-filter select {
  min-height: 42px;
  width: 100%;
}
.supervise-reset-btn {
  min-height: 42px;
  align-self: end;
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
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
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
  .main-tab-strip.tab-strip {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    overflow: visible;
    padding: 6px 2px 4px;
  }
  .main-tab-strip .chip-btn {
    justify-content: center;
    width: 100%;
    min-height: 48px;
    padding: 10px 28px 10px 10px;
    border-radius: 14px;
    overflow: hidden;
  }
  .main-tab-strip .chip-btn-label {
    white-space: normal;
    text-align: center;
    line-height: 1.35;
    font-size: 13px;
    padding-inline: 2px;
  }
  .main-tab-strip .tasking-tab-badge.is-main {
    top: 5px;
    inset-inline-end: 5px;
    min-width: 17px;
    height: 17px;
    font-size: 10px;
    padding: 0 4px;
  }
  .tab-strip:not(.main-tab-strip) {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    overflow: visible;
    padding-bottom: 2px;
  }
  .tab-strip:not(.main-tab-strip) .chip-btn {
    justify-content: space-between;
    align-items: center;
    width: 100%;
    min-height: 44px;
    padding: 8px 10px;
    border-radius: 12px;
    font-size: 12px;
    gap: 8px;
    overflow: hidden;
  }
  .tab-strip:not(.main-tab-strip) .chip-btn-label {
    white-space: nowrap;
    text-align: start;
    flex: 1 1 auto;
    min-width: 0;
  }
  .tab-strip:not(.main-tab-strip) .tasking-tab-badge.is-sub {
    flex: 0 0 auto;
    min-width: 15px;
    height: 15px;
    font-size: 9px;
  }
}

@media (max-width: 420px) {
  .tab-strip:not(.main-tab-strip) {
    grid-template-columns: minmax(0, 1fr);
  }

  .tab-strip:not(.main-tab-strip) .chip-btn {
    min-height: 40px;
  }
}
</style>
