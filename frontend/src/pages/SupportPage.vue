<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { formatAmountInput } from '../utils/amount'
import { useWorkflowHub } from '../stores/workflowHub'

const PAYMENT_TICKET_SUBJECT = 'پرداخت کیف پول'

const {
  state,
  loadSupportTickets,
  loadSupportTicketDetail,
  createSupportTicket,
  submitSupportReply,
  submitSupportFeedback,
  submitSupportWalletDeposit,
  markSupportTicketsSeen,
  openProtectedFile,
} = useWorkflowHub()

const activeStatus = ref('all')
const activeCategory = ref('all')
const query = ref('')
const modalOpen = ref(false)
const walletDepositModalOpen = ref(false)
const replyBody = ref('')
const feedback = reactive({ score: 0, text: '' })
const walletDepositForm = reactive({ amount: '' })
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
  return message?.senderPlatformRole === 'hq_support' ? 'support' : 'tenant'
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
}

async function sendFeedback() {
  if (!selectedTicket.value?.id || !feedback.score) return
  await submitSupportFeedback(selectedTicket.value.id, { score: feedback.score, feedback: feedback.text })
}

function openWalletDepositModal() {
  walletDepositForm.amount = ''
  walletDepositModalOpen.value = true
}

async function submitWalletDeposit() {
  if (!selectedTicket.value?.id) return
  await submitSupportWalletDeposit(selectedTicket.value.id, { amount: walletDepositForm.amount })
  walletDepositModalOpen.value = false
  walletDepositForm.amount = ''
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
</script>

<template>
  <section class="support-page">
    <section class="support-hero">
      <div class="support-hero-actions">
        <button
          v-for="item in statusTabs"
          :key="item.key"
          :class="['support-status-card', statusClass(item.key), activeStatus === item.key && 'is-active']"
          type="button"
          @click="activeStatus = item.key"
        >
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <b>{{ item.count }}</b>
          <small>{{ item.label }}</small>
        </button>
      </div>
      <button class="support-primary" type="button" @click="modalOpen = true">
        <span class="material-symbols-outlined">add_circle</span>
        ثبت تیکت
      </button>
    </section>

    <div v-if="state.support.error || state.support.message" class="support-alert" :class="{ danger: state.support.error }">
      {{ state.support.error || state.support.message }}
    </div>

    <section class="support-workspace">
      <aside class="support-inbox">
        <div class="support-tools">
          <input v-model="query" placeholder="جستجو" />
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
          <span class="material-symbols-outlined">progress_activity</span>
        </div>

        <div v-else-if="!filteredTickets.length" class="support-empty compact">
          <span class="material-symbols-outlined">inbox</span>
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
            <b>{{ ticket.subject }}</b>
            <small>{{ ticket.organization }} · {{ ticket.lastMessagePreview }}</small>
            <em>#{{ ticket.id }} · {{ ticket.categoryLabel }} · {{ ticket.priorityLabel }}</em>
          </button>
        </div>
      </aside>

      <main class="support-conversation">
        <div v-if="state.support.detailLoading" class="support-empty compact">
          <span class="material-symbols-outlined">progress_activity</span>
        </div>

        <div v-else-if="!selectedTicket" class="support-empty compact">
          <span class="material-symbols-outlined">chat</span>
        </div>

        <template v-else>
          <header class="conversation-head">
            <div>
              <span :class="['status-pill', statusClass(selectedTicket.status)]">{{ selectedTicket.statusLabel }}</span>
              <h3>{{ selectedTicket.subject }}</h3>
            </div>
            <div class="conversation-meta">
              <span>{{ selectedTicket.organization }}</span>
              <span>{{ selectedTicket.categoryLabel }}</span>
              <span>{{ selectedTicket.priorityLabel }}</span>
              <span>#{{ selectedTicket.id }}</span>
            </div>
          </header>

          <section v-if="selectedTicket.attachments?.length" class="attachment-strip">
            <button v-for="item in selectedTicket.attachments" :key="item.id" type="button" @click="openProtectedFile(item.fileUrl, item.originalName)">
              <span class="material-symbols-outlined">attach_file</span>
              {{ item.originalName }}
            </button>
          </section>

          <section class="message-thread">
            <article
              v-for="message in selectedTicket.messages || []"
              :key="message.id"
              :class="['message-row', messageClass(message)]"
            >
              <div :class="['message-bubble', messageClass(message)]">
                <div>
                  <b>{{ message.sender }}</b>
                  <small>{{ message.time }}</small>
                </div>
                <p>{{ message.body }}</p>
              </div>
            </article>
          </section>

          <section v-if="selectedTicket.status !== 'closed'" class="reply-box">
            <textarea v-model="replyBody" rows="4" placeholder="پاسخ..." />
            <div>
              <button
                v-if="canDepositToWallet"
                class="support-soft"
                type="button"
                :disabled="state.support.submitting"
                @click="openWalletDepositModal"
              >
                واریز
              </button>
              <button
                v-if="canCloseTicket"
                class="support-soft"
                type="button"
                :disabled="state.support.submitting"
                @click="sendReply(true)"
              >
                بستن
              </button>
              <button class="support-primary" type="button" :disabled="state.support.submitting || !replyBody.trim()" @click="sendReply(false)">
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
            <textarea v-if="!selectedTicket.customerSatisfaction" v-model="feedback.text" rows="3" placeholder="نظر کوتاه..." />
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
            <span>دسته</span>
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
          <span>عنوان</span>
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
          <button class="support-soft" type="button" @click="modalOpen = false">لغو</button>
          <button class="support-primary" type="submit" :disabled="state.support.submitting">ثبت</button>
        </div>
      </form>
    </div>

    <div v-if="walletDepositModalOpen" class="support-modal-backdrop" @click.self="walletDepositModalOpen = false">
      <form class="support-modal" @submit.prevent="submitWalletDeposit">
        <div class="modal-handle"></div>
        <h3>واریز به کیف پول</h3>
        <label>
          <span>مبلغ</span>
          <input v-model.trim="walletDepositForm.amount" inputmode="decimal" required placeholder="0" @input="walletDepositForm.amount = formatAmountInput($event.target.value)" />
        </label>
        <div class="modal-actions">
          <button class="support-soft" type="button" @click="walletDepositModalOpen = false">لغو</button>
          <button class="support-primary" type="submit" :disabled="state.support.submitting">تایید</button>
        </div>
      </form>
    </div>
  </section>
</template>

<style scoped>
.support-page {
  --support-navy: #183153;
  --support-blue: #3763a8;
  --support-gold: #e09b58;
  --support-ink: #1f3557;
  --support-muted: #66758f;
  --support-line: rgba(32, 58, 105, 0.08);
  display: grid;
  gap: 18px;
}

.support-hero,
.support-status-card,
.support-inbox,
.support-conversation,
.support-modal {
  border: 1px solid var(--support-line);
  box-shadow: 0 18px 42px rgba(24, 41, 77, 0.1);
}

.support-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  overflow: hidden;
  padding: 24px;
  border-radius: 34px;
  background:
    radial-gradient(circle at 12% 18%, rgba(55, 99, 168, 0.18), transparent 34%),
    radial-gradient(circle at 76% 8%, rgba(224, 155, 88, 0.18), transparent 28%),
    linear-gradient(135deg, #f8fbff 0%, #eff4fb 48%, #fbfdff 100%);
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
  border-radius: 16px;
  min-height: 44px;
  padding: 0 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 900;
}

.support-primary {
  color: #fff;
  background: linear-gradient(135deg, #234783, #3763a8);
  box-shadow: 0 16px 34px rgba(35, 71, 131, 0.2);
}

.support-soft {
  color: var(--support-ink);
  background: rgba(55, 99, 168, 0.1);
}

.support-alert {
  padding: 14px 18px;
  border-radius: 18px;
  color: #254f85;
  background: rgba(55, 99, 168, 0.1);
  font-weight: 900;
}

.support-alert.danger {
  color: #9f1239;
  background: #fff1f2;
}

.support-status-card {
  flex: 1 1 0;
  min-width: 0;
  min-height: 54px;
  padding: 0 14px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  color: var(--support-ink);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 250, 255, 0.94));
}

