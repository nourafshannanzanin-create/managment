<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import HqReportsPanel from '../components/hq/HqReportsPanel.vue'
import HqServicesPanel from '../components/hq/HqServicesPanel.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

import { formatAmountInput } from '../utils/amount'
import { unlockTicketAlerts } from '../utils/ticketAlert'
import { useWorkflowHub } from '../stores/workflowHub'

const PAYMENT_TICKET_SUBJECT = 'درخواست واریز کیف پول'

const {
  state,
  loadHqPanel,
  selectHqOrganization,
  createHqOrganization,
  loadSupportTickets,
  loadHqTickets,
  loadSupportTicketDetail,
  submitSupportReply,
  loadHqTeam,
  createHqTeamMember,
  updateHqTeamMember,
  deleteHqTeamMember,
  submitSupportWalletDeposit,
  submitSupportBankWithdrawComplete,
  submitSupportRegistrationApproval,
  openProtectedFile,
} = useWorkflowHub()

const isHqAdmin = computed(() => Boolean(state.currentUser.isHqAdmin))
const isSupportOnly = computed(() =>
  state.currentUser.platformRole === 'hq_support' && !isHqAdmin.value,
)

const activeTab = ref('tickets')
const ticketScope = ref('all')
const ticketQuery = ref('')
const ticketFiltersOpen = ref(false)
const ticketPriority = ref('all')
const ticketStatusFilter = ref('all')
const replyBody = ref('')
const replyStatus = ref('')
const replyAssignTo = ref(0)
const replyInternal = ref(false)
const threadRef = ref(null)
const pollTimer = ref(null)

const walletDepositModalOpen = ref(false)
const bankWithdrawModalOpen = ref(false)
const registrationModalOpen = ref(false)
const walletDepositForm = reactive({ amount: '' })
const bankWithdrawForm = reactive({ amount: '' })
const registrationForm = reactive({ companyCode: '' })

const organizationForm = reactive({
  organizationName: '',
  organizationCode: '',
  managerName: '',
  managerUsername: '',
  managerEmail: '',
  managerPhone: '',
  managerPassword: '',
})

const teamForm = reactive({
  fullName: '',
  username: '',
  phone: '',
  password: '',
})
const teamFormError = ref('')
const teamFormSuccess = ref('')
const teamSaving = ref(false)
const teamEditingId = ref(null)

const ticketResponseTemplates = [
  {
    id: 'need-info',
    title: 'درخواست اطلاعات بیشتر',
    body: 'برای بررسی دقیق‌تر، لطفا جزئیات تکمیلی، زمان رخداد و در صورت نیاز شماره سفارش یا تراکنش را ارسال کنید.',
  },
  {
    id: 'under-review',
    title: 'در حال بررسی',
    body: 'موضوع شما دریافت شد و در حال بررسی توسط تیم مربوطه است. نتیجه بررسی به‌محض جمع‌بندی از همین تیکت اعلام می‌شود.',
  },
  {
    id: 'resolved',
    title: 'جمع‌بندی و حل',
    body: 'بررسی انجام شد و مورد از سمت ما رفع شده است. لطفا یک‌بار مجدد بررسی کنید و اگر هنوز مشکل باقی بود همین تیکت را ادامه دهید.',
  },
]

const visibleTabs = computed(() => {
  if (isSupportOnly.value) {
    return [{ key: 'tickets', label: 'تیکت‌ها', icon: 'support_agent' }]
  }
  if (isHqAdmin.value) {
    return [
      { key: 'tickets', label: 'تیکت‌ها', icon: 'support_agent' },
      { key: 'services', label: 'سرویس‌ها', icon: 'payments' },
      { key: 'reports', label: 'گزارشات HQ', icon: 'table_chart' },
      { key: 'team', label: 'تیم', icon: 'groups' },
      { key: 'overview', label: 'مجموعه‌ها', icon: 'domain' },
    ]
  }
  return [
    { key: 'tickets', label: 'تیکت‌ها', icon: 'support_agent' },
    { key: 'overview', label: 'نمای کلی', icon: 'dashboard' },
  ]
})

const tickets = computed(() => state.support.tickets?.length
  ? state.support.tickets
  : (state.hq.tickets || []))
const selectedTicket = computed(() => state.support.selectedTicket)
const teamMembers = computed(() => state.hq.team || [])
const teamAssignable = computed(() =>
  teamMembers.value.filter((item) => ['hq_admin', 'hq_support'].includes(item.platformRole)),
)

const summaryCards = computed(() => [
  { label: 'مجموعه', value: state.hq.summary.organizations || 0, icon: 'domain' },
  { label: 'کاربر', value: state.hq.summary.users || 0, icon: 'groups' },
  { label: 'فعال', value: state.hq.summary.activeUsers || 0, icon: 'verified_user' },
  { label: 'پرداخت', value: state.hq.summary.paymentTotal || '0', icon: 'payments' },
  { label: 'در انتظار', value: state.hq.summary.pendingPaymentTotal || '0', icon: 'pending_actions' },
  { label: 'درخواست باز', value: state.hq.summary.openRequests || 0, icon: 'assignment_late' },
  { label: 'سند باز', value: state.hq.summary.pendingDocuments || 0, icon: 'edit_document' },
  { label: 'تیکت', value: state.hq.summary.tickets || 0, icon: 'support_agent' },
])

const reportRows = computed(() => state.hq.organizations || [])

const ticketScopeOptions = computed(() => {
  if (isHqAdmin.value) {
    return [
      { key: 'all', label: 'همه' },
      { key: 'mine', label: 'ارجاع به من' },
      { key: 'unassigned', label: 'بدون مسئول' },
      { key: 'urgent', label: 'فوری' },
    ]
  }
  return [
    { key: 'active', label: 'صف فعال' },
    { key: 'answered', label: 'پاسخ‌داده‌شده' },
    { key: 'urgent', label: 'فوری' },
  ]
})

const ticketSummary = computed(() => {
  const items = tickets.value || []
  const me = Number(state.currentUser.id || 0)
  const counts = items.reduce((acc, item) => {
    if (item.status === 'open') acc.open += 1
    if (item.status === 'pending') acc.pending += 1
    if (item.status === 'answered') acc.answered += 1
    if (item.status === 'closed') acc.closed += 1
    if (!item.assignedTo) acc.unassigned += 1
    if (Number(item.assignedTo || 0) === me) acc.mine += 1
    if (['urgent', 'high'].includes(item.priority)) acc.urgent += 1
    return acc
  }, { open: 0, pending: 0, answered: 0, closed: 0, unassigned: 0, mine: 0, urgent: 0 })
  const active = counts.open + counts.pending + counts.answered
  return { ...counts, active }
})

const ticketStatCards = computed(() => {
  if (isHqAdmin.value) {
    return [
      { key: 'all', label: 'فعال', value: ticketSummary.value.active },
      { key: 'urgent', label: 'فوری', value: ticketSummary.value.urgent, urgent: true },
      { key: 'mine', label: 'من', value: ticketSummary.value.mine },
    ]
  }
  return [
    { key: 'active', label: 'فعال', value: ticketSummary.value.active },
    { key: 'urgent', label: 'فوری', value: ticketSummary.value.urgent, urgent: true },
    { key: 'answered', label: 'پاسخ‌داده‌شده', value: ticketSummary.value.answered },
  ]
})

