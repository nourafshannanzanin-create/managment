<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, reactive, watch } from 'vue'

import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { formatAmountInput } from '../utils/amount'
import { formatJalali, getTodayJalali } from '../utils/jalali'
import { useWorkflowHub } from '../stores/workflowHub'

const CARD_NUMBER = '6274121774209571'
const CARD_HOLDER = 'کارنومند'
const PAYMENT_SUBJECT = 'درخواست شارژ کیف پول'

const { state, loadWalletDashboard, loadWalletOptions, submitWalletTransaction, submitFeaturePurchase, createSupportTicket } = useWorkflowHub()

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

function optionDisabled(option) {
  return Boolean(option.disabled || option.isDisabled || option.is_disabled)
}

function optionIcon(option) {
  const key = option.featureKey || option.feature_key
  if (key === 'cloud_storage') return 'cloud'
  if (key === 'attendance') return 'login'
  if (key === 'accounting') return 'lock'
  return 'shopping_cart'
}

function optionStatus(option) {
  if (optionDisabled(option)) return option.disabledLabel || option.disabled_label || 'غیرفعال'
  if (option.required) return 'اجباری'
  if (option.isActive || option.is_active) return 'فعال'
  return 'قابل خرید'
}

const paymentMethods = [
  { key: 'pos', label: 'دستگاه کارتخوان' },
  { key: 'card_to_card', label: 'کارت به کارت' },
  { key: 'app', label: 'اپلیکیشن' },
]

