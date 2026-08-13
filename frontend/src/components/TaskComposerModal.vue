<script setup>
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import DurationPicker from './DurationPicker.vue'
import ErrorNotice from './ErrorNotice.vue'
import IconlyIcon from './base/IconlyIcon.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatDurationFa } from '../utils/duration'
import { jalaliToIso } from '../utils/jalali'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'created'])

const {
  state,
  createTaskingTask,
  previewTaskSchedule,
  closeTaskComposer,
} = useWorkflowHub()

const form = reactive({
  title: '',
  description: '',
  assigneeId: '',
  priority: 'normal',
  estimatedMinutes: 60,
  category: '',
  departmentId: '',
  dueDate: '',
  observerIds: [],
  reviewRequired: true,
})

const files = ref([])
const preview = ref(null)
const busyPreview = ref(false)
const localError = ref('')

const assigneeOptions = computed(() => state.tasking.assigneeOptions || [])
const departmentOptions = computed(() =>
  state.tasking.departments?.length
    ? state.tasking.departments
    : state.settings?.departments || state.directories?.departments || [],
)
const estimatedMinutes = computed(() => Number(form.estimatedMinutes || 0))

function buildDueAt() {
  if (!form.dueDate) return ''
  const isoDate = jalaliToIso(form.dueDate)
  if (!isoDate) return ''
  // Day-only deadline → backend stores end of that day
  return isoDate
}

watch(
  () => props.open,
  (open) => {
    if (!open) return
    form.title = ''
    form.description = ''
    form.assigneeId = String(state.currentUser.id || '')
    form.priority = 'normal'
    form.estimatedMinutes = 60
    form.category = ''
    form.departmentId = String(state.currentUser.departmentId || state.currentUser.department_id || '')
    form.dueDate = ''
    form.observerIds = []
    form.reviewRequired = true
    files.value = []
    preview.value = null
    localError.value = ''
  },
)

watch(
  () => [props.open, form.assigneeId, estimatedMinutes.value],
  async () => {
    if (!props.open || estimatedMinutes.value <= 0 || !form.assigneeId) return
    busyPreview.value = true
    try {
      preview.value = await previewTaskSchedule({
        assigneeId: Number(form.assigneeId),
        estimatedMinutes: estimatedMinutes.value,
      })
    } catch {
      preview.value = null
    } finally {
      busyPreview.value = false
    }
  },
)

function onFiles(event) {
  files.value = Array.from(event.target.files || [])
}

async function submit() {
  localError.value = ''
  if (!String(form.title || '').trim()) {
    localError.value = 'عنوان تسک الزامی است.'
    return
  }
  if (estimatedMinutes.value <= 0) {
    localError.value = 'زمان تخمینی باید بیشتر از صفر باشد.'
    return
  }
  try {
    const task = await createTaskingTask(
      {
        title: form.title,
        description: form.description,
        assigneeId: Number(form.assigneeId),
        priority: form.priority,
        estimatedMinutes: estimatedMinutes.value,
        category: form.category,
        departmentId: form.departmentId || undefined,
        dueAt: buildDueAt() || undefined,
        observerIds: form.observerIds,
        reviewRequired: form.reviewRequired,
      },
      files.value,
    )
    emit('created', task)
    closeTaskComposer()
    emit('close')
  } catch {
    // ErrorNotice via store
  }
}
</script>

