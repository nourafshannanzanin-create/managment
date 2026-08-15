<script setup>
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import DurationPicker from './DurationPicker.vue'
import ErrorNotice from './ErrorNotice.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import UserAvatar from './UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatDurationFa } from '../utils/duration'
import { isoToJalali, jalaliToIso } from '../utils/jalali'
import { toneForStatus } from '../utils/status'

const props = defineProps({
  open: { type: Boolean, default: false },
  task: { type: Object, default: null },
})

const emit = defineEmits(['close', 'changed'])

const {
  state,
  startTask,
  pauseTask,
  resumeTask,
  submitTaskReview,
  approveTask,
  requestTaskChanges,
  acceptTask,
  rejectTask,
  addTaskComment,
  markTaskMentionsRead,
  updateTaskingTask,
  closeTaskDetail,
} = useWorkflowHub()

const commentBody = ref('')
const deliveryNote = ref('')
const reviewComment = ref('')
const rejectReason = ref('')
const activePanel = ref('overview')
const editing = ref(false)
const replyTo = ref(null)
const mentionPickerOpen = ref(false)
const selectedMentionUsers = ref([])
const actionModal = ref('') // requestChanges | approve | accept | startRevision
const actionComment = ref('')
const actionMinutes = ref(30)
const actionError = ref('')
const editForm = reactive({
  title: '',
  description: '',
  priority: 'normal',
  category: '',
  departmentId: '',
  estimatedMinutes: 60,
  dueDate: '',
})

watch(
  () => props.open,
  (open) => {
    if (!open) return
    commentBody.value = ''
    deliveryNote.value = ''
    reviewComment.value = ''
    rejectReason.value = ''
    activePanel.value = 'overview'
    editing.value = false
    replyTo.value = null
    selectedMentionUsers.value = []
    mentionPickerOpen.value = false
    actionModal.value = ''
    actionComment.value = ''
    actionMinutes.value = 30
    actionError.value = ''
  },
)

const task = computed(() => props.task || state.tasking.selectedTask)
const mentionMembers = computed(() => {
  const me = Number(state.currentUser.id)
  const fromTasking = state.tasking.assigneeOptions || []
  const fromUsers = state.users || []
  const fromDirectories = state.directories?.users || []
  const source = [...fromTasking, ...fromUsers, ...fromDirectories]
  const seen = new Set()
  return source
    .map((u) => ({
      id: u.id,
      name: u.name || u.fullName || u.full_name || '',
      jobTitle: u.jobTitle || u.job_title || '',
      department: typeof u.department === 'string' ? u.department : (u.department?.name || ''),
      avatarUrl: u.avatarUrl || u.avatar_url || '',
    }))
    .filter((u) => {
      const id = Number(u.id)
      if (!id || id === me || seen.has(id) || !u.name) return false
      seen.add(id)
      return true
    })
    .sort((a, b) => String(a.name).localeCompare(String(b.name), 'fa'))
})
const selectedMentionIds = computed(() => selectedMentionUsers.value.map((u) => Number(u.id)))
const departmentOptions = computed(() =>
  state.tasking.departments?.length
    ? state.tasking.departments
    : state.settings?.departments || state.directories?.departments || [],
)

watch(
  () => [props.open, activePanel.value, task.value?.id, task.value?.unreadCount],
  async ([open, panel, taskId, unread]) => {
    if (!open || panel !== 'chat' || !taskId || !unread) return
    try {
      await markTaskMentionsRead(taskId)
      emit('changed')
    } catch {
      // ignore
    }
  },
)

function minutesLabel(value) {
  return formatDurationFa(value)
}

