<script setup>
import { computed, ref, watch } from 'vue'

import FilterDialog from '../components/FilterDialog.vue'
import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, statusTone, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const filterOpen = ref(false)
const {
  approvalHistory,
  approvalInbox,
  approvalPeople,
  navigateTo,
  openApprovalDetail,
  openDocumentComposer,
  openSignatureComposer,
  resetPageFilters,
  signatureState,
  state,
  updatePageFilter,
  visibleNavItems,
} = useWorkflowHub()

const approvalFilters = computed(() => state.filters.approvals)

function renderApprovalCard(item, history = false) {
  return `
    <div class="bg-surface-container-lowest p-card-padding rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-outline-variant/10 relative overflow-hidden group">
      <div class="absolute top-0 right-0 w-1.5 h-full ${history ? 'bg-primary' : 'bg-error'}"></div>
      <div class="flex justify-between items-start mb-4">
        <div class="space-y-1">
          <span class="font-label-sm text-label-sm text-on-surface-variant/70 block">شناسه سند</span>
          <code class="font-label-sm text-label-sm font-bold text-primary tracking-wider">${escapeHtml(item.id)}</code>
        </div>
        <div class="${statusTone(item.status)} px-3 py-1 rounded-full font-label-sm text-label-sm">${escapeHtml(item.status)}</div>
      </div>
      <div class="space-y-1">
        <span class="font-label-sm text-label-sm text-on-surface-variant/70 block">عنوان سند</span>
        <p class="font-body-md text-body-md text-on-surface font-semibold">${escapeHtml(item.title)}</p>
      </div>
      <div class="mt-6 pt-4 border-t border-outline-variant/10 flex justify-between items-center">
        <span class="font-label-sm text-label-sm text-on-surface-variant">${escapeHtml(item.owner)} · ${escapeHtml(item.department)}</span>
        <button class="text-primary font-label-sm text-label-sm flex items-center gap-1 approval-detail-btn" data-approval-id="${escapeHtml(item.id)}">
          مشاهده جزئیات
          <span class="material-symbols-outlined text-[16px]">chevron_left</span>
        </button>
      </div>
    </div>
  `
}

function filterSummary() {
  const parts = []
  if (approvalFilters.value.query) parts.push(`جستجو: ${approvalFilters.value.query}`)
  if (approvalFilters.value.person) parts.push(`شخص: ${approvalFilters.value.person}`)
  if (approvalFilters.value.startDate) parts.push(`از: ${approvalFilters.value.startDate}`)
  if (approvalFilters.value.endDate) parts.push(`تا: ${approvalFilters.value.endDate}`)
  return parts.join(' | ') || 'برای فیلتر کلیک کنید'
}

function applyFilters(filters) {
  Object.entries(filters).forEach(([key, value]) => updatePageFilter('approvals', key, value))
  filterOpen.value = false
}

function resetFilters() {
  resetPageFilters('approvals')
}

function hydrate(root) {
  const buttons = root.querySelectorAll('section.grid button')
  if (buttons[0]) buttons[0].onclick = () => openDocumentComposer()
  if (buttons[1]) buttons[1].onclick = () => openSignatureComposer()

  const searchInput = root.querySelector('input[type="text"]')
  if (searchInput) {
    searchInput.readOnly = true
    searchInput.value = filterSummary()
    searchInput.placeholder = 'برای فیلتر کلیک کنید'
    searchInput.onclick = () => { filterOpen.value = true }
  }

  const filterSection = root.querySelector('section.bg-surface-container-lowest')
  if (filterSection) filterSection.onclick = () => { filterOpen.value = true }

  const warning = root.querySelector('.bg-primary\\/5 p.font-label-sm')
  if (warning) warning.textContent = signatureState.hasSignature ? 'امضای دیجیتال شما ثبت شده و آماده استفاده است.' : 'برای تایید اسناد ابتدا امضای خود را در پنل کاربری ثبت کنید.'

  const sections = root.querySelectorAll('main > section')
  const pendingSection = sections[3]
  if (pendingSection) {
    const header = pendingSection.firstElementChild?.outerHTML || ''
    pendingSection.innerHTML = `${header}${approvalInbox.value.length ? approvalInbox.value.map((item) => renderApprovalCard(item)).join('') : '<div class="flex flex-col items-center justify-center py-12 bg-white rounded-xl border-2 border-dashed border-outline-variant/30 text-on-surface-variant"><span class="material-symbols-outlined text-5xl opacity-20 mb-3">history_edu</span><p class="font-body-md text-body-md">هیچ موردی برای تایید وجود ندارد</p></div>'}`
  }

  const historySection = sections[4]
  if (historySection) {
    const header = historySection.firstElementChild?.outerHTML || ''
    historySection.innerHTML = `${header}${approvalHistory.value.map((item) => renderApprovalCard(item, true)).join('') || '<div class="bg-surface-container-lowest p-card-padding rounded-xl text-on-surface-variant">تاریخچه‌ای موجود نیست.</div>'}`
  }

  root.querySelectorAll('.approval-detail-btn').forEach((button) => {
    button.onclick = () => openApprovalDetail(button.dataset.approvalId)
  })

  wirePageNavigation(root, navigateTo, '/approvals', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

watch(() => [approvalInbox.value, approvalHistory.value, signatureState.hasSignature, state.filters.approvals], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage ref="runtime" stitch-id="_6" @ready="hydrate" />
  <FilterDialog
    :open="filterOpen"
    title="فیلتر تاییدها"
    :filters="approvalFilters"
    :people="approvalPeople"
    @close="filterOpen = false"
    @apply="applyFilters"
    @reset="resetFilters"
  />
</template>
