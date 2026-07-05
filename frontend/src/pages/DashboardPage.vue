<script setup>
import { computed } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatJalali, getTodayJalali } from '../utils/jalali'

const {
  state,
  openApprovalDetail,
  openExpenseDetail,
  openRequestComposer,
  openRequestDetail,
} = useWorkflowHub()

const todayLabel = computed(() => formatJalali(getTodayJalali()))
const currentRole = computed(() => String(state.currentUser.accessRole || ''))
const isManagerDashboard = computed(() => ['admin', 'executive_manager', 'manager'].includes(currentRole.value))
const currentUserName = computed(() => String(state.currentUser.name || '').trim())

const ownRequests = computed(() =>
  (state.requests || []).filter((item) => String(item.owner || '').trim() === currentUserName.value),
)

const ownExpenses = computed(() =>
  (state.expenses || []).filter((item) => String(item.owner || '').trim() === currentUserName.value),
)

const inboxApprovals = computed(() =>
  [...(state.approvals || [])].filter(
    (item) =>
      item.bucket === 'pending' ||
      String(item.status || '').includes('انتظار') ||
      String(item.status || '').includes('بررسی'),
  ),
)

const pageTitle = computed(() => (isManagerDashboard.value ? 'داشبورد مدیریتی' : 'داشبورد کاری'))
const pageDescription = computed(() =>
  isManagerDashboard.value
    ? `امروز ${todayLabel.value} است. این نما، وضعیت درخواست‌ها، هزینه‌ها و تاییدها را به صورت خلاصه نشان می‌دهد.`
    : `امروز ${todayLabel.value} است. این نما، پرونده‌ها و اقدام‌های مرتبط با حساب شما را خلاصه می‌کند.`,
)

const heroTitle = computed(() =>
  isManagerDashboard.value ? 'نمای زنده تصمیم‌ها و بار عملیاتی' : 'نمای سریع کارهای روزانه و پرونده‌های شما',
)

const heroDescription = computed(() =>
  isManagerDashboard.value
    ? 'مهم‌ترین شاخص‌ها و پرونده‌های قابل اقدام در یک نگاه.'
    : 'درخواست‌ها، هزینه‌ها و موارد قابل پیگیری شما در این صفحه جمع شده‌اند.',
)

const quickFocus = computed(() => {
  if (isManagerDashboard.value) {
    return [
      { label: 'صف تایید', value: state.approvalMetrics.pending || 0, icon: 'gavel' },
      { label: 'هزینه‌های باز', value: state.expenses.length, icon: 'account_balance_wallet' },
      { label: 'فرم‌های فعال', value: state.requests.length, icon: 'folder_managed' },
    ]
  }

  return [
    { label: 'درخواست‌های من', value: ownRequests.value.length, icon: 'assignment' },
    { label: 'هزینه‌های من', value: ownExpenses.value.length, icon: 'receipt_long' },
    { label: 'اقدام‌های من', value: inboxApprovals.value.length, icon: 'task' },
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
    { label: 'درخواست‌های من', value: ownRequests.value.length, detail: 'فرم ثبت شده', icon: 'description' },
    { label: 'هزینه‌های من', value: ownExpenses.value.length, detail: 'ثبت هزینه', icon: 'payments' },
    { label: 'تاییدیه‌ها', value: state.approvals.length, detail: 'اسناد قابل مشاهده', icon: 'fact_check' },
    {
      label: 'گزارش‌ها',
      value: state.currentUser.canViewReports ? state.reports.length : 0,
      detail: state.currentUser.canViewReports ? 'خروجی آماده' : 'بدون دسترسی',
      icon: 'monitoring',
    },
  ]
})

const highlightedStats = computed(() => {
  const monthlyExpense = state.stats.find((item) => item.id === 'monthly')?.value || state.expenseSummary[2]?.value || '0'
  const approvedDocs = state.stats.find((item) => item.id === 'approved')?.value || state.approvalMetrics.approved || 0

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
        value: state.requests.length,
        note: 'در گردش',
        icon: 'assignment',
        tone: 'is-request',
        accent: 'جریان باز',
      },
      {
        id: 'pending-approvals',
        label: 'در انتظار تایید',
        value: state.approvalMetrics.pending || 0,
        note: 'نیازمند تصمیم',
        icon: 'pending_actions',
        tone: 'is-approval',
        accent: 'اقدام فوری',
      },
      {
        id: 'approved-docs',
        label: 'اسناد تاییدشده',
        value: approvedDocs,
        note: 'نهایی شده',
        icon: 'verified',
        tone: 'is-success',
        accent: 'بایگانی',
      },
    ]
  }

  return [
    {
      id: 'my-requests',
      label: 'درخواست‌های من',
      value: ownRequests.value.length,
      note: 'ثبت شده',
      icon: 'assignment',
      tone: 'is-request',
      accent: 'پرونده',
    },
    {
      id: 'my-expenses',
      label: 'هزینه‌های من',
      value: ownExpenses.value.length,
      note: 'ثبت هزینه',
      icon: 'payments',
      tone: 'is-expense',
      accent: 'مصارف',
    },
    {
      id: 'my-approvals',
      label: 'اقدام‌های باز',
      value: inboxApprovals.value.length,
      note: 'در انتظار',
      icon: 'pending_actions',
      tone: 'is-approval',
      accent: 'پیگیری',
    },
    {
      id: 'my-reports',
      label: 'گزارش‌های آماده',
      value: state.currentUser.canViewReports ? state.reports.length : 0,
      note: state.currentUser.canViewReports ? 'قابل دریافت' : 'بدون دسترسی',
      icon: 'verified',
      tone: 'is-success',
      accent: 'خروجی',
    },
  ]
})

