<script setup>
import { computed } from 'vue'

import { inferGenderFromName } from '../utils/gender'

const props = defineProps({
  name: { type: String, default: '' },
  avatar: { type: String, default: '' },
  avatarUrl: { type: String, default: '' },
  gender: { type: String, default: '' },
  size: { type: String, default: 'md' },
  alt: { type: String, default: '' },
})

const resolvedGender = computed(() => {
  const explicit = String(props.gender || '').toLowerCase()
  if (explicit === 'female' || explicit === 'male') return explicit
  return inferGenderFromName(props.name)
})

const label = computed(() => props.alt || props.name || 'پروفایل')
</script>

<template>
  <div
    class="user-avatar-face"
    :class="[
      `size-${size}`,
      avatarUrl ? 'has-photo' : `is-${resolvedGender}`,
    ]"
    :title="label"
    role="img"
    :aria-label="label"
  >
    <img v-if="avatarUrl" :src="avatarUrl" :alt="label" />

    <div v-else class="avatar-placeholder" aria-hidden="true">
      <svg class="avatar-person-icon" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="17.5" r="8.5" stroke="currentColor" stroke-width="2.6" />
        <path
          d="M10.5 40.5c1.8-8.8 7.1-13.5 13.5-13.5s11.7 4.7 13.5 13.5"
          stroke="currentColor"
          stroke-width="2.6"
          stroke-linecap="round"
        />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.user-avatar-face {
  --avatar-bg: linear-gradient(160deg, #edf8f6 0%, #d8ece8 100%);
  --avatar-fg: #1f5c59;
  --avatar-ring: rgba(52, 144, 139, 0.18);
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  overflow: hidden;
  flex: 0 0 auto;
  background: var(--avatar-bg);
  color: var(--avatar-fg);
  line-height: 1;
  user-select: none;
  isolation: isolate;
  border: 1px solid var(--avatar-ring);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.user-avatar-face.has-photo {
  background: #e4f4f2;
  border-color: rgba(52, 144, 139, 0.14);
  box-shadow: none;
}

.user-avatar-face.is-female {
  --avatar-bg: linear-gradient(160deg, #faf1f5 0%, #f0dde6 100%);
  --avatar-fg: #8a4a63;
  --avatar-ring: rgba(138, 74, 99, 0.16);
}

.user-avatar-face.is-male {
  --avatar-bg: linear-gradient(160deg, #edf8f6 0%, #d8ece8 100%);
  --avatar-fg: #1f5c59;
  --avatar-ring: rgba(52, 144, 139, 0.18);
}

.user-avatar-face.is-unknown {
  --avatar-bg: linear-gradient(160deg, #f3f8f7 0%, #e4f4f2 100%);
  --avatar-fg: #2f6f6a;
  --avatar-ring: rgba(52, 144, 139, 0.14);
}

.user-avatar-face img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  border-radius: inherit;
  background: var(--avatar-bg);
  color: var(--avatar-fg);
}

.avatar-person-icon {
  width: 72%;
  height: 72%;
  display: block;
  opacity: 0.92;
}

.size-sm { width: 34px; height: 34px; border-radius: 10px; font-size: 0.85rem; }
.size-md { width: 44px; height: 44px; border-radius: 14px; font-size: 1rem; }
.size-lg { width: 64px; height: 64px; border-radius: 18px; font-size: 1.35rem; }
.size-xl { width: 88px; height: 88px; border-radius: 24px; font-size: 1.7rem; }
</style>