function paymentTicketRank(ticket) {
  return ticket?.category === 'financial'
    && ticket?.priority === 'urgent'
    && ticket?.subject === PAYMENT_TICKET_SUBJECT
    ? 0
    : 1
}

function matchesQuery(ticket, needle) {
  if (!needle) return true
  return `${ticket.id} ${ticket.subject} ${ticket.message || ''} ${ticket.categoryLabel || ''} ${ticket.organization || ''} ${ticket.lastMessagePreview || ''} ${ticket.requester || ''} ${ticket.assignedToName || ''}`
    .toLowerCase()
    .includes(needle)
}

const visibleTickets = computed(() => {
  const needle = ticketQuery.value.trim().toLowerCase()
  const me = Number(state.currentUser.id || 0)
  return (tickets.value || [])
    .filter((item) => {
      if (ticketPriority.value !== 'all' && item.priority !== ticketPriority.value) return false
      if (isHqAdmin.value && ticketStatusFilter.value !== 'all' && item.status !== ticketStatusFilter.value) return false
      if (!isHqAdmin.value && item.status === 'closed' && ticketScope.value !== 'answered') return false

      if (ticketScope.value === 'mine') return Number(item.assignedTo || 0) === me
      if (ticketScope.value === 'unassigned') return !item.assignedTo
      if (ticketScope.value === 'urgent') return ['urgent', 'high'].includes(item.priority)
      if (ticketScope.value === 'answered') return item.status === 'answered'
      if (ticketScope.value === 'active') return ['open', 'pending', 'answered'].includes(item.status)
      if (ticketScope.value === 'all' && !isHqAdmin.value) return ['open', 'pending', 'answered'].includes(item.status)
      return true
    })
    .filter((item) => matchesQuery(item, needle))
    .sort((a, b) => {
      const rankDiff = paymentTicketRank(a) - paymentTicketRank(b)
      if (rankDiff !== 0) return rankDiff
      return new Date(b.updatedAt || b.lastMessageAt || 0) - new Date(a.updatedAt || a.lastMessageAt || 0)
    })
})

const conversationMessages = computed(() => {
  const ticket = selectedTicket.value
  if (!ticket) return []
  const messages = Array.isArray(ticket.messages) ? ticket.messages.filter((message) => message?.body) : []
  const normalized = messages.map((message, index) => ({
    ...message,
    id: message.id ?? `message-${index}`,
    sender: message.sender || ticket.requester || ticket.organization || 'کاربر',
    createdAt: message.createdAt || message.created_at || '',
    time: message.time || message.createdAtIso || '',
    isInternal: Boolean(message.isInternal || message.is_internal),
  }))
  if (normalized.length) {
    return normalized.sort((a, b) => new Date(a.createdAt || 0) - new Date(b.createdAt || 0))
  }
  if (!ticket.message) return []
  return [{
    id: `ticket-${ticket.id}-initial`,
    sender: ticket.requester || ticket.organization || 'کاربر',
    senderPlatformRole: 'tenant',
    body: ticket.message,
    createdAt: ticket.createdAt || '',
    time: ticket.createdAtIso || ticket.time || '',
    isInternal: false,
  }]
})

const canDepositToWallet = computed(() =>
  state.currentUser.canUseHq
  && !selectedTicket.value?.organizationIsShowcase
  && paymentTicketRank(selectedTicket.value) === 0,
)
const canCompleteWalletTransfer = computed(() =>
  state.currentUser.canUseHq
  && !selectedTicket.value?.organizationIsShowcase
  && selectedTicket.value?.actionMeta?.actionType === 'wallet_withdrawal'
  && selectedTicket.value?.actionMeta?.destinationType === 'wallet',
)
const canCompleteBankWithdraw = computed(() =>
  state.currentUser.canUseHq
  && !selectedTicket.value?.organizationIsShowcase
  && selectedTicket.value?.actionMeta?.actionType === 'wallet_withdrawal'
  && selectedTicket.value?.actionMeta?.destinationType === 'bank',
)
const isRegistrationTicket = computed(() =>
  selectedTicket.value?.actionMeta?.actionType === 'organization_registration',
)
const canApproveRegistration = computed(() =>
  state.currentUser.canUseHq
  && isRegistrationTicket.value
  && selectedTicket.value?.actionMeta?.canApprove,
)
const showActionCards = computed(() =>
  Boolean(
    selectedTicket.value
    && (
      canDepositToWallet.value
      || canCompleteWalletTransfer.value
      || canCompleteBankWithdraw.value
      || canApproveRegistration.value
      || isRegistrationTicket.value
      || selectedTicket.value?.attachments?.length
    ),
  ),
)

function selectTab(tabKey) {
  if (!visibleTabs.value.some((tab) => tab.key === tabKey)) return
  activeTab.value = tabKey
}

function resetReplyComposer(ticket = selectedTicket.value) {
  replyBody.value = ''
  replyStatus.value = ''
  replyInternal.value = false
  replyAssignTo.value = Number(ticket?.assignedTo || 0)
}

async function scrollThreadToBottom() {
  await nextTick()
  if (!threadRef.value) return
  threadRef.value.scrollTop = threadRef.value.scrollHeight
}

async function openTicket(ticketId) {
  if (!ticketId) return
  await loadSupportTicketDetail(ticketId)
  resetReplyComposer(state.support.selectedTicket)
  await scrollThreadToBottom()
}

function clearSelectedTicket() {
  state.support.selectedTicket = null
  resetReplyComposer(null)
}

function applyTicketTemplate(body) {
  replyBody.value = body
}

function messageIsMine(message) {
  return message?.senderPlatformRole === 'hq_support' || message?.senderPlatformRole === 'hq_admin'
}

function messageRoleLabel(message) {
  if (message?.isInternal) return 'یادداشت داخلی'
  if (message?.senderPlatformRole === 'hq_admin') return 'مدیر HQ'
  if (message?.senderPlatformRole === 'hq_support') return 'پشتیبانی'
  return 'کاربر'
}

async function refreshTickets(options = {}) {
  await loadSupportTickets(true, options)
}

async function sendTicketReply() {
  if (!selectedTicket.value?.id || !replyBody.value.trim()) return
  const payload = {
    body: replyBody.value.trim(),
    status: replyStatus.value || undefined,
    isInternal: isHqAdmin.value ? replyInternal.value : false,
    assignToUserId: isHqAdmin.value && replyAssignTo.value ? Number(replyAssignTo.value) : undefined,
  }
  await submitSupportReply(selectedTicket.value.id, payload)
  resetReplyComposer(state.support.selectedTicket)
  await scrollThreadToBottom()
}

function openWalletDepositModal() {
  walletDepositForm.amount = selectedTicket.value?.actionMeta?.amount || ''
  walletDepositModalOpen.value = true
}

function openBankWithdrawModal() {
  bankWithdrawForm.amount = selectedTicket.value?.actionMeta?.amount || ''
  bankWithdrawModalOpen.value = true
}

