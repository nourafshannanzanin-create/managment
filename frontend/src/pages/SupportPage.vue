<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'

import { formatAmountInput } from '../utils/amount'
import { useWorkflowHub } from '../stores/workflowHub'

const PAYMENT_TICKET_SUBJECT = 'درخواست شارژ کیف پول'

const {
  state,
  loadSupportTickets,
  loadSupportTicketDetail,
  createSupportTicket,
  submitSupportReply,
  submitSupportFeedback,
  submitSupportWalletDeposit,
  submitSupportBankWithdrawComplete,
  submitSupportRegistrationApproval,
  markSupportTicketsSeen,
  openProtectedFile,
} = useWorkflowHub()

const activeStatus = ref('all')
const activeCategory = ref('all')
const query = ref('')
const modalOpen = ref(false)
const walletDepositModalOpen = ref(false)
const bankWithdrawModalOpen = ref(false)
const registrationModalOpen = ref(false)
const replyBody = ref('')
const threadRef = ref(null)
const feedback = reactive({ score: 0, text: '' })
const walletDepositForm = reactive({ amount: '' })
const bankWithdrawForm = reactive({ amount: '' })
const registrationForm = reactive({ companyCode: '' })
const form = reactive({
  subject: '',
  message: '',
  category: 'technical',
  priority: 'medium',
  attachments: [],
})

const tickets = computed(() => state.support.tickets || [])
const selectedTicket = computed(() => state.support.selectedTicket)
const canCloseTicket = computed(() => state.currentUser.canUseHq)

const statusCounts = computed(() => tickets.value.reduce((acc, item) => {
  acc[item.status] = (acc[item.status] || 0) + 1
  return acc
}, { open: 0, pending: 0, answered: 0, closed: 0 }))

const activeTicketCount = computed(() => (statusCounts.value.open || 0) + (statusCounts.value.pending || 0) + (statusCounts.value.answered || 0))

const statusTabs = computed(() => [
  { key: 'all', label: 'همه', icon: 'inbox', count: activeTicketCount.value },
  { key: 'open', label: 'باز', icon: 'radio_button_checked', count: statusCounts.value.open || 0 },
  { key: 'pending', label: 'در حال بررسی', icon: 'hourglass_top', count: statusCounts.value.pending || 0 },
  { key: 'answered', label: 'پاسخ داده شده', icon: 'mark_chat_read', count: statusCounts.value.answered || 0 },
  { key: 'closed', label: 'بسته شده', icon: 'task_alt', count: statusCounts.value.closed || 0 },
])

const categories = [
  { key: 'all', label: 'همه' },
  { key: 'technical', label: 'فنی' },
  { key: 'financial', label: 'مالی' },
  { key: 'operations', label: 'عملیات' },
  { key: 'account', label: 'حساب' },
  { key: 'other', label: 'سایر' },
]

const priorities = [
  { key: 'low', label: 'کم' },
  { key: 'medium', label: 'متوسط' },
  { key: 'high', label: 'زیاد' },
  { key: 'urgent', label: 'فوری' },
]

function paymentTicketRank(ticket) {
  return ticket?.category === 'financial' && ticket?.priority === 'urgent' && ticket?.subject === PAYMENT_TICKET_SUBJECT ? 0 : 1
}

const canDepositToWallet = computed(() => state.currentUser.canUseHq && paymentTicketRank(selectedTicket.value) === 0)
const canCompleteWalletTransfer = computed(() => state.currentUser.canUseHq && selectedTicket.value?.actionMeta?.actionType === 'wallet_withdrawal' && selectedTicket.value?.actionMeta?.destinationType === 'wallet')
const canCompleteBankWithdraw = computed(() => state.currentUser.canUseHq && selectedTicket.value?.actionMeta?.actionType === 'wallet_withdrawal' && selectedTicket.value?.actionMeta?.destinationType === 'bank')
const isRegistrationTicket = computed(() => selectedTicket.value?.actionMeta?.actionType === 'organization_registration')
const canApproveRegistration = computed(() => state.currentUser.canUseHq && isRegistrationTicket.value && selectedTicket.value?.actionMeta?.canApprove)

const filteredTickets = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return tickets.value.filter((ticket) => {
    if (activeStatus.value === 'all') {
      if (!['open', 'pending', 'answered'].includes(ticket.status)) return false
    } else if (ticket.status !== activeStatus.value) {
      return false
    }
    if (activeCategory.value !== 'all' && ticket.category !== activeCategory.value) return false
    if (!needle) return true
    return `${ticket.id} ${ticket.subject} ${ticket.message} ${ticket.categoryLabel} ${ticket.organization} ${ticket.lastMessagePreview}`.toLowerCase().includes(needle)
  }).sort((a, b) => {
    const rankDiff = paymentTicketRank(a) - paymentTicketRank(b)
    if (rankDiff !== 0) return rankDiff
    return new Date(b.updatedAt) - new Date(a.updatedAt)
  })
})

