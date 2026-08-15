<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import UserAvatar from './UserAvatar.vue'

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
          <UserAvatar
            :name="item.approver"
            :avatar-url="item.approverAvatarUrl || item.avatarUrl"
            :avatar-image="item.approverAvatarImage"
            size="sm"
          />
          <div class="decision-row-copy">
            <strong>{{ item.approver }}</strong>
            <small>{{ item.role }}</small>
          </div>
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

<style scoped>
.decision-row-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.decision-row-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}
</style>
