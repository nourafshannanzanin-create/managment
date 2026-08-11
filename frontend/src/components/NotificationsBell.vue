<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import IconlyIcon from './base/IconlyIcon.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { markCenterRead, toastState } from '../utils/notify'

const router = useRouter()
const {
  state,
  openApprovalDetail,
  openExpenseDetail,
  openRequestDetail,
  chatUnreadCount,
  supportUnreadCount,
  markSupportTicketsSeen,
} = useWorkflowHub()

const open = ref(false)
const rootEl = ref(null)
const panelEl = ref(null)
const panelStyle = ref({})

const liveItems = computed(() => {
  const rows = []

  ;(state.approvals || [])
    .filter((item) => item.canApprove)
    .slice(0, 8)
    .forEach((item) => {
      rows.push({
        id: `approval-${item.id}`,
        type: 'warning',
        title: 'تایید در انتظار',
        message: item.title || `تاییدیه #${item.id}`,
        meta: item.owner || item.status || '',
        icon: 'fact_check',
        createdAt: item.updatedAt || item.createdAt || '',
        onOpen: () => {
          openApprovalDetail(item.id)
          open.value = false
        },
      })
    })

  ;(state.requests || [])
    .filter((item) => item.canApprove)
    .slice(0, 6)
    .forEach((item) => {
      rows.push({
        id: `request-${item.id}`,
        type: 'info',
        title: 'درخواست نیازمند بررسی',
        message: item.title || `درخواست #${item.id}`,
        meta: item.owner || item.status || '',
        icon: 'assignment',
        createdAt: item.updatedAt || item.createdAt || '',
        onOpen: () => {
          openRequestDetail(item.id)
          open.value = false
        },
      })
    })

  ;(state.expenses || [])
    .filter((item) => item.canApprove)
    .slice(0, 6)
    .forEach((item) => {
      rows.push({
        id: `expense-${item.id}`,
        type: 'info',
        title: 'هزینه نیازمند تایید',
        message: item.title || `هزینه #${item.id}`,
        meta: item.owner || item.status || '',
        icon: 'payments',
        createdAt: item.updatedAt || item.createdAt || '',
        onOpen: () => {
          openExpenseDetail(item.id)
          open.value = false
        },
      })
    })

  if (Number(chatUnreadCount.value || 0) > 0) {
    rows.push({
      id: 'chat-unread',
      type: 'info',
      title: 'پیام خوانده‌نشده',
      message: `${Number(chatUnreadCount.value).toLocaleString('fa-IR')} گفتگوی جدید دارید`,
      meta: 'چت سازمانی',
      icon: 'forum',
      createdAt: '',
      onOpen: () => {
        open.value = false
        router.push('/chat')
      },
    })
  }

  if (state.currentUser.isHq) {
    ;(state.support.tickets || [])
      .filter((ticket) => ['open', 'pending'].includes(String(ticket.status || '')))
      .slice(0, 6)
      .forEach((ticket) => {
        rows.push({
          id: `support-${ticket.id}`,
          type: 'warning',
          title: 'تیکت پشتیبانی',
          message: ticket.subject || ticket.title || `تیکت #${ticket.id}`,
          meta: ticket.statusLabel || ticket.status || '',
          icon: 'support_agent',
          createdAt: ticket.updatedAt || ticket.createdAt || '',
          onOpen: () => {
            open.value = false
            router.push('/support')
          },
        })
      })
  } else if (Number(supportUnreadCount.value || 0) > 0) {
    rows.push({
      id: 'support-unread',
      type: 'success',
      title: 'پاسخ پشتیبانی',
      message: `${Number(supportUnreadCount.value).toLocaleString('fa-IR')} پاسخ جدید دارید`,
      meta: 'پشتیبانی',
      icon: 'support_agent',
      createdAt: '',
      onOpen: () => {
        markSupportTicketsSeen()
        open.value = false
        router.push('/support')
      },
    })
  }

  return rows
})

const historyItems = computed(() =>
  (toastState.center || []).map((item) => ({
    id: `history-${item.id}`,
    type: item.type || 'info',
    title: item.title || 'اعلان',
    message: item.message,
    meta: formatWhen(item.createdAt),
    icon: item.type === 'error' ? 'error' : item.type === 'success' ? 'check_circle' : 'notifications',
    createdAt: item.createdAt || '',
    read: Boolean(item.read),
    onOpen: () => {
      markCenterRead(item.id)
      open.value = false
      if (item.route) router.push(item.route)
    },
  })),
)

const items = computed(() => {
  const seen = new Set()
  const merged = []
  ;[...liveItems.value, ...historyItems.value].forEach((item) => {
    if (seen.has(item.id)) return
    seen.add(item.id)
    merged.push(item)
  })
  return merged.slice(0, 24)
})

const unreadCount = computed(() => {
  const live = liveItems.value.length
  const historyUnread = (toastState.center || []).filter((item) => !item.read).length
  return live + historyUnread
})

const badgeLabel = computed(() => {
  const count = unreadCount.value
  if (count <= 0) return ''
  if (count > 9) return '۹+'
  return count.toLocaleString('fa-IR')
})

function formatWhen(value) {
  if (!value) return ''
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))
  } catch {
    return ''
  }
}

async function updatePanelPosition() {
  await nextTick()
  const trigger = rootEl.value?.querySelector('.notifications-bell-btn')
  if (!trigger) return
  const rect = trigger.getBoundingClientRect()
  const panelWidth = Math.min(380, window.innerWidth - 24)
  const left = Math.max(12, Math.min(window.innerWidth - panelWidth - 12, rect.right - panelWidth))
  panelStyle.value = {
    top: `${Math.min(window.innerHeight - 120, rect.bottom + 12)}px`,
    left: `${left}px`,
    width: `${panelWidth}px`,
  }
}