const conversationMessages = computed(() => {
  const ticket = selectedTicket.value
  if (!ticket) return []

  const messages = Array.isArray(ticket.messages) ? ticket.messages.filter((message) => message?.body) : []
  const normalizedMessages = messages.map((message, index) => ({
    ...message,
    id: message.id ?? `message-${index}`,
    sender: message.sender || ticket.requester || ticket.organization || 'کاربر',
    createdAt: message.createdAt || message.created_at || ticket.createdAt || ticket.updatedAt || '',
    time: message.time || message.createdAtIso || ticket.time || '',
  }))

  if (normalizedMessages.length) {
    return normalizedMessages.sort((a, b) => new Date(a.createdAt || 0) - new Date(b.createdAt || 0))
  }

  if (!ticket.message) return []
  return [{
    id: `ticket-${ticket.id}-initial`,
    sender: ticket.requester || ticket.organization || 'کاربر',
    senderPlatformRole: 'tenant',
    body: ticket.message,
    createdAt: ticket.createdAt || ticket.updatedAt || '',
    time: ticket.createdAtIso || ticket.time || '',
    isFallback: true,
  }]
})

const selectedTicketSubtitle = computed(() => {
  if (!selectedTicket.value) return ''
  const parts = [
    selectedTicket.value.organization,
    selectedTicket.value.requester,
    selectedTicket.value.updatedAtIso || selectedTicket.value.time,
  ].filter(Boolean)
  return parts.join(' / ')
})

function statusClass(status) {
  return {
    all: 'all',
    open: 'open',
    pending: 'pending',
    answered: 'answered',
    closed: 'closed',
  }[status] || 'open'
}

function messageClass(message) {
  const isSupportMessage = message?.senderPlatformRole === 'hq_support'
  const isMine = state.currentUser.isHq ? isSupportMessage : !isSupportMessage
  return isMine ? 'outgoing' : 'incoming'
}

function messageRoleLabel(message) {
  return message?.senderPlatformRole === 'hq_support' ? 'پشتیبانی' : 'کاربر'
}

async function scrollThreadToBottom() {
  await nextTick()
  if (!threadRef.value) return
  threadRef.value.scrollTop = threadRef.value.scrollHeight
}

function resetForm() {
  form.subject = ''
  form.message = ''
  form.category = 'technical'
  form.priority = 'medium'
  form.attachments = []
}

function setFiles(event) {
  form.attachments = Array.from(event.target.files || [])
}

function markCurrentAnsweredTicketsSeen() {
  const answeredIds = (tickets.value || []).filter((ticket) => ticket.status === 'answered').map((ticket) => ticket.id)
  if (answeredIds.length) {
    markSupportTicketsSeen(answeredIds)
  }
}

async function openTicket(ticketId) {
  await loadSupportTicketDetail(ticketId)
  replyBody.value = ''
  feedback.score = 0
  feedback.text = ''
  if (selectedTicket.value?.status === 'answered') {
    markSupportTicketsSeen([selectedTicket.value.id])
  }
  await scrollThreadToBottom()
}

async function submitTicket() {
  await createSupportTicket({ ...form })
  modalOpen.value = false
  resetForm()
}

async function sendReply(close = false) {
  if (!selectedTicket.value?.id) return
  await submitSupportReply(selectedTicket.value.id, { body: replyBody.value, close })
  replyBody.value = ''
  await scrollThreadToBottom()
}

async function sendFeedback() {
  if (!selectedTicket.value?.id || !feedback.score) return
  await submitSupportFeedback(selectedTicket.value.id, { score: feedback.score, feedback: feedback.text })
}

function openWalletDepositModal() {
  walletDepositForm.amount = selectedTicket.value?.actionMeta?.amount || ''
  walletDepositModalOpen.value = true
}

function openBankWithdrawModal() {
  bankWithdrawForm.amount = selectedTicket.value?.actionMeta?.amount || ''
  bankWithdrawModalOpen.value = true
}

async function submitWalletDeposit() {
  if (!selectedTicket.value?.id) return
  await submitSupportWalletDeposit(selectedTicket.value.id, { amount: walletDepositForm.amount })
  walletDepositModalOpen.value = false
  walletDepositForm.amount = ''
}

