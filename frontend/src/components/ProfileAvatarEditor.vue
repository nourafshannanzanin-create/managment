<script setup>
import { computed, ref } from 'vue'

import IconlyIcon from './base/IconlyIcon.vue'
import UserAvatar from './UserAvatar.vue'

const props = defineProps({
  name: { type: String, default: '' },
  avatar: { type: String, default: '' },
  avatarUrl: { type: String, default: '' },
  avatarFileName: { type: String, default: '' },
  previewUrl: { type: String, default: '' },
  size: { type: String, default: 'xl' },
  busy: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  title: { type: String, default: 'عکس پروفایل' },
  description: {
    type: String,
    default: 'تا قبل از آپلود، آیکون متناسب با نام (آقا/خانم) نمایش داده می‌شود.',
  },
  addLabel: { type: String, default: 'افزودن پروفایل' },
  changeLabel: { type: String, default: 'تغییر عکس' },
})

const emit = defineEmits(['select', 'clear'])

const inputRef = ref(null)

const displayUrl = computed(() => props.previewUrl || props.avatarUrl || '')
const hasPhoto = computed(() => Boolean(displayUrl.value))
const fileLabel = computed(() => {
  if (props.avatarFileName) return props.avatarFileName
  return hasPhoto.value ? 'عکس پروفایل تنظیم شده' : ''
})

function openPicker() {
  if (props.busy || props.disabled) return
  inputRef.value?.click()
}

function onFileChange(event) {
  const file = event.target.files?.[0] || null
  event.target.value = ''
  if (!file) return
  if (!String(file.type || '').startsWith('image/')) return
  emit('select', file)
}

function onClear() {
  if (props.busy || props.disabled || !hasPhoto.value) return
  emit('clear')
}
</script>

<template>
  <section class="profile-avatar-editor">
    <div class="profile-avatar-editor-main">
      <UserAvatar
        :name="name"
        :avatar="avatar"
        :avatar-url="displayUrl"
        :size="size"
      />
      <div class="profile-avatar-editor-copy">
        <strong>{{ title }}</strong>
        <p v-if="name" class="profile-avatar-name">{{ name }}</p>
        <p>{{ description }}</p>
        <small v-if="fileLabel" class="profile-avatar-file" dir="ltr">{{ fileLabel }}</small>
      </div>
    </div>

    <div class="profile-avatar-editor-actions">
      <input
        ref="inputRef"
        class="sr-only"
        type="file"
        accept="image/*"
        :disabled="busy || disabled"
        @change="onFileChange"
      />
      <button
        class="action-btn tone-primary"
        type="button"
        :disabled="busy || disabled"
        @click="openPicker"
      >
        <IconlyIcon name="person_add" decorative />
        <span>{{ busy ? 'در حال ذخیره...' : (hasPhoto ? changeLabel : addLabel) }}</span>
      </button>
      <button
        v-if="hasPhoto"
        class="action-btn tone-soft"
        type="button"
        :disabled="busy || disabled"
        @click="onClear"
      >
        <IconlyIcon name="delete" decorative />
        <span>حذف عکس</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.profile-avatar-editor {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(180px, 0.75fr);
  gap: 16px;
  align-items: center;
  padding: 16px 18px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(247, 251, 250, 0.96), rgba(220, 239, 236, 0.9));
  border: 1px solid rgba(52, 144, 139, 0.16);
  box-shadow: 0 10px 28px rgba(31, 92, 89, 0.08);
}

.profile-avatar-editor-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.profile-avatar-editor-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.profile-avatar-editor-copy strong {
  color: #152523;
  font-size: 0.98rem;
}

.profile-avatar-name {
  margin: 0;
  color: #1f5c59;
  font-size: 0.92rem;
  font-weight: 800;
}

.profile-avatar-editor-copy p {
  margin: 0;
  color: #45605c;
  font-size: 0.82rem;
  line-height: 1.6;
}

.profile-avatar-file {
  color: #1f5c59;
  font-size: 0.78rem;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-avatar-editor-actions {
  display: grid;
  gap: 8px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 760px) {
  .profile-avatar-editor {
    grid-template-columns: 1fr;
  }
}
</style>
