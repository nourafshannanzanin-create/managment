<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, reactive, watch } from 'vue'

import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import InfiniteScrollSentinel from '../components/InfiniteScrollSentinel.vue'
import { formatAmountInput } from '../utils/amount'
import { formatJalali, getTodayJalali } from '../utils/jalali'
import { useInfiniteList } from '../composables/useInfiniteList'
import { useWorkflowHub } from '../stores/workflowHub'

const CARD_NUMBER = '6274121774209571'
const CARD_HOLDER = 'کارنومند'
const PAYMENT_SUBJECT = 'درخواست واریز کیف پول'

const { state, loadWalletDashboard, loadWalletOptions, loadMoreWalletTransactions, submitWalletTransaction, submitFeaturePurchase, payFeatureInstallment, createSupportTicket } = useWorkflowHub()

const transactionForm = reactive({
  open: false,
  direction: 'in',
  walletId: '',
  amount: '',
  note: '',
  destinationType: 'bank',
  targetWalletId: '',
  iban: '',
})

const paymentSetup = reactive({
  open: false,
  walletId: '',
  amount: '',
  purpose: '',
  method: 'card_to_card',
})

const paymentGuide = reactive({
  open: false,
  walletId: '',
  amount: '',
  purpose: '',
  method: 'card_to_card',
})

const paymentForm = reactive({
  open: false,
  walletId: '',
  amount: '',
  purpose: '',
  method: 'card_to_card',
  date: '',
  time: '',
  referenceCode: '',
  receipt: null,
})

const purchaseForm = reactive({
  open: false,
  featureKey: '',
  paymentPlan: 'cash',
  walletId: '',
})

const optionDetail = reactive({
  open: false,
  featureKey: '',
})

const canUseWallet = computed(() => state.currentUser.isManager || state.currentUser.canUseHq)
const isSchematicWallet = computed(() => Boolean(state.wallet.schematic))
const needsOrganization = computed(() => state.currentUser.isHq && !state.hq.selectedOrganizationId)
const wallets = computed(() => state.wallet.wallets || [])
const mainWallets = computed(() => wallets.value.filter((item) => item.key === 'main'))
const transactions = computed(() => state.wallet.transactions || [])
const purchaseOptions = computed(() => state.wallet.options || [])
const licenseStatus = computed(() => state.currentUser.licenseStatus || state.wallet.licenseStatus || {})
const licenseLocked = computed(() => Boolean(licenseStatus.value?.isLocked || licenseStatus.value?.is_locked))
const activeWallet = computed(() => {
  const activeId = transactionForm.walletId || paymentSetup.walletId || paymentGuide.walletId || paymentForm.walletId || purchaseForm.walletId
  return wallets.value.find((item) => String(item.id) === String(activeId)) || wallets.value[0] || null
})
const selectedPurchaseOption = computed(() =>
  purchaseOptions.value.find((item) => (item.featureKey || item.feature_key) === purchaseForm.featureKey) || null,
)
const selectedOptionDetail = computed(() =>
  purchaseOptions.value.find((item) => (item.featureKey || item.feature_key) === optionDetail.featureKey) || null,
)
const purchasePayNowAmount = computed(() => {
  const option = selectedPurchaseOption.value
  if (!option) return 0
  if (purchaseForm.paymentPlan === 'cash') return Number(option.totalAmountRaw || 0)
  return Number(option.upfrontAmountRaw || option.monthlyInstallmentAmountRaw || 0)
})
const purchasePayNowLabel = computed(() =>
  new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 0 }).format(purchasePayNowAmount.value || 0),
)
const purchaseWallet = computed(() =>
  wallets.value.find((item) => String(item.id) === String(purchaseForm.walletId)) || activeWallet.value,
)
const usesManagerPaymentFlow = computed(() => state.currentUser.isManager && !state.currentUser.canUseHq)

const overdueInstallmentOptions = computed(() =>
  purchaseOptions.value.filter(
    (item) => item.installmentIsDue || item.installment_is_due || item.installmentIsLocked || item.installment_is_locked,
  ),
)

function optionCatalogDisabled(option) {
  return Boolean(option.disabled || option.isDisabled || option.is_disabled)
}

function optionInstallmentLocked(option) {
  return Boolean(option.installmentIsLocked || option.installment_is_locked)
}

function optionDisabled(option) {
  return optionCatalogDisabled(option) || optionInstallmentLocked(option)
}

function optionKey(option) {
  return String(option?.featureKey || option?.feature_key || '')
}

function optionField(option, camelKey, snakeKey = '') {
  if (!option) return ''
  const snake = snakeKey || camelKey.replace(/[A-Z]/g, (ch) => `_${ch.toLowerCase()}`)
  const value = option[camelKey] ?? option[snake]
  if (value == null) return ''
  return String(value).trim()
}

const isCeoUser = computed(() => {
  const user = state.currentUser || {}
  return Boolean(user.accessRole === 'admin' || user.isHq || user.canUseHq)
})

/** مدیرعامل همه متن‌ها را می‌بیند؛ مدیر همان بخش هم متن مربوط به سرویس خودش را می‌بیند. */
function canSeeOptionTexts(option) {
  const user = state.currentUser || {}
  if (!user.isManager && !user.canUseHq && !user.isHq && user.accessRole !== 'admin') return false
  if (isCeoUser.value) return true

  const key = optionKey(option)
  if (key === 'accounting') return Boolean(user.canAccessExpenses || user.isManager)
  if (key === 'attendance') return Boolean(user.canViewReports || user.canEditWorkTimes || user.isManager)
  if (key === 'cloud_storage') return Boolean(user.canAccessSettings || user.isManager)
  // core_software و سایر سرویس‌ها: مدیران کیف پول
  return Boolean(user.isManager)
}

function optionSubtitle(option) {
  return optionField(option, 'subtitle')
}

function optionDescription(option) {
  return optionField(option, 'description')
}

function optionRetention(option) {
  return optionField(option, 'retentionSummary', 'retention_summary')
}

function optionIcon(option) {
  const key = optionKey(option)
  if (key === 'cloud_storage') return 'cloud'
  if (key === 'attendance') return 'badge'
  if (key === 'accounting') return 'receipt_long'
  if (key === 'core_software' || key === 'software' || key === 'license' || key === 'core') return 'workspace_premium'
  return 'shopping_cart'
}

function optionTone(option) {
  const key = optionKey(option)
  if (key === 'cloud_storage') return 'cloud'
  if (key === 'attendance') return 'attendance'
  if (key === 'accounting') return 'accounting'
  return 'software'
}

function optionStatus(option) {
  if (option.installmentIsLocked || option.installment_is_locked) return 'قفل شده'
  if (optionDisabled(option)) return optionField(option, 'disabledLabel', 'disabled_label') || 'غیرفعال'
  if (option.required) return 'اجباری'
  if (option.isActive || option.is_active) return 'فعال'
  return optionField(option, 'statusLabel', 'status_label') || 'قابل خرید'
}

function openOptionDetail(option) {
  optionDetail.featureKey = option.featureKey || option.feature_key || ''
  optionDetail.open = true
  state.wallet.error = ''
  state.wallet.message = ''
}

function closeOptionDetail() {
  optionDetail.open = false
  optionDetail.featureKey = ''
}

async function submitInstallmentPayment(option) {
  const key = option.featureKey || option.feature_key
  if (!key) return
  await payFeatureInstallment(key)
}

const paymentMethods = [
  { key: 'pos', label: 'دستگاه کارتخوان' },
  { key: 'card_to_card', label: 'کارت به کارت' },
  { key: 'app', label: 'اپلیکیشن' },
]

const shortcuts = computed(() => {
  if (isSchematicWallet.value) return []
  return [
    { label: 'واریز', icon: 'add_card', direction: 'in', tone: 'deposit' },
    { label: 'برداشت', icon: 'payments', direction: 'out', tone: 'withdraw' },
  ]
})

const summaryCards = computed(() => [
  { label: 'کل موجودی', value: state.wallet.summary.totalBalance, icon: 'account_balance_wallet', tone: 'primary' },
  { label: 'کیف اصلی', value: state.wallet.summary.mainBalance, icon: 'account_balance', tone: 'main' },
  { label: 'کیف پیامک', value: state.wallet.summary.smsBalance, icon: 'sms', tone: 'sms' },
  { label: 'جمع واریزی', value: state.wallet.summary.depositsTotal, icon: 'south_west', tone: 'deposit' },
])

const selectedPaymentMethodLabel = computed(
  () => paymentMethods.find((item) => item.key === paymentForm.method)?.label || 'کارت به کارت',
)

function nowParts() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return {
    date: formatJalali(getTodayJalali()),
    time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
  }
}

function openTransaction(direction) {
  if (isSchematicWallet.value) {
    state.wallet.error = ''
    state.wallet.message = state.wallet.schematicNotice || 'کیف پول این مجموعه صرفاً نمایشی است.'
    return
  }
  state.wallet.error = ''
  state.wallet.message = ''

  const walletId = activeWallet.value?.id ? String(activeWallet.value.id) : ''
  if (direction === 'in' && usesManagerPaymentFlow.value) {
    paymentSetup.walletId = walletId
    paymentSetup.amount = ''
    paymentSetup.purpose = ''
    paymentSetup.method = 'card_to_card'
    paymentSetup.open = true
    return
  }

  transactionForm.direction = direction
  transactionForm.walletId = walletId
  transactionForm.amount = ''
  transactionForm.note = ''
  transactionForm.destinationType = 'bank'
  transactionForm.targetWalletId = wallets.value.find((item) => String(item.id) !== String(walletId))?.id || ''
  transactionForm.iban = ''
  transactionForm.open = true
}

