<script setup>
import { computed, ref, watch } from 'vue'

import FilterDialog from '../components/FilterDialog.vue'
import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const filterOpen = ref(false)
const { filteredUsers, navigateTo, openUserComposer, resetPageFilters, state, updatePageFilter, userPeople, visibleNavItems } = useWorkflowHub()
const userFilters = computed(() => state.filters.users)

function renderUserCard(item) {
  const initial = escapeHtml((item.name || '?').slice(0, 1))

  return `
    <div class="bg-surface-container-lowest p-card-padding rounded-2xl card-shadow border border-outline-variant/5">
      <div class="flex items-start justify-between mb-4">
        <div class="flex items-center gap-4">
          <div class="relative w-16 h-16 rounded-2xl bg-primary/10 overflow-hidden border border-outline-variant/10">
            <div class="w-full h-full flex items-center justify-center text-primary font-bold text-xl">
              ${initial}
            </div>
            <div class="absolute -top-2 -right-2 w-10 h-10 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-headline-md shadow-md">
              <span>${initial}</span>
            </div>
          </div>
          <div>
            <h4 class="font-headline-md text-body-lg text-on-surface font-bold">${escapeHtml(item.name)}</h4>
            <span class="inline-block px-2 py-0.5 mt-1 bg-primary/10 text-primary rounded font-label-sm text-label-sm">${escapeHtml(item.role)}</span>
          </div>
        </div>
        <button class="material-symbols-outlined text-on-surface-variant">more_vert</button>
      </div>
      <div class="space-y-2 border-t border-secondary/5 pt-4">
        <div class="flex items-center gap-3 text-on-surface-variant">
          <span class="material-symbols-outlined text-[20px]">mail</span>
          <span class="font-label-sm text-label-sm">${escapeHtml(item.email)}</span>
        </div>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 text-on-surface-variant">
            <span class="material-symbols-outlined text-[20px]">hub</span>
            <span class="font-label-sm text-label-sm">${escapeHtml(item.department)}</span>
          </div>
          <span class="text-outline text-[11px] font-label-sm">عضویت: ${escapeHtml(item.joinedAt)}</span>
        </div>
      </div>
    </div>
  `
}

function filterSummary() {
  const parts = []
  if (userFilters.value.query) parts.push(`جستجو: ${userFilters.value.query}`)
  if (userFilters.value.person) parts.push(`شخص: ${userFilters.value.person}`)
  if (userFilters.value.startDate) parts.push(`از: ${userFilters.value.startDate}`)
  if (userFilters.value.endDate) parts.push(`تا: ${userFilters.value.endDate}`)
  return parts.join(' | ') || 'برای فیلتر کلیک کنید'
}

function applyFilters(filters) {
  Object.entries(filters).forEach(([key, value]) => updatePageFilter('users', key, value))
  filterOpen.value = false
}

function resetFilters() {
  resetPageFilters('users')
}

function hydrate(root) {
  const searchInput = root.querySelector('input[type="text"]')
  if (searchInput) {
    searchInput.readOnly = true
    searchInput.value = filterSummary()
    searchInput.placeholder = 'برای فیلتر کلیک کنید'
    searchInput.onclick = () => { filterOpen.value = true }
  }

  const filterSection = root.querySelector('section.mb-6')
  if (filterSection) filterSection.onclick = () => { filterOpen.value = true }

  const stats = root.querySelectorAll('.grid.grid-cols-2 .font-stat-value')
  if (stats[0]) stats[0].textContent = String(state.users.length)
  if (stats[1]) stats[1].textContent = String(filteredUsers.value.filter((item) => item.status === 'فعال').length)

  const heading = root.querySelector('h2.font-headline-md')
  if (heading) heading.onclick = () => openUserComposer()

  const cardGroups = root.querySelectorAll('.space-y-4')
  const usersContainer = cardGroups[cardGroups.length - 1]
  if (usersContainer) usersContainer.innerHTML = filteredUsers.value.map(renderUserCard).join('') || '<div class="bg-surface-container-lowest p-card-padding rounded-2xl text-on-surface-variant">کاربری یافت نشد.</div>'

  wirePageNavigation(root, navigateTo, '/users', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

watch(() => [filteredUsers.value, state.filters.users, state.users.length], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage ref="runtime" stitch-id="_2" @ready="hydrate" />
  <FilterDialog
    :open="filterOpen"
    title="فیلتر کاربران"
    :filters="userFilters"
    :people="userPeople"
    @close="filterOpen = false"
    @apply="applyFilters"
    @reset="resetFilters"
  />
</template>