function openRegistrationModal() {
  registrationForm.companyCode = selectedTicket.value?.actionMeta?.companyCode || ''
  registrationModalOpen.value = true
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

async function approveRegistration() {
  if (!selectedTicket.value?.id) return
  const ok = await submitSupportRegistrationApproval(selectedTicket.value.id, registrationForm.companyCode)
  if (ok) registrationModalOpen.value = false
}

function openOrganization(organizationId) {
  void selectHqOrganization(organizationId)
}

function resetOrganizationForm() {
  Object.assign(organizationForm, {
    organizationName: '',
    organizationCode: '',
    managerName: '',
    managerUsername: '',
    managerEmail: '',
    managerPhone: '',
    managerPassword: '',
  })
}

async function submitOrganization() {
  await createHqOrganization({ ...organizationForm })
  resetOrganizationForm()
}

function resetTeamForm() {
  Object.assign(teamForm, { fullName: '', username: '', phone: '', password: '' })
  teamFormError.value = ''
  teamFormSuccess.value = ''
  teamEditingId.value = null
}

function startEditTeamMember(member) {
  Object.assign(teamForm, {
    fullName: member.fullName || member.name || '',
    username: member.username || member.slug || '',
    phone: member.phone || '',
    password: '',
  })
  teamFormError.value = ''
  teamFormSuccess.value = ''
  teamEditingId.value = member.id
}

async function submitTeamMember() {
  teamFormError.value = ''
  teamFormSuccess.value = ''
  teamSaving.value = true
  try {
    const payload = {
      fullName: teamForm.fullName.trim(),
      username: teamForm.username.trim(),
      phone: teamForm.phone.trim(),
    }
    if (teamForm.password) payload.password = teamForm.password
    if (teamEditingId.value) {
      const member = await updateHqTeamMember(teamEditingId.value, payload)
      if (payload.password) {
        teamFormSuccess.value = member?.smsSent
          ? 'پشتیبان به‌روزرسانی شد و مشخصات ورود پیامک شد.'
          : `پشتیبان به‌روزرسانی شد.${member?.smsMessage ? ` پیامک: ${member.smsMessage}` : ''}`
      } else {
        teamFormSuccess.value = 'پشتیبان به‌روزرسانی شد.'
      }
      resetTeamForm()
    } else {
      if (!payload.password) {
        teamFormError.value = 'رمز عبور برای پشتیبان جدید الزامی است.'
        return
      }
      if (!payload.phone) {
        teamFormError.value = 'شماره موبایل برای ارسال پیامک مشخصات ورود الزامی است.'
        return
      }
      const member = await createHqTeamMember(payload)
      const loginId = member?.username || member?.slug || payload.username
      const smsNote = member?.smsSent
        ? 'پیامک مشخصات ورود ارسال شد.'
        : (member?.smsMessage ? `پیامک ارسال نشد: ${member.smsMessage}` : 'پیامک ارسال نشد.')
      teamFormSuccess.value = `پشتیبان ساخته شد. ورود با «${loginId}». ${smsNote}`
      Object.assign(teamForm, { fullName: '', username: '', phone: '', password: '' })
      teamEditingId.value = null
    }
  } catch (error) {
    teamFormError.value = error?.message || 'ثبت پشتیبان ناموفق بود.'
  } finally {
    teamSaving.value = false
  }
}

async function removeTeamMember(member) {
  if (!member?.id || member.platformRole !== 'hq_support') return
  const label = member.fullName || member.username || 'پشتیبان'
  if (!window.confirm(`حذف نرم پشتیبان «${label}»؟`)) return
  await deleteHqTeamMember(member.id)
  if (teamEditingId.value === member.id) resetTeamForm()
}

function formatSupportScore(value) {
  const num = Number(value || 0)
  if (!Number.isFinite(num) || num <= 0) return '—'
  return num.toFixed(1)
}

function supportScorePercent(value) {
  const num = Math.max(0, Math.min(5, Number(value || 0)))
  return (num / 5) * 100
}

function formatResponseMinutes(value) {
  const num = Number(value || 0)
  if (!Number.isFinite(num) || num <= 0) return '—'
  if (num < 60) return `${Math.round(num)} دقیقه`
  const hours = Math.floor(num / 60)
  const minutes = Math.round(num % 60)
  return minutes ? `${hours}س ${minutes}د` : `${hours} ساعت`
}

function initials(name) {
  const text = String(name || '').trim()
  if (!text) return 'SP'
  return text.slice(0, 2).toUpperCase()
}

function toFa(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}

watch(isHqAdmin, (admin) => {
  ticketScope.value = admin ? 'all' : 'active'
  if (!admin && ['team', 'overview', 'services', 'reports'].includes(activeTab.value)) {
    activeTab.value = 'tickets'
  }
}, { immediate: true })

watch(
  () => conversationMessages.value.length,
  () => { void scrollThreadToBottom() },
)

watch(activeTab, async (tab) => {
  if (tab === 'team' && isHqAdmin.value) await loadHqTeam(true)
  if (tab === 'overview' && isHqAdmin.value) await loadHqPanel(true)
})

onMounted(async () => {
  window.addEventListener('pointerdown', unlockTicketAlerts, { once: true })
  window.addEventListener('keydown', unlockTicketAlerts, { once: true })

  if (!isHqAdmin.value) activeTab.value = 'tickets'

  await Promise.all([
    loadHqPanel(true, { soft: false }).catch(() => {}),
    loadSupportTickets(true, { soft: false }).catch(() => loadHqTickets(true)),
    isHqAdmin.value ? loadHqTeam(true).catch(() => {}) : Promise.resolve(),
  ])

  pollTimer.value = window.setInterval(() => {
    void loadSupportTickets(true, { soft: true, notifyNew: true })
    void loadHqPanel(true, { soft: true })
  }, 10000)
})

onUnmounted(() => {
  if (pollTimer.value) window.clearInterval(pollTimer.value)
  window.removeEventListener('pointerdown', unlockTicketAlerts)
  window.removeEventListener('keydown', unlockTicketAlerts)
})
</script>

<template>
  <section
    class="page-shell hq-panel-page"
    :class="{
      'support-only': isSupportOnly,
      'ticket-focus-mode': activeTab === 'tickets',
    }"
  >
    <section v-if="!state.currentUser.canUseHq" class="surface-block hq-locked">
      <IconlyIcon name="lock" decorative />
      <strong>HQ</strong>
    </section>

    <template v-else>
      <nav v-if="visibleTabs.length > 1" class="hq-panel-tabs" aria-label="بخش‌های پنل مرکزی">
        <button
          v-for="tab in visibleTabs"
          :key="tab.key"
          type="button"
          class="hq-panel-tab"
          :class="{ active: activeTab === tab.key }"
          @click="selectTab(tab.key)"
        >
          <IconlyIcon :name="tab.icon" decorative />
          <span>{{ tab.label }}</span>
        </button>
      </nav>

      <!-- TICKET DESK -->
      <section
        v-if="activeTab === 'tickets'"
        class="ticket-desk"
        :class="{
          'support-ticket-mode': isSupportOnly,
          'ticket-desk-open': Boolean(selectedTicket),
        }"
      >
        <aside class="ticket-desk-inbox">
          <div class="ticket-desk-inbox-top">
            <div class="ticket-desk-brand">
              <div>
                <strong>{{ isHqAdmin ? 'مرکز تیکت' : 'میز پاسخ‌گویی' }}</strong>
                <span>{{ toFa(visibleTickets.length) }} گفتگو</span>
              </div>
              <div class="ticket-desk-brand-actions">
                <button type="button" class="ticket-icon-btn" title="بروزرسانی" @click="refreshTickets()">
                  <IconlyIcon name="sync" decorative />
                </button>
              </div>
            </div>

            <div class="ticket-desk-stats">
              <button
                v-for="stat in ticketStatCards"
                :key="stat.key"
                type="button"
                class="ticket-stat"
                :class="{ active: ticketScope === stat.key, urgent: stat.urgent }"
                @click="ticketScope = stat.key"
              >
                <small>{{ stat.label }}</small>
                <strong>{{ toFa(stat.value) }}</strong>
              </button>
            </div>

            <label class="ticket-desk-search">
              <span class="sr-only">جستجو</span>
              <input v-model.trim="ticketQuery" placeholder="جستجو در عنوان، مجموعه یا متن..." />
            </label>

            <div class="ticket-desk-scopes">
              <button
                v-for="scope in ticketScopeOptions"
                :key="scope.key"
                type="button"
                class="ticket-scope"
                :class="{ active: ticketScope === scope.key }"
                @click="ticketScope = scope.key"
              >
                {{ scope.label }}
              </button>
              <button
                type="button"
                class="ticket-scope ticket-scope-filters"
                :class="{ active: ticketFiltersOpen }"
                @click="ticketFiltersOpen = !ticketFiltersOpen"
              >
                فیلتر
              </button>
            </div>

            <div v-if="ticketFiltersOpen" class="ticket-desk-filters">
              <select v-if="isHqAdmin" v-model="ticketStatusFilter">
                <option value="all">همه وضعیت‌ها</option>
                <option value="open">باز</option>
                <option value="pending">در انتظار پیگیری</option>
                <option value="answered">پاسخ داده شده</option>
                <option value="closed">بسته شده</option>
              </select>
              <select v-model="ticketPriority">
                <option value="all">همه اولویت‌ها</option>
                <option value="low">کم</option>
                <option value="medium">متوسط</option>
                <option value="high">بالا</option>
                <option value="urgent">فوری</option>
              </select>
            </div>
          </div>

          <div class="ticket-desk-list">
            <div v-if="state.support.loading && !tickets.length" class="ticket-desk-empty">
              <IconlyIcon name="progress_activity" decorative />
              <strong>در حال دریافت تیکت‌ها</strong>
            </div>

            <button
              v-for="item in visibleTickets"
              :key="item.id"
              type="button"
              class="ticket-row"
              :class="{
                active: selectedTicket?.id === item.id,
                urgent: ['urgent', 'high'].includes(item.priority),
              }"
              @click="openTicket(item.id)"
            >
              <div class="ticket-row-main">
                <strong>{{ item.subject }}</strong>
                <span class="ticket-row-status" :class="`is-${item.status}`">{{ item.statusLabel || item.status }}</span>
              </div>
              <p>{{ item.lastMessagePreview || item.message }}</p>
              <div class="ticket-row-foot">
                <span>{{ item.organization || 'بدون مجموعه' }}</span>
                <span>{{ item.priorityLabel || item.priority }}</span>
                <span>{{ item.time || item.updatedAtIso }}</span>
              </div>
            </button>

            <div v-if="!state.support.loading && !visibleTickets.length" class="ticket-desk-empty">
              <strong>تیکتی اینجا نیست</strong>
              <span>فیلتر را عوض کنید یا لیست را بروزرسانی کنید.</span>
            </div>
          </div>
        </aside>

        <section class="ticket-desk-stage">
          <div v-if="state.support.detailLoading" class="ticket-stage-empty">
            <IconlyIcon name="progress_activity" decorative />
            <strong>در حال دریافت مکالمه</strong>
          </div>

          <div v-else-if="selectedTicket" class="ticket-stage-body">
            <header class="ticket-stage-head">
              <button type="button" class="ticket-back-btn" @click="clearSelectedTicket">
                بازگشت به لیست
              </button>
              <div class="ticket-stage-title">
                <div class="ticket-stage-title-row">
                  <h2>{{ selectedTicket.subject }}</h2>
                  <span class="ticket-row-status" :class="`is-${selectedTicket.status}`">
                    {{ selectedTicket.statusLabel || selectedTicket.status }}
                  </span>
                </div>
                <div class="ticket-stage-meta">
                  <span>{{ selectedTicket.organization || 'بدون مجموعه' }}</span>
                  <span>{{ selectedTicket.categoryLabel }}</span>
                  <span>{{ selectedTicket.priorityLabel }}</span>
                  <span v-if="selectedTicket.assignedToName">مسئول: {{ selectedTicket.assignedToName }}</span>
                  <span class="mono">#{{ selectedTicket.id }}</span>
                </div>
              </div>
              <div class="ticket-stage-controls">
                <label>
                  <span>وضعیت</span>
                  <select v-model="replyStatus">
                    <option value="">بدون تغییر</option>
                    <option value="answered">پاسخ داده شده</option>
                    <option value="pending">در انتظار پیگیری</option>
                    <option value="closed">بستن تیکت</option>
                  </select>
                </label>
                <label v-if="isHqAdmin">
                  <span>ارجاع</span>
                  <select v-model.number="replyAssignTo">
                    <option :value="0">بدون ارجاع</option>
                    <option v-for="member in teamAssignable" :key="member.id" :value="member.id">
                      {{ member.fullName || member.username }}
                    </option>
                  </select>
                </label>
              </div>
            </header>

            <div v-if="showActionCards" class="ticket-stage-actions">
              <section v-if="isRegistrationTicket" class="ticket-action-card approve">
                <div>
                  <strong>تایید ثبت‌نام مجموعه</strong>
                  <p>
                    {{ selectedTicket.actionMeta.organizationName }}
                    —
                    {{ selectedTicket.actionMeta.managerName }}
                  </p>
                  <div class="ticket-reg-meta">
                    <small dir="ltr">{{ selectedTicket.actionMeta.managerUsername }}</small>
                    <small dir="ltr">{{ selectedTicket.actionMeta.managerPhone }}</small>
                    <small dir="ltr">{{ selectedTicket.actionMeta.companyCode || 'کد در انتظار' }}</small>
                  </div>
                </div>
                <button
                  v-if="canApproveRegistration"
                  type="button"
                  class="action-btn tone-primary"
                  :disabled="state.support.submitting"
                  @click="openRegistrationModal"
                >
                  تایید و فعال‌سازی
                </button>
              </section>

              <section v-if="canDepositToWallet || canCompleteWalletTransfer" class="ticket-action-card wallet">
                <div>
                  <strong>{{ canCompleteWalletTransfer ? 'تکمیل انتقال کیف' : 'واریز کیف پول' }}</strong>
                  <p>مبلغ تاییدشده را وارد کنید تا به کیف پول مقصد اعمال شود.</p>
                </div>
                <button
                  type="button"
                  class="action-btn tone-primary"
                  :disabled="state.support.submitting"
                  @click="openWalletDepositModal"
                >
                  {{ canCompleteWalletTransfer ? 'تکمیل انتقال' : 'واریز کیف پول' }}
                </button>
              </section>

              <section v-if="canCompleteBankWithdraw" class="ticket-action-card wallet">
                <div>
                  <strong>تکمیل برداشت بانکی</strong>
                  <p>شبا: {{ selectedTicket.actionMeta.iban || '—' }}</p>
                </div>
                <button
                  type="button"
                  class="action-btn tone-primary"
                  :disabled="state.support.submitting"
                  @click="openBankWithdrawModal"
                >
                  ثبت برداشت
                </button>
              </section>

              <section v-if="selectedTicket.attachments?.length" class="ticket-action-card files">
                <strong>پیوست‌ها</strong>
                <div class="ticket-file-row">
                  <button
                    v-for="attachment in selectedTicket.attachments"
                    :key="attachment.id"
                    type="button"
                    class="ticket-file-chip"
                    @click="openProtectedFile(attachment.fileUrl, attachment.originalName)"
                  >
                    <IconlyIcon name="attach_file" decorative />
                    {{ attachment.originalName || 'فایل' }}
                  </button>
                </div>
              </section>
            </div>

            <div ref="threadRef" class="ticket-stage-stream">
              <div
                v-for="message in conversationMessages"
                :key="message.id"
                class="ticket-bubble"
                :class="{
                  mine: messageIsMine(message),
                  internal: message.isInternal,
                }"
              >
                <div class="ticket-bubble-meta">
                  <strong>{{ message.sender }}</strong>
                  <span>{{ messageRoleLabel(message) }}</span>
                  <small>{{ message.time }}</small>
                </div>
                <p>{{ message.body }}</p>
              </div>
              <div v-if="!conversationMessages.length" class="ticket-desk-empty">
                <strong>پیامی نیست</strong>
              </div>
            </div>

            <footer v-if="selectedTicket.status !== 'closed'" class="ticket-stage-composer">
              <div class="ticket-template-row">
                <button
                  v-for="template in ticketResponseTemplates"
                  :key="template.id"
                  type="button"
                  class="ticket-template"
                  @click="applyTicketTemplate(template.body)"
                >
                  {{ template.title }}
                </button>
              </div>
              <textarea
                v-model.trim="replyBody"
                rows="3"
                placeholder="پاسخ را اینجا بنویسید..."
                @keydown.ctrl.enter.prevent="sendTicketReply"
                @keydown.meta.enter.prevent="sendTicketReply"
              />
              <div class="ticket-composer-bar">
                <label v-if="isHqAdmin" class="ticket-internal">
                  <input v-model="replyInternal" type="checkbox" />
                  <span>یادداشت داخلی</span>
                </label>
                <span v-else class="ticket-composer-hint">Ctrl + Enter برای ارسال</span>
                <button
                  type="button"
                  class="action-btn tone-primary"
                  :disabled="state.support.submitting || !replyBody"
                  @click="sendTicketReply"
                >
                  <IconlyIcon name="send" decorative />
                  <span>ارسال پاسخ</span>
                </button>
              </div>
            </footer>
          </div>

          <div v-else class="ticket-stage-empty">
            <IconlyIcon name="chat" decorative />
            <strong>یک تیکت انتخاب کنید</strong>
            <span>از لیست سمت راست گفتگو را باز کنید و مستقیم پاسخ بدهید.</span>
          </div>
        </section>
      </section>

      <!-- TEAM TAB -->
      <section v-else-if="activeTab === 'team' && isHqAdmin" class="hq-team-grid">
        <article class="surface-block hq-team-create">
          <div class="section-label-row">
            <h3>{{ teamEditingId ? 'ویرایش پشتیبان' : 'افزودن پشتیبان' }}</h3>
            <span>دسترسی: فقط مرکز تیکت</span>
          </div>
          <form class="hq-team-form" @submit.prevent="submitTeamMember">
            <label>
              <span>نام کامل</span>
              <input v-model.trim="teamForm.fullName" required placeholder="میلاد دهستانی" />
            </label>
            <label>
              <span>نام کاربری ورود</span>
              <input v-model.trim="teamForm.username" dir="ltr" required placeholder="nazanin.nrf" />
              <small class="hq-team-hint">برای ورود همین نام کاربری یا ایمیل داخلی را وارد کنید. نقطه به خط تیره تبدیل می‌شود.</small>
            </label>
            <label>
              <span>موبایل</span>
              <input v-model.trim="teamForm.phone" dir="ltr" :required="!teamEditingId" placeholder="09xxxxxxxxx" />
              <small class="hq-team-hint">مشخصات ورود بلافاصله برای همین شماره پیامک می‌شود.</small>
            </label>
            <label>
              <span>{{ teamEditingId ? 'رمز عبور جدید (اختیاری)' : 'رمز عبور' }}</span>
              <input v-model="teamForm.password" dir="ltr" type="password" :required="!teamEditingId" minlength="6" />
            </label>
            <p v-if="teamFormError" class="hq-team-error">{{ teamFormError }}</p>
            <p v-if="teamFormSuccess" class="hq-team-success">{{ teamFormSuccess }}</p>
            <div class="hq-team-form-actions">
              <button v-if="teamEditingId" class="action-btn tone-soft" type="button" @click="resetTeamForm">انصراف</button>
              <button class="action-btn tone-primary" type="submit" :disabled="teamSaving">
                <IconlyIcon name="person_add" decorative />
                <span>{{ teamSaving ? 'در حال ثبت' : (teamEditingId ? 'ذخیره' : 'ثبت پشتیبان') }}</span>
              </button>
            </div>
          </form>
        </article>

        <article class="surface-block hq-team-list">
          <div class="section-label-row">
            <h3>تیم مرکزی</h3>
            <span>{{ toFa(teamMembers.length) }} کاربر</span>
          </div>
          <div class="team-grid">
            <div v-for="member in teamMembers" :key="member.id" class="team-card">
              <UserAvatar
                class="team-avatar"
                :person="member"
                :name="member.fullName || member.username"
                size="md"
              />
              <div class="team-card-body">
                <strong>{{ member.fullName || member.username }}</strong>
                <p>{{ member.platformRole === 'hq_admin' ? 'مدیرکل' : 'پشتیبان مرکزی' }}</p>
                <small dir="ltr">{{ member.username || member.slug }}</small>
                <small v-if="member.email" dir="ltr" class="team-email">{{ member.email }}</small>

                <template v-if="member.platformRole === 'hq_support'">
                  <div class="team-rating">
                    <div class="team-stars" :title="`امتیاز ${formatSupportScore(member.supportStarRating)} از 5`">
                      <span class="team-stars-base">★★★★★</span>
                      <span class="team-stars-fill" :style="{ width: `${supportScorePercent(member.supportStarRating)}%` }">★★★★★</span>
                    </div>
                    <span class="team-rating-score">{{ formatSupportScore(member.supportStarRating) }}</span>
                  </div>
                  <div class="team-metrics">
                    <small>رضایت: {{ formatSupportScore(member.supportCustomerSatisfactionAvg) }} / ۵</small>
                    <small>کیفیت پاسخ: {{ formatSupportScore(member.supportResponseQualityAvg) }} / ۵</small>
                    <small>پاسخ‌ اول: {{ formatResponseMinutes(member.supportFirstResponseMinutesAvg) }}</small>
                    <small>تعداد رضایت: {{ toFa(member.supportRatingCount || 0) }}</small>
                  </div>
                  <div class="team-actions">
                    <button type="button" class="action-btn tone-soft" @click="startEditTeamMember(member)">
                      <IconlyIcon name="edit" decorative />
                      <span>ویرایش</span>
                    </button>
                    <button type="button" class="action-btn tone-danger" @click="removeTeamMember(member)">
                      <IconlyIcon name="delete" decorative />
                      <span>حذف</span>
                    </button>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </article>
      </section>

      <HqServicesPanel v-else-if="activeTab === 'services' && isHqAdmin" />

      <HqReportsPanel v-else-if="activeTab === 'reports' && isHqAdmin" />

      <!-- OVERVIEW / ORGANIZATIONS -->
      <template v-else-if="activeTab === 'overview' && isHqAdmin">
        <section class="hq-report-grid">
          <article v-for="item in summaryCards" :key="item.label" class="hq-report-card">
            <IconlyIcon :name="item.icon" decorative />
            <strong>{{ item.value }}</strong>
            <small>{{ item.label }}</small>
          </article>
        </section>

        <section class="surface-block hq-report-surface">
          <div class="section-label-row">
            <h3>مجموعه‌ها</h3>
            <button class="icon-btn" type="button" :disabled="state.hq.loading" @click="loadHqPanel(true)">
              <IconlyIcon name="sync" decorative />
            </button>
          </div>

          <div class="table-shell">
            <table class="data-table">
              <thead>
                <tr>
                  <th>مجموعه</th>
                  <th>کد</th>
                  <th>کاربر</th>
                  <th>پرداخت</th>
                  <th>درخواست</th>
                  <th>سند</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="organization in reportRows" :key="organization.id">
                  <td>
                    <strong>{{ organization.name }}</strong>
                    <small class="table-muted">{{ organization.createdAt }}</small>
                  </td>
                  <td>{{ organization.code }}</td>
                  <td>{{ organization.activeUsers }} / {{ organization.users }}</td>
                  <td>{{ organization.paymentTotal }}</td>
                  <td>{{ organization.requests }}</td>
                  <td>{{ organization.documents }}</td>
                  <td>
                    <button class="action-btn tone-soft" type="button" @click="openOrganization(organization.id)">
                      <IconlyIcon name="input" decorative />
                      <span>انتخاب</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="surface-block hq-create-surface">
          <div class="section-label-row">
            <h3>اضافه کردن مجموعه</h3>
          </div>

          <form class="hq-create-form" @submit.prevent="submitOrganization">
            <label>
              <span>نام مجموعه</span>
              <input v-model="organizationForm.organizationName" required />
            </label>
            <label>
              <span>کد مجموعه</span>
              <input v-model="organizationForm.organizationCode" dir="ltr" placeholder="business-code" />
            </label>
            <label>
              <span>نام مدیر</span>
              <input v-model="organizationForm.managerName" required />
            </label>
            <label>
              <span>نام کاربری مدیر</span>
              <input v-model="organizationForm.managerUsername" dir="ltr" required />
            </label>
            <label>
              <span>ایمیل مدیر</span>
              <input v-model="organizationForm.managerEmail" dir="ltr" type="email" placeholder="optional@email.com" />
            </label>
            <label>
              <span>تلفن مدیر</span>
              <input v-model="organizationForm.managerPhone" dir="ltr" />
            </label>
            <label>
              <span>رمز عبور مدیر</span>
              <input v-model="organizationForm.managerPassword" dir="ltr" required type="password" />
            </label>
            <button class="action-btn tone-primary hq-create-submit" type="submit" :disabled="state.hq.saving">
              <IconlyIcon name="domain_add" decorative />
              <span>{{ state.hq.saving ? 'در حال ثبت' : 'ثبت مجموعه' }}</span>
            </button>
          </form>
        </section>

        <section class="hq-report-lower">
          <article class="surface-block">
            <div class="section-label-row">
              <h3>نقش‌ها</h3>
            </div>
            <div class="hq-segment-list">
              <div v-for="item in state.hq.segments.roles" :key="item.key" class="hq-segment-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.count }}</strong>
              </div>
            </div>
          </article>

          <article class="surface-block">
            <div class="section-label-row">
              <h3>پرداخت‌ها</h3>
            </div>
            <div class="hq-segment-list">
              <div v-for="item in state.hq.segments.payments" :key="item.key" class="hq-segment-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.count }}</strong>
              </div>
            </div>
          </article>

          <article class="surface-block">
            <div class="section-label-row">
              <h3>وضعیت تیکت‌ها</h3>
            </div>
            <div class="hq-segment-list">
              <div v-for="item in state.hq.segments.tickets" :key="item.key" class="hq-segment-row">
                <span>{{ item.label }}</span>
                <strong>{{ item.count }}</strong>
              </div>
            </div>
          </article>
        </section>
      </template>
    </template>

    <div v-if="walletDepositModalOpen" class="hq-modal-backdrop" @click.self="walletDepositModalOpen = false">
      <form class="hq-modal" @submit.prevent="submitWalletDeposit">
        <h3>{{ canCompleteWalletTransfer ? 'تکمیل انتقال کیف' : 'واریز کیف پول' }}</h3>
        <label>
          <span>مبلغ (تومان)</span>
          <input
            v-model.trim="walletDepositForm.amount"
            inputmode="numeric"
            required
            placeholder="0"
            @input="walletDepositForm.amount = formatAmountInput($event.target.value)"
          />
        </label>
        <div class="hq-modal-actions">
          <button class="action-btn tone-soft" type="button" @click="walletDepositModalOpen = false">بستن</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.support.submitting">ثبت</button>
        </div>
      </form>
    </div>

    <div v-if="bankWithdrawModalOpen" class="hq-modal-backdrop" @click.self="bankWithdrawModalOpen = false">
      <form class="hq-modal" @submit.prevent="submitBankWithdraw">
        <h3>ثبت برداشت بانکی</h3>
        <label>
          <span>شماره شبا</span>
          <input :value="selectedTicket?.actionMeta?.iban || '-'" dir="ltr" readonly />
        </label>
        <label>
          <span>مبلغ (تومان)</span>
          <input
            v-model.trim="bankWithdrawForm.amount"
            inputmode="numeric"
            required
            placeholder="0"
            @input="bankWithdrawForm.amount = formatAmountInput($event.target.value)"
          />
        </label>
        <div class="hq-modal-actions">
          <button class="action-btn tone-soft" type="button" @click="bankWithdrawModalOpen = false">بستن</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.support.submitting">ثبت برداشت</button>
        </div>
      </form>
    </div>

    <div v-if="registrationModalOpen" class="hq-modal-backdrop" @click.self="registrationModalOpen = false">
      <form class="hq-modal" @submit.prevent="approveRegistration">
        <h3>بررسی و ثبت مجموعه</h3>
        <p>پس از بررسی مدارک و تایید اطلاعات، کد شرکت را وارد کنید تا مجموعه و مدیر اصلی فعال شوند.</p>
        <label>
          <span>کد شرکت</span>
          <input v-model.trim="registrationForm.companyCode" dir="ltr" required placeholder="company-code" />
        </label>
        <div class="hq-modal-actions">
          <button class="action-btn tone-soft" type="button" @click="registrationModalOpen = false">بستن</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.support.submitting || !registrationForm.companyCode">
            ثبت مجموعه
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<style scoped>
.hq-panel-page {
  --jade: #0f766e;
  --jade-strong: #0d9488;
  --jade-soft: rgba(15, 118, 110, 0.12);
  --jade-line: rgba(13, 148, 136, 0.28);
  --desk-ink: #0f172a;
  --desk-muted: #64748b;
  --desk-line: rgba(226, 232, 240, 0.95);
  gap: 16px;
}

