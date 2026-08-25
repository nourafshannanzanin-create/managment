<script setup>
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import DurationPicker from './DurationPicker.vue'
import ErrorNotice from './ErrorNotice.vue'
import IconlyIcon from './base/IconlyIcon.vue'
import UserAvatar from './UserAvatar.vue'
import { formatDurationFa } from '../utils/duration'
import { useWorkflowHub } from '../stores/workflowHub'

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
  observerIds: [],
  reviewRequired: true,
})

const files = ref([])
const preview = ref(null)
const busyPreview = ref(false)
const localError = ref('')
const observerPickerOpen = ref(false)
const selectedObservers = ref([])

const assigneeOptions = computed(() => {
  const me = Number(state.currentUser.id)
  const source = [
    ...(state.tasking.assigneeOptions || []),
    ...(state.users || []),
    ...(state.directories?.users || []),
  ]
  const seen = new Set()
  return source
    .filter((user) => {
      const id = Number(user?.id)
      if (!id || seen.has(id)) return false
      seen.add(id)
      return Boolean(user.name || user.fullName || user.full_name)
    })
    .map((user) => ({
      ...user,
      name: user.name || user.fullName || user.full_name || 'کاربر',
      isSelf: Number(user.id) === me,
    }))
    .sort((a, b) => String(a.name).localeCompare(String(b.name), 'fa'))
})

function assigneeLabel(user) {
  const role = user.jobTitle || user.department || 'بدون سمت'
  const selfSuffix = user.isSelf ? ' (خودم)' : ''
  const capacity = user.capacityToday != null ? ` (${user.capacityToday}٪)` : ''
  return `${user.name}${selfSuffix} — ${role}${capacity}`
}
const observerMembers = computed(() => {
  const me = Number(state.currentUser.id)
  const assignee = Number(form.assigneeId || 0)
  const picked = new Set(selectedObservers.value.map((u) => Number(u.id)))
  const source = [
    ...(state.tasking.assigneeOptions || []),
    ...(state.users || []),
    ...(state.directories?.users || []),
  ]
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
      if (!id || id === me || id === assignee || seen.has(id) || picked.has(id) || !u.name) return false
      seen.add(id)
      return true
    })
    .sort((a, b) => String(a.name).localeCompare(String(b.name), 'fa'))
})
const departmentOptions = computed(() =>
  state.tasking.departments?.length
    ? state.tasking.departments
    : state.settings?.departments || state.directories?.departments || [],
)
const estimatedMinutes = computed(() => Number(form.estimatedMinutes || 0))

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
    form.observerIds = []
    selectedObservers.value = []
    observerPickerOpen.value = false
    form.reviewRequired = true
    files.value = []
    preview.value = null
    localError.value = ''
  },
)

watch(
  () => form.assigneeId,
  (assigneeId) => {
    const id = Number(assigneeId || 0)
    if (!id) return
    const next = selectedObservers.value.filter((item) => Number(item.id) !== id)
    if (next.length !== selectedObservers.value.length) {
      selectedObservers.value = next
      form.observerIds = next.map((item) => Number(item.id))
    }
  },
)