async function submitBankWithdraw() {
  if (!selectedTicket.value?.id) return
  await submitSupportBankWithdrawComplete(selectedTicket.value.id, { amount: bankWithdrawForm.amount })
  bankWithdrawModalOpen.value = false
  bankWithdrawForm.amount = ''
}

function openRegistrationModal() {
  registrationForm.companyCode = ''
  registrationModalOpen.value = true
}

async function approveRegistration() {
  if (!selectedTicket.value?.id) return
  const ok = await submitSupportRegistrationApproval(selectedTicket.value.id, registrationForm.companyCode)
  if (ok) registrationModalOpen.value = false
}

async function hydrateSupportWorkspace() {
  await loadSupportTickets(true)
  markCurrentAnsweredTicketsSeen()
  if (filteredTickets.value[0]) {
    await openTicket(filteredTickets.value[0].id)
  }
}

onMounted(async () => {
  await hydrateSupportWorkspace()
})

watch(
  () => state.hq.selectedOrganizationId,
  async () => {
    if (!state.currentUser.isHq) return
    await hydrateSupportWorkspace()
  },
)

watch(
  () => conversationMessages.value.length,
  () => {
    void scrollThreadToBottom()
  },
)
</script>

<template>
  <section class="support-page">
    <section class="support-hero" aria-label="پشتیبانی">
      <div class="support-title">
        <IconlyIcon name="support_agent" decorative />
        <div>
          <h2>پشتیبانی</h2>
          <small>{{ filteredTickets.length }} مکالمه</small>
        </div>
      </div>
      <div class="support-hero-actions">
        <button
          v-for="item in statusTabs"
          :key="item.key"
          :class="['support-status-card', statusClass(item.key), activeStatus === item.key && 'is-active']"
          type="button"
          @click="activeStatus = item.key"
        >
          <IconlyIcon :name="item.icon" decorative />
          <span>{{ item.label }}</span>
          <b>{{ item.count }}</b>
        </button>
      </div>
      <button class="support-primary icon-label" type="button" @click="modalOpen = true">
        <IconlyIcon name="add" decorative />
        تیکت جدید
      </button>
    </section>

    <div v-if="state.support.error || state.support.message" class="support-alert" :class="{ danger: state.support.error }">
      {{ state.support.error || state.support.message }}
    </div>

    <section class="support-workspace">
      <aside class="support-inbox">
        <div class="support-tools">
          <label class="support-search">
            <IconlyIcon name="search" decorative />
            <input v-model="query" placeholder="جستجو در تیکت‌ها" />
          </label>
          <div class="support-chips">
            <button
              v-for="item in categories"
              :key="item.key"
              :class="{ active: activeCategory === item.key }"
              type="button"
              @click="activeCategory = item.key"
            >
              {{ item.label }}
            </button>
          </div>
        </div>

        <div v-if="state.support.loading" class="support-empty compact">
          <IconlyIcon name="progress_activity" decorative />
          <small>در حال دریافت تیکت‌ها</small>
        </div>

        <div v-else-if="!filteredTickets.length" class="support-empty compact">
          <IconlyIcon name="inbox" decorative />
          <small>تیکتی برای این فیلتر نیست</small>
        </div>

        <div v-else class="ticket-list">
          <button
            v-for="ticket in filteredTickets"
            :key="ticket.id"
            :class="['ticket-row', selectedTicket?.id === ticket.id && 'is-active']"
            type="button"
            @click="openTicket(ticket.id)"
          >
            <span :class="['ticket-dot', statusClass(ticket.status)]"></span>
            <span class="ticket-title">
              <b>{{ ticket.subject }}</b>
              <time>{{ ticket.time }}</time>
            </span>
            <small>{{ ticket.lastMessagePreview || ticket.message }}</small>
            <em>{{ ticket.organization }} / #{{ ticket.id }} / {{ ticket.categoryLabel }} / {{ ticket.priorityLabel }}</em>
          </button>
        </div>
      </aside>

      <main class="support-conversation">
        <div v-if="state.support.detailLoading" class="support-empty compact">
          <IconlyIcon name="progress_activity" decorative />
          <small>در حال دریافت مکالمه</small>
        </div>

        <div v-else-if="!selectedTicket" class="support-empty compact">
          <IconlyIcon name="chat" decorative />
          <small>یک تیکت را انتخاب کنید</small>
        </div>

        <template v-else>
          <header class="conversation-head">
            <div>
              <span :class="['status-pill', statusClass(selectedTicket.status)]">{{ selectedTicket.statusLabel }}</span>
              <h3>{{ selectedTicket.subject }}</h3>
              <small>{{ selectedTicketSubtitle }}</small>
            </div>
            <div class="conversation-meta">
              <span><IconlyIcon name="business" decorative />{{ selectedTicket.organization }}</span>
              <span><IconlyIcon name="sell" decorative />{{ selectedTicket.categoryLabel }}</span>
              <span><IconlyIcon name="flag" decorative />{{ selectedTicket.priorityLabel }}</span>
              <span>#{{ selectedTicket.id }}</span>
            </div>
          </header>

          <section v-if="selectedTicket.attachments?.length" class="attachment-strip">
            <button v-for="item in selectedTicket.attachments" :key="item.id" type="button" @click="openProtectedFile(item.fileUrl, item.originalName)">
              <IconlyIcon name="attach_file" decorative />
              {{ item.originalName }}
            </button>
          </section>

          <section v-if="isRegistrationTicket" class="registration-summary">
            <div><span>نام مجموعه</span><b>{{ selectedTicket.actionMeta.organizationName }}</b></div>
            <div><span>نام مدیر</span><b>{{ selectedTicket.actionMeta.managerName }}</b></div>
            <div><span>نام کاربری</span><b dir="ltr">{{ selectedTicket.actionMeta.managerUsername }}</b></div>
            <div><span>موبایل</span><b dir="ltr">{{ selectedTicket.actionMeta.managerPhone }}</b></div>
            <div><span>ایمیل</span><b dir="ltr">{{ selectedTicket.actionMeta.managerEmail || 'ثبت نشده' }}</b></div>
            <div><span>کد شرکت</span><b dir="ltr">{{ selectedTicket.actionMeta.companyCode || 'در انتظار ثبت' }}</b></div>
          </section>

          <section ref="threadRef" class="message-thread" aria-live="polite">
            <article
              v-for="message in conversationMessages"
              :key="message.id"
              :class="['message-row', messageClass(message)]"
            >
              <div :class="['message-bubble', messageClass(message)]">
                <div class="message-meta">
                  <span>
                    <b>{{ message.sender }}</b>
                    <em>{{ messageRoleLabel(message) }}</em>
                  </span>
                  <time>{{ message.time }}</time>
                </div>
                <p>{{ message.body }}</p>
              </div>
            </article>
            <div v-if="!conversationMessages.length" class="thread-empty">
              <IconlyIcon name="forum" decorative />
              <small>پیامی برای نمایش وجود ندارد</small>
            </div>
          </section>

          <section v-if="selectedTicket.status !== 'closed'" class="reply-box">
            <textarea v-model="replyBody" rows="3" placeholder="پاسخ را بنویسید..." @keydown.ctrl.enter.prevent="sendReply(false)" />
            <div class="reply-actions">
              <button v-if="canDepositToWallet" class="support-soft" type="button" :disabled="state.support.submitting" @click="openWalletDepositModal">شارژ کیف پول</button>
              <button v-if="canCompleteWalletTransfer" class="support-soft" type="button" :disabled="state.support.submitting" @click="openWalletDepositModal">تکمیل انتقال کیف</button>
              <button v-if="canCompleteBankWithdraw" class="support-soft" type="button" :disabled="state.support.submitting" @click="openBankWithdrawModal">تکمیل برداشت</button>
              <button v-if="canApproveRegistration" class="support-primary" type="button" :disabled="state.support.submitting" @click="openRegistrationModal">ثبت مجموعه</button>
              <button
                v-if="canCloseTicket"
                class="support-soft"
                type="button"
                :disabled="state.support.submitting"
                @click="sendReply(true)"
              >
                بستن
              </button>
              <button class="support-primary icon-label" type="button" :disabled="state.support.submitting || !replyBody.trim()" @click="sendReply(false)">
                <IconlyIcon name="send" decorative />
                ارسال
              </button>
            </div>
          </section>

          <section v-else class="feedback-box">
            <div class="stars">
              <button
                v-for="score in 5"
                :key="score"
                :class="{ active: feedback.score >= score || selectedTicket.customerSatisfaction >= score }"
                type="button"
                :disabled="!!selectedTicket.customerSatisfaction"
                @click="feedback.score = score"
              >
                ★
              </button>
            </div>
            <textarea v-if="!selectedTicket.customerSatisfaction" v-model="feedback.text" rows="3" placeholder="نظر شما..." />
            <button v-if="!selectedTicket.customerSatisfaction" class="support-primary" type="button" :disabled="!feedback.score" @click="sendFeedback">
              ثبت نظر
            </button>
          </section>
        </template>
      </main>
    </section>

    <div v-if="modalOpen" class="support-modal-backdrop" @click.self="modalOpen = false">
      <form class="support-modal" @submit.prevent="submitTicket">
        <div class="modal-handle"></div>
        <h3>تیکت جدید</h3>
        <div class="modal-grid">
          <label>
            <span>دسته‌بندی</span>
            <select v-model="form.category">
              <option v-for="item in categories.filter((category) => category.key !== 'all')" :key="item.key" :value="item.key">
                {{ item.label }}
              </option>
            </select>
          </label>
          <label>
            <span>اولویت</span>
            <select v-model="form.priority">
              <option v-for="item in priorities" :key="item.key" :value="item.key">{{ item.label }}</option>
            </select>
          </label>
        </div>
        <label>
          <span>موضوع</span>
          <input v-model.trim="form.subject" required />
        </label>
        <label>
          <span>متن</span>
          <textarea v-model.trim="form.message" required rows="5"></textarea>
        </label>
        <label>
          <span>پیوست</span>
          <input type="file" multiple @change="setFiles" />
        </label>
        <div class="modal-actions">
          <button class="support-soft" type="button" @click="modalOpen = false">بستن</button>
          <button class="support-primary" type="submit" :disabled="state.support.submitting">ثبت</button>
        </div>
      </form>
    </div>

    <div v-if="walletDepositModalOpen" class="support-modal-backdrop" @click.self="walletDepositModalOpen = false">
      <form class="support-modal" @submit.prevent="submitWalletDeposit">
        <div class="modal-handle"></div>
        <h3>شارژ کیف پول</h3>
        <label>
          <span>مبلغ (تومان)</span>
          <input v-model.trim="walletDepositForm.amount" inputmode="decimal" required placeholder="0" @input="walletDepositForm.amount = formatAmountInput($event.target.value)" />
        </label>
        <div class="modal-actions">
          <button class="support-soft" type="button" @click="walletDepositModalOpen = false">بستن</button>
          <button class="support-primary" type="submit" :disabled="state.support.submitting">شارژ</button>
        </div>
      </form>
    </div>
    <div v-if="bankWithdrawModalOpen" class="support-modal-backdrop" @click.self="bankWithdrawModalOpen = false">
      <form class="support-modal" @submit.prevent="submitBankWithdraw">
        <div class="modal-handle"></div>
        <h3>ثبت برداشت بانکی</h3>
        <label>
          <span>شماره شبا</span>
          <input :value="selectedTicket?.actionMeta?.iban || '-'" dir="ltr" readonly />
        </label>
        <label>
          <span>مبلغ (تومان)</span>
          <input v-model.trim="bankWithdrawForm.amount" inputmode="decimal" required placeholder="0" @input="bankWithdrawForm.amount = formatAmountInput($event.target.value)" />
        </label>
        <div class="modal-actions">
          <button class="support-soft" type="button" @click="bankWithdrawModalOpen = false">بستن</button>
          <button class="support-primary" type="submit" :disabled="state.support.submitting">ثبت برداشت</button>
        </div>
      </form>
    </div>
    <div v-if="registrationModalOpen" class="support-modal-backdrop" @click.self="registrationModalOpen = false">
      <form class="support-modal" @submit.prevent="approveRegistration">
        <div class="modal-handle"></div>
        <h3>بررسی و ثبت مجموعه</h3>
        <p>پس از بررسی مدارک و تایید اطلاعات، کد شرکت را وارد کنید تا مجموعه و مدیر اصلی فعال شوند.</p>
        <label>
          <span>کد شرکت</span>
          <input v-model.trim="registrationForm.companyCode" dir="ltr" required placeholder="company-code" />
        </label>
        <div class="modal-actions">
          <button class="support-soft" type="button" @click="registrationModalOpen = false">بستن</button>
          <button class="support-primary" type="submit" :disabled="state.support.submitting || !registrationForm.companyCode">ثبت مجموعه</button>
        </div>
      </form>
    </div>
  </section>
