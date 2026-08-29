<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import DecisionAssigneesList from './DecisionAssigneesList.vue'
import UserAvatar from './UserAvatar.vue'
import VoiceNotePlayer from './VoiceNotePlayer.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatTehranDateTime } from '../utils/jalali'
import { typePayloadSummaryRows } from '../utils/requestTypeConfig'

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
const editing = ref(false)
const saving = ref(false)
const referForm = reactive({
  manager: '',
  managerAssigneeIds: [],
  employeeAssigneeIds: [],
})
const editForm = reactive({
  title: '',
  description: '',
  priority: 'medium',
})
const noteBody = ref('')
const replyTo = ref(null)
const noteSubmitting = ref(false)

const {
  availableManagerDirectory,
  availableRecipientUsers,
  canApproveSelectedRequest,
  approveSelectedRequest,
  referSelectedRequest,
  rejectSelectedRequest,
  updateSelectedRequest,
  deleteSelectedRequest,
  addRequestNote,
  openProtectedFile,
  state,
} = useWorkflowHub()

const decisions = computed(() => props.request?.decisions || [])
const attachments = computed(() => props.request?.attachments || [])
const requestNotes = computed(() => props.request?.notes || [])
const typeDetailRows = computed(() => typePayloadSummaryRows(props.request?.requestType, props.request?.typePayload || {}))
const canEdit = computed(() => Boolean(props.request?.canEdit))
const canRefer = computed(() => Boolean(props.request?.canRefer || canApproveSelectedRequest.value))
const canDelete = computed(() => Boolean(props.request?.canDelete))
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
    editing.value = false
    syncEditForm()
  },
  { immediate: true },
)

watch(
  () => props.open,
  (open) => {
    if (open) {
      editing.value = false
      syncEditForm()
    }
  },
)

function syncEditForm() {
  editForm.title = props.request?.title || ''
  editForm.description = props.request?.description || ''
  editForm.priority = props.request?.priorityValue || 'medium'
}

function beginEdit() {
  syncEditForm()
  editing.value = true
}

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

async function saveEdit() {
  saving.value = true
  try {
    await updateSelectedRequest({
      title: editForm.title,
      description: editForm.description,
      priority: editForm.priority,
    })
    editing.value = false
  } finally {
    saving.value = false
  }
}

function formatLeaveDateTime(value) {
  if (!value) return '-'
  return formatTehranDateTime(value)
}

function leaveModeLabel(mode) {
  return mode === 'daily' ? 'روزانه' : mode === 'hourly' ? 'ساعتی' : mode || '-'
}

function formatDateTime(value) {
  if (!value) return '-'
  return formatTehranDateTime(value)
}

function isMyNote(note) {
  return Number(note?.author?.id) === Number(state.currentUser?.id)
}

function startReply(note) {
  replyTo.value = note
}

function cancelReply() {
  replyTo.value = null
}

