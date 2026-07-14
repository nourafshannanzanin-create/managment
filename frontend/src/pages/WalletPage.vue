<script setup>
import { computed, onMounted, reactive, watch } from 'vue'

import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { formatAmountInput } from '../utils/amount'
import { formatJalali, getTodayJalali } from '../utils/jalali'
import { useWorkflowHub } from '../stores/workflowHub'

const CARD_NUMBER = '6274121774209571'
const CARD_HOLDER = 'امید کریمی'
const PAYMENT_SUBJECT = 'پرداخت کیف پول'

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

const paymentMethods = [
  { key: 'pos', label: 'درگاه پرداخت' },
  { key: 'card_to_card', label: 'کارت به کارت' },
  { key: 'app', label: 'اپ' },
]

const shortcuts = computed(() => [
  { label: 'شارژ', icon: 'add_card', direction: 'in', tone: 'deposit' },
  { label: 'برداشت', icon: 'payments', direction: 'out', tone: 'withdraw' },
])

const summaryCards = computed(() => [
  { label: 'کل موجودی', value: state.wallet.summary.totalBalance, icon: 'account_balance_wallet', tone: 'primary' },
  { label: 'اصلی', value: state.wallet.summary.mainBalance, icon: 'account_balance', tone: 'main' },
  { label: 'پیامک', value: state.wallet.summary.smsBalance, icon: 'sms', tone: 'sms' },
  { label: 'ورودی', value: state.wallet.summary.depositsTotal, icon: 'south_west', tone: 'deposit' },
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
    await createSupportTicket({ subject: 'برداشت کیف پول', message, category: 'financial', priority: 'urgent', attachments: [] })
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

  state.wallet.message = 'درخواست تایید پرداخت برای HQ ارسال شد.'
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
      <span class="material-symbols-outlined">lock</span>
    </div>

    <div v-else-if="needsOrganization" class="wallet-empty">
      <span class="material-symbols-outlined">corporate_fare</span>
    </div>

    <template v-else>
      <div class="wallet-hero">
        <div class="wallet-hero-balance">
          <span class="material-symbols-outlined">account_balance_wallet</span>
          <strong>{{ state.wallet.summary.totalBalance }}</strong>
          <small>{{ state.wallet.organization?.name || state.currentUser.organization }}</small>
        </div>

        <div class="wallet-actions">
          <button
            v-for="item in shortcuts"
            :key="item.direction"
            :class="['wallet-action', item.tone]"
            type="button"
            @click="openTransaction(item.direction)"
          >
            <span class="material-symbols-outlined">{{ item.icon }}</span>
            <b>{{ item.label }}</b>
          </button>
        </div>
      </div>

      <div v-if="state.wallet.error || state.wallet.message" class="wallet-alert" :class="{ danger: state.wallet.error }">
        {{ state.wallet.error || state.wallet.message }}
      </div>

      <div v-if="licenseLocked" class="wallet-license-alert">
        <span class="material-symbols-outlined">lock</span>
        <div>
          <strong>خرید اصلی نرم‌افزار باید تایید شود.</strong>
          <small>{{ licenseStatus.notice || 'برای ادامه استفاده از بخش‌های عملیاتی، گزینه خرید اصلی را ثبت کنید.' }}</small>
        </div>
      </div>

      <div v-if="purchaseOptions.length" class="wallet-options-grid">
        <article
          v-for="option in purchaseOptions"
          :key="option.featureKey || option.feature_key"
          class="wallet-option-card"
          :class="{ active: option.isActive || option.is_active, required: option.required }"
          :style="{ '--option-accent': option.accent || '#315f9f' }"
        >
          <div class="wallet-option-head">
            <span class="material-symbols-outlined">{{ (option.featureKey || option.feature_key) === 'cloud_storage' ? 'cloud' : ((option.featureKey || option.feature_key) === 'attendance' ? 'login' : 'shopping_cart') }}</span>
            <small>{{ option.required ? 'الزامی' : ((option.isActive || option.is_active) ? 'فعال' : 'اختیاری') }}</small>
          </div>
          <strong>{{ option.title }}</strong>
          <p>{{ option.description }}</p>
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
            <b>{{ option.monthlyInstallmentAmount || option.monthly_installment_amount }} × {{ option.installmentMonths || option.installment_months }}</b>
          </div>
          <div v-if="option.annualSubscriptionAmountRaw" class="wallet-option-price annual">
            <span>اشتراک سالانه</span>
            <b>{{ option.annualSubscriptionAmount }} / {{ option.annualSubscriptionInstallmentAmount }} × {{ option.annualSubscriptionInstallmentMonths }}</b>
          </div>
          <div class="wallet-option-actions">
            <button class="action-btn tone-soft" type="button" :disabled="state.wallet.submitting || option.isActive || option.is_active" @click="openPurchase(option, 'installment')">اقساطی</button>
            <button class="action-btn tone-primary" type="button" :disabled="state.wallet.submitting || option.isActive || option.is_active" @click="openPurchase(option, 'cash')">
              <span class="material-symbols-outlined">shopping_cart_checkout</span>
              <span>خرید</span>
            </button>
          </div>
        </article>
      </div>

      <div class="wallet-summary-grid">
        <article v-for="card in summaryCards" :key="card.label" :class="['wallet-summary-card', card.tone]">
          <span class="material-symbols-outlined">{{ card.icon }}</span>
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
            <span class="material-symbols-outlined">{{ wallet.key === 'sms' ? 'sms' : 'account_balance' }}</span>
            <b>{{ wallet.name }}</b>
            <strong>{{ wallet.balance }}</strong>
            <small v-if="wallet.isLow">LOW</small>
          </button>
        </aside>

        <div class="wallet-ledger">
          <div class="ledger-head">
            <span>Ledger</span>
            <b>{{ ledgerItems.length }}</b>
          </div>

          <div v-if="state.wallet.loading" class="wallet-loading">
            <span class="material-symbols-outlined">progress_activity</span>
          </div>

          <div v-else-if="!ledgerItems.length" class="wallet-empty compact">
            <span class="material-symbols-outlined">receipt_long</span>
          </div>

          <div v-else class="ledger-list">
            <article v-for="item in ledgerItems" :key="item.id" class="ledger-row">
              <div :class="['ledger-icon', item.direction]">
                <span class="material-symbols-outlined">{{ item.direction === 'in' ? 'south_west' : 'north_east' }}</span>
              </div>
              <div>
                <b>{{ item.walletName }}</b>
                <small>{{ item.actor }} · {{ item.time }}</small>
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
          <span class="material-symbols-outlined">{{ transactionForm.direction === 'in' ? 'add_card' : 'payments' }}</span>
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
          <span>یادداشت</span>
          <textarea v-model="transactionForm.note" rows="3"></textarea>
        </label>

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
          <button class="action-btn tone-soft" type="button" @click="closeTransaction">لغو</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.wallet.submitting">
            <span class="material-symbols-outlined">check</span>
            ثبت
          </button>
        </div>
      </form>
    </div>

    <div v-if="paymentSetup.open" class="wallet-modal-backdrop" @click.self="closePaymentSetup">
      <form class="wallet-modal payment-request-modal" @submit.prevent="continuePaymentFlow">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <span class="material-symbols-outlined">payments</span>
          <strong>مشخصات پرداخت</strong>
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
          <span>شرح :</span>
          <input v-model.trim="paymentSetup.purpose" required placeholder="مثلا شارژ پیامک یا موجودی اصلی" />
        </label>

        <label>
          <span>روش پرداخت</span>
          <select v-model="paymentSetup.method" required>
            <option v-for="method in paymentMethods" :key="method.key" :value="method.key">{{ method.label }}</option>
          </select>
        </label>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePaymentSetup">لغو</button>
          <button class="action-btn tone-primary" type="submit">
            <span class="material-symbols-outlined">arrow_back</span>
            ادامه
          </button>
        </div>
      </form>
    </div>

    <div v-if="purchaseForm.open && selectedPurchaseOption" class="wallet-modal-backdrop" @click.self="closePurchase">
      <form class="wallet-modal purchase-modal" @submit.prevent="submitPurchase">
        <div class="modal-handle"></div>
        <div class="purchase-modal-head">
          <span class="material-symbols-outlined">workspace_premium</span>
          <div>
            <small>خرید مستقیم از کیف پول</small>
            <strong>{{ selectedPurchaseOption.title }}</strong>
          </div>
        </div>

        <p class="purchase-copy">{{ selectedPurchaseOption.description }}</p>

        <div class="purchase-plan-toggle">
          <button type="button" :class="{ active: purchaseForm.paymentPlan === 'cash' }" @click="purchaseForm.paymentPlan = 'cash'">
            <span class="material-symbols-outlined">payments</span>
            <b>نقدی</b>
            <small>{{ selectedPurchaseOption.cashAmount || selectedPurchaseOption.totalAmount }}</small>
          </button>
          <button type="button" :class="{ active: purchaseForm.paymentPlan === 'installment' }" @click="purchaseForm.paymentPlan = 'installment'">
            <span class="material-symbols-outlined">calendar_month</span>
            <b>اقساطی</b>
            <small>{{ selectedPurchaseOption.upfrontAmount || selectedPurchaseOption.monthlyInstallmentAmount }} امروز</small>
          </button>
        </div>

        <div class="purchase-details-grid">
          <article>
            <small>پرداخت الآن</small>
            <strong>{{ purchasePayNowLabel }}</strong>
          </article>
          <article>
            <small>اقساط</small>
            <strong>{{ selectedPurchaseOption.monthlyInstallmentAmount }} × {{ selectedPurchaseOption.installmentMonths }}</strong>
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
          <span class="material-symbols-outlined">account_balance_wallet</span>
          <div>
            <small>موجودی قابل استفاده</small>
            <strong>{{ purchaseWallet?.balance || '0.00' }}</strong>
          </div>
        </div>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePurchase">لغو</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.wallet.submitting">
            <span class="material-symbols-outlined">verified</span>
            تایید و خرید
          </button>
        </div>
      </form>
    </div>

    <div v-if="paymentGuide.open" class="wallet-modal-backdrop" @click.self="closePaymentGuide">
      <div class="wallet-modal payment-guide-modal">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <span class="material-symbols-outlined">credit_card</span>
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
          <button class="action-btn tone-soft" type="button" @click="closePaymentGuide">بستن</button>
          <button class="action-btn tone-primary" type="button" @click="openPaymentForm">
            <span class="material-symbols-outlined">verified</span>
            پرداخت کردم
          </button>
        </div>
      </div>
    </div>

    <div v-if="paymentForm.open" class="wallet-modal-backdrop" @click.self="closePaymentForm">
      <form class="wallet-modal payment-request-modal" @submit.prevent="submitPaymentTicket">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <span class="material-symbols-outlined">support_agent</span>
          <strong>ثبت درخواست تایید پرداخت</strong>
        </div>

        <div class="payment-summary-box">
          <b>{{ PAYMENT_SUBJECT }}</b>
          <small>روش پرداخت: {{ selectedPaymentMethodLabel }}</small>
          <small>بابت: {{ paymentForm.purpose || '-' }}</small>
          <small>فیلدها را بر اساس رسید پرداختی خود تکمیل کنید.</small>
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
            <span>کد تراکنش</span>
            <input v-model.trim="paymentForm.referenceCode" required dir="ltr" placeholder="پیگیری یا مرجع" />
          </label>
        </div>

        <label>
          <span>تصویر رسید</span>
          <input type="file" accept="image/*,.pdf" @change="setReceipt" />
        </label>

        <div class="modal-actions">
          <button class="action-btn tone-soft" type="button" @click="closePaymentForm">لغو</button>
          <button class="action-btn tone-primary" type="submit" :disabled="state.support.submitting">
            <span class="material-symbols-outlined">send</span>
            ارسال برای HQ
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<style scoped>
.wallet-page {
  --wallet-navy: #183153;
  --wallet-blue: #3763a8;
  --wallet-gold: #e09b58;
  --wallet-ink: #1f3557;
  --wallet-muted: #66758f;
  --wallet-line: rgba(32, 58, 105, 0.08);
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
  border-radius: 34px;
  background:
    radial-gradient(circle at 18% 20%, rgba(55, 99, 168, 0.18), transparent 34%),
    radial-gradient(circle at 76% 8%, rgba(224, 155, 88, 0.18), transparent 28%),
    linear-gradient(135deg, #f8fbff 0%, #eff4fb 48%, #fbfdff 100%);
  box-shadow: 0 24px 70px rgba(24, 41, 77, 0.12);
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

.wallet-hero-balance .material-symbols-outlined {
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
  border-radius: 22px;
  color: #fff;
  background: linear-gradient(135deg, #234783, var(--wallet-blue));
  box-shadow: 0 18px 38px rgba(35, 71, 131, 0.22);
  cursor: pointer;
}

.wallet-action b {
  font-size: 0.92rem;
  font-weight: 750;
}

.wallet-action.withdraw {
  color: var(--wallet-navy);
  background: #f1c56f;
}

.wallet-alert {
  padding: 14px 18px;
  border-radius: 18px;
  color: #254f85;
  background: rgba(55, 99, 168, 0.1);
  font-weight: 750;
}

.wallet-alert.danger {
  color: #8f1d1d;
  background: rgba(202, 65, 65, 0.12);
}

.wallet-license-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(171, 92, 28, 0.18);
  border-radius: 8px;
  color: #7a3f14;
  background: #fff6ea;
}

.wallet-license-alert .material-symbols-outlined {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  background: #a9581a;
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
  border: 1px solid color-mix(in srgb, var(--option-accent), transparent 78%);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 16px 38px rgba(24, 41, 77, 0.08);
}

.wallet-option-card.active {
  background: color-mix(in srgb, var(--option-accent), white 92%);
}

.wallet-option-head,
.wallet-option-price,
.wallet-option-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.wallet-option-head .material-symbols-outlined {
  color: var(--option-accent);
}

.wallet-option-head small {
  color: var(--option-accent);
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

.wallet-option-price {
  padding: 9px 10px;
  border-radius: 8px;
  background: #f7f3ea;
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

.wallet-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.wallet-summary-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  min-height: 138px;
  border: 1px solid var(--wallet-line);
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 16px 38px rgba(24, 41, 77, 0.08);
}

.wallet-summary-card .material-symbols-outlined {
  color: var(--wallet-blue);
}

.wallet-summary-card strong {
  color: var(--wallet-navy);
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
  border-radius: 24px;
  text-align: start;
  color: var(--wallet-ink);
  background: rgba(255, 255, 255, 0.68);
  cursor: pointer;
}

.wallet-tile.is-active {
  border-color: rgba(55, 99, 168, 0.3);
  background: linear-gradient(135deg, var(--wallet-navy), var(--wallet-blue));
  color: #fff;
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
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 18px 44px rgba(24, 41, 77, 0.08);
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
  background: #f7f3ea;
}

.ledger-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 16px;
}

.ledger-icon.in {
  color: #31589c;
  background: rgba(73, 114, 190, 0.12);
}

.ledger-icon.out {
  color: #8d5d1e;
  background: rgba(224, 155, 88, 0.18);
}

.ledger-row > div:nth-child(2) {
  flex: 1;
  display: grid;
  gap: 4px;
}

.ledger-row strong.in {
  color: #31589c;
}

.ledger-row strong.out {
  color: #8d5d1e;
}

.wallet-empty,
.wallet-loading {
  min-height: 280px;
  display: grid;
  place-items: center;
  border-radius: 30px;
  color: rgba(24, 49, 83, 0.55);
  background: rgba(255, 255, 255, 0.66);
}

.wallet-empty.compact {
  min-height: 240px;
  background: #f7f3ea;
}

.wallet-empty .material-symbols-outlined,
.wallet-loading .material-symbols-outlined {
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
  backdrop-filter: blur(10px);
}

.wallet-modal {
  width: min(520px, 100%);
  display: grid;
  gap: 16px;
  padding: 22px;
  border-radius: 30px;
  background: #f8fbff;
  box-shadow: 0 30px 90px rgba(24, 41, 77, 0.28);
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
  background: linear-gradient(135deg, var(--wallet-navy), var(--wallet-blue));
}

.purchase-modal-head > .material-symbols-outlined {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  color: var(--wallet-navy);
  background: #f1c56f;
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
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, var(--wallet-navy), var(--wallet-blue));
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

.purchase-wallet-box .material-symbols-outlined {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #31589c;
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
  border-radius: 22px;
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
  .wallet-summary-grid,
  .wallet-options-grid,
  .purchase-plan-toggle,
  .purchase-details-grid,
  .payment-grid {
    grid-template-columns: 1fr;
  }
}
</style>


