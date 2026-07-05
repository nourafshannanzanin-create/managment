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

const highlightedStats = computed(() => {
  const monthlyExpense = state.stats.find((item) => item.id === 'monthly')?.value || state.expenseSummary[2]?.value || '0'
  const approvedDocs = state.stats.find((item) => item.id === 'approved')?.value || state.approvalMetrics.approved || 0

  return [
    {
      label: 'هزینه ماه جاری',
      value: monthlyExpense,
      note: 'جمع مصارف این ماه',
      icon: 'payments',
      tone: 'is-expense',
    },
    {
      label: 'درخواست‌های فعال',
      value: state.requests.length,
      note: 'کل درخواست‌های در گردش',
      icon: 'assignment',
      tone: 'is-request',
    },
    {
      label: 'در انتظار تایید',
      value: state.approvalMetrics.pending || 0,
      note: 'نیازمند تصمیم مدیران',
      icon: 'pending_actions',
      tone: 'is-approval',
    },
    {
      label: 'اسناد تاییدشده',
      value: approvedDocs,
      note: 'خروجی نهایی ثبت شده',
      icon: 'verified',
      tone: 'is-success',
    },
  ]
})

const operationalSnapshot = computed(() => [
  {
    label: 'کاربران فعال',
    value: state.users.length,
    detail: 'افراد حاضر در ساختار سازمانی',
    icon: 'groups',
  },
  {
    label: 'واحدهای سازمانی',
    value: state.directories.departments.length,
    detail: 'واحدهای ثبت شده در سیستم',
    icon: 'apartment',
  },
  {
    label: 'گزارش‌های آماده',
    value: state.reports.length,
    detail: 'خروجی‌های قابل دریافت',
    icon: 'monitoring',
  },
  {
    label: 'فعالیت‌های اخیر',
    value: state.activities.length,
    detail: 'آخرین رخدادهای سیستمی',
    icon: 'bolt',
  },
])

const expenseBars = computed(() => {
  const raw = (state.chartData?.length ? state.chartData : state.expenseSummary || []).slice(0, 7)
  const max = Math.max(...raw.map((item) => Number(item.value || item.amount || item.total || 0)), 1)

  return raw.map((item, index) => {
    const amount = Number(item.value || item.amount || item.total || 0)
    return {
      key: item.id || item.label || item.day || index,
      label: item.label || item.day || item.title || item.name || `بازه ${index + 1}`,
      value: item.value || item.amount || item.total || '0',
      height: `${Math.max(14, (amount / max) * 100)}%`,
      amount,
    }
  })
})

const expenseWindows = computed(() => {
  const summary = state.expenseSummary || []
  return summary.map((item, index) => ({
    key: item.label || index,
    label: item.label || `بازه ${index + 1}`,
    value: item.value || '0',
  }))
})

const pipelineItems = computed(() => {
  const raw = state.pipeline || []
  const max = Math.max(...raw.map((item) => Number(item.count || 0)), 1)
  return raw.map((item, index) => ({
    key: item.label || index,
    label: item.label || `مرحله ${index + 1}`,
    count: Number(item.count || 0),
    width: `${Math.max(10, (Number(item.count || 0) / max) * 100)}%`,
  }))
})

const recentActivities = computed(() => (state.activities || []).slice(0, 6))

const recentRequests = computed(() => {
  const sortable = [...(state.requests || [])]
  return sortable
    .sort((a, b) => String(b.createdAtIso || '').localeCompare(String(a.createdAtIso || '')))
    .slice(0, 4)
})

const pendingApprovals = computed(() =>
  [...(state.approvals || [])]
    .filter((item) => item.bucket === 'pending' || String(item.status || '').includes('انتظار') || String(item.status || '').includes('بررسی'))
    .slice(0, 4),
)
</script>

