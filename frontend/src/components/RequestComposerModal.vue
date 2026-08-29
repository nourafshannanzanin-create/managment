<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import TimePicker from './TimePicker.vue'
import UserAvatar from './UserAvatar.vue'
import VoiceDescriptionField from './VoiceDescriptionField.vue'
import { formatFileSize } from '../utils/uploads'
import {
  REQUEST_TYPE_OPTIONS,
  defaultTitleForRequestType,
  requestTypeConfig,
} from '../utils/requestTypeConfig'
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

const attachmentInputRef = ref(null)

async function onAttachmentChange(event) {
  const input = event.target
  try {
    await setRequestFiles(input?.files)
  } catch {
    // ErrorNotice reads state.lastErrorDetails
  } finally {
    if (input) input.value = ''
  }
}

const typeConfig = computed(() => requestTypeConfig(props.form.requestType || 'general'))
const isLeaveHourly = computed(() => props.form.requestType === 'leave_hourly')
const isLeaveDaily = computed(() => props.form.requestType === 'leave_daily')
const isLeave = computed(() => isLeaveHourly.value || isLeaveDaily.value)

const computedLeaveHours = computed(() => {
  if (!isLeaveHourly.value) return 0
  const start = String(props.form.leaveStartTime || '')
  const end = String(props.form.leaveEndTime || '')
  const [sh, sm] = start.split(':').map(Number)
  const [eh, em] = end.split(':').map(Number)
  if ([sh, sm, eh, em].some((item) => Number.isNaN(item))) return 0
  return Math.max(0, Math.round((((eh * 60 + em) - (sh * 60 + sm)) / 60) * 100) / 100)
})

const computedOvertimeHours = computed(() => {
  const start = String(props.form.overtimeStartTime || '')
  const end = String(props.form.overtimeEndTime || '')
  const [sh, sm] = start.split(':').map(Number)
  const [eh, em] = end.split(':').map(Number)
  if ([sh, sm, eh, em].some((item) => Number.isNaN(item))) return 0
  return Math.max(0, Math.round((((eh * 60 + em) - (sh * 60 + sm)) / 60) * 100) / 100)
})

const leaveSummaryRows = computed(() => {
  if (!isLeave.value) return []
  const rows = [
    { label: 'نوع', value: isLeaveDaily.value ? 'مرخصی روزانه' : 'مرخصی ساعتی' },
    { label: isLeaveDaily.value ? 'از تاریخ' : 'تاریخ', value: props.form.leaveStartDate || '—' },
  ]
  if (isLeaveDaily.value) {
    rows.push({ label: 'تا تاریخ', value: props.form.leaveEndDate || props.form.leaveStartDate || '—' })
  }
  if (isLeaveHourly.value) {
    rows.push(
      { label: 'از ساعت', value: props.form.leaveStartTime || '—' },
      { label: 'تا ساعت', value: props.form.leaveEndTime || '—' },
      { label: 'جمع ساعات', value: `${computedLeaveHours.value} ساعت` },
    )
  }
  return rows
})

const typeSummaryRows = computed(() => {
  const config = typeConfig.value
  const rows = [{ label: 'نوع', value: REQUEST_TYPE_OPTIONS.find((item) => item.value === props.form.requestType)?.label || '—' }]

  if (config.showPeriod) {
    rows.push(
      { label: config.periodStartLabel || 'از تاریخ', value: props.form.periodStartDate || '—' },
      { label: config.periodEndLabel || 'تا تاریخ', value: props.form.periodEndDate || '—' },
    )
  }
  if (config.showLocation && props.form.location) {
    rows.push({ label: config.locationLabel || 'محل', value: props.form.location })
  }
  if (config.showOvertime) {
    rows.push(
      { label: 'تاریخ', value: props.form.overtimeDate || '—' },
      { label: 'از ساعت', value: props.form.overtimeStartTime || '—' },
      { label: 'تا ساعت', value: props.form.overtimeEndTime || '—' },
      { label: 'جمع ساعات', value: `${computedOvertimeHours.value} ساعت` },
    )
  }
  if (config.showPurchase) {
    if (props.form.purchaseItem) rows.push({ label: 'کالا / خدمت', value: props.form.purchaseItem })
    if (props.form.estimatedAmount) rows.push({ label: 'مبلغ تقریبی', value: props.form.estimatedAmount })
  }
  if (config.showDeadline && props.form.deadline) {
    rows.push({ label: config.deadlineLabel || 'تاریخ', value: props.form.deadline })
  }
  return rows
})

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

