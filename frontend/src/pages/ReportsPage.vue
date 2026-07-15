<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import PageHeader from '../components/PageHeader.vue'
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
  { key: 'requests', label: '???????', icon: 'assignment' },
  { key: 'expenses', label: '????? ??', icon: 'payments' },
  { key: 'approvals', label: '??????? ??', icon: 'fact_check' },
  { key: 'users', label: '???????', icon: 'groups' },
]

const periods = [
  { key: 'today', label: '?????' },
  { key: 'week', label: '??? ????' },
  { key: 'month', label: '??? ???' },
  { key: 'year', label: '?????' },
  { key: 'custom', label: '????' },
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
  return row.title || row.description || row.id || '?????? ?????'
})

const selectedDetailSubtitle = computed(() => {
  const row = selectedReportRow.value
  if (!row) return ''
  if (selectedReportType.value === 'expenses') return joinDisplayParts([row.owner, row.department, row.submittedAt], ' � ')
  if (selectedReportType.value === 'approvals') return joinDisplayParts([row.owner, row.type, row.uploadedAt], ' � ')
  if (selectedReportType.value === 'users') return joinDisplayParts([row.role, row.department, row.financeUpdatedAt || row.joinedAt], ' � ')
  return joinDisplayParts([row.owner, row.manager, row.createdAt], ' � ')
})

const selectedPrimaryMetrics = computed(() => {
  const row = selectedReportRow.value
  if (!row) return []
  if (selectedReportType.value === 'expenses') {
    return [
      { label: '????', value: row.amount || '-', icon: 'payments' },
      { label: '?????', value: row.status || '-', icon: 'verified' },
      { label: '???', value: row.department || '-', icon: 'apartment' },
    ]
  }
  if (selectedReportType.value === 'approvals') {
    return [
      { label: '????', value: row.risk || '-', icon: 'warning' },
      { label: '?????', value: row.status || '-', icon: 'fact_check' },
      { label: '??? ???', value: row.type || '-', icon: 'description' },
    ]
  }
  if (selectedReportType.value === 'users') {
    return [
      { label: '?????', value: row.bonusAmount || '-', icon: 'award_star' },
      { label: '?????', value: row.penaltyAmount || '-', icon: 'gavel' },
      { label: '????', value: row.netAdjustment || '-', icon: 'balance' },
    ]
  }
  return [
    { label: '??????', value: row.priority || '-', icon: 'priority_high' },
    { label: '?????', value: row.status || '-', icon: 'verified' },
    { label: '???', value: row.department || '-', icon: 'apartment' },
  ]
})

