<script setup>
import { computed, ref, watch } from 'vue'

import FilterDialog from '../components/FilterDialog.vue'
import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, priorityTone, statusTone, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const filterOpen = ref(false)
const {
  filteredRequests,
  navigateTo,
  openRequestComposer,
  openRequestDetail,
  requestPeople,
  resetPageFilters,
  state,
  updatePageFilter,
  visibleNavItems,
} = useWorkflowHub()

const requestFilters = computed(() => state.filters.requests)

function renderRequestCard(item) {
  return `
    <div class="glass-card rounded-2xl p-card-padding space-y-4">
      <div class="flex justify-between items-start">
        <div class="space-y-1">
          <span class="text-label-sm font-label-sm text-primary tracking-wider">${escapeHtml(item.id)}</span>
          <h3 class="font-headline-md text-[18px] text-on-surface">${escapeHtml(item.title)}</h3>
        </div>
        <span class="${statusTone(item.status)} px-3 py-1 rounded-lg text-label-sm font-label-sm">${escapeHtml(item.status)}</span>
      </div>
      <div class="grid grid-cols-2 gap-4 pt-2 border-t border-outline-variant/10">
        <div class="space-y-1">
          <p class="text-on-surface-variant text-[11px] font-label-sm">- ثبت‌کننده -</p>
          <p class="text-on-surface text-label-sm font-label-sm">${escapeHtml(item.owner)}</p>
        </div>
        <div class="space-y-1">
          <p class="text-on-surface-variant text-[11px] font-label-sm">اولویت</p>
          <span class="text-on-surface-variant text-label-sm font-label-sm flex items-center gap-1">
            <span class="w-2 h-2 rounded-full ${priorityTone(item.priority)}"></span>
            ${escapeHtml(item.priority)}
          </span>
        </div>
        <div class="space-y-1">
          <p class="text-on-surface-variant text-[11px] font-label-sm">تاریخ</p>
          <p class="text-on-surface text-label-sm font-label-sm">${escapeHtml(item.createdAt || item.deadline || '-')}</p>
        </div>
        <div class="space-y-1">
          <p class="text-on-surface-variant text-[11px] font-label-sm">بخش</p>
          <p class="text-on-surface text-label-sm font-label-sm">${escapeHtml(item.department)}</p>
        </div>
      </div>
      <button class="text-primary font-label-sm text-label-sm flex items-center gap-1 request-detail-btn" data-request-id="${escapeHtml(item.id)}">
        مشاهده جزئیات
        <span class="material-symbols-outlined text-[16px]">arrow_back</span>
      </button>
    </div>
  `
}

function filterSummary() {
  const parts = []
  if (requestFilters.value.query) parts.push(`جستجو: ${requestFilters.value.query}`)
  if (requestFilters.value.person) parts.push(`شخص: ${requestFilters.value.person}`)
  if (requestFilters.value.startDate) parts.push(`از: ${requestFilters.value.startDate}`)
  if (requestFilters.value.endDate) parts.push(`تا: ${requestFilters.value.endDate}`)
  return parts.join(' | ') || 'برای فیلتر کلیک کنید'
}

function openFilterModal() {
  filterOpen.value = true
}

function applyFilters(filters) {
  Object.entries(filters).forEach(([key, value]) => updatePageFilter('requests', key, value))
  filterOpen.value = false
}

function resetFilters() {
  resetPageFilters('requests')
}

function hydrate(root) {
  const addButton = root.querySelector('section button.bg-primary')
  if (addButton) addButton.onclick = () => openRequestComposer()

  const searchInput = root.querySelector('input[type="text"]')
  if (searchInput) {
    searchInput.readOnly = true
    searchInput.value = filterSummary()
    searchInput.placeholder = 'برای فیلتر کلیک کنید'
    searchInput.onclick = () => openFilterModal()
  }

  const filterArea = root.querySelector('section.space-y-3')
  if (filterArea) filterArea.onclick = () => openFilterModal()

  const countLabel = root.querySelector('section.space-y-4 .text-on-surface-variant.font-label-sm')
  if (countLabel) countLabel.textContent = `${filteredRequests.value.length} ردیف یافت شد`

  const sections = root.querySelectorAll('main > section')
  const listSection = sections[2]
  if (listSection) {
    const header = listSection.firstElementChild?.outerHTML || ''
    listSection.innerHTML = `${header}${filteredRequests.value.map(renderRequestCard).join('') || '<div class="glass-card rounded-2xl p-card-padding text-on-surface-variant">درخواستی یافت نشد.</div>'}`
    listSection.querySelectorAll('.request-detail-btn').forEach((button) => {
      button.onclick = () => openRequestDetail(button.dataset.requestId)
    })
  }

  wirePageNavigation(root, navigateTo, '/requests', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

watch(() => [filteredRequests.value, state.filters.requests], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage ref="runtime" stitch-id="_7" @ready="hydrate" />
  <FilterDialog
    :open="filterOpen"
    title="فیلتر درخواست‌ها"
    :filters="requestFilters"
    :people="requestPeople"
    @close="filterOpen = false"
    @apply="applyFilters"
    @reset="resetFilters"
  />
</template>
