<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import UserAvatar from './UserAvatar.vue'
import SubmitAreaAlert from './SubmitAreaAlert.vue'
import VoiceDescriptionField from './VoiceDescriptionField.vue'
import { formatAmountInput } from '../utils/amount'
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

const { state, fieldHasError, setExpenseInvoice, submitExpense, availableRecipientUsers } = useWorkflowHub()

async function onInvoiceChange(event) {
  const input = event.target
  try {
    await setExpenseInvoice(input?.files?.[0] || null)
  } catch {
    // ErrorNotice reads state.lastErrorDetails
  } finally {
    if (input) input.value = ''
  }
}

const managerChoices = computed(() => state.directories.managers || [])
const employeeChoices = computed(() => availableRecipientUsers().filter((item) => item.accessRole === 'employee'))
const filteredManagers = computed(() => managerChoices.value.filter((item) => !referralSearch.value || `${item.name} ${item.role}`.toLowerCase().includes(referralSearch.value.toLowerCase())))
const filteredEmployees = computed(() => employeeChoices.value.filter((item) => !referralSearch.value || `${item.name} ${item.role} ${item.department}`.toLowerCase().includes(referralSearch.value.toLowerCase())))

function toggle(listKey, id) {
  const current = new Set((props.form[listKey] || []).map(Number))
  if (current.has(Number(id))) current.delete(Number(id))
  else current.add(Number(id))
  props.form[listKey] = [...current]
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
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">هزینه جدید</p><h2>ثبت و ارجاع هزینه</h2></div>

      <div class="modal-grid two-col">
        <label :class="['field-shell', fieldHasError('amount') && 'has-error']"><span>مبلغ (تومان)</span><input v-model="form.amount" inputmode="numeric" placeholder="0" @input="form.amount = formatAmountInput($event.target.value)" /></label>
        <label class="field-shell"><span>تاریخ</span><ShamsiDatePicker v-model="form.expenseDate" model-type="jalali" /></label>
        <label class="field-shell"><span>بخش</span><select v-model="form.department"><option value="">انتخاب بخش</option><option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option></select></label>
        <label class="field-shell"><span>ارجاع گیرنده</span><button class="action-btn tone-soft inline-open-btn" type="button" @click="referralOpen = true"><IconlyIcon name="group_add" decorative /><span>{{ selectedNames() }}</span></button></label>
      </div>

      <VoiceDescriptionField
        class="full-width-field"
        :class="fieldHasError('description') && 'has-error'"
        v-model="form.description"
        v-model:voice-file="form.descriptionVoice"
        label="شرح"
        :rows="4"
        :disabled="submitting"
        :error="fieldHasError('description')"
      />
      <label class="upload-pad compact-upload full-width-field">
        <input
          type="file"
          accept=".jpg,.jpeg,.png,.webp,.gif,.pdf,image/*,application/pdf"
          :disabled="submitting || state.fileUploadPreparing"
          @change="onInvoiceChange"
        />
        <IconlyIcon name="receipt_long" decorative />
        <strong>{{ state.fileUploadPreparing ? 'در حال آماده‌سازی فایل...' : (form.invoice?.name || 'افزودن فاکتور') }}</strong>
        <small>اختیاری — حداکثر ۸ مگابایت</small>
      </label>
      <SubmitAreaAlert />
      <div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="$emit('close')"><IconlyIcon name="close" decorative /><span>بستن</span></button><button class="action-btn tone-primary" :disabled="submitting || state.fileUploadPreparing" type="button" @click="submitExpense('refer')"><IconlyIcon name="send" decorative /><span>{{ submitting ? 'در حال ثبت...' : 'ثبت و ارجاع' }}</span></button></div>
    </div>
  </BaseModal>

  <BaseModal :open="referralOpen" size="detail" @close="referralOpen = false">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">ارجاع هزینه</p><h2>انتخاب گیرنده ها</h2></div>
      <div class="filter-toolbar"><div class="chip-row"><button :class="['filter-chip', referralTab === 'managers' && 'is-active']" type="button" @click="referralTab = 'managers'">مدیران</button><button :class="['filter-chip', referralTab === 'employees' && 'is-active']" type="button" @click="referralTab = 'employees'">کارمندان</button></div><label class="search-shell search-shell-wide"><IconlyIcon name="search" decorative /><input v-model="referralSearch" placeholder="جستجو" /></label></div>
      <div class="recipient-grid">
        <button v-for="item in (referralTab === 'managers' ? filteredManagers : filteredEmployees)" :key="item.id" :class="['recipient-card', (referralTab === 'managers' ? form.managerAssigneeIds : form.employeeAssigneeIds).map(Number).includes(Number(item.id)) && 'is-selected']" type="button" @click="toggle(referralTab === 'managers' ? 'managerAssigneeIds' : 'employeeAssigneeIds', item.id)"><div class="recipient-card-main"><UserAvatar :person="item" :name="item.name" size="sm" /><div class="recipient-card-copy"><strong>{{ item.name }}</strong><small>{{ item.role || item.department }}</small></div></div><IconlyIcon name="check_circle" decorative /></button>
      </div>
      <div class="modal-actions"><button class="action-btn tone-primary" type="button" @click="referralOpen = false">ثبت انتخاب ها</button></div>
    </div>
  </BaseModal>
</template>

<style scoped>
.inline-error { margin: 0; color: #b42318; }
.full-width-field { width: 100%; }
@media (max-width: 760px) { .modal-grid.two-col { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
