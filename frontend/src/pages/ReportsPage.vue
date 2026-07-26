<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, reactive, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import PageHeader from '../components/PageHeader.vue'
import SectionHeading from '../components/SectionHeading.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { jalaliToIso } from '../utils/jalali'
import { useWorkflowHub } from '../stores/workflowHub'
import { joinDisplayParts } from '../utils/text'

const { exportReport, loadReports, state } = useWorkflowHub()

const activeTab = ref('requests')
const selectedReportRow = ref(null)
const selectedReportType = ref('')
const filters = reactive({ period: 'month', startDate: '', endDate: '', userId: '' })

const tabs = [
  { key: 'requests', label: 'درخواست‌ها', icon: 'assignment' },
  { key: 'expenses', label: 'هزینه‌ها', icon: 'payments' },
  { key: 'approvals', label: 'تاییدیه‌ها', icon: 'fact_check' },
  { key: 'users', label: 'کاربران', icon: 'groups' },
]

const periods = [
  { key: 'today', label: 'امروز' },
  { key: 'week', label: 'این هفته' },
  { key: 'month', label: 'این ماه' },
  { key: 'year', label: 'امسال' },
  { key: 'custom', label: 'دلخواه' },
]

const reportUsers = computed(() => state.users || [])

function rowDate(item) {
  if (activeTab.value === 'requests') return item.createdAtIso || item.deadlineIso || ''
  if (activeTab.value === 'expenses') return item.createdAtIso || ''
  if (activeTab.value === 'users') return item.financeUpdatedAtIso || item.joinedAtIso || ''
  return item.uploadedAtIso || ''
}

function inPeriod(isoDate) {
  if (!isoDate) return activeTab.value === 'users'
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
  const rows = activeTab.value === 'requests'
    ? state.requests
    : activeTab.value === 'expenses'
      ? state.expenses
      : activeTab.value === 'users'
        ? state.users
        : state.approvals
  return rows.filter((item) => {
    const user = reportUsers.value.find((row) => String(row.id) === String(filters.userId))
    const matchesUser = !filters.userId || [item.owner, item.manager, item.name].filter(Boolean).includes(user?.name)
    return matchesUser && inPeriod(rowDate(item))
  })
})

const selectedTabMeta = computed(() => tabs.find((item) => item.key === selectedReportType.value) || tabs[0])

const selectedDetailTitle = computed(() => {
  const row = selectedReportRow.value
  if (!row) return ''
  return row.title || row.description || row.id || 'جزئیات گزارش'
})

const selectedDetailSubtitle = computed(() => {
  const row = selectedReportRow.value
  if (!row) return ''
  if (selectedReportType.value === 'expenses') return joinDisplayParts([row.owner, row.department, row.submittedAt], ' / ')
  if (selectedReportType.value === 'approvals') return joinDisplayParts([row.owner, row.type, row.uploadedAt], ' / ')
  if (selectedReportType.value === 'users') return joinDisplayParts([row.role, row.department, row.financeUpdatedAt || row.joinedAt], ' / ')
  return joinDisplayParts([row.owner, row.manager, row.createdAt], ' / ')
})

const selectedPrimaryMetrics = computed(() => {
  const row = selectedReportRow.value
  if (!row) return []
  if (selectedReportType.value === 'expenses') {
    return [
      { label: 'مبلغ', value: row.amount || '-', icon: 'payments' },
      { label: 'وضعیت', value: row.status || '-', icon: 'verified' },
      { label: 'واحد', value: row.department || '-', icon: 'apartment' },
    ]
  }
  if (selectedReportType.value === 'approvals') {
    return [
      { label: 'ریسک', value: row.risk || '-', icon: 'warning' },
      { label: 'وضعیت', value: row.status || '-', icon: 'fact_check' },
      { label: 'نوع سند', value: row.type || '-', icon: 'description' },
    ]
  }
  if (selectedReportType.value === 'users') {
    return [
      { label: 'پاداش', value: row.bonusAmount || '-', icon: 'award_star' },
      { label: 'جریمه', value: row.penaltyAmount || '-', icon: 'gavel' },
      { label: 'خالص', value: row.netAdjustment || '-', icon: 'balance' },
    ]
  }
  return [
    { label: 'اولویت', value: row.priority || '-', icon: 'priority_high' },
    { label: 'وضعیت', value: row.status || '-', icon: 'verified' },
    { label: 'واحد', value: row.department || '-', icon: 'apartment' },
  ]
})

