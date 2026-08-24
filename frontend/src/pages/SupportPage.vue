<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getTodayJalali } from '../utils/jalali'
import { createLiveEventSource, parseLiveEvent } from '../utils/live'
import { formatFileSize, prepareUploadFile, UPLOAD_LIMITS } from '../utils/uploads'
import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const router = useRouter()

const {
  state,
  loadSupportTickets,
  loadSupportTicketDetail,
  createSupportTicket,
  submitSupportReply,
  submitSupportFeedback,
  markSupportTicketsSeen,
  openProtectedFile,
} = useWorkflowHub()

const searchQuery = ref('')
const activeStatusTab = ref('open')
const activeCategoryTab = ref('all')
const messageThreadRef = ref(null)
const replyBody = ref('')
const sendingReply = ref(false)

let supportPollingTimer = null
let supportLiveStream = null
let supportLiveRefreshTimer = null
let supportPollingInFlight = false

const getEmptyContext = () => ({
  transaction_id: '',
  payment_amount: '',
  payment_date: '',
  order_number: '',
  service_name: '',
  device_type: '',
  browser_name: '',
  os_name: '',
  account_phone: '',
  account_issue: '',
})

const getTodayJalaliString = () => {
  const today = getTodayJalali()
  const month = String(today.jm).padStart(2, '0')
  const day = String(today.jd).padStart(2, '0')
  return `${today.jy}/${month}/${day}`
}

const ticketModal = reactive({
  open: false,
  mode: 'default',
  subject: '',
  description: '',
  category: 'technical',
  priority: 'medium',
  context: getEmptyContext(),
  attachments: [],
})

const attachmentPreparing = ref(false)
const attachmentError = ref('')

const feedback = reactive({
  score: 0,
  text: '',
})

const tickets = computed(() => state.support.tickets || [])
const selectedTicket = computed(() => state.support.selectedTicket)

const statusCount = computed(() => tickets.value.reduce((acc, item) => {
  if (acc[item.status] === undefined) acc[item.status] = 0
  acc[item.status] += 1
  return acc
}, { open: 0, pending: 0, answered: 0, closed: 0 }))

const statusTrack = computed(() => [
  { key: 'open', label: 'باز', icon: 'radio_button_checked', count: statusCount.value.open + statusCount.value.pending, description: 'در انتظار پاسخ پشتیبان — کارتابل' },
  { key: 'answered', label: 'منتظر مجموعه', icon: 'mark_chat_read', count: statusCount.value.answered, description: 'در انتظار پاسخ مجموعه — کارتابل' },
  { key: 'closed', label: 'بسته شده', icon: 'task_alt', count: statusCount.value.closed, description: 'قابل مشاهده؛ بدون شمارنده' },
])

const categoryTabs = [
  { key: 'all', label: 'همه' },
  { key: 'technical', label: 'فنی' },
  { key: 'financial', label: 'مالی' },
  { key: 'operations', label: 'عملیاتی' },
  { key: 'account', label: 'حساب' },
  { key: 'other', label: 'سایر' },
]

const priorities = [
  { key: 'low', label: 'کم' },
  { key: 'medium', label: 'متوسط' },
  { key: 'high', label: 'زیاد' },
  { key: 'urgent', label: 'فوری' },
]

const activeStatusLabel = computed(() => ({
  open: 'باز (کارتابل)',
  pending: 'در حال بررسی',
  answered: 'منتظر پاسخ مجموعه',
  closed: 'بسته شده',
}[activeStatusTab.value] || 'باز'))

const waitingForUserCount = computed(() => Number(statusCount.value.answered || 0))
const inProgressCount = computed(() => Number(statusCount.value.pending || 0) + Number(statusCount.value.open || 0))

const filteredTickets = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return tickets.value
    .filter((item) => {
      if (activeStatusTab.value === 'open') {
        if (!['open', 'pending'].includes(item.status)) return false
      } else if (item.status !== activeStatusTab.value) {
        return false
      }
      if (activeCategoryTab.value !== 'all' && item.category !== activeCategoryTab.value) return false
      if (!query) return true
      const haystack = `${item.id} ${item.subject} ${item.message || ''} ${item.category || ''} ${item.categoryLabel || ''} ${item.lastMessagePreview || ''}`.toLowerCase()
      return haystack.includes(query)
    })
    .sort((a, b) => new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0))
})

const conversationMessages = computed(() => {
  const ticket = selectedTicket.value
  if (!ticket) return []

  const messages = Array.isArray(ticket.messages) ? ticket.messages.filter((message) => message?.body) : []
  const normalized = messages.map((message, index) => ({
    ...message,
    id: message.id ?? `message-${index}`,
    sender: message.sender || ticket.requester || 'کاربر',
    createdAt: message.createdAt || message.created_at || ticket.createdAt || '',
    time: message.time || message.createdAtIso || '',
  }))

  if (normalized.length) {
    return normalized.sort((a, b) => new Date(a.createdAt || 0) - new Date(b.createdAt || 0))
  }

  if (!ticket.message) return []
  return [{
    id: `ticket-${ticket.id}-initial`,
    sender: ticket.requester || 'کاربر',
    senderPlatformRole: 'tenant',
    body: ticket.message,
    createdAt: ticket.createdAt || '',
    time: ticket.createdAtIso || ticket.time || '',
  }]
})

const isWalletCardPaymentDraft = computed(() => ticketModal.mode === 'wallet-card-payment')
const walletCardPaymentNotice = computed(() => {
  if (!isWalletCardPaymentDraft.value) return ''
  return 'این متن برای ثبت پرداخت کارت به کارت آماده شده است. فقط شماره یا کد تراکنش را تکمیل کنید. اگر امکان بارگذاری رسید را دارید، رسید واریز را هم اضافه کنید و بدون تغییر ساختار آماده، ثبت را بزنید.'
})
const selectedAttachmentNames = computed(() => (ticketModal.attachments || []).map((file) => file.name).join('، '))

const toFa = (value) => Number(value || 0).toLocaleString('fa-IR')

const statusClass = (value) => ({
  open: 'open',
  pending: 'pending',
  answered: 'answered',
  closed: 'closed',
}[value] || 'open')

