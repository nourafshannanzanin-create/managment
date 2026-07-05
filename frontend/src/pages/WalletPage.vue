<script setup>
import { computed, onMounted, reactive, watch } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const { state, loadWalletDashboard, submitWalletTransaction } = useWorkflowHub()

const form = reactive({
  open: false,
  direction: 'in',
  walletId: '',
  amount: '',
  note: '',
})

const canUseWallet = computed(() => state.currentUser.isManager || state.currentUser.canUseHq)
const needsOrganization = computed(() => state.currentUser.isHq && !state.hq.selectedOrganizationId)
const wallets = computed(() => state.wallet.wallets || [])
const transactions = computed(() => state.wallet.transactions || [])
const activeWallet = computed(() => wallets.value.find((item) => String(item.id) === String(form.walletId)) || wallets.value[0] || null)

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

function openTransaction(direction) {
  form.direction = direction
  form.walletId = activeWallet.value?.id ? String(activeWallet.value.id) : ''
  form.amount = ''
  form.note = ''
  form.open = true
  state.wallet.error = ''
  state.wallet.message = ''
}

function closeTransaction() {
  form.open = false
}

async function submitTransaction() {
  await submitWalletTransaction({
    direction: form.direction,
    walletId: Number(form.walletId),
    amount: form.amount,
    note: form.note,
  })
  closeTransaction()
}

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
            :class="['wallet-tile', String(wallet.id) === String(form.walletId || activeWallet?.id) && 'is-active']"
            type="button"
            @click="form.walletId = String(wallet.id)"
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
            <b>{{ transactions.length }}</b>
          </div>

          <div v-if="state.wallet.loading" class="wallet-loading">
            <span class="material-symbols-outlined">progress_activity</span>
          </div>

          <div v-else-if="!transactions.length" class="wallet-empty compact">
            <span class="material-symbols-outlined">receipt_long</span>
          </div>

          <div v-else class="ledger-list">
            <article v-for="item in transactions" :key="item.id" class="ledger-row">
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

    <div v-if="form.open" class="wallet-modal-backdrop" @click.self="closeTransaction">
      <form class="wallet-modal" @submit.prevent="submitTransaction">
        <div class="modal-handle"></div>
        <div class="modal-title">
          <span class="material-symbols-outlined">{{ form.direction === 'in' ? 'add_card' : 'payments' }}</span>
          <strong>{{ form.direction === 'in' ? 'شارژ کیف پول' : 'برداشت از کیف پول' }}</strong>
        </div>

        <label>
          <span>کیف پول</span>
          <select v-model="form.walletId" required>
            <option v-for="wallet in wallets" :key="wallet.id" :value="wallet.id">{{ wallet.name }}</option>
          </select>
        </label>

        <label>
          <span>مبلغ</span>
          <input v-model="form.amount" inputmode="decimal" required placeholder="0" />
        </label>

        <label>
          <span>یادداشت</span>
          <textarea v-model="form.note" rows="3"></textarea>
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
.wallet-modal label span {
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
  width: min(460px, 100%);
  display: grid;
  gap: 16px;
  padding: 22px;
  border-radius: 30px;
  background: #f8fbff;
  box-shadow: 0 30px 90px rgba(24, 41, 77, 0.28);
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

  .wallet-summary-grid {
    grid-template-columns: 1fr;
  }

  .ledger-row {
    flex-wrap: wrap;
  }
}
</style>
