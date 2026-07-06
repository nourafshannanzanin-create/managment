<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { jalaliToIso } from '../utils/jalali'
import { useWorkflowHub } from '../stores/workflowHub'

const { exportReport, loadReports, state } = useWorkflowHub()

const activeTab = ref('requests')
const filters = reactive({ period: 'month', startDate: '', endDate: '', userId: '' })

const tabs = [
  { key: 'requests', label: 'درخواست', icon: 'assignment' },
  { key: 'expenses', label: 'هزینه ها', icon: 'payments' },
  { key: 'approvals', label: 'تاییدیه ها', icon: 'fact_check' },
]

const periods = [
  { key: 'today', label: 'امروز' },
  { key: 'week', label: 'این هفته' },
  { key: 'month', label: 'این ماه' },
  { key: 'year', label: 'امسال' },
  { key: 'custom', label: 'بازه' },
]

const reportUsers = computed(() => state.users || [])

function rowDate(item) {
  if (activeTab.value === 'requests') return item.createdAtIso || item.deadlineIso || ''
  if (activeTab.value === 'expenses') return item.createdAtIso || ''
  return item.uploadedAtIso || ''
}

function inPeriod(isoDate) {
  if (!isoDate) return false
  const date = new Date(`${isoDate}T00:00:00`)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (filters.period === 'today') return date.getTime() === today.getTime()
  if (filters.period === 'week') {
    const start = new Date(today)
    start.setDate(today.getDate() - ((today.getDay() + 6) % 7))
    return date >= start && date <= today
  }
  if (filters.period === 'month') return date.getFullYear() === today.getFullYear() && date.getMonth() === today.getMonth()
  if (filters.period === 'year') return date.getFullYear() === today.getFullYear()
  const startIso = filters.startDate ? jalaliToIso(filters.startDate) : ''
  const endIso = filters.endDate ? jalaliToIso(filters.endDate) : ''
  if (startIso && isoDate < startIso) return false
  if (endIso && isoDate > endIso) return false
  return true
}

const activeRows = computed(() => {
  const rows = activeTab.value === 'requests' ? state.requests : activeTab.value === 'expenses' ? state.expenses : state.approvals
  return rows.filter((item) => {
    const user = reportUsers.value.find((row) => String(row.id) === String(filters.userId))
    const matchesUser = !filters.userId || [item.owner, item.manager].filter(Boolean).includes(user?.name)
    return matchesUser && inPeriod(rowDate(item))
  })
})

function decisionText(item) {
  const decisions = item.decisions || []
  return decisions.length ? decisions.map((row) => `${row.approver}: ${row.statusLabel}`).join(' | ') : '-'
}

function exportActiveTab() {
  const params = new URLSearchParams({ format: 'csv', period: filters.period })
  if (filters.period === 'custom') {
    if (filters.startDate) params.set('startDate', jalaliToIso(filters.startDate))
    if (filters.endDate) params.set('endDate', jalaliToIso(filters.endDate))
  }
  if (filters.userId) params.set('userId', filters.userId)
  exportReport('', 'csv', `/reports/${activeTab.value}/export?${params.toString()}`)
}

onMounted(() => loadReports(true))
</script>