const categoryLabel = (value) => ({
  technical: 'فنی',
  financial: 'مالی',
  operations: 'عملیاتی',
  account: 'حساب',
  other: 'سایر',
}[value] || value || 'سایر')

const priorityLabel = (value) => ({
  low: 'کم',
  medium: 'متوسط',
  high: 'زیاد',
  urgent: 'فوری',
}[value] || value || 'متوسط')

const clientStatusLabel = (ticket) => ticket?.statusLabel || ({
  open: 'باز',
  pending: 'در حال بررسی',
  answered: 'پاسخ داده شده',
  closed: 'بسته شده',
}[ticket?.status] || 'باز')

const isSupportMessage = (message) => ['hq_support', 'hq_admin'].includes(message?.senderPlatformRole)
const messageAlignmentClass = (message) => (isSupportMessage(message) ? 'support' : 'tenant')
const messageRoleLabel = (message) => (isSupportMessage(message) ? 'مرکز پشتیبانی' : 'شما')

const ticketLastResponder = (ticket) => {
  if (ticket?.respondedBy && ticket?.respondedAt) return `پاسخ توسط ${ticket.respondedBy}`
  if (ticket?.messages?.length) {
    const lastMessage = ticket.messages[ticket.messages.length - 1]
    return isSupportMessage(lastMessage) ? 'آخرین پیام از پشتیبانی' : 'آخرین پیام از شما'
  }
  return 'بدون پاسخ'
}

const satisfactionLabel = (value) => {
  if (!value) return 'ثبت نشده'
  return `${toFa(value)} از ۵`
}

const canRateTicket = (ticket) => {
  if (!ticket) return false
  if (!['answered', 'closed'].includes(ticket.status)) return false
  return !ticket.customerSatisfaction
}

const toggleStatusFilter = () => {
  const order = ['open', 'answered', 'closed']
  const currentIndex = order.findIndex((item) => item === activeStatusTab.value)
  activeStatusTab.value = order[(currentIndex + 1) % order.length]
}

const buildStructuredMessage = () => {
  const lines = [String(ticketModal.description || '').trim()]
  const contextLines = []

  const fieldMap = {
    transaction_id: 'شماره تراکنش',
    payment_amount: 'مبلغ پرداخت',
    payment_date: 'تاریخ پرداخت',
    service_name: 'سرویس',
    device_type: 'نوع دستگاه',
    browser_name: 'مرورگر / اپ',
    os_name: 'سیستم‌عامل',
    account_phone: 'موبایل حساب',
    account_issue: 'موضوع حساب',
  }

  Object.entries(ticketModal.context).forEach(([key, value]) => {
    if (key === 'order_number') return
    const text = String(value || '').trim()
    if (!text) return
    contextLines.push(`${fieldMap[key]}: ${text}`)
  })

  if (contextLines.length) {
    lines.push('')
    lines.push('اطلاعات مرتبط:')
    lines.push(...contextLines)
  }

  return lines.join('\n').trim()
}

const openCreateTicketModal = () => {
  ticketModal.open = true
  ticketModal.mode = 'default'
}

const openWalletPaymentTicketModal = () => {
  const amount = String(route.query.amount || '').trim()
  const walletName = String(route.query.wallet_name || '').trim()
  const walletId = String(route.query.wallet_id || '').trim()
  ticketModal.open = true
  ticketModal.mode = 'wallet-card-payment'
  ticketModal.category = 'financial'
  ticketModal.priority = 'high'
  ticketModal.subject = 'درخواست بررسی پرداخت کارت به کارت و واریز کیف پول'
  ticketModal.description = [
    'نوع درخواست: wallet-card-payment',
    'اینجانب مدیر سازمان، مبلغ واریز کیف پول را به صورت کارت به کارت پرداخت کرده‌ام.',
    'درخواست دارم پرداخت بررسی شود و در صورت تایید، به کیف پول سازمان واریز شود.',
    walletId ? `شناسه کیف پول مقصد: ${walletId}` : '',
    'شماره یا کد تراکنش و مشخصات رسید واریز را در این تیکت تکمیل می‌کنم.',
  ].filter(Boolean).join('\n')
  Object.assign(ticketModal.context, getEmptyContext(), {
    payment_amount: amount,
    payment_date: getTodayJalaliString(),
    order_number: walletName,
  })
}

const handleAttachmentChange = async (event) => {
  const input = event?.target
  const incoming = Array.from(input?.files || [])
  attachmentError.value = ''
  if (!incoming.length) return

  attachmentPreparing.value = true
  try {
    const nextAttachments = [...ticketModal.attachments]
    if (nextAttachments.length + incoming.length > UPLOAD_LIMITS.maxAttachments) {
      throw new Error(`حداکثر ${UPLOAD_LIMITS.maxAttachments} پیوست مجاز است.`)
    }
    for (const file of incoming) {
      nextAttachments.push(markRaw(await prepareUploadFile(file)))
    }
    ticketModal.attachments = nextAttachments
  } catch (error) {
    attachmentError.value = error.message || 'انتخاب فایل پیوست ناموفق بود.'
  } finally {
    attachmentPreparing.value = false
    if (input) input.value = ''
  }
}

const closeCreateTicketModal = () => {
  ticketModal.open = false
  ticketModal.mode = 'default'
  ticketModal.subject = ''
  ticketModal.description = ''
  ticketModal.category = 'technical'
  ticketModal.priority = 'medium'
  ticketModal.attachments = []
  attachmentError.value = ''
  Object.assign(ticketModal.context, getEmptyContext())
}

const resetSelectionUi = () => {
  replyBody.value = ''
  feedback.score = 0
  feedback.text = ''
}

const scrollMessagesToBottom = async () => {
  await nextTick()
  const thread = messageThreadRef.value
  if (thread) thread.scrollTop = thread.scrollHeight
}

const openTicketDetail = async (ticketId, options = {}) => {
  if (!ticketId) return
  if (!options.keepReply) replyBody.value = ''
  await loadSupportTicketDetail(ticketId)
  const ticket = state.support.selectedTicket
  feedback.score = Number(ticket?.customerSatisfaction || 0)
  feedback.text = ticket?.customerFeedback || ''
  if (ticket?.status === 'answered') {
    markSupportTicketsSeen([ticket.id])
  }
  if (!options.soft) {
    await scrollMessagesToBottom()
  }
}