function formatDate(value) {
  if (!value) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      dateStyle: 'medium',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function formatDateTime(value) {
  if (!value) return '-'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function beginEdit() {
  if (!task.value) return
  editForm.title = task.value.title || ''
  editForm.description = task.value.description || ''
  editForm.priority = task.value.priority || 'normal'
  editForm.category = task.value.category || ''
  editForm.departmentId = String(task.value.departmentId || '')
  editForm.estimatedMinutes = Number(task.value.estimatedMinutes || 60)
  editForm.dueDate = task.value.dueAt ? isoToJalali(String(task.value.dueAt).slice(0, 10)) : ''
  editing.value = true
}

async function saveEdit() {
  if (!task.value?.id) return
  await updateTaskingTask(task.value.id, {
    title: editForm.title,
    description: editForm.description,
    priority: editForm.priority,
    category: editForm.category,
    departmentId: editForm.departmentId || null,
    estimatedMinutes: Number(editForm.estimatedMinutes || 0),
    dueAt: editForm.dueDate ? jalaliToIso(editForm.dueDate) : '',
  })
  editing.value = false
  emit('changed')
}

async function run(action, { close = false } = {}) {
  if (!task.value?.id) return
  try {
    await action()
    emit('changed')
    if (close) {
      closeTaskDetail()
      emit('close')
    }
  } catch {
    // store surfaces error
  }
}

function closeActionModal() {
  actionModal.value = ''
  actionComment.value = ''
  actionMinutes.value = 30
  actionError.value = ''
}

function openActionModal(kind) {
  actionError.value = ''
  actionComment.value = ''
  actionMinutes.value = 30
  actionModal.value = kind
}

const actionModalTitle = computed(() => {
  if (actionModal.value === 'requestChanges') return 'درخواست اصلاح'
  if (actionModal.value === 'approve') return 'تأیید تسک'
  if (actionModal.value === 'accept') return 'پذیرش ارجاع'
  if (actionModal.value === 'startRevision') return 'پذیرش اصلاح و ادامه'
  return ''
})

function onStartClick() {
  if (task.value?.status === 'changes_requested') {
    openActionModal('startRevision')
    return
  }
  void run(() => startTask(task.value.id, true))
}

async function submitActionModal() {
  if (!task.value?.id) return
  actionError.value = ''
  const minutes = Number(actionMinutes.value || 0)
  const comment = String(actionComment.value || '').trim()

  if (actionModal.value === 'requestChanges') {
    if (!comment) {
      actionError.value = 'توضیح درخواست اصلاح الزامی است.'
      return
    }
    if (minutes <= 0) {
      actionError.value = 'زمان اضافی اصلاح را مشخص کنید.'
      return
    }
    await run(() => requestTaskChanges(task.value.id, comment, minutes), { close: true })
    closeActionModal()
    return
  }

  if (actionModal.value === 'approve') {
    const needsExtra = Number(task.value.reviewIteration || 0) > 1 || Number(task.value.review_iteration || 0) > 1
    if (needsExtra && minutes <= 0) {
      actionError.value = 'زمان اضافی اصلاح را مشخص کنید تا به تسک اضافه شود.'
      return
    }
    await run(() => approveTask(task.value.id, comment, minutes > 0 ? minutes : 0), { close: true })
    closeActionModal()
    return
  }

  if (actionModal.value === 'accept') {
    if (minutes <= 0) {
      actionError.value = 'زمان را مشخص کنید تا به تسک اضافه شود.'
      return
    }
    await run(() => acceptTask(task.value.id, minutes), { close: true })
    closeActionModal()
    return
  }

  if (actionModal.value === 'startRevision') {
    if (minutes <= 0) {
      actionError.value = 'زمان اضافی اصلاح را مشخص کنید.'
      return
    }
    await run(() => startTask(task.value.id, true, minutes))
    closeActionModal()
  }
}

function addMention(user) {
  const id = Number(user.id)
  if (!id || selectedMentionIds.value.includes(id)) {
    mentionPickerOpen.value = false
    return
  }
  selectedMentionUsers.value = [...selectedMentionUsers.value, user]
  mentionPickerOpen.value = false
}

function removeMention(userId) {
  const id = Number(userId)
  selectedMentionUsers.value = selectedMentionUsers.value.filter((item) => Number(item.id) !== id)
}

function startReply(comment) {
  replyTo.value = comment
  if (comment?.author?.id && Number(comment.author.id) !== Number(state.currentUser.id)) {
    addMention(comment.author)
  }
}

async function sendComment() {
  if (!commentBody.value.trim() || !task.value?.id) return
  await addTaskComment(
    task.value.id,
    commentBody.value.trim(),
    selectedMentionIds.value,
    replyTo.value?.id || null,
  )
  commentBody.value = ''
  selectedMentionUsers.value = []
  replyTo.value = null
  mentionPickerOpen.value = false
  emit('changed')
}
</script>

<template>
  <BaseModal :open="open && Boolean(task)" size="wide" @close="emit('close')">
    <div v-if="task" class="task-detail">
      <div class="modal-header task-detail-header">
        <div class="task-detail-heading">
          <p class="eyebrow">{{ task.code }}</p>
          <h2>{{ task.title }}</h2>
          <div class="task-detail-meta">
            <span :class="['status-badge', toneForStatus(task.statusLabel)]">{{ task.statusLabel }}</span>
            <span class="priority-pill" :data-priority="task.priority">{{ task.priorityLabel }}</span>
            <small v-if="task.overdue" class="is-danger-text">عقب‌افتاده</small>
          </div>
        </div>
        <button
          v-if="task.canEdit && !editing"
          class="action-btn tone-soft task-edit-btn"
          type="button"
          @click="beginEdit"
        >
          ویرایش
        </button>
      </div>

      <ErrorNotice v-if="state.lastErrorDetails" :error="state.lastErrorDetails" />

      <div class="task-action-row">
        <button v-if="task.canAccept" class="action-btn tone-primary" type="button" @click="openActionModal('accept')">پذیرفتن ارجاع</button>
        <button v-if="task.canReject" class="action-btn tone-soft" type="button" @click="run(() => rejectTask(task.id, rejectReason || 'رد ارجاع'), { close: true })">رد ارجاع</button>
        <button v-if="task.canStart && task.status !== 'in_progress'" class="action-btn tone-primary" type="button" @click="onStartClick">
          {{ task.status === 'changes_requested' ? 'پذیرش اصلاح و شروع' : 'شروع' }}
        </button>
        <button v-if="task.canPause" class="action-btn tone-soft" type="button" @click="run(() => pauseTask(task.id))">توقف</button>
        <button v-if="task.status === 'paused'" class="action-btn tone-primary" type="button" @click="run(() => resumeTask(task.id))">ادامه</button>
        <button v-if="task.canComplete" class="action-btn tone-primary" type="button" @click="run(() => submitTaskReview(task.id, deliveryNote), { close: true })">پایان و ارسال برای بررسی</button>
        <button v-if="task.canReview" class="action-btn tone-primary" type="button" @click="openActionModal('approve')">تأیید و بستن</button>
        <button v-if="task.canReview" class="action-btn tone-soft" type="button" @click="openActionModal('requestChanges')">درخواست اصلاح</button>
      </div>

      <div class="chip-row tab-strip">
        <button type="button" :class="['chip-btn', activePanel === 'overview' && 'is-active']" @click="activePanel = 'overview'">خلاصه</button>
        <button type="button" :class="['chip-btn', activePanel === 'schedule' && 'is-active']" @click="activePanel = 'schedule'">زمان‌بندی</button>
        <button type="button" :class="['chip-btn', activePanel === 'activity' && 'is-active']" @click="activePanel = 'activity'">فعالیت</button>
        <button type="button" :class="['chip-btn', activePanel === 'chat' && 'is-active']" @click="activePanel = 'chat'">
          گفتگو
          <span v-if="task.unreadCount" class="mini-count">{{ task.unreadCount }}</span>
        </button>
      </div>

      <section v-if="activePanel === 'overview'" class="task-panel">
        <template v-if="editing">
          <div class="edit-grid">
            <label class="field-shell full">
              <span>عنوان</span>
              <input v-model="editForm.title" type="text" />
            </label>
            <label class="field-shell full">
              <span>توضیحات</span>
              <textarea v-model="editForm.description" rows="3"></textarea>
            </label>
            <label class="field-shell">
              <span>اولویت</span>
              <select v-model="editForm.priority">
                <option value="critical">بحرانی</option>
                <option value="high">بالا</option>
                <option value="medium">متوسط</option>
                <option value="normal">عادی</option>
                <option value="low">پایین</option>
              </select>
            </label>
            <label class="field-shell">
              <span>بخش</span>
              <select v-model="editForm.departmentId">
                <option value="">بدون بخش</option>
                <option v-for="dept in departmentOptions" :key="dept.id || dept.code" :value="String(dept.id || '')">{{ dept.name }}</option>
              </select>
            </label>
            <div class="field-shell">
              <span>تخمین</span>
              <DurationPicker v-model="editForm.estimatedMinutes" />
            </div>
            <div class="field-shell">
              <span>ددلاین (روز)</span>
              <ShamsiDatePicker v-model="editForm.dueDate" model-type="jalali" picker-only placeholder="انتخاب تاریخ" />
            </div>
            <label class="field-shell">
              <span>دسته‌بندی</span>
              <input v-model="editForm.category" type="text" />
            </label>
          </div>
          <div class="task-action-row">
            <button class="action-btn tone-soft" type="button" @click="editing = false">انصراف</button>
            <button class="action-btn tone-primary" type="button" :disabled="state.tasking.submitting" @click="saveEdit">ذخیره تغییرات</button>
          </div>
        </template>
        <template v-else>
          <div class="info-grid">
            <article>
              <small>مسئول</small>
              <div class="person-inline">
                <UserAvatar :person="task.assignee" :name="task.assignee?.name" size="sm" />
                <strong>{{ task.assignee?.name || '-' }}</strong>
              </div>
            </article>
            <article>
              <small>سازنده</small>
              <div class="person-inline">
                <UserAvatar :person="task.creator" :name="task.creator?.name" size="sm" />
                <strong>{{ task.creator?.name || '-' }}</strong>
              </div>
            </article>
            <article>
              <small>بخش</small>
              <strong>{{ task.department || '-' }}</strong>
            </article>
            <article>
              <small>تخمین</small>
              <strong>{{ minutesLabel(task.estimatedMinutes) }}</strong>
            </article>
            <article>
              <small>واقعی</small>
              <strong>{{ minutesLabel(task.actualMinutes) }}</strong>
            </article>
            <article>
              <small>باقی‌مانده</small>
              <strong>{{ minutesLabel(task.remainingMinutes) }}</strong>
            </article>
            <article>
              <small>ددلاین</small>
              <strong>{{ formatDate(task.dueAt) }}</strong>
            </article>
          </div>
          <div class="field-shell">
            <span>توضیحات</span>
            <p>{{ task.description || 'بدون توضیح' }}</p>
          </div>
        </template>
        <label v-if="task.canComplete" class="field-shell">
          <span>یادداشت تحویل</span>
          <textarea v-model="deliveryNote" rows="3" placeholder="خلاصه نتیجه کار"></textarea>
        </label>
        <label v-if="task.canReject" class="field-shell">
          <span>دلیل رد ارجاع</span>
          <textarea v-model="rejectReason" rows="2"></textarea>
        </label>
        <div v-if="task.attachments?.length" class="attachment-list">
          <a v-for="file in task.attachments" :key="file.id" :href="file.fileUrl" target="_blank" rel="noopener">{{ file.originalName }}</a>
        </div>
      </section>

      <section v-else-if="activePanel === 'schedule'" class="task-panel">
        <article v-for="item in task.allocations || []" :key="item.id" class="schedule-row">
          <strong>{{ item.workDate }}</strong>
          <span>{{ minutesLabel(item.plannedMinutes) }}</span>
          <small>{{ item.segmentStatus }}</small>
        </article>
        <p v-if="!(task.allocations || []).length" class="empty-copy">هنوز تخصیص روزانه‌ای ثبت نشده است.</p>
      </section>

      <section v-else-if="activePanel === 'activity'" class="task-panel timeline-panel">
        <article v-for="item in task.activities || []" :key="item.id" class="timeline-item">
          <div class="person-inline">
            <UserAvatar :person="item.actor" :name="item.actor?.name || 'سیستم'" size="sm" />
            <strong>{{ item.actor?.name || 'سیستم' }}</strong>
          </div>
          <p>{{ item.detail || item.action }}</p>
          <small>{{ formatDateTime(item.createdAt) }}</small>
        </article>
      </section>

      <section v-else class="task-panel chat-panel">
        <div class="chat-list">
          <article v-for="item in task.comments || []" :key="item.id" class="chat-item">
            <UserAvatar :person="item.author" :name="item.author?.name" size="sm" />
            <div class="chat-item-body">
              <strong>{{ item.author?.name }}</strong>
              <div v-if="item.parent" class="chat-reply-ref">
                <small>پاسخ به {{ item.parent.author?.name || 'پیام' }}</small>
                <p>{{ item.parent.body }}</p>
              </div>
              <p>{{ item.body }}</p>
              <div v-if="(item.mentionUsers || []).length" class="chat-mention-targets">
                <span v-for="user in item.mentionUsers" :key="user.id" class="mention-pill is-static">@{{ user.name }}</span>
              </div>
              <small>{{ formatDateTime(item.createdAt) }}</small>
              <button class="linkish" type="button" @click="startReply(item)">پاسخ</button>
            </div>
          </article>
        </div>
          <div class="chat-composer">
          <div v-if="replyTo" class="reply-banner">
            پاسخ به {{ replyTo.author?.name }}
            <button type="button" @click="replyTo = null">×</button>
          </div>

          <div class="chat-input-shell">
            <div class="chat-input-top">
              <div class="mention-trigger-wrap">
                <button
                  class="mention-at-btn"
                  type="button"
                  title="منشن اعضا"
                  aria-label="منشن اعضا"
                  :class="{ 'is-open': mentionPickerOpen }"
                  @click.stop="mentionPickerOpen = !mentionPickerOpen"
                >
                  @
                </button>
                <div v-if="mentionPickerOpen" class="mention-dropdown" @click.stop>
                  <p class="mention-dropdown-title">اعضای مجموعه</p>
                  <button
                    v-for="user in mentionMembers"
                    :key="user.id"
                    type="button"
                    class="mention-option"
                    :class="{ 'is-picked': selectedMentionIds.includes(Number(user.id)) }"
                    @click="addMention(user)"
                  >
                    <UserAvatar :person="user" :name="user.name" size="sm" />
                    <span>
                      <strong>{{ user.name }}</strong>
                      <small>{{ user.jobTitle || user.department || 'عضو مجموعه' }}</small>
                    </span>
                  </button>
                  <p v-if="!mentionMembers.length" class="mention-empty">عضوی برای منشن نیست.</p>
                </div>
              </div>

              <div class="mention-selected">
                <span
                  v-for="user in selectedMentionUsers"
                  :key="user.id"
                  class="mention-pill"
                >
                  @{{ user.name }}
                  <button type="button" aria-label="حذف منشن" @click="removeMention(user.id)">×</button>
                </span>
                <span v-if="!selectedMentionUsers.length" class="mention-placeholder">برای منشن روی @ بزنید</span>
              </div>
            </div>

            <textarea
              v-model="commentBody"
              rows="3"
              class="chat-textarea"
              placeholder="پیام داخل تسک..."
              @keydown.escape="mentionPickerOpen = false"
            ></textarea>
          </div>

          <button class="action-btn tone-primary" type="button" @click="sendComment">ارسال</button>
        </div>
      </section>
    </div>
  </BaseModal>

  <BaseModal :open="Boolean(actionModal)" size="sm" @close="closeActionModal">
    <div class="action-modal-shell">
      <div class="modal-headline">
        <p class="page-eyebrow">اقدام تسک</p>
        <h2>{{ actionModalTitle }}</h2>
      </div>

      <label v-if="actionModal === 'requestChanges' || actionModal === 'approve'" class="field-shell">
        <span>{{ actionModal === 'requestChanges' ? 'توضیح اصلاح' : 'نظر تأیید (اختیاری)' }}</span>
        <textarea
          v-model="actionComment"
          rows="4"
          :placeholder="actionModal === 'requestChanges' ? 'چه مواردی باید اصلاح شود؟' : 'توضیح اختیاری برای تأیید'"
        ></textarea>
      </label>

      <div v-if="actionModal !== 'approve' || Number(task?.reviewIteration || task?.review_iteration || 0) > 1" class="field-shell">
        <span>
          {{
            actionModal === 'requestChanges' || actionModal === 'startRevision'
              ? 'زمان اضافی برای اصلاح'
              : 'زمان اضافی برای افزودن به تسک'
          }}
        </span>
        <DurationPicker v-model="actionMinutes" placeholder="انتخاب زمان" />
        <small class="action-modal-hint">این زمان به تخمین و برنامه‌ی تسک اضافه می‌شود.</small>
      </div>

      <div v-else class="field-shell">
        <span>زمان اضافی (اختیاری)</span>
        <DurationPicker v-model="actionMinutes" placeholder="در صورت نیاز انتخاب کنید" />
        <small class="action-modal-hint">اگر لازم است زمان بیشتری به تسک اضافه شود، اینجا مشخص کنید.</small>
      </div>

      <p v-if="actionError" class="inline-error">{{ actionError }}</p>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="closeActionModal">انصراف</button>
        <button
          class="action-btn tone-primary"
          type="button"
          :disabled="state.tasking.submitting"
          @click="submitActionModal"
        >
          {{ state.tasking.submitting ? 'در حال ثبت...' : 'ثبت و ارسال' }}
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.task-detail { display: grid; gap: 14px; }
.task-detail-header,
.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  /* جا برای دکمه بستن مودال (absolute left) */
  padding-left: 52px;
  min-width: 0;
}
.task-detail-heading {
  min-width: 0;
  flex: 1;
}
.task-edit-btn {
  flex: 0 0 auto;
  margin-top: 2px;
  white-space: nowrap;
}
.task-detail-meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px; }
.priority-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  background: #eef7f6;
  color: #1f5c59;
}
.priority-pill[data-priority='critical'] { background: #fde8e8; color: #9b1c1c; }
.priority-pill[data-priority='high'] { background: #fff4e5; color: #9a3412; }
.task-action-row, .tab-strip, .chip-row { display: flex; flex-wrap: wrap; gap: 8px; }
.chip-btn {
  border: 1px solid rgba(52, 144, 139, 0.18);
  background: #f7fbfa;
  border-radius: 999px;
  padding: 8px 12px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.chip-btn.is-active { background: #dcefec; color: #1f5c59; }
.mini-count {
  display: inline-flex;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  align-items: center;
  justify-content: center;
  background: #c45a4a;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
}
.task-panel { display: grid; gap: 12px; }
.info-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.info-grid article {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  border-radius: 14px;
  padding: 12px;
  background: #fff;
  min-width: 0;
}
.info-grid small {
  display: block;
  color: var(--muted, #5f7a76);
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.3;
}
.info-grid strong {
  display: block;
  font-size: 0.92rem;
  line-height: 1.45;
  word-break: break-word;
}
.person-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.person-inline strong {
  min-width: 0;
}
.action-modal-shell {
  display: grid;
  gap: 14px;
  padding: 4px;
}
.action-modal-hint {
  color: var(--muted, #5f7a76);
  font-size: 12px;
}
.inline-error {
  margin: 0;
  color: #b42318;
  font-weight: 700;
}
.schedule-row, .timeline-item, .chat-item {
  border: 1px solid rgba(52, 144, 139, 0.12);
  border-radius: 14px;
  padding: 12px;
  background: #fff;
}
.timeline-item small, .chat-item small { color: var(--muted); }
.schedule-row, .chat-item, .chat-composer {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}
.chat-item { align-items: flex-start; justify-content: flex-start; }
.chat-item-body { display: grid; gap: 4px; min-width: 0; }
.chat-list { display: grid; gap: 10px; max-height: 320px; overflow: auto; }
.chat-composer {
  align-items: stretch;
  flex-direction: column;
  gap: 10px;
  overflow: visible;
  position: relative;
  z-index: 2;
}
.chat-input-shell {
  display: grid;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  background: #ffffff !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.8);
  overflow: visible;
  position: relative;
}
.chat-input-top {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
  overflow: visible;
  position: relative;
  z-index: 3;
}
.mention-selected {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  min-width: 0;
  flex: 1;
  min-height: 36px;
}
.mention-placeholder {
  color: #8aa19c;
  font-size: 12px;
}
.mention-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef7f6;
  color: #1f5c59;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid rgba(52, 144, 139, 0.16);
}
.mention-pill button {
  border: 0;
  background: transparent;
  color: #1f5c59;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0;
}
.chat-reply-ref {
  display: grid;
  gap: 4px;
  margin: 6px 0 8px;
  padding: 8px 10px;
  border-radius: 10px;
  border-right: 3px solid #34908b;
  background: #f3faf9;
}
.chat-reply-ref small {
  color: #1f5c59;
  font-weight: 800;
}
.chat-reply-ref p {
  margin: 0;
  color: #5f7a76;
  font-size: 12px;
  line-height: 1.6;
}
.chat-mention-targets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 6px 0;
}
.mention-pill.is-static {
  padding-inline-end: 10px;
}
.mention-trigger-wrap {
  position: relative;
  flex: 0 0 auto;
  z-index: 5;
}
.mention-at-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(52, 144, 139, 0.22) !important;
  background: #ffffff !important;
  color: #1f5c59 !important;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
  line-height: 1;
  box-shadow: 0 1px 0 rgba(31, 92, 89, 0.12), 0 4px 10px rgba(31, 92, 89, 0.08);
}
.mention-at-btn.is-open,
.mention-at-btn:hover {
  background: #dcefec !important;
}
.mention-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  bottom: auto;
  right: 0;
  z-index: 80;
  width: min(320px, 82vw);
  max-height: min(280px, 42vh);
  overflow: auto;
  overscroll-behavior: contain;
  display: grid;
  gap: 4px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  background: #ffffff !important;
  box-shadow: 0 16px 36px rgba(31, 92, 89, 0.18);
}
.mention-dropdown-title {
  margin: 0;
  padding: 6px 8px 8px;
  color: #5f7a76;
  font-size: 11px;
  font-weight: 800;
}
.mention-option {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  text-align: right;
  border: 0;
  background: transparent;
  border-radius: 10px;
  padding: 8px;
  cursor: pointer;
}
.mention-option:hover,
.mention-option.is-picked {
  background: #eef7f6;
}
.mention-option strong,
.mention-option small {
  display: block;
}
.mention-option small {
  color: var(--muted, #5f7a76);
  font-size: 11px;
}
.mention-empty {
  margin: 0;
  padding: 10px;
  color: var(--muted, #5f7a76);
  font-size: 12px;
}
.task-detail .chat-textarea,
.chat-textarea {
  width: 100% !important;
  min-height: 72px !important;
  resize: vertical;
  border: 0 !important;
  outline: none !important;
  background: #ffffff !important;
  background-color: #ffffff !important;
  color: #1f2a28 !important;
  padding: 4px 2px !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
.reply-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(52, 144, 139, 0.1);
  font-size: 12px;
}
.linkish {
  border: 0;
  background: transparent;
  color: #1f7a72;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  width: fit-content;
}
.edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.edit-grid .full { grid-column: 1 / -1; }
.attachment-list { display: grid; gap: 6px; }
.is-danger-text { color: #9b1c1c; font-weight: 700; }
.empty-copy { color: var(--muted); }
@media (max-width: 760px) {
  .info-grid, .edit-grid { grid-template-columns: 1fr 1fr; }
  .chat-composer { flex-direction: column; }
}
</style>
