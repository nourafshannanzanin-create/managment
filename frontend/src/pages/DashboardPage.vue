<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AttendancePunchModal from '../components/AttendancePunchModal.vue'
import NotificationsBell from '../components/NotificationsBell.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatJalali, getTodayJalali } from '../utils/jalali'
import { joinDisplayParts } from '../utils/text'
import { isPendingWorkflowItem } from '../utils/status'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const router = useRouter()

const {
  state,
  openApprovalDetail,
  openExpenseDetail,
  openRequestDetail,
  chatUnreadCount,
  loadChatUnreadConversations,
} = useWorkflowHub()

const todayHoursLabel = ref('—')
const attendancePunchOpen = ref(false)
const todayLabel = computed(() => formatJalali(getTodayJalali()))
const currentRole = computed(() => String(state.currentUser.accessRole || ''))
const isManagerDashboard = computed(() => ['admin', 'executive_manager', 'manager'].includes(currentRole.value))
const currentUserName = computed(() => String(state.currentUser.name || '').trim())
const currentUserBonus = computed(() => state.currentUser.bonusAmount || '0.00')
const currentUserPenalty = computed(() => state.currentUser.penaltyAmount || '0.00')
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
const pageDescription = computed(() =>
  isManagerDashboard.value
    ? `امروز ${todayLabel.value} است. این نما، وضعیت درخواست‌ها، هزینه‌ها و تاییدها را به صورت خلاصه نشان می‌دهد.`
    : `امروز ${todayLabel.value} است. حضور، پاداش/جریمه و موارد مهم شما اینجاست.`,
)

const heroTitle = computed(() =>
  isManagerDashboard.value ? 'نمای زنده تصمیم‌ها و بار عملیاتی' : 'وضعیت امروز شما',
)

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
      { label: 'کاربران فعال', value: state.users.length, detail: 'ساختار سازمانی', icon: 'groups' },
      { label: 'واحدها', value: state.directories.departments.length, detail: 'بخش‌های ثبت شده', icon: 'apartment' },
      { label: 'گزارش‌ها', value: state.reports.length, detail: 'خروجی آماده', icon: 'monitoring' },
      { label: 'فعالیت‌ها', value: state.activities.length, detail: 'رخداد اخیر', icon: 'bolt' },
    ]
  }
  return [
    { label: 'تیکت باز', value: openTicketsCount.value, detail: 'پشتیبانی', icon: 'support_agent' },
    { label: 'گفتگوی جدید', value: chatUnreadCount.value || 0, detail: 'خوانده‌نشده', icon: 'forum' },
    { label: 'اسناد مهم', value: importantDocs.value.length, detail: 'اولویت بالا', icon: 'priority_high' },
    { label: 'اقدام باز', value: inboxApprovals.value.length, detail: 'نیازمند تصمیم', icon: 'task' },
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
        note: 'جمع ماه',
        icon: 'payments',
        tone: 'is-expense',
        accent: 'مصارف',
      },
      {
        id: 'active-requests',
        label: 'درخواست‌های فعال',
        value: pendingRequests.value.length,
        note: 'در انتظار تایید',
        icon: 'assignment',
        tone: 'is-request',
        accent: 'جریان باز',
      },
      {
        id: 'pending-approvals',
        label: 'در انتظار تایید',
        value: inboxApprovals.value.length,
        note: 'نیازمند تصمیم',
        icon: 'pending_actions',
        tone: 'is-approval',
        accent: 'اقدام فوری',
      },
      {
        id: 'pending-expenses',
        label: 'هزینه‌های باز',
        value: pendingExpenses.value.length,
        note: 'در انتظار تایید',
        icon: 'receipt_long',
        tone: 'is-success',
        accent: 'نیازمند اقدام',
      },
    ]
  }

  return [
    {
      id: 'today-hours',
      label: 'ساعت حضور امروز',
      value: todayHoursLabel.value,
      note: 'بر اساس ورود/خروج',
      icon: 'schedule',
      tone: 'is-request',
      accent: 'حضور',
    },
    {
      id: 'my-bonus',
      label: 'پاداش',
      value: currentUserBonus.value,
      note: 'جمع پاداش',
      icon: 'award_star',
      tone: 'is-success',
      accent: 'پاداش',
    },
    {
      id: 'my-penalty',
      label: 'جریمه',
      value: currentUserPenalty.value,
      note: 'جمع جریمه',
      icon: 'gavel',
      tone: 'is-approval',
      accent: 'جریمه',
    },
    {
      id: 'open-tickets',
      label: 'تیکت باز',
      value: openTicketsCount.value,
      note: 'پشتیبانی',
      icon: 'support_agent',
      tone: 'is-expense',
      accent: 'پشتیبانی',
    },
  ]
})

const recentPendingRequests = computed(() =>
  [...pendingRequests.value]
    .sort((a, b) => String(b.createdAtIso || '').localeCompare(String(a.createdAtIso || '')))
    .slice(0, 4),
)

const pendingExpenseHighlights = computed(() => pendingExpenses.value.slice(0, 3))

