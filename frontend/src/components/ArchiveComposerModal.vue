<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import UserAvatar from './UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const activeRecipientTab = ref('employees')
const recipientSearch = ref('')

const {
  state,
  fieldHasError,
  setArchiveFile,
  submitArchiveDocument,
} = useWorkflowHub()

async function onArchiveFileChange(event) {
  const input = event.target
  try {
    await setArchiveFile(input?.files?.[0] || null)
  } catch {
    // ErrorNotice reads state.lastErrorDetails
  } finally {
    if (input) input.value = ''
  }
}

async function handleSubmit() {
  try {
    await submitArchiveDocument()
  } catch {
    // ErrorNotice reads state.lastErrorDetails
  }
}

const recipientGroups = computed(() => {
  const managerDirectory = (state.directories?.managers || []).map((item) => ({
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
    (item, index, array) =>
      item.id &&
      item.name &&
      Number(item.id) !== Number(state.currentUser.id) &&
      array.findIndex((entry) => Number(entry.id) === Number(item.id)) === index,
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

const departmentOptions = computed(() =>
  state.directories?.departments?.length
    ? state.directories.departments
    : state.settings?.departments || [],
)

function toggleAssignee(id) {
  const current = new Set(state.archiveForm.assigneeIds)
  if (current.has(id)) current.delete(id)
  else current.add(id)
  state.archiveForm.assigneeIds = [...current]
}

function isSelected(id) {
  return state.archiveForm.assigneeIds.includes(id)
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout archive-composer">
      <div class="modal-headline">
        <p class="page-eyebrow">بایگانی الکترونیکی</p>
        <h2>ثبت سند جدید</h2>
        <p>نام، توضیحات، تاریخ و فایل را مشخص کنید. ارجاع به افراد اختیاری است.</p>
      </div>

      <div class="modal-grid two-col">
        <label :class="['field-shell full-span', fieldHasError('title') && 'has-error']">
          <span>نام سند *</span>
          <input v-model="form.title" type="text" placeholder="مثلاً قرارداد همکاری ۱۴۰۵" />
        </label>

        <label class="field-shell full-span">
          <span>توضیحات سند</span>
          <textarea v-model="form.description" rows="3" placeholder="توضیح کوتاه درباره محتوا و کاربرد سند"></textarea>
        </label>

        <div :class="['field-shell', fieldHasError('documentDate') && 'has-error']">
          <span>تاریخ سند *</span>
          <ShamsiDatePicker v-model="form.documentDate" model-type="iso" placeholder="انتخاب تاریخ" />
        </div>

        <label class="field-shell">
          <span>بخش</span>
          <select v-model="form.departmentId">
            <option value="">بدون بخش مشخص</option>
            <option
              v-for="dept in departmentOptions"
              :key="dept.id || dept.code || dept.name"
              :value="String(dept.id || dept.code || '')"
            >
              {{ dept.name }}
            </option>
          </select>
        </label>

        <label :class="['upload-pad compact-upload full-span', fieldHasError('file') && 'has-error']">
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.webp,.gif,.pdf,.doc,.docx,.xls,.xlsx,.zip,.txt,image/*,application/pdf"
            :disabled="submitting || state.fileUploadPreparing"
            @change="onArchiveFileChange"
          />
          <IconlyIcon name="upload_file" decorative />
          <strong>
            {{
              state.fileUploadPreparing
                ? 'در حال آماده‌سازی فایل...'
                : (form.file?.name || 'بارگذاری فایل *')
            }}
          </strong>
          <small>PDF، تصویر، Word، Excel یا ZIP — حداکثر ۱۵ مگابایت</small>
        </label>
      </div>

      <section class="archive-recipients">
        <div class="archive-recipients-head">
          <div>
            <strong>ارجاع به افراد</strong>
            <small>اختیاری — افراد انتخاب‌شده سند را در بایگانی خود می‌بینند</small>
          </div>
          <div class="recipient-tabs">
            <button type="button" :class="['chip-btn', activeRecipientTab === 'employees' && 'is-active']" @click="activeRecipientTab = 'employees'">کارمندان</button>
            <button type="button" :class="['chip-btn', activeRecipientTab === 'managers' && 'is-active']" @click="activeRecipientTab = 'managers'">مدیران</button>
          </div>
        </div>

        <label class="search-shell">
          <IconlyIcon name="search" decorative />
          <input v-model="recipientSearch" type="search" placeholder="جستجوی نام یا سمت..." />
        </label>

        <div class="recipient-list">
          <button
            v-for="user in visibleRecipients"
            :key="user.id"
            type="button"
            :class="['recipient-card', isSelected(user.id) && 'is-selected']"
            @click="toggleAssignee(user.id)"
          >
            <UserAvatar :person="user" :name="user.name" size="sm" />
            <span>
              <strong>{{ user.name }}</strong>
              <small>{{ user.role || user.department || 'عضو مجموعه' }}</small>
            </span>
            <IconlyIcon :name="isSelected(user.id) ? 'check_circle' : 'add'" decorative />
          </button>
          <p v-if="!visibleRecipients.length" class="empty-hint">موردی پیدا نشد.</p>
        </div>
      </section>

      <ErrorNotice :error="state.lastErrorDetails" compact />

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <IconlyIcon name="close" decorative />
          <span>بستن</span>
        </button>
        <button
          class="action-btn tone-primary"
          type="button"
          :disabled="submitting || state.fileUploadPreparing"
          @click="handleSubmit"
        >
          <IconlyIcon name="upload_file" decorative />
          <span>{{ submitting ? 'در حال ثبت...' : 'ثبت در بایگانی' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.archive-composer .full-span { grid-column: 1 / -1; }
.archive-recipients {
  display: grid;
  gap: 12px;
  margin-top: 8px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(52, 144, 139, 0.05);
  border: 1px solid rgba(52, 144, 139, 0.12);
}
.archive-recipients-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.archive-recipients-head strong { display: block; color: #123735; }
.archive-recipients-head small { color: #5f7a76; }
.recipient-tabs { display: inline-flex; gap: 6px; }
.recipient-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  max-height: 220px;
  overflow: auto;
}
.recipient-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: #fff;
  text-align: right;
  cursor: pointer;
  font: inherit;
}
.recipient-card.is-selected {
  border-color: rgba(52, 144, 139, 0.4);
  background: rgba(52, 144, 139, 0.08);
}
.recipient-card strong,
.recipient-card small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recipient-card small { color: #5f7a76; font-size: 0.75rem; }
.empty-hint { margin: 0; color: #5f7a76; grid-column: 1 / -1; }
@media (max-width: 720px) {
  .recipient-list { grid-template-columns: 1fr; }
}
</style>