function closeTransaction() {
  transactionForm.open = false
}

function closePaymentSetup() {
  paymentSetup.open = false
}

function closePaymentGuide() {
  paymentGuide.open = false
}

function closePaymentForm() {
  paymentForm.open = false
  paymentForm.walletId = ''
  paymentForm.amount = ''
  paymentForm.purpose = ''
  paymentForm.method = 'card_to_card'
  paymentForm.date = ''
  paymentForm.time = ''
  paymentForm.referenceCode = ''
  paymentForm.receipt = null
}

function openPurchase(option, paymentPlan = 'cash') {
  if (isSchematicWallet.value) {
    state.wallet.error = ''
    state.wallet.message = state.wallet.schematicNotice || 'کیف پول این مجموعه صرفاً نمایشی است.'
    return
  }
  state.wallet.error = ''
  state.wallet.message = ''
  purchaseForm.featureKey = option.featureKey || option.feature_key
  purchaseForm.paymentPlan = paymentPlan
  purchaseForm.walletId = activeWallet.value?.id ? String(activeWallet.value.id) : ''
  purchaseForm.open = true
  optionDetail.open = false
}

async function payInstallmentFromDetail(option) {
  await submitInstallmentPayment(option)
  if (!state.wallet.error) closeOptionDetail()
}

function closePurchase() {
  purchaseForm.open = false
  purchaseForm.featureKey = ''
  purchaseForm.paymentPlan = 'cash'
  purchaseForm.walletId = ''
}

function continuePaymentFlow() {
  if (paymentSetup.method === 'card_to_card') {
    paymentGuide.walletId = paymentSetup.walletId
    paymentGuide.amount = paymentSetup.amount
    paymentGuide.purpose = paymentSetup.purpose
    paymentGuide.method = paymentSetup.method
    paymentGuide.open = true
    paymentSetup.open = false
    return
  }

  openPaymentForm()
}

function openPaymentForm() {
  const current = nowParts()
  paymentGuide.open = false
  paymentSetup.open = false
  paymentForm.walletId = paymentGuide.walletId || paymentSetup.walletId || (activeWallet.value?.id ? String(activeWallet.value.id) : '')
  paymentForm.amount = paymentGuide.amount || paymentSetup.amount || ''
  paymentForm.purpose = paymentGuide.purpose || paymentSetup.purpose || ''
  paymentForm.method = paymentGuide.method || paymentSetup.method || 'card_to_card'
  paymentForm.date = current.date
  paymentForm.time = current.time
  paymentForm.referenceCode = ''
  paymentForm.receipt = null
  paymentForm.open = true
}

function setReceipt(event) {
  paymentForm.receipt = event.target.files?.[0] || null
}

async function submitTransaction() {
  if (usesManagerPaymentFlow.value) {
    const sourceWallet = wallets.value.find((item) => String(item.id) === String(transactionForm.walletId))
    const targetWallet = wallets.value.find((item) => String(item.id) === String(transactionForm.targetWalletId))
    const actionType = transactionForm.direction === 'in' ? 'wallet_deposit' : 'wallet_withdrawal'
    const actionLabel = transactionForm.direction === 'in' ? 'واریز' : 'برداشت'
    const message = [
      `ACTION_TYPE: ${actionType}`,
      `SOURCE_WALLET_ID: ${sourceWallet?.id || ''}`,
      `SOURCE_WALLET_NAME: ${sourceWallet?.name || '-'}`,
      `DESTINATION_TYPE: ${transactionForm.destinationType}`,
      `TARGET_WALLET_ID: ${transactionForm.destinationType === 'wallet' ? targetWallet?.id || '' : ''}`,
      `TARGET_WALLET_NAME: ${transactionForm.destinationType === 'wallet' ? targetWallet?.name || '-' : ''}`,
      `IBAN: ${transactionForm.destinationType === 'bank' ? transactionForm.iban || '-' : ''}`,
      `AMOUNT: ${transactionForm.amount}`,
      `NOTE: ${transactionForm.note || '-'}`,
    ].join('\n')
    await createSupportTicket({ subject: PAYMENT_SUBJECT, message, category: 'financial', priority: 'urgent', attachments: [] })
    state.wallet.message = `درخواست ${actionLabel} برای پشتیبانی ارسال شد.`
    closeTransaction()
    return
  }
  await submitWalletTransaction({
    direction: transactionForm.direction,
    walletId: Number(transactionForm.walletId),
    amount: transactionForm.amount,
    note: transactionForm.note,
  })
  closeTransaction()
}

async function submitPaymentTicket() {
  const wallet = wallets.value.find((item) => String(item.id) === String(paymentForm.walletId)) || activeWallet.value
  const message = [
    'ACTION_TYPE: wallet_payment',
    `WALLET_ID: ${wallet?.id || ''}`,
    `WALLET_NAME: ${wallet?.name || '-'}`,
    `METHOD: ${selectedPaymentMethodLabel.value}`,
    `PURPOSE: ${paymentForm.purpose || '-'}`,
    `DATE: ${paymentForm.date}`,
    `TIME: ${paymentForm.time}`,
    `AMOUNT: ${paymentForm.amount}`,
    `REFERENCE_CODE: ${paymentForm.referenceCode}`,
    ...(paymentForm.method === 'card_to_card'
      ? [`DESTINATION_CARD: ${CARD_NUMBER}`, `CARD_OWNER: ${CARD_HOLDER}`]
      : []),
  ].join('\n')

  state.wallet.error = ''
  try {
    await createSupportTicket({
      subject: PAYMENT_SUBJECT,
      message,
      category: 'financial',
      priority: 'urgent',
      attachments: paymentForm.receipt ? [paymentForm.receipt] : [],
    })
    state.wallet.message = 'درخواست واریز برای HQ ارسال شد.'
    closePaymentForm()
  } catch {
    state.wallet.error = state.support.error || 'ارسال درخواست واریز ناموفق بود.'
  }
}

const ledgerItems = computed(() => [...transactions.value].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)))
const transactionsPaging = computed(() => state.wallet.transactionsPaging || { total: 0, hasMore: false, loading: false })

const {
  items: visibleLedgerItems,
  hasMore: hasMoreLedger,
  loadingMore: loadingMoreLedger,
  loadMore: loadMoreLedger,
} = useInfiniteList(ledgerItems, {
  hasMoreRemote: computed(() => Boolean(transactionsPaging.value.hasMore)),
  onLoadMore: () => loadMoreWalletTransactions(),
})

async function submitPurchase() {
  const option = selectedPurchaseOption.value
  if (!option) return
  await submitFeaturePurchase({
    featureKey: option.featureKey || option.feature_key,
    paymentPlan: purchaseForm.paymentPlan,
    walletId: Number(purchaseForm.walletId),
    paidAmount: purchasePayNowAmount.value,
  })
  if (!state.wallet.error) closePurchase()
}

onMounted(() => {
  void loadWalletDashboard(true)
  void loadWalletOptions(true)
})

watch(
  () => state.hq.selectedOrganizationId,
  () => {
    if (state.currentUser.isHq) void loadWalletDashboard(true)
  },
)
</script>