<template>
  <section class="page-shell enterprise-page dashboard-page-rich">
    <PageHeader
      eyebrow="مرکز عملیات"
      title="داشبورد مدیریتی"
      :description="`امروز ${todayLabel} است. این نما، وضعیت جاری درخواست‌ها، هزینه‌ها، تاییدها و تحرک سازمان را یک‌جا نشان می‌دهد.`"
      action-label="ثبت درخواست"
      action-icon="add_circle"
      @action="openRequestComposer"
    />

    <section class="dashboard-hero-grid">
      <article class="dashboard-hero-panel">
        <div class="dashboard-hero-copy">
          <span class="dashboard-hero-kicker">تصویر کلی عملیات</span>
          <h2>نمای کامل‌تری از جریان کار، تصمیم‌ها و حجم فعالیت امروز</h2>
          <p>
            این داشبورد از داده‌های واقعی سیستم ساخته شده و همزمان وضعیت هزینه، صف تایید، تعداد درخواست‌ها،
            روند فعالیت و نقاطی که نیاز به اقدام دارند را نشان می‌دهد.
          </p>
        </div>

        <div class="dashboard-hero-summary">
          <div v-for="item in operationalSnapshot" :key="item.label" class="dashboard-mini-stat">
            <div class="dashboard-mini-icon">
              <span class="material-symbols-outlined">{{ item.icon }}</span>
            </div>
            <div>
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
              <small>{{ item.detail }}</small>
            </div>
          </div>
        </div>
      </article>

      <article class="dashboard-command-panel">
        <div class="section-label-row">
          <div>
            <h3>جمع‌بندی سریع</h3>
            <p>چهار شاخص کلیدی برای بررسی فوری وضعیت جاری.</p>
          </div>
        </div>

        <div class="dashboard-command-grid">
          <article v-for="item in highlightedStats" :key="item.label" :class="['metric-card', 'dashboard-kpi-card', item.tone]">
            <div class="dashboard-kpi-head">
              <span class="metric-label">{{ item.label }}</span>
              <span class="material-symbols-outlined dashboard-kpi-icon">{{ item.icon }}</span>
            </div>
            <strong>{{ item.value }}</strong>
            <small>{{ item.note }}</small>
          </article>
        </div>
      </article>
    </section>

    <section class="dashboard-main-grid">
      <article class="surface-block dashboard-chart-panel">
        <div class="section-label-row">
          <div>
            <h3>روند هزینه‌ها</h3>
            <p>الگوی ثبت هزینه در چند بازه آخر برای مقایسه سریع حجم مصرف.</p>
          </div>
        </div>

        <div v-if="expenseBars.length" class="bar-chart dashboard-bar-chart">
          <div v-for="item in expenseBars" :key="item.key" class="bar-chart-item">
            <div class="bar-chart-rail">
              <span :style="{ height: item.height }"></span>
            </div>
            <strong>{{ item.value }}</strong>
            <small>{{ item.label }}</small>
          </div>
        </div>
        <div v-else class="empty-state-inline">
          <span class="material-symbols-outlined">bar_chart</span>
          <p>برای این بازه هنوز داده روند هزینه ثبت نشده است.</p>
        </div>

        <div class="dashboard-expense-strip">
          <article v-for="item in expenseWindows" :key="item.key" class="dashboard-expense-chip">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </article>

      <article class="surface-block dashboard-pipeline-panel">
        <div class="section-label-row">
          <div>
            <h3>خط جریان درخواست‌ها</h3>
            <p>هر مرحله نشان می‌دهد چه میزان از بار عملیاتی در کدام وضعیت مانده است.</p>
          </div>
        </div>

        <div v-if="pipelineItems.length" class="dashboard-pipeline-list">
          <article v-for="item in pipelineItems" :key="item.key" class="dashboard-pipeline-row">
            <div class="dashboard-pipeline-copy">
              <strong>{{ item.label }}</strong>
              <small>{{ item.count }} مورد</small>
            </div>
            <div class="dashboard-pipeline-bar">
              <span :style="{ width: item.width }"></span>
            </div>
          </article>
        </div>
        <div v-else class="empty-state-inline">
          <span class="material-symbols-outlined">lan</span>
          <p>داده‌ای برای مراحل جریان درخواست‌ها ثبت نشده است.</p>
        </div>
      </article>
    </section>

    <section class="dashboard-secondary-grid">
      <article class="surface-block dashboard-feed-panel">
        <div class="section-label-row">
          <div>
            <h3>آخرین فعالیت‌ها</h3>
            <p>مروری سریع بر جدیدترین رویدادهای عملیاتی سیستم.</p>
          </div>
        </div>

        <div v-if="recentActivities.length" class="dashboard-activity-list">
          <article v-for="item in recentActivities" :key="item.id" class="dashboard-activity-row">
            <div class="dashboard-activity-icon">
              <span class="material-symbols-outlined">{{ item.icon || 'history' }}</span>
            </div>
            <div class="dashboard-activity-copy">
              <strong>{{ item.user || 'کاربر' }}</strong>
              <p>{{ item.detail || item.action || '-' }}</p>
            </div>
            <small>{{ item.time || '-' }}</small>
          </article>
        </div>
        <div v-else class="empty-state-inline">
          <span class="material-symbols-outlined">schedule</span>
          <p>هنوز فعالیتی برای نمایش ثبت نشده است.</p>
        </div>
      </article>

      <article class="surface-block dashboard-queue-panel">
        <div class="section-label-row">
          <div>
            <h3>صف اقدام سریع</h3>
            <p>نزدیک‌ترین آیتم‌هایی که احتمالا به پیگیری مدیریتی نیاز دارند.</p>
          </div>
        </div>

        <div class="dashboard-queue-stack">
          <article v-for="item in pendingApprovals" :key="item.id" class="dashboard-queue-card">
            <div class="dashboard-queue-head">
              <div>
                <strong>{{ item.title }}</strong>
                <small>{{ item.owner }} - {{ item.department }}</small>
              </div>
              <span class="status-badge is-warning">{{ item.status }}</span>
            </div>
            <div class="dashboard-queue-meta">
              <span>{{ item.type }}</span>
              <span>{{ item.risk }}</span>
              <span>{{ item.uploadedAt || '-' }}</span>
            </div>
            <button class="table-link" type="button" @click="openApprovalDetail(item.id)">مشاهده و تصمیم</button>
          </article>

          <article v-for="item in recentRequests" :key="item.id" class="dashboard-queue-card request-tone">
            <div class="dashboard-queue-head">
              <div>
                <strong>{{ item.title }}</strong>
                <small>{{ item.owner }} - {{ item.department }}</small>
              </div>
              <span class="status-badge is-success">{{ item.status }}</span>
            </div>
            <div class="dashboard-queue-meta">
              <span>{{ item.priority || '-' }}</span>
              <span>{{ item.manager || '-' }}</span>
              <span>{{ item.createdAt || item.deadline || '-' }}</span>
            </div>
            <button class="table-link" type="button" @click="openRequestDetail(item.id)">جزئیات درخواست</button>
          </article>

          <article
            v-for="item in (state.expenses || []).slice(0, 3)"
            :key="item.id"
            class="dashboard-queue-card expense-tone"
          >
            <div class="dashboard-queue-head">
              <div>
                <strong>{{ item.title }}</strong>
                <small>{{ item.owner }} - {{ item.category }}</small>
              </div>
              <span class="status-badge is-danger">{{ item.status }}</span>
            </div>
            <div class="dashboard-queue-meta">
              <span>{{ item.amount }}</span>
              <span>{{ item.department }}</span>
              <span>{{ item.submittedAt || '-' }}</span>
            </div>
            <button class="table-link" type="button" @click="openExpenseDetail(item.id)">بررسی هزینه</button>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page-rich {
  display: grid;
  gap: 18px;
}

