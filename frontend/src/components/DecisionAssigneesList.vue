<script setup>
import IconlyIcon from './base/IconlyIcon.vue'

defineProps({
  decisions: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <div v-if="decisions.length" class="decision-list">
    <article
      v-for="item in decisions"
      :key="item.id"
      :class="['decision-row', `is-${item.status || 'pending'}`]"
    >
      <div class="decision-row-main">
        <div class="decision-row-meta">
          <strong>{{ item.approver }}</strong>
          <small>{{ item.role }}</small>
        </div>
        <span class="decision-status-badge">{{ item.statusLabel }}</span>
      </div>
      <p v-if="item.decisionNote" class="decision-row-note">{{ item.decisionNote }}</p>
    </article>
  </div>
  <div v-else class="empty-state-inline centered-empty">
    <IconlyIcon name="hourglass_empty" decorative />
    <p>ارجاع گیرنده ای ثبت نشده است.</p>
  </div>
</template>