const ensureActiveTicket = async () => {
  const visibleIds = filteredTickets.value.map((item) => item.id)
  if (!visibleIds.length) {
    state.support.selectedTicket = null
    resetSelectionUi()
    return
  }
  if (selectedTicket.value?.id && visibleIds.includes(selectedTicket.value.id)) return
  await openTicketDetail(visibleIds[0])
}

const submitTicket = async () => {
  await createSupportTicket({
    subject: ticketModal.subject,
    message: buildStructuredMessage(),
    category: ticketModal.category,
    priority: ticketModal.priority,
    attachments: ticketModal.attachments,
  })
  activeStatusTab.value = 'open'
  closeCreateTicketModal()
  const createdId = state.support.selectedTicket?.id
  if (createdId) await openTicketDetail(createdId)
}

const submitReply = async () => {
  if (!selectedTicket.value?.id || !replyBody.value.trim() || sendingReply.value || selectedTicket.value.status === 'closed') return
  sendingReply.value = true
  try {
    await submitSupportReply(selectedTicket.value.id, { body: replyBody.value.trim() })
    replyBody.value = ''
    await scrollMessagesToBottom()
  } finally {
    sendingReply.value = false
  }
}

const submitTicketFeedback = async () => {
  if (!selectedTicket.value?.id || !feedback.score) return
  await submitSupportFeedback(selectedTicket.value.id, {
    score: feedback.score,
    feedback: feedback.text,
  })
}

const refreshTicketsQuietly = async () => {
  if (supportPollingInFlight || ticketModal.open || sendingReply.value || state.support.submitting || document.visibilityState === 'hidden') return
  supportPollingInFlight = true
  try {
    const previousId = selectedTicket.value?.id
    await loadSupportTickets(true, { soft: true })
    if (previousId && !replyBody.value.trim()) {
      await openTicketDetail(previousId, { keepReply: true, soft: true })
    }
  } catch {
    // Keep the current UI if a quiet poll fails.
  } finally {
    supportPollingInFlight = false
  }
}

const stopSupportLive = () => {
  if (supportPollingTimer) {
    window.clearInterval(supportPollingTimer)
    supportPollingTimer = null
  }
  if (supportLiveRefreshTimer) {
    window.clearTimeout(supportLiveRefreshTimer)
    supportLiveRefreshTimer = null
  }
  supportLiveStream?.close()
  supportLiveStream = null
}

const startSupportLive = () => {
  stopSupportLive()
  supportLiveStream = createLiveEventSource(state.authToken)
  supportLiveStream?.addEventListener('open', refreshTicketsQuietly)
  supportLiveStream?.addEventListener('message', (event) => {
    const payload = parseLiveEvent(event.data)
    if (!payload?.type || !String(payload.type).startsWith('support.')) return
    if (supportLiveRefreshTimer) window.clearTimeout(supportLiveRefreshTimer)
    supportLiveRefreshTimer = window.setTimeout(refreshTicketsQuietly, 350)
  })
  supportPollingTimer = window.setInterval(refreshTicketsQuietly, 60000)
}

watch(activeStatusTab, async () => {
  await ensureActiveTicket()
})

watch(activeCategoryTab, async () => {
  await ensureActiveTicket()
})

watch(searchQuery, async () => {
  await ensureActiveTicket()
})

watch(() => ticketModal.category, (value) => {
  if (value === 'financial' && !ticketModal.context.payment_date) {
    ticketModal.context.payment_date = getTodayJalaliString()
  }
})

watch(
  () => conversationMessages.value.length,
  () => {
    void scrollMessagesToBottom()
  },
)

onMounted(async () => {
  if (state.currentUser.isHq) {
    await router.replace('/hq')
    return
  }

  startSupportLive()
  await loadSupportTickets(true)
  await ensureActiveTicket()

  if (route.query.prefill === 'wallet-card-payment') {
    openWalletPaymentTicketModal()
    router.replace({ path: route.path, query: {} })
  }
})

onBeforeUnmount(() => {
  stopSupportLive()
})
</script>

