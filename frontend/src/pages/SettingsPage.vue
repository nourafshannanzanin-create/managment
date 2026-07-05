<script setup>
import { computed, onMounted, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const saving = ref(false)
const accessModalOpen = ref(false)
const selectedSectionKey = ref('')
const selectedUserIds = ref([])
const userSearch = ref('')
const activeLetter = ref('همه')

const { loadSettings, saveSettings, state } = useWorkflowHub()

const selectedSection = computed(() => state.settings.sections.find((item) => item.key === selectedSectionKey.value) || null)

const availableLetters = computed(() => {
  const letters = new Set(
    (state.settings.organizationUsers || [])
      .map((item) => String(item.name || '').trim().slice(0, 1))
      .filter(Boolean),
  )
  return ['همه', ...[...letters].sort((a, b) => a.localeCompare(b, 'fa'))]
})

const filteredOrganizationUsers = computed(() => {
  const query = userSearch.value.trim().toLowerCase()

  return [...(state.settings.organizationUsers || [])]
    .filter((item) => {
      const firstLetter = String(item.name || '').trim().slice(0, 1)
      const matchesLetter = activeLetter.value === 'همه' || firstLetter === activeLetter.value
      const matchesQuery = !query ||
        ['name', 'role', 'department', 'email']
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
  activeLetter.value = 'همه'
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

function toggleUser(userId) {
  const next = new Set(selectedUserIds.value)
  if (next.has(userId)) next.delete(userId)
  else next.add(userId)
  selectedUserIds.value = [...next]
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
            <h3>پروفایل سازمان</h3>
            <p>فقط اطلاعات هویتی سازمان نگه داشته شده تا صفحه جمع‌وجور و کاربردی بماند.</p>
          </div>
        </div>

        <div class="settings-stack">
          <label class="field-shell">
            <span>نام سازمان</span>
            <input v-model="state.settings.organizationName" type="text" :readonly="!state.settings.canEdit" />
          </label>

          <label class="field-shell">
            <span>کدنوم سازمان</span>
            <input v-model="state.settings.systemId" type="text" :readonly="!state.settings.canEdit" />
          </label>

          <button v-if="state.settings.canEdit" class="action-btn tone-primary" type="button" @click="persistSettings">
            <span class="material-symbols-outlined">save</span>
            <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات' }}</span>
          </button>
        </div>
      </article>

      <article class="surface-block">
        <div class="section-label-row">
          <div>
            <h3>خلاصه دسترسی‌ها</h3>
            <p>نمای فشرده از بخش‌های قابل مدیریت و تعداد افراد مجاز در هر بخش.</p>
          </div>
        </div>

        <div class="progress-list">
          <article v-for="item in state.settings.sections" :key="item.key" class="progress-row">
            <strong>{{ item.title }}</strong>
            <div class="progress-bar">
              <span :style="{ width: `${Math.max(12, ((item.allowedUsers || []).length / Math.max(state.settings.organizationUsers.length, 1)) * 100)}%` }"></span>
            </div>
            <small>{{ (item.allowedUsers || []).length }} نفر</small>
          </article>
        </div>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>دسترسی به بخش‌ها</h3>
          <p>به‌جای کارت‌های بزرگ، دسترسی‌ها در یک جدول سبک و قابل جستجو نمایش داده می‌شوند.</p>
        </div>
      </div>

      <div v-if="state.settings.sections.length" class="settings-access-table">
        <div class="settings-access-table-head">
          <span>بخش</span>
          <span>شرح</span>
          <span>کاربران مجاز</span>
          <span>عملیات</span>
        </div>

        <button
          v-for="item in state.settings.sections"
          :key="item.key"
          class="settings-access-table-row"
          type="button"
          @click="openSectionAccess(item)"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.description }}</span>
          <span>{{ (item.allowedUsers || []).length }} نفر</span>
          <span class="table-link">مدیریت</span>
        </button>
      </div>
      <div v-else class="empty-state-inline">
        <span class="material-symbols-outlined">rule</span>
        <p>بخشی برای تنظیم دسترسی دریافت نشد.</p>
      </div>
    </section>
  </section>

  <BaseModal :open="accessModalOpen" size="detail" @close="accessModalOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">دسترسی بخش</p>
        <h2>{{ selectedSection?.title || 'بخش' }}</h2>
      </div>

      <section class="surface-inline access-directory-panel">
        <div class="filter-toolbar users-filter-toolbar">
          <label class="search-shell search-shell-wide">
            <span class="material-symbols-outlined">search</span>
            <input v-model="userSearch" type="text" placeholder="جستجو در اعضا..." />
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
            <span>انتخاب</span>
            <span>نام</span>
            <span>سمت</span>
            <span>بخش</span>
          </div>

          <label v-for="user in filteredOrganizationUsers" :key="user.id" class="access-selection-row">
            <input type="checkbox" :checked="isSelected(user.id)" @change="toggleUser(user.id)" />
            <strong>{{ user.name }}</strong>
            <span>{{ user.role || '-' }}</span>
            <span>{{ user.department || '-' }}</span>
          </label>
        </div>
      </section>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="accessModalOpen = false">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" type="button" @click="persistSectionAccess">
          <span class="material-symbols-outlined">save</span>
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره دسترسی' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
