<script setup>
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  request: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])

const rejectOpen = ref(false)
const rejectReason = ref('')
const referOpen = ref(false)
const referTab = ref('managers')
const referSearch = ref('')
const referForm = reactive({
  manager: '',
  managerAssigneeIds: [],
  employeeAssigneeIds: [],
})

const {
  availableManagerDirectory,
  availableRecipientUsers,
  canApproveSelectedRequest,
  approveSelectedRequest,
  referSelectedRequest,
  rejectSelectedRequest,
  openProtectedFile,
  state,
} = useWorkflowHub()

const decisions = computed(() => props.request?.decisions || [])
const attachments = computed(() => props.request?.attachments || [])
const managerChoices = computed(() => availableManagerDirectory())
const employeeChoices = computed(() => availableRecipientUsers().filter((item) => item.accessRole === 'employee'))
const filteredManagers = computed(() => {
  const query = referSearch.value.trim().toLowerCase()
  return managerChoices.value.filter((item) => !query || `${item.name} ${item.role}`.toLowerCase().includes(query))
})
const filteredEmployees = computed(() => {
  const query = referSearch.value.trim().toLowerCase()
  return employeeChoices.value.filter((item) => !query || `${item.name} ${item.role} ${item.department}`.toLowerCase().includes(query))
})

watch(
  () => props.request?.id,
  () => {
    referForm.manager = ''
    referForm.managerAssigneeIds = []
    referForm.employeeAssigneeIds = []
    referSearch.value = ''
    referTab.value = 'managers'
  },
  { immediate: true },
)

function toggle(listKey, id) {
  const current = new Set((referForm[listKey] || []).map(Number))
  const numericId = Number(id)
  if (current.has(numericId)) current.delete(numericId)
  else current.add(numericId)
  referForm[listKey] = [...current]
  if (listKey === 'managerAssigneeIds') {
    const primary = managerChoices.value.find((item) => referForm.managerAssigneeIds.includes(Number(item.id)))
    referForm.manager = primary?.slug || ''
  }
}

async function submitReject() {
  await rejectSelectedRequest(rejectReason.value)
  rejectReason.value = ''
  rejectOpen.value = false
}