.hq-panel-page.ticket-focus-mode {
  min-height: calc(100dvh - 120px);
}

.hq-panel-page.support-only.ticket-focus-mode {
  min-height: calc(100dvh - 96px);
}

.hq-locked {
  min-height: 320px;
  display: grid;
  place-items: center;
  color: var(--muted);
}

.hq-panel-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hq-panel-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 42px;
  padding: 8px 14px;
  border: 1px solid var(--desk-line);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
  color: var(--desk-muted);
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.hq-panel-tab.active {
  background: linear-gradient(135deg, var(--jade-soft), rgba(13, 148, 136, 0.08));
  border-color: var(--jade-line);
  color: var(--jade);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Ticket desk */
.ticket-desk {
  display: grid !important;
  grid-template-columns: minmax(300px, 380px) minmax(0, 1fr) !important;
  gap: 0 !important;
  height: calc(100dvh - 180px);
  min-height: 560px;
  background:
    radial-gradient(circle at top left, rgba(13, 148, 136, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(236, 253, 245, 0.55), rgba(248, 250, 252, 0.98));
  border: 1px solid var(--desk-line);
  border-radius: 20px;
  overflow: hidden;
}

.ticket-desk-inbox,
.ticket-desk-stage {
  min-width: 0;
  min-height: 0;
}

.ticket-desk-inbox {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  background: rgba(255, 255, 255, 0.94);
  border-left: 1px solid var(--desk-line);
  backdrop-filter: blur(12px);
}

.ticket-desk-inbox-top {
  display: grid;
  gap: 12px;
  padding: 16px 14px 12px;
  border-bottom: 1px solid var(--desk-line);
}

.ticket-desk-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ticket-desk-brand strong {
  display: block;
  font-size: 16px;
  color: var(--desk-ink);
}

.ticket-desk-brand span {
  color: var(--desk-muted);
  font-size: 12px;
}

.ticket-desk-brand-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ticket-icon-btn,
.ticket-back-btn,
.ticket-scope,
.ticket-template,
.ticket-file-chip,
.ticket-stat,
.ticket-row {
  border: 0;
  background: transparent;
  font: inherit;
  cursor: pointer;
}

.ticket-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: #ecfdf5;
  color: var(--jade);
  display: inline-grid;
  place-items: center;
}

.ticket-back-btn {
  display: none;
  color: var(--jade);
  font-size: 13px;
  font-weight: 700;
  padding: 8px 10px;
  border-radius: 10px;
}

.ticket-desk-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.ticket-stat {
  display: grid;
  gap: 2px;
  padding: 10px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid var(--desk-line);
  text-align: right;
}

.ticket-stat small {
  color: var(--desk-muted);
  font-size: 11px;
}

.ticket-stat strong {
  color: var(--desk-ink);
  font-size: 18px;
  line-height: 1.2;
}

.ticket-stat.active {
  background: var(--jade-soft);
  border-color: var(--jade-line);
}

.ticket-stat.urgent.active,
.ticket-stat.urgent:hover {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.35);
}

