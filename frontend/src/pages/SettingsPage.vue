<script setup>
import { ref, watch } from 'vue'

import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const { navigateTo, state, visibleNavItems } = useWorkflowHub()

function hydrate(root) {
  const orgNameInput = root.querySelector('input[type="text"]')
  if (orgNameInput) orgNameInput.value = state.currentUser.organization || 'کارنومند'

  const systemId = root.querySelector('.ghost-input span')
  if (systemId) systemId.textContent = `KARO-${String(state.currentUser.id || 0).padStart(4, '0')}`

  const sectionCards = root.querySelector('.grid.grid-cols-1.gap-3')
  if (sectionCards) {
    sectionCards.innerHTML = state.settingsCards.map((item, index) => `
      <div class="luxury-card rounded-xl p-4 flex flex-row-reverse items-center justify-between hover:bg-surface-container-low transition-colors cursor-pointer">
        <div class="flex flex-row-reverse items-center gap-4">
          <div class="w-10 h-10 rounded-lg bg-secondary-container flex items-center justify-center">
            <span class="material-symbols-outlined text-primary">${index % 2 === 0 ? 'description' : 'person'}</span>
          </div>
          <div class="text-right">
            <span class="font-body-md text-body-md font-medium block">${escapeHtml(item.title)}</span>
            <small class="text-on-surface-variant">${escapeHtml(item.description)}</small>
          </div>
        </div>
        <span class="material-symbols-outlined text-outline-variant">chevron_left</span>
      </div>
    `).join('')
  }

  wirePageNavigation(root, navigateTo, '/settings', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

watch(() => [state.currentUser.organization, state.currentUser.id, state.settingsCards], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage ref="runtime" stitch-id="_1" @ready="hydrate" />
</template>