<template>
  <section class="page-shell support-page" dir="rtl">
    <header class="support-toolbar">
      <div class="support-title">
        <span class="title-icon">
          <IconlyIcon name="support_agent" decorative />
        </span>
        <div>
          <h2>پشتیبانی</h2>
        </div>
      </div>
      <div class="toolbar-actions">
        <label class="search-shell">
          <IconlyIcon name="search" decorative />
          <input v-model="searchQuery" type="search" placeholder="جستجو بر اساس شماره، عنوان یا متن..." />
        </label>
        <button type="button" class="primary-btn icon-label" @click="openCreateTicketModal">
          <IconlyIcon name="add" decorative />
          ثبت تیکت جدید
        </button>
      </div>
    </header>

    <section class="support-sla-banner">
      تیکت‌ها در تایم اداری حداکثر نیم ساعت و در تایم غیر اداری حداکثر ۲۴ ساعت پاسخ داده خواهند شد.
    </section>

    <div v-if="state.support.error || state.support.message" class="support-alert" :class="{ danger: state.support.error }">
      {{ state.support.error || state.support.message }}
    </div>

    <section class="stats-grid">
      <article
        v-for="item in statusTrack"
        :key="item.key"
        class="stat-card"
        :class="[statusClass(item.key), { active: activeStatusTab === item.key }]"
        role="button"
        tabindex="0"
        @click="activeStatusTab = item.key"
        @keydown.enter.prevent="activeStatusTab = item.key"
      >
        <div class="stat-icon">
          <IconlyIcon :name="item.icon" decorative />
        </div>
        <strong>{{ toFa(item.count) }}</strong>
        <span>{{ item.label }}</span>
        <small>{{ item.description }}</small>
      </article>
    </section>

    <section class="workspace-grid">
      <aside class="surface-card inbox-card">
        <header class="panel-head">
          <div>
            <p class="panel-kicker">Ticket Inbox</p>
            <div class="support-title-row">
              <h3>لیست تیکت‌های من</h3>
            </div>
            <span>{{ toFa(filteredTickets.length) }} مورد در وضعیت {{ activeStatusLabel }}</span>
          </div>
          <button type="button" class="mini-btn" @click="toggleStatusFilter">بعدی</button>
        </header>

        <div class="chip-row">
          <button
            v-for="item in categoryTabs"
            :key="item.key"
            type="button"
            class="chip-btn"
            :class="{ active: activeCategoryTab === item.key }"
            @click="activeCategoryTab = item.key"
          >
            {{ item.label }}
          </button>
        </div>

        <div class="inbox-summary-grid">
          <article class="summary-tile">
            <small>کارتابل · منتظر مجموعه</small>
            <strong>{{ toFa(waitingForUserCount) }}</strong>
          </article>
          <article class="summary-tile">
            <small>کارتابل · منتظر پشتیبان</small>
            <strong>{{ toFa(inProgressCount) }}</strong>
          </article>
        </div>

        <div v-if="state.support.loading && !tickets.length" class="empty-state compact">
          <IconlyIcon name="progress_activity" decorative />
          <h3>در حال بارگذاری</h3>
          <p>تیکت‌های شما در حال دریافت است...</p>
        </div>

        <div v-else-if="filteredTickets.length" class="ticket-list">
          <article
            v-for="ticket in filteredTickets"
            :key="ticket.id"
            class="ticket-row"
            :class="[statusClass(ticket.status), { selected: selectedTicket?.id === ticket.id }]"
            role="button"
            tabindex="0"
            @click="openTicketDetail(ticket.id)"
            @keydown.enter.prevent="openTicketDetail(ticket.id)"
            @keydown.space.prevent="openTicketDetail(ticket.id)"
          >
            <div class="ticket-row-meta ticket-row-meta-top">
              <span class="meta-pill mono">#{{ ticket.id }}</span>
              <span>{{ ticket.time || ticket.updatedAtIso }}</span>
            </div>
            <div class="ticket-row-top">
              <strong>{{ ticket.subject }}</strong>
              <span class="status-pill" :class="statusClass(ticket.status)">{{ clientStatusLabel(ticket) }}</span>
            </div>
            <p>{{ ticket.lastMessagePreview || ticket.message }}</p>
            <div class="ticket-row-tags">
              <span class="meta-pill">{{ ticket.categoryLabel || categoryLabel(ticket.category) }}</span>
              <span class="meta-pill">{{ ticket.priorityLabel || priorityLabel(ticket.priority) }}</span>
              <span>{{ toFa(ticket.messagesCount || 0) }} پیام</span>
            </div>
            <div class="ticket-row-meta">
              <span>{{ ticketLastResponder(ticket) }}</span>
            </div>
          </article>
        </div>

        <div v-else class="empty-state">
          <div class="empty-icon" aria-hidden="true">
            <IconlyIcon name="inbox" decorative />
          </div>
          <h3>تیکتی در این نما نیست</h3>
          <p>فیلتر وضعیت یا دسته‌بندی را تغییر دهید، یا یک تیکت تازه ثبت کنید.</p>
          <button type="button" class="primary-btn" @click="openCreateTicketModal">ثبت تیکت</button>
        </div>
      </aside>

      <section class="surface-card conversation-card">
        <div v-if="state.support.detailLoading && !selectedTicket" class="loading-state">
          <IconlyIcon name="progress_activity" decorative />
          در حال بارگذاری گفتگو...
        </div>

        <template v-else-if="selectedTicket">
          <header class="conversation-head">
            <div class="conversation-copy">
              <span class="panel-kicker">Conversation</span>
              <div class="conversation-title">
                <h3>{{ selectedTicket.subject }}</h3>
                <span class="status-pill" :class="statusClass(selectedTicket.status)">
                  {{ clientStatusLabel(selectedTicket) }}
                </span>
              </div>
              <p>{{ selectedTicket.message }}</p>
            </div>

            <div class="conversation-tags">
              <span class="meta-pill">{{ selectedTicket.categoryLabel || categoryLabel(selectedTicket.category) }}</span>
              <span class="meta-pill">{{ selectedTicket.priorityLabel || priorityLabel(selectedTicket.priority) }}</span>
              <span class="meta-pill mono">#{{ selectedTicket.id }}</span>
            </div>
          </header>

          <section v-if="selectedTicket.attachments?.length" class="ticket-attachments-shell">
            <div class="reply-head">
              <strong>فایل‌های پیوست</strong>
              <small>{{ toFa(selectedTicket.attachments.length) }} فایل</small>
            </div>
            <div class="ticket-attachments-list">
              <button
                v-for="attachment in selectedTicket.attachments"
                :key="attachment.id"
                type="button"
                class="ticket-attachment-item"
                @click="openProtectedFile(attachment.fileUrl, attachment.originalName)"
              >
                <IconlyIcon name="attach_file" decorative />
                <strong>{{ attachment.originalName || 'فایل پیوست' }}</strong>
                <span>مشاهده فایل</span>
              </button>
            </div>
          </section>

          <section ref="messageThreadRef" class="message-thread" aria-live="polite">
            <article
              v-for="message in conversationMessages"
              :key="message.id"
              class="message-row"
              :class="messageAlignmentClass(message)"
            >
              <div class="message-bubble" :class="messageAlignmentClass(message)">
                <div class="message-meta">
                  <span class="sender-tag" :class="messageAlignmentClass(message)">
                    {{ messageRoleLabel(message) }}
                  </span>
                  <small>{{ message.time || message.createdAtIso }}</small>
                </div>
                <p>{{ message.body }}</p>
              </div>
            </article>
            <div v-if="!conversationMessages.length" class="thread-empty">
              <IconlyIcon name="forum" decorative />
              <small>پیامی برای نمایش وجود ندارد</small>
            </div>
          </section>

          <section class="reply-shell">
            <div class="reply-head">
              <strong>ارسال پاسخ</strong>
              <small v-if="selectedTicket.status === 'closed'">این تیکت بسته شده و فقط برای مشاهده است.</small>
              <small v-else>پاسخ کوتاه و شفاف بنویسید. با Ctrl + Enter هم ارسال می‌شود.</small>
            </div>

            <div v-if="selectedTicket.status !== 'closed'" class="reply-form">
              <textarea
                v-model.trim="replyBody"
                :disabled="sendingReply || state.support.submitting"
                rows="4"
                placeholder="پاسخ تکمیلی خود را بنویسید..."
                @keydown.ctrl.enter.prevent="submitReply"
              />
              <div class="reply-actions">
                <span class="hint">{{ toFa(replyBody.length) }} کاراکتر</span>
                <button
                  type="button"
                  class="primary-btn icon-label"
                  :disabled="sendingReply || state.support.submitting || !replyBody"
                  @click="submitReply"
                >
                  <IconlyIcon name="send" decorative />
                  {{ sendingReply || state.support.submitting ? 'در حال ارسال...' : 'ارسال پیام' }}
                </button>
              </div>
            </div>

            <div v-else class="closed-note">
              <span class="status-pill closed">تیکت بسته شده</span>
              <p>اگر هنوز مشکل باقی است، یک تیکت جدید با ارجاع به شماره همین تیکت ثبت کنید.</p>
            </div>
          </section>

          <section v-if="canRateTicket(selectedTicket) || selectedTicket.customerSatisfaction" class="feedback-shell">
            <div class="reply-head">
              <strong>نظر شما درباره این تیکت</strong>
              <small v-if="canRateTicket(selectedTicket)">تجربه رسیدگی را ثبت کنید تا کیفیت پشتیبانی بهتر شود.</small>
              <small v-else>نظر شما قبلا برای این تیکت ثبت شده است.</small>
            </div>

            <template v-if="canRateTicket(selectedTicket)">
              <div class="rating-stars">
                <button
                  v-for="score in 5"
                  :key="score"
                  type="button"
                  class="rating-star-btn"
                  :class="{ active: feedback.score >= score }"
                  @click="feedback.score = score"
                >
                  ★
                </button>
              </div>
              <textarea
                v-model.trim="feedback.text"
                rows="3"
                placeholder="اگر خواستید، خیلی کوتاه تجربه خود از رسیدگی این تیکت را بنویسید..."
              />
              <div class="reply-actions">
                <span class="hint">امتیاز شما برای ارزیابی کیفیت پشتیبانی استفاده می‌شود.</span>
                <button
                  type="button"
                  class="primary-btn"
                  :disabled="!feedback.score || state.support.submitting"
                  @click="submitTicketFeedback"
                >
                  ثبت نظر
                </button>
              </div>
            </template>

            <div v-else class="feedback-static">
              <div class="feedback-score">{{ satisfactionLabel(selectedTicket.customerSatisfaction) }}</div>
              <p v-if="selectedTicket.customerFeedback">{{ selectedTicket.customerFeedback }}</p>
              <p v-else>برای این تیکت امتیاز ثبت شده است.</p>
            </div>
          </section>
        </template>

        <div v-else class="empty-state conversation-empty">
          <div class="empty-icon" aria-hidden="true">
            <IconlyIcon name="chat" decorative />
          </div>
          <h3>یک تیکت را انتخاب کنید</h3>
          <p>برای دیدن جزئیات کامل، پاسخ‌های پشتیبانی و ادامه گفتگو، از ستون لیست یک تیکت را باز کنید.</p>
        </div>
      </section>
    </section>

    <div v-if="ticketModal.open" class="modal-overlay" @click.self="closeCreateTicketModal">
      <section class="modal-panel">
        <header class="modal-head">
          <div>
            <span class="panel-kicker">New Ticket</span>
            <h3>ثبت تیکت جدید</h3>
            <p>درخواست را دقیق ثبت کنید تا سریع‌تر به واحد درست ارجاع شود.</p>
          </div>
          <button type="button" class="close-btn" aria-label="بستن" @click="closeCreateTicketModal">×</button>
        </header>

        <div class="modal-layout">
          <form class="modal-form" @submit.prevent="submitTicket">
            <div v-if="isWalletCardPaymentDraft" class="wallet-ticket-notice full">
              <strong>ثبت آماده برای واریز کیف پول</strong>
              <p>{{ walletCardPaymentNotice }}</p>
            </div>

            <label>
              <span>دسته‌بندی</span>
              <select v-model="ticketModal.category" :disabled="isWalletCardPaymentDraft">
                <option value="technical">مشکل فنی</option>
                <option value="financial">مشکل پرداخت</option>
                <option value="operations">سفارش و عملیات</option>
                <option value="account">حساب کاربری</option>
                <option value="other">سایر</option>
              </select>
            </label>

            <label class="full">
              <span>اولویت</span>
              <select v-model="ticketModal.priority" :disabled="isWalletCardPaymentDraft">
                <option v-for="item in priorities" :key="item.key" :value="item.key">{{ item.label }}</option>
              </select>
            </label>

            <label class="full">
              <span>عنوان تیکت</span>
              <input
                v-model.trim="ticketModal.subject"
                :readonly="isWalletCardPaymentDraft"
                required
                placeholder="مثلا: پرداخت انجام شد ولی وضعیت به‌روز نشد"
              />
            </label>

            <label class="full">
              <span>{{ isWalletCardPaymentDraft ? 'شرح آماده + تکمیل اطلاعات تراکنش' : 'شرح کامل' }}</span>
              <textarea
                v-model.trim="ticketModal.description"
                rows="5"
                required
                :placeholder="isWalletCardPaymentDraft
                  ? 'متن آماده را نگه دارید و فقط اطلاعات تراکنش یا توضیح رسید را تکمیل کنید...'
                  : 'زمان رخداد، نتیجه مورد انتظار، خطا یا جزئیات مرتبط را کامل بنویسید...'"
              />
            </label>

            <template v-if="ticketModal.category === 'financial'">
              <label>
                <span>شماره تراکنش</span>
                <input v-model.trim="ticketModal.context.transaction_id" placeholder="مثلا 9854123" />
              </label>
              <label>
                <span>مبلغ پرداخت</span>
                <input v-model.trim="ticketModal.context.payment_amount" placeholder="مثلا 250000" />
              </label>
              <label class="full">
                <span>تاریخ پرداخت</span>
                <ShamsiDatePicker v-model="ticketModal.context.payment_date" model-type="jalali" placeholder="انتخاب تاریخ پرداخت" />
              </label>
            </template>

            <template v-else-if="ticketModal.category === 'operations'">
              <label class="full">
                <span>خدمت یا سرویس</span>
                <input v-model.trim="ticketModal.context.service_name" placeholder="مثلا ثبت درخواست یا تایید هزینه" />
              </label>
            </template>

            <template v-else-if="ticketModal.category === 'technical'">
              <label>
                <span>نوع دستگاه</span>
                <input v-model.trim="ticketModal.context.device_type" placeholder="مثلا لپ‌تاپ ویندوز" />
              </label>
              <label>
                <span>مرورگر / اپ</span>
                <input v-model.trim="ticketModal.context.browser_name" placeholder="مثلا Chrome 136" />
              </label>
              <label class="full">
                <span>سیستم‌عامل</span>
                <input v-model.trim="ticketModal.context.os_name" placeholder="مثلا Windows 11" />
              </label>
            </template>

            <template v-else-if="ticketModal.category === 'account'">
              <label>
                <span>موبایل حساب</span>
                <input v-model.trim="ticketModal.context.account_phone" placeholder="09xxxxxxxxx" />
              </label>
              <label>
                <span>موضوع حساب</span>
                <input v-model.trim="ticketModal.context.account_issue" placeholder="مثلا ورود یا تغییر شماره" />
              </label>
            </template>

            <div class="form-note full">
              <strong>{{ isWalletCardPaymentDraft ? 'راهنمای ثبت پرداخت' : 'نکته امنیتی' }}</strong>
              <p>
                {{ isWalletCardPaymentDraft
                  ? 'اگر امکان ارسال رسید در همین تیکت را دارید، تصویر رسید را هم اضافه کنید. در غیر این صورت شماره تراکنش، مبلغ و زمان پرداخت را کامل بنویسید و ساختار آماده را تغییر ندهید.'
                  : 'رمز عبور، اطلاعات کامل کارت بانکی یا کدهای امنیتی را داخل تیکت ارسال نکنید.' }}
              </p>
            </div>

            <label class="full receipt-upload-field">
              <span>{{ ticketModal.category === 'financial' ? 'آپلود رسید / پیوست' : 'پیوست' }}</span>
              <input
                type="file"
                multiple
                accept=".jpg,.jpeg,.png,.webp,.pdf,image/*,application/pdf"
                :disabled="state.support.submitting || attachmentPreparing"
                @change="handleAttachmentChange"
              />
              <small v-if="attachmentPreparing" class="receipt-file-name">در حال آماده‌سازی فایل...</small>
              <small v-else-if="selectedAttachmentNames" class="receipt-file-name">{{ selectedAttachmentNames }}</small>
              <small v-if="ticketModal.attachments.length" class="receipt-file-name">
                {{ ticketModal.attachments.map((file) => formatFileSize(file.size)).join(' • ') }}
              </small>
              <small v-if="attachmentError" class="receipt-upload-error">{{ attachmentError }}</small>
            </label>

            <div class="modal-actions full">
              <button type="button" class="secondary-btn" @click="closeCreateTicketModal">انصراف</button>
              <button type="submit" class="primary-btn" :disabled="state.support.submitting || attachmentPreparing">
                {{ state.support.submitting ? 'در حال ثبت...' : 'ثبت تیکت' }}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.support-page {
  --jade: #34908B;
  --jade-deep: #2b7874;
  --jade-soft: rgba(52, 144, 139, 0.12);
  --ink: #1f2a37;
  --muted: #667085;
  --line: rgba(52, 144, 139, 0.16);
  --surface: rgba(255, 255, 255, 0.88);
  --soft: #f4faf9;
  display: grid;
  gap: 18px;
}

