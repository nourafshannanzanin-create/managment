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
  const fromName = String(props.name || '').trim()
  if (fromName) return fromName.slice(0, 1)
  return '?'
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

    <div v-else-if="resolvedGender === 'female'" class="avatar-gender-badge" aria-hidden="true">
      <svg class="gender-icon" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="15" r="9.5" fill="currentColor" />
        <path
          d="M11.5 43.5c1.8-9.2 7.2-14.5 12.5-14.5s10.7 5.3 12.5 14.5"
          fill="currentColor"
        />
        <path
          d="M17 22.5c1.6 3.2 4.1 4.8 7 4.8s5.4-1.6 7-4.8"
          fill="currentColor"
          opacity="0.22"
        />
      </svg>
    </div>

    <div v-else-if="resolvedGender === 'male'" class="avatar-gender-badge" aria-hidden="true">
      <svg class="gender-icon" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="15.2" r="9" fill="currentColor" />
        <path
          d="M10.5 43.5c1.6-8.8 6.5-13.8 13.5-13.8s11.9 5 13.5 13.8"
          fill="currentColor"
        />
        <path
          d="M15.5 11.5c2.3-2.1 5.2-3.2 8.5-3.2s6.2 1.1 8.5 3.2"
          fill="currentColor"
          opacity="0.18"
        />
      </svg>
    </div>

    <span v-else class="avatar-initial">{{ initial }}</span>
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
  line-height: 1;
  user-select: none;
  isolation: isolate;
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

.user-avatar-face.is-female,
.user-avatar-face.is-male {
  font-size: 0;
}

.user-avatar-face img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-gender-badge {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  border-radius: inherit;
  background: var(--avatar-bg);
  color: var(--avatar-fg);
}

.user-avatar-face.is-female .avatar-gender-badge {
  background: linear-gradient(160deg, #faf1f5 0%, #f0dde6 100%);
}

.user-avatar-face.is-male .avatar-gender-badge {
  background: linear-gradient(160deg, #edf8f6 0%, #d8ece8 100%);
}

.gender-icon {
  width: 78%;
  height: 78%;
  display: block;
}

.avatar-initial {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  font-weight: 800;
  font-size: 1em;
  color: var(--avatar-fg);
  background: var(--avatar-bg);
}

.size-sm { width: 34px; height: 34px; border-radius: 10px; font-size: 0.85rem; }
.size-md { width: 44px; height: 44px; border-radius: 14px; font-size: 1rem; }
.size-lg { width: 64px; height: 64px; border-radius: 18px; font-size: 1.35rem; }
.size-xl { width: 88px; height: 88px; border-radius: 24px; font-size: 1.7rem; }
</style>