const selectedDetailFields = computed(() => {
  const row = selectedReportRow.value
  if (!row) return []
  if (selectedReportType.value === 'expenses') {
    return [
      { label: 'کد', value: row.id },
      { label: 'ثبت‌کننده', value: row.owner },
      { label: 'تاریخ ثبت', value: row.submittedAt || row.createdAt },
      { label: 'واحد', value: row.department },
      { label: 'وضعیت', value: row.status },
      { label: 'مبلغ', value: row.amount },
      { label: 'شرح', value: row.description, wide: true },
    ]
  }
  if (selectedReportType.value === 'approvals') {
    return [
      { label: 'کد', value: row.id },
      { label: 'عنوان', value: row.title },
      { label: 'ثبت‌کننده', value: row.owner },
      { label: 'نوع', value: row.type },
      { label: 'واحد', value: row.department },
      { label: 'ریسک', value: row.risk },
      { label: 'وضعیت', value: row.status },
      { label: 'تاریخ بارگذاری', value: row.uploadedAt },
    ]
  }
  if (selectedReportType.value === 'users') {
    return [
      { label: 'شناسه', value: row.id },
      { label: 'نام', value: row.name },
      { label: 'نام کاربری', value: row.username },
      { label: 'نقش', value: row.role },
      { label: 'عنوان شغلی', value: row.jobTitle },
      { label: 'واحد', value: row.department },
      { label: 'مدیر مستقیم', value: row.manager },
      { label: 'وضعیت', value: row.status },
      { label: 'تاریخ عضویت', value: row.joinedAt },
      { label: 'آخرین بروزرسانی مالی', value: row.financeUpdatedAt || '-' },
      { label: 'پاداش', value: row.bonusAmount },
      { label: 'جریمه', value: row.penaltyAmount },
      { label: 'خالص پاداش/جریمه', value: row.netAdjustment },
    ]
  }
  return [
    { label: 'کد', value: row.id },
    { label: 'عنوان', value: row.title },
    { label: 'ثبت‌کننده', value: row.owner },
    { label: 'مدیر', value: row.manager },
    { label: 'واحد', value: row.department },
    { label: 'اولویت', value: row.priority },
    { label: 'وضعیت', value: row.status },
    { label: 'تاریخ ثبت', value: row.createdAt },
  ]
})

function decisionText(item) {
  if (activeTab.value === 'users') return item.netAdjustment || '-'
  const decisions = item.decisions || []
  return decisions.length ? decisions.map((row) => `${row.approver}: ${row.statusLabel}`).join(' | ') : '-'
}

function openReportDetails(row) {
  selectedReportType.value = activeTab.value
  selectedReportRow.value = row
}

function closeReportDetails() {
  selectedReportRow.value = null
  selectedReportType.value = ''
}

