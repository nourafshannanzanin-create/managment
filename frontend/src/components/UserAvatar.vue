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

const initial = computed(() => {
  const fromAvatar = String(props.avatar || '').trim()
  if (fromAvatar) return fromAvatar.slice(0, 1)
  return String(props.name || '?').trim().slice(0, 1) || '?'
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
    <svg
      v-else-if="resolvedGender === 'female'"
      class="gender-icon"
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="24" cy="16" r="8.5" fill="currentColor" opacity="0.92" />
      <path
        d="M10 40.5c1.8-8.2 7.2-12.5 14-12.5s12.2 4.3 14 12.5"
        stroke="currentColor"
        stroke-width="5.2"
        stroke-linecap="round"
        fill="none"
      />
      <path
        d="M14.5 18.5c1.2 5.5 4.2 8.2 9.5 8.2s8.3-2.7 9.5-8.2"
        stroke="currentColor"
        stroke-width="3.2"
        stroke-linecap="round"
        fill="none"
        opacity="0.55"
      />
    </svg>
    <svg
      v-else-if="resolvedGender === 'male'"
      class="gender-icon"
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="24" cy="16.5" r="8" fill="currentColor" opacity="0.92" />
      <path
        d="M11 40c1.6-7.6 6.6-11.5 13-11.5S38.4 32.4 40 40"
        stroke="currentColor"
        stroke-width="5.2"
        stroke-linecap="round"
        fill="none"
      />
      <path
        d="M16 11.2c2.2-2.4 5-3.7 8-3.7s5.8 1.3 8 3.7"
        stroke="currentColor"
        stroke-width="3"
        stroke-linecap="round"
        fill="none"
        opacity="0.45"
      />
    </svg>
    <span v-else>{{ initial }}</span>
  </div>
</template>

<style scoped>
.user-avatar-face {
  --avatar-bg: #dcefec;
  --avatar-fg: #1f5c59;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  overflow: hidden;
  flex: 0 0 auto;
  background: var(--avatar-bg);
  color: var(--avatar-fg);
  font-weight: 800;
  line-height: 1;
  user-select: none;
}

.user-avatar-face.has-photo {
  background: #e4f4f2;
}

.user-avatar-face.is-female {
  --avatar-bg: #f3e4ea;
  --avatar-fg: #8a4a63;
}

.user-avatar-face.is-male {
  --avatar-bg: #dcefec;
  --avatar-fg: #1f5c59;
}

.user-avatar-face.is-unknown {
  --avatar-bg: #e4f4f2;
  --avatar-fg: #1f5c59;
}

.user-avatar-face img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.gender-icon {
  width: 62%;
  height: 62%;
  display: block;
}

.size-sm { width: 34px; height: 34px; border-radius: 10px; font-size: 0.85rem; }
.size-md { width: 44px; height: 44px; border-radius: 14px; font-size: 1rem; }
.size-lg { width: 64px; height: 64px; border-radius: 18px; font-size: 1.35rem; }
.size-xl { width: 88px; height: 88px; border-radius: 24px; font-size: 1.7rem; }
</style>