const actionCards = computed(() => {
  if (!isManagerDashboard.value && importantDocs.value.length) {
    return importantDocs.value.map((item) => ({
      key: item.key,
      kind: 'important',
      tone: 'is-approval',
      typeLabel: item.kind,
      status: item.status,
      title: item.title,
      subtitle: 'اولویت بالا',
      meta: [item.kind, item.status || '-'],
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
      typeLabel: 'تاییدیه',
      status: item.status,
      title: item.title,
      subtitle: joinDisplayParts([item.owner, item.department]),
      meta: [item.type, item.risk, item.uploadedAt || '-'],
      actionLabel: 'مشاهده و تصمیم',
      action: () => openApprovalDetail(item.id),
    })
  })
  recentPendingRequests.value.forEach((item) => {
    cards.push({
      key: `request-${item.id}`,
      kind: 'request',
      tone: 'is-request',
      typeLabel: 'درخواست',
      status: item.status,
      title: item.title,
      subtitle: joinDisplayParts([item.owner, item.department]),
      meta: [item.priority || '-', item.manager || '-', item.createdAt || item.deadline || '-'],
      actionLabel: 'جزئیات درخواست',
      action: () => openRequestDetail(item.id),
    })
  })
  pendingExpenseHighlights.value.forEach((item) => {
    cards.push({
      key: `expense-${item.id}`,
      kind: 'expense',
      tone: 'is-expense',
      typeLabel: 'هزینه',
      status: item.status,
      title: item.title,
      subtitle: joinDisplayParts([item.owner, item.category]),
      meta: [item.amount, item.department, item.submittedAt || '-'],
      actionLabel: 'بررسی هزینه',
      action: () => openExpenseDetail(item.id),
    })
  })
  return cards.slice(0, isManagerDashboard.value ? 10 : 8)
})

function statusClass(status) {
  const text = String(status || '')
  if (text.includes('رد')) return 'is-danger'
  if (text.includes('تایید')) return 'is-success'
  return 'is-warning'
}

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
})
</script>

<template>
  <section class="page-shell enterprise-page dashboard-page-premium">
    <PageHeader
      eyebrow="مرکز عملیات"
      :title="pageTitle"
      :description="pageDescription"
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
        <div class="dashboard-stage-copy">
          <span class="dashboard-stage-badge">{{ isManagerDashboard ? 'نمای زنده عملیات' : 'نمای کار روزانه' }}</span>
          <h2 :class="{ 'is-single-line': !isManagerDashboard }">{{ heroTitle }}</h2>
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
              <small>{{ item.detail }}</small>
            </div>
          </article>
        </div>
      </article>

      <article class="dashboard-metrics-panel">
        <div class="dashboard-section-head">
          <div>
            <span class="dashboard-section-kicker">مرور سریع</span>
            <h3>{{ isManagerDashboard ? 'شاخص‌های کلیدی امروز' : 'وضعیت شخصی امروز' }}</h3>
          </div>
        </div>
        <div class="dashboard-metrics-grid">
          <article
            v-for="item in highlightedStats"
            :key="item.id"
            :class="['dashboard-metric-card', item.tone]"
          >
            <div class="dashboard-metric-topline">
              <span class="dashboard-metric-accent">{{ item.accent }}</span>
              <IconlyIcon :name="item.icon" class="dashboard-metric-icon" decorative />
            </div>
            <div class="dashboard-metric-main">
              <span class="dashboard-metric-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.note }}</small>
            </div>
          </article>
        </div>
      </article>
    </section>

    <section class="dashboard-actions-shell">
      <article class="surface-block dashboard-actions-panel">
        <div class="dashboard-section-head dashboard-section-head-tight">
          <div>
            <span class="dashboard-section-kicker">{{ isManagerDashboard ? 'اولویت جاری' : 'اسناد مهم' }}</span>
            <h3>{{ isManagerDashboard ? 'موارد قابل اقدام' : 'اولویت بالا برای شما' }}</h3>
          </div>
        </div>
        <div v-if="actionCards.length" class="dashboard-queue-grid">
          <article v-for="item in actionCards" :key="item.key" :class="['dashboard-action-card', item.tone]">
            <div class="dashboard-action-top">
              <span class="dashboard-action-type">{{ item.typeLabel }}</span>
              <span class="status-badge" :class="statusClass(item.status)">{{ item.status }}</span>
            </div>
            <div class="dashboard-action-copy">
              <strong>{{ item.title }}</strong>
              <small>{{ item.subtitle }}</small>
            </div>
            <div class="dashboard-action-meta">
              <span v-for="(meta, idx) in item.meta" :key="idx">{{ meta }}</span>
            </div>
            <button class="dashboard-action-button" type="button" @click="item.action()">
              {{ item.actionLabel }}
            </button>
          </article>
        </div>
        <div v-else class="empty-state-inline">مورد مهمی برای نمایش نیست.</div>
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
  background: transparent;
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
  gap: 10px;
  align-items: center;
  padding: 8px 0;
  border-radius: 0;
  background: transparent;
  backdrop-filter: none;
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
  font-size: 16px;
  color: var(--dashboard-navy);
  line-height: 1;
}