function rowFileUrl(row = selectedReportRow.value) {
  if (!row) return ''
  if (selectedReportType.value === 'users') return ''
  return row.invoiceUrl || row.previewUrl || row.downloadUrl || ''
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
    <PageHeader
      eyebrow="گزارشات"
      title="گزارش‌های مدیریتی و خروجی‌ها"
      description="نمای تفکیکی گزارش در درخواست‌ها، هزینه‌ها و تاییدها با خروجی مستقیم."
    />

    <section class="surface-block report-controls">
      <div class="report-tabs">
        <button v-for="tab in tabs" :key="tab.key" :class="['report-tab', activeTab === tab.key && 'is-active']" type="button" @click="activeTab = tab.key">
          <IconlyIcon :name="tab.icon" decorative />
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <div class="report-filter-grid">
        <div class="chip-row report-period-chips">
          <button v-for="item in periods" :key="item.key" :class="['filter-chip', filters.period === item.key && 'is-active']" type="button" @click="filters.period = item.key">
            {{ item.label }}
          </button>
        </div>
        <label class="report-filter-field">
          <span class="report-filter-label">شخص</span>
          <select v-model="filters.userId" class="report-filter-control">
            <option value="">همه افراد</option>
            <option v-for="user in reportUsers" :key="user.id" :value="user.id">{{ user.name }}</option>
          </select>
        </label>
        <template v-if="filters.period === 'custom'">
          <label class="report-filter-field">
            <span class="report-filter-label">از تاریخ</span>
            <ShamsiDatePicker v-model="filters.startDate" model-type="jalali" />
          </label>
          <label class="report-filter-field">
            <span class="report-filter-label">تا تاریخ</span>
            <ShamsiDatePicker v-model="filters.endDate" model-type="jalali" />
          </label>
        </template>
        <button class="action-btn tone-primary report-export-btn" type="button" @click="exportActiveTab">
          <IconlyIcon name="download" decorative />
          <span>دانلود جدول</span>
        </button>
      </div>
    </section>

    <section class="surface-block report-table-card">
      <div class="section-label-row">
        <SectionHeading
          :title="tabs.find((item) => item.key === activeTab)?.label || 'گزارش'"
          :description="`${activeRows.length} ردیف در این خروجی نمایش داده می‌شود.`"
        />
        <span class="meta-pill">{{ activeRows.length }} ردیف</span>
      </div>

      <div class="report-table-wrap">
        <table class="report-table">
          <thead>
            <tr v-if="activeTab === 'requests'"><th>کد</th><th>عنوان</th><th>ثبت‌کننده</th><th>مدیر</th><th>واحد</th><th>وضعیت</th><th>اولویت</th><th>تاریخ</th><th>تصمیم‌ها</th></tr>
            <tr v-else-if="activeTab === 'expenses'"><th>کد</th><th>شرح</th><th>ثبت‌کننده</th><th>مبلغ</th><th>واحد</th><th>وضعیت</th><th>تاریخ</th><th>تصمیم‌ها</th></tr>
            <tr v-else-if="activeTab === 'approvals'"><th>کد</th><th>عنوان</th><th>ثبت‌کننده</th><th>نوع</th><th>واحد</th><th>ریسک</th><th>وضعیت</th><th>تاریخ</th><th>تصمیم‌ها</th></tr>
            <tr v-else><th>شناسه</th><th>نام</th><th>نام کاربری</th><th>نقش</th><th>واحد</th><th>مدیر</th><th>پاداش</th><th>جریمه</th><th>خالص</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in activeRows" :key="row.id" class="report-click-row" tabindex="0" @click="openReportDetails(row)" @keydown.enter.prevent="openReportDetails(row)" @keydown.space.prevent="openReportDetails(row)">
              <template v-if="activeTab === 'requests'"><td>{{ row.id }}</td><td>{{ row.title }}</td><td>{{ row.owner }}</td><td>{{ row.manager }}</td><td>{{ row.department }}</td><td>{{ row.status }}</td><td>{{ row.priority }}</td><td>{{ row.createdAt }}</td><td>{{ decisionText(row) }}</td></template>
              <template v-else-if="activeTab === 'expenses'"><td>{{ row.id }}</td><td>{{ row.description }}</td><td>{{ row.owner }}</td><td>{{ row.amount }}</td><td>{{ row.department }}</td><td>{{ row.status }}</td><td>{{ row.submittedAt }}</td><td>{{ decisionText(row) }}</td></template>
              <template v-else-if="activeTab === 'approvals'"><td>{{ row.id }}</td><td>{{ row.title }}</td><td>{{ row.owner }}</td><td>{{ row.type }}</td><td>{{ row.department }}</td><td>{{ row.risk }}</td><td>{{ row.status }}</td><td>{{ row.uploadedAt }}</td><td>{{ decisionText(row) }}</td></template>
              <template v-else><td>{{ row.id }}</td><td>{{ row.name }}</td><td>{{ row.username }}</td><td>{{ row.role }}</td><td>{{ row.department }}</td><td>{{ row.manager }}</td><td>{{ row.bonusAmount }}</td><td>{{ row.penaltyAmount }}</td><td>{{ row.netAdjustment }}</td></template>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <BaseModal :open="!!selectedReportRow" size="detail" @close="closeReportDetails">
      <article v-if="selectedReportRow" class="report-detail-modal">
        <header class="report-detail-hero">
          <div class="report-detail-icon">
            <IconlyIcon :name="selectedTabMeta.icon" decorative />
          </div>
          <div class="report-detail-title">
            <span class="page-eyebrow">{{ selectedTabMeta.label }}</span>
            <h2>{{ selectedDetailTitle }}</h2>
            <p>{{ selectedDetailSubtitle }}</p>
          </div>
          <span class="report-detail-code">{{ selectedReportRow.id }}</span>
        </header>

        <section class="report-detail-metrics">
          <article v-for="item in selectedPrimaryMetrics" :key="item.label" class="report-detail-metric">
            <IconlyIcon :name="item.icon" decorative />
            <small>{{ item.label }}</small>
            <strong>{{ item.value }}</strong>
          </article>
        </section>

        <section class="report-detail-grid">
          <article v-for="field in selectedDetailFields" :key="field.label" :class="['report-detail-field', field.wide && 'is-wide']">
            <span>{{ field.label }}</span>
            <strong>{{ field.value || '-' }}</strong>
          </article>
        </section>

        <section v-if="selectedReportType !== 'users'" class="report-detail-decisions">
          <div class="section-label-row">
            <SectionHeading
              title="تصمیمات و گردش تایید"
              description="مسیر تایید، ارجاع و تصمیم‌های ثبت‌شده برای این ردیف گزارش."
            />
            <span class="meta-pill">{{ (selectedReportRow.decisions || []).length }} مورد</span>
          </div>
          <div v-if="(selectedReportRow.decisions || []).length" class="decision-timeline">
            <article v-for="decision in selectedReportRow.decisions" :key="`${decision.approver}-${decision.statusLabel}`" class="decision-step">
              <span class="decision-dot"></span>
              <div>
                <strong>{{ decision.approver || 'نامشخص' }}</strong>
                <small>{{ decision.statusLabel || '-' }}</small>
              </div>
            </article>
          </div>
          <div v-else class="empty-state-inline compact-empty">
            <IconlyIcon name="pending_actions" decorative />
            <p>تصمیمی برای این مورد ثبت نشده است.</p>
          </div>
        </section>

        <footer class="report-detail-actions">
          <a v-if="rowFileUrl()" class="action-btn tone-primary" :href="rowFileUrl()" target="_blank" rel="noreferrer">
            <IconlyIcon name="open_in_new" decorative />
            <span>مشاهده فایل</span>
          </a>
          <button class="action-btn tone-soft" type="button" @click="closeReportDetails">
            <IconlyIcon name="close" decorative />
            <span>بستن</span>
          </button>
        </footer>
      </article>
    </BaseModal>
  </section>

  <section v-else class="page-shell"><article class="access-denied-card"><h2>دسترسی گزارشات ندارید</h2></article></section>
</template>

<style scoped>
.reports-page { gap: 16px; }
.report-controls { display: grid; gap: 14px; }
.report-tabs,
.report-filter-grid {
  display: flex;
  align-items: end;
  gap: 10px;
  flex-wrap: wrap;
}
.report-tab {
  min-height: 34px;
  border: 0;
  border-radius: 10px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #1f5c59;
  background: #e4f4f2;
  font-weight: 700;
  font-size: 0.8rem;
  cursor: pointer;
}
.report-tab.is-active {
  color: #fff;
  background: #34908B;
}
.report-period-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 36px;
}
.report-filter-field {
  display: grid;
  grid-template-rows: 18px 36px;
  gap: 6px;
  min-width: 180px;
  margin: 0;
}
.report-filter-label {
  display: inline-flex;
  align-items: center;
  height: 18px;
  font-size: 11px;
  font-weight: 700;
  color: #45605c;
}
.report-filter-control {
  box-sizing: border-box;
  width: 100%;
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
  padding: 0 12px !important;
  border: 0 !important;
  border-radius: 10px !important;
  background: #e4f4f2 !important;
  color: #152523;
  font: inherit;
  font-size: 0.82rem;
}
.report-filter-field :deep(.shamsi-picker),
.report-filter-field :deep(.shamsi-picker-input-wrap) {
  width: 100%;
  height: 36px !important;
  min-height: 36px !important;
  max-height: 36px !important;
}
.report-filter-field :deep(.shamsi-picker-input-wrap) {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  padding-inline: 12px 36px !important;
  padding-block: 0 !important;
  border-radius: 10px !important;
  background: #e4f4f2 !important;
}
.report-filter-field :deep(.shamsi-picker-input) {
  height: 100% !important;
  min-height: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  line-height: 36px;
}
.report-filter-field :deep(.shamsi-picker-toggle) {
  position: absolute;
  inset-inline-end: 5px;
  top: 50%;
  transform: translateY(-50%);
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: #f3f9f7 !important;
}
.report-export-btn {
  height: 36px !important;
  min-height: 36px !important;
  align-self: end;
}
.compact-field { min-width: 190px; margin: 0; }
.report-table-wrap { overflow-x: auto; }
.report-table { width: 100%; min-width: 980px; border-collapse: collapse; }
.report-table th, .report-table td { padding: 12px 10px; border-bottom: 1px solid rgba(38,56,92,.08); text-align: right; vertical-align: top; }
.report-table th { color: #52607a; font-size: 12px; }
.report-table td { color: #203255; line-height: 1.7; }
.report-click-row {
  cursor: pointer;
  outline: 0;
  transition: background-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}
.report-click-row:hover,
.report-click-row:focus-visible {
  background: rgba(52, 144, 139, 0.08);
  box-shadow: none;
}
.report-detail-modal {
  display: grid;
  gap: 18px;
  padding: 4px;
}
.report-detail-hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: start;
  padding: 22px;
  border-radius: 8px;
  background: var(--surface, #fff);
  color: #fff;
  box-shadow: none;
}
.report-detail-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.report-detail-icon span { font-size: 30px; }
.report-detail-title {
  display: grid;
  gap: 7px;
  min-width: 0;
}
.report-detail-title h2,
.report-detail-title p {
  margin: 0;
}
.report-detail-title h2 {
  font-size: clamp(22px, 2vw, 32px);
  line-height: 1.35;
  overflow-wrap: anywhere;
}
.report-detail-title p {
  color: rgba(255, 255, 255, 0.76);
  line-height: 1.9;
  overflow-wrap: anywhere;
}
.report-detail-code {
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.14);
  font-weight: 900;
  direction: ltr;
}
.report-detail-metrics,
.report-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.report-detail-metric,
.report-detail-field,
.report-detail-decisions {
  border: 1px solid rgba(38, 56, 92, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: none;
}
.report-detail-metric {
  min-height: 112px;
  display: grid;
  align-content: center;
  gap: 6px;
  padding: 16px;
}
.report-detail-metric span {
  color: var(--primary);
  font-size: 28px;
}
.report-detail-metric small,
.report-detail-field span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}
.report-detail-metric strong,
.report-detail-field strong {
  color: #203255;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
.report-detail-field {
  display: grid;
  gap: 7px;
  padding: 14px 16px;
}
.report-detail-field.is-wide {
  grid-column: 1 / -1;
}
.report-detail-decisions {
  display: grid;
  gap: 12px;
  padding: 16px;
}
.decision-timeline {
  display: grid;
  gap: 10px;
}
.decision-step {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: start;
  min-width: 0;
  padding: 12px;
  border-radius: 8px;
  background: rgba(246, 248, 252, 0.9);
}
.decision-dot {
  width: 12px;
  height: 12px;
  margin-top: 7px;
  border-radius: 999px;
  background: var(--primary);
  box-shadow: none;
}
.decision-step strong,
.decision-step small {
  display: block;
  overflow-wrap: anywhere;
}
.decision-step small {
  margin-top: 4px;
  color: var(--muted);
}
.compact-empty {
  padding: 12px;
}
.report-detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}
@media (max-width: 760px) {
  .report-filter-grid,
  .report-tabs,
  .report-detail-hero {
    display: grid;
    grid-template-columns: 1fr;
  }
  .report-detail-metrics,
  .report-detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .compact-field,
  .action-btn,
  .report-detail-actions {
    width: 100%;
  }
  .report-detail-hero {
    padding: 18px;
  }
  .report-detail-actions {
    justify-content: stretch;
  }
}
@media (max-width: 420px) {
  .report-detail-metrics,
  .report-detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