watch(
  [() => props.open, () => form.assigneeId, estimatedMinutes],
  async ([open, assigneeId, minutes]) => {
    if (!open || Number(minutes) <= 0 || !assigneeId) {
      preview.value = null
      return
    }
    busyPreview.value = true
    try {
      preview.value = await previewTaskSchedule({
        assigneeId: Number(assigneeId),
        estimatedMinutes: Number(minutes),
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

function addObserver(user) {
  const id = Number(user.id)
  if (!id || selectedObservers.value.some((item) => Number(item.id) === id)) {
    observerPickerOpen.value = false
    return
  }
  selectedObservers.value = [...selectedObservers.value, user]
  form.observerIds = selectedObservers.value.map((item) => Number(item.id))
  observerPickerOpen.value = false
}

function removeObserver(userId) {
  const id = Number(userId)
  selectedObservers.value = selectedObservers.value.filter((item) => Number(item.id) !== id)
  form.observerIds = selectedObservers.value.map((item) => Number(item.id))
}

async function submit() {
  localError.value = ''
  if (!String(form.title || '').trim()) {
    localError.value = 'عنوان تسک الزامی است.'
    return
  }
  if (!Number(form.assigneeId)) {
    localError.value = 'مسئول انجام را انتخاب کنید.'
    return
  }
  if (estimatedMinutes.value <= 0) {
    localError.value = 'زمان تخمینی باید بیشتر از صفر باشد.'
    return
  }
  if (state.tasking.submitting) return
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
        observerIds: form.observerIds,
        reviewRequired: form.reviewRequired,
      },
      files.value,
    )
    emit('created', task)
    closeTaskComposer()
    emit('close')
  } catch (error) {
    localError.value = error?.message || state.lastError || 'ثبت تسک ناموفق بود.'
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
            {{ assigneeLabel(user) }}
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

      <div class="field-shell full-span observer-field">
        <span>ناظران (منشن)</span>
        <small class="field-hint">افرادی که فقط باید تسک را ببینند و در بخش منشن برایشان نمایش داده شود.</small>
        <div class="observer-picker">
          <div class="mention-trigger-wrap">
            <button
              class="mention-at-btn"
              type="button"
              title="افزودن ناظر"
              aria-label="افزودن ناظر"
              :class="{ 'is-open': observerPickerOpen }"
              @click.stop="observerPickerOpen = !observerPickerOpen"
            >
              @
            </button>
            <div v-if="observerPickerOpen" class="mention-dropdown" @click.stop>
              <p class="mention-dropdown-title">اعضای مجموعه</p>
              <button
                v-for="user in observerMembers"
                :key="user.id"
                type="button"
                class="mention-option"
                @click="addObserver(user)"
              >
                <UserAvatar :person="user" :name="user.name" size="sm" />
                <span>
                  <strong>{{ user.name }}</strong>
                  <small>{{ user.jobTitle || user.department || 'عضو مجموعه' }}</small>
                </span>
              </button>
              <p v-if="!observerMembers.length" class="mention-empty">عضوی برای انتخاب نیست.</p>
            </div>
          </div>
          <div class="mention-selected">
            <span v-for="user in selectedObservers" :key="user.id" class="mention-pill">
              @{{ user.name }}
              <button type="button" aria-label="حذف ناظر" @click="removeObserver(user.id)">×</button>
            </span>
            <span v-if="!selectedObservers.length" class="mention-placeholder">برای افزودن ناظر روی @ بزنید</span>
          </div>
        </div>
      </div>

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
.observer-field {
  display: grid;
  gap: 8px;
}
.observer-picker {
  display: grid;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  background: #fff;
}
.mention-trigger-wrap {
  position: relative;
  display: inline-flex;
}
.mention-at-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(52, 144, 139, 0.2);
  background: #f8fafc;
  color: #134e4a;
  font-weight: 900;
  cursor: pointer;
}
.mention-at-btn.is-open,
.mention-at-btn:hover {
  background: rgba(47, 157, 137, 0.12);
  border-color: #2f9d89;
}
.mention-dropdown {
  position: absolute;
  inset-inline-start: 0;
  top: calc(100% + 8px);
  z-index: 20;
  width: min(320px, 88vw);
  max-height: 240px;
  overflow: auto;
  display: grid;
  gap: 6px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  background: #fff;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
}
.mention-dropdown-title {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 800;
  color: #64748b;
}
.mention-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  text-align: start;
  cursor: pointer;
}
.mention-option:hover {
  background: rgba(47, 157, 137, 0.08);
}
.mention-option strong,
.mention-option small {
  display: block;
}
.mention-option small {
  color: #64748b;
  font-size: 11px;
}
.mention-empty {
  margin: 0;
  color: #94a3b8;
  font-size: 12px;
}
.mention-selected {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 28px;
}
.mention-placeholder {
  color: #94a3b8;
  font-size: 12px;
}
.mention-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(47, 157, 137, 0.12);
  color: #134e4a;
  font-size: 12px;
  font-weight: 700;
}
.mention-pill button {
  border: 0;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}
</style>