.support-toolbar,
.panel-head,
.chip-row,
.ticket-row-top,
.ticket-row-meta,
.conversation-title,
.conversation-tags,
.reply-actions,
.message-meta,
.modal-actions,
.toolbar-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.support-toolbar {
  padding: 18px 20px;
  border-radius: 24px;
  border: 1px solid var(--line);
  background:
    radial-gradient(circle at top left, rgba(52, 144, 139, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(244, 250, 249, 0.94));
  box-shadow: 0 18px 42px rgba(31, 42, 55, 0.05);
}

.support-title {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.support-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.support-title-row h2,
.support-title-row h3 {
  margin: 0;
  min-width: 0;
}

.title-icon {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(135deg, var(--jade), var(--jade-deep));
  box-shadow: 0 14px 28px rgba(52, 144, 139, 0.28);
}

.support-title h2,
.panel-head h3,
.conversation-title h3,
.modal-head h3,
.empty-state h3 {
  margin: 0;
  color: var(--ink);
}

.support-title h2 {
  font-size: 1.25rem;
}

.support-title p,
.ticket-row p,
.conversation-copy p,
.empty-state p,
.modal-head p,
.form-note p,
.feedback-static p,
.closed-note p,
.support-alert {
  margin: 0;
  color: var(--muted);
  line-height: 1.9;
}

.toolbar-actions {
  justify-content: flex-end;
  flex: 1 1 auto;
}

.search-shell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: min(320px, 100%);
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.92);
}

