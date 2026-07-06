<script setup>
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
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

const { state, fieldHasError, setExpenseInvoice, submitExpense } = useWorkflowHub()

const managerChoices = computed(() => state.directories.managers || [])
const employeeChoices = computed(() => (state.users || []).filter((item) => item.accessRole === 'employee'))
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
        <label :class="['field-shell', fieldHasError('amount') && 'has-error']"><span>مبلغ</span><input v-model="form.amount" inputmode="decimal" placeholder="0" @input="form.amount = formatAmountInput($event.target.value)" /></label>
        <label class="field-shell"><span>تاریخ</span><ShamsiDatePicker v-model="form.expenseDate" model-type="jalali" /></label>
        <label class="field-shell"><span>بخش</span><select v-model="form.department"><option value="">انتخاب بخش</option><option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option></select></label>
        <label class="field-shell"><span>ارجاع گیرنده</span><button class="action-btn tone-soft inline-open-btn" type="button" @click="referralOpen = true"><span class="material-symbols-outlined">group_add</span><span>{{ selectedNames() }}</span></button></label>
      </div>

      <label :class="['field-shell', fieldHasError('description') && 'has-error']"><span>شرح</span><textarea v-model="form.description" rows="4" /></label>
      <label class="upload-pad compact-upload"><input type="file" accept="image/*,.pdf" @change="setExpenseInvoice($event.target.files?.[0])" /><span class="material-symbols-outlined">receipt_long</span><strong>{{ form.invoice?.name || 'افزودن فاکتور' }}</strong><small>اختیاری</small></label>
      <ErrorNotice :error="state.lastErrorDetails" compact />
      <div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="$emit('close')"><span class="material-symbols-outlined">close</span><span>بستن</span></button><button class="action-btn tone-primary" :disabled="submitting" type="button" @click="submitExpense('refer')"><span class="material-symbols-outlined">send</span><span>{{ submitting ? 'در حال ثبت...' : 'ثبت و ارجاع' }}</span></button></div>
    </div>
  </BaseModal>

  <BaseModal :open="referralOpen" size="detail" @close="referralOpen = false">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">ارجاع هزینه</p><h2>انتخاب گیرنده ها</h2></div>
      <div class="filter-toolbar"><div class="chip-row"><button :class="['filter-chip', referralTab === 'managers' && 'is-active']" type="button" @click="referralTab = 'managers'">مدیران</button><button :class="['filter-chip', referralTab === 'employees' && 'is-active']" type="button" @click="referralTab = 'employees'">کارمندان</button></div><label class="search-shell search-shell-wide"><span class="material-symbols-outlined">search</span><input v-model="referralSearch" placeholder="جستجو" /></label></div>
      <div class="recipient-grid">
        <button v-for="item in (referralTab === 'managers' ? filteredManagers : filteredEmployees)" :key="item.id" :class="['recipient-card', (referralTab === 'managers' ? form.managerAssigneeIds : form.employeeAssigneeIds).map(Number).includes(Number(item.id)) && 'is-selected']" type="button" @click="toggle(referralTab === 'managers' ? 'managerAssigneeIds' : 'employeeAssigneeIds', item.id)"><div class="recipient-card-main"><strong>{{ item.name }}</strong><small>{{ item.role || item.department }}</small></div><span class="material-symbols-outlined">check_circle</span></button>
      </div>
      <div class="modal-actions"><button class="action-btn tone-primary" type="button" @click="referralOpen = false">ثبت انتخاب ها</button></div>
    </div>
  </BaseModal>
</template>

<style scoped>
.inline-error { margin: 0; color: #b42318; }
@media (max-width: 760px) { .modal-grid.two-col { grid-template-columns: 1fr; } }
</style>