</template>

<style scoped>
.support-page {
  --support-navy: #111827;
  --support-blue: var(--button-primary-bg, #17315d);
  --support-action-bg: #34908B;
  --support-action-shadow: 0 16px 38px rgba(40, 82, 143, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.32);
  --support-green: #667085;
  --support-gold: #667085;
  --support-rose: #667085;
  --support-ink: #344054;
  --support-muted: #667085;
  --support-line: #e4e7ec;
  --support-soft-bg: #f9fafb;
  display: grid;
  gap: 18px;
}

.registration-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 0 20px;
  padding: 16px;
  border: 1px solid rgba(55, 99, 168, 0.14);
  border-radius: 20px;
  background: var(--surface, #fff);
}
.registration-summary div { display: grid; gap: 5px; min-width: 0; }
.registration-summary span { color: var(--support-muted); font-size: .75rem; font-weight: 800; }
.registration-summary b { overflow-wrap: anywhere; color: var(--support-ink); }
@media (max-width: 720px) { .registration-summary { grid-template-columns: 1fr 1fr; } }

.support-hero,
.support-status-card,
.support-inbox,
.support-conversation,
.support-modal {
  border: 1px solid var(--support-line);
  box-shadow: none;
}

.support-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  overflow: hidden;
  padding: 16px;
  border-radius: 12px;
  background: var(--surface, #fff);
}

.support-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 180px;
}