<template>
  <section v-if="state.currentUser.canViewReports" class="page-shell enterprise-page reports-page">
    <PageHeader eyebrow="گزارشات" title="گزارش تفکیکی" description="" />

    <section class="surface-block report-controls">
      <div class="report-tabs">
        <button v-for="tab in tabs" :key="tab.key" :class="['report-tab', activeTab === tab.key && 'is-active']" type="button" @click="activeTab = tab.key">
          <span class="material-symbols-outlined">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <div class="report-filter-grid">
        <div class="chip-row">
          <button v-for="item in periods" :key="item.key" :class="['filter-chip', filters.period === item.key && 'is-active']" type="button" @click="filters.period = item.key">
            {{ item.label }}
          </button>
        </div>
        <label class="field-shell compact-field">
          <span>کاربر</span>
          <select v-model="filters.userId">
            <option value="">همه کاربران</option>
            <option v-for="user in reportUsers" :key="user.id" :value="user.id">{{ user.name }}</option>
          </select>
        </label>
        <template v-if="filters.period === 'custom'">
          <label class="field-shell compact-field"><span>از تاریخ</span><ShamsiDatePicker v-model="filters.startDate" model-type="jalali" /></label>
          <label class="field-shell compact-field"><span>تا تاریخ</span><ShamsiDatePicker v-model="filters.endDate" model-type="jalali" /></label>
        </template>
        <button class="action-btn tone-primary" type="button" @click="exportActiveTab">
          <span class="material-symbols-outlined">download</span>
          <span>دانلود جدول</span>
        </button>
      </div>
    </section>

    <section class="surface-block report-table-card">
      <div class="section-label-row">
        <div><h3>{{ tabs.find((item) => item.key === activeTab)?.label }}</h3></div>
        <span class="meta-pill">{{ activeRows.length }} ردیف</span>
      </div>

      <div class="report-table-wrap">
        <table class="report-table">
          <thead>
            <tr v-if="activeTab === 'requests'"><th>کد</th><th>عنوان</th><th>ثبت کننده</th><th>مدیر</th><th>بخش</th><th>وضعیت</th><th>اولویت</th><th>تاریخ</th><th>تصمیم ها</th></tr>
            <tr v-else-if="activeTab === 'expenses'"><th>کد</th><th>شرح</th><th>ثبت کننده</th><th>مبلغ</th><th>بخش</th><th>وضعیت</th><th>تاریخ</th><th>تصمیم ها</th></tr>
            <tr v-else><th>کد</th><th>عنوان</th><th>ثبت کننده</th><th>نوع</th><th>بخش</th><th>ریسک</th><th>وضعیت</th><th>تاریخ</th><th>تصمیم ها</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in activeRows" :key="row.id">
              <template v-if="activeTab === 'requests'"><td>{{ row.id }}</td><td>{{ row.title }}</td><td>{{ row.owner }}</td><td>{{ row.manager }}</td><td>{{ row.department }}</td><td>{{ row.status }}</td><td>{{ row.priority }}</td><td>{{ row.createdAt }}</td><td>{{ decisionText(row) }}</td></template>
              <template v-else-if="activeTab === 'expenses'"><td>{{ row.id }}</td><td>{{ row.description }}</td><td>{{ row.owner }}</td><td>{{ row.amount }}</td><td>{{ row.department }}</td><td>{{ row.status }}</td><td>{{ row.submittedAt }}</td><td>{{ decisionText(row) }}</td></template>
              <template v-else><td>{{ row.id }}</td><td>{{ row.title }}</td><td>{{ row.owner }}</td><td>{{ row.type }}</td><td>{{ row.department }}</td><td>{{ row.risk }}</td><td>{{ row.status }}</td><td>{{ row.uploadedAt }}</td><td>{{ decisionText(row) }}</td></template>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <section v-else class="page-shell"><article class="access-denied-card"><h2>دسترسی گزارش ندارید</h2></article></section>
</template>

<style scoped>
.reports-page { gap: 16px; }
.report-controls { display: grid; gap: 16px; }
.report-tabs, .report-filter-grid { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.report-tab { min-height: 44px; border: 0; border-radius: 14px; padding: 0 14px; display: inline-flex; align-items: center; gap: 8px; color: #31405f; background: rgba(72,103,183,.09); font-weight: 900; cursor: pointer; }
.report-tab.is-active { color: #fff; background: linear-gradient(135deg, var(--primary), var(--secondary)); }
.compact-field { min-width: 190px; margin: 0; }
.report-table-wrap { overflow-x: auto; }
.report-table { width: 100%; min-width: 980px; border-collapse: collapse; }
.report-table th, .report-table td { padding: 12px 10px; border-bottom: 1px solid rgba(38,56,92,.08); text-align: right; vertical-align: top; }
.report-table th { color: #52607a; font-size: 12px; }
.report-table td { color: #203255; line-height: 1.7; }
@media (max-width: 760px) { .report-filter-grid, .report-tabs { display: grid; grid-template-columns: 1fr; } .compact-field, .action-btn { width: 100%; } }
</style>