.search-shell input {
  width: 100%;
  min-height: 44px;
  border: 0;
  background: transparent;
  font: inherit;
  color: var(--ink);
  outline: none;
}

.primary-btn,
.secondary-btn,
.mini-btn,
.chip-btn,
.rating-star-btn,
.close-btn,
.ticket-attachment-item {
  border: 0;
  cursor: pointer;
  font: inherit;
}

.primary-btn,
.secondary-btn,
.mini-btn {
  min-height: 44px;
  border-radius: 14px;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 800;
}

.primary-btn {
  color: #fff;
  background: linear-gradient(135deg, var(--jade), var(--jade-deep));
  box-shadow: 0 16px 32px rgba(52, 144, 139, 0.24);
}

.primary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.secondary-btn,
.mini-btn {
  color: var(--ink);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
}

.icon-label .iconly-shell {
  font-size: 1.1rem;
}

.support-sla-banner {
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(52, 144, 139, 0.22);
  background: linear-gradient(135deg, #ffffff, #eef8f7);
  color: var(--jade-deep);
  font-weight: 800;
  line-height: 1.9;
  box-shadow: 0 12px 28px rgba(52, 144, 139, 0.08);
}

.support-alert {
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--jade-soft);
  color: var(--jade-deep);
  font-weight: 800;
}