watch(
  () => props.form.requestType,
  (next, prev) => {
    const defaultTitle = defaultTitleForRequestType(next)
    const prevDefault = defaultTitleForRequestType(prev)
    const currentTitle = String(props.form.title || '').trim()
    if (defaultTitle && (!currentTitle || currentTitle === prevDefault)) {
      props.form.title = defaultTitle
    }
  },
)
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout request-composer-shell">
      <div class="modal-headline">
        <p class="page-eyebrow">درخواست جدید</p>
        <h2>ثبت و ارجاع درخواست</h2>
      </div>

      <section class="request-type-banner">
        <div class="request-type-banner-copy">
          <IconlyIcon :name="REQUEST_TYPE_OPTIONS.find((item) => item.value === form.requestType)?.icon || 'assignment'" decorative />
          <div>
            <strong>{{ REQUEST_TYPE_OPTIONS.find((item) => item.value === form.requestType)?.label }}</strong>
            <small>{{ typeConfig.summaryTitle }}</small>
          </div>
        </div>
      </section>

      <div class="modal-grid two-col request-composer-grid">
        <label class="field-shell">
          <span>نوع درخواست</span>
          <select v-model="form.requestType">
            <option v-for="item in REQUEST_TYPE_OPTIONS" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </label>

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
            <IconlyIcon name="group_add" decorative />
            <span>{{ selectedNames() }}</span>
          </button>
        </label>

        <label v-if="typeConfig.showDeadline" :class="['field-shell', fieldHasError('description') && 'has-error']">
          <span>{{ typeConfig.deadlineLabel || 'تاریخ' }}</span>
          <ShamsiDatePicker v-model="form.deadline" model-type="jalali" placeholder="1405/04/01" />
        </label>

        <template v-if="typeConfig.showPeriod">
          <label :class="['field-shell', fieldHasError('periodStartDate') && 'has-error']">
            <span>{{ typeConfig.periodStartLabel || 'از تاریخ' }}</span>
            <ShamsiDatePicker v-model="form.periodStartDate" model-type="jalali" placeholder="1405/04/01" />
          </label>
          <label class="field-shell">
            <span>{{ typeConfig.periodEndLabel || 'تا تاریخ' }}</span>
            <ShamsiDatePicker v-model="form.periodEndDate" model-type="jalali" placeholder="1405/04/07" />
          </label>
        </template>

        <label v-if="typeConfig.showLocation" class="field-shell">
          <span>{{ typeConfig.locationLabel || 'محل' }}</span>
          <input v-model="form.location" type="text" placeholder="مثلاً شعبه مرکزی یا شهر مقصد" />
        </label>

        <template v-if="typeConfig.showOvertime">
          <label :class="['field-shell', fieldHasError('overtimeDate') && 'has-error']">
            <span>تاریخ اضافه‌کار</span>
            <ShamsiDatePicker v-model="form.overtimeDate" model-type="jalali" placeholder="1405/04/01" />
          </label>
          <label class="field-shell">
            <span>از ساعت</span>
            <TimePicker v-model="form.overtimeStartTime" :clearable="false" placeholder="انتخاب ساعت شروع" />
          </label>
          <label class="field-shell">
            <span>تا ساعت</span>
            <TimePicker v-model="form.overtimeEndTime" :clearable="false" placeholder="انتخاب ساعت پایان" />
          </label>
          <div class="field-shell">
            <span>جمع ساعات</span>
            <strong class="leave-hours-value">{{ computedOvertimeHours }} ساعت</strong>
          </div>
        </template>

        <template v-if="typeConfig.showPurchase">
          <label class="field-shell">
            <span>کالا / خدمت</span>
            <input v-model="form.purchaseItem" type="text" placeholder="نام کالا یا خدمت مورد نیاز" />
          </label>
          <label class="field-shell">
            <span>مبلغ تقریبی (ریال)</span>
            <input v-model="form.estimatedAmount" type="text" inputmode="numeric" placeholder="مثلاً ۵۰۰۰۰۰۰" />
          </label>
        </template>

        <template v-if="isLeave">
          <label :class="['field-shell', fieldHasError('leaveStartDate') && 'has-error']">
            <span>{{ isLeaveDaily ? 'از تاریخ' : 'تاریخ مرخصی' }}</span>
            <ShamsiDatePicker v-model="form.leaveStartDate" model-type="jalali" placeholder="1405/04/01" />
          </label>
          <label v-if="isLeaveDaily" class="field-shell">
            <span>تا تاریخ</span>
            <ShamsiDatePicker v-model="form.leaveEndDate" model-type="jalali" placeholder="1405/04/01" />
          </label>
          <template v-if="isLeaveHourly">
            <label class="field-shell">
              <span>از ساعت</span>
              <TimePicker v-model="form.leaveStartTime" :clearable="false" placeholder="انتخاب ساعت شروع" />
            </label>
            <label class="field-shell">
              <span>تا ساعت</span>
              <TimePicker v-model="form.leaveEndTime" :clearable="false" placeholder="انتخاب ساعت پایان" />
            </label>
            <div class="field-shell">
              <span>جمع ساعات</span>
              <strong class="leave-hours-value">{{ computedLeaveHours }} ساعت</strong>
            </div>
          </template>
        </template>

        <section v-if="isLeave && leaveSummaryRows.length" class="leave-summary-card full-width-field">
          <div class="section-label-row"><div><h3>خلاصه مرخصی</h3></div></div>
          <div class="leave-summary-grid">
            <article v-for="row in leaveSummaryRows" :key="row.label">
              <span>{{ row.label }}</span>
              <strong>{{ row.value }}</strong>
            </article>
          </div>
        </section>

        <section v-else-if="typeSummaryRows.length > 1" class="leave-summary-card full-width-field">
          <div class="section-label-row"><div><h3>{{ typeConfig.summaryTitle }}</h3></div></div>
          <div class="leave-summary-grid">
            <article v-for="row in typeSummaryRows" :key="row.label">
              <span>{{ row.label }}</span>
              <strong>{{ row.value }}</strong>
            </article>
          </div>
        </section>

        <label class="field-shell priority-field">
          <span>اولویت</span>
          <div class="segmented-row priority-strip">
            <button :class="['priority-chip', form.priority === 'low' && 'is-active']" type="button" @click="form.priority = 'low'">پایین</button>
            <button :class="['priority-chip', form.priority === 'medium' && 'is-active']" type="button" @click="form.priority = 'medium'">متوسط</button>
            <button :class="['priority-chip', form.priority === 'high' && 'is-active']" type="button" @click="form.priority = 'high'">بالا</button>
            <button :class="['priority-chip', form.priority === 'critical' && 'is-active']" type="button" @click="form.priority = 'critical'">بحرانی</button>
          </div>
        </label>

        <label class="upload-pad compact-upload">
          <input
            ref="attachmentInputRef"
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.webp,.gif,.pdf,image/*,application/pdf"
            :disabled="submitting || state.fileUploadPreparing"
            @change="onAttachmentChange"
          />
          <IconlyIcon name="attach_file" decorative />
          <strong>{{ state.fileUploadPreparing ? 'در حال آماده‌سازی فایل...' : 'افزودن پیوست' }}</strong>
          <small>{{ typeConfig.attachmentHint || 'اختیاری — حداکثر ۸ مگابایت' }}</small>
        </label>

        <div v-if="form.attachments.length" class="file-list attachment-list">
          <article v-for="(file, index) in form.attachments" :key="`${file.name}-${index}`" class="file-row">
            <div>
              <strong>{{ file.name }}</strong>
              <small>{{ formatFileSize(file.size) }}</small>
            </div>
            <button class="icon-btn" type="button" :disabled="submitting || state.fileUploadPreparing" @click="removeAttachment(index)">
              <IconlyIcon name="delete" decorative />
            </button>
          </article>
        </div>

        <VoiceDescriptionField
          class="full-width-field"
          :class="fieldHasError('description') && 'has-error'"
          v-model="form.description"
          v-model:voice-file="form.descriptionVoice"
          :label="typeConfig.descriptionLabel || 'توضیحات'"
          :placeholder="typeConfig.descriptionPlaceholder || ''"
          :rows="5"
          :disabled="submitting"
          :required="Boolean(typeConfig.requiresDescription)"
          :error="fieldHasError('description')"
        />
      </div>

      <ErrorNotice :error="state.lastErrorDetails" compact />
      <p class="request-flow-note">
        درخواست بعد از ثبت، برای گیرنده‌های انتخاب‌شده ارجاع می‌شود و تایید نهایی در این مرحله انجام نمی‌شود.
      </p>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <IconlyIcon name="close" decorative />
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting || state.fileUploadPreparing" type="button" @click="submitRequest">
          <IconlyIcon name="send" decorative />
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
          <IconlyIcon name="search" decorative />
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
            <UserAvatar :person="item" :name="item.name" size="sm" />
            <div class="recipient-card-copy">
              <strong>{{ item.name }}</strong>
              <small>{{ item.role || item.department }}</small>
            </div>
          </div>
          <IconlyIcon name="check_circle" decorative />
        </button>
      </div>

      <div class="modal-actions">
        <button class="action-btn tone-primary" type="button" @click="referralOpen = false">ثبت انتخاب ها</button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.request-composer-shell {
  gap: 14px;
}

.request-type-banner {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  background: linear-gradient(135deg, rgba(52, 144, 139, 0.1), rgba(72, 103, 183, 0.06));
}

.request-type-banner-copy {
  display: flex;
  align-items: center;
  gap: 12px;
}

.request-type-banner-copy strong {
  display: block;
  color: #1f3b55;
  font-size: 0.98rem;
}

.request-type-banner-copy small {
  color: #5f7a76;
  font-size: 12px;
}

.compact-upload {
  grid-column: 1 / -1;
  width: 100%;
}

.request-flow-note {
  margin: 0;
  color: #52607a;
  font-size: 0.92rem;
}

.priority-field {
  grid-column: 1 / -1;
}

.full-width-field,
.attachment-list {
  grid-column: 1 / -1;
}

.priority-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  width: 100%;
}

.priority-strip .priority-chip {
  width: 100%;
  min-width: 0;
  justify-content: center;
}

@media (max-width: 760px) {
  .modal-grid.two-col {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .priority-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.leave-hours-value {
  display: block;
  padding: 10px 12px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface-soft, #f3f6f4) 88%, white);
  font-size: 0.95rem;
}

.leave-summary-card {
  padding: 14px;
  border-radius: 16px;
  background: rgba(72, 103, 183, 0.07);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.leave-summary-card h3 {
  margin: 0;
  font-size: 0.95rem;
}

.leave-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.leave-summary-grid article {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
}

.leave-summary-grid span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.leave-summary-grid strong {
  color: #203255;
}
</style>
