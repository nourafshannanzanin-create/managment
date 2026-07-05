<script setup>
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const referralPickerOpen = ref(false)
const referralTab = ref('managers')
const referralSearch = ref('')

const {
  state,
  requestManagerAssigneeOptions,
  requestManagerAssigneeNames,
  requestEmployeeAssigneeNames,
  setRequestManager,
  setRequestFiles,
  removeAttachment,
  submitRequest,
} = useWorkflowHub()

const managerChoices = computed(() => state.directories.managers || [])
const employeeChoices = computed(() =>
  (state.users || []).filter((item) => item.accessRole === 'employee'),
)

const filteredManagers = computed(() => {
  const query = referralSearch.value.trim().toLowerCase()
  const items = referralTab.value === 'managers' ? managerChoices.value : requestManagerAssigneeOptions.value
  if (!query) return items
  return items.filter((item) => [item.name, item.role].join(' ').toLowerCase().includes(query))
})

const filteredEmployees = computed(() => {
  const query = referralSearch.value.trim().toLowerCase()
  if (!query) return employeeChoices.value
  return employeeChoices.value.filter((item) =>
    [item.name, item.role, item.department].join(' ').toLowerCase().includes(query),
  )
})

function toggleEmployeeAssignee(id) {
  const current = new Set((state.requestForm.employeeAssigneeIds || []).map(Number))
  if (current.has(Number(id))) current.delete(Number(id))
  else current.add(Number(id))
  state.requestForm.employeeAssigneeIds = [...current]
}

function isEmployeeSelected(id) {
  return (state.requestForm.employeeAssigneeIds || []).map(Number).includes(Number(id))
}

function toggleManagerAssignee(id) {
  const current = new Set((state.requestForm.managerAssigneeIds || []).map(Number))
  if (current.has(Number(id))) current.delete(Number(id))
  else current.add(Number(id))
  state.requestForm.managerAssigneeIds = [...current]
}

function isManagerSelected(id) {
  return (state.requestForm.managerAssigneeIds || []).map(Number).includes(Number(id))
}

function openReferralPicker() {
  referralSearch.value = ''
  referralTab.value = 'managers'
  referralPickerOpen.value = true
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">درخواست جدید</p>
        <h2>ثبت درخواست سازمانی</h2>
      </div>

      <div class="modal-grid two-col request-composer-grid">
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

        <label class="field-shell">
          <span>ارجاع</span>
          <button class="action-btn tone-soft inline-open-btn" type="button" @click="openReferralPicker">
            <span class="material-symbols-outlined">group_add</span>
            <span>انتخاب مدیر و کارمند</span>
          </button>
        </label>

        <div class="field-shell referral-summary-shell">
          <span>خلاصه ارجاع</span>
          <div class="referral-summary-list">
            <small>مدیر اصلی: {{ managerChoices.find((item) => item.slug === form.manager)?.name || 'تعیین نشده' }}</small>
            <small>مدیران ارجاعی: {{ requestManagerAssigneeNames() }}</small>
            <small>کارمندان ارجاعی: {{ requestEmployeeAssigneeNames() }}</small>
          </div>
        </div>

        <label class="field-shell">
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

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-danger" :disabled="submitting" type="button" @click="submitRequest('reject')">
          <span class="material-symbols-outlined">cancel</span>
          <span>{{ submitting ? 'در حال ثبت...' : 'رد' }}</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting" type="button" @click="submitRequest('approve')">
          <span class="material-symbols-outlined">check_circle</span>
          <span>{{ submitting ? 'در حال ثبت...' : 'تایید' }}</span>
        </button>
        <button class="action-btn tone-soft" :disabled="submitting" type="button" @click="submitRequest('refer')">
          <span class="material-symbols-outlined">send</span>
          <span>{{ submitting ? 'در حال ثبت...' : 'ارجاع' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>

  <BaseModal :open="referralPickerOpen" size="detail" @close="referralPickerOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">ارجاع درخواست</p>
        <h2>انتخاب مدیر و کارمندان</h2>
      </div>

      <div class="filter-toolbar">
        <div class="chip-row">
          <button :class="['filter-chip', referralTab === 'managers' && 'is-active']" type="button" @click="referralTab = 'managers'">مدیران</button>
          <button :class="['filter-chip', referralTab === 'employees' && 'is-active']" type="button" @click="referralTab = 'employees'">کارمندان</button>
        </div>

        <label class="search-shell search-shell-wide">
          <span class="material-symbols-outlined">search</span>
          <input v-model="referralSearch" type="text" placeholder="جستجو در نام‌ها..." />
        </label>
      </div>

      <section v-if="referralTab === 'managers'" class="surface-inline recipient-selector">
        <div class="section-label-row">
          <div>
            <h3>مدیر اصلی</h3>
            <p>یک مدیر اصلی برای درخواست انتخاب کنید.</p>
          </div>
        </div>

        <div class="recipient-grid">
          <button
            v-for="item in filteredManagers"
            :key="`primary-${item.id}`"
            :class="['recipient-card', form.manager === item.slug && 'is-selected']"
            type="button"
            @click="setRequestManager(item.slug)"
          >
            <div class="recipient-card-main">
              <strong>{{ item.name }}</strong>
              <small>{{ item.role || 'مدیر' }}</small>
            </div>
            <div class="recipient-card-meta">
              <span>مدیر اصلی</span>
              <span class="material-symbols-outlined">{{ form.manager === item.slug ? 'check_circle' : 'radio_button_unchecked' }}</span>
            </div>
          </button>
        </div>

        <div class="section-label-row">
          <div>
            <h3>مدیران ارجاعی</h3>
            <p>در صورت نیاز مدیران دیگری را هم برای پیگیری انتخاب کنید.</p>
          </div>
        </div>

        <div class="recipient-grid">
          <button
            v-for="item in requestManagerAssigneeOptions"
            :key="`manager-${item.id}`"
            :class="['recipient-card', isManagerSelected(item.id) && 'is-selected']"
            type="button"
            @click="toggleManagerAssignee(item.id)"
          >
            <div class="recipient-card-main">
              <strong>{{ item.name }}</strong>
              <small>{{ item.role || 'مدیر' }}</small>
            </div>
            <div class="recipient-card-meta">
              <span>ارجاع مدیریتی</span>
              <span class="material-symbols-outlined">{{ isManagerSelected(item.id) ? 'check_circle' : 'add_circle' }}</span>
            </div>
          </button>
        </div>
      </section>

      <section v-else class="surface-inline recipient-selector">
        <div class="section-label-row">
          <div>
            <h3>کارمندان ارجاعی</h3>
            <p>نام کارمندان مورد نظر را برای پیگیری داخل درخواست ثبت کنید.</p>
          </div>
        </div>

        <div class="recipient-grid">
          <button
            v-for="item in filteredEmployees"
            :key="`employee-${item.id}`"
            :class="['recipient-card', isEmployeeSelected(item.id) && 'is-selected']"
            type="button"
            @click="toggleEmployeeAssignee(item.id)"
          >
            <div class="recipient-card-main">
              <strong>{{ item.name }}</strong>
              <small>{{ item.role || 'کارمند' }}</small>
            </div>
            <div class="recipient-card-meta">
              <span>{{ item.department || 'بدون بخش' }}</span>
              <span class="material-symbols-outlined">{{ isEmployeeSelected(item.id) ? 'check_circle' : 'add_circle' }}</span>
            </div>
          </button>
        </div>
      </section>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="referralPickerOpen = false">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" type="button" @click="referralPickerOpen = false">
          <span class="material-symbols-outlined">done</span>
          <span>ثبت انتخاب‌ها</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