async function submitNote() {
  const body = noteBody.value.trim()
  if (!body || !props.request?.id || noteSubmitting.value) return
  noteSubmitting.value = true
  try {
    await addRequestNote(props.request.id, body, replyTo.value?.id || null)
    noteBody.value = ''
    replyTo.value = null
  } finally {
    noteSubmitting.value = false
  }
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
        <article><span>نوع درخواست</span><strong>{{ request.requestTypeLabel || 'عمومی' }}</strong></article>
        <article><span>ثبت کننده</span><strong>{{ request.owner }}</strong></article>
        <article><span>بخش</span><strong>{{ request.department }}</strong></article>
        <article><span>وضعیت</span><strong>{{ request.status }}</strong></article>
        <article><span>اولویت</span><strong>{{ request.priority }}</strong></article>
        <article><span>تاریخ</span><strong>{{ request.deadline || request.createdAt || '-' }}</strong></article>
      </section>

      <section v-if="typeDetailRows.length" class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>جزئیات {{ request.requestTypeLabel || 'درخواست' }}</h3></div></div>
        <div class="detail-summary-grid">
          <article v-for="row in typeDetailRows" :key="row.label">
            <span>{{ row.label }}</span>
            <strong>{{ row.value }}</strong>
          </article>
        </div>
      </section>

      <section v-if="request.leave" class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>جزئیات مرخصی</h3></div></div>
        <div class="detail-summary-grid">
          <article><span>نوع مرخصی</span><strong>{{ leaveModeLabel(request.leave.mode) }}</strong></article>
          <article><span>شروع</span><strong>{{ formatLeaveDateTime(request.leave.startsAt) }}</strong></article>
          <article><span>پایان</span><strong>{{ formatLeaveDateTime(request.leave.endsAt) }}</strong></article>
          <article><span>مدت</span><strong>{{ request.leave.hours }} ساعت</strong></article>
          <article><span>وضعیت مرخصی</span><strong>{{ request.leave.statusLabel || request.leave.status || '-' }}</strong></article>
        </div>
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>{{ request.requestType === 'work_report' ? 'شرح فعالیت‌ها' : 'شرح درخواست' }}</h3></div></div>
        <template v-if="editing">
          <label class="field-shell"><span>عنوان</span><input v-model="editForm.title" type="text" /></label>
          <label class="field-shell"><span>اولویت</span>
            <select v-model="editForm.priority">
              <option value="low">پایین</option>
              <option value="medium">متوسط</option>
              <option value="high">بالا</option>
              <option value="critical">بحرانی</option>
            </select>
          </label>
          <label class="field-shell"><span>توضیحات</span><textarea v-model="editForm.description" rows="5" /></label>
        </template>
        <p v-else class="long-text">{{ request.description || 'توضیحی ثبت نشده است.' }}</p>
        <VoiceNotePlayer
          v-if="!editing && request.hasDescriptionVoice"
          :url="request.descriptionVoiceUrl"
          label="پیام صوتی توضیحات"
        />
      </section>

      <section class="surface-inline detail-section request-notes-panel">
        <div class="section-label-row">
          <div class="notes-heading">
            <IconlyIcon name="edit" decorative />
            <div>
              <h3>یادداشت‌های درخواست</h3>
              <small>ثبت توضیحات و پیگیری برای همه افراد دارای دسترسی</small>
            </div>
          </div>
          <span class="meta-pill">{{ request.noteCount || requestNotes.length }} یادداشت</span>
        </div>

        <div class="notes-feed">
          <article
            v-for="item in requestNotes"
            :key="item.id"
            :class="['note-card', isMyNote(item) && 'is-mine']"
          >
            <UserAvatar :person="item.author" :name="item.author?.name" size="sm" />
            <div class="note-card-body">
              <div class="note-card-head">
                <div class="note-author-meta">
                  <strong>{{ item.author?.name || 'کاربر' }}</strong>
                  <span v-if="item.author?.role" class="note-role-pill">{{ item.author.role }}</span>
                </div>
                <small>{{ formatDateTime(item.createdAt) }}</small>
              </div>
              <div v-if="item.parent" class="note-reply-ref">
                <small>پاسخ به {{ item.parent.author?.name || 'یادداشت' }}</small>
                <p>{{ item.parent.body }}</p>
              </div>
              <p class="note-body">{{ item.body }}</p>
              <button class="linkish" type="button" @click="startReply(item)">پاسخ</button>
            </div>
          </article>
          <div v-if="!requestNotes.length" class="empty-state-inline centered-empty notes-empty">
            <IconlyIcon name="edit" decorative />
            <p>هنوز یادداشتی ثبت نشده است.</p>
          </div>
        </div>

        <div class="notes-composer">
          <div v-if="replyTo" class="reply-banner">
            <span>پاسخ به {{ replyTo.author?.name }}</span>
            <button type="button" aria-label="لغو پاسخ" @click="cancelReply">×</button>
          </div>
          <label class="field-shell notes-field">
            <span>یادداشت جدید</span>
            <textarea v-model="noteBody" rows="3" placeholder="یادداشت خود را بنویسید..." @keydown.ctrl.enter.prevent="submitNote" />
          </label>
          <div class="notes-composer-actions">
            <button class="action-btn tone-primary" type="button" :disabled="!noteBody.trim() || noteSubmitting" @click="submitNote">
              {{ noteSubmitting ? 'در حال ارسال...' : 'ثبت یادداشت' }}
            </button>
          </div>
        </div>
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>وضعیت ارجاع گیرنده ها</h3></div><span class="meta-pill">{{ decisions.length }} نفر</span></div>
        <DecisionAssigneesList :decisions="decisions" />
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row"><div><h3>فایل های پیوست</h3></div><span class="meta-pill">{{ attachments.length }}</span></div>
        <div v-if="attachments.length" class="file-list">
          <button v-for="file in attachments" :key="file.id" class="file-row file-button" type="button" @click="openProtectedFile(file.fileUrl, file.originalName)">
            <IconlyIcon name="attach_file" decorative />
            <strong>{{ file.originalName }}</strong>
          </button>
        </div>
        <div v-else class="empty-state-inline centered-empty"><IconlyIcon name="attach_file_off" decorative /><p>فایل پیوست وارد نشده است.</p></div>
      </section>

      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')"><IconlyIcon name="close" decorative /><span>بستن</span></button>
        <button v-if="canDelete" class="action-btn tone-danger" type="button" @click="deleteSelectedRequest"><IconlyIcon name="delete" decorative /><span>حذف</span></button>
        <button v-if="canEdit && !editing" class="action-btn tone-soft" type="button" @click="beginEdit"><IconlyIcon name="edit" decorative /><span>ویرایش</span></button>
        <button v-if="editing" class="action-btn tone-soft" type="button" @click="editing = false">انصراف</button>
        <button v-if="editing" class="action-btn tone-primary" type="button" :disabled="saving" @click="saveEdit">{{ saving ? 'در حال ذخیره...' : 'ذخیره' }}</button>
        <button v-if="canRefer && !editing" class="action-btn tone-soft" type="button" @click="referOpen = true"><IconlyIcon name="forward" decorative /><span>ارجاع</span></button>
        <button v-if="canApproveSelectedRequest && !editing" class="action-btn tone-danger" type="button" @click="rejectOpen = true"><IconlyIcon name="cancel" decorative /><span>رد</span></button>
        <button v-if="canApproveSelectedRequest && !editing" class="action-btn tone-primary" type="button" @click="approveSelectedRequest"><IconlyIcon name="check_circle" decorative /><span>تایید</span></button>
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
        <label class="search-shell search-shell-wide"><IconlyIcon name="search" decorative /><input v-model="referSearch" placeholder="جستجو" /></label>
      </div>
      <div class="recipient-grid">
        <button v-for="item in (referTab === 'managers' ? filteredManagers : filteredEmployees)" :key="item.id" :class="['recipient-card', (referTab === 'managers' ? referForm.managerAssigneeIds : referForm.employeeAssigneeIds).map(Number).includes(Number(item.id)) && 'is-selected']" type="button" @click="toggle(referTab === 'managers' ? 'managerAssigneeIds' : 'employeeAssigneeIds', item.id)">
          <div class="recipient-card-main"><UserAvatar :person="item" :name="item.name" size="sm" /><div class="recipient-card-copy"><strong>{{ item.name }}</strong><small>{{ item.role || item.department }}</small></div></div>
          <IconlyIcon name="check_circle" decorative />
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
.detail-summary-grid span { color: var(--muted); font-size: 12px; font-weight: 800; }
.detail-summary-grid strong { color: #203255; overflow-wrap: anywhere; }
.detail-section { display: grid; gap: 12px; }
.long-text { margin: 0; line-height: 2; color: #33415f; white-space: pre-wrap; }
.file-button { width: 100%; border: 0; text-align: right; cursor: pointer; }
.inline-error { margin: 0; color: #b42318; }
.request-notes-panel { gap: 14px; }
.notes-heading { display: flex; align-items: flex-start; gap: 10px; }
.notes-feed { display: grid; gap: 10px; max-height: 280px; overflow: auto; padding-inline: 2px; }
.note-card { display: grid; grid-template-columns: auto 1fr; gap: 10px; padding: 12px; border-radius: 14px; background: rgba(72, 103, 183, 0.06); }
.note-card.is-mine { background: rgba(52, 144, 139, 0.1); }
.note-card-body { display: grid; gap: 8px; min-width: 0; }
.note-card-head { display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; }
.note-author-meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.note-role-pill { font-size: 11px; padding: 2px 8px; border-radius: 999px; background: rgba(72, 103, 183, 0.12); color: #4867b7; }
.note-body { margin: 0; line-height: 1.8; white-space: pre-wrap; }
.note-reply-ref { padding: 8px 10px; border-radius: 10px; background: rgba(255, 255, 255, 0.7); border-inline-start: 3px solid rgba(52, 144, 139, 0.45); }
.note-reply-ref p { margin: 4px 0 0; font-size: 12px; color: #5f7a76; }
.notes-composer { display: grid; gap: 10px; }
.reply-banner { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-radius: 10px; background: rgba(52, 144, 139, 0.08); font-size: 12px; }
.notes-composer-actions { display: flex; justify-content: flex-end; }
.linkish { border: 0; background: transparent; color: #34908b; cursor: pointer; font: inherit; padding: 0; justify-self: start; }
@media (max-width: 760px) { .detail-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