const shortcuts = computed(() => {
  if (isSchematicWallet.value) return []
  return [
    { label: 'شارژ', icon: 'add_card', direction: 'in', tone: 'deposit' },
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
  if (transactionForm.direction === 'out' && usesManagerPaymentFlow.value) {
    const sourceWallet = wallets.value.find((item) => String(item.id) === String(transactionForm.walletId))
    const targetWallet = wallets.value.find((item) => String(item.id) === String(transactionForm.targetWalletId))
    const message = [
      'ACTION_TYPE: wallet_withdrawal',
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
    state.wallet.message = 'درخواست برداشت برای پشتیبانی ارسال شد.'
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

  await createSupportTicket({
    subject: PAYMENT_SUBJECT,
    message,
    category: 'financial',
    priority: 'urgent',
    attachments: paymentForm.receipt ? [paymentForm.receipt] : [],
  })

  state.wallet.message = 'درخواست شارژ برای HQ ارسال شد.'
  state.wallet.error = ''
  closePaymentForm()
}

const ledgerItems = computed(() => [...transactions.value].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)))

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
        <div class="wallet-hero-balance">
          <IconlyIcon name="account_balance_wallet" decorative />
          <strong>{{ state.wallet.summary.totalBalance }}</strong>
          <small>{{ state.wallet.organization?.name || state.currentUser.organization }}</small>
        </div>

        <div v-if="shortcuts.length" class="wallet-actions">
          <button
            v-for="item in shortcuts"
            :key="item.direction"
            :class="['wallet-action', item.tone]"
            type="button"
            @click="openTransaction(item.direction)"
          >
            <IconlyIcon :name="item.icon" decorative />
            <b>{{ item.label }}</b>
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

      <div v-if="purchaseOptions.length" class="wallet-options-grid">
        <article
          v-for="option in purchaseOptions"
          :key="option.featureKey || option.feature_key"
          class="wallet-option-card"
          :class="{ active: option.isActive || option.is_active, required: option.required, disabled: optionDisabled(option) }"
        >
          <div class="wallet-option-head">
            <IconlyIcon :name="optionIcon(option)" decorative />
            <small>{{ optionStatus(option) }}</small>
          </div>
          <strong>{{ option.title }}</strong>
          <p>{{ option.description }}</p>
          <small v-if="option.retentionSummary || option.retention_summary" class="wallet-option-retention">
            {{ option.retentionSummary || option.retention_summary }}
          </small>
          <template v-if="!optionDisabled(option)">
            <div class="wallet-option-price">
              <span>نقدی</span>
              <b>{{ option.cashAmount || option.cash_amount || option.totalAmount || option.total_amount }}</b>
            </div>
            <div v-if="option.upfrontAmount || option.upfront_amount" class="wallet-option-price">
              <span>پیش‌پرداخت</span>
              <b>{{ option.upfrontAmount || option.upfront_amount }}</b>
            </div>
            <div class="wallet-option-price">
              <span>اقساط</span>
              <b>{{ option.monthlyInstallmentAmount || option.monthly_installment_amount }} / {{ option.installmentMonths || option.installment_months }} ماه</b>
            </div>
            <div v-if="option.annualSubscriptionAmountRaw" class="wallet-option-price annual">
              <span>اشتراک سالانه</span>
              <b>{{ option.annualSubscriptionAmount }} / {{ option.annualSubscriptionInstallmentAmount }} / {{ option.annualSubscriptionInstallmentMonths }} ماه</b>
            </div>
            <div v-if="!isSchematicWallet" class="wallet-option-actions">
              <button class="action-btn tone-soft" type="button" :disabled="state.wallet.submitting || option.isActive || option.is_active" @click="openPurchase(option, 'installment')">قسطی</button>
              <button class="action-btn tone-primary" type="button" :disabled="state.wallet.submitting || option.isActive || option.is_active" @click="openPurchase(option, 'cash')">
                <IconlyIcon name="shopping_cart_checkout" decorative />
                <span>خرید نقدی</span>
              </button>
            </div>
            <div v-else class="wallet-option-disabled">
              <IconlyIcon name="visibility" decorative />
              <b>نمایشی — بدون خرید واقعی</b>
            </div>
          </template>
          <div v-else class="wallet-option-disabled">
            <IconlyIcon name="lock" decorative />
            <b>فعلا غیرفعال است</b>
          </div>
        </article>
      </div>

      <div class="wallet-summary-grid">
        <article v-for="card in summaryCards" :key="card.label" :class="['wallet-summary-card', card.tone]">
          <IconlyIcon :name="card.icon" decorative />
          <small>{{ card.label }}</small>
          <strong>{{ card.value }}</strong>
        </article>
      </div>

      <div class="wallet-layout">
        <aside class="wallet-stack">
          <button
            v-for="wallet in wallets"
            :key="wallet.id"
            :class="['wallet-tile', String(wallet.id) === String(transactionForm.walletId || paymentSetup.walletId || paymentGuide.walletId || paymentForm.walletId || purchaseForm.walletId || activeWallet?.id) && 'is-active']"
            type="button"
            @click="transactionForm.walletId = String(wallet.id); paymentSetup.walletId = String(wallet.id); paymentGuide.walletId = String(wallet.id); paymentForm.walletId = String(wallet.id); purchaseForm.walletId = String(wallet.id)"
          >
            <IconlyIcon :name="wallet.key === 'sms' ? 'sms' : 'account_balance'" decorative />
            <b>{{ wallet.name }}</b>
            <strong>{{ wallet.balance }}</strong>
            <small v-if="wallet.isLow">کمبود موجودی</small>
          </button>
        </aside>

        <div class="wallet-ledger">
          <div class="ledger-head">
            <span>گردش حساب</span>
            <b>{{ ledgerItems.length }}</b>
          </div>

          <div v-if="state.wallet.loading" class="wallet-loading">
            <IconlyIcon name="progress_activity" decorative />
          </div>

          <div v-else-if="!ledgerItems.length" class="wallet-empty compact">
            <IconlyIcon name="receipt_long" decorative />
          </div>

          <div v-else class="ledger-list">
            <article v-for="item in ledgerItems" :key="item.id" class="ledger-row">
              <div :class="['ledger-icon', item.direction]">
                <IconlyIcon :name="item.direction === 'in' ? 'south_west' : 'north_east'" decorative />
              </div>
              <div>
                <b>{{ item.walletName }}</b>
                <small>{{ item.actor }} / {{ item.time }}</small>
              </div>
              <strong :class="item.direction">{{ item.direction === 'in' ? '+' : '-' }}{{ item.amount }}</strong>
            </article>
          </div>
        </div>
      </div>
    </template>

    <div v-if="transactionForm.open" class="wallet-modal-backdrop" @click.self="closeTransaction">
      <form class="wallet-modal" @submit.prevent="submitTransaction">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <IconlyIcon :name="transactionForm.direction === 'in' ? 'add_card' : 'payments'" decorative />
          <strong>{{ transactionForm.direction === 'in' ? 'شارژ کیف پول' : 'برداشت از کیف پول' }}</strong>
        </div>

        <label>
          <span>کیف پول</span>
          <select v-model="transactionForm.walletId" required>
            <option v-for="wallet in wallets" :key="wallet.id" :value="wallet.id">{{ wallet.name }}</option>
          </select>
        </label>

        <label>
          <span>مبلغ (تومان)</span>
          <input v-model="transactionForm.amount" inputmode="decimal" required placeholder="0" @input="transactionForm.amount = formatAmountInput($event.target.value)" />
        </label>

        <label>
          <span>توضیحات</span>
          <textarea v-model="transactionForm.note" rows="3"></textarea>
        </label>

        <div v-if="state.wallet.error" class="wallet-alert danger in-modal">
          {{ state.wallet.error }}
        </div>

        <template v-if="transactionForm.direction === 'out' && usesManagerPaymentFlow">
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
            <input v-model.trim="paymentSetup.amount" inputmode="decimal" required placeholder="0" @input="paymentSetup.amount = formatAmountInput($event.target.value)" />
          </label>
        </div>

        <label>
          <span>بابت</span>
          <input v-model.trim="paymentSetup.purpose" required placeholder="مثلا شارژ پیامک یا تمدید سرویس" />
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
            <strong>{{ purchaseWallet?.balance || '0.00' }}</strong>
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
            <input v-model.trim="paymentForm.amount" inputmode="decimal" required placeholder="0" @input="paymentForm.amount = formatAmountInput($event.target.value)" />
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

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePaymentForm">بستن</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.support.submitting">
            <IconlyIcon name="send" decorative />
            ارسال برای HQ
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<style scoped>
.wallet-page {
  --wallet-navy: #111827;
  --wallet-blue: var(--button-primary-bg, #17315d);
  --wallet-action-bg: #34908B;
  --wallet-action-shadow: 0 8px 20px rgba(52, 144, 139, 0.22);
  --wallet-gold: #667085;
  --wallet-ink: #344054;
  --wallet-muted: #667085;
  --wallet-line: #e4e7ec;
  display: grid;
  gap: 18px;
  font-size: 13px;
}

.wallet-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  overflow: hidden;
  min-height: 230px;
  padding: 26px;
  border: 1px solid var(--wallet-line);
  border-radius: 12px;
  background: var(--surface, #fff);
  box-shadow: none;
}

.wallet-hero-balance,
.wallet-actions,
.wallet-summary-card,
.wallet-tile,
.wallet-ledger,
.wallet-modal,
.wallet-license-alert,
.wallet-option-card {
  position: relative;
  z-index: 1;
}

.wallet-hero-balance {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}

.wallet-hero-balance .iconly-shell {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  color: #fff;
  background: var(--wallet-navy);
}

.wallet-hero-balance strong {
  color: var(--wallet-navy);
  font-size: clamp(1.85rem, 4.8vw, 3.35rem);
  font-weight: 760;
  line-height: 1;
  letter-spacing: -0.04em;
}

.wallet-hero-balance small,
.wallet-summary-card small,
.wallet-tile small,
.ledger-row small,
.ledger-head span,
.wallet-modal label span,
.payment-card-box small,
.payment-summary-box small {
  color: var(--wallet-muted);
  font-weight: 650;
}

.wallet-actions {
  display: grid;
  align-content: center;
  gap: 12px;
  min-width: 170px;
}

.wallet-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border: 0;
  border-radius: 12px;
  color: #fff;
  background: var(--wallet-blue);
  box-shadow: none;
  cursor: pointer;
}

.wallet-action .iconly-shell,
.wallet-action b {
  color: inherit;
}

.wallet-action.deposit {
  color: #fff;
  background: var(--wallet-navy);
}

.wallet-action b {
  font-size: 0.92rem;
  font-weight: 750;
}

.wallet-action.withdraw {
  color: #fff;
  background: var(--wallet-blue);
}

.wallet-alert {
  padding: 14px 18px;
  border-radius: 18px;
  color: #254f85;
  background: rgba(55, 99, 168, 0.1);
  font-weight: 750;
}

.wallet-alert.danger {
  color: var(--wallet-ink);
  background: #f9fafb;
}

.wallet-alert.in-modal {
  border: 1px solid #fecdca;
  border-radius: 8px;
  color: #b42318 !important;
  background: #fffbfa !important;
}

.wallet-license-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(171, 92, 28, 0.18);
  border-radius: 8px;
  color: #7a3f14;
  background: #f9fafb;
}

.wallet-license-alert.wallet-trial-alert {
  border-color: rgba(52, 144, 139, 0.2);
  color: #1f5f5b;
  background: rgba(52, 144, 139, 0.08);
}

.wallet-license-alert.wallet-trial-alert .iconly-shell {
  background: #34908B;
}

.wallet-license-alert .iconly-shell {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  background: var(--wallet-blue);
}

.wallet-license-alert div {
  display: grid;
  gap: 4px;
}

.wallet-options-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.wallet-option-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--wallet-line);
  border-radius: 8px;
  background: #fff;
  box-shadow: none;
}

