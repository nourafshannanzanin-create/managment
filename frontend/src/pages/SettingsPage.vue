<script setup>
import { computed, onMounted, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const saving = ref(false)
const accessModalOpen = ref(false)
const selectedSectionKey = ref('')
const selectedUserIds = ref([])
const userSearch = ref('')
const sectionSearch = ref('')
const newDepartmentName = ref('')
const activeLetter = ref('Ù‡Ù…Ù‡')

const { loadSettings, saveSettings, state } = useWorkflowHub()

const selectedSection = computed(() => state.settings.sections.find((item) => item.key === selectedSectionKey.value) || null)

const filteredSettingsSections = computed(() => {
  const query = sectionSearch.value.trim().toLowerCase()
  if (!query) return state.settings.sections
  return state.settings.sections.filter((item) =>
    [item.title, item.description, item.key]
      .some((field) => String(field || '').toLowerCase().includes(query)),
  )
})

const availableLetters = computed(() => {
  const letters = new Set(
    (state.settings.organizationUsers || [])
      .map((item) => String(item.name || '').trim().slice(0, 1))
      .filter(Boolean),
  )
  return ['Ù‡Ù…Ù‡', ...[...letters].sort((a, b) => a.localeCompare(b, 'fa'))]
})

const filteredOrganizationUsers = computed(() => {
  const query = userSearch.value.trim().toLowerCase()

  return [...(state.settings.organizationUsers || [])]
    .filter((item) => {
      const firstLetter = String(item.name || '').trim().slice(0, 1)
      const matchesLetter = activeLetter.value === 'Ù‡Ù…Ù‡' || firstLetter === activeLetter.value
      const matchesQuery = !query ||
        ['name', 'role', 'department']
          .some((field) => String(item[field] || '').toLowerCase().includes(query))
      return matchesLetter && matchesQuery
    })
    .sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'fa'))
})

async function persistSettings() {
  if (!state.settings.canEdit || saving.value) return
  saving.value = true
  try {
    await saveSettings({
      organizationName: state.settings.organizationName,
      systemId: state.settings.systemId,
    })
  } finally {
    saving.value = false
  }
}

