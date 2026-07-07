<script setup>
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const referralOpen = ref(false)
const referralTab = ref('managers')
const referralSearch = ref('')

const {
  state,
  fieldHasError,
  setRequestFiles,
  removeAttachment,
  submitRequest,
  availableRecipientUsers,
} = useWorkflowHub()

const managerChoices = computed(() => state.directories.managers || [])
const employeeChoices = computed(() => availableRecipientUsers().filter((item) => item.accessRole === 'employee'))

const filteredManagers = computed(() => {
  const query = referralSearch.value.trim().toLowerCase()
  return managerChoices.value.filter((item) =>
    !query || `${item.name} ${item.role}`.toLowerCase().includes(query),
  )
})

const filteredEmployees = computed(() => {
  const query = referralSearch.value.trim().toLowerCase()
  return employeeChoices.value.filter((item) =>
    !query || `${item.name} ${item.role} ${item.department}`.toLowerCase().includes(query),
  )
})

function toggle(listKey, id) {
  const current = new Set((props.form[listKey] || []).map(Number))
  const numericId = Number(id)
  if (current.has(numericId)) current.delete(numericId)
  else current.add(numericId)
  props.form[listKey] = [...current]

  if (listKey === 'managerAssigneeIds') {
    const selectedManagers = managerChoices.value.filter((item) => props.form[listKey].map(Number).includes(Number(item.id)))
    const currentManagerSelected = selectedManagers.some((item) => item.slug === props.form.manager)
    props.form.manager = currentManagerSelected ? props.form.manager : selectedManagers[0]?.slug || ''
  }
}

function selectedNames() {
  const managerIds = (props.form.managerAssigneeIds || []).map(Number)
  const employeeIds = (props.form.employeeAssigneeIds || []).map(Number)
  const names = [
    ...managerChoices.value.filter((item) => managerIds.includes(Number(item.id))).map((item) => item.name),
    ...employeeChoices.value.filter((item) => employeeIds.includes(Number(item.id))).map((item) => item.name),
  ]
  return names.length ? names.join('، ') : 'تعیین نشده'
}

function openReferral() {
  referralSearch.value = ''
  referralTab.value = 'managers'
  referralOpen.value = true
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">درخواست جدید</p>
        <h2>ثبت و ارجاع درخواست</h2>
      </div>

      <div class="modal-grid two-col request-composer-grid">
        <label :class="['field-shell', fieldHasError('title') && 'has-error']">
          <span>عنوان</span>
          <input v-model="form.title" type="text" />
        </label>

        <label class="field-shell">
          <span>بخش</span>
          <select v-model="form.department">
            <option value="">انتخاب بخش</option>
            <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">
              {{ item.name }}
            </option>
          </select>
        </label>

        <label :class="['field-shell', fieldHasError('manager') && 'has-error']">
          <span>ارجاع گیرنده</span>
          <button class="action-btn tone-soft inline-open-btn" type="button" @click="openReferral">
            <span class="material-symbols-outlined">group_add</span>
            <span>{{ selectedNames() }}</span>
          </button>
        </label>

        <label :class="['field-shell', fieldHasError('description') && 'has-error']">
          <span>تاریخ</span>
          <ShamsiDatePicker v-model="form.deadline" model-type="jalali" placeholder="1405/04/01" />
        </label>

        <label class="field-shell">
          <span>اولویت</span>
          <div class="segmented-row">
            <button :class="['priority-chip', form.priority === 'low' && 'is-active']" type="button" @click="form.priority = 'low'">پایین</button>
            <button :class="['priority-chip', form.priority === 'medium' && 'is-active']" type="button" @click="form.priority = 'medium'">متوسط</button>
            <button :class="['priority-chip', form.priority === 'high' && 'is-active']" type="button" @click="form.priority = 'high'">بالا</button>
            <button :class="['priority-chip', form.priority === 'critical' && 'is-active']" type="button" @click="form.priority = 'critical'">بحرانی</button>
          </div>
        </label>

        <label class="field-shell">
          <span>توضیحات</span>
          <textarea v-model="form.description" rows="5"></textarea>
        </label>

        <label class="upload-pad compact-upload">
          <input type="file" multiple @change="setRequestFiles($event.target.files)" />
          <span class="material-symbols-outlined">attach_file</span>
          <strong>افزودن پیوست</strong>
          <small>اختیاری</small>
        </label>
      </div>

      <div v-if="form.attachments.length" class="file-list">
        <article v-for="(file, index) in form.attachments" :key="`${file.name}-${index}`" class="file-row">
          <div>
            <strong>{{ file.name }}</strong>
            <small>{{ Math.round(file.size / 1024) }} KB</small>
          </div>
          <button class="icon-btn" type="button" @click="removeAttachment(index)">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </article>
      </div>

      <ErrorNotice :error="state.lastErrorDetails" compact />
      <p class="request-flow-note">
        درخواست بعد از ثبت، برای گیرنده‌های انتخاب‌شده ارجاع می‌شود و تایید نهایی در این مرحله انجام نمی‌شود.
      </p>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting" type="button" @click="submitRequest">
          <span class="material-symbols-outlined">send</span>
          <span>{{ submitting ? 'در حال ثبت...' : 'ثبت و ارجاع' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>

  <BaseModal :open="referralOpen" size="detail" @close="referralOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">ارجاع درخواست</p>
        <h2>انتخاب گیرنده ها</h2>
      </div>

      <div class="filter-toolbar">
        <div class="chip-row">
          <button :class="['filter-chip', referralTab === 'managers' && 'is-active']" type="button" @click="referralTab = 'managers'">مدیران</button>
          <button :class="['filter-chip', referralTab === 'employees' && 'is-active']" type="button" @click="referralTab = 'employees'">کارمندان</button>
        </div>

        <label class="search-shell search-shell-wide">
          <span class="material-symbols-outlined">search</span>
          <input v-model="referralSearch" placeholder="جستجو" />
        </label>
      </div>

      <div class="recipient-grid">
        <button
          v-for="item in (referralTab === 'managers' ? filteredManagers : filteredEmployees)"
          :key="item.id"
          :class="[
            'recipient-card',
            (referralTab === 'managers' ? form.managerAssigneeIds : form.employeeAssigneeIds).map(Number).includes(Number(item.id)) && 'is-selected',
          ]"
          type="button"
          @click="toggle(referralTab === 'managers' ? 'managerAssigneeIds' : 'employeeAssigneeIds', item.id)"
        >
          <div class="recipient-card-main">
            <strong>{{ item.name }}</strong>
            <small>{{ item.role || item.department }}</small>
          </div>
          <span class="material-symbols-outlined">check_circle</span>
        </button>
      </div>

      <div class="modal-actions">
        <button class="action-btn tone-primary" type="button" @click="referralOpen = false">ثبت انتخاب ها</button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.compact-upload {
  grid-column: 1 / -1;
  width: 100%;
}

.inline-error {
  margin: 0;
  color: #b42318;
  font-size: 0.92rem;
}

.request-flow-note {
  margin: 0;
  color: #52607a;
  font-size: 0.92rem;
}

@media (max-width: 760px) {
  .modal-grid.two-col {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 420px) {
  .modal-grid.two-col {
    grid-template-columns: 1fr;
  }
}
</style>