.support-title > .iconly-shell {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background: var(--support-navy);
}

.support-title h2 {
  margin: 0;
  color: var(--support-ink);
  font-size: 1.15rem;
  line-height: 1.5;
}

.support-title small {
  color: var(--support-muted);
  font-weight: 800;
}

.support-hero-actions {
  display: flex;
  align-items: stretch;
  gap: 10px;
  flex: 1 1 auto;
  min-width: 0;
}

.conversation-meta span,
.support-modal label span {
  color: var(--support-muted);
  font-size: 0.78rem;
  font-weight: 900;
}

.conversation-meta {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.conversation-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 28px;
  padding: 0 8px;
  border-radius: 8px;
  background: var(--support-soft-bg);
}

.conversation-meta i {
  font-size: 1rem;
}

.support-primary,
.support-soft,
.support-chips button {
  cursor: pointer;
}

.support-chips,
.modal-actions,
.reply-box div,
.conversation-meta,
.attachment-strip {
  display: flex;
  align-items: center;
  gap: 10px;
}

.support-primary,
.support-soft {
  border: 0;
  border-radius: 10px;
  min-height: 44px;
  padding: 0 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 900;
}

.support-primary:disabled,
.support-soft:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.icon-label .iconly-shell {
  font-size: 1.15rem;
}

