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
const subTab = ref('today')
const query = ref('')
const timerTick = ref(0)
let timerHandle = null
let pollHandle = null

onMounted(async () => {
  await loadTaskingDashboard(true)
  timerHandle = window.setInterval(() => {
    timerTick.value += 1
  }, 1000)
  pollHandle = window.setInterval(() => {
    void loadTaskingDashboard(true).catch(() => {})
  }, 20000)
})

onUnmounted(() => {
  if (timerHandle) window.clearInterval(timerHandle)
  if (pollHandle) window.clearInterval(pollHandle)
})

watch(mainTab, (tab) => {
  if (tab === 'mine') subTab.value = 'today'
  if (tab === 'assignments') subTab.value = 'pending'
  if (tab === 'supervise') subTab.value = 'pendingReview'
  if (tab === 'mentions') subTab.value = 'unread'
})

const capacity = computed(() => state.tasking.capacity || {})
const capacityPercent = computed(() => Math.min(100, Number(capacity.value.utilizationPercent || 0)))
const capacityTone = computed(() => {
  const band = capacity.value.band
  if (band === 'over') return 'is-danger'
  if (band === 'high') return 'is-warning'
  if (band === 'target') return 'is-success'
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

const mineSubTabs = computed(() => [
  { key: 'today', label: 'امروز', count: counts.value.mine?.today },
  { key: 'upcoming', label: 'پیش‌رو', count: counts.value.mine?.upcoming },
  { key: 'inProgress', label: 'در حال انجام', count: counts.value.mine?.inProgress },
  { key: 'pendingReview', label: 'در انتظار بررسی', count: counts.value.mine?.pendingReview },
  { key: 'changesRequested', label: 'برگشتی', count: counts.value.mine?.changesRequested },
  { key: 'closed', label: 'بسته‌شده', count: counts.value.mine?.closed },
  { key: 'all', label: 'همه', count: counts.value.mine?.all },
])

const assignmentSubTabs = computed(() => [
  { key: 'pending', label: 'نیازمند پاسخ', count: counts.value.assignments?.pending },
  { key: 'all', label: 'همه ارجاع‌ها', count: counts.value.assignments?.all },
])

const superviseSubTabs = computed(() => [
  { key: 'pendingReview', label: 'نیازمند بررسی', count: counts.value.supervise?.pendingReview },
  { key: 'inProgress', label: 'در حال انجام تیم', count: counts.value.supervise?.inProgress },
  { key: 'overdue', label: 'تأخیرها', count: counts.value.supervise?.overdue },
  { key: 'completed', label: 'تکمیل‌شده', count: counts.value.supervise?.completed },
  { key: 'all', label: 'همه تحت نظارت', count: counts.value.supervise?.all },
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
              <strong>{{ capacity.utilizationPercent || 0 }}٪</strong>
              <small>بهره‌برداری</small>
            </div>
          </div>
        </div>
        <div class="capacity-copy">
          <p class="capacity-eyebrow">ظرفیت امروز</p>
          <h3>{{ capacity.bandLabel || 'بدون برنامه' }}</h3>
          <p class="capacity-lede">بر اساس ساعت کاری مؤثر و هدف برنامه‌ریزی مجموعه به‌روز می‌شود.</p>
          <div class="capacity-bars">
            <div class="capacity-bar-row">
              <div class="capacity-bar-meta">
                <span>برنامه‌ریزی‌شده</span>
                <strong>{{ formatDurationRatioFa(capacity.plannedMinutes, capacity.targetMinutes) }}</strong>
              </div>
              <div class="capacity-track">
                <span
                  class="is-planned"
                  :style="{ width: `${Math.min(100, capacity.targetMinutes ? (Number(capacity.plannedMinutes || 0) / Number(capacity.targetMinutes)) * 100 : 0)}%` }"
                ></span>
              </div>
            </div>
            <div class="capacity-bar-row">
              <div class="capacity-bar-meta">
                <span>انجام‌شده</span>
                <strong>{{ formatDurationRatioFa(capacity.actualMinutes, capacity.effectiveWorkMinutes) }}</strong>
              </div>
              <div class="capacity-track">
                <span
                  class="is-actual"
                  :style="{ width: `${Math.min(100, capacity.effectiveWorkMinutes ? (Number(capacity.actualMinutes || 0) / Number(capacity.effectiveWorkMinutes)) * 100 : 0)}%` }"
                ></span>
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
          <small>انجام‌شده</small>
          <strong>{{ minutesLabel(capacity.actualMinutes) }}</strong>
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

      <div v-if="state.tasking.loading" class="empty-copy">در حال بارگذاری...</div>

      <div v-else-if="!currentTasks.length" class="empty-state-card">
        <strong>موردی برای نمایش نیست</strong>
        <p v-if="mainTab === 'mine' && subTab === 'today'">برای امروز هنوز تسکی برنامه‌ریزی نشده است.</p>
        <p v-else-if="mainTab === 'assignments'">ارجاع جدیدی نیازمند پاسخ شما نیست.</p>
        <p v-else>در این فیلتر تسکی وجود ندارد.</p>
        <button v-if="mainTab === 'mine'" class="action-btn tone-primary" type="button" @click="openTaskComposer">افزودن تسک</button>
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
            <span>{{ minutesLabel(task.estimatedMinutes) }}</span>
            <span v-if="task.todayPlannedMinutes">امروز {{ minutesLabel(task.todayPlannedMinutes) }}</span>
            <span v-if="task.spillover" class="spill-badge">ادامه فردا</span>
            <span v-if="task.dueAt">ددلاین دارد</span>
          </div>

          <div class="task-card-footer">
            <div class="assignee-mini" v-if="task.assignee">
              <UserAvatar :name="task.assignee.name" :avatar-url="task.assignee.avatarUrl" size="sm" />
              <small>{{ task.assignee.name }}</small>
            </div>
            <div class="task-card-actions" @click.stop>
              <button v-if="task.canAccept" class="action-btn tone-primary" type="button" @click="acceptTask(task.id)">پذیرش</button>
              <button v-if="task.canReject" class="action-btn tone-soft" type="button" @click="rejectTask(task.id, 'رد ارجاع')">رد</button>
              <button v-if="task.canStart && task.status !== 'in_progress'" class="action-btn tone-primary" type="button" @click="startTask(task.id, true)">شروع</button>
              <button v-if="task.canPause" class="action-btn tone-soft" type="button" @click="pauseTask(task.id)">توقف</button>
              <button v-if="task.canComplete" class="action-btn tone-soft" type="button" @click="submitTaskReview(task.id)">پایان</button>
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
      @changed="loadTaskingDashboard(true)"
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
  transition: width 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}
.capacity-track .is-planned { background: linear-gradient(90deg, #34908b, #5bb8b2); }
.capacity-track .is-actual { background: linear-gradient(90deg, #0f766e, #14b8a6); }
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
