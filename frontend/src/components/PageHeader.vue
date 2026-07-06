<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  searchValue: { type: String, default: '' },
  searchPlaceholder: { type: String, default: '' },
  showSearch: { type: Boolean, default: false },
  actionLabel: { type: String, default: '' },
  actionIcon: { type: String, default: 'add' },
  actionTone: { type: String, default: 'primary' },
})

const emit = defineEmits(['update:searchValue', 'action', 'menu'])
</script>

<template>
</template>
