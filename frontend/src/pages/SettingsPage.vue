<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { escapeHtml, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const saving = ref(false)
const accessModalOpen = ref(false)
const selectedSectionKey = ref('')
const selectedUserIds = ref([])
const {
  loadSettings,
  logout,
  navigateTo,
  saveSettings,
  state,
  visibleNavItems,
} = useWorkflowHub()

const selectedSection = computed(() => state.settings.sections.find((item) => item.key === selectedSectionKey.value) || null)

async function persistSettings(root, organizationName, twoFactorRequired) {
  if (!state.settings.canEdit || saving.value) return
  saving.value = true
  try {
    await saveSettings({ organizationName, twoFactorRequired })
    if (root) hydrate(root)
  } finally {
    saving.value = false
  }
}

async function persistSectionAccess() {
  if (!selectedSection.value || saving.value) return
  saving.value = true
  try {
    await saveSettings({
      sectionKey: selectedSection.value.key,
      allowedUserIds: selectedUserIds.value,
    })
    accessModalOpen.value = false
  } finally {
    saving.value = false
  }
}

function openSectionAccess(section) {
  if (!state.settings.canEdit) return
  selectedSectionKey.value = section.key
  selectedUserIds.value = [...(section.allowedUserIds || [])]
  accessModalOpen.value = true
}

function bindSaveButton(root, organizationNameInput, securityToggle) {
  const card = organizationNameInput?.closest('.luxury-card')
  if (!card || card.querySelector('[data-settings-save]')) return

  const saveButton = document.createElement('button')
  saveButton.type = 'button'
  saveButton.dataset.settingsSave = 'true'
  saveButton.className = 'w-full rounded-lg bg-primary text-on-primary py-3 font-body-md text-body-md'
  saveButton.textContent = 'ذخیره تنظیمات'
  saveButton.onclick = async () => {
    await persistSettings(root, organizationNameInput.value.trim(), securityToggle?.checked ?? true)
  }
  card.appendChild(saveButton)
}

function hydrate(root) {
  const organizationNameInput = root.querySelector('input[type="text"]')
  if (organizationNameInput) {
    organizationNameInput.value = state.settings.organizationName || state.currentUser.organization || 'کارنومند'
    organizationNameInput.readOnly = !state.settings.canEdit
  }

  const systemId = root.querySelector('.ghost-input span')
  if (systemId) systemId.textContent = state.settings.systemId || `KARO-${String(state.currentUser.id || 0).padStart(4, '0')}`

  const securityToggle = root.querySelector('.toggle-switch input')
  if (securityToggle) {
    securityToggle.checked = Boolean(state.settings.security?.twoFactorRequired)
    securityToggle.disabled = !state.settings.canEdit
    securityToggle.onchange = async () => {
      await persistSettings(root, organizationNameInput?.value.trim() || state.settings.organizationName, securityToggle.checked)
    }
  }

  if (organizationNameInput) {
    organizationNameInput.onkeydown = async (event) => {
      if (event.key !== 'Enter') return
      event.preventDefault()
      await persistSettings(root, organizationNameInput.value.trim(), securityToggle?.checked ?? true)
    }
  }

  const sessionButton = Array.from(root.querySelectorAll('button')).find((item) =>
    /chevron_left/.test(item.innerHTML || ''),
  )
  if (sessionButton) {
    const sessionCopy = sessionButton.querySelector('p.text-on-surface-variant')
    if (sessionCopy) sessionCopy.textContent = state.settings.security?.recentSessionLabel || 'بدون نشست اخیر'
  }

  const sectionCards = root.querySelector('.grid.grid-cols-1.gap-3')
  if (sectionCards) {
    const cards = state.settings.sections?.length ? state.settings.sections : state.settingsCards
    sectionCards.innerHTML = cards.map((item, index) => `
      <button
        type="button"
        data-section-key="${escapeHtml(item.key || '')}"
        class="luxury-card rounded-xl p-4 flex flex-row-reverse items-center justify-between hover:bg-surface-container-low transition-colors cursor-pointer w-full text-right"
      >
        <div class="flex flex-row-reverse items-center gap-4">
          <div class="w-10 h-10 rounded-lg bg-secondary-container flex items-center justify-center">
            <span class="material-symbols-outlined text-primary">${index % 2 === 0 ? 'description' : 'person'}</span>
          </div>
          <div class="text-right">
            <span class="font-body-md text-body-md font-medium block">${escapeHtml(item.title)}</span>
            <small class="text-on-surface-variant block">${escapeHtml(item.description)}</small>
            <small class="text-primary block mt-1">${escapeHtml(`${(item.allowedUsers || []).length} کاربر مجاز`)}</small>
          </div>
        </div>
        <span class="material-symbols-outlined text-outline-variant">chevron_left</span>
      </button>
    `).join('')

    sectionCards.querySelectorAll('[data-section-key]').forEach((button) => {
      button.onclick = () => {
        const section = state.settings.sections.find((item) => item.key === button.getAttribute('data-section-key'))
        if (section) openSectionAccess(section)
      }
    })
  }

  const logoutButton = Array.from(root.querySelectorAll('button')).find((item) =>
    /logout/.test(item.innerHTML || ''),
  )
  if (logoutButton) logoutButton.onclick = logout

  bindSaveButton(root, organizationNameInput, securityToggle)
  wirePageNavigation(root, navigateTo, '/settings', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

onMounted(async () => {
  await loadSettings(true)
})

watch(() => [state.currentUser.organization, state.currentUser.id, state.settings, state.settingsCards], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage ref="runtime" stitch-id="_1" @ready="hydrate" />
  <BaseModal :open="accessModalOpen" size="detail" @close="accessModalOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">دسترسی بخش</p>
        <h2>{{ selectedSection?.title || 'بخش' }}</h2>
      </div>
      <section class="modal-section">
        <p class="text-on-surface-variant">
          کاربرانی را انتخاب کن که به این صفحه دسترسی داشته باشند.
        </p>
        <div class="timeline-rail">
          <label
            v-for="user in state.settings.organizationUsers"
            :key="user.id"
            class="checkbox-card"
          >
            <input
              v-model="selectedUserIds"
              type="checkbox"
              :value="user.id"
            />
            <div>
              <strong>{{ user.name }}</strong>
              <p>{{ user.role }} - {{ user.department }}</p>
            </div>
          </label>
        </div>
      </section>
      <div class="modal-actions">
        <button class="action-btn tone-soft" @click="accessModalOpen = false">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" @click="persistSectionAccess">
          <span class="material-symbols-outlined">save</span>
          <span>ذخیره دسترسی</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
