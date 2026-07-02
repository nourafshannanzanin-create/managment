<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import FilterDialog from '../components/FilterDialog.vue'
import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, formatMetric, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const filterOpen = ref(false)
const { exportReport, filteredReports, loadReports, navigateTo, reportPeople, resetPageFilters, state, updatePageFilter, visibleNavItems } = useWorkflowHub()
const reportFilters = computed(() => state.filters.reports)

function filterSummary() {
  const parts = []
  if (reportFilters.value.query) parts.push(`جستجو: ${reportFilters.value.query}`)
  if (reportFilters.value.person) parts.push(`شخص: ${reportFilters.value.person}`)
  if (reportFilters.value.startDate) parts.push(`از: ${reportFilters.value.startDate}`)
  if (reportFilters.value.endDate) parts.push(`تا: ${reportFilters.value.endDate}`)
  return parts.join(' | ') || 'برای فیلتر کلیک کنید'
}

function applyFilters(filters) {
  Object.entries(filters).forEach(([key, value]) => updatePageFilter('reports', key, value))
  filterOpen.value = false
}

function resetFilters() {
  resetPageFilters('reports')
}

function bindReportCard(card, report) {
  if (!card) return

  card.style.display = report ? '' : 'none'
  if (!report) return

  const title = card.querySelector('span.text-on-surface')
  if (title) title.textContent = report.title

  const button = card.querySelector('button')
  if (button) {
    button.onclick = async () => {
      await exportReport(report.id, 'csv')
    }
  }
}

function hydrate(root) {
  const searchInput = root.querySelector('input[type="text"]')
  if (searchInput) {
    searchInput.readOnly = true
    searchInput.value = filterSummary()
    searchInput.placeholder = 'برای فیلتر کلیک کنید'
    searchInput.onclick = () => { filterOpen.value = true }
  }

  const filterPanel = root.querySelector('.bg-surface-container-low')
  if (filterPanel) filterPanel.onclick = () => { filterOpen.value = true }

  const statValues = root.querySelectorAll('.font-stat-value')
  if (statValues[0]) statValues[0].textContent = formatMetric(state.reportSummary?.expenseTotal)
  if (statValues[1]) statValues[1].textContent = String(state.reportSummary?.users || 0)
  if (statValues[2]) statValues[2].textContent = String(state.reportSummary?.requests || 0)

  const exportCards = root.querySelectorAll('section.space-y-3 .grid > div')
  Array.from(exportCards).forEach((card, index) => bindReportCard(card, filteredReports.value[index]))

  const listGroups = root.querySelectorAll('.space-y-4')
  const spenders = listGroups[listGroups.length - 1]
  if (spenders) {
    const maxAmount = Math.max(...state.topSubmitters.map((item) => Number(item.count || 0)), 0)
    spenders.innerHTML = state.topSubmitters.map((item, index) => `
      <div class="flex flex-row-reverse items-center gap-4 group">
        <div class="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-label-sm text-label-sm">${index + 1}</div>
        <div class="flex-1 flex flex-row-reverse justify-between items-center">
          <span class="text-on-surface font-body-md text-body-md">${escapeHtml(item.name)} - ${escapeHtml(item.amount || '0')}</span>
          <div class="w-16 h-1 bg-surface-container rounded-full overflow-hidden">
            <div class="h-full bg-primary" style="width:${Math.max(25, maxAmount > 0 ? (Number(item.count || 0) / maxAmount) * 100 : 0)}%"></div>
          </div>
        </div>
      </div>
    `).join('') || '<div class="text-on-surface-variant">داده‌ای برای نمایش وجود ندارد.</div>'
  }

  wirePageNavigation(root, navigateTo, '/reports', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

onMounted(() => {
  loadReports(true)
})

watch(() => [state.reportSummary, state.topSubmitters, filteredReports.value, state.filters.reports], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage v-if="state.currentUser.canViewReports" ref="runtime" stitch-id="_3" @ready="hydrate" />
  <section v-else class="page-shell" style="padding: 32px;">
    دسترسی به گزارشات فقط برای مدیرعامل فعال است.
  </section>
  <FilterDialog
    v-if="state.currentUser.canViewReports"
    :open="filterOpen"
    title="فیلتر گزارشات"
    :filters="reportFilters"
    :people="reportPeople"
    @close="filterOpen = false"
    @apply="applyFilters"
    @reset="resetFilters"
  />
</template>