const recentRequests = computed(() => {
  const sortable = [...(state.requests || [])]
  return sortable
    .sort((a, b) => String(b.createdAtIso || '').localeCompare(String(a.createdAtIso || '')))
    .slice(0, 4)
})

const expenseHighlights = computed(() => (state.expenses || []).slice(0, 3))

const actionCards = computed(() => {
  const cards = []

  inboxApprovals.value.forEach((item) => {
    cards.push({
      key: `approval-${item.id}`,
      kind: 'approval',
      tone: 'is-approval',
      typeLabel: 'تاییدیه',
      status: item.status,
      title: item.title,
      subtitle: `${item.owner} - ${item.department}`,
      meta: [item.type, item.risk, item.uploadedAt || '-'],
      actionLabel: 'مشاهده و تصمیم',
      action: () => openApprovalDetail(item.id),
    })
  })

  recentRequests.value.forEach((item) => {
    cards.push({
      key: `request-${item.id}`,
      kind: 'request',
      tone: 'is-request',
      typeLabel: 'درخواست',
      status: item.status,
      title: item.title,
      subtitle: `${item.owner} - ${item.department}`,
      meta: [item.priority || '-', item.manager || '-', item.createdAt || item.deadline || '-'],
      actionLabel: 'جزئیات درخواست',
      action: () => openRequestDetail(item.id),
    })
  })

  expenseHighlights.value.forEach((item) => {
    cards.push({
      key: `expense-${item.id}`,
      kind: 'expense',
      tone: 'is-expense',
      typeLabel: 'هزینه',
      status: item.status,
      title: item.title,
      subtitle: `${item.owner} - ${item.category}`,
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
</script>

<template>
  <section class="page-shell enterprise-page dashboard-page-premium">
    <PageHeader
      eyebrow="مرکز عملیات"
      :title="pageTitle"
      :description="pageDescription"
      action-label="ثبت درخواست"
      action-icon="add_circle"
      @action="openRequestComposer"
    />

    <section class="dashboard-stage-grid">
      <article class="dashboard-stage-panel">
        <div class="dashboard-stage-copy">
          <span class="dashboard-stage-badge">{{ isManagerDashboard ? 'نمای زنده عملیات' : 'نمای کار روزانه' }}</span>
          <h2 :class="{ 'is-single-line': !isManagerDashboard }">{{ heroTitle }}</h2>
          <p>{{ heroDescription }}</p>
        </div>

        <div class="dashboard-focus-ribbon">
          <article v-for="item in quickFocus" :key="item.label" class="dashboard-focus-chip">
            <span class="material-symbols-outlined">{{ item.icon }}</span>
            <div>
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </article>
        </div>

        <div class="dashboard-stage-summary">
          <article v-for="item in operationalSnapshot" :key="item.label" class="dashboard-summary-card">
            <div class="dashboard-summary-icon">
              <span class="material-symbols-outlined">{{ item.icon }}</span>
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
            <h3>{{ isManagerDashboard ? 'شاخص‌های کلیدی امروز' : 'مرور سریع حساب شما' }}</h3>
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
              <span class="material-symbols-outlined dashboard-metric-icon">{{ item.icon }}</span>
            </div>
            <div class="dashboard-metric-main">
              <span class="dashboard-metric-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
            <small>{{ item.note }}</small>
          </article>
        </div>
      </article>
    </section>

    <section class="dashboard-actions-shell">
      <article class="surface-block dashboard-actions-panel">
        <div class="dashboard-section-head dashboard-section-head-tight">
          <div>
            <span class="dashboard-section-kicker">اولویت جاری</span>
            <h3>{{ isManagerDashboard ? 'صف اقدام سریع' : 'پرونده‌های قابل پیگیری' }}</h3>
          </div>
        </div>

        <div class="dashboard-queue-grid">
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
              <span v-for="meta in item.meta" :key="meta">{{ meta }}</span>
            </div>
            <button class="dashboard-action-button" type="button" @click="item.action()">
              {{ item.actionLabel }}
            </button>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page-premium {
  --dashboard-navy: #183153;
  --dashboard-ink: #1f3557;
  --dashboard-muted: #66758f;
  --dashboard-line: rgba(32, 58, 105, 0.08);
  --dashboard-shadow: 0 18px 42px rgba(24, 41, 77, 0.1);
  position: relative;
  display: grid;
  gap: 18px;
}

.dashboard-page-premium::before {
  content: '';
  position: absolute;
  inset: -20px -20px auto;
  height: 220px;
  border-radius: 34px;
  background:
    radial-gradient(circle at top right, rgba(70, 115, 201, 0.14), transparent 34%),
    radial-gradient(circle at 18% 15%, rgba(224, 160, 94, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0));
  pointer-events: none;
  z-index: 0;
}

.dashboard-page-premium > * {
  position: relative;
  z-index: 1;
}

:deep(.page-header) {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 18px;
  padding: 22px 24px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(78, 119, 199, 0.12), transparent 30%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(244, 248, 253, 0.95));
  border: 1px solid rgba(34, 58, 102, 0.08);
  box-shadow: 0 18px 44px rgba(25, 46, 86, 0.08);
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
  background: linear-gradient(135deg, #234783, #3763a8);
  color: #fff;
  box-shadow: 0 14px 28px rgba(39, 75, 134, 0.18);
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
  overflow: hidden;
  border: 1px solid var(--dashboard-line);
  box-shadow: var(--dashboard-shadow);
}

.dashboard-stage-panel,
.dashboard-metrics-panel,
.dashboard-actions-panel {
  border-radius: 28px;
}

.dashboard-stage-panel {
  padding: 22px;
  display: grid;
  gap: 14px;
  background:
    radial-gradient(circle at top right, rgba(58, 115, 214, 0.15), transparent 34%),
    radial-gradient(circle at bottom left, rgba(224, 155, 88, 0.12), transparent 32%),
    linear-gradient(140deg, #f8fbff 0%, #eff4fb 45%, #fbfdff 100%);
}

.dashboard-stage-panel::after {
  content: '';
  position: absolute;
  inset: 14px;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.54);
  pointer-events: none;
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
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
}

.dashboard-focus-chip .material-symbols-outlined,
.dashboard-summary-icon,
.dashboard-metric-icon {
  display: grid;
  place-items: center;
}

.dashboard-focus-chip .material-symbols-outlined {
  width: 38px;
  height: 38px;
  border-radius: 13px;
  background: rgba(73, 114, 190, 0.1);
  color: #31589c;
  font-size: 20px;
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
  padding: 16px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 250, 255, 0.88));
}

.dashboard-summary-icon {
  width: 46px;
  height: 46px;
  border-radius: 15px;
  background: linear-gradient(135deg, rgba(73, 114, 190, 0.12), rgba(224, 155, 88, 0.18));
  color: #27467f;
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
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(246, 249, 252, 0.96));
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
  border-radius: 22px;
  display: grid;
  gap: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 250, 255, 0.94));
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
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(70, 110, 186, 0.1);
  color: #375d9f;
  font-size: 20px;
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
  background:
    radial-gradient(circle at top right, rgba(239, 180, 96, 0.14), transparent 32%),
    linear-gradient(180deg, rgba(255, 249, 241, 0.98), rgba(255, 243, 224, 0.95));
}

.dashboard-metric-card.is-request {
  background:
    radial-gradient(circle at top right, rgba(89, 144, 234, 0.16), transparent 32%),
    linear-gradient(180deg, rgba(242, 247, 255, 0.98), rgba(232, 240, 255, 0.95));
}

.dashboard-metric-card.is-approval {
  background:
    radial-gradient(circle at top right, rgba(255, 191, 82, 0.16), transparent 32%),
    linear-gradient(180deg, rgba(255, 249, 235, 0.98), rgba(255, 240, 207, 0.95));
}

.dashboard-metric-card.is-success {
  background:
    radial-gradient(circle at top right, rgba(108, 197, 143, 0.16), transparent 32%),
    linear-gradient(180deg, rgba(240, 251, 245, 0.98), rgba(228, 247, 235, 0.95));
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
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 253, 0.96));
}