.wallet-option-card.active {
  background: #ffffff;
}

.wallet-option-card.disabled {
  border-color: var(--wallet-line);
  background: #fff;
}

.wallet-option-card.disabled .wallet-option-head .iconly-shell,
.wallet-option-card.disabled .wallet-option-head small {
  color: var(--wallet-blue);
}

.wallet-option-card.disabled strong {
  color: var(--wallet-navy);
}

.wallet-option-head,
.wallet-option-price,
.wallet-option-actions,
.wallet-option-disabled {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.wallet-option-head .iconly-shell {
  color: var(--wallet-blue);
}

.wallet-option-head small {
  color: var(--wallet-muted);
  font-weight: 850;
}

.wallet-option-card strong {
  color: var(--wallet-navy);
}

.wallet-option-card p {
  min-height: 58px;
  margin: 0;
  color: var(--wallet-muted);
  line-height: 1.8;
}

.wallet-option-retention {
  display: block;
  min-height: 48px;
  padding: 10px 12px;
  border: 1px solid #d0d5dd;
  border-radius: 8px;
  color: #344054;
  background: #f9fafb;
  line-height: 1.8;
  font-weight: 700;
}

.wallet-option-price {
  padding: 9px 10px;
  border-radius: 8px;
  background: #f9fafb;
}

.wallet-option-price span {
  color: var(--wallet-muted);
}

.wallet-option-price b {
  color: var(--wallet-ink);
}

.wallet-option-actions .action-btn {
  min-height: 38px;
  flex: 1;
}

.wallet-option-disabled {
  min-height: 38px;
  margin-top: auto;
  padding: 11px 12px;
  border-radius: 8px;
  color: var(--wallet-navy);
  background: #f9fafb;
  font-weight: 800;
}

.wallet-option-disabled .iconly-shell {
  color: var(--wallet-blue);
}

.wallet-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.wallet-summary-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  min-height: 138px;
  border: 1px solid var(--wallet-line);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: none;
}

