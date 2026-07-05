<script setup>
import { computed, onMounted, ref } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const activeTab = ref('requests')

const { exportReport, filteredReports, loadReports, state } = useWorkflowHub()

const reportStats = computed(() => [
  { label: 'جمع هزینه‌ها', value: state.reportSummary?.expenseTotal || '0' },
  { label: 'کاربران فعال', value: state.reportSummary?.users || 0 },
  { label: 'درخواست‌ها', value: state.reportSummary?.requests || 0 },
  { label: 'گزارش آماده', value: filteredReports.value.length },
])

const reportTabs = computed(() => [
  {
    key: 'requests',
    label: 'درخواست‌ها',
    rows: state.requests,
    exportId: 'requests',
    columns: [
      { key: 'id', label: 'کد' },
      { key: 'title', label: 'عنوان' },
      { key: 'owner', label: 'ثبت‌کننده' },
      { key: 'manager', label: 'مسئول' },
      { key: 'status', label: 'وضعیت' },
      { key: 'priority', label: 'اولویت' },
      { key: 'createdAt', label: 'تاریخ' },
    ],
  },
  {
    key: 'expenses',
    label: 'هزینه‌ها',
    rows: state.expenses,
    exportId: 'expenses',
    columns: [
      { key: 'id', label: 'کد' },
      { key: 'title', label: 'عنوان' },
      { key: 'owner', label: 'ثبت‌کننده' },
      { key: 'amount', label: 'مبلغ' },
      { key: 'category', label: 'دسته' },
      { key: 'status', label: 'وضعیت' },
      { key: 'submittedAt', label: 'تاریخ' },
    ],
  },
  {
    key: 'approvals',
    label: 'تاییدها',
    rows: state.approvals,
    exportId: 'approvals',
    columns: [
      { key: 'id', label: 'کد' },
      { key: 'title', label: 'عنوان' },
      { key: 'owner', label: 'ثبت‌کننده' },
      { key: 'type', label: 'نوع' },
      { key: 'status', label: 'وضعیت' },
      { key: 'risk', label: 'ریسک' },
      { key: 'uploadedAt', label: 'تاریخ' },
    ],
  },
])

const currentTab = computed(() => reportTabs.value.find((item) => item.key === activeTab.value) || reportTabs.value[0])

onMounted(() => {
  loadReports(true)
})
</script>

<template>
  <section v-if="state.currentUser.canViewReports" class="page-shell enterprise-page">
    <PageHeader
      eyebrow="گزارشات"
      title="گزارش‌ها و خروجی‌های تحلیلی"
      description="هر تب گزارش کامل همان بخش را با داده‌های آماده خروجی نمایش می‌دهد."
    />

    <section class="metric-grid metric-grid-4">
      <article v-for="item in reportStats" :key="item.label" class="metric-card">
        <span class="metric-label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>دسته‌بندی گزارش‌ها</h3>
          <p>نمای تفکیکی برای درخواست‌ها، هزینه‌ها و تاییدها.</p>
        </div>
        <div class="chip-row">
          <button
            v-for="tab in reportTabs"
            :key="tab.key"
            :class="['filter-chip', activeTab === tab.key && 'is-active']"
            type="button"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div class="report-tab-header">
        <div>
          <strong>{{ currentTab.label }}</strong>
          <small class="table-muted">{{ currentTab.rows.length }} ردیف آماده گزارش</small>
        </div>
        <button class="action-btn tone-primary" type="button" @click="exportReport(currentTab.exportId, 'csv')">
          <span class="material-symbols-outlined">download</span>
          <span>دریافت خروجی {{ currentTab.label }}</span>
        </button>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="column in currentTab.columns" :key="column.key">{{ column.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in currentTab.rows" :key="row.id">
              <td v-for="column in currentTab.columns" :key="`${row.id}-${column.key}`">
                <strong v-if="column.key === 'title' || column.key === 'id'">{{ row[column.key] || '-' }}</strong>
                <span v-else>{{ row[column.key] || '-' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
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
