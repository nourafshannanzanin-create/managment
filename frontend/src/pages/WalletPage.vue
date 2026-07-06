<script setup>
import { computed, onMounted, reactive, watch } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const CARD_NUMBER = '6037991719847703'
const CARD_HOLDER = 'میلاد دهستانی'
const PAYMENT_SUBJECT = 'پرداخت کیف پول'

const { state, loadWalletDashboard, submitWalletTransaction, createSupportTicket } = useWorkflowHub()

const transactionForm = reactive({
  open: false,
  direction: 'in',
  walletId: '',
  amount: '',
  note: '',
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

const canUseWallet = computed(() => state.currentUser.isManager || state.currentUser.canUseHq)
const needsOrganization = computed(() => state.currentUser.isHq && !state.hq.selectedOrganizationId)
const wallets = computed(() => state.wallet.wallets || [])
const transactions = computed(() => state.wallet.transactions || [])
const activeWallet = computed(() => {
  const activeId = transactionForm.walletId || paymentSetup.walletId || paymentGuide.walletId || paymentForm.walletId
  return wallets.value.find((item) => String(item.id) === String(activeId)) || wallets.value[0] || null
})
const usesManagerPaymentFlow = computed(() => state.currentUser.isManager && !state.currentUser.canUseHq)

const paymentMethods = [
  { key: 'app', label: 'آپ' },
  { key: 'pos', label: 'دستگاه پرداخت' },
  { key: 'card_to_card', label: 'کارت به کارت' },
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
    date: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
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
    'درخواست تایید پرداخت کیف پول',
    `کیف پول: ${wallet?.name || '-'}`,
    `WALLET_ID: ${wallet?.id || ''}`,
    `روش پرداخت: ${selectedPaymentMethodLabel.value}`,
    `بابت: ${paymentForm.purpose || '-'}`,
    `تاریخ: ${paymentForm.date}`,
    `ساعت: ${paymentForm.time}`,
    `مبلغ: ${paymentForm.amount}`,
    `کد تراکنش: ${paymentForm.referenceCode}`,
    ...(paymentForm.method === 'card_to_card'
      ? [`شماره کارت مقصد: ${CARD_NUMBER}`, `نام صاحب کارت: ${CARD_HOLDER}`]
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

onMounted(() => {
  void loadWalletDashboard(true)
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
        <div class="wallet-orb"></div>
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
            :class="['wallet-tile', String(wallet.id) === String(transactionForm.walletId || paymentSetup.walletId || paymentGuide.walletId || paymentForm.walletId || activeWallet?.id) && 'is-active']"
            type="button"
            @click="transactionForm.walletId = String(wallet.id); paymentSetup.walletId = String(wallet.id); paymentGuide.walletId = String(wallet.id); paymentForm.walletId = String(wallet.id)"
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
          <span>مبلغ</span>
          <input v-model="transactionForm.amount" inputmode="decimal" required placeholder="0" />
        </label>

        <label>
          <span>یادداشت</span>
          <textarea v-model="transactionForm.note" rows="3"></textarea>
        </label>

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
              <option v-for="wallet in wallets" :key="wallet.id" :value="wallet.id">{{ wallet.name }}</option>
            </select>
          </label>
          <label>
            <span>مبلغ</span>
            <input v-model.trim="paymentSetup.amount" inputmode="decimal" required placeholder="0" />
          </label>
        </div>

        <label>
          <span>بابت چه چیزی</span>
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
        </div>

        <div class="payment-grid">
          <label>
            <span>تاریخ</span>
            <input v-model.trim="paymentForm.date" required placeholder="1405-04-16" />
          </label>
          <label>
            <span>ساعت</span>
            <input v-model.trim="paymentForm.time" required placeholder="14:35" />
          </label>
          <label>
            <span>مبلغ</span>
            <input v-model.trim="paymentForm.amount" inputmode="decimal" required placeholder="0" />
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

.wallet-orb {
  position: absolute;
  inset-inline-end: 28%;
  inset-block-start: -90px;
  width: 260px;
  height: 260px;
  border-radius: 999px;
  background: linear-gradient(145deg, rgba(55, 99, 168, 0.22), rgba(224, 155, 88, 0.18));
  filter: blur(3px);
}

.wallet-hero-balance,
.wallet-actions,
.wallet-summary-card,
.wallet-tile,
.wallet-ledger,
.wallet-modal {
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
  font-size: clamp(2.4rem, 8vw, 5rem);
  line-height: 1;
  letter-spacing: -0.08em;
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
  font-weight: 800;
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

.wallet-action.withdraw {
  color: var(--wallet-navy);
  background: #f1c56f;
}

.wallet-alert {
  padding: 14px 18px;
  border-radius: 18px;
  color: #254f85;
  background: rgba(55, 99, 168, 0.1);
  font-weight: 900;
}

.wallet-alert.danger {
  color: #8f1d1d;
  background: rgba(202, 65, 65, 0.12);
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
  font-size: 1.35rem;
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
  font-size: 1.45rem;
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
  font-size: 3.4rem;
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
  font-size: 1.1rem;
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
  font-size: 1.2rem;
  letter-spacing: 0.04em;
}

.payment-card-box span {
  color: var(--wallet-ink);
  font-weight: 800;
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
}

@media (max-width: 640px) {
  .wallet-hero {
    padding: 20px;
    border-radius: 26px;
  }

  .wallet-summary-grid,
  .payment-grid {
    grid-template-columns: 1fr;
  }

  .ledger-row,
  .modal-actions {
    flex-wrap: wrap;
  }
}
</style>