async function submitRefer() {
  await referSelectedRequest({
    manager: referForm.manager,
    managerAssigneeIds: referForm.managerAssigneeIds,
    employeeAssigneeIds: referForm.employeeAssigneeIds,
  })
  referOpen.value = false
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="request" class="detail-layout request-detail-modern">
      <div class="modal-headline">
        <p class="page-eyebrow">جزئیات درخواست</p>
        <h2>{{ request.title }}</h2>
      </div>

      <section class="detail-summary-grid">
        <article><span>کد</span><strong>{{ request.id }}</strong></article>
        <article><span>ثبت کننده</span><strong>{{ request.owner }}</strong></article>
        <article><span>بخش</span><strong>{{ request.department }}</strong></article>
        <article><span>وضعیت</span><strong>{{ request.status }}</strong></article>
        <article><span>اولویت</span><strong>{{ request.priority }}</strong></article>
        <article><span>تاریخ</span><strong>{{ request.deadline || request.createdAt || '-' }}</strong></article>
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>شرح درخواست</h3></div></div>
        <p class="long-text">{{ request.description || 'توضیحی ثبت نشده است.' }}</p>
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>وضعیت ارجاع گیرنده ها</h3></div><span class="meta-pill">{{ decisions.length }} نفر</span></div>
        <div v-if="decisions.length" class="decision-list">
          <article v-for="item in decisions" :key="item.id" :class="['decision-row', item.status]">
            <div><strong>{{ item.approver }}</strong><small>{{ item.role }}</small></div>
            <span>{{ item.statusLabel }}</span>
            <p v-if="item.decisionNote">{{ item.decisionNote }}</p>
          </article>
        </div>
        <div v-else class="empty-state-inline centered-empty"><span class="material-symbols-outlined">hourglass_empty</span><p>ارجاع گیرنده ای ثبت نشده است.</p></div>
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>فایل های پیوست</h3></div><span class="meta-pill">{{ attachments.length }}</span></div>
        <div v-if="attachments.length" class="file-list">
          <button v-for="file in attachments" :key="file.id" class="file-row file-button" type="button" @click="openProtectedFile(file.fileUrl, file.originalName)">
            <span class="material-symbols-outlined">attach_file</span>
            <strong>{{ file.originalName }}</strong>
          </button>
        </div>
        <div v-else class="empty-state-inline centered-empty"><span class="material-symbols-outlined">attach_file_off</span><p>فایل پیوست وارد نشده است.</p></div>
      </section>

      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')"><span class="material-symbols-outlined">close</span><span>بستن</span></button>
        <button v-if="canApproveSelectedRequest" class="action-btn tone-soft" type="button" @click="referOpen = true"><span class="material-symbols-outlined">forward</span><span>ارجاع</span></button>
        <button v-if="canApproveSelectedRequest" class="action-btn tone-danger" type="button" @click="rejectOpen = true"><span class="material-symbols-outlined">cancel</span><span>رد</span></button>
        <button v-if="canApproveSelectedRequest" class="action-btn tone-primary" type="button" @click="approveSelectedRequest"><span class="material-symbols-outlined">check_circle</span><span>تایید</span></button>
      </div>
    </div>
  </BaseModal>

  <BaseModal :open="rejectOpen" size="sm" @close="rejectOpen = false">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">علت رد</p><h2>توضیح رد درخواست</h2></div>
      <label class="field-shell"><span>علت رد</span><textarea v-model.trim="rejectReason" rows="4" /></label>
      <div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="rejectOpen = false">لغو</button><button class="action-btn tone-danger" :disabled="!rejectReason" type="button" @click="submitReject">ثبت رد</button></div>
    </div>
  </BaseModal>

  <BaseModal :open="referOpen" size="detail" @close="referOpen = false">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">ارجاع درخواست</p><h2>انتخاب ارجاع گیرنده جدید</h2></div>
      <div class="filter-toolbar">
        <div class="chip-row">
          <button :class="['filter-chip', referTab === 'managers' && 'is-active']" type="button" @click="referTab = 'managers'">مدیران</button>
          <button :class="['filter-chip', referTab === 'employees' && 'is-active']" type="button" @click="referTab = 'employees'">کارمندان</button>
        </div>
        <label class="search-shell search-shell-wide"><span class="material-symbols-outlined">search</span><input v-model="referSearch" placeholder="جستجو" /></label>
      </div>
      <div class="recipient-grid">
        <button v-for="item in (referTab === 'managers' ? filteredManagers : filteredEmployees)" :key="item.id" :class="['recipient-card', (referTab === 'managers' ? referForm.managerAssigneeIds : referForm.employeeAssigneeIds).map(Number).includes(Number(item.id)) && 'is-selected']" type="button" @click="toggle(referTab === 'managers' ? 'managerAssigneeIds' : 'employeeAssigneeIds', item.id)">
          <div class="recipient-card-main"><strong>{{ item.name }}</strong><small>{{ item.role || item.department }}</small></div>
          <span class="material-symbols-outlined">check_circle</span>
        </button>
      </div>
      <div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="referOpen = false">بستن</button><button class="action-btn tone-primary" type="button" :disabled="!referForm.managerAssigneeIds.length && !referForm.employeeAssigneeIds.length" @click="submitRefer">ثبت ارجاع</button></div>
    </div>
  </BaseModal>
</template>

<style scoped>
.request-detail-modern { gap: 16px; }
.detail-summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.detail-summary-grid article { display: grid; gap: 6px; padding: 14px; border-radius: 16px; background: rgba(72,103,183,.07); }
.detail-summary-grid span, .decision-row small { color: var(--muted); font-size: 12px; font-weight: 800; }
.detail-summary-grid strong { color: #203255; overflow-wrap: anywhere; }
.detail-section { display: grid; gap: 12px; }
.long-text { margin: 0; line-height: 2; color: #33415f; white-space: pre-wrap; }
.decision-list { display: grid; gap: 10px; }
.decision-row { display: grid; grid-template-columns: 1fr auto; gap: 6px 12px; padding: 12px; border-radius: 14px; background: #fff; border: 1px solid rgba(38,56,92,.08); }
.decision-row p { grid-column: 1 / -1; margin: 0; color: #8a3d3d; }
.decision-row.approved span { color: #176f52; }
.decision-row.rejected span { color: #ab4343; }
.file-button { width: 100%; border: 0; text-align: right; cursor: pointer; }
.inline-error { margin: 0; color: #b42318; }
.centered-empty {
  min-height: 180px;
  width: min(100%, 320px);
  margin-inline: auto;
  display: grid;
  place-items: center;
  justify-items: center;
  align-content: center;
  justify-content: center;
  text-align: center;
}
@media (max-width: 760px) { .detail-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .decision-row { grid-template-columns: 1fr; } }
@media (max-width: 420px) { .detail-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