.ticket-desk-search input,
.ticket-desk-filters select,
.ticket-stage-controls select,
.ticket-stage-composer textarea,
.hq-team-form input,
.hq-create-form input,
.hq-modal input,
.hq-modal textarea {
  width: 100%;
  border: 1px solid rgba(203, 213, 225, 0.95);
  background: #fff;
  border-radius: 14px;
  padding: 11px 12px;
  color: var(--desk-ink);
  outline: none;
  font: inherit;
}

.ticket-desk-search input:focus,
.ticket-desk-filters select:focus,
.ticket-stage-controls select:focus,
.ticket-stage-composer textarea:focus,
.hq-team-form input:focus,
.hq-create-form input:focus,
.hq-modal input:focus {
  border-color: var(--jade-line);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.14);
}

.ticket-desk-scopes {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}

.ticket-desk-scopes::-webkit-scrollbar {
  display: none;
}

.ticket-scope {
  flex: 0 0 auto;
  padding: 8px 12px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.ticket-scope.active {
  background: var(--jade);
  color: #fff;
}

.ticket-scope-filters.active {
  background: var(--jade-soft);
  color: var(--jade);
}

.ticket-desk-filters {
  display: grid;
  gap: 8px;
}

.ticket-desk-list {
  overflow: auto;
  padding: 8px;
  display: grid;
  align-content: start;
  gap: 6px;
}

.ticket-row {
  display: grid;
  gap: 8px;
  padding: 12px;
  border-radius: 16px;
  text-align: right;
  border: 1px solid transparent;
  transition: background 0.16s ease, border-color 0.16s ease;
}

.ticket-row:hover {
  background: #f0fdfa;
}

.ticket-row.active {
  background: var(--jade-soft);
  border-color: var(--jade-line);
}

.ticket-row.urgent:not(.active) {
  background: rgba(255, 251, 235, 0.7);
}

.ticket-row-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.ticket-row-main strong {
  color: var(--desk-ink);
  font-size: 13px;
  line-height: 1.55;
}

.ticket-row p {
  margin: 0;
  color: var(--desk-muted);
  font-size: 12px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ticket-row-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: #94a3b8;
  font-size: 11px;
}

.ticket-row-status {
  flex: 0 0 auto;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: #e2e8f0;
  color: #334155;
}

.ticket-row-status.is-open { background: rgba(13, 148, 136, 0.12); color: var(--jade); }
.ticket-row-status.is-pending { background: rgba(245, 158, 11, 0.16); color: #b45309; }
.ticket-row-status.is-answered { background: rgba(22, 163, 74, 0.12); color: #15803d; }
.ticket-row-status.is-closed { background: #e2e8f0; color: #64748b; }

.ticket-desk-empty,
.ticket-stage-empty {
  display: grid;
  place-content: center;
  gap: 8px;
  text-align: center;
  padding: 32px 20px;
  color: var(--desk-muted);
}

.ticket-desk-empty strong,
.ticket-stage-empty strong {
  color: var(--desk-ink);
  font-size: 16px;
}

.ticket-desk-stage {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(13, 148, 136, 0.08), transparent 28%),
    #f8fafc;
}

.ticket-stage-body {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.ticket-stage-head,
.ticket-stage-actions,
.ticket-stage-composer {
  flex: 0 0 auto;
}

.ticket-stage-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px 16px;
  align-items: start;
  padding: 16px 18px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid var(--desk-line);
}

.ticket-stage-title {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.ticket-stage-title-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.ticket-stage-title h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.5;
  color: var(--desk-ink);
}

.ticket-stage-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--desk-muted);
  font-size: 12px;
}

.ticket-stage-meta .mono {
  font-variant-numeric: tabular-nums;
  direction: ltr;
}

.ticket-stage-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ticket-stage-controls label {
  display: grid;
  gap: 4px;
  min-width: 140px;
}

.ticket-stage-controls label span {
  font-size: 11px;
  color: var(--desk-muted);
}

.ticket-stage-actions {
  display: grid;
  gap: 10px;
  padding: 12px 18px 0;
}

.ticket-action-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px 14px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid var(--desk-line);
}