.dashboard-hero-grid,
.dashboard-main-grid,
.dashboard-secondary-grid {
  display: grid;
  gap: 18px;
}

.dashboard-hero-grid {
  grid-template-columns: minmax(0, 1.3fr) minmax(360px, 0.95fr);
}

.dashboard-main-grid {
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
}

.dashboard-secondary-grid {
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.92fr);
}

.dashboard-hero-panel,
.dashboard-command-panel,
.dashboard-kpi-card,
.dashboard-mini-stat,
.dashboard-pipeline-row,
.dashboard-expense-chip,
.dashboard-activity-row,
.dashboard-queue-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(36, 59, 107, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.95)),
    var(--surface);
  box-shadow: 0 18px 42px rgba(30, 45, 84, 0.08);
}

.dashboard-hero-panel,
.dashboard-command-panel {
  border-radius: 30px;
  padding: 22px;
}

.dashboard-hero-panel {
  display: grid;
  gap: 24px;
  background:
    radial-gradient(circle at top right, rgba(72, 103, 183, 0.12), transparent 34%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.95)),
    var(--surface);
}

.dashboard-hero-copy {
  display: grid;
  gap: 10px;
}

.dashboard-hero-kicker {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: rgba(72, 103, 183, 0.78);
}

.dashboard-hero-copy h2 {
  margin: 0;
  font-size: clamp(28px, 2.2vw, 38px);
  line-height: 1.35;
  color: #203255;
}

.dashboard-hero-copy p {
  margin: 0;
  color: var(--muted);
  line-height: 1.95;
  max-width: 90%;
}

.dashboard-hero-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.dashboard-mini-stat {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: center;
  padding: 16px;
  border-radius: 22px;
}

.dashboard-mini-icon,
.dashboard-kpi-icon,
.dashboard-activity-icon {
  display: grid;
  place-items: center;
}

.dashboard-mini-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: rgba(72, 103, 183, 0.08);
  color: var(--primary);
}

.dashboard-mini-stat strong,
.dashboard-mini-stat span,
.dashboard-mini-stat small {
  display: block;
}

.dashboard-mini-stat strong {
  font-size: 22px;
  color: #203255;
}

.dashboard-mini-stat span {
  font-size: 13px;
  font-weight: 800;
}

.dashboard-mini-stat small {
  margin-top: 2px;
  color: var(--muted);
  line-height: 1.7;
}

