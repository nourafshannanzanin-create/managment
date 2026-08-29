<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AttendancePunchModal from '../components/AttendancePunchModal.vue'
import NotificationsBell from '../components/NotificationsBell.vue'
import PageHeader from '../components/PageHeader.vue'
import ProfileAvatarEditor from '../components/ProfileAvatarEditor.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatMoneyWithUnit } from '../utils/amount'
import { isPendingWorkflowItem } from '../utils/status'
import { notifyError, notifyInfo } from '../utils/notify'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const router = useRouter()

const {
  state,
  openApprovalDetail,
  openExpenseDetail,
  openRequestDetail,
  chatUnreadCount,
  loadChatUnreadConversations,
  loadTaskingDashboard,
  taskingBadgeCount,
  uploadOwnAvatar,
  clearOwnAvatar,
} = useWorkflowHub()

const todayHoursLabel = ref('—')
const attendancePunchOpen = ref(false)
const avatarBusy = ref(false)
const currentRole = computed(() => String(state.currentUser.accessRole || ''))
const isManagerDashboard = computed(() => ['admin', 'executive_manager', 'manager'].includes(currentRole.value))
const currentUserName = computed(() => String(state.currentUser.name || '').trim())
const currentUserBonus = computed(() => formatMoneyWithUnit(state.currentUser.bonusAmount))
const currentUserPenalty = computed(() => formatMoneyWithUnit(state.currentUser.penaltyAmount))
const attendanceToken = computed(() =>
  String(state.currentUser.attendanceToken || state.currentUser.attendance_token || '').trim(),
)
const canPunchAttendance = computed(() =>
  Boolean(
    !state.currentUser.isHq &&
    attendanceToken.value &&
    state.currentUser.menuAccess?.attendance === true,
  ),
)

const ownRequests = computed(() =>
  (state.requests || []).filter((item) => String(item.owner || '').trim() === currentUserName.value),
)

const ownExpenses = computed(() =>
  (state.expenses || []).filter((item) => String(item.owner || '').trim() === currentUserName.value),
)

const pendingRequests = computed(() =>
  (state.requests || []).filter((item) => isPendingWorkflowItem(item, 'request')),
)

const pendingExpenses = computed(() =>
  (state.expenses || []).filter((item) => isPendingWorkflowItem(item, 'expense')),
)

const inboxApprovals = computed(() =>
  (state.approvals || []).filter((item) => isPendingWorkflowItem(item, 'approval')),
)

const openTicketsCount = computed(() =>
  (state.support.tickets || []).filter((item) => ['open', 'pending', 'answered'].includes(String(item.status || ''))).length,
)

function isHighPriority(item) {
  const raw = String(item.priority || item.priorityLabel || item.risk || '').toLowerCase()
  return (
    raw.includes('high') ||
    raw.includes('critical') ||
    raw.includes('بالا') ||
    raw.includes('بحرانی') ||
    raw.includes('urgent')
  )
}

const importantDocs = computed(() => {
  const rows = []
  ;(state.requests || []).forEach((item) => {
    if (!isHighPriority(item)) return
    rows.push({
      key: `req-${item.id}`,
      kind: 'درخواست',
      title: item.title,
      status: item.status,
      action: () => openRequestDetail(item.id),
    })
  })
  ;(state.expenses || []).forEach((item) => {
    if (!isHighPriority(item) && !String(item.category || '').includes('اضطر')) return
    if (!isHighPriority(item)) return
    rows.push({
      key: `exp-${item.id}`,
      kind: 'هزینه',
      title: item.title,
      status: item.status,
      action: () => openExpenseDetail(item.id),
    })
  })
  ;(state.approvals || []).forEach((item) => {
    if (!isHighPriority(item)) return
    rows.push({
      key: `apr-${item.id}`,
      kind: 'تاییدیه',
      title: item.title,
      status: item.status,
      action: () => openApprovalDetail(item.id),
    })
  })
  return rows.slice(0, 8)
})

const pageTitle = computed(() => (isManagerDashboard.value ? 'داشبورد مدیریتی' : 'داشبورد کاری'))

const quickFocus = computed(() => {
  if (isManagerDashboard.value) {
    return [
      { label: 'صف تایید', value: inboxApprovals.value.length, icon: 'gavel' },
      { label: 'هزینه‌های باز', value: pendingExpenses.value.length, icon: 'account_balance_wallet' },
      { label: 'فرم‌های فعال', value: pendingRequests.value.length, icon: 'folder_managed' },
    ]
  }
  return [
    { label: 'ساعت امروز', value: todayHoursLabel.value, icon: 'schedule' },
    { label: 'پاداش', value: currentUserBonus.value, icon: 'award_star' },
    { label: 'جریمه', value: currentUserPenalty.value, icon: 'gavel' },
  ]
})

