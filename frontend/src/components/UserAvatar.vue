<script setup>
import { computed } from 'vue'

import { personAvatarUrl, resolveAvatarUrl } from '../utils/avatar'
import { inferGenderFromName } from '../utils/gender'

const props = defineProps({
  name: { type: String, default: '' },
  avatar: { type: String, default: '' },
  avatarUrl: { type: String, default: '' },
  avatarImage: { type: String, default: '' },
  person: { type: Object, default: null },
  gender: { type: String, default: '' },
  size: { type: String, default: 'md' },
  alt: { type: String, default: '' },
})

const resolvedGender = computed(() => {
  const explicit = String(props.gender || '').toLowerCase()
  if (explicit === 'female' || explicit === 'male') return explicit
  return inferGenderFromName(props.name || props.person?.name || '')
})

const photoUrl = computed(() => {
  if (props.person) {
    const fromPerson = personAvatarUrl(props.person)
    if (fromPerson) return fromPerson
  }
  return resolveAvatarUrl(props.avatarUrl, props.avatarImage)
})

const label = computed(() => props.alt || props.name || props.person?.name || 'پروفایل')
</script>

<template>
  <div
    class="user-avatar-face"
    :class="[
      `size-${size}`,
      photoUrl ? 'has-photo' : `is-${resolvedGender}`,
    ]"
    :title="label"
    role="img"
    :aria-label="label"
  >
    <img v-if="photoUrl" :src="photoUrl" :alt="label" loading="lazy" />

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
  flex: 0 0 auto;
  overflow: hidden;
  background: var(--avatar-bg);
  color: var(--avatar-fg);
  box-shadow: inset 0 0 0 1px var(--avatar-ring);
}
.user-avatar-face.has-photo {
  background: #e8f2f0;
}
.user-avatar-face.is-female {
  --avatar-bg: linear-gradient(160deg, #fce7f3 0%, #fbcfe8 100%);
  --avatar-fg: #9d174d;
  --avatar-ring: rgba(219, 39, 119, 0.18);
}
.user-avatar-face.is-male {
  --avatar-bg: linear-gradient(160deg, #e0f2fe 0%, #bae6fd 100%);
  --avatar-fg: #075985;
  --avatar-ring: rgba(14, 165, 233, 0.18);
}
.user-avatar-face.is-unknown {
  --avatar-bg: linear-gradient(160deg, #edf8f6 0%, #d8ece8 100%);
  --avatar-fg: #1f5c59;
}
.user-avatar-face img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.avatar-placeholder {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
}
.avatar-person-icon {
  width: 58%;
  height: 58%;
}
.size-xs { width: 28px; height: 28px; border-radius: 9px; }
.size-sm { width: 34px; height: 34px; border-radius: 11px; }
.size-md { width: 44px; height: 44px; border-radius: 14px; }
.size-lg { width: 64px; height: 64px; border-radius: 18px; }
.size-xl { width: 88px; height: 88px; border-radius: 24px; }
</style>