.wallet-summary-card small,
.wallet-summary-card .iconly-shell,
.wallet-summary-card strong {
  color: inherit;
}

.wallet-summary-card.primary {
  color: #fff;
  border-color: var(--wallet-blue);
  background: var(--wallet-blue);
}

.wallet-summary-card.primary small {
  color: rgba(255, 255, 255, 0.76);
}

.wallet-summary-card.main {
  color: var(--wallet-navy);
  border-color: var(--wallet-line);
  background: #ffffff;
}

.wallet-summary-card.main small {
  color: #486388;
}

.wallet-summary-card.sms {
  color: var(--wallet-navy);
  border-color: var(--wallet-line);
  background: #ffffff;
}

.wallet-summary-card.sms small {
  color: #41675d;
}

.wallet-summary-card.deposit {
  color: var(--wallet-navy);
  border-color: var(--wallet-line);
  background: #ffffff;
}

.wallet-summary-card.deposit small {
  color: #8e6130;
}

.wallet-summary-card .iconly-shell {
  opacity: 0.96;
}

.wallet-summary-card strong {
  font-size: 1.06rem;
  font-weight: 740;
}

.wallet-layout {
  display: grid;
  grid-template-columns: 310px minmax(0, 1fr);
  gap: 16px;
}

.wallet-stack,
.ledger-list {
  display: grid;
  gap: 12px;
}

