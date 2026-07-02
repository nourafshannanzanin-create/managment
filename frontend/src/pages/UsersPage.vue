<script setup>
import { computed, ref, watch } from 'vue'

import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const searchQuery = ref('')
const activeCategory = ref('all')
const { navigateTo, openUserComposer, state, visibleNavItems } = useWorkflowHub()

const categoryButtons = computed(() => [
  { key: 'all', label: 'همه افراد' },
  { key: 'managers', label: 'مدیران' },
  { key: 'experts', label: 'کارشناسان' },
  { key: 'it', label: 'فناوری اطلاعات' },
])

const filteredUsers = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return state.users.filter((item) => {
    const matchesCategory =
      activeCategory.value === 'all' ||
      (activeCategory.value === 'managers' && ['admin', 'executive_manager', 'manager'].includes(item.accessRole)) ||
      (activeCategory.value === 'experts' && item.accessRole === 'employee') ||
      (activeCategory.value === 'it' && String(item.department || '').includes('فناوری اطلاعات'))

    if (!matchesCategory) return false
    if (!query) return true

    return ['name', 'email', 'role', 'department', 'manager', 'status']
      .some((field) => String(item[field] || '').toLowerCase().includes(query))
  })
})

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
          <span class="inline-block px-2 py-0.5 bg-surface-variant text-on-surface-variant rounded font-label-sm text-label-sm">${escapeHtml(item.status)}</span>
        </div>
      </div>
    </div>
  `
}

function hydrate(root) {
  const searchInput = root.querySelector('input[type="text"]')
  if (searchInput) {
    searchInput.readOnly = false
    searchInput.value = searchQuery.value
    searchInput.placeholder = 'جستجو در کاربران'
    searchInput.oninput = (event) => {
      searchQuery.value = event.target.value || ''
    }
  }

  const tuneButton = root.querySelector('button.material-symbols-outlined.absolute')
  if (tuneButton) tuneButton.remove()

  const filterSection = root.querySelector('.flex.gap-2.overflow-x-auto')
  if (filterSection) {
    filterSection.innerHTML = categoryButtons.value.map((item) => {
      const isActive = activeCategory.value === item.key
      return `
        <button
          type="button"
          data-user-category="${item.key}"
          class="whitespace-nowrap px-4 py-2 rounded-full font-label-sm text-label-sm ${isActive ? 'bg-primary text-on-primary shadow-md' : 'bg-surface-container-highest text-on-surface-variant'}"
        >
          ${escapeHtml(item.label)}
        </button>
      `
    }).join('')

    filterSection.querySelectorAll('[data-user-category]').forEach((button) => {
      button.onclick = () => {
        activeCategory.value = button.getAttribute('data-user-category') || 'all'
      }
    })
  }

  const stats = root.querySelectorAll('.grid.grid-cols-2 .font-stat-value')
  if (stats[0]) stats[0].textContent = String(filteredUsers.value.length)
  if (stats[1]) stats[1].textContent = String(filteredUsers.value.filter((item) => item.status === 'فعال').length)

  const heading = root.querySelector('h2.font-headline-md')
  if (heading) heading.onclick = () => openUserComposer()

  const cardGroups = root.querySelectorAll('.space-y-4')
  const usersContainer = cardGroups[cardGroups.length - 1]
  if (usersContainer) {
    usersContainer.innerHTML = filteredUsers.value.map(renderUserCard).join('') || '<div class="bg-surface-container-lowest p-card-padding rounded-2xl text-on-surface-variant">کاربری یافت نشد.</div>'
  }

  wirePageNavigation(root, navigateTo, '/users', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

watch(() => [filteredUsers.value, activeCategory.value, searchQuery.value, state.users.length], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage v-if="state.currentUser.canAccessUsers || state.currentUser.canManageUsers" ref="runtime" stitch-id="_2" @ready="hydrate" />
  <section v-else class="page-shell" style="padding: 32px;">
    دسترسی به صفحه کاربران برای شما فعال نیست.
  </section>
</template>
