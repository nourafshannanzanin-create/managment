<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, reactive, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import DecisionAssigneesList from './DecisionAssigneesList.vue'
import UserAvatar from './UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({ open: { type: Boolean, default: false }, expense: { type: Object, default: null }, loading: { type: Boolean, default: false } })
defineEmits(['close'])

const rejectOpen = ref(false)
const rejectReason = ref('')
const referOpen = ref(false)
const referTab = ref('managers')
const referSearch = ref('')
const referForm = reactive({ managerAssigneeIds: [], employeeAssigneeIds: [] })

const { availableManagerDirectory, availableRecipientUsers, canApproveSelectedExpense, approveSelectedExpense, rejectSelectedExpense, referSelectedExpense, openProtectedFile, state } = useWorkflowHub()
const decisions = computed(() => props.expense?.decisions || [])
const managerChoices = computed(() => availableManagerDirectory())
const employeeChoices = computed(() => availableRecipientUsers().filter((item) => item.accessRole === 'employee'))
const filteredManagers = computed(() => managerChoices.value.filter((item) => !referSearch.value || `${item.name} ${item.role}`.toLowerCase().includes(referSearch.value.toLowerCase())))
const filteredEmployees = computed(() => employeeChoices.value.filter((item) => !referSearch.value || `${item.name} ${item.role} ${item.department}`.toLowerCase().includes(referSearch.value.toLowerCase())))

function toggle(listKey, id) {
  const current = new Set((referForm[listKey] || []).map(Number))
  if (current.has(Number(id))) current.delete(Number(id))
  else current.add(Number(id))
  referForm[listKey] = [...current]
}

async function submitReject() { await rejectSelectedExpense(rejectReason.value); rejectReason.value = ''; rejectOpen.value = false }
async function submitRefer() { await referSelectedExpense({ managerAssigneeIds: referForm.managerAssigneeIds, employeeAssigneeIds: referForm.employeeAssigneeIds }); referOpen.value = false }
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="expense" class="detail-layout expense-detail-modern">
      <div class="modal-headline"><p class="page-eyebrow">جزئیات هزینه</p><h2>{{ expense.title }}</h2></div>
      <section class="detail-summary-grid">
        <article><span>کد</span><strong>{{ expense.id }}</strong></article><article><span>ثبت کننده</span><strong>{{ expense.owner }}</strong></article><article><span>مبلغ (تومان)</span><strong>{{ expense.amount }}</strong></article><article><span>بخش</span><strong>{{ expense.department }}</strong></article><article><span>وضعیت</span><strong>{{ expense.status }}</strong></article><article><span>تاریخ</span><strong>{{ expense.submittedAt }}</strong></article>
      </section>
      <section class="surface-inline detail-section"><div class="section-label-row"><div><h3>شرح هزینه</h3></div></div><p class="long-text">{{ expense.description || '-' }}</p></section>
      <section class="surface-inline detail-section"><div class="section-label-row"><div><h3>تصمیم ارجاع گیرنده ها</h3></div><span class="meta-pill">{{ decisions.length }} نفر</span></div><DecisionAssigneesList :decisions="decisions" /></section>
      <section class="surface-inline detail-section"><div class="section-label-row"><div><h3>فاکتور</h3></div></div><button v-if="expense.invoiceUrl" class="action-btn tone-primary" type="button" @click="openProtectedFile(expense.invoiceUrl, expense.invoiceName || 'invoice')"><IconlyIcon name="description" decorative /><span>مشاهده فایل</span></button><div v-else class="empty-state-inline centered-empty"><IconlyIcon name="description" decorative /><p>فایل پیوست وارد نشده است.</p></div></section>
      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>
      <div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="$emit('close')">بستن</button><button v-if="canApproveSelectedExpense" class="action-btn tone-soft" type="button" @click="referOpen = true">ارجاع</button><button v-if="canApproveSelectedExpense" class="action-btn tone-danger" type="button" @click="rejectOpen = true">رد</button><button v-if="canApproveSelectedExpense" class="action-btn tone-primary" type="button" @click="approveSelectedExpense">تایید</button></div>
    </div>
  </BaseModal>
  <BaseModal :open="rejectOpen" size="sm" @close="rejectOpen = false"><div class="detail-layout"><div class="modal-headline"><p class="page-eyebrow">علت رد</p><h2>توضیح رد هزینه</h2></div><label class="field-shell"><span>علت رد</span><textarea v-model.trim="rejectReason" rows="4" /></label><div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="rejectOpen = false">لغو</button><button class="action-btn tone-danger" :disabled="!rejectReason" type="button" @click="submitReject">ثبت رد</button></div></div></BaseModal>
  <BaseModal :open="referOpen" size="detail" @close="referOpen = false"><div class="detail-layout"><div class="modal-headline"><p class="page-eyebrow">ارجاع هزینه</p><h2>انتخاب گیرنده جدید</h2></div><div class="filter-toolbar"><div class="chip-row"><button :class="['filter-chip', referTab === 'managers' && 'is-active']" type="button" @click="referTab = 'managers'">مدیران</button><button :class="['filter-chip', referTab === 'employees' && 'is-active']" type="button" @click="referTab = 'employees'">کارمندان</button></div><label class="search-shell search-shell-wide"><IconlyIcon name="search" decorative /><input v-model="referSearch" placeholder="جستجو" /></label></div><div class="recipient-grid"><button v-for="item in (referTab === 'managers' ? filteredManagers : filteredEmployees)" :key="item.id" :class="['recipient-card', (referTab === 'managers' ? referForm.managerAssigneeIds : referForm.employeeAssigneeIds).map(Number).includes(Number(item.id)) && 'is-selected']" type="button" @click="toggle(referTab === 'managers' ? 'managerAssigneeIds' : 'employeeAssigneeIds', item.id)"><div class="recipient-card-main"><UserAvatar :person="item" :name="item.name" size="sm" /><div class="recipient-card-copy"><strong>{{ item.name }}</strong><small>{{ item.role || item.department }}</small></div></div><IconlyIcon name="check_circle" decorative /></button></div><div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="referOpen = false">بستن</button><button class="action-btn tone-primary" type="button" :disabled="!referForm.managerAssigneeIds.length && !referForm.employeeAssigneeIds.length" @click="submitRefer">ثبت ارجاع</button></div></div></BaseModal>
</template>

<style scoped>
.detail-summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.detail-summary-grid article { display: grid; gap: 6px; padding: 14px; border-radius: 16px; background: rgba(72,103,183,.07); }
.detail-summary-grid span { color: var(--muted); font-size: 12px; font-weight: 800; }
.detail-section { display: grid; gap: 12px; }
.long-text { margin: 0; line-height: 2; white-space: pre-wrap; }
.inline-error { color: #b42318; }
@media (max-width: 760px) { .detail-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 420px) { .detail-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