<template>
  <section class="wallet-page">
    <div v-if="!canUseWallet" class="wallet-empty">
      <IconlyIcon name="lock" decorative />
    </div>

    <div v-else-if="needsOrganization" class="wallet-empty">
      <IconlyIcon name="corporate_fare" decorative />
    </div>

    <template v-else>
      <div class="wallet-hero">
        <div class="wallet-hero-visual" aria-hidden="true">
          <span class="wallet-orb wallet-orb-a"></span>
          <span class="wallet-orb wallet-orb-b"></span>
          <span class="wallet-orb wallet-orb-c"></span>
          <span class="wallet-hero-shine"></span>
          <span class="wallet-hero-grid"></span>
        </div>
        <div class="wallet-hero-balance">
          <div class="wallet-hero-top">
            <div class="wallet-hero-icon">
              <IconlyIcon name="account_balance_wallet" decorative />
            </div>
            <div class="wallet-hero-labels">
              <span class="wallet-hero-eyebrow">کیف پول سازمانی</span>
              <small>{{ state.wallet.organization?.name || state.currentUser.organization }}</small>
            </div>
            <span class="wallet-hero-chip">به‌روز</span>
          </div>
          <p class="wallet-hero-caption">موجودی قابل استفاده</p>
          <strong class="wallet-hero-amount">{{ state.wallet.summary.totalBalance }}</strong>
          <div class="wallet-hero-meta">
            <span>
              <IconlyIcon name="trending_up" decorative />
              واریزها {{ state.wallet.summary.depositsTotal || '—' }}
            </span>
            <span>
              <IconlyIcon name="sms" decorative />
              پیامک {{ state.wallet.summary.smsBalance || '—' }}
            </span>
          </div>
        </div>

        <div v-if="shortcuts.length" class="wallet-actions">
          <button
            v-for="item in shortcuts"
            :key="item.direction"
            :class="['wallet-action', item.tone]"
            type="button"
            @click="openTransaction(item.direction)"
          >
            <span class="wallet-action-icon">
              <IconlyIcon :name="item.icon" decorative />
            </span>
            <span class="wallet-action-copy">
              <b>{{ item.label }}</b>
              <small>{{ item.direction === 'in' ? 'افزایش موجودی' : 'برداشت از حساب' }}</small>
            </span>
          </button>
        </div>
      </div>

      <div v-if="isSchematicWallet" class="wallet-license-alert wallet-trial-alert">
        <IconlyIcon name="info" decorative />
        <div>
          <strong>کیف پول نمایشی</strong>
          <small>{{ state.wallet.schematicNotice || 'اعداد صرفاً برای نمایش هستند؛ واریز و برداشت واقعی انجام نمی‌شود.' }}</small>
        </div>
      </div>

      <div v-if="state.wallet.error || state.wallet.message" class="wallet-alert" :class="{ danger: state.wallet.error }">
        {{ state.wallet.error || state.wallet.message }}
      </div>

      <div v-if="licenseLocked" class="wallet-license-alert">
        <IconlyIcon name="lock" decorative />
        <div>
          <strong>حساب کاربری به دلیل اتمام اعتبار قفل شده است.</strong>
          <small>{{ licenseStatus.notice || 'برای تمدید دسترسی، یکی از گزینه‌های پایین را از کیف پول خریداری کنید.' }}</small>
        </div>
      </div>

      <div
        v-else-if="licenseStatus.trialActive || licenseStatus.trial_active"
        class="wallet-license-alert wallet-trial-alert"
      >
        <IconlyIcon name="calendar" decorative />
        <div>
          <strong>استفاده رایگان فعال است.</strong>
          <small>{{ licenseStatus.notice || 'پس از پایان مهلت رایگان، برای ادامه باید خرید نرم‌افزار ثبت شود.' }}</small>
        </div>
      </div>

      <div v-if="overdueInstallmentOptions.length" class="wallet-license-alert wallet-installment-alert">
        <IconlyIcon name="warning" decorative />
        <div>
          <strong>یادآوری پرداخت قسط</strong>
          <small
            v-for="option in overdueInstallmentOptions"
            :key="option.featureKey || option.feature_key"
          >
            {{ option.installmentLockNotice || option.installment_lock_notice || option.title }}
            · سررسید: {{ option.nextInstallmentDueAt || option.next_installment_due_at || '—' }}
            · مبلغ: {{ option.nextInstallmentAmount || option.next_installment_amount || '—' }}
          </small>
        </div>
      </div>

      <div class="wallet-summary-grid">
        <article v-for="(card, index) in summaryCards" :key="card.label" :class="['wallet-summary-card', card.tone]" :style="{ '--i': index }">
          <div class="wallet-summary-icon">
            <IconlyIcon :name="card.icon" decorative />
          </div>
          <small>{{ card.label }}</small>
          <strong>{{ card.value }}</strong>
          <span class="wallet-summary-glow" aria-hidden="true"></span>
        </article>
      </div>

      <div v-if="purchaseOptions.length" class="wallet-options-section">
        <header class="wallet-section-head options-head">
          <div>
            <span>سرویس‌ها و قابلیت‌ها</span>
            <small class="options-head-desktop-hint">جزئیات و خرید روی همان کارت</small>
            <small class="options-head-mobile-hint">برای جزئیات روی کارت بزنید</small>
          </div>
          <b>{{ purchaseOptions.length }}</b>
        </header>

        <div class="wallet-options-grid wallet-options-desktop">
          <article
            v-for="(option, index) in purchaseOptions"
            :key="`desktop-${option.featureKey || option.feature_key}`"
            class="wallet-option-card"
            :class="[
              optionTone(option),
              {
                active: option.isActive || option.is_active,
                disabled: optionCatalogDisabled(option),
                locked: optionInstallmentLocked(option),
                purchased: (option.isActive || option.is_active) && !optionCatalogDisabled(option),
              },
            ]"
            :style="{ '--i': index, '--option-accent': option.accent || '#34908b' }"
          >
            <div class="wallet-option-card-head">
              <span class="wallet-option-card-icon">
                <IconlyIcon :name="optionIcon(option)" decorative />
              </span>
              <div class="wallet-option-card-titles">
                <strong>{{ option.title }}</strong>
                <em v-if="canSeeOptionTexts(option) && optionSubtitle(option)">{{ optionSubtitle(option) }}</em>
              </div>
              <span class="wallet-option-card-status">{{ optionStatus(option) }}</span>
            </div>

            <p
              v-if="canSeeOptionTexts(option) && optionDescription(option)"
              class="wallet-option-card-desc"
            >{{ optionDescription(option) }}</p>
            <p
              v-if="canSeeOptionTexts(option) && optionRetention(option)"
              class="wallet-option-card-retention"
            >{{ optionRetention(option) }}</p>

            <div v-if="!optionDisabled(option) && !(option.isActive || option.is_active)" class="wallet-option-price-stack">
              <div>
                <small>نقدی</small>
                <strong>{{ option.cashAmount || option.totalAmount || '—' }}</strong>
              </div>
              <div v-if="option.installmentMonths || option.installment_months">
                <small>قسط ماهانه</small>
                <strong>{{ option.monthlyInstallmentAmount || option.monthly_installment_amount }}</strong>
                <em>{{ option.installmentMonths || option.installment_months }} ماه</em>
              </div>
            </div>

            <div v-if="option.isActive || option.is_active" class="wallet-option-live">
              <div>
                <small>پرداخت‌شده</small>
                <strong>{{ option.paidAmount || option.paid_amount }}</strong>
              </div>
              <div>
                <small>مانده</small>
                <strong>{{ option.remainingAmount || option.remaining_amount }}</strong>
              </div>
              <div v-if="option.nextInstallmentDueAt || option.next_installment_due_at">
                <small>سررسید بعدی</small>
                <strong>{{ option.nextInstallmentDueAt || option.next_installment_due_at }}</strong>
              </div>
              <div class="wallet-option-progress">
                <span :style="{ width: `${option.progressPercent || option.progress_percent || 0}%` }" />
              </div>
            </div>

            <div v-if="optionInstallmentLocked(option)" class="wallet-option-lock-note">
              <strong>قفل به‌خاطر قسط پرداخت‌نشده</strong>
              <small>{{ option.installmentLockNotice || option.installment_lock_notice || 'موجودی کافی نبود؛ دسترسی قفل شد.' }}</small>
            </div>

            <div class="wallet-option-card-actions">
              <template v-if="!isSchematicWallet && !optionCatalogDisabled(option)">
                <button
                  v-if="option.canPayNextInstallment || option.can_pay_next_installment"
                  class="action-btn tone-primary"
                  type="button"
                  :disabled="state.wallet.submitting"
                  @click="submitInstallmentPayment(option)"
                >
                  پرداخت قسط {{ option.nextInstallmentAmount || option.next_installment_amount }}
                </button>
                <template v-else-if="!(option.isActive || option.is_active) && !optionInstallmentLocked(option)">
                  <button class="action-btn tone-soft" type="button" @click="openPurchase(option, 'installment')">خرید قسطی</button>
                  <button class="action-btn tone-primary" type="button" @click="openPurchase(option, 'cash')">خرید نقدی</button>
                </template>
                <span v-else-if="option.isActive || option.is_active" class="wallet-option-active-tag">فعال است</span>
              </template>
              <div v-else-if="isSchematicWallet" class="option-detail-schematic compact">
                <IconlyIcon name="visibility" decorative />
                <b>نمایشی</b>
              </div>
            </div>
          </article>
        </div>

        <div class="wallet-options-grid wallet-options-mobile">
          <button
            v-for="(option, index) in purchaseOptions"
            :key="`mobile-${option.featureKey || option.feature_key}`"
            type="button"
            class="wallet-option-tile"
            :class="[
              optionTone(option),
              {
                active: option.isActive || option.is_active,
                disabled: optionDisabled(option),
                locked: option.installmentIsLocked || option.installment_is_locked,
              },
            ]"
            :style="{ '--i': index }"
            @click="openOptionDetail(option)"
          >
            <span class="wallet-option-tile-icon">
              <IconlyIcon :name="optionIcon(option)" decorative />
            </span>
            <strong>{{ option.title }}</strong>
            <small class="wallet-option-tile-status">{{ optionStatus(option) }}</small>
            <span class="wallet-option-tile-glow" aria-hidden="true"></span>
          </button>
        </div>
      </div>

      <div class="wallet-layout is-ledger-only">
        

        <div class="wallet-ledger">
          <div class="ledger-head">
            <div>
              <span>گردش حساب</span>
              <small>آخرین تراکنش‌ها</small>
            </div>
            <b>{{ transactionsPaging.total || ledgerItems.length }}</b>
          </div>

          <div v-if="state.wallet.loading" class="wallet-loading">
            <IconlyIcon name="progress_activity" decorative />
          </div>

          <div v-else-if="!ledgerItems.length" class="wallet-empty compact">
            <IconlyIcon name="receipt_long" decorative />
            <p>هنوز تراکنشی ثبت نشده است</p>
          </div>

          <div v-else class="ledger-list">
            <article v-for="(item, index) in visibleLedgerItems" :key="item.id" class="ledger-row" :style="{ '--i': index }">
              <div :class="['ledger-icon', item.direction]">
                <IconlyIcon :name="item.direction === 'in' ? 'south_west' : 'north_east'" decorative />
              </div>
              <div>
                <b>{{ item.walletName }}</b>
                <small>{{ item.actor }} · {{ item.time }}</small>
              </div>
              <strong :class="item.direction">{{ item.direction === 'in' ? '+' : '−' }}{{ item.amount }}</strong>
            </article>
            <InfiniteScrollSentinel
              :disabled="!hasMoreLedger || loadingMoreLedger"
              @reach-end="loadMoreLedger"
            >
              <small v-if="loadingMoreLedger" class="list-loading-more">در حال بارگذاری...</small>
              <small v-else-if="hasMoreLedger" class="list-loading-more">برای ادامه اسکرول کنید</small>
            </InfiniteScrollSentinel>
          </div>
        </div>
      </div>
    </template>

    <Teleport to="body">
    <div v-if="transactionForm.open" class="wallet-modal-backdrop" @click.self="closeTransaction">
      <form class="wallet-modal" @submit.prevent="submitTransaction">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <IconlyIcon :name="transactionForm.direction === 'in' ? 'add_card' : 'payments'" decorative />
          <strong>{{ transactionForm.direction === 'in' ? 'واریز به حساب بانکی' : 'برداشت از حساب بانکی' }}</strong>
        </div>

        <label>
          <span>کیف پول</span>
          <select v-model="transactionForm.walletId" required>
            <option v-for="wallet in wallets" :key="wallet.id" :value="wallet.id">{{ wallet.name }}</option>
          </select>
        </label>

        <label>
          <span>مبلغ (تومان)</span>
          <input v-model="transactionForm.amount" inputmode="numeric" required placeholder="0" @input="transactionForm.amount = formatAmountInput($event.target.value)" />
        </label>

        <label>
          <span>توضیحات</span>
          <textarea v-model="transactionForm.note" rows="3"></textarea>
        </label>

        <div v-if="state.wallet.error" class="wallet-alert danger in-modal">
          {{ state.wallet.error }}
        </div>

        <template v-if="usesManagerPaymentFlow">
          <label>
            <span>مقصد</span>
            <select v-model="transactionForm.destinationType">
              <option value="bank">حساب بانکی</option>
              <option value="wallet">کیف پول دیگر</option>
            </select>
          </label>
          <label v-if="transactionForm.destinationType === 'wallet'">
            <span>کیف پول مقصد</span>
            <select v-model="transactionForm.targetWalletId">
              <option v-for="wallet in wallets.filter((item) => String(item.id) !== String(transactionForm.walletId))" :key="wallet.id" :value="wallet.id">{{ wallet.name }}</option>
            </select>
          </label>
          <label v-else>
            <span>شماره شبا</span>
            <input v-model.trim="transactionForm.iban" dir="ltr" placeholder="IR..." required />
          </label>
        </template>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closeTransaction">بستن</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.wallet.submitting">
            <IconlyIcon name="check" decorative />
            ثبت
          </button>
        </div>
      </form>
    </div>

    <div v-if="paymentSetup.open" class="wallet-modal-backdrop" @click.self="closePaymentSetup">
      <form class="wallet-modal payment-request-modal" @submit.prevent="continuePaymentFlow">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <IconlyIcon name="payments" decorative />
          <strong>درخواست پرداخت</strong>
        </div>

        <div class="payment-grid">
          <label>
            <span>کیف پول</span>
            <select v-model="paymentSetup.walletId" required>
              <option v-for="wallet in (usesManagerPaymentFlow ? mainWallets : wallets)" :key="wallet.id" :value="wallet.id">{{ wallet.name }}</option>
            </select>
          </label>
          <label>
            <span>مبلغ (تومان)</span>
            <input v-model.trim="paymentSetup.amount" inputmode="numeric" required placeholder="0" @input="paymentSetup.amount = formatAmountInput($event.target.value)" />
          </label>
        </div>

        <label>
          <span>بابت</span>
          <input v-model.trim="paymentSetup.purpose" required placeholder="مثلا واریز پیامک یا تمدید سرویس" />
        </label>

        <label>
          <span>روش پرداخت</span>
          <select v-model="paymentSetup.method" required>
            <option v-for="method in paymentMethods" :key="method.key" :value="method.key">{{ method.label }}</option>
          </select>
        </label>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePaymentSetup">بستن</button>
          <button class="action-btn tone-primary" type="submit">
            <IconlyIcon name="arrow_back" decorative />
            ادامه
          </button>
        </div>
      </form>
    </div>

    <div v-if="optionDetail.open && selectedOptionDetail" class="wallet-modal-backdrop" @click.self="closeOptionDetail">
      <div class="wallet-modal option-detail-modal" :class="optionTone(selectedOptionDetail)">
        <div class="modal-handle"></div>
        <div class="option-detail-hero">
          <span class="option-detail-icon">
            <IconlyIcon :name="optionIcon(selectedOptionDetail)" decorative />
          </span>
          <div class="option-detail-copy">
            <small>{{ optionStatus(selectedOptionDetail) }}</small>
            <strong>{{ selectedOptionDetail.title }}</strong>
            <em
              v-if="canSeeOptionTexts(selectedOptionDetail) && optionSubtitle(selectedOptionDetail)"
              class="option-detail-subtitle"
            >{{ optionSubtitle(selectedOptionDetail) }}</em>
          </div>
          <button class="option-detail-close" type="button" aria-label="بستن" @click="closeOptionDetail">
            <IconlyIcon name="close" decorative />
          </button>
        </div>

        <div
          v-if="canSeeOptionTexts(selectedOptionDetail) && (optionDescription(selectedOptionDetail) || optionRetention(selectedOptionDetail))"
          class="option-detail-texts"
        >
          <p v-if="optionDescription(selectedOptionDetail)" class="option-detail-desc">
            {{ optionDescription(selectedOptionDetail) }}
          </p>
          <p v-if="optionRetention(selectedOptionDetail)" class="option-detail-retention">
            {{ optionRetention(selectedOptionDetail) }}
          </p>
        </div>

        <template v-if="!optionDisabled(selectedOptionDetail)">
          <div class="option-detail-prices">
            <article>
              <small>نقدی</small>
              <strong>{{ selectedOptionDetail.cashAmount || selectedOptionDetail.cash_amount || selectedOptionDetail.totalAmount || selectedOptionDetail.total_amount || '—' }}</strong>
            </article>
            <article v-if="selectedOptionDetail.upfrontAmount || selectedOptionDetail.upfront_amount">
              <small>پیش‌پرداخت</small>
              <strong>{{ selectedOptionDetail.upfrontAmount || selectedOptionDetail.upfront_amount }}</strong>
            </article>
            <article v-if="selectedOptionDetail.installmentMonths || selectedOptionDetail.installment_months">
              <small>اقساط</small>
              <strong>{{ selectedOptionDetail.monthlyInstallmentAmount || selectedOptionDetail.monthly_installment_amount }} / {{ selectedOptionDetail.installmentMonths || selectedOptionDetail.installment_months }} ماه</strong>
            </article>
            <article v-if="selectedOptionDetail.annualSubscriptionAmountRaw">
              <small>اشتراک سالانه</small>
              <strong>{{ selectedOptionDetail.annualSubscriptionAmount }}</strong>
            </article>
          </div>

          <div v-if="selectedOptionDetail.isActive || selectedOptionDetail.is_active" class="option-detail-live">
            <article>
              <small>پرداخت‌شده</small>
              <strong>{{ selectedOptionDetail.paidAmount || selectedOptionDetail.paid_amount }}</strong>
            </article>
            <article>
              <small>مانده</small>
              <strong>{{ selectedOptionDetail.remainingAmount || selectedOptionDetail.remaining_amount }}</strong>
            </article>
            <article v-if="selectedOptionDetail.nextInstallmentDueAt || selectedOptionDetail.next_installment_due_at">
              <small>سررسید بعدی</small>
              <strong>{{ selectedOptionDetail.nextInstallmentDueAt || selectedOptionDetail.next_installment_due_at }}</strong>
            </article>
          </div>

          <div v-if="state.wallet.error" class="wallet-alert danger in-modal">
            {{ state.wallet.error }}
          </div>

          <div class="modal-actions option-detail-actions">
            <button class="action-btn tone-soft" type="button" @click="closeOptionDetail">بستن</button>
            <template v-if="!isSchematicWallet">
              <button
                v-if="selectedOptionDetail.canPayNextInstallment || selectedOptionDetail.can_pay_next_installment"
                class="action-btn tone-primary"
                type="button"
                :disabled="state.wallet.submitting"
                @click="payInstallmentFromDetail(selectedOptionDetail)"
              >
                پرداخت قسط {{ selectedOptionDetail.nextInstallmentAmount || selectedOptionDetail.next_installment_amount }}
              </button>
              <template v-else-if="!(selectedOptionDetail.isActive || selectedOptionDetail.is_active)">
                <button
                  class="action-btn tone-soft"
                  type="button"
                  :disabled="state.wallet.submitting"
                  @click="openPurchase(selectedOptionDetail, 'installment')"
                >
                  خرید قسطی
                </button>
                <button
                  class="action-btn tone-primary"
                  type="button"
                  :disabled="state.wallet.submitting"
                  @click="openPurchase(selectedOptionDetail, 'cash')"
                >
                  <IconlyIcon name="shopping_cart_checkout" decorative />
                  خرید نقدی
                </button>
              </template>
            </template>
            <div v-else class="option-detail-schematic">
              <IconlyIcon name="visibility" decorative />
              <b>نمایشی — بدون خرید واقعی</b>
            </div>
          </div>
        </template>

        <div v-else class="option-detail-locked">
          <IconlyIcon name="lock" decorative />
          <div>
            <strong>
              {{
                optionInstallmentLocked(selectedOptionDetail)
                  ? (selectedOptionDetail.installmentLockNotice || selectedOptionDetail.installment_lock_notice || 'این بخش به دلیل عدم پرداخت قسط قفل شده است.')
                  : (selectedOptionDetail.disabledLabel || selectedOptionDetail.disabled_label || 'فعلا غیرفعال است')
              }}
            </strong>
          </div>
          <button class="action-btn tone-soft" type="button" @click="closeOptionDetail">بستن</button>
        </div>
      </div>
    </div>

    <div v-if="purchaseForm.open && selectedPurchaseOption" class="wallet-modal-backdrop" @click.self="closePurchase">
      <form class="wallet-modal purchase-modal" @submit.prevent="submitPurchase">
        <div class="modal-handle"></div>
        <div class="purchase-modal-head">
          <IconlyIcon name="workspace_premium" decorative />
          <div>
            <small>خرید قابلیت از کیف پول</small>
            <strong>{{ selectedPurchaseOption.title }}</strong>
          </div>
        </div>

        <p class="purchase-copy">{{ selectedPurchaseOption.description }}</p>
        <p v-if="selectedPurchaseOption.retentionSummary || selectedPurchaseOption.retention_summary" class="purchase-copy retention">
          {{ selectedPurchaseOption.retentionSummary || selectedPurchaseOption.retention_summary }}
        </p>

        <div class="purchase-plan-toggle">
          <button type="button" :class="{ active: purchaseForm.paymentPlan === 'cash' }" @click="purchaseForm.paymentPlan = 'cash'">
            <IconlyIcon name="payments" decorative />
            <b>نقدی</b>
            <small>{{ selectedPurchaseOption.cashAmount || selectedPurchaseOption.totalAmount }}</small>
          </button>
          <button type="button" :class="{ active: purchaseForm.paymentPlan === 'installment' }" @click="purchaseForm.paymentPlan = 'installment'">
            <IconlyIcon name="calendar_month" decorative />
            <b>قسطی</b>
            <small>{{ selectedPurchaseOption.upfrontAmount || selectedPurchaseOption.monthlyInstallmentAmount }} تومان</small>
          </button>
        </div>

        <div class="purchase-details-grid">
          <article>
            <small>پرداخت امروز</small>
            <strong>{{ purchasePayNowLabel }}</strong>
          </article>
          <article>
            <small>اقساط</small>
            <strong>{{ selectedPurchaseOption.monthlyInstallmentAmount }} / {{ selectedPurchaseOption.installmentMonths }} ماه</strong>
          </article>
          <article v-if="selectedPurchaseOption.annualSubscriptionAmountRaw">
            <small>اشتراک سالانه</small>
            <strong>{{ selectedPurchaseOption.annualSubscriptionAmount }}</strong>
          </article>
        </div>

        <label>
          <span>کیف پول پرداخت</span>
          <select v-model="purchaseForm.walletId" required>
            <option v-for="wallet in mainWallets.length ? mainWallets : wallets" :key="wallet.id" :value="wallet.id">
              {{ wallet.name }} - {{ wallet.balance }}
            </option>
          </select>
        </label>

        <div class="purchase-wallet-box">
          <IconlyIcon name="account_balance_wallet" decorative />
          <div>
            <small>موجودی قابل استفاده</small>
            <strong>{{ purchaseWallet?.balance || '0' }}</strong>
          </div>
        </div>

        <div v-if="state.wallet.error" class="wallet-alert danger in-modal">
          {{ state.wallet.error }}
        </div>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePurchase">بستن</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.wallet.submitting">
            <IconlyIcon name="verified" decorative />
            تایید و پرداخت
          </button>
        </div>
      </form>
    </div>

    <div v-if="paymentGuide.open" class="wallet-modal-backdrop" @click.self="closePaymentGuide">
      <div class="wallet-modal payment-guide-modal">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <IconlyIcon name="credit_card" decorative />
          <strong>پرداخت کارت به کارت</strong>
        </div>

        <div class="payment-summary-box">
          <b>{{ wallets.find((item) => String(item.id) === String(paymentGuide.walletId))?.name || 'کیف پول' }}</b>
          <small>مبلغ: {{ paymentGuide.amount }}</small>
          <small>بابت: {{ paymentGuide.purpose }}</small>
        </div>

        <div class="payment-card-box">
          <small>شماره کارت مقصد</small>
          <strong>{{ CARD_NUMBER }}</strong>
          <span>{{ CARD_HOLDER }}</span>
        </div>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePaymentGuide">بازگشت</button>
          <button class="action-btn tone-primary" type="button" @click="openPaymentForm">
            <IconlyIcon name="verified" decorative />
            ثبت رسید
          </button>
        </div>
      </div>
    </div>

    <div v-if="paymentForm.open" class="wallet-modal-backdrop" @click.self="closePaymentForm">
      <form class="wallet-modal payment-request-modal" @submit.prevent="submitPaymentTicket">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <IconlyIcon name="support_agent" decorative />
          <strong>ثبت اطلاعات رسید پرداخت</strong>
        </div>

        <div class="payment-summary-box">
          <b>{{ PAYMENT_SUBJECT }}</b>
          <small>روش پرداخت: {{ selectedPaymentMethodLabel }}</small>
          <small>بابت: {{ paymentForm.purpose || '-' }}</small>
          <small>اطلاعات رسید را وارد کنید تا پشتیبانی آن را بررسی کند.</small>
        </div>

        <div class="payment-grid">
          <label>
            <span>تاریخ</span>
            <ShamsiDatePicker v-model="paymentForm.date" model-type="jalali" placeholder="1405/04/16" />
          </label>
          <label>
            <span>ساعت</span>
            <input v-model.trim="paymentForm.time" required placeholder="14:35" />
          </label>
          <label>
            <span>مبلغ (تومان)</span>
            <input v-model.trim="paymentForm.amount" inputmode="numeric" required placeholder="0" @input="paymentForm.amount = formatAmountInput($event.target.value)" />
          </label>
          <label>
            <span>کد پیگیری</span>
            <input v-model.trim="paymentForm.referenceCode" required dir="ltr" placeholder="شماره یا کد رسید" />
          </label>
        </div>

        <label>
          <span>تصویر رسید</span>
          <input type="file" accept="image/*,.pdf" @change="setReceipt" />
        </label>

        <div v-if="state.wallet.error" class="wallet-alert danger in-modal">
          {{ state.wallet.error }}
        </div>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePaymentForm">بستن</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.support.submitting">
            <IconlyIcon name="send" decorative />
            ارسال برای HQ
          </button>
        </div>
      </form>
    </div>
    </Teleport>
  </section>