function openSectionAccess(section) {
  if (!state.settings.canEdit) return
  selectedSectionKey.value = section.key
  selectedUserIds.value = [...(section.allowedUserIds || [])]
  userSearch.value = ''
  activeLetter.value = 'Ù‡Ù…Ù‡'
  accessModalOpen.value = true
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

function isSelected(userId) {
  return selectedUserIds.value.includes(userId)
}

async function persistDepartments() {
  if (!state.settings.canEdit || saving.value) return
  const departments = (state.settings.departments || [])
    .map((item) => ({ id: item.id, code: item.code, name: String(item.name || '').trim() }))
    .filter((item) => item.name)
  const newName = newDepartmentName.value.trim()
  if (newName) departments.push({ name: newName })

  saving.value = true
  try {
    await saveSettings({ departments })
    newDepartmentName.value = ''
  } finally {
    saving.value = false
  }
}

function toggleUser(userId) {
  const next = new Set(selectedUserIds.value)
  if (next.has(userId)) next.delete(userId)
  else next.add(userId)
  selectedUserIds.value = [...next]
}

function removeDepartment(index) {
  if (!state.settings.canEdit || saving.value) return
  state.settings.departments = state.settings.departments.filter((_, itemIndex) => itemIndex !== index)
}

onMounted(async () => {
  await loadSettings(true)
})
</script>

<template>
  <section class="page-shell enterprise-page">
    <section class="dashboard-grid settings-modern-grid">
      <article class="surface-block">
        <div class="section-label-row">
          <div>
            <h3>Ù¾Ø±ÙˆÙØ§ÛŒÙ„ Ø³Ø§Ø²Ù…Ø§Ù†</h3>
            <p>ÙÙ‚Ø· Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ù‡ÙˆÛŒØªÛŒ Ø³Ø§Ø²Ù…Ø§Ù† Ù†Ú¯Ù‡ Ø¯Ø§Ø´ØªÙ‡ Ø´Ø¯Ù‡ ØªØ§ ØµÙØ­Ù‡ Ø¬Ù…Ø¹â€ŒÙˆØ¬ÙˆØ± Ùˆ Ú©Ø§Ø±Ø¨Ø±Ø¯ÛŒ Ø¨Ù…Ø§Ù†Ø¯.</p>
          </div>
        </div>

        <div class="settings-stack">
          <label class="field-shell">
            <span>Ù†Ø§Ù… Ø³Ø§Ø²Ù…Ø§Ù†</span>
            <input v-model="state.settings.organizationName" type="text" :readonly="!state.settings.canEdit" />
          </label>

          <label class="field-shell">
            <span>Ú©Ø¯Ù†ÙˆÙ… Ø³Ø§Ø²Ù…Ø§Ù†</span>
            <input v-model="state.settings.systemId" type="text" :readonly="!state.settings.canEdit" />
          </label>

          <button v-if="state.settings.canEdit" class="action-btn tone-primary" type="button" @click="persistSettings">
            <span class="material-symbols-outlined">save</span>
            <span>{{ saving ? 'Ø¯Ø± Ø­Ø§Ù„ Ø°Ø®ÛŒØ±Ù‡...' : 'Ø°Ø®ÛŒØ±Ù‡ ØªÙ†Ø¸ÛŒÙ…Ø§Øª' }}</span>
          </button>
        </div>
      </article>

      <article class="surface-block">
        <div class="section-label-row">
          <div>
            <h3>Ø®Ù„Ø§ØµÙ‡ Ø¯Ø³ØªØ±Ø³ÛŒâ€ŒÙ‡Ø§</h3>
            <p>Ù†Ù…Ø§ÛŒ ÙØ´Ø±Ø¯Ù‡ Ø§Ø² Ø¨Ø®Ø´â€ŒÙ‡Ø§ÛŒ Ù‚Ø§Ø¨Ù„ Ù…Ø¯ÛŒØ±ÛŒØª Ùˆ ØªØ¹Ø¯Ø§Ø¯ Ø§ÙØ±Ø§Ø¯ Ù…Ø¬Ø§Ø² Ø¯Ø± Ù‡Ø± Ø¨Ø®Ø´.</p>
          </div>
        </div>

        <div class="progress-list">
          <article v-for="item in state.settings.sections" :key="item.key" class="progress-row">
            <strong>{{ item.title }}</strong>
            <div class="progress-bar">
              <span :style="{ width: `${Math.max(12, ((item.allowedUsers || []).length / Math.max(state.settings.organizationUsers.length, 1)) * 100)}%` }"></span>
            </div>
            <small>{{ (item.allowedUsers || []).length }} Ù†ÙØ±</small>
          </article>
        </div>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>Ø¨Ø®Ø´â€ŒÙ‡Ø§ÛŒ Ø³Ø§Ø²Ù…Ø§Ù†</h3>
          <p>Ù‡Ù…ÛŒÙ† Ù„ÛŒØ³Øª Ø¯Ø± ÙØ±Ù…â€ŒÙ‡Ø§ÛŒ Ø¯Ø±Ø®ÙˆØ§Ø³ØªØŒ Ù‡Ø²ÛŒÙ†Ù‡ØŒ Ø³Ù†Ø¯ Ùˆ Ú©Ø§Ø±Ø¨Ø± Ø¨Ù‡ Ø¹Ù†ÙˆØ§Ù† Â«Ø§Ù†ØªØ®Ø§Ø¨ Ø¨Ø®Ø´Â» Ù†Ù…Ø§ÛŒØ´ Ø¯Ø§Ø¯Ù‡ Ù…ÛŒâ€ŒØ´ÙˆØ¯.</p>
        </div>
      </div>

      <div class="settings-stack">
        <div v-for="(department, index) in state.settings.departments" :key="department.id || department.code" class="department-row">
          <div class="department-card">
            <div class="department-card-head">
              <span class="department-code">{{ department.code }}</span>
              <button
                v-if="state.settings.canEdit"
                class="action-btn tone-danger department-delete-btn"
                type="button"
                @click="removeDepartment(index)"
              >
                <span class="material-symbols-outlined">delete</span>
                <span>Ø­Ø°Ù</span>
              </button>
            </div>

            <label class="field-shell">
              <span>Ù†Ø§Ù… Ø¨Ø®Ø´</span>
              <input v-model="department.name" type="text" :readonly="!state.settings.canEdit" />
            </label>
          </div>
        </div>

        <label v-if="state.settings.canEdit" class="field-shell">
          <span>Ø¨Ø®Ø´ Ø¬Ø¯ÛŒØ¯</span>
          <input v-model="newDepartmentName" type="text" placeholder="Ù…Ø«Ù„Ø§ ÙØ±ÙˆØ´ØŒ Ø¹Ù…Ù„ÛŒØ§ØªØŒ Ù…Ø§Ù„ÛŒ..." />
        </label>

        <button v-if="state.settings.canEdit" class="action-btn tone-primary" type="button" @click="persistDepartments">
          <span class="material-symbols-outlined">save</span>
          <span>{{ saving ? 'Ø¯Ø± Ø­Ø§Ù„ Ø°Ø®ÛŒØ±Ù‡...' : 'Ø°Ø®ÛŒØ±Ù‡ Ø¨Ø®Ø´â€ŒÙ‡Ø§' }}</span>
        </button>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>Ø¯Ø³ØªØ±Ø³ÛŒ Ø¨Ù‡ Ø¨Ø®Ø´â€ŒÙ‡Ø§</h3>
          <p>Ø¨Ù‡â€ŒØ¬Ø§ÛŒ Ú©Ø§Ø±Øªâ€ŒÙ‡Ø§ÛŒ Ø¨Ø²Ø±Ú¯ØŒ Ø¯Ø³ØªØ±Ø³ÛŒâ€ŒÙ‡Ø§ Ø¯Ø± ÛŒÚ© Ø¬Ø¯ÙˆÙ„ Ø³Ø¨Ú© Ùˆ Ù‚Ø§Ø¨Ù„ Ø¬Ø³ØªØ¬Ùˆ Ù†Ù…Ø§ÛŒØ´ Ø¯Ø§Ø¯Ù‡ Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯.</p>
        </div>
      </div>

      <label class="search-shell search-shell-wide settings-section-search">
        <span class="material-symbols-outlined">search</span>
        <input v-model="sectionSearch" type="text" placeholder="Ø¬Ø³ØªØ¬Ùˆ Ø¯Ø± Ø¨Ø®Ø´â€ŒÙ‡Ø§..." />
      </label>

      <div v-if="filteredSettingsSections.length" class="settings-access-table">
        <div class="settings-access-table-head">
          <span>Ø¨Ø®Ø´</span>
          <span>Ø´Ø±Ø­</span>
          <span>Ú©Ø§Ø±Ø¨Ø±Ø§Ù† Ù…Ø¬Ø§Ø²</span>
          <span>Ø¹Ù…Ù„ÛŒØ§Øª</span>
        </div>

        <button
          v-for="item in filteredSettingsSections"
          :key="item.key"
          class="settings-access-table-row"
          type="button"
          @click="openSectionAccess(item)"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.description }}</span>
          <span>{{ (item.allowedUsers || []).length }} Ù†ÙØ±</span>
          <span class="table-link">Ù…Ø¯ÛŒØ±ÛŒØª</span>
        </button>
      </div>
      <div v-else class="empty-state-inline">
        <span class="material-symbols-outlined">rule</span>
        <p>{{ state.settings.sections.length ? 'Ø¨Ø®Ø´ÛŒ Ù…Ø·Ø§Ø¨Ù‚ Ø¬Ø³ØªØ¬Ùˆ Ù¾ÛŒØ¯Ø§ Ù†Ø´Ø¯.' : 'Ø¨Ø®Ø´ÛŒ Ø¨Ø±Ø§ÛŒ ØªÙ†Ø¸ÛŒÙ… Ø¯Ø³ØªØ±Ø³ÛŒ Ø¯Ø±ÛŒØ§ÙØª Ù†Ø´Ø¯.' }}</p>
      </div>
    </section>
  </section>

  <BaseModal :open="accessModalOpen" size="detail" @close="accessModalOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">Ø¯Ø³ØªØ±Ø³ÛŒ Ø¨Ø®Ø´</p>
        <h2>{{ selectedSection?.title || 'Ø¨Ø®Ø´' }}</h2>
      </div>

      <section class="surface-inline access-directory-panel">
        <div class="filter-toolbar users-filter-toolbar">
          <label class="search-shell search-shell-wide">
            <span class="material-symbols-outlined">search</span>
            <input v-model="userSearch" type="text" placeholder="Ø¬Ø³ØªØ¬Ùˆ Ø¯Ø± Ø§Ø¹Ø¶Ø§..." />
          </label>

          <div class="alphabet-strip">
            <button
              v-for="letter in availableLetters"
              :key="letter"
              :class="['alphabet-chip', activeLetter === letter && 'is-active']"
              type="button"
              @click="activeLetter = letter"
            >
              {{ letter }}
            </button>
          </div>
        </div>

        <div class="access-selection-table">
          <div class="settings-access-table-head">
            <span>ÙˆØ¶Ø¹ÛŒØª</span>
            <span>Ù†Ø§Ù…</span>
            <span>Ø³Ù…Øª</span>
            <span>Ø¨Ø®Ø´</span>
          </div>

          <button
            v-for="user in filteredOrganizationUsers"
            :key="user.id"
            :class="['access-selection-row', isSelected(user.id) && 'is-selected']"
            type="button"
            @click="toggleUser(user.id)"
          >
            <span class="access-selection-state">{{ isSelected(user.id) ? 'Ø§Ù†ØªØ®Ø§Ø¨ Ø´Ø¯Ù‡' : 'Ø§Ù†ØªØ®Ø§Ø¨ Ù†Ø´Ø¯Ù‡' }}</span>
            <strong>{{ user.name }}</strong>
            <span>{{ user.role || '-' }}</span>
            <span>{{ user.department || '-' }}</span>
          </button>
        </div>
      </section>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="accessModalOpen = false">
          <span class="material-symbols-outlined">close</span>
          <span>Ø¨Ø³ØªÙ†</span>
        </button>
        <button class="action-btn tone-primary" type="button" @click="persistSectionAccess">
          <span class="material-symbols-outlined">save</span>
          <span>{{ saving ? 'Ø¯Ø± Ø­Ø§Ù„ Ø°Ø®ÛŒØ±Ù‡...' : 'Ø°Ø®ÛŒØ±Ù‡ Ø¯Ø³ØªØ±Ø³ÛŒ' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.settings-stack {
  gap: 10px;
}

.settings-stack .field-shell input {
  min-height: 42px;
}

.department-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(32, 58, 105, 0.1);
}

.department-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.department-code {
  font-size: 0.84rem;
  font-weight: 700;
  color: rgba(23, 37, 84, 0.86);
}

.department-row .field-shell {
  margin: 0;
  background: transparent;
  border: 0;
  padding: 0;
}

.department-delete-btn {
  min-height: 42px;
  flex-shrink: 0;
}

.settings-section-search {
  margin-bottom: 14px;
  max-width: 420px;
}

@media (min-width: 860px) {
  .surface-block:nth-of-type(2) .settings-stack {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-items: stretch;
  }
}
</style>
