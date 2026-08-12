<script setup>
import { computed, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import IconlyIcon from './base/IconlyIcon.vue'
import UserAvatar from './UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatDurationFa } from '../utils/duration'
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
  closeTaskDetail,
} = useWorkflowHub()

const commentBody = ref('')
const deliveryNote = ref('')
const reviewComment = ref('')
const rejectReason = ref('')
const activePanel = ref('overview')

watch(
  () => props.open,
  (open) => {
    if (!open) return
    commentBody.value = ''
    deliveryNote.value = ''
    reviewComment.value = ''
    rejectReason.value = ''
    activePanel.value = 'overview'
  },
)

const task = computed(() => props.task || state.tasking.selectedTask)

function minutesLabel(value) {
  return formatDurationFa(value)
}

function formatDate(value) {
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

async function sendComment() {
  if (!commentBody.value.trim() || !task.value?.id) return
  await addTaskComment(task.value.id, commentBody.value.trim())
  commentBody.value = ''
  emit('changed')
}
</script>

<template>
  <BaseModal :open="open && Boolean(task)" size="wide" @close="emit('close')">
    <div v-if="task" class="task-detail">
      <div class="modal-header">
        <div>
          <p class="eyebrow">{{ task.code }}</p>
          <h2>{{ task.title }}</h2>
          <div class="task-detail-meta">
            <span :class="['status-badge', toneForStatus(task.statusLabel)]">{{ task.statusLabel }}</span>
            <span class="priority-pill" :data-priority="task.priority">{{ task.priorityLabel }}</span>
            <small v-if="task.overdue" class="is-danger-text">عقب‌افتاده</small>
          </div>
        </div>
      </div>

      <ErrorNotice v-if="state.lastErrorDetails" :error="state.lastErrorDetails" />

      <div class="task-action-row">
        <button v-if="task.canAccept" class="action-btn tone-primary" type="button" @click="run(() => acceptTask(task.id), { close: true })">پذیرفتن ارجاع</button>
        <button v-if="task.canReject" class="action-btn tone-soft" type="button" @click="run(() => rejectTask(task.id, rejectReason || 'رد ارجاع'), { close: true })">رد ارجاع</button>
        <button v-if="task.canStart && task.status !== 'in_progress'" class="action-btn tone-primary" type="button" @click="run(() => startTask(task.id, true))">شروع</button>
        <button v-if="task.canPause" class="action-btn tone-soft" type="button" @click="run(() => pauseTask(task.id))">توقف</button>
        <button v-if="task.status === 'paused'" class="action-btn tone-primary" type="button" @click="run(() => resumeTask(task.id))">ادامه</button>
        <button v-if="task.canComplete" class="action-btn tone-primary" type="button" @click="run(() => submitTaskReview(task.id, deliveryNote), { close: true })">پایان و ارسال برای بررسی</button>
        <button v-if="task.canReview" class="action-btn tone-primary" type="button" @click="run(() => approveTask(task.id, reviewComment), { close: true })">تأیید و بستن</button>
        <button v-if="task.canReview" class="action-btn tone-soft" type="button" @click="run(() => requestTaskChanges(task.id, reviewComment || 'نیازمند اصلاح'), { close: true })">درخواست اصلاح</button>
      </div>

      <div class="chip-row tab-strip">
        <button type="button" :class="['chip-btn', activePanel === 'overview' && 'is-active']" @click="activePanel = 'overview'">خلاصه</button>
        <button type="button" :class="['chip-btn', activePanel === 'schedule' && 'is-active']" @click="activePanel = 'schedule'">زمان‌بندی</button>
        <button type="button" :class="['chip-btn', activePanel === 'activity' && 'is-active']" @click="activePanel = 'activity'">فعالیت</button>
        <button type="button" :class="['chip-btn', activePanel === 'chat' && 'is-active']" @click="activePanel = 'chat'">گفتگو</button>
      </div>

      <section v-if="activePanel === 'overview'" class="task-panel">
        <div class="info-grid">
          <article><small>مسئول</small><strong>{{ task.assignee?.name || '-' }}</strong></article>
          <article><small>سازنده</small><strong>{{ task.creator?.name || '-' }}</strong></article>
          <article><small>تخمین</small><strong>{{ minutesLabel(task.estimatedMinutes) }}</strong></article>
          <article><small>واقعی</small><strong>{{ minutesLabel(task.actualMinutes) }}</strong></article>
          <article><small>باقی‌مانده</small><strong>{{ minutesLabel(task.remainingMinutes) }}</strong></article>
          <article><small>ددلاین</small><strong>{{ formatDate(task.dueAt) }}</strong></article>
        </div>
        <div class="field-shell">
          <span>توضیحات</span>
          <p>{{ task.description || 'بدون توضیح' }}</p>
        </div>
        <label v-if="task.canComplete" class="field-shell">
          <span>یادداشت تحویل</span>
          <textarea v-model="deliveryNote" rows="3" placeholder="خلاصه نتیجه کار"></textarea>
        </label>
        <label v-if="task.canReview" class="field-shell">
          <span>نظر بررسی</span>
          <textarea v-model="reviewComment" rows="3" placeholder="توضیح تأیید یا درخواست اصلاح"></textarea>
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
          <strong>{{ item.actor?.name || item.actor?.name || 'سیستم' }}</strong>
          <p>{{ item.detail || item.action }}</p>
          <small>{{ formatDate(item.createdAt) }}</small>
        </article>
      </section>

      <section v-else class="task-panel chat-panel">
        <div class="chat-list">
          <article v-for="item in task.comments || []" :key="item.id" class="chat-item">
            <UserAvatar :name="item.author?.name" :avatar-url="item.author?.avatarUrl" size="sm" />
            <div>
              <strong>{{ item.author?.name }}</strong>
              <p>{{ item.body }}</p>
              <small>{{ formatDate(item.createdAt) }}</small>
            </div>
          </article>
        </div>
        <div class="chat-composer">
          <textarea v-model="commentBody" rows="3" placeholder="پیام داخل تسک..."></textarea>
          <button class="action-btn tone-primary" type="button" @click="sendComment">ارسال</button>
        </div>
      </section>
    </div>
  </BaseModal>
</template>

<style scoped>
.task-detail { display: grid; gap: 14px; }
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
}
.chip-btn.is-active { background: #dcefec; color: #1f5c59; }
.task-panel { display: grid; gap: 12px; }
.info-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.info-grid article, .schedule-row, .timeline-item, .chat-item {
  border: 1px solid rgba(52, 144, 139, 0.12);
  border-radius: 14px;
  padding: 12px;
  background: #fff;
}
.info-grid small, .timeline-item small, .chat-item small { color: var(--muted); }
.schedule-row, .chat-item, .chat-composer {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}
.chat-item { align-items: flex-start; justify-content: flex-start; }
.chat-list { display: grid; gap: 10px; max-height: 320px; overflow: auto; }
.chat-composer { align-items: stretch; }
.chat-composer textarea { flex: 1; }
.attachment-list { display: grid; gap: 6px; }
.is-danger-text { color: #9b1c1c; font-weight: 700; }
.empty-copy { color: var(--muted); }
@media (max-width: 760px) {
  .info-grid { grid-template-columns: 1fr 1fr; }
  .chat-composer { flex-direction: column; }
}
</style>
