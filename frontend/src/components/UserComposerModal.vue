<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import UserAvatar from './UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const { availableManagerDirectory, state, fieldHasError, submitUser } = useWorkflowHub()

const sectionAccessOptions = [
  { key: 'users', title: 'کاربران' },
  { key: 'expenses', title: 'هزینه‌ها' },
  { key: 'reports', title: 'گزارشات' },
  { key: 'settings', title: 'تنظیمات' },
]

function onAvatarSelected(event) {
  const file = event.target.files?.[0] || null
  if (formPreviewNeedsRevoke()) {
    URL.revokeObjectURL(propsFormPreview())
  }
  if (!file) {
    clearAvatar()
    return
  }
  if (!String(file.type || '').startsWith('image/')) {
    event.target.value = ''
    return
  }
  state.userForm.avatarFile = file
  state.userForm.avatarPreview = URL.createObjectURL(file)
}

function propsFormPreview() {
  return state.userForm.avatarPreview || ''
}

function formPreviewNeedsRevoke() {
  return String(state.userForm.avatarPreview || '').startsWith('blob:')
}

function clearAvatar() {
  if (formPreviewNeedsRevoke()) URL.revokeObjectURL(state.userForm.avatarPreview)
  state.userForm.avatarFile = null
  state.userForm.avatarPreview = ''
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">کاربر جدید</p>
        <h2>افزودن کارمند</h2>
      </div>

      <section class="user-avatar-uploader">
        <UserAvatar
          :name="form.fullName"
          :avatar-url="form.avatarPreview"
          size="lg"
        />
        <div class="user-avatar-actions">
          <strong>عکس پروفایل</strong>
          <p>تصویر در فهرست کاربران، تنظیمات و صفحه ورود/خروج نمایش داده می‌شود. بدون عکس، آیکون زنانه/مردانه بر اساس نام می‌آید.</p>
          <div class="user-avatar-buttons">
            <label class="action-btn tone-primary avatar-upload-btn">
              <IconlyIcon name="person_add" decorative />
              <span>{{ form.avatarFile ? 'تغییر عکس' : 'افزودن پروفایل' }}</span>
              <input type="file" accept="image/*" @change="onAvatarSelected" />
            </label>
            <button
              v-if="form.avatarFile"
              class="action-btn tone-soft"
              type="button"
              @click="clearAvatar"
            >
              <IconlyIcon name="delete" decorative />
              <span>حذف عکس</span>
            </button>
          </div>
          <small v-if="form.avatarFile?.name" class="avatar-file-name">{{ form.avatarFile.name }}</small>
        </div>
      </section>

      <div class="modal-grid two-col">
        <label :class="['field-shell', fieldHasError('fullName') && 'has-error']">
          <span>نام کامل</span>
          <input v-model="form.fullName" type="text" />
        </label>

        <label :class="['field-shell', fieldHasError('username') && 'has-error']">
          <span>نام کاربری</span>
          <input v-model="form.username" type="text" dir="ltr" />
        </label>

        <label :class="['field-shell', fieldHasError('password') && 'has-error']">
          <span>رمز عبور</span>
          <input v-model="form.password" type="password" />
        </label>

        <label class="field-shell">
          <span>موبایل</span>
          <input v-model="form.phone" type="text" dir="ltr" />
        </label>

        <label class="field-shell">
          <span>نوع دسترسی</span>
          <select v-model="form.accessRole">
            <option value="manager">مدیر</option>
            <option value="employee">کارمند</option>
          </select>
        </label>

        <label class="field-shell">
          <span>بخش</span>
          <select v-model="form.department">
            <option value="">انتخاب بخش</option>
            <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option>
          </select>
        </label>

        <label class="field-shell">
          <span>مدیر مستقیم</span>
          <select v-model="form.managerId">
            <option value="">بدون مدیر</option>
            <option v-for="item in availableManagerDirectory()" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </label>
      </div>

      <label class="field-shell">
        <span>عنوان شغلی</span>
        <input v-model="form.jobTitle" type="text" />
      </label>

      <section class="surface-inline user-access-panel">
        <div class="section-label-row compact">
          <div>
            <h3>دسترسی به بخش‌ها</h3>
          </div>
        </div>

        <div class="modal-grid access-check-grid">
          <label
            v-for="item in sectionAccessOptions"
            :key="item.key"
            :class="['check-tile', form.sectionAccess[item.key] && 'is-checked']"
          >
            <input v-model="form.sectionAccess[item.key]" type="checkbox" />
            <IconlyIcon :name="form.sectionAccess[item.key] ? 'check_circle' : 'radio_button_unchecked'" class="check-state" decorative />
            <div>
              <strong>{{ item.title }}</strong>
            </div>
            <span class="check-tile-badge">انتخاب شده</span>
          </label>
        </div>
      </section>

      <ErrorNotice :error="state.lastErrorDetails" compact />

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <IconlyIcon name="close" decorative />
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" type="button" :disabled="submitting" @click="submitUser">
          <IconlyIcon name="person_add" decorative />
          <span>{{ submitting ? 'در حال ایجاد...' : 'ایجاد کاربر' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.user-avatar-uploader {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  background: rgba(220, 239, 236, 0.55);
}

.user-avatar-actions {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.user-avatar-actions strong {
  color: #152523;
}

.user-avatar-actions p {
  margin: 0;
  color: #45605c;
  font-size: 0.82rem;
  line-height: 1.6;
}

.user-avatar-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.avatar-upload-btn {
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.avatar-upload-btn input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.avatar-file-name {
  color: #45605c;
  direction: ltr;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-access-panel {
  display: grid;
  gap: 14px;
}

.section-label-row.compact h3,
.section-label-row.compact p {
  margin: 0;
}

.access-check-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.check-tile {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(36, 59, 107, 0.1);
  background: rgba(255, 255, 255, 0.74);
  color: #203255;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.check-tile input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.check-tile.is-checked {
  border-color: #3264a9;
  background: #eff6ff;
  box-shadow: inset 3px 0 0 #3264a9;
}

.check-state {
  color: #98a2b3;
  font-size: 22px;
}

.check-tile.is-checked .check-state,
.check-tile.is-checked strong {
  color: #17315d;
}

.check-tile strong {
  display: block;
}

@media (max-width: 760px) {
  .user-avatar-uploader {
    grid-template-columns: 1fr;
    justify-items: start;
  }

  .access-check-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