const operationalSnapshot = computed(() => {
  if (isManagerDashboard.value) {
    return [
      { label: 'کاربران فعال', value: state.users.length, icon: 'groups' },
      { label: 'واحدها', value: state.directories.departments.length, icon: 'apartment' },
      { label: 'گزارش‌ها', value: state.reports.length, icon: 'monitoring' },
      { label: 'فعالیت‌ها', value: state.activities.length, icon: 'bolt' },
    ]
  }
  return [
    { label: 'تیکت باز', value: openTicketsCount.value, icon: 'support_agent' },
    { label: 'گفتگوی جدید', value: chatUnreadCount.value || 0, icon: 'forum' },
    { label: 'اسناد مهم', value: importantDocs.value.length, icon: 'priority_high' },
    { label: 'اقدام باز', value: inboxApprovals.value.length, icon: 'task' },
  ]
})

const highlightedStats = computed(() => {
  const monthlyExpense = state.stats.find((item) => item.id === 'monthly')?.value || state.expenseSummary[2]?.value || '0'

  if (isManagerDashboard.value) {
    return [
      {
        id: 'monthly-expense',
        label: 'هزینه ماه جاری',
        value: monthlyExpense,
        icon: 'payments',
        tone: 'is-expense',
      },
      {
        id: 'active-requests',
        label: 'درخواست‌های فعال',
        value: pendingRequests.value.length,
        icon: 'assignment',
        tone: 'is-request',
      },
      {
        id: 'pending-approvals',
        label: 'در انتظار تایید',
        value: inboxApprovals.value.length,
        icon: 'pending_actions',
        tone: 'is-approval',
      },
      {
        id: 'pending-expenses',
        label: 'هزینه‌های باز',
        value: pendingExpenses.value.length,
        icon: 'receipt_long',
        tone: 'is-success',
      },
    ]
  }

  return [
    {
      id: 'today-hours',
      label: 'ساعت حضور امروز',
      value: todayHoursLabel.value,
      icon: 'schedule',
      tone: 'is-request',
    },
    {
      id: 'my-bonus',
      label: 'پاداش',
      value: currentUserBonus.value,
      icon: 'award_star',
      tone: 'is-success',
    },
    {
      id: 'my-penalty',
      label: 'جریمه',
      value: currentUserPenalty.value,
      icon: 'gavel',
      tone: 'is-approval',
    },
    {
      id: 'open-tickets',
      label: 'تیکت باز',
      value: openTicketsCount.value,
      icon: 'support_agent',
      tone: 'is-expense',
    },
  ]
})

const recentPendingRequests = computed(() =>
  [...pendingRequests.value]
    .sort((a, b) => String(b.createdAtIso || '').localeCompare(String(a.createdAtIso || '')))
    .slice(0, 4),
)

const pendingExpenseHighlights = computed(() => pendingExpenses.value.slice(0, 3))

const operationalAlerts = computed(() => state.operationalAlerts || [])

const actionCards = computed(() => {
  if (!isManagerDashboard.value && importantDocs.value.length) {
    return importantDocs.value.map((item) => ({
      key: item.key,
      kind: 'important',
      tone: 'is-approval',
      title: item.title,
      actionLabel: 'مشاهده',
      action: item.action,
    }))
  }

  const cards = []
  inboxApprovals.value.forEach((item) => {
    cards.push({
      key: `approval-${item.id}`,
      kind: 'approval',
      tone: 'is-approval',
      title: item.title,
      actionLabel: 'مشاهده',
      action: () => openApprovalDetail(item.id),
    })
  })
  recentPendingRequests.value.forEach((item) => {
    cards.push({
      key: `request-${item.id}`,
      kind: 'request',
      tone: 'is-request',
      title: item.title,
      actionLabel: 'مشاهده',
      action: () => openRequestDetail(item.id),
    })
  })
  pendingExpenseHighlights.value.forEach((item) => {
    cards.push({
      key: `expense-${item.id}`,
      kind: 'expense',
      tone: 'is-expense',
      title: item.title,
      actionLabel: 'مشاهده',
      action: () => openExpenseDetail(item.id),
    })
  })
  return cards.slice(0, isManagerDashboard.value ? 10 : 8)
})