.ticket-action-card.approve {
  background: rgba(240, 253, 244, 0.9);
  border-color: rgba(34, 197, 94, 0.2);
}

.ticket-action-card.wallet {
  background: rgba(236, 253, 245, 0.95);
  border-color: var(--jade-line);
}

.ticket-action-card.files {
  grid-template-columns: 1fr;
}

.ticket-action-card strong {
  display: block;
  color: var(--desk-ink);
  font-size: 13px;
}

.ticket-action-card p {
  margin: 4px 0 0;
  color: var(--desk-muted);
  font-size: 12px;
  line-height: 1.7;
}

.ticket-reg-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  color: var(--desk-muted);
  font-size: 11px;
}

.ticket-file-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ticket-file-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  background: #ecfdf5;
  color: var(--jade);
  font-size: 12px;
  font-weight: 700;
}

.ticket-stage-stream {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  padding: 16px 18px;
  display: grid;
  align-content: start;
  gap: 10px;
}

.ticket-bubble {
  max-width: min(720px, 92%);
  justify-self: start;
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 18px 18px 18px 8px;
  background: #fff;
  border: 1px solid var(--desk-line);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.03);
}

.ticket-bubble.mine {
  justify-self: end;
  border-radius: 18px 18px 8px 18px;
  background: rgba(13, 148, 136, 0.1);
  border-color: rgba(13, 148, 136, 0.2);
}

