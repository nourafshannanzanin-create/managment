<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
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
const activeLetter = ref('همه')

const { loadSettings, saveSettings, state } = useWorkflowHub()

const selectedSection = computed(() => state.settings.sections.find((item) => item.key === selectedSectionKey.value) || null)

const filteredSettingsSections = computed(() => {
  const query = sectionSearch.value.trim().toLowerCase()
  if (!query) return state.settings.sections
  return state.settings.sections.filter((item) =>
    [item.title, item.description, item.key].some((field) => String(field || '').toLowerCase().includes(query)),
  )
})

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
        ['name', 'role', 'department'].some((field) => String(item[field] || '').toLowerCase().includes(query))
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
            <h3>پروفایل سازمان</h3>
            <p>اطلاعات هویتی و کدنوم سازمان از همین بخش مدیریت می‌شود.</p>
          </div>
        </div>

        <div class="settings-stack">
          <label class="field-shell">
            <span>نام سازمان</span>
            <input v-model="state.settings.organizationName" type="text" :readonly="!state.settings.canEdit" />
          </label>

          <label class="field-shell">
            <span>کدنوم سازمان</span>
            <input v-model="state.settings.systemId" type="text" dir="ltr" :readonly="!state.settings.canEdit" />
          </label>

          <button v-if="state.settings.canEdit" class="action-btn tone-primary" type="button" @click="persistSettings">
            <IconlyIcon name="save" decorative />
            <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات' }}</span>
          </button>
        </div>
      </article>

      <article class="surface-block">
        <div class="section-label-row">
          <div>
            <h3>خلاصه دسترسی‌ها</h3>
            <p>نمای فشرده‌ای از تعداد کاربران مجاز هر بخش.</p>
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
          <h3>بخش‌های سازمان</h3>
          <p>این فهرست در فرم‌های درخواست، هزینه، سند و کاربران نمایش داده می‌شود.</p>
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
                <IconlyIcon name="delete" decorative />
                <span>حذف</span>
              </button>
            </div>

            <label class="field-shell">
              <span>نام بخش</span>
              <input v-model="department.name" type="text" :readonly="!state.settings.canEdit" />
            </label>
          </div>
        </div>

        <label v-if="state.settings.canEdit" class="field-shell">
          <span>بخش جدید</span>
          <input v-model="newDepartmentName" type="text" placeholder="مثلا فروش، عملیات، مالی..." />
        </label>

        <button v-if="state.settings.canEdit" class="action-btn tone-primary" type="button" @click="persistDepartments">
          <IconlyIcon name="save" decorative />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره بخش‌ها' }}</span>
        </button>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>دسترسی به بخش‌ها</h3>
          <p>کاربران مجاز هر بخش را از این جدول جستجو و مدیریت کنید.</p>
        </div>
      </div>

      <label class="search-shell search-shell-wide settings-section-search">
        <IconlyIcon name="search" decorative />
        <input v-model="sectionSearch" type="text" placeholder="جستجو در بخش‌ها..." />
      </label>

      <div v-if="filteredSettingsSections.length" class="settings-access-table">
        <div class="settings-access-table-head">
          <span>بخش</span>
          <span>شرح</span>
          <span>کاربران مجاز</span>
          <span>عملیات</span>
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
          <span>{{ (item.allowedUsers || []).length }} نفر</span>
          <span class="table-link">مدیریت</span>
        </button>
      </div>
      <div v-else class="empty-state-inline">
        <IconlyIcon name="rule" decorative />
        <p>{{ state.settings.sections.length ? 'بخشی مطابق جستجو پیدا نشد.' : 'بخشی برای تنظیم دسترسی دریافت نشد.' }}</p>
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
            <IconlyIcon name="search" decorative />
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
            <span>وضعیت</span>
            <span>نام</span>
            <span>سمت</span>
            <span>بخش</span>
          </div>

          <button
            v-for="user in filteredOrganizationUsers"
            :key="user.id"
            :class="['access-selection-row', isSelected(user.id) && 'is-selected']"
            type="button"
            @click="toggleUser(user.id)"
          >
            <span class="access-selection-state">{{ isSelected(user.id) ? 'انتخاب شده' : 'انتخاب نشده' }}</span>
            <strong>{{ user.name }}</strong>
            <span>{{ user.role || '-' }}</span>
            <span>{{ user.department || '-' }}</span>
          </button>
        </div>
      </section>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="accessModalOpen = false">
          <IconlyIcon name="close" decorative />
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" type="button" @click="persistSectionAccess">
          <IconlyIcon name="save" decorative />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره دسترسی' }}</span>
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
  border-radius: 14px;
  background: #ffffff;
  border: 0;
  box-shadow: 0 4px 14px rgba(40, 110, 105, 0.1);
}

.department-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.department-code {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #1f5c59;
  background: #dcefec;
}

.department-row .field-shell {
  margin: 0;
  background: #e4f4f2;
  border: 0;
  padding: 8px 12px;
  border-radius: 10px;
}

.department-delete-btn {
  min-height: 32px;
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