.support-primary {
  color: #fff;
  background: var(--support-blue) !important;
  box-shadow: none;
}

.support-soft {
  color: var(--support-ink) !important;
  background: rgba(55, 99, 168, 0.1) !important;
}

.support-alert {
  padding: 14px 18px;
  border-radius: 18px;
  color: #254f85;
  background: rgba(55, 99, 168, 0.1);
  font-weight: 900;
}

.support-alert.danger {
  color: var(--support-ink);
  background: #f9fafb;
}

.support-status-card {
  flex: 1 1 0;
  min-width: 0;
  min-height: 48px;
  padding: 0 12px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  color: var(--support-ink);
  background: var(--surface, #fff);
}

.support-status-card.is-active {
  color: #fff;
  background: var(--support-navy);
}

.support-status-card.is-active b,
.support-status-card.is-active span,
.support-status-card.is-active .iconly-shell {
  color: #fff;
}

.support-status-card b {
  color: var(--support-navy);
  font-size: 1rem;
}

.support-status-card span:not(.iconly-shell) {
  white-space: nowrap;
  font-weight: 900;
}

.support-workspace {
  display: grid;
  grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}

.support-inbox,
.support-conversation {
  min-height: min(680px, calc(100vh - 210px));
  padding: 18px;
  border-radius: 12px;
  background: var(--surface, #fff);
}

.support-conversation {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.support-tools {
  display: grid;
  gap: 12px;
  margin-bottom: 14px;
}

.support-search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border: 1px solid rgba(32, 58, 105, 0.12);
  border-radius: 10px;
  padding: 0 12px;
  background: #fff;
}

.support-search .iconly-shell {
  color: var(--support-muted);
  font-size: 1.1rem;
}

.support-search input {
  border: 0;
  padding-inline: 0;
}

.support-modal input,
.support-modal select,
.support-modal textarea,
.reply-box textarea,
.feedback-box textarea {
  width: 100%;
  border: 1px solid rgba(32, 58, 105, 0.12);
  border-radius: 10px;
  padding: 12px 14px;
  color: var(--support-navy);
  background: #fff;
  font: inherit;
  outline: none;
}

.support-chips {
  flex-wrap: wrap;
}

.support-chips button {
  border: 0;
  border-radius: 10px;
  padding: 8px 12px;
  color: var(--support-muted);
  background: rgba(55, 99, 168, 0.08);
  font-weight: 900;
}

.support-chips button.active {
  color: #fff;
  background: var(--support-navy);
}

.ticket-list,
.message-thread,
.reply-box,
.feedback-box,
.support-modal {
  display: grid;
  gap: 12px;
}

.ticket-row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 7px 10px;
  width: 100%;
  padding: 15px;
  border: 1px solid rgba(32, 58, 105, 0.08);
  border-radius: 10px;
  text-align: start;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.ticket-row:hover {
  border-color: rgba(37, 99, 235, 0.28);
  background: #f8fbff;
}

.ticket-row.is-active {
  border-color: rgba(37, 99, 235, 0.4);
  background: #eff6ff;
}

.ticket-row small,
.ticket-row em {
  grid-column: 2;
}

.ticket-title {
  grid-column: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}

.ticket-title b {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ticket-title time {
  flex: 0 0 auto;
  color: var(--support-muted);
  font-size: 0.72rem;
  font-weight: 800;
}

.ticket-row b,
.conversation-head h3 {
  color: var(--support-navy);
}

.ticket-row small,
.message-bubble time {
  color: var(--support-muted);
}

.ticket-row small {
  display: -webkit-box;
  overflow: hidden;
  line-height: 1.8;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.ticket-row em {
  color: var(--support-muted);
  font-style: normal;
  font-size: 0.78rem;
  font-weight: 900;
}

.ticket-dot {
  grid-row: 1 / span 3;
  width: 12px;
  height: 12px;
  margin-top: 4px;
  border-radius: 999px;
  background: var(--support-blue);
}

.ticket-dot.pending,
.ticket-dot.answered {
  background: var(--support-gold);
}

.ticket-dot.closed {
  background: var(--support-blue);
}

.conversation-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--support-line);
}

.conversation-head h3 {
  margin: 8px 0 2px;
  font-size: 1.18rem;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.conversation-head small {
  color: var(--support-muted);
  font-weight: 800;
}

.status-pill {
  display: inline-flex;
  width: max-content;
  padding: 7px 11px;
  border-radius: 999px;
  color: #335ea5;
  background: rgba(73, 114, 190, 0.12);
  font-weight: 900;
}

.status-pill.closed {
  color: var(--support-ink);
  background: #f9fafb;
}

.attachment-strip {
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.attachment-strip button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 12px;
  border: 0;
  border-radius: 14px;
  color: var(--support-ink);
  background: rgba(224, 155, 88, 0.14);
  font-weight: 900;
  cursor: pointer;
}

.message-thread {
  flex: 1 1 auto;
  min-height: 320px;
  max-height: none;
  overflow: auto;
  align-content: end;
  padding: 18px;
  border-radius: 12px;
  background: #f9fafb;
}

.message-row {
  display: flex;
}

.message-row.incoming {
  justify-content: flex-start;
}

.message-row.outgoing {
  justify-content: flex-end;
}

.message-bubble {
  max-width: min(620px, 88%);
  padding: 13px 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.message-bubble.outgoing {
  color: #fff;
  border-color: transparent;
  border-bottom-left-radius: 14px;
  border-bottom-right-radius: 4px;
  background: var(--support-blue);
}

.message-bubble.outgoing b,
.message-bubble.outgoing em,
.message-bubble.outgoing time,
.message-bubble.outgoing p {
  color: #fff;
}

.message-bubble.incoming {
  color: var(--support-navy);
  border-bottom-right-radius: 14px;
  border-bottom-left-radius: 4px;
  background: #eef4ff;
}

.message-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.message-meta span {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
}

.message-meta b {
  overflow: hidden;
  color: var(--support-ink);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-meta em {
  flex: 0 0 auto;
  color: var(--support-muted);
  font-size: 0.72rem;
  font-style: normal;
  font-weight: 900;
}

.message-meta time {
  flex: 0 0 auto;
  font-size: 0.72rem;
  font-weight: 800;
}

.message-bubble p {
  margin: 8px 0 0;
  line-height: 1.9;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.thread-empty {
  min-height: 260px;
  display: grid;
  place-items: center;
  gap: 6px;
  color: var(--support-muted);
  text-align: center;
}

.reply-box,
.feedback-box {
  margin-top: 14px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--support-line);
  background: #fff;
}

.reply-box textarea {
  min-height: 94px;
  resize: vertical;
}

.reply-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
}

.stars {
  display: flex;
  gap: 6px;
}

.stars button {
  border: 0;
  color: #cbd5e1;
  background: transparent;
  font-size: 1.8rem;
  cursor: pointer;
}

.stars button.active {
  color: var(--support-gold);
}

.support-empty {
  min-height: 320px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  border-radius: 12px;
  color: rgba(24, 49, 83, 0.5);
  background: rgba(255, 255, 255, 0.72);
}

.support-empty.compact {
  min-height: 240px;
}

.support-empty .iconly-shell {
  font-size: 3rem;
}

.support-empty small {
  font-weight: 900;
}

.support-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(24, 49, 83, 0.4);
  backdrop-filter: none;
}

.support-modal {
  width: min(560px, 100%);
  padding: 22px;
  border-radius: 12px;
  background: #f8fbff;
}

.support-modal h3 {
  margin: 0;
  color: var(--support-navy);
}

.modal-handle {
  width: 54px;
  height: 5px;
  margin: 0 auto;
  border-radius: 999px;
  background: rgba(24, 49, 83, 0.18);
}

.modal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.support-modal label {
  display: grid;
  gap: 8px;
}

@media (max-width: 1050px) {
  .support-hero,
  .support-workspace {
    grid-template-columns: 1fr;
  }

  .support-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .support-hero-actions {
    flex-wrap: wrap;
  }
}

@media (max-width: 640px) {
  .support-hero,
  .conversation-head,
  .reply-box div,
  .modal-grid {
    display: grid;
    grid-template-columns: 1fr;
  }

  .support-hero-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* Dashboard-aligned neutral navy theme. */
.support-page {
  --support-navy: #111827;
  --support-blue: var(--button-primary-bg, #17315d);
  --support-green: #667085;
  --support-gold: #667085;
  --support-rose: #667085;
  --support-ink: #344054;
  --support-muted: #667085;
  --support-line: #e4e7ec;
  --support-soft-bg: #f9fafb;
}

.support-hero,
.support-status-card,
.support-inbox,
.support-conversation,
.support-modal,
.registration-summary,
.ticket-row,
.reply-box,
.feedback-box {
  background: #ffffff;
  border: 1px solid var(--support-line);
  box-shadow: none;
}

.message-bubble.incoming {
  background: #eef4ff;
  border: 1px solid #c7d8f7;
  box-shadow: none;
}

.support-title > .iconly-shell,
.support-primary,
.support-status-card,
.support-status-card.is-active,
.message-bubble.outgoing {
  color: #ffffff !important;
  background: #34908B !important;
  background-image: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
}

.support-primary:hover:not(:disabled),
.support-status-card:hover:not(:disabled),
.support-status-card.is-active:hover:not(:disabled) {
  color: #ffffff !important;
  background: #2b7874 !important;
  background-image: none !important;
  border-color: transparent !important;
  box-shadow: none !important;
}

.support-soft,
.support-chips button,
.conversation-meta span,
.status-pill,
.status-pill.closed,
.attachment-strip button,
.ticket-row:hover,
.ticket-row.is-active,
.support-alert,
.support-alert.danger {
  color: var(--support-ink) !important;
  background: #f9fafb !important;
  border-color: var(--support-line);
}

.support-title h2,
.ticket-row b,
.conversation-head h3,
.registration-summary b,
.message-meta b,
.message-bubble.incoming,
.support-modal h3,
.support-modal input,
.support-modal select,
.support-modal textarea,
.reply-box textarea,
.feedback-box textarea {
  color: var(--support-navy);
}

.support-title small,
.conversation-meta span,
.support-modal label span,
.registration-summary span,
.ticket-row small,
.ticket-row em,
.ticket-title time,
.conversation-head small,
.message-meta em,
.message-meta time,
.thread-empty,
.support-empty,
.support-search .iconly-shell {
  color: var(--support-muted);
}

.ticket-dot,
.ticket-dot.pending,
.ticket-dot.answered,
.ticket-dot.closed,
.stars button.active {
  color: var(--support-blue);
}

.support-status-card b,
.support-status-card span,
.support-status-card .iconly-shell {
  color: #ffffff !important;
}

.ticket-dot,
.ticket-dot.pending,
.ticket-dot.answered,
.ticket-dot.closed {
  background: var(--support-blue);
}

.support-search,
.support-modal input,
.support-modal select,
.support-modal textarea,
.reply-box textarea,
.feedback-box textarea {
  background: #ffffff;
  border: 1px solid var(--support-line);
}

.message-thread {
  background: #f9fafb;
}

.support-empty {
  background: #ffffff;
}

.support-modal {
  background: #ffffff;
}

.modal-handle {
  background: #e4e7ec;
}
</style>