const selectedDetailFields = computed(() => {
  const row = selectedReportRow.value
  if (!row) return []
  if (selectedReportType.value === 'expenses') {
    return [
      { label: '??', value: row.id },
      { label: '??? ?????', value: row.owner },
      { label: '????? ???', value: row.submittedAt || row.createdAt },
      { label: '???', value: row.department },
      { label: '?????', value: row.status },
      { label: '????', value: row.amount },
      { label: '???', value: row.description, wide: true },
    ]
  }
  if (selectedReportType.value === 'approvals') {
    return [
      { label: '??', value: row.id },
      { label: '?????', value: row.title },
      { label: '??? ?????', value: row.owner },
      { label: '???', value: row.type },
      { label: '???', value: row.department },
      { label: '????', value: row.risk },
      { label: '?????', value: row.status },
      { label: '????? ????????', value: row.uploadedAt },
    ]
  }
  if (selectedReportType.value === 'users') {
    return [
      { label: '?????', value: row.id },
      { label: '???', value: row.name },
      { label: '??? ??????', value: row.username },
      { label: '???', value: row.role },
      { label: '????? ????', value: row.jobTitle },
      { label: '???', value: row.department },
      { label: '???? ??????', value: row.manager },
      { label: '?????', value: row.status },
      { label: '????? ?????', value: row.joinedAt },
      { label: '????? ??? ????', value: row.financeUpdatedAt || '-' },
      { label: '?????', value: row.bonusAmount },
      { label: '?????', value: row.penaltyAmount },
      { label: '???? ?????/?????', value: row.netAdjustment },
    ]
  }
  return [
    { label: '??', value: row.id },
    { label: '?????', value: row.title },
    { label: '??? ?????', value: row.owner },
    { label: '????', value: row.manager },
    { label: '???', value: row.department },
    { label: '??????', value: row.priority },
    { label: '?????', value: row.status },
    { label: '????? ???', value: row.createdAt },
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
    <PageHeader eyebrow="???????" title="????? ??????" description="" />

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
          <span>?????</span>
          <select v-model="filters.userId">
            <option value="">??? ???????</option>
            <option v-for="user in reportUsers" :key="user.id" :value="user.id">{{ user.name }}</option>
          </select>
        </label>
        <template v-if="filters.period === 'custom'">
          <label class="field-shell compact-field"><span>?? ?????</span><ShamsiDatePicker v-model="filters.startDate" model-type="jalali" /></label>
          <label class="field-shell compact-field"><span>?? ?????</span><ShamsiDatePicker v-model="filters.endDate" model-type="jalali" /></label>
        </template>
        <button class="action-btn tone-primary" type="button" @click="exportActiveTab">
          <span class="material-symbols-outlined">download</span>
          <span>?????? ????</span>
        </button>
      </div>
    </section>

    <section class="surface-block report-table-card">
      <div class="section-label-row">
        <div><h3>{{ tabs.find((item) => item.key === activeTab)?.label }}</h3></div>
        <span class="meta-pill">{{ activeRows.length }} ????</span>
      </div>

      <div class="report-table-wrap">
        <table class="report-table">
          <thead>
            <tr v-if="activeTab === 'requests'"><th>??</th><th>?????</th><th>??? ?????</th><th>????</th><th>???</th><th>?????</th><th>??????</th><th>?????</th><th>????? ??</th></tr>
            <tr v-else-if="activeTab === 'expenses'"><th>??</th><th>???</th><th>??? ?????</th><th>????</th><th>???</th><th>?????</th><th>?????</th><th>????? ??</th></tr>
            <tr v-else-if="activeTab === 'approvals'"><th>??</th><th>?????</th><th>??? ?????</th><th>???</th><th>???</th><th>????</th><th>?????</th><th>?????</th><th>????? ??</th></tr>
            <tr v-else><th>?????</th><th>???</th><th>??? ??????</th><th>???</th><th>???</th><th>????</th><th>?????</th><th>?????</th><th>????</th></tr>
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
            <span class="material-symbols-outlined">{{ selectedTabMeta.icon }}</span>
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
            <span class="material-symbols-outlined">{{ item.icon }}</span>
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
            <div><h3>???????? ? ???? ?????</h3></div>
            <span class="meta-pill">{{ (selectedReportRow.decisions || []).length }} ????</span>
          </div>
          <div v-if="(selectedReportRow.decisions || []).length" class="decision-timeline">
            <article v-for="decision in selectedReportRow.decisions" :key="`${decision.approver}-${decision.statusLabel}`" class="decision-step">
              <span class="decision-dot"></span>
              <div>
                <strong>{{ decision.approver || '???? ???' }}</strong>
                <small>{{ decision.statusLabel || '-' }}</small>
              </div>
            </article>
          </div>
          <div v-else class="empty-state-inline compact-empty">
            <span class="material-symbols-outlined">pending_actions</span>
            <p>?????? ???? ??? ???? ??? ???? ???.</p>
          </div>
        </section>

        <footer class="report-detail-actions">
          <a v-if="rowFileUrl()" class="action-btn tone-primary" :href="rowFileUrl()" target="_blank" rel="noreferrer">
            <span class="material-symbols-outlined">open_in_new</span>
            <span>?????? ????</span>
          </a>
          <button class="action-btn tone-soft" type="button" @click="closeReportDetails">
            <span class="material-symbols-outlined">close</span>
            <span>????</span>
          </button>
        </footer>
      </article>
    </BaseModal>
  </section>

  <section v-else class="page-shell"><article class="access-denied-card"><h2>?????? ????? ??????</h2></article></section>
</template>

<style scoped>
.reports-page { gap: 16px; }
.report-controls { display: grid; gap: 16px; }
.report-tabs, .report-filter-grid { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.report-tab { min-height: 44px; border: 0; border-radius: 14px; padding: 0 14px; display: inline-flex; align-items: center; gap: 8px; color: #31405f; background: rgba(72,103,183,.09); font-weight: 900; cursor: pointer; }
.report-tab.is-active { color: #fff; background: var(--surface, #fff); }
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
  background: rgba(72, 103, 183, 0.07);
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