</template>

<style scoped>
.wallet-page {
  --wallet-ink: #143634;
  --wallet-muted: #5f7a77;
  --wallet-line: rgba(52, 144, 139, 0.14);
  --wallet-jade: #34908b;
  --wallet-ease: cubic-bezier(0.22, 1, 0.36, 1);
  display: grid;
  gap: 20px;
  font-size: 13px;
  min-width: 0;
  animation: wallet-page-in 0.55s var(--wallet-ease) both;
}

@keyframes wallet-page-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes wallet-orb-float {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(12px, -10px, 0) scale(1.08); }
}

@keyframes wallet-shine-sweep {
  0% { transform: translateX(-120%) rotate(18deg); opacity: 0; }
  35% { opacity: 0.55; }
  100% { transform: translateX(180%) rotate(18deg); opacity: 0; }
}

@keyframes wallet-pulse-soft {
  0%, 100% { box-shadow: 0 0 0 0 rgba(201, 168, 108, 0.28); }
  50% { box-shadow: 0 0 0 10px rgba(201, 168, 108, 0); }
}

@keyframes wallet-rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

.wallet-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(200px, 0.7fr);
  gap: 22px;
  overflow: hidden;
  min-height: 280px;
  padding: 28px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 28px;
  color: #fff;
  background:
    radial-gradient(ellipse 70% 80% at 100% -10%, rgba(201, 168, 108, 0.28), transparent 55%),
    radial-gradient(ellipse 55% 70% at -5% 110%, rgba(52, 144, 139, 0.55), transparent 50%),
    linear-gradient(145deg, #0b2f2d 0%, #145652 42%, #1f7a72 78%, #34908b 100%);
  box-shadow: none;
}