.wallet-tile {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 12px;
  align-items: center;
  padding: 18px;
  border: 1px solid var(--wallet-line);
  border-radius: 12px;
  text-align: start;
  color: var(--wallet-ink);
  background: rgba(255, 255, 255, 0.68);
  cursor: pointer;
}

.wallet-tile.is-active {
  border-color: var(--wallet-blue);
  background: #fff;
  color: var(--wallet-navy);
}

.wallet-tile.is-active b,
.wallet-tile.is-active strong,
.wallet-tile.is-active .iconly-shell {
  color: var(--wallet-navy);
}

.wallet-tile.is-active small {
  color: var(--wallet-muted);
}

.wallet-tile strong {
  grid-column: 1 / -1;
  font-size: 1.12rem;
  font-weight: 740;
}

.wallet-tile b,
.ledger-row b,
.ledger-head b {
  font-weight: 740;
}

.wallet-ledger {
  min-height: 360px;
  padding: 18px;
  border: 1px solid var(--wallet-line);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: none;
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

.ledger-head {
  margin-bottom: 14px;
}

.ledger-head b {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #f8f3e7;
  background: var(--wallet-navy);
}

.ledger-row {
  padding: 14px;
  border-radius: 20px;
  background: #f9fafb;
}

.ledger-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 16px;
}

.ledger-icon.in {
  color: var(--wallet-blue);
  background: rgba(73, 114, 190, 0.12);
}

.ledger-icon.out {
  color: var(--wallet-blue);
  background: rgba(224, 155, 88, 0.18);
}

.ledger-row > div:nth-child(2) {
  flex: 1;
  display: grid;
  gap: 4px;
}

.ledger-row strong.in {
  color: var(--wallet-blue);
}

.ledger-row strong.out {
  color: var(--wallet-blue);
}

.wallet-empty,
.wallet-loading {
  min-height: 280px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: rgba(24, 49, 83, 0.55);
  background: rgba(255, 255, 255, 0.66);
}

.wallet-empty.compact {
  min-height: 240px;
  background: #f9fafb;
}

.wallet-empty .iconly-shell,
.wallet-loading .iconly-shell {
  font-size: 2.55rem;
}

.wallet-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(24, 49, 83, 0.38);
  backdrop-filter: none;
}

.wallet-modal {
  width: min(520px, 100%);
  display: grid;
  gap: 16px;
  padding: 22px;
  border-radius: 12px;
  background: #f8fbff;
  box-shadow: none;
}

.payment-guide-modal {
  width: min(460px, 100%);
}

.payment-request-modal {
  width: min(620px, 100%);
}

.purchase-modal {
  width: min(680px, 100%);
  overflow: hidden;
}

.purchase-modal-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 18px;
  color: #fff;
  background: var(--wallet-blue);
}

.purchase-modal-head > .iconly-shell {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  color: var(--wallet-navy);
  background: #eff6ff;
}

.purchase-modal-head div {
  display: grid;
  gap: 3px;
}

.purchase-modal-head small {
  color: rgba(255, 255, 255, 0.72);
  font-weight: 750;
}

.purchase-modal-head strong {
  font-size: 1.05rem;
  font-weight: 850;
}