async function togglePanel() {
  open.value = !open.value
  if (open.value) {
    markCenterRead()
    await updatePanelPosition()
  }
}

function onDocumentPointer(event) {
  if (!open.value) return
  if (
    rootEl.value &&
    !rootEl.value.contains(event.target) &&
    panelEl.value &&
    !panelEl.value.contains(event.target)
  ) {
    open.value = false
  }
}

function onKeydown(event) {
  if (event.key === 'Escape') open.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointer)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', updatePanelPosition)
  window.addEventListener('scroll', updatePanelPosition, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointer)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', updatePanelPosition)
  window.removeEventListener('scroll', updatePanelPosition, true)
})
</script>

<template>
  <div ref="rootEl" class="notifications-bell" dir="rtl">
    <button
      class="icon-btn notifications-bell-btn"
      type="button"
      aria-label="اعلان‌ها"
      title="اعلان‌ها"
      :aria-expanded="open ? 'true' : 'false'"
      @click="togglePanel"
    >
      <IconlyIcon name="notifications" size="lg" decorative />
      <span v-if="badgeLabel" class="notifications-bell-badge">{{ badgeLabel }}</span>
    </button>

    <Teleport to="body">
      <div
        v-if="open"
        ref="panelEl"
        class="notifications-panel"
        :style="panelStyle"
        dir="rtl"
        role="dialog"
        aria-label="فهرست اعلان‌ها"
      >
        <header class="notifications-panel-head">
          <div>
            <strong>اعلان‌ها</strong>
            <span>{{ unreadCount ? `${badgeLabel || unreadCount.toLocaleString('fa-IR')} مورد` : 'مورد جدیدی نیست' }}</span>
          </div>
        </header>

        <div v-if="items.length" class="notifications-list">
          <button
            v-for="item in items"
            :key="item.id"
            class="notifications-item"
            :class="[`is-${item.type}`, item.read && 'is-read']"
            type="button"
            @click="item.onOpen"
          >
            <span class="notifications-item-icon" aria-hidden="true">
              <IconlyIcon :name="item.icon" decorative />
            </span>
            <span class="notifications-item-copy">
              <strong>{{ item.title }}</strong>
              <span>{{ item.message }}</span>
              <small v-if="item.meta">{{ item.meta }}</small>
            </span>
          </button>
        </div>

        <p v-else class="notifications-empty">اعلانی برای نمایش وجود ندارد.</p>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.notifications-bell {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.notifications-bell-btn {
  position: relative;
  width: 48px !important;
  height: 48px !important;
  min-width: 48px !important;
  min-height: 48px !important;
  border-radius: 16px !important;
  background: #dcefec !important;
  color: #1f5c59 !important;
}

.notifications-bell-badge {
  position: absolute;
  top: -2px;
  inset-inline-start: -2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #c2410c;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 0 0 2px #f3f9f7;
}

.notifications-panel {
  position: fixed;
  z-index: 10050;
  max-height: min(70dvh, 520px);
  overflow: auto;
  display: grid;
  gap: 0;
  border-radius: 16px;
  background: #f7fbfa;
  border: 1px solid rgba(52, 144, 139, 0.14);
  box-shadow: 0 18px 40px rgba(20, 60, 55, 0.16);
}

.notifications-panel-head {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 12px 14px;
  background: rgba(247, 251, 250, 0.96);
  border-bottom: 1px solid rgba(52, 144, 139, 0.1);
  backdrop-filter: blur(8px);
}

.notifications-panel-head strong {
  display: block;
  font-size: 0.95rem;
}

.notifications-panel-head span {
  display: block;
  margin-top: 2px;
  color: #5c6780;
  font-size: 0.75rem;
}

.notifications-list {
  display: grid;
}

.notifications-item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: start;
  width: 100%;
  padding: 12px 14px;
  border: 0;
  border-bottom: 1px solid rgba(52, 144, 139, 0.08);
  background: transparent;
  text-align: right;
  cursor: pointer;
  color: inherit;
  font: inherit;
}

.notifications-item:hover {
  background: rgba(52, 144, 139, 0.08);
}

.notifications-item.is-read {
  opacity: 0.72;
}

.notifications-item-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
}

.notifications-item.is-warning .notifications-item-icon {
  background: rgba(194, 65, 12, 0.12);
  color: #c2410c;
}

.notifications-item.is-success .notifications-item-icon {
  background: rgba(31, 138, 112, 0.12);
  color: #1f8a70;
}

.notifications-item.is-error .notifications-item-icon {
  background: rgba(185, 28, 28, 0.12);
  color: #b91c1c;
}

.notifications-item-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.notifications-item-copy strong {
  font-size: 0.82rem;
}

.notifications-item-copy span {
  color: #2a344c;
  font-size: 0.86rem;
  line-height: 1.45;
}

.notifications-item-copy small {
  color: #6a768f;
  font-size: 0.72rem;
}

.notifications-empty {
  margin: 0;
  padding: 28px 16px;
  text-align: center;
  color: #6a768f;
  font-size: 0.88rem;
}

@media (max-width: 640px) {
  .notifications-panel {
    inset-inline: 12px !important;
    top: 84px !important;
    width: auto !important;
    max-height: calc(100dvh - 108px);
    border-radius: 18px;
  }

  .notifications-item {
    grid-template-columns: 30px minmax(0, 1fr);
    padding: 12px;
  }

  .notifications-item-icon {
    width: 30px;
    height: 30px;
    border-radius: 9px;
  }
}
</style>