function computeWorkedHours(events) {
  const sorted = [...(events || [])].sort(
    (a, b) => new Date(a.eventAt || a.event_at || 0) - new Date(b.eventAt || b.event_at || 0),
  )
  let totalMs = 0
  let openIn = null
  sorted.forEach((event) => {
    const type = event.eventType || event.event_type
    const at = new Date(event.eventAt || event.event_at || 0)
    if (Number.isNaN(at.getTime())) return
    if (type === 'in') openIn = at
    if (type === 'out' && openIn) {
      totalMs += Math.max(0, at - openIn)
      openIn = null
    }
  })
  if (openIn) totalMs += Math.max(0, Date.now() - openIn)
  const hours = totalMs / 3600000
  return hours ? hours.toFixed(1) : '0'
}

async function loadTodayAttendanceHours() {
  const token = String(state.currentUser.attendanceToken || state.currentUser.attendance_token || '').trim()
  if (!token || isManagerDashboard.value) return
  try {
    const response = await fetch(`${API_BASE_URL}/attendance/public/${encodeURIComponent(token)}`)
    if (!response.ok) return
    const payload = await response.json()
    const events = payload.events || payload.todayEvents || payload.recentEvents || []
    todayHoursLabel.value = computeWorkedHours(events)
  } catch {
    todayHoursLabel.value = '—'
  }
}

onMounted(() => {
  void loadTodayAttendanceHours()
  void loadChatUnreadConversations()
  void loadTaskingDashboard(false).catch(() => {})
})

const taskingSnapshot = computed(() => {
  const stats = state.tasking?.stats || {}
  const capacity = state.tasking?.capacity || {}
  const effective = Number(capacity.effectiveWorkMinutes || 0)
  const actual = Number(capacity.actualMinutes || 0)
  const donePct = effective > 0 ? Math.min(100, Math.round((actual / effective) * 100)) : (actual > 0 ? 100 : 0)
  return [
    { label: 'کارهای امروز', value: stats.todayCount || 0, icon: 'assignment' },
    { label: 'نیازمند اقدام', value: stats.needsAction || taskingBadgeCount.value || 0, icon: 'pending_actions' },
    { label: 'منشن‌ها', value: stats.unreadMentions || 0, icon: 'forum' },
    { label: 'انجام‌شده', value: `${donePct}٪`, icon: 'verified' },
  ]
})

async function onOwnAvatarSelect(file) {
  if (!file || avatarBusy.value) return
  avatarBusy.value = true
  try {
    await uploadOwnAvatar(file)
    notifyInfo('عکس پروفایل به‌روز شد.')
  } catch (error) {
    notifyError(error?.message || 'آپلود عکس پروفایل ناموفق بود.')
  } finally {
    avatarBusy.value = false
  }
}

async function onOwnAvatarClear() {
  if (avatarBusy.value) return
  avatarBusy.value = true
  try {
    await clearOwnAvatar()
    notifyInfo('عکس پروفایل حذف شد.')
  } catch (error) {
    notifyError(error?.message || 'حذف عکس پروفایل ناموفق بود.')
  } finally {
    avatarBusy.value = false
  }
}
</script>