.ticket-bubble.internal {
  background: rgba(254, 243, 199, 0.7);
  border-color: rgba(245, 158, 11, 0.25);
}

.ticket-bubble-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  color: var(--desk-muted);
  font-size: 11px;
}

.ticket-bubble-meta strong {
  color: var(--desk-ink);
  font-size: 12px;
}

.ticket-bubble p {
  margin: 0;
  color: #1e293b;
  font-size: 13px;
  line-height: 1.85;
  white-space: pre-wrap;
}

.ticket-stage-composer {
  display: grid;
  gap: 10px;
  padding: 12px 18px 16px;
  background: rgba(255, 255, 255, 0.96);
  border-top: 1px solid var(--desk-line);
}

.ticket-template-row {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}

.ticket-template-row::-webkit-scrollbar {
  display: none;
}

.ticket-template {
  flex: 0 0 auto;
  padding: 7px 11px;
  border-radius: 999px;
  background: #ecfdf5;
  color: var(--jade);
  font-size: 12px;
  font-weight: 700;
}

.ticket-stage-composer textarea {
  min-height: 72px;
  max-height: 120px;
  resize: none;
  line-height: 1.8;
}

.ticket-composer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ticket-internal {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 13px;
}

.ticket-composer-hint {
  color: #94a3b8;
  font-size: 12px;
}