.wallet-hero-visual {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.wallet-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  animation: wallet-orb-float 8s ease-in-out infinite;
}

.wallet-orb-a {
  width: 180px;
  height: 180px;
  top: -48px;
  left: -36px;
  background: radial-gradient(circle, rgba(201, 168, 108, 0.45), transparent 70%);
}

.wallet-orb-b {
  width: 220px;
  height: 220px;
  right: -40px;
  bottom: -70px;
  background: radial-gradient(circle, rgba(120, 210, 200, 0.35), transparent 68%);
  animation-delay: -2.5s;
}

.wallet-orb-c {
  width: 120px;
  height: 120px;
  top: 38%;
  left: 42%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.16), transparent 70%);
  animation-delay: -4s;
}

.wallet-hero-shine {
  position: absolute;
  inset: -20% -40%;
  width: 40%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.22), transparent);
  animation: wallet-shine-sweep 5.5s var(--wallet-ease) infinite;
}

.wallet-hero-grid {
  position: absolute;
  inset: 0;
  opacity: 0.18;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(circle at 30% 40%, #000 20%, transparent 75%);
}

.wallet-hero-balance,
.wallet-actions,
.wallet-summary-card,
.wallet-tile,
.wallet-ledger,
.wallet-license-alert,
.wallet-option-tile,
.wallet-option-card {
  position: relative;
  z-index: 1;
}

.wallet-hero-balance {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  color: #fff;
}

.wallet-hero-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.wallet-hero-icon {
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  color: #fff;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.06));
  border: 1px solid rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.wallet-hero-labels {
  display: grid;
  gap: 3px;
  flex: 1;
  min-width: 0;
}

.wallet-hero-eyebrow {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: rgba(255, 245, 220, 0.88);
}

.wallet-hero-labels small {
  color: rgba(255, 255, 255, 0.68);
  font-weight: 650;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wallet-hero-chip {
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: #3d2f12;
  background: linear-gradient(135deg, #f0d9a8, #c9a86c);
  box-shadow: 0 8px 18px rgba(201, 168, 108, 0.35);
  animation: wallet-pulse-soft 2.8s ease-in-out infinite;
}

.wallet-hero-caption {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  font-weight: 650;
}

.wallet-hero-amount {
  color: #fff !important;
  font-size: clamp(2.2rem, 5.2vw, 3.8rem) !important;
  font-weight: 850;
  line-height: 1 !important;
  letter-spacing: -0.04em;
  text-shadow: 0 10px 28px rgba(0, 0, 0, 0.25);
  background: linear-gradient(180deg, #ffffff 20%, #f5e6c8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.wallet-hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 4px;
}

.wallet-hero-meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(8px);
  font-size: 11px;
  font-weight: 700;
}

.wallet-hero-meta :deep(.iconly-shell),
.wallet-hero-icon :deep(.iconly-shell),
.wallet-action :deep(.iconly-shell) {
  color: inherit;
}

.wallet-actions {
  display: grid;
  align-content: center;
  gap: 12px;
}

.wallet-action {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 18px;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: transform 0.22s var(--wallet-ease), background 0.22s ease, box-shadow 0.22s ease;
}

.wallet-action:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.18);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
}

.wallet-action.deposit {
  background: linear-gradient(145deg, #14b887 0%, #0d9a72 48%, #087a5c 100%);
  border-color: rgba(200, 255, 230, 0.42);
  color: #fff;
  box-shadow:
    0 12px 28px rgba(13, 154, 114, 0.32),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.wallet-action.withdraw {
  background: linear-gradient(145deg, #ff8f5a 0%, #f06a3d 48%, #d44d28 100%);
  border-color: rgba(255, 230, 210, 0.42);
  color: #fff;
  box-shadow:
    0 12px 28px rgba(240, 106, 61, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.wallet-action.deposit:hover {
  background: linear-gradient(145deg, #1cc994 0%, #10a87d 48%, #0a8665 100%);
  box-shadow:
    0 14px 32px rgba(13, 154, 114, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
  filter: none;
}

.wallet-action.withdraw:hover {
  background: linear-gradient(145deg, #ffa06e 0%, #f5784a 48%, #de5630 100%);
  box-shadow:
    0 14px 32px rgba(240, 106, 61, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
  filter: none;
}

.wallet-action-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.wallet-action.deposit .wallet-action-icon,
.wallet-action.withdraw .wallet-action-icon {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.wallet-action.deposit :deep(.iconly-shell),
.wallet-action.withdraw :deep(.iconly-shell),
.wallet-action.deposit :deep(.iconly-img),
.wallet-action.withdraw :deep(.iconly-img),
.wallet-action-icon :deep(.iconly-shell),
.wallet-action-icon :deep(.iconly-img) {
  --iconly-filter: brightness(0) invert(1) !important;
  filter: brightness(0) invert(1) !important;
}

.wallet-action-copy {
  display: grid;
  gap: 2px;
  text-align: start;
}

.wallet-action-copy b {
  font-size: 0.95rem;
  font-weight: 800;
}

.wallet-action-copy small {
  opacity: 0.78;
  font-weight: 650;
}

.wallet-alert {
  padding: 14px 18px;
  border-radius: 16px;
  color: #1f5c59;
  background: linear-gradient(135deg, rgba(52, 144, 139, 0.12), rgba(52, 144, 139, 0.05));
  border: 1px solid rgba(52, 144, 139, 0.18);
  font-weight: 750;
}

.wallet-alert.danger {
  color: #9b3b2f;
  background: linear-gradient(135deg, #fff5f3, #ffe8e3);
  border-color: rgba(196, 90, 74, 0.2);
}

.wallet-alert.in-modal {
  border-radius: 12px;
  color: #b42318 !important;
  background: #fffbfa !important;
  border: 1px solid #fecdca;
}

.wallet-license-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(196, 125, 42, 0.22);
  border-radius: 18px;
  color: #7a4a12;
  background: linear-gradient(135deg, #fff8ec, #fff2d9);
  animation: wallet-rise 0.5s var(--wallet-ease) both;
}

.wallet-license-alert.wallet-trial-alert {
  border-color: rgba(52, 144, 139, 0.22);
  color: #1f5f5b;
  background: linear-gradient(135deg, #eaf7f4, #d8efe9);
}

.wallet-license-alert.wallet-installment-alert {
  border-color: rgba(196, 90, 74, 0.22);
  color: #8a3a2e;
  background: linear-gradient(135deg, #fff4f1, #ffe6e0);
}

.wallet-license-alert .iconly-shell {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(145deg, #34908b, #1f6f6a);
  flex-shrink: 0;
}

.wallet-license-alert.wallet-installment-alert .iconly-shell {
  background: linear-gradient(145deg, #d97757, #c45a4a);
}

.wallet-license-alert div {
  display: grid;
  gap: 4px;
}

.wallet-options-section {
  display: grid;
  gap: 12px;
}

.wallet-section-head.options-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.wallet-section-head.options-head > div {
  display: grid;
  gap: 2px;
}

.wallet-section-head.options-head span {
  color: var(--wallet-ink);
  font-weight: 850;
}

.wallet-section-head.options-head small {
  color: var(--wallet-muted);
  font-weight: 650;
}

.wallet-section-head.options-head b {
  min-width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(145deg, #1f6f6a, #34908b);
  font-weight: 800;
}

.wallet-options-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.wallet-options-desktop {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.wallet-options-mobile {
  display: none;
}

.options-head-mobile-hint { display: none; }
.options-head-desktop-hint { display: block; }

.wallet-option-card {
  --option-accent: #34908b;
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 18px;
  background: linear-gradient(165deg, #fffaf5, #ffffff);
  box-shadow: 0 8px 22px rgba(20, 70, 66, 0.06);
  animation: wallet-rise 0.5s var(--wallet-ease) both;
  animation-delay: calc(var(--i, 0) * 55ms);
}

.wallet-option-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: var(--option-accent);
}

.wallet-option-card.purchased,
.wallet-option-card.active {
  background: linear-gradient(165deg, #f0fdf4, #ffffff);
  border-color: rgba(22, 163, 74, 0.22);
}

.wallet-option-card.locked {
  background: linear-gradient(165deg, #fef2f2, #ffffff);
  border-color: rgba(185, 28, 28, 0.2);
}

.wallet-option-card.disabled {
  opacity: 0.78;
  background: #f8fafc;
}

.wallet-option-card-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.wallet-option-card-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex: 0 0 42px;
  border-radius: 12px;
  color: var(--option-accent);
  background: color-mix(in srgb, var(--option-accent) 12%, #fff);
  border: 1px solid color-mix(in srgb, var(--option-accent) 22%, transparent);
}

.wallet-option-card-titles {
  display: grid;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.wallet-option-card-titles strong {
  font-size: 1rem;
  font-weight: 850;
  color: var(--wallet-ink);
}

.wallet-option-card-titles em {
  font-style: normal;
  color: var(--wallet-muted);
  font-size: 0.78rem;
  font-weight: 650;
  line-height: 1.5;
}

.wallet-option-card-status {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
  font-size: 10px;
  font-weight: 800;
  white-space: nowrap;
}

.wallet-option-card.purchased .wallet-option-card-status,
.wallet-option-card.active .wallet-option-card-status {
  background: #dcfce7;
  color: #166534;
}

.wallet-option-card.locked .wallet-option-card-status {
  background: #fee2e2;
  color: #991b1b;
}

.wallet-option-card-desc,
.wallet-option-card-retention {
  margin: 0;
  color: var(--wallet-muted);
  font-size: 0.8rem;
  line-height: 1.8;
  font-weight: 650;
}

.wallet-option-card-retention {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(52, 144, 139, 0.05);
  color: #2d5c58;
}

.wallet-option-price-stack,
.wallet-option-live {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.wallet-option-price-stack > div,
.wallet-option-live > div:not(.wallet-option-progress) {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.1);
  background: #fff;
}

.wallet-option-price-stack small,
.wallet-option-live small {
  color: var(--wallet-muted);
  font-size: 10px;
  font-weight: 750;
}

.wallet-option-price-stack strong,
.wallet-option-live strong {
  color: var(--wallet-ink);
  font-size: 0.92rem;
  font-weight: 850;
}

.wallet-option-price-stack em {
  font-style: normal;
  color: var(--wallet-muted);
  font-size: 11px;
  font-weight: 700;
}

.wallet-option-progress {
  grid-column: 1 / -1;
  height: 8px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.12);
  overflow: hidden;
}

.wallet-option-progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #1f6f6a, #34908b);
}

.wallet-option-lock-note {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fef2f2;
  color: #991b1b;
}

.wallet-option-lock-note strong {
  font-size: 0.82rem;
}

.wallet-option-lock-note small {
  font-size: 0.74rem;
  line-height: 1.7;
  font-weight: 650;
}

.wallet-option-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.wallet-option-card-actions .action-btn {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 12px;
  font-weight: 800;
}

.wallet-option-active-tag {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: #dcfce7;
  color: #166534;
  font-size: 12px;
  font-weight: 800;
}

.option-detail-schematic.compact {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.08);
  color: #1f5c59;
  font-size: 12px;
}

.wallet-option-tile {
  position: relative;
  overflow: hidden;
  display: grid;
  justify-items: center;
  gap: 10px;
  min-height: 132px;
  padding: 18px 14px 16px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 22px;
  color: var(--wallet-ink);
  background: #ffffff;
  cursor: pointer;
  text-align: center;
  box-shadow: 0 10px 24px rgba(20, 70, 66, 0.06);
  transition: transform 0.22s var(--wallet-ease), box-shadow 0.22s ease, border-color 0.22s ease;
  animation: wallet-rise 0.5s var(--wallet-ease) both;
  animation-delay: calc(var(--i, 0) * 55ms);
}

.wallet-option-tile:hover {
  transform: translateY(-4px) scale(1.02);
  border-color: rgba(52, 144, 139, 0.28);
  box-shadow: 0 16px 32px rgba(20, 70, 66, 0.1);
}

.wallet-option-tile.software,
.wallet-option-tile.cloud,
.wallet-option-tile.attendance,
.wallet-option-tile.accounting {
  color: var(--wallet-ink);
  background: #ffffff;
}

.wallet-option-tile.active {
  outline: 2px solid rgba(52, 144, 139, 0.45);
  outline-offset: 2px;
  border-color: rgba(52, 144, 139, 0.35);
}

.wallet-option-tile.disabled,
.wallet-option-tile.locked {
  opacity: 0.72;
  filter: grayscale(0.25);
}

.wallet-option-tile-icon {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  color: #1f6f6a;
  background: rgba(52, 144, 139, 0.1);
  border: 1px solid rgba(52, 144, 139, 0.16);
}

.wallet-option-tile-icon :deep(.iconly-shell),
.option-detail-icon :deep(.iconly-shell),
.option-detail-close :deep(.iconly-shell) {
  --iconly-filter: brightness(0) saturate(100%) invert(36%) sepia(24%) saturate(980%) hue-rotate(131deg) brightness(92%) contrast(88%);
  font-size: 22px;
}

.option-detail-icon :deep(.iconly-shell),
.option-detail-close :deep(.iconly-shell) {
  --iconly-filter: brightness(0) invert(1);
}

.wallet-option-tile strong {
  color: var(--wallet-ink);
  font-size: 0.92rem;
  font-weight: 820;
  line-height: 1.35;
}

.wallet-option-tile-status {
  padding: 4px 10px;
  border-radius: 999px;
  color: #1f5c59;
  background: rgba(52, 144, 139, 0.1);
  font-size: 10px;
  font-weight: 750;
}

.wallet-option-tile-glow {
  display: none;
}

.option-detail-modal {
  width: min(560px, 100%);
  gap: 14px;
}

.option-detail-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 20px;
  color: #fff;
  background: linear-gradient(135deg, #145652, #34908b);
}

.option-detail-modal.cloud .option-detail-hero {
  background: linear-gradient(135deg, #1a4b66, #4a9ab8);
}

.option-detail-modal.attendance .option-detail-hero {
  background: linear-gradient(135deg, #145a4c, #39b08f);
}

.option-detail-modal.accounting .option-detail-hero {
  background: linear-gradient(135deg, #6b4a1a, #c47d2a);
}

.option-detail-icon {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.24);
  flex-shrink: 0;
}

.option-detail-copy {
  display: grid;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.option-detail-copy small {
  color: rgba(255, 255, 255, 0.75);
  font-weight: 750;
}

.option-detail-copy strong {
  font-size: 1.08rem;
  font-weight: 850;
}

.option-detail-subtitle {
  display: block;
  margin: 0;
  font-style: normal;
  font-size: 0.82rem;
  font-weight: 650;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.5;
}

.option-detail-close {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
  cursor: pointer;
}

.option-detail-texts {
  display: grid;
  gap: 10px;
}

.option-detail-desc {
  margin: 0;
  color: #3d5f5c;
  line-height: 1.9;
  font-weight: 650;
}

.option-detail-retention {
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  color: #2d5c58;
  background: rgba(52, 144, 139, 0.06);
  line-height: 1.8;
  font-weight: 700;
}

.option-detail-prices,
.option-detail-live {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.option-detail-prices article,
.option-detail-live article {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--wallet-line);
  background: linear-gradient(180deg, #fff, #f3faf7);
}

.option-detail-prices small,
.option-detail-live small {
  color: var(--wallet-muted);
  font-weight: 750;
}

.option-detail-prices strong,
.option-detail-live strong {
  color: var(--wallet-ink);
  font-weight: 820;
}

.option-detail-actions {
  flex-wrap: wrap;
}

.option-detail-schematic,
.option-detail-locked {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px;
  border-radius: 14px;
  color: var(--wallet-ink);
  background: rgba(20, 54, 52, 0.05);
  font-weight: 800;
}

.option-detail-locked {
  flex-wrap: wrap;
}

.wallet-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.wallet-summary-card {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 8px;
  padding: 16px;
  min-height: 112px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 18px;
  color: #fff;
  box-shadow: none;
  animation: wallet-rise 0.55s var(--wallet-ease) both;
  animation-delay: calc(var(--i, 0) * 60ms);
  transition: transform 0.22s var(--wallet-ease), border-color 0.22s var(--wallet-ease);
}

.wallet-summary-card:hover { transform: translateY(-2px); }

.wallet-summary-card.primary {
  background: linear-gradient(145deg, #0f4a46, #1f7a72 55%, #34908b);
}

.wallet-summary-card.main {
  background: linear-gradient(145deg, #1d4f6b, #2f6f8f 55%, #4a93b3);
}

.wallet-summary-card.sms {
  background: linear-gradient(145deg, #1d6b55, #2f9b7a 55%, #4db896);
}

.wallet-summary-card.deposit {
  background: linear-gradient(145deg, #8a5a18, #c47d2a 55%, #d9a04a);
}

.wallet-summary-glow {
  position: absolute;
  inset: auto -20% -40% auto;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
  filter: blur(8px);
  pointer-events: none;
}

.wallet-summary-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.24);
  color: #fff;
}

.wallet-summary-icon :deep(.iconly-shell),
.wallet-summary-card :deep(.iconly-shell) {
  color: #fff !important;
  --iconly-filter: brightness(0) invert(1) !important;
  filter: none !important;
}

.wallet-summary-icon :deep(.iconly-img),
.wallet-summary-card :deep(.iconly-img) {
  filter: brightness(0) invert(1) !important;
}

.wallet-summary-card small,
.wallet-summary-card strong,
.wallet-summary-card .iconly-shell {
  color: inherit;
}

.wallet-summary-card small {
  color: rgba(255, 255, 255, 0.78);
  font-weight: 700;
}

.wallet-summary-card strong {
  font-size: 1.12rem;
  font-weight: 820;
  letter-spacing: -0.02em;
}

.wallet-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
}

.wallet-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding: 0 4px 2px;
  color: var(--wallet-ink);
  font-weight: 850;
}

.wallet-section-head small {
  color: var(--wallet-muted);
  font-weight: 700;
}

.wallet-stack,
.ledger-list {
  display: grid;
  gap: 12px;
}

.wallet-tile {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 8px;
  align-content: start;
  padding: 18px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 22px;
  text-align: start;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 16px 32px rgba(15, 63, 60, 0.16);
  transition: transform 0.22s var(--wallet-ease), box-shadow 0.22s ease;
  animation: wallet-rise 0.55s var(--wallet-ease) both;
  animation-delay: calc(var(--i, 0) * 70ms);
}

.wallet-tile.is-main {
  background:
    radial-gradient(circle at 100% 0%, rgba(201, 168, 108, 0.28), transparent 42%),
    linear-gradient(145deg, #123f3c, #1f6f6a 55%, #2d8a84);
}

.wallet-tile.is-sms {
  background:
    radial-gradient(circle at 0% 100%, rgba(120, 200, 180, 0.3), transparent 45%),
    linear-gradient(145deg, #164f5f, #247a8a 55%, #3498a8);
}

.wallet-tile:hover,
.wallet-tile.is-active {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 20px 40px rgba(15, 63, 60, 0.22);
}

.wallet-tile.is-active {
  outline: 2px solid rgba(201, 168, 108, 0.75);
  outline-offset: 2px;
}

.wallet-tile-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 30%, rgba(255, 255, 255, 0.14) 48%, transparent 62%);
  pointer-events: none;
}

.wallet-tile-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.wallet-tile-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.wallet-tile b,
.wallet-tile strong,
.wallet-tile .iconly-shell {
  color: #fff;
}

.wallet-tile strong {
  font-size: 1.28rem;
  font-weight: 820;
  letter-spacing: -0.02em;
}

.wallet-tile-ok,
.wallet-tile-warn {
  width: fit-content;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 750;
}

.wallet-tile-ok {
  color: rgba(255, 255, 255, 0.88);
  background: rgba(255, 255, 255, 0.12);
}

.wallet-tile-warn {
  color: #5a3208;
  background: linear-gradient(135deg, #f0d9a8, #c9a86c);
}

.wallet-ledger {
  min-height: 360px;
  padding: 20px;
  border: 1px solid var(--wallet-line);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(240, 249, 246, 0.94));
  box-shadow: 0 16px 36px rgba(20, 70, 66, 0.07);
}

.ledger-head,
.ledger-row,
.modal-actions,
.modal-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.ledger-head { margin-bottom: 16px; }
.ledger-head > div { display: grid; gap: 2px; }

.ledger-head span {
  color: var(--wallet-ink);
  font-weight: 850;
  font-size: 0.98rem;
}

.ledger-head small {
  color: var(--wallet-muted);
  font-weight: 650;
}

.ledger-head b {
  min-width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(145deg, #1f6f6a, #34908b);
  font-weight: 800;
}

.ledger-row {
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(52, 144, 139, 0.08);
  box-shadow: 0 6px 16px rgba(20, 70, 66, 0.04);
  animation: wallet-rise 0.45s var(--wallet-ease) both;
  animation-delay: calc(var(--i, 0) * 35ms);
  transition: transform 0.18s ease;
}

.ledger-row:hover { transform: translateX(-3px); }

.ledger-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
}

.ledger-icon.in {
  color: #1f7a5c;
  background: linear-gradient(145deg, #dff7ec, #c7efdc);
}

.ledger-icon.out {
  color: #a85a1f;
  background: linear-gradient(145deg, #ffefd8, #ffe0ba);
}

.ledger-row > div:nth-child(2) {
  flex: 1;
  display: grid;
  gap: 4px;
  min-width: 0;
}

.ledger-row b {
  color: var(--wallet-ink);
  font-weight: 780;
}

.ledger-row small {
  color: var(--wallet-muted);
  font-weight: 650;
}

.ledger-row strong.in { color: #1f7a5c; }
.ledger-row strong.out { color: #b4631e; }

.wallet-empty,
.wallet-loading {
  min-height: 280px;
  display: grid;
  place-items: center;
  gap: 10px;
  border-radius: 20px;
  color: rgba(31, 95, 91, 0.55);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.7), rgba(236, 247, 244, 0.85));
}

.wallet-empty.compact { min-height: 220px; }
.wallet-empty p { margin: 0; font-weight: 700; }
.wallet-empty .iconly-shell,
.wallet-loading .iconly-shell { font-size: 2.55rem; }

.wallet-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 5000;
  display: grid;
  place-items: end center;
  padding: 0;
  background: rgba(8, 28, 26, 0.58);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

@media (min-width: 721px) {
  .wallet-modal-backdrop {
    place-items: center;
    padding: 24px;
  }
}

.wallet-modal {
  position: relative;
  z-index: 5001;
  width: min(520px, 100%);
  max-height: min(92dvh, 920px);
  overflow: auto;
  display: grid;
  gap: 16px;
  padding: 22px;
  border-radius: 24px 24px 0 0;
  color: #10231f;
  background: linear-gradient(180deg, #ffffff 0%, #f3faf8 100%) !important;
  border: 1px solid rgba(52, 144, 139, 0.16) !important;
  box-shadow: 0 28px 60px rgba(12, 40, 38, 0.32) !important;
  pointer-events: auto;
}

@media (min-width: 721px) {
  .wallet-modal {
    border-radius: 24px;
  }
}

.payment-guide-modal { width: min(460px, 100%); }
.payment-request-modal { width: min(620px, 100%); }
.purchase-modal { width: min(680px, 100%); overflow: hidden; }

.purchase-modal-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 18px;
  color: #fff;
  background: linear-gradient(135deg, #145652, #34908b);
}

.purchase-modal-head > .iconly-shell {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  color: #1f5c59;
  background: #effaf6;
}

.purchase-modal-head div { display: grid; gap: 3px; }
.purchase-modal-head small { color: rgba(255, 255, 255, 0.72); font-weight: 750; }
.purchase-modal-head strong { font-size: 1.05rem; font-weight: 850; }

.purchase-copy {
  margin: 0;
  color: var(--wallet-muted);
  line-height: 1.9;
}

.purchase-copy.retention {
  padding: 12px 14px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 12px;
  color: #2d5c58;
  background: rgba(52, 144, 139, 0.06);
  font-weight: 700;
}

.purchase-plan-toggle {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.purchase-plan-toggle button {
  display: grid;
  justify-items: start;
  gap: 7px;
  min-height: 112px;
  padding: 14px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 18px;
  color: var(--wallet-ink);
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.purchase-plan-toggle button.active {
  color: #0f3f3c;
  border-color: rgba(52, 144, 139, 0.45);
  background: linear-gradient(180deg, #f2fbf8, #e4f5f0);
  box-shadow: inset 0 0 0 2px rgba(52, 144, 139, 0.18);
  transform: translateY(-1px);
}

.purchase-plan-toggle small { color: inherit; opacity: 0.72; }

.purchase-details-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.purchase-details-grid article,
.purchase-wallet-box {
  display: grid;
  gap: 6px;
  padding: 13px;
  border: 1px solid var(--wallet-line);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
}

.purchase-details-grid small,
.purchase-wallet-box small {
  color: var(--wallet-muted);
  font-weight: 750;
}

.purchase-details-grid strong,
.purchase-wallet-box strong {
  color: var(--wallet-ink);
}

.purchase-wallet-box {
  grid-template-columns: auto 1fr;
  align-items: center;
}

.purchase-wallet-box .iconly-shell {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(145deg, #34908b, #1f6f6a);
}

.modal-handle {
  width: 54px;
  height: 5px;
  margin: 0 auto;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.25);
}

.modal-title {
  justify-content: flex-start;
  color: var(--wallet-ink);
  font-size: 0.98rem;
  font-weight: 780;
}

.wallet-modal .modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #10231f !important;
  font-size: 1.05rem;
  font-weight: 850;
}

.wallet-modal label {
  display: grid;
  gap: 8px;
}

.wallet-modal .modal-handle {
  width: 44px;
  height: 4px;
  margin: 0 auto 4px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.22);
}

.wallet-modal label span {
  color: #52645f !important;
  font-size: 0.78rem;
  font-weight: 750;
}

.wallet-modal input,
.wallet-modal select,
.wallet-modal textarea {
  width: 100%;
  min-height: 46px;
  padding: 10px 12px;
  border: 1px solid rgba(52, 144, 139, 0.18) !important;
  border-radius: 14px !important;
  color: #10231f !important;
  background: #fff !important;
  box-shadow: none !important;
  font: inherit;
}

.wallet-modal .action-btn {
  min-height: 46px;
  border-radius: 14px;
  font-weight: 800;
  cursor: pointer;
  pointer-events: auto;
}

.wallet-modal input,
.wallet-modal select,
.wallet-modal textarea {
  width: 100%;
  border: 1px solid rgba(52, 144, 139, 0.16);
  border-radius: 14px;
  padding: 12px 14px;
  color: var(--wallet-ink);
  background: rgba(255, 255, 255, 0.9);
  font: inherit;
  outline: none;
}

.wallet-modal input:focus,
.wallet-modal select:focus,
.wallet-modal textarea:focus {
  border-color: rgba(52, 144, 139, 0.45);
  box-shadow: 0 0 0 4px rgba(52, 144, 139, 0.12);
}

.payment-card-box,
.payment-summary-box {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(145deg, #0f3f3c, #1f6f6a);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
}

.payment-card-box small,
.payment-summary-box small {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 650;
}

.payment-card-box strong,
.payment-summary-box b {
  color: #fff;
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.payment-card-box span {
  color: #f0d9a8;
  font-weight: 700;
}

.wallet-modal .action-btn.tone-primary,
.wallet-option-actions .action-btn.tone-primary {
  color: #fff !important;
  background: linear-gradient(135deg, #1f6f6a, #34908b) !important;
  box-shadow: 0 10px 22px rgba(52, 144, 139, 0.28) !important;
}

.wallet-modal .action-btn.tone-soft,
.wallet-option-actions .action-btn.tone-soft {
  color: #1f5c59 !important;
  background: rgba(52, 144, 139, 0.1) !important;
}

.payment-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 1100px) {
  .wallet-summary-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .wallet-options-desktop,
  .wallet-options-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .wallet-hero,
  .wallet-layout {
    grid-template-columns: 1fr;
  }

  .wallet-actions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .wallet-options-desktop,
  .options-head-desktop-hint {
    display: none;
  }

  .wallet-options-mobile,
  .wallet-options-grid,
  .options-head-mobile-hint {
    display: grid;
  }

  .wallet-options-mobile,
  .wallet-options-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
  }

  .options-head-mobile-hint {
    display: block;
  }

  .wallet-option-tile {
    min-height: 0;
    padding: 10px 6px 12px;
    gap: 6px;
  }

  .wallet-option-tile strong {
    font-size: 0.72rem;
    line-height: 1.25;
  }

  .wallet-option-tile-status {
    font-size: 0.62rem;
  }
}

@media (max-width: 640px) {
  .wallet-hero {
    padding: 18px;
    border-radius: 22px;
    min-height: 0;
  }

  .wallet-hero-amount {
    font-size: clamp(1.6rem, 9vw, 2.4rem) !important;
    overflow-wrap: anywhere;
  }

  .wallet-hero-chip { display: none; }

  .wallet-actions,
  .wallet-summary-grid,
  .purchase-details-grid,
  .payment-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .wallet-summary-card {
    min-height: 96px;
    padding: 14px;
  }

  .wallet-options-mobile,
  .wallet-options-grid {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 8px;
  }

  .wallet-option-card,
  .wallet-option-tile {
    padding: 12px 10px;
    border-radius: 14px;
    gap: 8px;
  }

  .wallet-option-tile {
    min-height: 0;
    padding: 10px 6px 12px;
    gap: 6px;
    border-radius: 14px;
  }

  .wallet-option-tile-icon {
    width: 36px;
    height: 36px;
    border-radius: 12px;
  }

  .wallet-option-tile strong {
    font-size: 0.72rem;
    line-height: 1.25;
  }

  .wallet-option-tile-status {
    font-size: 0.62rem;
  }

  .ledger-row,
  .modal-actions { flex-wrap: wrap; }

  .modal-actions .action-btn {
    width: 100%;
    justify-content: center;
  }

  .wallet-modal {
    gap: 12px;
    padding: 16px 12px;
    border-radius: 22px 22px 0 0;
    max-width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .wallet-page,
  .wallet-orb,
  .wallet-hero-shine,
  .wallet-hero-chip,
  .wallet-summary-card,
  .wallet-tile,
  .wallet-option-tile,
  .ledger-row {
    animation: none !important;
  }
}

</style>