<template>
  <section class="page-shell enterprise-page dashboard-page-premium">
    <PageHeader
      eyebrow="مرکز عملیات"
      :title="pageTitle"
      description=""
    >
      <template #actions>
        <NotificationsBell />
        <button
          v-if="canPunchAttendance"
          class="icon-btn topbar-icon-action tone-primary is-icon-only is-punch-action attendance-punch-topbar-btn dashboard-punch-btn"
          type="button"
          aria-label="ورود و خروج"
          title="ورود و خروج"
          @click="attendancePunchOpen = true"
        >
          <IconlyIcon name="fingerprint" size="xl" decorative />
        </button>
      </template>
    </PageHeader>

    <AttendancePunchModal
      :open="attendancePunchOpen"
      :token="attendanceToken"
      @close="attendancePunchOpen = false"
    />

    <section class="dashboard-stage-grid">
      <article class="dashboard-stage-panel">
        <div class="dashboard-profile-row">
          <ProfileAvatarEditor
            :name="currentUserName"
            :avatar="state.currentUser.avatar"
            :avatar-url="state.currentUser.avatarUrl"
            :avatar-file-name="state.currentUser.avatarFileName"
            size="lg"
            :busy="avatarBusy"
            title=""
            description=""
            add-label="افزودن عکس"
            change-label="تغییر عکس"
            @select="onOwnAvatarSelect"
            @clear="onOwnAvatarClear"
          />
        </div>

        <div class="dashboard-focus-ribbon">
          <article v-for="item in quickFocus" :key="item.label" class="dashboard-focus-chip">
            <IconlyIcon :name="item.icon" decorative />
            <div>
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </article>
        </div>

        <div class="dashboard-stage-summary">
          <article
            v-for="item in operationalSnapshot"
            :key="item.label"
            class="dashboard-summary-card"
            :role="!isManagerDashboard && (item.label === 'گفتگوی جدید' || item.label === 'تیکت باز') ? 'button' : undefined"
            @click="
              !isManagerDashboard && item.label === 'گفتگوی جدید'
                ? router.push('/chat')
                : !isManagerDashboard && item.label === 'تیکت باز'
                  ? router.push('/support')
                  : undefined
            "
          >
            <div class="dashboard-summary-icon">
              <IconlyIcon :name="item.icon" decorative />
            </div>
            <div class="dashboard-summary-copy">
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </article>
        </div>
      </article>

      <article class="dashboard-metrics-panel">
        <div class="dashboard-section-head">
          <h3>{{ isManagerDashboard ? 'شاخص‌های کلیدی' : 'وضعیت امروز' }}</h3>
        </div>
        <div class="dashboard-metrics-grid">
          <article
            v-for="item in highlightedStats"
            :key="item.id"
            :class="['dashboard-metric-card', item.tone]"
          >
            <div class="dashboard-metric-topline">
              <IconlyIcon :name="item.icon" class="dashboard-metric-icon" decorative />
            </div>
            <div class="dashboard-metric-main">
              <span class="dashboard-metric-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </article>
        </div>
      </article>
    </section>

    <section v-if="isManagerDashboard && operationalAlerts.length" class="dashboard-actions-shell">
      <article class="surface-block dashboard-alerts-panel">
        <div class="dashboard-section-head dashboard-section-head-tight">
          <div>
            <h3>رویدادهای خودکار تیم</h3>
            <p class="dashboard-alerts-lead">خروج یا توقف تسک ثبت‌نشده — برای اصلاح داده‌ها به تنظیمات بروید.</p>
          </div>
          <button class="action-btn tone-soft" type="button" @click="router.push('/settings')">
            <IconlyIcon name="settings" decorative />
            <span>تنظیمات</span>
          </button>
        </div>
        <div class="dashboard-alerts-list">
          <article v-for="item in operationalAlerts" :key="item.id" class="dashboard-alert-row">
            <div class="dashboard-alert-icon">
              <IconlyIcon :name="item.icon || 'logout'" decorative />
            </div>
            <div class="dashboard-alert-copy">
              <strong>{{ item.userName }}</strong>
              <p>{{ item.summary }}</p>
              <small>{{ item.time }}</small>
            </div>
          </article>
        </div>
      </article>
    </section>

    <section class="dashboard-actions-shell">
      <article class="surface-block dashboard-actions-panel">
        <div class="dashboard-section-head dashboard-section-head-tight">
          <h3>{{ isManagerDashboard ? 'موارد قابل اقدام' : 'اولویت بالا' }}</h3>
        </div>
        <div v-if="actionCards.length" class="dashboard-queue-grid">
          <article v-for="item in actionCards" :key="item.key" :class="['dashboard-action-card', item.tone]">
            <div class="dashboard-action-copy">
              <strong>{{ item.title }}</strong>
            </div>
            <button class="dashboard-action-button" type="button" @click="item.action()">
              {{ item.actionLabel }}
            </button>
          </article>
        </div>
        <div v-else class="empty-state-inline">مورد مهمی برای نمایش نیست.</div>
      </article>
    </section>

    <section class="dashboard-actions-shell">
      <article class="surface-block dashboard-actions-panel">
        <div class="dashboard-section-head dashboard-section-head-tight">
          <h3>تسکینگ</h3>
          <button class="action-btn tone-primary" type="button" @click="router.push('/tasking')">
            <IconlyIcon name="task_alt" decorative />
            <span>رفتن به تسکینگ</span>
          </button>
        </div>
        <div class="dashboard-stage-summary">
          <article
            v-for="item in taskingSnapshot"
            :key="item.label"
            class="dashboard-summary-card"
            role="button"
            @click="router.push('/tasking')"
          >
            <div class="dashboard-summary-icon">
              <IconlyIcon :name="item.icon" decorative />
            </div>
            <div class="dashboard-summary-copy">
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page-premium {
  --dashboard-navy: #2f3a55;
  --dashboard-ink: #2f3a55;
  --dashboard-muted: #5c6780;
  --dashboard-line: rgba(47, 58, 85, 0.14);
  --dashboard-shadow: none;
  position: relative;
  display: grid;
  gap: 28px;
}

.dashboard-page-premium::before {
  content: none;
}

.dashboard-page-premium > * {
  position: relative;
  z-index: 1;
}

.dashboard-alerts-panel {
  display: grid;
  gap: 14px;
}

.dashboard-alerts-lead {
  margin: 6px 0 0;
  color: #5c6780;
  font-size: 0.82rem;
}

.dashboard-alerts-list {
  display: grid;
  gap: 10px;
}

