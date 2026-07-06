<script setup>
import { computed, onMounted } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { exportReport, filteredReports, loadReports, state } = useWorkflowHub()

const reportStats = computed(() => [
  { label: 'جمع هزینه‌ها', value: state.reportSummary?.expenseTotal || '0', icon: 'payments', note: 'خلاصه مالی', tone: 'is-total' },
  { label: 'کاربران فعال', value: state.reportSummary?.users || 0, icon: 'verified_user', note: 'اعضای فعال', tone: 'is-approved' },
  { label: 'درخواست‌ها', value: state.reportSummary?.requests || 0, icon: 'pending_actions', note: 'ثبت عملیاتی', tone: 'is-pending' },
  { label: 'گزارش آماده', value: filteredReports.value.length, icon: 'folder_copy', note: 'خروجی‌های قابل دانلود', tone: 'is-rejected' },
])

onMounted(() => {
  loadReports(true)
})
</script>

<template>
  <section v-if="state.currentUser.canViewReports" class="page-shell enterprise-page">
    <PageHeader
      eyebrow="گزارشات"
      title="گزارش‌ها و خروجی‌های تحلیلی"
      description="در این بخش فقط خلاصه و خروجی‌های آماده گزارش نمایش داده می‌شود."
    />

    <section class="metric-grid metric-grid-4">
      <article v-for="item in reportStats" :key="item.label" :class="['metric-card', 'approval-metric-card', item.tone]">
        <div class="metric-card-headline">
          <span class="metric-label">{{ item.label }}</span>
          <span class="material-symbols-outlined approval-metric-icon">{{ item.icon }}</span>
        </div>
        <strong>{{ item.value }}</strong>
        <small class="approval-metric-note">{{ item.note }}</small>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>خروجی‌های آماده</h3>
          <p>نمای تفکیکی درخواست‌ها، هزینه‌ها و تاییدها از این صفحه حذف شده و فقط فایل‌های خروجی نمایش داده می‌شود.</p>
        </div>
        <span class="meta-pill">{{ filteredReports.length }} خروجی</span>
      </div>

      <div v-if="filteredReports.length" class="report-export-grid">
        <article v-for="item in filteredReports" :key="item.title" class="report-export-card">
          <div class="report-export-copy">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description || 'خروجی آماده دریافت است.' }}</p>
            <small class="table-muted">{{ item.export || 'CSV' }} · {{ item.generatedAt || '-' }}</small>
          </div>

          <button class="action-btn tone-primary" type="button" @click="exportReport('', 'csv', item.downloadUrl)">
            <span class="material-symbols-outlined">download</span>
            <span>دانلود</span>
          </button>
        </article>
      </div>

      <div v-else class="empty-state-inline">
        <span class="material-symbols-outlined">folder_off</span>
        <p>خروجی‌ای برای این فیلترها پیدا نشد.</p>
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

<style scoped>
.report-export-grid {
  display: grid;
  gap: 14px;
}

.report-export-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid rgba(36, 59, 107, 0.1);
  background: rgba(255, 255, 255, 0.8);
}

.report-export-copy {
  display: grid;
  gap: 6px;
}

.report-export-copy strong,
.report-export-copy p,
.report-export-copy small {
  margin: 0;
}

@media (max-width: 760px) {
  .report-export-card {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