.ticket-stage-empty {
  flex: 1 1 auto;
  min-height: 100%;
}

/* Team */
.hq-team-grid {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 16px;
}

.hq-team-form {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.hq-team-form label,
.hq-create-form label,
.hq-modal label {
  display: grid;
  gap: 7px;
  min-width: 0;
}

.hq-team-form label span,
.hq-create-form label span,
.hq-modal label span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.hq-team-form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.hq-team-error {
  margin: 0;
  color: #b91c1c;
  font-size: 13px;
  font-weight: 700;
}

.hq-team-success {
  margin: 0;
  color: #0f766e;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

.hq-team-hint {
  display: block;
  margin-top: 0.3rem;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
  font-weight: 500;
}

.team-email {
  display: block;
  opacity: 0.75;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.team-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.78);
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.team-card-body {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.team-avatar {
  flex: 0 0 auto;
}

.team-card p,
.team-card small {
  margin: 4px 0 0;
  color: var(--muted);
}

.team-rating {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.team-stars {
  position: relative;
  display: inline-block;
  font-size: 16px;
  line-height: 1;
  letter-spacing: 1px;
}

.team-stars-base {
  color: #cbd5e1;
}

.team-stars-fill {
  position: absolute;
  inset: 0 auto 0 0;
  overflow: hidden;
  color: #f59e0b;
  white-space: nowrap;
}

.team-rating-score {
  font-weight: 800;
  color: var(--desk-ink);
}

.team-metrics {
  display: grid;
  gap: 4px;
  margin-top: 8px;
}

.team-metrics small {
  font-size: 11px;
}

.team-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

/* Overview preserved */
.hq-report-grid,
.hq-report-lower {
  display: grid;
  gap: 14px;
}

.hq-report-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.hq-report-lower {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.hq-report-card {
  min-height: 132px;
  padding: 18px;
  border-radius: 12px;
  display: grid;
  align-content: space-between;
  background: var(--surface, #fff);
  border: 1px solid var(--line);
}

.hq-report-card .iconly-shell {
  color: var(--jade-strong);
}

.hq-report-card strong {
  color: var(--primary);
  font-size: 24px;
  overflow-wrap: anywhere;
}

.hq-report-card small,
.hq-segment-row span {
  color: var(--muted);
}

.hq-create-form {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.hq-create-submit {
  align-self: end;
  min-height: 48px;
}

.hq-segment-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.hq-segment-row {
  min-height: 54px;
  padding: 12px 14px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(36, 59, 107, 0.08);
}

/* Modals */
.hq-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.42);
}

.hq-modal {
  width: min(440px, 100%);
  display: grid;
  gap: 14px;
  padding: 22px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid var(--desk-line);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}

.hq-modal h3 {
  margin: 0;
  color: var(--desk-ink);
}

.hq-modal p {
  margin: 0;
  color: var(--desk-muted);
  line-height: 1.8;
  font-size: 13px;
}

.hq-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1120px) {
  .hq-report-grid,
  .hq-report-lower,
  .hq-create-form,
  .hq-team-grid,
  .team-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hq-team-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 980px) {
  .ticket-desk {
    grid-template-columns: 1fr !important;
    height: calc(100dvh - 160px);
  }

  .ticket-desk:not(.ticket-desk-open) .ticket-desk-stage,
  .ticket-desk.ticket-desk-open .ticket-desk-inbox {
    display: none;
  }

  .ticket-back-btn {
    display: inline-flex;
    grid-column: 1 / -1;
    justify-self: start;
    padding-inline: 0;
  }

  .ticket-stage-head {
    grid-template-columns: 1fr;
  }

  .ticket-stage-controls {
    width: 100%;
  }

  .ticket-stage-controls label {
    flex: 1;
    min-width: 0;
  }

  .ticket-action-card,
  .ticket-action-card.wallet {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .hq-report-grid,
  .hq-report-lower,
  .hq-create-form,
  .team-grid {
    grid-template-columns: 1fr;
  }

  .ticket-desk-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .ticket-stat strong {
    font-size: 16px;
  }
}
</style>