.dashboard-alert-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(52, 144, 139, 0.14);
}

.dashboard-alert-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
}

.dashboard-alert-copy strong {
  display: block;
  color: #152523;
  font-size: 0.92rem;
}

.dashboard-alert-copy p {
  margin: 4px 0 0;
  color: #45605c;
  font-size: 0.82rem;
  line-height: 1.6;
}

.dashboard-alert-copy small {
  display: block;
  margin-top: 6px;
  color: #7a8a9a;
  font-size: 0.75rem;
}

:deep(.page-header) {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 18px;
  padding: 0 0 8px;
  border-radius: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

:deep(.page-header-copy) {
  gap: 8px;
}

:deep(.page-eyebrow) {
  width: fit-content;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(66, 105, 178, 0.1);
  color: #385d9e;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.07em;
}

:deep(.page-header h1) {
  font-size: clamp(20px, 2vw, 28px);
  line-height: 1.1;
  color: var(--dashboard-navy);
  white-space: nowrap;
}

:deep(.page-header-title-row) {
  flex-wrap: nowrap;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

:deep(.page-header-title-row h1) {
  flex: 0 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-stage-title-row,
.dashboard-section-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.dashboard-stage-title-row h2,
.dashboard-section-title-row h3 {
  margin: 0;
  min-width: 0;
}

:deep(.page-header-description) {
  max-width: 64ch;
  font-size: 11px;
  line-height: 1.8;
  color: var(--dashboard-muted);
}

:deep(.page-header .action-btn) {
  min-height: 48px;
  padding: 0 18px;
  border-radius: 16px;
  background: var(--surface, #fff);
  color: #fff;
  box-shadow: none;
}

.dashboard-stage-grid,
.dashboard-actions-shell {
  display: grid;
  gap: 16px;
}

.dashboard-stage-grid {
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.88fr);
  background: transparent !important;
  background-image: none !important;
  border: 0 !important;
  box-shadow: none !important;
}

.dashboard-stage-grid > .dashboard-stage-panel,
.dashboard-stage-grid > .dashboard-metrics-panel {
  background: transparent !important;
  background-image: none !important;
  border: 0 !important;
  box-shadow: none !important;
}

.dashboard-stage-panel,
.dashboard-metrics-panel,
.dashboard-actions-panel,
.dashboard-summary-card,
.dashboard-focus-chip,
.dashboard-metric-card,
.dashboard-action-card {
  position: relative;
  overflow: visible;
  border: 0;
  box-shadow: none;
  background: transparent;
}

.dashboard-stage-panel,
.dashboard-metrics-panel,
.dashboard-actions-panel {
  border-radius: 0;
  padding: 24px;
}

.dashboard-stage-panel {
  padding: 24px;
  display: grid;
  gap: 14px;
}

.dashboard-stage-panel::after {
  content: none;
}

.dashboard-stage-copy {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 8px;
}

.dashboard-profile-row {
  position: relative;
  z-index: 1;
  margin-bottom: 2px;
}

.dashboard-profile-row :deep(.profile-avatar-editor) {
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  background: rgba(255, 255, 255, 0.72);
}

.dashboard-stage-badge,
.dashboard-section-kicker,
.dashboard-metric-accent,
.dashboard-action-type {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.dashboard-stage-badge {
  color: #335ea5;
  background: rgba(73, 114, 190, 0.12);
}

.dashboard-stage-copy h2 {
  margin: 0;
  max-width: 24ch;
  font-size: clamp(19px, 1.9vw, 26px);
  line-height: 1.35;
  color: var(--dashboard-navy);
}

.dashboard-stage-copy h2.is-single-line {
  max-width: none;
  white-space: nowrap;
  font-size: clamp(17px, 1.45vw, 22px);
}

.dashboard-stage-copy p {
  margin: 0;
  max-width: 58ch;
  font-size: 11px;
  line-height: 1.8;
  color: var(--dashboard-muted);
}

.dashboard-focus-ribbon {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.dashboard-focus-chip {
  min-width: 0;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 4px 14px rgba(31, 92, 89, 0.05);
}

.dashboard-focus-chip .iconly-shell,
.dashboard-summary-icon,
.dashboard-metric-icon {
  display: grid;
  place-items: center;
}

.dashboard-focus-chip .iconly-shell {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: rgba(73, 114, 190, 0.1);
  color: #31589c;
  font-size: 12px;
}

.dashboard-focus-chip strong,
.dashboard-focus-chip span,
.dashboard-summary-copy strong,
.dashboard-summary-copy span,
.dashboard-summary-copy small {
  display: block;
}

.dashboard-focus-chip strong {
  font-size: 0.95rem;
  color: var(--dashboard-navy);
  line-height: 1.15;
  overflow-wrap: anywhere;
}

.dashboard-focus-chip span:last-child {
  margin-top: 5px;
  font-size: 10px;
  color: var(--dashboard-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-stage-summary {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.dashboard-summary-card {
  min-width: 0;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 4px 14px rgba(31, 92, 89, 0.05);
}

.dashboard-summary-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(52, 144, 139, 0.08);
  color: #27467f;
}

.dashboard-summary-icon :deep(.iconly-shell) {
  font-size: 12px;
}

.dashboard-summary-copy strong {
  font-size: 1.05rem;
  line-height: 1.15;
  color: var(--dashboard-navy);
  overflow-wrap: anywhere;
}

.dashboard-summary-copy span {
  margin-top: 3px;
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--dashboard-ink);
}

.dashboard-summary-copy small {
  margin-top: 2px;
  font-size: 0.64rem;
  line-height: 1.4;
  color: var(--dashboard-muted);
}

.dashboard-metrics-panel,
.dashboard-actions-panel {
  padding: 20px;
  background: var(--surface, #fff);
}

.dashboard-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.dashboard-section-head-tight {
  align-items: end;
}

.dashboard-section-head h3 {
  margin: 0;
  font-size: 15px;
  color: var(--dashboard-navy);
}

.dashboard-section-kicker {
  color: #8d5d1e;
  background: rgba(230, 174, 98, 0.16);
}

.dashboard-metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.dashboard-metric-card {
  min-height: 108px;
  padding: 14px;
  border-radius: 14px;
  display: grid;
  gap: 12px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 4px 14px rgba(31, 92, 89, 0.05);
}

.dashboard-metric-topline {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.dashboard-metric-accent {
  color: #425a88;
  background: rgba(67, 98, 159, 0.1);
}

.dashboard-metric-icon {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: rgba(70, 110, 186, 0.1);
  color: #375d9f;
  font-size: 12px;
}

.dashboard-punch-btn {
  position: relative;
  width: 56px !important;
  height: 56px !important;
  min-width: 56px !important;
  min-height: 56px !important;
  border-radius: 50% !important;
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, 0.35), transparent 42%),
    linear-gradient(145deg, #2bb89a 0%, #1f8a70 48%, #176f5a 100%) !important;
  color: #fff !important;
  box-shadow: none !important;
  border: 0 !important;
  overflow: visible !important;
  transition: transform 0.2s ease, filter 0.2s ease !important;
}

.dashboard-punch-btn::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1.5px solid rgba(43, 184, 154, 0.45);
  box-shadow: none;
  pointer-events: none;
  animation: punch-ring-breathe 2.8s ease-in-out infinite;
}

.dashboard-punch-btn:hover {
  transform: translateY(-1px) scale(1.03);
  filter: brightness(1.04);
  box-shadow: none !important;
}

.dashboard-punch-btn:active {
  transform: translateY(0) scale(0.97);
}

.page-header-tools :deep(.notifications-bell-btn) {
  width: 48px !important;
  height: 48px !important;
  min-width: 48px !important;
  min-height: 48px !important;
}

.dashboard-punch-btn :deep(.iconly-shell) {
  position: relative;
  z-index: 1;
  font-size: 28px !important;
  color: #fff !important;
  --iconly-filter: brightness(0) invert(1) !important;
  filter: drop-shadow(0 2px 4px rgba(15, 70, 58, 0.25));
}

.dashboard-punch-btn :deep(.iconly-img) {
  filter: brightness(0) invert(1) !important;
}

@keyframes punch-ring-breathe {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.04); }
}

.dashboard-metric-main {
  display: grid;
  gap: 8px;
}

.dashboard-metric-label {
  font-size: 11px;
  font-weight: 800;
  color: var(--dashboard-ink);
}

.dashboard-metric-card strong {
  font-size: clamp(1rem, 1.4vw, 1.35rem);
  line-height: 1.15;
  color: var(--dashboard-navy);
  overflow-wrap: anywhere;
}

.dashboard-metric-card small {
  font-size: 10px;
  color: var(--dashboard-muted);
  line-height: 1.6;
}

.dashboard-metric-card.is-expense {
  border-color: rgba(217, 119, 6, 0.24);
  background: linear-gradient(155deg, rgba(255, 251, 235, 0.98), rgba(254, 243, 199, 0.94));
  box-shadow: 0 6px 18px rgba(217, 119, 6, 0.1);
}

.dashboard-metric-card.is-expense .dashboard-metric-accent {
  color: #b45309;
  background: rgba(245, 158, 11, 0.18);
}

.dashboard-metric-card.is-expense .dashboard-metric-icon {
  background: rgba(245, 158, 11, 0.2);
  color: #d97706;
}

.dashboard-metric-card.is-expense strong {
  color: #92400e;
}

.dashboard-metric-card.is-request {
  border-color: rgba(37, 99, 235, 0.22);
  background: linear-gradient(155deg, rgba(239, 246, 255, 0.98), rgba(219, 234, 254, 0.94));
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.1);
}

.dashboard-metric-card.is-request .dashboard-metric-accent {
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.16);
}

.dashboard-metric-card.is-request .dashboard-metric-icon {
  background: rgba(59, 130, 246, 0.18);
  color: #2563eb;
}

.dashboard-metric-card.is-request strong {
  color: #1e3a8a;
}

.dashboard-metric-card.is-approval {
  border-color: rgba(124, 58, 237, 0.22);
  background: linear-gradient(155deg, rgba(245, 243, 255, 0.98), rgba(237, 233, 254, 0.94));
  box-shadow: 0 6px 18px rgba(124, 58, 237, 0.1);
}

.dashboard-metric-card.is-approval .dashboard-metric-accent {
  color: #6d28d9;
  background: rgba(139, 92, 246, 0.16);
}

.dashboard-metric-card.is-approval .dashboard-metric-icon {
  background: rgba(139, 92, 246, 0.18);
  color: #7c3aed;
}

.dashboard-metric-card.is-approval strong {
  color: #5b21b6;
}

.dashboard-metric-card.is-success {
  border-color: rgba(22, 163, 74, 0.22);
  background: linear-gradient(155deg, rgba(240, 253, 244, 0.98), rgba(220, 252, 231, 0.94));
  box-shadow: 0 6px 18px rgba(22, 163, 74, 0.1);
}

.dashboard-metric-card.is-success .dashboard-metric-accent {
  color: #15803d;
  background: rgba(34, 197, 94, 0.16);
}

.dashboard-metric-card.is-success .dashboard-metric-icon {
  background: rgba(34, 197, 94, 0.18);
  color: #16a34a;
}

.dashboard-metric-card.is-success strong {
  color: #166534;
}

.dashboard-queue-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.dashboard-action-card {
  min-width: 0;
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 4px 14px rgba(31, 92, 89, 0.05);
}

.dashboard-action-card.is-approval {
  background: var(--surface, #fff);
}

.dashboard-action-card.is-request {
  background: var(--surface, #fff);
}

.dashboard-action-card.is-expense {
  background: var(--surface, #fff);
}

.dashboard-action-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.dashboard-action-type {
  color: #46629c;
  background: rgba(70, 98, 156, 0.1);
}

.dashboard-action-copy strong,
.dashboard-action-copy small {
  display: block;
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.dashboard-action-copy strong {
  color: var(--dashboard-navy);
  font-size: 14px;
  line-height: 1.8;
}

.dashboard-action-copy small {
  margin-top: 4px;
  font-size: 11px;
  color: var(--dashboard-muted);
  line-height: 1.7;
}

.dashboard-action-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  min-width: 0;
}

.dashboard-action-meta span {
  max-width: 100%;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(64, 93, 148, 0.08);
  color: #5f6f8c;
  font-size: 11px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.dashboard-action-button {
  width: 100%;
  border: 0;
  border-radius: 16px;
  padding: 11px 12px;
  background: var(--surface, #fff);
  color: #fff;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: none;
}

@media (min-width: 1241px) {
  .dashboard-queue-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (min-width: 1560px) {
  .dashboard-queue-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }
}

@media (max-width: 1240px) {
  .dashboard-stage-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  :deep(.page-header) {
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
  }

  .dashboard-stage-summary,
  .dashboard-metrics-grid,
  .dashboard-queue-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .dashboard-focus-ribbon {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }
}

@media (max-width: 640px) {
  .dashboard-page-premium {
    gap: 14px;
  }

  :deep(.page-header) {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 10px !important;
    padding: 4px 0 8px !important;
    border-radius: 0 !important;
    grid-template-columns: unset !important;
  }

  :deep(.page-header-copy) {
    min-width: 0;
    flex: 1 1 auto;
  }

  :deep(.page-header-description) {
    display: none;
  }

  :deep(.page-header-title-row) {
    flex-wrap: nowrap !important;
  }

  :deep(.page-header h1) {
    font-size: 1.05rem !important;
    white-space: nowrap !important;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  :deep(.page-header-tools) {
    width: auto !important;
    display: flex !important;
    flex: 0 0 auto !important;
    grid-template-columns: unset !important;
    gap: 8px !important;
    margin-inline-start: 0 !important;
  }

  .dashboard-punch-btn {
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    min-height: 48px !important;
  }

  .dashboard-punch-btn :deep(.iconly-shell) {
    font-size: 24px !important;
  }

  .dashboard-stage-panel,
  .dashboard-metrics-panel,
  .dashboard-actions-panel {
    padding: 14px 12px;
    border-radius: 16px;
  }

  .dashboard-stage-copy h2,
  .dashboard-stage-copy p {
    max-width: none;
  }

  .dashboard-stage-copy h2.is-single-line {
    white-space: normal;
    font-size: 1.05rem;
    line-height: 1.45;
  }

  .dashboard-focus-ribbon {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
  }

  .dashboard-stage-summary,
  .dashboard-metrics-grid,
  .dashboard-queue-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .dashboard-focus-chip {
    grid-template-columns: 28px minmax(0, 1fr);
    gap: 6px;
    padding: 8px 10px;
  }

  .dashboard-focus-chip .iconly-shell {
    width: 28px;
    height: 28px;
    border-radius: 9px;
    font-size: 13px;
  }

  .dashboard-focus-chip strong {
    font-size: 0.82rem;
    line-height: 1.15;
  }

  .dashboard-focus-chip span:last-child {
    font-size: 0.62rem;
    line-height: 1.3;
  }

  .dashboard-summary-card {
    grid-template-columns: 36px minmax(0, 1fr);
    gap: 8px;
    padding: 10px 12px;
  }

  .dashboard-summary-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
  }

  .dashboard-summary-copy strong {
    font-size: 1rem;
  }

  .dashboard-summary-copy span {
    font-size: 0.72rem;
  }

  .dashboard-summary-copy small {
    font-size: 0.64rem;
  }

  .dashboard-metric-card {
    min-height: 0;
    padding: 12px;
  }

  .dashboard-metric-card strong {
    font-size: 1.1rem;
  }

  .dashboard-section-head {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .dashboard-section-head .action-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 420px) {
  .dashboard-focus-ribbon {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-stage-summary,
  .dashboard-metrics-grid,
  .dashboard-queue-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.dashboard-stage-badge,
.dashboard-section-kicker,
.dashboard-metric-accent,
.dashboard-action-type,
.dashboard-focus-chip span:last-child,
.dashboard-stage-copy p,
.dashboard-summary-copy span,
.dashboard-summary-copy small,
.dashboard-metric-label,
.dashboard-metric-card small,
.dashboard-action-copy small,
.dashboard-action-meta span,
:deep(.page-eyebrow),
:deep(.page-header-description) {
  font-size: 12px;
}

.dashboard-stage-panel,
.dashboard-metrics-panel,
.dashboard-actions-panel,
:deep(.page-header) {
  border-radius: 20px;
}

/* Unified dashboard cards — always 2-column peer grids on mobile. */
.dashboard-page-premium {
  --dashboard-navy: #2a3348;
  --dashboard-ink: #2a3348;
  --dashboard-muted: #5f6b82;
  --dashboard-line: rgba(45, 55, 85, 0.12);
  --dashboard-shadow: none;
  gap: 20px;
}

.dashboard-page-premium::before,
.dashboard-stage-panel::after {
  content: none;
}

:deep(.page-header) {
  padding: 0 0 8px;
  margin-bottom: 8px;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.dashboard-stage-grid,
.dashboard-actions-shell {
  gap: 16px;
}

.dashboard-stage-panel,
.dashboard-metrics-panel,
.dashboard-actions-panel {
  padding: 16px 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.dashboard-summary-card,
.dashboard-focus-chip,
.dashboard-metric-card,
.dashboard-action-card {
  min-width: 0;
}

.dashboard-summary-copy span,
.dashboard-summary-copy small,
.dashboard-metric-card small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.page-eyebrow),
.dashboard-stage-badge,
.dashboard-section-kicker,
.dashboard-action-type {
  padding: 0;
  color: var(--dashboard-muted);
  background: transparent;
  border: 0;
  font-size: 11px;
  font-weight: 600;
}

.dashboard-metric-card .dashboard-metric-accent {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}

.dashboard-metric-card .dashboard-metric-icon {
  width: 28px;
  height: 28px;
  border-radius: 9px;
  font-size: 13px;
}

:deep(.page-header .action-btn),
.dashboard-action-button {
  background: #4d5d8a;
  border: 1px solid #4d5d8a;
  border-radius: 8px;
  box-shadow: none;
  color: #fff;
}

.dashboard-focus-chip .iconly-shell,
.dashboard-summary-icon {
  background: transparent;
  border: 0;
  color: #4d5d8a;
  border-radius: 0;
}

.dashboard-action-meta span {
  background: transparent;
  border: 0;
  color: #5f6b82;
}

</style>