.dashboard-focus-chip span:last-child {
  margin-top: 5px;
  font-size: 10px;
  color: var(--dashboard-muted);
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
  gap: 12px;
  align-items: center;
  padding: 8px 0;
  border-radius: 0;
  background: transparent;
}

.dashboard-summary-icon {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: var(--surface, #fff);
  color: #27467f;
}

.dashboard-summary-icon :deep(.iconly-shell) {
  font-size: 12px;
}

.dashboard-summary-copy strong {
  font-size: 18px;
  line-height: 1;
  color: var(--dashboard-navy);
}

.dashboard-summary-copy span {
  margin-top: 4px;
  font-size: 11px;
  font-weight: 800;
  color: var(--dashboard-ink);
}

.dashboard-summary-copy small {
  margin-top: 3px;
  font-size: 10px;
  line-height: 1.6;
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
  margin: 4px 0 0;
  font-size: 16px;
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
  min-height: 156px;
  padding: 16px;
  border-radius: 12px;
  display: grid;
  gap: 14px;
  background: var(--surface, #fff);
}

.dashboard-metric-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  width: 64px !important;
  height: 64px !important;
  min-width: 64px !important;
  min-height: 64px !important;
  border-radius: 20px !important;
  background: #1f8a70 !important;
  color: #fff !important;
  box-shadow: 0 12px 28px rgba(31, 138, 112, 0.32) !important;
  border: 0 !important;
}

.page-header-tools :deep(.notifications-bell-btn) {
  width: 48px !important;
  height: 48px !important;
  min-width: 48px !important;
  min-height: 48px !important;
}

.dashboard-punch-btn :deep(.iconly-shell) {
  font-size: 34px !important;
  color: #fff !important;
  --iconly-filter: brightness(0) invert(1) !important;
}

.dashboard-punch-btn :deep(.iconly-img) {
  filter: brightness(0) invert(1) !important;
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
  font-size: clamp(20px, 1.7vw, 26px);
  line-height: 1;
  color: var(--dashboard-navy);
}

.dashboard-metric-card small {
  font-size: 10px;
  color: var(--dashboard-muted);
  line-height: 1.6;
}

.dashboard-metric-card.is-expense {
  background: var(--surface, #fff);
}

.dashboard-metric-card.is-request {
  background: var(--surface, #fff);
}

.dashboard-metric-card.is-approval {
  background: var(--surface, #fff);
}

.dashboard-metric-card.is-success {
  background: var(--surface, #fff);
}

.dashboard-queue-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.dashboard-action-card {
  min-width: 0;
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: var(--surface, #fff);
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

@media (max-width: 1360px) {
  .dashboard-queue-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 1240px) {
  .dashboard-stage-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .dashboard-queue-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  :deep(.page-header) {
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
  }

  .dashboard-focus-ribbon {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-stage-summary,
  .dashboard-metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-section-head {
    display: grid;
  }

  .dashboard-queue-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .dashboard-page-premium {
    gap: 14px;
  }

  :deep(.page-header) {
    padding: 16px;
    border-radius: 12px;
  }

  .dashboard-stage-panel,
  .dashboard-metrics-panel,
  .dashboard-actions-panel {
    padding: 16px;
    border-radius: 12px;
  }

  .dashboard-stage-copy h2,
  .dashboard-stage-copy p {
    max-width: none;
  }

  .dashboard-stage-copy h2.is-single-line {
    white-space: normal;
  }

  .dashboard-focus-ribbon {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-stage-summary,
  .dashboard-metrics-grid,
  .dashboard-queue-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

/* Unified continuous dashboard: no boxed panels. */
.dashboard-page-premium {
  --dashboard-navy: #2a3348;
  --dashboard-ink: #2a3348;
  --dashboard-muted: #5f6b82;
  --dashboard-line: rgba(45, 55, 85, 0.12);
  --dashboard-shadow: none;
  gap: 28px;
}

.dashboard-page-premium::before,
.dashboard-stage-panel::after {
  content: none;
}

:deep(.page-header),
.dashboard-stage-panel,
.dashboard-metrics-panel,
.dashboard-actions-panel,
.dashboard-summary-card,
.dashboard-focus-chip,
.dashboard-metric-card,
.dashboard-action-card {
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  backdrop-filter: none;
  padding-left: 0;
  padding-right: 0;
}

:deep(.page-header) {
  padding: 0 0 8px;
  margin-bottom: 12px;
  border: 0;
  border-radius: 0;
}

.dashboard-stage-grid,
.dashboard-actions-shell {
  gap: 28px;
}

.dashboard-stage-panel,
.dashboard-metrics-panel,
.dashboard-actions-panel {
  padding: 24px;
}

:deep(.page-eyebrow),
.dashboard-stage-badge,
.dashboard-section-kicker,
.dashboard-metric-accent,
.dashboard-action-type {
  padding: 0;
  color: var(--dashboard-muted);
  background: transparent;
  border: 0;
  font-size: 11px;
  font-weight: 600;
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
.dashboard-summary-icon,
.dashboard-metric-icon {
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
