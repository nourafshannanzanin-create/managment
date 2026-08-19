<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import DecisionAssigneesList from './DecisionAssigneesList.vue'
import UserAvatar from './UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatTehranDateTime } from '../utils/jalali'

const props = defineProps({ open: { type: Boolean, default: false }, expense: { type: Object, default: null }, loading: { type: Boolean, default: false } })
defineEmits(['close'])

const rejectOpen = ref(false)
const rejectReason = ref('')
const referOpen = ref(false)
const referTab = ref('managers')
const referSearch = ref('')
const referForm = reactive({ managerAssigneeIds: [], employeeAssigneeIds: [] })
const noteBody = ref('')
const replyTo = ref(null)
const noteSubmitting = ref(false)

const {
  availableManagerDirectory,
  availableRecipientUsers,
  canApproveSelectedExpense,
  approveSelectedExpense,
  rejectSelectedExpense,
  referSelectedExpense,
  addExpenseNote,
  openProtectedFile,
  state,
} = useWorkflowHub()

const decisions = computed(() => props.expense?.decisions || [])
const expenseNotes = computed(() => props.expense?.notes || [])
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

function formatDateTime(value) {
  return formatTehranDateTime(value) || '-'
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

async function submitReject() {
  await rejectSelectedExpense(rejectReason.value)
  rejectReason.value = ''
  rejectOpen.value = false
}

async function submitRefer() {
  await referSelectedExpense({ managerAssigneeIds: referForm.managerAssigneeIds, employeeAssigneeIds: referForm.employeeAssigneeIds })
  referOpen.value = false
}

async function submitNote() {
  const body = noteBody.value.trim()
  if (!body || !props.expense?.id || noteSubmitting.value) return
  noteSubmitting.value = true
  try {
    await addExpenseNote(props.expense.id, body, replyTo.value?.id || null)
    noteBody.value = ''
    replyTo.value = null
  } finally {
    noteSubmitting.value = false
  }
}

watch(
  () => props.expense?.id,
  () => {
    noteBody.value = ''
    replyTo.value = null
  },
)
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="expense" class="detail-layout expense-detail-modern">
      <div class="modal-headline">
        <p class="page-eyebrow">جزئیات هزینه</p>
        <h2>{{ expense.title }}</h2>
      </div>

      <section class="detail-summary-grid">
        <article><span>کد</span><strong>{{ expense.id }}</strong></article>
        <article><span>ثبت کننده</span><strong>{{ expense.owner }}</strong></article>
        <article><span>مبلغ (تومان)</span><strong>{{ expense.amount }}</strong></article>
        <article><span>بخش</span><strong>{{ expense.department }}</strong></article>
        <article><span>وضعیت</span><strong>{{ expense.status }}</strong></article>
        <article><span>تاریخ</span><strong>{{ expense.submittedAt }}</strong></article>
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row">
          <div><h3>شرح هزینه</h3></div>
        </div>
        <p class="long-text">{{ expense.description || '-' }}</p>
      </section>

      <section class="surface-inline detail-section expense-notes-panel">
        <div class="section-label-row">
          <div class="notes-heading">
            <IconlyIcon name="edit" decorative />
            <div>
              <h3>یادداشت‌های هزینه</h3>
              <small>ثبت توضیحات، پیگیری و هماهنگی بین ثبت‌کننده و ارجاع‌گیرندگان</small>
            </div>
          </div>
          <span class="meta-pill">{{ expense.noteCount || expenseNotes.length }} یادداشت</span>
        </div>

        <div class="notes-feed">
          <article
            v-for="item in expenseNotes"
            :key="item.id"
            :class="['note-card', isMyNote(item) && 'is-mine']"
          >
            <UserAvatar :person="item.author" :name="item.author?.name" size="sm" />
            <div class="note-card-body">
              <div class="note-card-head">
                <div class="note-author-meta">
                  <strong>{{ item.author?.name || 'کاربر' }}</strong>
                  <span v-if="item.author?.role" class="note-role-pill">{{ item.author.role }}</span>
                  <span v-if="isMyNote(item)" class="note-mine-pill">شما</span>
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

          <div v-if="!expenseNotes.length" class="empty-state-inline centered-empty notes-empty">
            <IconlyIcon name="edit" decorative />
            <p>هنوز یادداشتی ثبت نشده است.</p>
            <small>اولین یادداشت را برای پیگیری یا توضیح بیشتر بنویسید.</small>
          </div>
        </div>

        <div class="notes-composer">
          <div v-if="replyTo" class="reply-banner">
            <span>پاسخ به {{ replyTo.author?.name }}</span>
            <button type="button" aria-label="لغو پاسخ" @click="cancelReply">×</button>
          </div>

          <label class="field-shell notes-field">
            <span>یادداشت جدید</span>
            <textarea
              v-model="noteBody"
              rows="3"
              placeholder="یادداشت خود را بنویسید..."
              @keydown.ctrl.enter.prevent="submitNote"
            />
          </label>

          <div class="notes-composer-actions">
            <small class="notes-hint">Ctrl + Enter برای ارسال سریع</small>
            <button
              class="action-btn tone-primary"
              type="button"
              :disabled="!noteBody.trim() || noteSubmitting"
              @click="submitNote"
            >
              {{ noteSubmitting ? 'در حال ارسال...' : 'ثبت یادداشت' }}
            </button>
          </div>
        </div>
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row">
          <div><h3>تصمیم ارجاع گیرنده ها</h3></div>
          <span class="meta-pill">{{ decisions.length }} نفر</span>
        </div>
        <DecisionAssigneesList :decisions="decisions" />
      </section>

      <section class="surface-inline detail-section">
        <div class="section-label-row">
          <div><h3>فاکتور</h3></div>
        </div>
        <button v-if="expense.invoiceUrl" class="action-btn tone-primary" type="button" @click="openProtectedFile(expense.invoiceUrl, expense.invoiceName || 'invoice')">
          <IconlyIcon name="description" decorative />
          <span>مشاهده فایل</span>
        </button>
        <div v-else class="empty-state-inline centered-empty">
          <IconlyIcon name="description" decorative />
          <p>فایل پیوست وارد نشده است.</p>
        </div>
      </section>

      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">بستن</button>
        <button v-if="canApproveSelectedExpense" class="action-btn tone-soft" type="button" @click="referOpen = true">ارجاع</button>
        <button v-if="canApproveSelectedExpense" class="action-btn tone-danger" type="button" @click="rejectOpen = true">رد</button>
        <button v-if="canApproveSelectedExpense" class="action-btn tone-primary" type="button" @click="approveSelectedExpense">تایید</button>
      </div>
    </div>
  </BaseModal>

  <BaseModal :open="rejectOpen" size="sm" @close="rejectOpen = false">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">علت رد</p><h2>توضیح رد هزینه</h2></div>
      <label class="field-shell"><span>علت رد</span><textarea v-model.trim="rejectReason" rows="4" /></label>
      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="rejectOpen = false">لغو</button>
        <button class="action-btn tone-danger" :disabled="!rejectReason" type="button" @click="submitReject">ثبت رد</button>
      </div>
    </div>
  </BaseModal>

  <BaseModal :open="referOpen" size="detail" @close="referOpen = false">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">ارجاع هزینه</p><h2>انتخاب گیرنده جدید</h2></div>
      <div class="filter-toolbar">
        <div class="chip-row">
          <button :class="['filter-chip', referTab === 'managers' && 'is-active']" type="button" @click="referTab = 'managers'">مدیران</button>
          <button :class="['filter-chip', referTab === 'employees' && 'is-active']" type="button" @click="referTab = 'employees'">کارمندان</button>
        </div>
        <label class="search-shell search-shell-wide">
          <IconlyIcon name="search" decorative />
          <input v-model="referSearch" placeholder="جستجو" />
        </label>
      </div>
      <div class="recipient-grid">
        <button
          v-for="item in (referTab === 'managers' ? filteredManagers : filteredEmployees)"
          :key="item.id"
          :class="['recipient-card', (referTab === 'managers' ? referForm.managerAssigneeIds : referForm.employeeAssigneeIds).map(Number).includes(Number(item.id)) && 'is-selected']"
          type="button"
          @click="toggle(referTab === 'managers' ? 'managerAssigneeIds' : 'employeeAssigneeIds', item.id)"
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
        <button class="action-btn tone-soft" type="button" @click="referOpen = false">بستن</button>
        <button class="action-btn tone-primary" type="button" :disabled="!referForm.managerAssigneeIds.length && !referForm.employeeAssigneeIds.length" @click="submitRefer">ثبت ارجاع</button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.detail-summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.detail-summary-grid article { display: grid; gap: 6px; padding: 14px; border-radius: 16px; background: rgba(72,103,183,.07); }
.detail-summary-grid span { color: var(--muted); font-size: 12px; font-weight: 800; }
.detail-section { display: grid; gap: 12px; }
.long-text { margin: 0; line-height: 2; white-space: pre-wrap; }
.inline-error { color: #b42318; }

.expense-notes-panel {
  gap: 14px;
  padding-top: 4px;
}

.notes-heading {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.notes-heading small {
  display: block;
  margin-top: 2px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
}

.notes-feed {
  display: grid;
  gap: 10px;
  max-height: 340px;
  overflow: auto;
  padding-inline-end: 2px;
}

.note-card {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(72, 103, 183, 0.12);
  background: rgba(255, 255, 255, 0.92);
}

.note-card.is-mine {
  border-color: rgba(52, 144, 139, 0.28);
  background: linear-gradient(180deg, rgba(52, 144, 139, 0.07), rgba(255, 255, 255, 0.96));
}

.note-card-body {
  display: grid;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.note-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.note-author-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.note-role-pill,
.note-mine-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
}

.note-role-pill {
  color: #4867b7;
  background: rgba(72, 103, 183, 0.1);
}

.note-mine-pill {
  color: #1f7a74;
  background: rgba(52, 144, 139, 0.12);
}

.note-card-head small,
.notes-hint {
  color: var(--muted);
  white-space: nowrap;
}

.note-reply-ref {
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(72, 103, 183, 0.06);
  border-inline-start: 3px solid rgba(72, 103, 183, 0.28);
}

.note-reply-ref p,
.note-body {
  margin: 4px 0 0;
  line-height: 1.9;
  white-space: pre-wrap;
}

.note-body {
  color: var(--text, #17302d);
}

.notes-empty {
  padding: 18px 12px;
}

.notes-empty small {
  color: var(--muted);
}

.notes-composer {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 18px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  background: rgba(52, 144, 139, 0.04);
}

.notes-field textarea {
  min-height: 92px;
  resize: vertical;
}

.reply-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(72, 103, 183, 0.08);
  color: #4867b7;
  font-size: 13px;
  font-weight: 700;
}

.reply-banner button {
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.notes-composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.linkish {
  justify-self: start;
  border: 0;
  background: transparent;
  color: #4867b7;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  padding: 0;
}

@media (max-width: 760px) {
  .detail-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .note-card-head { flex-direction: column; }
}

@media (max-width: 420px) {
  .detail-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .notes-composer-actions { flex-direction: column; align-items: stretch; }
}
</style>
