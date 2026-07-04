<script setup>
import { computed, onMounted } from 'vue'

import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { exportReport, filteredReports, loadReports, reportPeople, resetPageFilters, state, updatePageFilter } = useWorkflowHub()

const reportFilters = computed(() => state.filters.reports)

const reportStats = computed(() => [
  { label: 'جمع هزینه‌ها', value: state.reportSummary?.expenseTotal || '0' },
  { label: 'کاربران فعال', value: state.reportSummary?.users || 0 },
  { label: 'درخواست‌ها', value: state.reportSummary?.requests || 0 },
  { label: 'گزارش‌های آماده', value: filteredReports.value.length },
])

const requestStatusItems = computed(() => {
  const entries = Object.entries(state.reportStatus || {})
  const max = Math.max(...entries.map(([, value]) => Number(value || 0)), 1)
  return entries.map(([label, value]) => ({
    label,
    value,
    width: `${Math.max(12, (Number(value || 0) / max) * 100)}%`,
  }))
})

function resetFilters() {
  resetPageFilters('reports')
}

onMounted(() => {
  loadReports(true)
})
</script>

<template>
  <section v-if="state.currentUser.canViewReports" class="page-shell enterprise-page">
    <PageHeader
      eyebrow="بینش مدیریتی"
      title="گزارش‌ها و خروجی‌های تحلیلی"
    />

    <section class="metric-grid metric-grid-4">
      <article v-for="item in reportStats" :key="item.label" class="metric-card">
        <span class="metric-label">{{ item.label }}</span>
      </article>
    </section>

    <PageFilters
      :query="reportFilters.query"
      :person="reportFilters.person"
      :start-date="reportFilters.startDate"
      :end-date="reportFilters.endDate"
      :people="reportPeople"
      @update:query="updatePageFilter('reports', 'query', $event)"
      @update:person="updatePageFilter('reports', 'person', $event)"
      @update:start-date="updatePageFilter('reports', 'startDate', $event)"
      @update:end-date="updatePageFilter('reports', 'endDate', $event)"
      @reset="resetFilters"
    />

    <section class="dashboard-grid">
      <article class="surface-block">
        <div class="section-label-row">
          <div>
            <h3>وضعیت درخواست‌ها</h3>
            <p>توزیع فعلی درخواست‌ها در چرخه عملیاتی</p>
          </div>
        </div>

        <div class="progress-list">
          <article v-for="item in requestStatusItems" :key="item.label" class="progress-row">
            <strong>{{ item.label }}</strong>
            <div class="progress-bar"><span :style="{ width: item.width }"></span></div>
            <small>{{ item.value }}</small>
          </article>
        </div>
      </article>

      <article class="surface-block">
        <div class="section-label-row">
          <div>
            <h3>افراد با بیشترین ثبت</h3>
            <p>کاربران پیشرو از نظر حجم فعالیت</p>
          </div>
        </div>

        <div class="stack-list">
          <article v-for="(item, index) in state.topSubmitters" :key="item.name || index" class="list-row">
            <div class="list-row-main">
              <strong>{{ item.name }}</strong>
              <p>{{ item.amount || '0' }}</p>
            </div>
            <div class="list-row-meta">
              <span class="meta-pill">{{ index + 1 }}</span>
              <small>{{ item.count || 0 }} ثبت</small>
            </div>
          </article>
        </div>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>گزارش‌های آماده خروجی</h3>
          <p>روی هر گزارش کلیک کنید تا فایل خروجی دریافت شود.</p>
        </div>
      </div>

      <div class="card-grid">
        <article v-for="item in filteredReports" :key="item.id" class="report-card">
          <span>{{ item.title }}</span>
          <strong>{{ item.description || 'گزارش مدیریتی سازمان' }}</strong>
          <small>{{ item.owner || 'سامانه' }} - {{ item.generatedAt || '-' }}</small>
          <button class="action-btn tone-primary" type="button" @click="exportReport(item.id, 'csv', item.downloadUrl)">
            <span class="material-symbols-outlined">download</span>
            <span>دریافت خروجی</span>
          </button>
        </article>
      </div>
    </section>
  </section>

  <section v-else class="page-shell">
    <article class="access-denied-card">
      <h2>دسترسی به گزارش‌ها فقط برای مدیران ارشد فعال است</h2>
      <p>برای مشاهده این بخش باید مجوز گزارش‌گیری مدیریتی برای حساب شما تعریف شده باشد.</p>
    </article>
  </section>
</template>