.dashboard-action-card.is-approval {
  background:
    radial-gradient(circle at top right, rgba(255, 193, 88, 0.16), transparent 30%),
    linear-gradient(180deg, rgba(255, 251, 242, 0.98), rgba(255, 244, 225, 0.95));
}

.dashboard-action-card.is-request {
  background:
    radial-gradient(circle at top right, rgba(92, 146, 239, 0.16), transparent 30%),
    linear-gradient(180deg, rgba(244, 248, 255, 0.98), rgba(235, 242, 255, 0.95));
}

.dashboard-action-card.is-expense {
  background:
    radial-gradient(circle at top right, rgba(229, 162, 91, 0.16), transparent 30%),
    linear-gradient(180deg, rgba(255, 248, 242, 0.98), rgba(255, 239, 226, 0.95));
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
  background: linear-gradient(135deg, #274b86, #365f9f);
  color: #fff;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 14px 24px rgba(39, 75, 134, 0.18);
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

  .dashboard-focus-ribbon,
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
    border-radius: 22px;
  }

  .dashboard-stage-panel,
  .dashboard-metrics-panel,
  .dashboard-actions-panel {
    padding: 16px;
    border-radius: 22px;
  }

  .dashboard-stage-copy h2,
  .dashboard-stage-copy p {
    max-width: none;
  }

  .dashboard-stage-copy h2.is-single-line {
    white-space: normal;
  }

  .dashboard-focus-ribbon,
  .dashboard-stage-summary,
  .dashboard-metrics-grid,
  .dashboard-queue-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