.purchase-copy {
  margin: 0;
  color: var(--wallet-muted);
  line-height: 1.9;
}

.purchase-copy.retention {
  padding: 12px 14px;
  border: 1px solid #d0d5dd;
  border-radius: 12px;
  color: #344054;
  background: #f9fafb;
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
  border: 1px solid rgba(32, 58, 105, 0.12);
  border-radius: 18px;
  color: var(--wallet-ink);
  background: #fff;
  cursor: pointer;
}

.purchase-plan-toggle button.active {
  color: var(--wallet-navy);
  border-color: #3264a9;
  background: #eff6ff;
  box-shadow: inset 0 0 0 2px rgba(50, 100, 169, 0.28);
}

.purchase-plan-toggle button.active .iconly-shell,
.purchase-plan-toggle button.active b,
.purchase-plan-toggle button.active small {
  color: var(--wallet-navy);
}

.purchase-plan-toggle small {
  color: inherit;
  opacity: 0.72;
}

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
  background: rgba(255, 255, 255, 0.82);
}

.purchase-details-grid small,
.purchase-wallet-box small {
  color: var(--wallet-muted);
  font-weight: 750;
}

.purchase-details-grid strong,
.purchase-wallet-box strong {
  color: var(--wallet-navy);
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
  color: var(--wallet-blue);
  background: rgba(73, 114, 190, 0.12);
}

.modal-handle {
  width: 54px;
  height: 5px;
  margin: 0 auto;
  border-radius: 999px;
  background: rgba(24, 49, 83, 0.18);
}

.modal-title {
  justify-content: flex-start;
  color: var(--wallet-navy);
  font-size: 0.98rem;
  font-weight: 740;
}

.wallet-modal label {
  display: grid;
  gap: 8px;
}

.wallet-modal input,
.wallet-modal select,
.wallet-modal textarea {
  width: 100%;
  border: 1px solid rgba(32, 58, 105, 0.12);
  border-radius: 18px;
  padding: 12px 14px;
  color: var(--wallet-navy);
  background: rgba(255, 255, 255, 0.76);
  font: inherit;
  outline: none;
}

.payment-card-box,
.payment-summary-box {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--wallet-line);
}

.payment-card-box strong,
.payment-summary-box b {
  color: var(--wallet-navy);
  font-size: 1.02rem;
  font-weight: 740;
  letter-spacing: 0.04em;
}

.payment-card-box span {
  color: var(--wallet-ink);
  font-weight: 700;
}

.wallet-modal .action-btn.tone-primary,
.wallet-option-actions .action-btn.tone-primary {
  color: #fff !important;
  background: var(--wallet-blue) !important;
}

.wallet-modal .action-btn.tone-soft,
.wallet-option-actions .action-btn.tone-soft {
  color: var(--wallet-navy) !important;
  background: rgba(55, 99, 168, 0.1) !important;
}

.payment-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 980px) {
  .wallet-hero,
  .wallet-layout {
    grid-template-columns: 1fr;
  }

  .wallet-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .wallet-options-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .wallet-hero {
    padding: 16px;
    border-radius: 20px;
  }

  .wallet-summary-grid,
  .wallet-options-grid,
  .purchase-details-grid,
  .payment-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ledger-row,
  .modal-actions {
    flex-wrap: wrap;
  }

  .wallet-modal {
    gap: 12px;
    padding: 16px 12px;
    border-radius: 20px 20px 0 0;
  }

  .wallet-modal input,
  .wallet-modal select,
  .wallet-modal textarea {
    border-radius: 14px;
    padding: 10px 12px;
    font-size: 12px;
  }
}