<template>
  <BaseModal :open="open" size="wide" @close="emit('close')">
    <div class="modal-header">
      <div>
        <p class="eyebrow">تسکینگ</p>
        <h2>تسک جدید</h2>
        <p>عنوان، مسئول، بخش، اولویت و زمان تخمینی را مشخص کنید. برنامه پیشنهادی قبل از ثبت نمایش داده می‌شود.</p>
      </div>
    </div>

    <ErrorNotice v-if="state.lastErrorDetails" :error="state.lastErrorDetails" />
    <p v-if="localError" class="form-inline-error">{{ localError }}</p>

    <div class="modal-grid two-col task-composer-grid">
      <label class="field-shell full-span">
        <span>عنوان تسک *</span>
        <input v-model="form.title" type="text" placeholder="مثلاً بررسی پیش‌فاکتور تجهیزات" />
      </label>

      <label class="field-shell full-span">
        <span>توضیحات</span>
        <textarea v-model="form.description" rows="4" placeholder="جزئیات کار، خروجی مورد انتظار و نکات مهم"></textarea>
      </label>

      <label class="field-shell">
        <span>مسئول انجام *</span>
        <select v-model="form.assigneeId">
          <option v-for="user in assigneeOptions" :key="user.id" :value="String(user.id)">
            {{ user.name }} — {{ user.jobTitle || user.department || 'بدون سمت' }} ({{ user.capacityToday || 0 }}٪)
          </option>
        </select>
      </label>

      <label class="field-shell">
        <span>بخش</span>
        <select v-model="form.departmentId">
          <option value="">هم‌راستا با مسئول / تنظیمات</option>
          <option v-for="dept in departmentOptions" :key="dept.id || dept.code" :value="String(dept.id || '')">
            {{ dept.name }}
          </option>
        </select>
      </label>

      <label class="field-shell">
        <span>اولویت *</span>
        <select v-model="form.priority">
          <option value="critical">بحرانی</option>
          <option value="high">بالا</option>
          <option value="medium">متوسط</option>
          <option value="normal">عادی</option>
          <option value="low">پایین</option>
        </select>
      </label>

      <div class="field-shell">
        <span>زمان تخمینی *</span>
        <DurationPicker v-model="form.estimatedMinutes" />
      </div>

      <div class="field-shell">
        <span>ددلاین (فقط روز)</span>
        <ShamsiDatePicker
          v-model="form.dueDate"
          model-type="jalali"
          picker-only
          placeholder="انتخاب تاریخ"
        />
        <small class="field-hint">مهلت تا پایان همان روز شمسی لحاظ می‌شود.</small>
      </div>

      <label class="field-shell">
        <span>دسته‌بندی</span>
        <input v-model="form.category" type="text" placeholder="اختیاری" />
      </label>

      <label class="field-shell">
        <span>نیازمند بررسی نهایی</span>
        <select v-model="form.reviewRequired">
          <option :value="true">بله</option>
          <option :value="false">خیر</option>
        </select>
      </label>

      <label class="field-shell full-span">
        <span>پیوست‌ها</span>
        <input type="file" multiple @change="onFiles" />
      </label>
    </div>

    <article v-if="preview || busyPreview" class="schedule-preview-card">
      <strong>پیش‌نمایش زمان‌بندی</strong>
      <p v-if="busyPreview">در حال محاسبه ظرفیت...</p>
      <template v-else-if="preview">
        <p>
          زمان تخمینی: {{ formatDurationFa(preview.estimatedMinutes) }}
          <template v-if="preview.spillover"> · تقسیم بین چند روز</template>
        </p>
        <ul>
          <li v-for="segment in preview.segments" :key="segment.date">
            {{ segment.date }} — {{ formatDurationFa(segment.plannedMinutes) }}
          </li>
        </ul>
      </template>
    </article>

    <div class="modal-actions">
      <button class="action-btn tone-soft" type="button" @click="emit('close')">انصراف</button>
      <button class="action-btn tone-primary" type="button" :disabled="state.tasking.submitting" @click="submit">
        <IconlyIcon name="save" decorative />
        <span>{{ state.tasking.submitting ? 'در حال ثبت...' : 'ثبت تسک' }}</span>
      </button>
    </div>
  </BaseModal>
</template>

<style scoped>
.task-composer-grid .full-span { grid-column: 1 / -1; }
.task-composer-grid,
.task-composer-grid > * {
  min-width: 0;
}
.field-hint {
  display: block;
  margin-top: 6px;
  color: var(--muted, #5f7a76);
  font-size: 0.72rem;
}
.form-inline-error {
  color: #b91c1c;
  margin: 0 0 10px;
  font-weight: 700;
}
.schedule-preview-card {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(52, 144, 139, 0.08);
  border: 1px solid rgba(52, 144, 139, 0.16);
  display: grid;
  gap: 8px;
}
.schedule-preview-card ul {
  margin: 0;
  padding-inline-start: 18px;
  display: grid;
  gap: 4px;
}
</style>
