<template>
  <span class="iconly-shell" :class="[`size-${size}`, { decorative }]" :aria-hidden="decorative ? 'true' : undefined">
    <img v-if="src" :src="src" :alt="decorative ? '' : alt" class="iconly-img" />
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { iconSrc, resolveIconName } from '../../config/iconly'

const props = defineProps({
  name: { type: String, required: true },
  alt: { type: String, default: '' },
  size: { type: String, default: 'md' },
  decorative: { type: Boolean, default: true }
})

const resolvedName = computed(() => resolveIconName(props.name))
const src = computed(() => iconSrc(resolvedName.value))
</script>

<style scoped>
.iconly-shell {
  --iconly-filter: brightness(0) saturate(100%) invert(47%) sepia(24%) saturate(785%) hue-rotate(131deg) brightness(92%) contrast(88%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1em;
  height: 1em;
  font-size: 18px;
  flex: 0 0 auto;
  line-height: 1;
}

.iconly-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: var(--iconly-filter);
}

.size-xs { font-size: 14px; }
.size-sm { font-size: 16px; }
.size-md { font-size: 18px; }
.size-lg { font-size: 20px; }
.size-xl { font-size: 24px; }
.size-2xl { font-size: 24px; }
</style>
