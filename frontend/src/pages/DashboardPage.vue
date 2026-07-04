<script setup>
import { computed } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatJalali, getTodayJalali } from '../utils/jalali'

const { state } = useWorkflowHub()

const todayLabel = computed(() => formatJalali(getTodayJalali()))

const highlightedStats = computed(() => {
  const monthly = state.stats.find((item) => item.id === 'monthly')?.value || state.expenseSummary[2]?.value || '0'

  return [
    { label: 'هزینه ماه جاری', value: monthly, icon: 'payments' },
    { label: 'تعداد درخواست‌ها', value: state.requests.length, icon: 'assignment' },
    { label: 'در انتظار تایید', value: state.approvalMetrics.pending || 0, icon: 'fact_check' },
    { label: 'فعالیت‌های ثبت‌شده', value: state.activities.length, icon: 'timeline' },
  ]
})

const expenseBars = computed(() => {
  const raw = (state.chartData?.length ? state.chartData : state.expenseSummary || []).slice(0, 6)
  const max = Math.max(...raw.map((item) => Number(item.value || item.amount || item.total || 0)), 1)

  return raw.map((item, index) => ({
    key: item.id || item.label || index,
    label: item.label || item.title || item.name || `بازه ${index + 1}`,
    value: item.value || item.amount || item.total || '0',
    height: `${Math.max(16, (Number(item.value || item.amount || item.total || 0) / max) * 100)}%`,
  }))
})
</script>

<template>
  <section class="page-shell enterprise-page">
    <PageHeader eyebrow="نمای کلی سازمان" title="داشبورد مدیریتی" :description="`تاریخ روز: ${todayLabel}`" />

    <section class="metric-grid metric-grid-4">
      <article v-for="item in highlightedStats" :key="item.label" class="metric-card">
        <span class="metric-label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small class="dashboard-metric-icon">
          <span class="material-symbols-outlined">{{ item.icon }}</span>
        </small>
      </article>
    </section>

    <section class="dashboard-grid">
      <article class="surface-block chart-card">
        <div class="section-label-row">
          <div>
            <h3>روند هزینه‌ها</h3>
            <p>نمای بصری از آخرین بازه‌های ثبت‌شده</p>
          </div>
        </div>

        <div class="bar-chart">
          <div v-for="item in expenseBars" :key="item.key" class="bar-chart-item">
            <div class="bar-chart-rail">
              <span :style="{ height: item.height }"></span>
            </div>
            <strong>{{ item.value }}</strong>
            <small>{{ item.label }}</small>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>