.dashboard-command-panel {
  display: grid;
  gap: 18px;
}

.dashboard-command-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.dashboard-kpi-card {
  min-height: 154px;
  padding: 18px;
  border-radius: 24px;
  display: grid;
  gap: 16px;
}

.dashboard-kpi-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: rgba(72, 103, 183, 0.08);
  color: var(--primary);
  font-size: 23px;
}

.dashboard-kpi-card strong {
  margin: 0;
  font-size: clamp(28px, 2.1vw, 38px);
  line-height: 1.05;
  color: #203255;
}

.dashboard-kpi-card small {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.dashboard-kpi-card.is-expense {
  background:
    linear-gradient(180deg, rgba(255, 249, 239, 0.98), rgba(255, 244, 226, 0.95)),
    var(--surface);
}

.dashboard-kpi-card.is-request {
  background:
    linear-gradient(180deg, rgba(242, 247, 255, 0.98), rgba(234, 241, 255, 0.95)),
    var(--surface);
}

.dashboard-kpi-card.is-approval {
  background:
    linear-gradient(180deg, rgba(255, 248, 232, 0.98), rgba(255, 241, 210, 0.95)),
    var(--surface);
}

.dashboard-kpi-card.is-success {
  background:
    linear-gradient(180deg, rgba(238, 250, 244, 0.98), rgba(227, 247, 236, 0.95)),
    var(--surface);
}

.dashboard-chart-panel,
.dashboard-pipeline-panel,
.dashboard-feed-panel,
.dashboard-queue-panel {
  display: grid;
  gap: 18px;
}

.dashboard-bar-chart {
  align-items: end;
  min-height: 290px;
}

.dashboard-expense-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.dashboard-expense-chip {
  padding: 16px;
  border-radius: 20px;
  display: grid;
  gap: 8px;
}

.dashboard-expense-chip span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.dashboard-expense-chip strong {
  margin: 0;
  font-size: 18px;
  color: #203255;
}

.dashboard-pipeline-list,
.dashboard-activity-list,
.dashboard-queue-stack {
  display: grid;
  gap: 12px;
}

.dashboard-pipeline-row {
  padding: 16px 18px;
  border-radius: 20px;
  display: grid;
  gap: 12px;
}

.dashboard-pipeline-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.dashboard-pipeline-copy strong {
  color: #203255;
}

.dashboard-pipeline-copy small {
  color: var(--muted);
}

.dashboard-pipeline-bar {
  height: 10px;
  border-radius: 999px;
  background: rgba(72, 103, 183, 0.08);
  overflow: hidden;
}

.dashboard-pipeline-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #4f69b8, #d6a16d);
}

.dashboard-activity-row {
  padding: 16px;
  border-radius: 20px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
}

.dashboard-activity-icon {
  width: 44px;
  height: 44px;
  border-radius: 15px;
  background: rgba(72, 103, 183, 0.08);
  color: var(--primary);
}

.dashboard-activity-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.dashboard-activity-copy strong,
.dashboard-activity-copy p {
  margin: 0;
}

.dashboard-activity-copy p {
  color: var(--muted);
  line-height: 1.75;
}

.dashboard-activity-row > small {
  color: var(--muted);
  white-space: nowrap;
}

.dashboard-queue-card {
  padding: 16px;
  border-radius: 22px;
  display: grid;
  gap: 12px;
}

.dashboard-queue-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-queue-head strong,
.dashboard-queue-head small {
  display: block;
}

.dashboard-queue-head small {
  margin-top: 4px;
  color: var(--muted);
}

.dashboard-queue-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dashboard-queue-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(72, 103, 183, 0.06);
  color: var(--muted);
  font-size: 12px;
}

.dashboard-queue-card.request-tone {
  background:
    linear-gradient(180deg, rgba(245, 249, 255, 0.98), rgba(237, 244, 255, 0.95)),
    var(--surface);
}

.dashboard-queue-card.expense-tone {
  background:
    linear-gradient(180deg, rgba(255, 248, 241, 0.98), rgba(255, 242, 230, 0.95)),
    var(--surface);
}

@media (max-width: 1240px) {
  .dashboard-hero-grid,
  .dashboard-main-grid,
  .dashboard-secondary-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .dashboard-hero-summary,
  .dashboard-command-grid,
  .dashboard-expense-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .dashboard-hero-copy p {
    max-width: none;
  }

  .dashboard-hero-summary,
  .dashboard-command-grid,
  .dashboard-expense-strip {
    grid-template-columns: minmax(0, 1fr);
  }

  .dashboard-activity-row {
    grid-template-columns: auto 1fr;
  }

  .dashboard-activity-row > small {
    grid-column: 2;
  }
}
</style>