@media (max-width: 420px) {
  .wallet-options-grid,
  .purchase-plan-toggle,
  .purchase-details-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .payment-grid,
  .wallet-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* Dashboard-aligned neutral navy theme. */
.wallet-page {
  --wallet-navy: #111827;
  --wallet-blue: var(--button-primary-bg, #17315d);
  --wallet-gold: #667085;
  --wallet-ink: #344054;
  --wallet-muted: #667085;
  --wallet-line: #e4e7ec;
}

.wallet-hero,
.wallet-summary-card,
.wallet-tile,
.wallet-ledger,
.wallet-option-card,
.wallet-modal,
.wallet-license-alert,
.purchase-details-grid article,
.purchase-wallet-box,
.payment-card-box,
.payment-summary-box {
  background: #ffffff;
  border: 1px solid var(--wallet-line);
  box-shadow: none;
}

.wallet-hero-balance .iconly-shell,
.ledger-head b,
.purchase-modal-head,
.wallet-modal .action-btn.tone-primary,
.wallet-option-actions .action-btn.tone-primary,
.wallet-action,
.wallet-action.deposit,
.wallet-action.withdraw {
  color: #ffffff !important;
  background: #34908B !important;
  background-image: none !important;
  border-color: transparent !important;
  box-shadow: 0 8px 20px rgba(52, 144, 139, 0.22) !important;
}

.wallet-action:hover:not(:disabled),
.wallet-modal .action-btn.tone-primary:hover:not(:disabled),
.wallet-option-actions .action-btn.tone-primary:hover:not(:disabled) {
  color: #ffffff !important;
  background: #2b7874 !important;
  background-image: none !important;
  border-color: transparent !important;
  box-shadow: 0 10px 24px rgba(52, 144, 139, 0.26) !important;
}

.wallet-hero-balance strong,
.wallet-option-card strong,
.wallet-summary-card strong,
.wallet-tile b,
.wallet-tile strong,
.ledger-row b,
.ledger-head b,
.payment-card-box strong,
.payment-summary-box b,
.purchase-details-grid strong,
.purchase-wallet-box strong,
.modal-title,
.wallet-modal input,
.wallet-modal select,
.wallet-modal textarea {
  color: var(--wallet-navy);
}

.wallet-hero-balance small,
.wallet-summary-card small,
.wallet-tile small,
.ledger-row small,
.ledger-head span,
.wallet-option-card p,
.wallet-option-price span,
.wallet-modal label span,
.payment-card-box small,
.payment-summary-box small,
.purchase-copy,
.purchase-details-grid small,
.purchase-wallet-box small {
  color: var(--wallet-muted);
}

.wallet-summary-card.primary,
.wallet-summary-card.main,
.wallet-summary-card.sms,
.wallet-summary-card.deposit,
.wallet-tile.is-active {
  color: var(--wallet-navy);
  border-color: var(--wallet-line);
  background: #ffffff;
}

.wallet-summary-card.primary small,
.wallet-summary-card.main small,
.wallet-summary-card.sms small,
.wallet-summary-card.deposit small,
.wallet-tile.is-active small {
  color: var(--wallet-muted);
}

.wallet-summary-card .iconly-shell,
.wallet-option-head .iconly-shell,
.wallet-option-head small,
.wallet-option-disabled .iconly-shell,
.purchase-wallet-box .iconly-shell,
.ledger-icon.in,
.ledger-icon.out,
.ledger-row strong.in,
.ledger-row strong.out {
  color: var(--wallet-blue);
}

.wallet-summary-card .iconly-shell,
.wallet-option-head .iconly-shell,
.purchase-wallet-box .iconly-shell,
.ledger-icon.in,
.ledger-icon.out {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.wallet-alert,
.wallet-alert.danger,
.wallet-license-alert,
.wallet-option-price,
.wallet-option-disabled,
.ledger-row,
.wallet-empty.compact,
.wallet-modal .action-btn.tone-soft,
.wallet-option-actions .action-btn.tone-soft {
  color: var(--wallet-ink) !important;
  background: #f9fafb !important;
  border-color: var(--wallet-line);
}

.wallet-license-alert .iconly-shell,
.purchase-modal-head > .iconly-shell {
  color: var(--wallet-blue);
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.wallet-modal,
.wallet-modal input,
.wallet-modal select,
.wallet-modal textarea {
  background: #ffffff;
}

.modal-handle {
  background: #e4e7ec;
}
</style>