.support-alert.danger {
  background: #fef3f2;
  color: #b42318;
}

.stats-grid,
.workspace-grid,
.inbox-summary-grid,
.modal-form,
.ticket-list,
.message-thread {
  display: grid;
  gap: 14px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stat-card {
  display: grid;
  gap: 6px;
  min-height: 132px;
  padding: 16px;
  border-radius: 22px;
  border: 1px solid var(--line);
  background: var(--surface);
  backdrop-filter: blur(10px);
  box-shadow: 0 14px 32px rgba(31, 42, 55, 0.04);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.stat-card:hover,
.stat-card.active {
  transform: translateY(-2px);
  box-shadow: 0 22px 40px rgba(52, 144, 139, 0.12);
}

.stat-card.open.active { background: linear-gradient(180deg, rgba(219, 234, 254, 0.72), rgba(255, 255, 255, 0.96)); }
.stat-card.pending.active { background: linear-gradient(180deg, rgba(254, 243, 199, 0.78), rgba(255, 255, 255, 0.96)); }
.stat-card.answered.active { background: linear-gradient(180deg, rgba(209, 250, 229, 0.78), rgba(255, 255, 255, 0.96)); }
.stat-card.closed.active { background: linear-gradient(180deg, rgba(226, 232, 240, 0.78), rgba(255, 255, 255, 0.96)); }

.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--jade-deep);
  background: var(--jade-soft);
}

.stat-card strong {
  color: var(--ink);
  font-size: 1.45rem;
}

.stat-card span {
  color: var(--ink);
  font-weight: 800;
}

.stat-card small,
.panel-head span,
.summary-tile small,
.modal-form label span,
.hint {
  color: var(--muted);
  font-size: 12px;
}

.workspace-grid {
  grid-template-columns: minmax(320px, 390px) minmax(0, 1fr);
  align-items: start;
}

.surface-card,
.modal-panel {
  border-radius: 24px;
  border: 1px solid var(--line);
  background:
    radial-gradient(circle at top right, rgba(52, 144, 139, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 250, 249, 0.96));
  box-shadow: 0 18px 42px rgba(31, 42, 55, 0.055);
  backdrop-filter: blur(12px);
}

.inbox-card,
.conversation-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  min-width: 0;
}

.panel-kicker {
  display: inline-flex;
  width: fit-content;
  margin: 0 0 6px;
  padding: 7px 11px;
  border-radius: 999px;
  background: var(--jade-soft);
  color: var(--jade-deep);
  font-size: 11px;
  font-weight: 800;
}

.chip-row {
  justify-content: flex-start;
  gap: 8px;
  overflow-x: auto;
  flex-wrap: nowrap;
  scrollbar-width: none;
}

.chip-row::-webkit-scrollbar {
  display: none;
}

.chip-btn {
  flex: 0 0 auto;
  min-height: 40px;
  border-radius: 999px;
  padding: 8px 13px;
  background: #eef4f3;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.chip-btn.active {
  color: #fff;
  background: linear-gradient(135deg, var(--jade), var(--jade-deep));
}

.inbox-summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-tile,
.reply-shell,
.feedback-shell,
.ticket-attachments-shell {
  border-radius: 18px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.9);
  padding: 14px 16px;
}

.summary-tile {
  display: grid;
  gap: 6px;
}

.summary-tile strong {
  color: var(--ink);
  font-size: 1.25rem;
}

.ticket-list,
.message-thread {
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
}

.ticket-list {
  max-height: calc(100vh - 380px);
  align-content: start;
}

