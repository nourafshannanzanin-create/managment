<script setup>
import { computed, ref, watch } from 'vue'

import FilterDialog from '../components/FilterDialog.vue'
import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, statusTone, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const filterOpen = ref(false)
const {
  expensePeople,
  filteredExpenses,
  navigateTo,
  openExpenseComposer,
  resetPageFilters,
  state,
  updatePageFilter,
  visibleNavItems,
} = useWorkflowHub()

const expenseFilters = computed(() => state.filters.expenses)

function renderExpenseCard(item) {
  const invoiceLabel = item.invoiceUrl ? 'مشاهده فاکتور' : 'بدون فاکتور'
  return `
    <div class="bg-surface-container-lowest rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-outline-variant/10 overflow-hidden">
      <div class="p-card-padding flex flex-col gap-4">
        <div class="flex justify-between items-start">
          <div>
            <span class="text-primary font-label-sm text-label-sm tracking-widest block mb-1">${escapeHtml(item.id)}</span>
            <h3 class="font-headline-md text-headline-md text-on-surface">${escapeHtml(item.title || item.description)}</h3>
          </div>
          <span class="${statusTone(item.status)} px-3 py-1 rounded-full font-label-sm text-label-sm">${escapeHtml(item.status)}</span>
        </div>
        <div class="grid grid-cols-2 gap-y-4 py-4 border-y border-outline-variant/10">
          <div><p class="text-on-surface-variant font-label-sm text-label-sm">- ثبت‌کننده -</p><p class="font-body-md text-on-surface mt-1">${escapeHtml(item.owner)}</p></div>
          <div><p class="text-on-surface-variant font-label-sm text-label-sm">بخش</p><p class="font-body-md text-on-surface mt-1">${escapeHtml(item.department)}</p></div>
          <div><p class="text-on-surface-variant font-label-sm text-label-sm">تاریخ</p><p class="font-body-md text-on-surface mt-1">${escapeHtml(item.createdAt)}</p></div>
          <div><p class="text-on-surface-variant font-label-sm text-label-sm">مبلغ</p><p class="font-headline-md text-headline-md text-primary mt-1">${escapeHtml(item.amount)}</p></div>
        </div>
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-2 text-on-surface-variant">
            <span class="material-symbols-outlined text-sm">description</span>
            ${item.invoiceUrl ? `<a class="font-label-sm text-label-sm text-primary" href="${escapeHtml(item.invoiceUrl)}" target="_blank" rel="noreferrer">${invoiceLabel}</a>` : `<span class="font-label-sm text-label-sm">${invoiceLabel}</span>`}
          </div>
          <span class="text-primary font-label-sm text-label-sm">${escapeHtml(item.category || '')}</span>
        </div>
      </div>
    </div>
  `
}

function filterSummary() {
  const parts = []
  if (expenseFilters.value.query) parts.push(`جستجو: ${expenseFilters.value.query}`)
  if (expenseFilters.value.person) parts.push(`شخص: ${expenseFilters.value.person}`)
  if (expenseFilters.value.startDate) parts.push(`از: ${expenseFilters.value.startDate}`)
  if (expenseFilters.value.endDate) parts.push(`تا: ${expenseFilters.value.endDate}`)
  return parts.join(' | ') || 'برای فیلتر کلیک کنید'
}

function applyFilters(filters) {
  Object.entries(filters).forEach(([key, value]) => updatePageFilter('expenses', key, value))
  filterOpen.value = false
}

function resetFilters() {
  resetPageFilters('expenses')
}

function hydrate(root) {
  const addButton = root.querySelector('section button.luxury-gradient')
  if (addButton) addButton.onclick = () => openExpenseComposer()

  const filterSection = root.querySelector('section.space-y-4')
  if (filterSection) filterSection.onclick = () => { filterOpen.value = true }

  const searchInput = root.querySelector('input[type="text"]')
  if (searchInput) {
    searchInput.readOnly = true
    searchInput.value = filterSummary()
    searchInput.placeholder = 'برای فیلتر کلیک کنید'
    searchInput.onclick = () => { filterOpen.value = true }
  }

  const countBadge = root.querySelector('section.space-y-4 span.bg-surface-container-high')
  if (countBadge) countBadge.textContent = `${filteredExpenses.value.length} ردیف`

  const sections = root.querySelectorAll('main > section')
  const listSection = sections[2]
  if (listSection) {
    const header = listSection.firstElementChild?.outerHTML || ''
    listSection.innerHTML = `${header}<div class="space-y-4">${filteredExpenses.value.map(renderExpenseCard).join('') || '<div class="bg-surface-container-lowest rounded-2xl p-card-padding text-on-surface-variant">هزینه‌ای یافت نشد.</div>'}</div>`
  }

  wirePageNavigation(root, navigateTo, '/expenses', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

watch(() => [filteredExpenses.value, state.filters.expenses], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage v-if="state.currentUser.canAccessExpenses !== false" ref="runtime" stitch-id="_4" @ready="hydrate" />
  <section v-else class="page-shell" style="padding: 32px;">
    دسترسی به صفحه هزینه ها برای شما فعال نیست.
  </section>
  <FilterDialog
    v-if="state.currentUser.canAccessExpenses !== false"
    :open="filterOpen"
    title="فیلتر هزینه‌ها"
    :filters="expenseFilters"
    :people="expensePeople"
    @close="filterOpen = false"
    @apply="applyFilters"
    @reset="resetFilters"
  />
</template>