.support-status-card.is-active {
  color: #fff;
  background: linear-gradient(135deg, #183153, #3763a8);
}

.support-status-card.is-active b,
.support-status-card.is-active small,
.support-status-card.is-active .material-symbols-outlined {
  color: #fff;
}

.support-status-card b {
  color: var(--support-navy);
  font-size: 1rem;
}

.support-status-card small {
  white-space: nowrap;
}

.support-workspace {
  display: grid;
  grid-template-columns: 380px minmax(0, 1fr);
  gap: 16px;
}

.support-inbox,
.support-conversation {
  min-height: 600px;
  padding: 18px;
  border-radius: 30px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(246, 249, 252, 0.96));
}

.support-tools {
  display: grid;
  gap: 12px;
  margin-bottom: 14px;
}

.support-tools input,
.support-modal input,
.support-modal select,
.support-modal textarea,
.reply-box textarea,
.feedback-box textarea {
  width: 100%;
  border: 1px solid rgba(32, 58, 105, 0.12);
  border-radius: 16px;
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
  border-radius: 999px;
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
  gap: 6px 10px;
  width: 100%;
  padding: 15px;
  border: 1px solid rgba(32, 58, 105, 0.08);
  border-radius: 22px;
  text-align: start;
  background: #fff;
  cursor: pointer;
}

.ticket-row.is-active {
  border-color: rgba(55, 99, 168, 0.3);
  background: #f2f7ff;
}

.ticket-row b,
.ticket-row small,
.ticket-row em {
  grid-column: 2;
}

.ticket-row b,
.conversation-head h3 {
  color: var(--support-navy);
}

.ticket-row small,
.message-bubble small {
  color: var(--support-muted);
}

.ticket-row em {
  color: #8d5d1e;
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
  background: #4b9968;
}

.conversation-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
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
  color: #166534;
  background: #dcfce7;
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
  max-height: 420px;
  overflow: auto;
  padding: 10px;
  border-radius: 24px;
  background: #f6f9fc;
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
  max-width: min(620px, 88%);
  padding: 14px;
  border-radius: 20px;
}

.message-bubble.support {
  color: #fff;
  background: linear-gradient(135deg, #183153, #3763a8);
}

.message-bubble.tenant {
  color: var(--support-navy);
  background: #fff;
}

.message-bubble p {
  margin: 8px 0 0;
  line-height: 1.9;
}

.reply-box,
.feedback-box {
  margin-top: 14px;
  padding: 14px;
  border-radius: 24px;
  background: #fff;
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
  border-radius: 30px;
  color: rgba(24, 49, 83, 0.5);
  background: rgba(255, 255, 255, 0.72);
}

.support-empty.compact {
  min-height: 240px;
}

.support-empty .material-symbols-outlined {
  font-size: 3rem;
}

.support-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(24, 49, 83, 0.4);
  backdrop-filter: blur(10px);
}

.support-modal {
  width: min(560px, 100%);
  padding: 22px;
  border-radius: 30px;
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
</style>
