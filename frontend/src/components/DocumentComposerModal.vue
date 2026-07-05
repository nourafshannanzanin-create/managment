<script setup>
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const activeRecipientTab = ref('managers')
const recipientSearch = ref('')

const { state, setDocumentFile, submitDocument } = useWorkflowHub()

const recipientGroups = computed(() => {
  const managerDirectory = state.directories.managers.map((item) => ({
    id: item.id,
    name: item.name,
    role: item.role || 'مدیر',
    department: item.department || '',
    group: 'managers',
  }))

  const userDirectory = (state.users || []).map((item) => ({
    id: item.id,
    name: item.name,
    role: item.role || item.jobTitle || '',
    department: item.department || '',
    accessRole: item.accessRole || '',
    group: ['admin', 'executive_manager', 'manager'].includes(item.accessRole) ? 'managers' : 'employees',
  }))

  const uniqueUsers = [...managerDirectory, ...userDirectory].filter(
    (item, index, array) => array.findIndex((entry) => entry.id === item.id) === index,
  )

  return {
    managers: uniqueUsers.filter((item) => item.group === 'managers'),
    employees: uniqueUsers.filter((item) => item.group === 'employees'),
  }
})

const visibleRecipients = computed(() => {
  const query = recipientSearch.value.trim().toLowerCase()
  return (recipientGroups.value[activeRecipientTab.value] || []).filter((item) => {
    if (!query) return true
    return [item.name, item.role, item.department]
      .some((field) => String(field || '').toLowerCase().includes(query))
  })
})

function toggleAssignee(id) {
  if (activeRecipientTab.value !== 'managers') return
  const current = new Set(state.documentForm.assigneeIds)
  if (current.has(id)) current.delete(id)
  else current.add(id)
  state.documentForm.assigneeIds = [...current]
}

function isSelected(id) {
  return state.documentForm.assigneeIds.includes(id)
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">سند جدید</p>
        <h2>ارسال برای تایید</h2>
      </div>

      <div class="modal-grid two-col">
        <label class="field-shell">
          <span>عنوان</span>
          <input v-model="form.title" type="text" />
        </label>

        <label class="field-shell">
          <span>بخش</span>
          <select v-model="form.department">
            <option value="">انتخاب بخش</option>
            <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option>
          </select>
        </label>
      </div>

      <label class="field-shell">
        <span>توضیحات</span>
        <textarea v-model="form.description" rows="4"></textarea>
      </label>

      <div class="modal-grid two-col">
        <label class="field-shell">
          <span>نوع سند</span>
          <input v-model="form.documentType" type="text" />
        </label>

        <label class="field-shell">
          <span>ریسک</span>
          <select v-model="form.risk">
            <option value="low">پایین</option>
            <option value="medium">متوسط</option>
            <option value="high">بالا</option>
          </select>
        </label>
      </div>

      <label class="upload-pad compact-upload">
        <input type="file" accept="image/*,.pdf" @change="setDocumentFile($event.target.files?.[0])" />
        <span class="material-symbols-outlined">upload_file</span>
        <strong>{{ form.file?.name || 'افزودن فایل سند' }}</strong>
        <small>فایل PDF یا تصویر</small>
      </label>

      <section class="surface-inline">
        <div class="section-label-row">
          <div>
            <h3>گیرنده سند تایید</h3>
            <p>بین مدیران و کارمندان جابه‌جا شوید، جستجو کنید و افراد موردنظر را انتخاب کنید.</p>
          </div>
        </div>

        <div class="recipient-selector">
          <div class="tab-strip">
            <button
              :class="['filter-chip', activeRecipientTab === 'managers' && 'is-active']"
              type="button"
              @click="activeRecipientTab = 'managers'"
            >
              مدیران
            </button>
            <button
              :class="['filter-chip', activeRecipientTab === 'employees' && 'is-active']"
              type="button"
              @click="activeRecipientTab = 'employees'"
            >
              کارمندان
            </button>
          </div>

          <label class="search-shell">
            <span class="material-symbols-outlined">search</span>
            <input v-model="recipientSearch" type="text" placeholder="جستجو در اعضا..." />
          </label>

          <p v-if="activeRecipientTab === 'employees'" class="table-muted">
            در این نسخه، انتخاب نهایی تاییدکننده فقط از میان مدیران فعال است و این تب برای مرور سریع کارکنان در دسترس قرار دارد.
          </p>

          <div v-if="visibleRecipients.length" class="recipient-grid">
            <button
              v-for="item in visibleRecipients"
              :key="item.id"
              :class="['recipient-card', isSelected(item.id) && 'is-selected', activeRecipientTab !== 'managers' && 'is-disabled']"
              type="button"
              @click="toggleAssignee(item.id)"
            >
              <div class="recipient-card-main">
                <strong>{{ item.name }}</strong>
                <small>{{ item.role || 'عضو سازمان' }}</small>
              </div>
              <div class="recipient-card-meta">
                <span>{{ item.department || 'بدون بخش' }}</span>
                <span class="material-symbols-outlined">{{ isSelected(item.id) ? 'check_circle' : 'add_circle' }}</span>
              </div>
            </button>
          </div>
          <div v-else class="empty-state-inline">
            <span class="material-symbols-outlined">person_search</span>
            <p>عضوی برای این جستجو پیدا نشد.</p>
          </div>
        </div>
      </section>

      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting || !state.documentForm.assigneeIds.length" type="button" @click="submitDocument">
          <span class="material-symbols-outlined">send</span>
          <span>{{ submitting ? 'در حال ارسال...' : 'ثبت سند' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