.ticket-row {
  position: relative;
  display: grid;
  gap: 10px;
  padding: 16px;
  overflow: hidden;
  border-radius: 18px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  background: linear-gradient(180deg, #ffffff, #f7fcfb);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.ticket-row::before {
  content: "";
  position: absolute;
  inset-block: 14px;
  inset-inline-start: 0;
  width: 4px;
  border-radius: 999px;
  background: var(--jade);
}

.ticket-row.pending::before { background: #d97706; }
.ticket-row.answered::before { background: #16a34a; }
.ticket-row.closed::before { background: #64748b; }

.ticket-row:hover,
.ticket-row.selected {
  transform: translateY(-1px);
  border-color: rgba(52, 144, 139, 0.38);
  box-shadow: 0 18px 34px rgba(52, 144, 139, 0.12);
}

.ticket-row.selected {
  background: linear-gradient(135deg, rgba(236, 250, 248, 0.98), rgba(255, 255, 255, 0.98));
}

.ticket-row-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.ticket-row-top strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.55;
}

.ticket-row p {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}

.ticket-row-tags,
.conversation-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-pill,
.meta-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

.meta-pill {
  background: #eef6f5;
  color: #3d6670;
}

.status-pill.open {
  background: #e8f1ff;
  color: #1d4ed8;
}

.status-pill.pending {
  background: #fef3c7;
  color: #b45309;
}

.status-pill.answered {
  background: #dcfce7;
  color: #166534;
}

.status-pill.closed {
  background: #f1f5f9;
  color: #475569;
}

.conversation-card {
  position: sticky;
  top: 18px;
  max-height: calc(100dvh - 148px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.conversation-card > * {
  min-width: 0;
}

.conversation-head {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(52, 144, 139, 0.12);
}

.conversation-copy {
  display: grid;
  gap: 10px;
}

.ticket-attachments-shell {
  display: grid;
  gap: 12px;
}

.ticket-attachments-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}

.ticket-attachment-item {
  display: grid;
  gap: 4px;
  justify-items: start;
  padding: 14px 16px;
  border-radius: 18px;
  text-align: start;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.98), rgba(236, 250, 248, 0.98));
  border: 1px solid rgba(52, 144, 139, 0.18);
  color: var(--ink);
}

.ticket-attachment-item span {
  color: var(--jade-deep);
  font-size: 12px;
  font-weight: 700;
}

.message-thread {
  flex: 1 1 auto;
  min-height: 280px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: linear-gradient(180deg, rgba(244, 250, 249, 0.94), rgba(255, 255, 255, 0.98));
}

.message-row {
  display: flex;
}

.message-row.support {
  justify-content: flex-start;
}

.message-row.tenant {
  justify-content: flex-end;
}

.message-bubble {
  width: min(74%, 640px);
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 18px;
  box-shadow: 0 12px 28px rgba(31, 42, 55, 0.05);
}

.message-bubble.support {
  background: #fff;
  border-top-right-radius: 8px;
}

.message-bubble.tenant {
  color: #fff;
  background: linear-gradient(135deg, var(--jade), var(--jade-deep));
  border-top-left-radius: 8px;
}

.sender-tag {
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}

.sender-tag.support {
  background: var(--jade-soft);
  color: var(--jade-deep);
}

.sender-tag.tenant {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

.message-bubble p {
  margin: 0;
  line-height: 1.95;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.message-meta small {
  color: inherit;
  opacity: 0.75;
}

.reply-shell,
.feedback-shell {
  flex: 0 0 auto;
  display: grid;
  gap: 12px;
}

.reply-head {
  display: grid;
  gap: 6px;
}

.reply-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(132px, auto);
  gap: 10px;
  align-items: end;
}

.reply-form textarea,
.feedback-shell textarea,
.modal-form input,
.modal-form textarea,
.modal-form select,
.search-shell input {
  font: inherit;
}

.reply-form textarea,
.feedback-shell textarea,
.modal-form input,
.modal-form textarea,
.modal-form select {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid rgba(52, 144, 139, 0.18);
  border-radius: 14px;
  padding: 11px 13px;
  background: #fff;
  color: var(--ink);
  resize: vertical;
}

.reply-form textarea {
  min-height: 54px;
  max-height: 96px;
  resize: none;
}

.reply-form textarea:focus,
.feedback-shell textarea:focus,
.modal-form input:focus,
.modal-form textarea:focus,
.modal-form select:focus,
.search-shell:focus-within {
  outline: none;
  border-color: var(--jade);
  box-shadow: 0 0 0 4px rgba(52, 144, 139, 0.12);
}

.modal-form input[readonly],
.modal-form select:disabled {
  opacity: 0.78;
  cursor: not-allowed;
  background: #f3f6f6;
  color: var(--muted);
}

.reply-actions {
  align-items: end;
  justify-content: flex-end;
}

.closed-note,
.feedback-static {
  display: grid;
  gap: 8px;
}

.rating-stars {
  display: flex;
  gap: 8px;
}

.rating-star-btn {
  background: transparent;
  color: #cbd5e1;
  font-size: 30px;
  padding: 0;
  line-height: 1;
}

.rating-star-btn.active {
  color: #f59e0b;
}

.feedback-score {
  color: var(--ink);
  font-size: 22px;
  font-weight: 800;
}

.empty-state,
.loading-state,
.thread-empty {
  min-height: 240px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  text-align: center;
  color: var(--muted);
}

.conversation-empty {
  min-height: 100%;
}

.empty-icon,
.loading-state .iconly-shell,
.empty-state .iconly-shell,
.thread-empty .iconly-shell {
  font-size: 2.8rem;
  color: var(--jade);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(15, 36, 34, 0.42);
  backdrop-filter: blur(8px);
  overflow: auto;
}

.modal-panel {
  width: min(980px, 100%);
  max-height: min(86vh, 820px);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  overflow: hidden;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 16px 20px 14px;
  border-bottom: 1px solid rgba(52, 144, 139, 0.12);
}

.close-btn {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: var(--jade-soft);
  color: var(--jade-deep);
  font-size: 28px;
}

.modal-layout {
  padding: 16px 20px 20px;
  overflow: auto;
}

.modal-form {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.modal-form label {
  display: grid;
  gap: 8px;
}

.modal-form .full {
  grid-column: 1 / -1;
}

.form-note {
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(254, 242, 242, 0.96);
  border: 1px solid rgba(254, 202, 202, 0.8);
  display: grid;
  gap: 4px;
}

.wallet-ticket-notice {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(236, 250, 248, 0.96), rgba(255, 255, 255, 0.98));
  border: 1px solid rgba(52, 144, 139, 0.28);
}

.wallet-ticket-notice strong {
  color: var(--jade-deep);
}

.receipt-upload-field input[type="file"] {
  padding: 12px;
  border: 1px dashed rgba(52, 144, 139, 0.34);
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(236, 250, 248, 0.96), rgba(255, 255, 255, 0.98));
}

.receipt-file-name {
  color: var(--jade-deep);
  font-weight: 700;
}

.receipt-upload-error {
  color: #b42318;
  font-weight: 700;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-weight: 700;
}

@media (max-width: 1180px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .conversation-card {
    position: static;
    max-height: none;
  }

  .message-thread {
    max-height: 56dvh;
  }
}

@media (max-width: 760px) {
  .support-page {
    gap: 12px;
  }

  .support-toolbar,
  .inbox-card,
  .conversation-card,
  .modal-layout {
    padding: 14px;
  }

  .support-toolbar,
  .toolbar-actions,
  .panel-head,
  .ticket-row-top,
  .ticket-row-meta,
  .conversation-title,
  .conversation-tags,
  .reply-actions,
  .message-meta,
  .modal-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .stats-grid {
    display: flex;
    overflow-x: auto;
    gap: 10px;
    padding-bottom: 6px;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
  }

  .stats-grid::-webkit-scrollbar {
    display: none;
  }

  .stat-card {
    min-width: 148px;
    min-height: 118px;
    scroll-snap-align: start;
  }

  .ticket-list {
    max-height: none;
  }

  .ticket-row-top {
    grid-template-columns: 1fr;
  }

  .message-bubble {
    width: 100%;
  }

  .reply-form,
  .modal-form {
    grid-template-columns: 1fr;
  }

  .reply-actions .primary-btn {
    width: 100%;
  }

  .modal-overlay {
    padding: 0;
    place-items: end center;
  }

  .modal-panel {
    width: 100%;
    max-height: 92dvh;
    border-radius: 24px 24px 0 0;
  }

  .reply-form textarea,
  .modal-form input,
  .modal-form textarea,
  .modal-form select {
    font-size: 16px;
  }
}
</style>
