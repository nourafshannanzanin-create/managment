<script setup>
import { computed, onMounted, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const saving = ref(false)
const accessModalOpen = ref(false)
const selectedSectionKey = ref('')
const selectedUserIds = ref([])

const { loadSettings, logout, saveSettings, state } = useWorkflowHub()

const selectedSection = computed(() => state.settings.sections.find((item) => item.key === selectedSectionKey.value) || null)

async function persistSettings() {
  if (!state.settings.canEdit || saving.value) return
  saving.value = true
  try {
    await saveSettings({
      organizationName: state.settings.organizationName,
      twoFactorRequired: state.settings.security?.twoFactorRequired,
    })
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

onMounted(async () => {
  await loadSettings(true)
})
</script>

<template>
  <section class="page-shell enterprise-page">
    <PageHeader
      eyebrow="پیکربندی سامانه"
      title="تنظیمات سازمان"
      description="تنظیمات هویت سازمانی، امنیت حساب‌ها و دسترسی بخش‌های مختلف را در این صفحه مدیریت کنید."
    />

    <section class="dashboard-grid">
      <article class="surface-block">
        <div class="section-label-row">
          <div>
            <h3>پروفایل سازمان</h3>
            <p>اطلاعات هویتی سازمان</p>
          </div>
        </div>

        <div class="settings-stack">
          <label class="field-shell">
            <span>نام سازمان</span>
            <input v-model="state.settings.organizationName" type="text" :readonly="!state.settings.canEdit" />
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
            <h3>امنیت و نشست‌ها</h3>
            <p>سیاست‌های دسترسی و نشست‌های فعال</p>
          </div>
        </div>

        <div class="settings-stack">
          <label class="toggle-row">
            <div>
              <strong>احراز هویت دومرحله‌ای</strong>
              <p>الزام ورود دومرحله‌ای برای کاربران سازمان</p>
            </div>
            <button
              :class="['toggle-pill', state.settings.security?.twoFactorRequired && 'is-active']"
              type="button"
              :disabled="!state.settings.canEdit"
              @click="state.settings.security.twoFactorRequired = !state.settings.security.twoFactorRequired"
            >
              <span></span>
            </button>
          </label>

          <div class="detail-meta-item">
            <span>نشست‌های اخیر</span>
            <strong>{{ state.settings.security?.recentSessionLabel || 'بدون نشست اخیر' }}</strong>
          </div>

          <button class="action-btn tone-soft" type="button" @click="logout">
            <span class="material-symbols-outlined">logout</span>
            <span>خروج از حساب</span>
          </button>
        </div>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>دسترسی بخش‌ها</h3>
          <p>دسترسی کاربران به ماژول‌های مختلف را برای هر بخش سازمان تنظیم کنید.</p>
        </div>
      </div>

      <div class="card-grid">
        <button
          v-for="(item, index) in state.settings.sections"
          :key="item.key"
          class="settings-access-card"
          type="button"
          @click="openSectionAccess(item)"
        >
          <div class="settings-access-icon">
            <span class="material-symbols-outlined">{{ index % 2 === 0 ? 'dashboard_customize' : 'admin_panel_settings' }}</span>
          </div>
          <div class="settings-access-copy">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
            <small>{{ (item.allowedUsers || []).length }} کاربر مجاز</small>
          </div>
          <span class="material-symbols-outlined">chevron_left</span>
        </button>
      </div>
    </section>
  </section>

  <BaseModal :open="accessModalOpen" size="detail" @close="accessModalOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">دسترسی بخش</p>
        <h2>{{ selectedSection?.title || 'بخش' }}</h2>
      </div>

      <section class="modal-section">
        <p class="modal-copy">کاربرانی را انتخاب کنید که به این بخش از سامانه دسترسی داشته باشند.</p>
        <div class="timeline-rail">
          <label v-for="user in state.settings.organizationUsers" :key="user.id" class="checkbox-card">
            <input v-model="selectedUserIds" type="checkbox" :value="user.id" />
            <div>
              <strong>{{ user.name }}</strong>
              <p>{{ user.role }} - {{ user.department }}</p>
            </div>
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
