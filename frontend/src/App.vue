<script setup>
import IconlyIcon from './components/base/IconlyIcon.vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import ApprovalDetailModal from './components/ApprovalDetailModal.vue'
import AppSidebar from './components/AppSidebar.vue'
import AppTopNav from './components/AppTopNav.vue'
import DocumentComposerModal from './components/DocumentComposerModal.vue'
import ErrorNotice from './components/ErrorNotice.vue'
import ExpenseComposerModal from './components/ExpenseComposerModal.vue'
import ExpenseDetailModal from './components/ExpenseDetailModal.vue'
import MobileBottomNav from './components/MobileBottomNav.vue'
import RequestComposerModal from './components/RequestComposerModal.vue'
import RequestDetailModal from './components/RequestDetailModal.vue'
import SignatureComposerModal from './components/SignatureComposerModal.vue'
import UserComposerModal from './components/UserComposerModal.vue'
import ToastHost from './components/ToastHost.vue'
import { unlockTicketAlerts } from './utils/ticketAlert'
import { useWorkflowHub } from './stores/workflowHub'

const route = useRoute()
const hub = useWorkflowHub()
const routeLoading = ref(false)
const nowTick = ref(Date.now())
let trialCountdownTimer = null
let trialExpiryHandled = false
let liveSyncTimer = null

const {
  state,
  modalState,
  requestDetailState,
  expenseDetailState,
  approvalDetailState,
  signatureState,
  selectedRequest,
  selectedExpense,
  selectedApproval,
  restoreSession,
  loadBootstrapData,
  softLiveSync,
  loadReports,
  loadSettings,
  loadWalletDashboard,
  loadSupportTickets,
  loadHqPanel,
  closeRequestDetail,
  closeExpenseDetail,
  closeApprovalDetail,
  closeRequestComposer,
  closeExpenseComposer,
  closeUserComposer,
  closeDocumentComposer,
  closeSignatureComposer,
  toggleSidebar,
} = hub

const isAuthRoute = computed(() => Boolean(route.meta.publicCanvas) || route.path === '/login' || route.path === '/')
const isLandingRoute = computed(() => Boolean(route.meta.landing) || route.name === 'landing')
const isPublicAttendanceRoute = computed(() => route.name === 'public-attendance')
const licenseSafeRoutes = new Set(['/dashboard', '/wallet', '/support', '/login', '/'])

const licenseStatus = computed(() => state.currentUser.licenseStatus || {})
const isLicenseLocked = computed(() => Boolean(licenseStatus.value?.isLocked || licenseStatus.value?.is_locked))
const showSmsBalanceWarning = computed(() =>
  !isAuthRoute.value &&
  state.authToken &&
  state.bootstrapLoaded &&
  !state.wallet.schematic &&
  (!state.currentUser.isHq || state.hq.selectedOrganizationId) &&
  (
    state.wallet.summary.smsIsLow === true ||
    Number(state.wallet.summary.smsBalanceRaw || 0) <= Number(state.wallet.summary.smsLowBalanceThresholdRaw || 0)
  ),
)
const smsBalanceWarningText = computed(() =>
  Number(state.wallet.summary.smsBalanceRaw || 0) <= 0
    ? 'شارژ پیامک تمام شده است؛ برای ادامه ارسال پیامک، پنل فراز/کیف پیامک را شارژ کنید.'
    : 'شارژ پیامک رو به اتمام است؛ قبل از توقف ارسال پیامک، پنل فراز/کیف پیامک را شارژ کنید.',
)

function toFaDigits(value) {
  return String(value ?? '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[digit] || digit)
}

function formatCountdown(totalSeconds) {
  const safe = Math.max(0, Number(totalSeconds) || 0)
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const seconds = safe % 60
  const pad = (n) => String(n).padStart(2, '0')
  return toFaDigits(`${pad(hours)}:${pad(minutes)}:${pad(seconds)}`)
}

const trialEndsAtMs = computed(() => {
  const raw = licenseStatus.value?.trialEndsAt || licenseStatus.value?.trial_ends_at || ''
  if (!raw) return 0
  const parsed = Date.parse(raw)
  return Number.isFinite(parsed) ? parsed : 0
})

const trialRemainingSeconds = computed(() => {
  if (!trialEndsAtMs.value) return 0
  return Math.max(0, Math.floor((trialEndsAtMs.value - nowTick.value) / 1000))
})

const showTrialBanner = computed(() =>
  !isAuthRoute.value &&
  Boolean(state.authToken) &&
  Boolean(state.bootstrapLoaded) &&
  !state.currentUser.isHq &&
  Boolean(licenseStatus.value?.trialActive || licenseStatus.value?.trial_active) &&
  trialRemainingSeconds.value > 0,
)

const trialProgressPercent = computed(() => {
  const totalHours = Number(licenseStatus.value?.trialHours || licenseStatus.value?.trial_hours || 24) || 24
  const totalSeconds = Math.max(totalHours * 3600, 1)
  return Math.min(100, Math.max(0, (trialRemainingSeconds.value / totalSeconds) * 100))
})

const trialBannerText = computed(() =>
  `زمان باقی‌مانده تا اتمام استفاده رایگان: ${formatCountdown(trialRemainingSeconds.value)}`,
)

function stopTrialCountdown() {
  if (trialCountdownTimer) {
    window.clearInterval(trialCountdownTimer)
    trialCountdownTimer = null
  }
}

function startTrialCountdown() {
  stopTrialCountdown()
  nowTick.value = Date.now()
  trialCountdownTimer = window.setInterval(() => {
    nowTick.value = Date.now()
  }, 1000)
}

async function handleTrialExpiry() {
  if (trialExpiryHandled) return
  trialExpiryHandled = true
  stopTrialCountdown()
  try {
    await loadBootstrapData(true)
  } finally {
    if (isLicenseLocked.value && !licenseSafeRoutes.has(route.path)) {
      await hub.navigateTo('/wallet')
    }
  }
}
const globalLoading = computed(() =>
  isLandingRoute.value
    ? false
    : (
  (!state.sessionReady && !state.bootstrapLoaded) ||
  (state.appLoading && !state.bootstrapLoaded) ||
  state.loginPending ||
  requestDetailState.loading ||
  expenseDetailState.loading ||
  approvalDetailState.loading ||
  state.requestSubmitting ||
  state.expenseSubmitting ||
  state.userSubmitting ||
  state.documentSubmitting ||
  state.fileUploadPreparing ||
  state.support.detailLoading ||
  state.support.submitting ||
  state.wallet.submitting ||
  signatureState.loading
    )
)

watch(showTrialBanner, (active) => {
  if (active) {
    trialExpiryHandled = false
    startTrialCountdown()
    return
  }
  stopTrialCountdown()
}, { immediate: true })

watch(trialRemainingSeconds, (value, previous) => {
  if ((previous ?? 0) > 0 && value <= 0 && (licenseStatus.value?.trialActive || licenseStatus.value?.trial_active)) {
    void handleTrialExpiry()
  }
})

async function refreshRouteData(path, { soft = false } = {}) {
  if (!state.authToken || path === '/login' || path === '/') return

  await loadBootstrapData(true, { soft: soft || state.bootstrapLoaded })

  if (isLicenseLocked.value && !licenseSafeRoutes.has(path)) {
    await hub.navigateTo('/wallet')
    return
  }

  if (path === '/support') {
    if (state.currentUser.accessRole === 'admin' || state.currentUser.isHq || state.currentUser.canUseHq) {
      await loadSupportTickets(true, { soft: true })
    }
    return
  }

  if (path === '/wallet') {
    await loadWalletDashboard(true)
    return
  }

  if (path === '/hq') {
    unlockTicketAlerts()
    await loadHqPanel(true, { soft: true })
    await loadSupportTickets(true, { soft: true, notifyNew: false })
    return
  }

  if (path === '/reports') {
    await loadReports(true)
    return
  }

  if (path === '/settings') {
    await loadSettings(true)
  }
}

watch(
  () => route.fullPath,
  async () => {
    state.mobileMenuOpen = false

    if (!state.sessionReady) return
    const soft = Boolean(state.bootstrapLoaded)
    if (!soft) routeLoading.value = true
    try {
      await refreshRouteData(route.path, { soft })
    } finally {
      routeLoading.value = false
    }
  },
)

onMounted(async () => {
  window.addEventListener('pointerdown', unlockTicketAlerts, { once: true })
  window.addEventListener('keydown', unlockTicketAlerts, { once: true })

  await restoreSession()
  await refreshRouteData(route.path, { soft: false })
  if (state.currentUser.isHq) {
    unlockTicketAlerts()
  }
  await softLiveSync({ includeSupport: true })

  liveSyncTimer = window.setInterval(() => {
    if (!state.authToken || state.liveSync.inFlight) return
    void softLiveSync({ includeSupport: true })
  }, 8000)
})

onUnmounted(() => {
  if (liveSyncTimer) {
    window.clearInterval(liveSyncTimer)
  }
  stopTrialCountdown()
  window.removeEventListener('pointerdown', unlockTicketAlerts)
  window.removeEventListener('keydown', unlockTicketAlerts)
})
</script>

<template>
  <div
    class="app-shell"
    :class="{
      'is-auth-route': isAuthRoute,
      'is-landing-route': isLandingRoute,
      'is-public-attendance': isPublicAttendanceRoute,
      'has-trial-banner': showTrialBanner,
      'has-mobile-menu-open': !isAuthRoute && state.mobileMenuOpen,
    }"
  >
    <template v-if="!isAuthRoute">
      <div class="shell-backdrop" :class="{ 'is-open': state.mobileMenuOpen }" @click="toggleSidebar"></div>
      <AppSidebar :mobile-menu-open="state.mobileMenuOpen" :toggle-sidebar="toggleSidebar" />

      <div class="shell-main">
        <div
          v-if="showTrialBanner"
          class="global-trial-banner"
          role="status"
          aria-live="polite"
        >
          <div class="global-trial-banner__content">
            <IconlyIcon name="calendar" decorative />
            <strong>{{ trialBannerText }}</strong>
          </div>
          <div class="global-trial-banner__track" aria-hidden="true">
            <span class="global-trial-banner__fill" :style="{ width: `${trialProgressPercent}%` }"></span>
          </div>
        </div>
        <main class="shell-content">
          <AppTopNav />
          <div class="shell-content-body">
            <ToastHost />
            <div v-if="showSmsBalanceWarning" class="global-sms-warning">
              <IconlyIcon name="sms_failed" decorative />
              <strong>{{ smsBalanceWarningText }}</strong>
            </div>
            <ErrorNotice
              v-if="state.lastErrorDetails && !modalState.requestComposer && !modalState.expenseComposer && !modalState.userComposer && !modalState.documentComposer"
              :error="state.lastErrorDetails"
            />
            <RouterView v-slot="{ Component }">
              <component :is="Component" :key="route.fullPath" />
            </RouterView>
          </div>
        </main>
        <MobileBottomNav />
      </div>
    </template>

    <main
      v-else
      class="shell-main auth-main"
      :class="{
        'landing-main': isLandingRoute,
        'public-canvas-main': Boolean(route.meta.publicCanvas) && !isLandingRoute,
      }"
    >
      <div
        class="shell-content"
        :class="{
          'landing-content': isLandingRoute,
          'public-canvas-content': Boolean(route.meta.publicCanvas) && !isLandingRoute,
        }"
      >
        <RouterView v-slot="{ Component }">
          <component :is="Component" :key="route.fullPath" />
        </RouterView>
      </div>
    </main>

    <RequestDetailModal
      :open="modalState.requestDetail"
      :request="selectedRequest"
      :loading="requestDetailState.loading"
      @close="closeRequestDetail"
    />

    <ExpenseDetailModal
      :open="modalState.expenseDetail"
      :expense="selectedExpense"
      :loading="expenseDetailState.loading"
      @close="closeExpenseDetail"
    />

    <ApprovalDetailModal
      :open="modalState.approvalDetail"
      :approval="selectedApproval"
      :loading="approvalDetailState.loading"
      @close="closeApprovalDetail"
    />

    <RequestComposerModal
      :open="modalState.requestComposer"
      :form="state.requestForm"
      :submitting="state.requestSubmitting"
      @close="closeRequestComposer"
    />

    <ExpenseComposerModal
      :open="modalState.expenseComposer"
      :form="state.expenseForm"
      :submitting="state.expenseSubmitting"
      @close="closeExpenseComposer"
    />

    <UserComposerModal
      :open="modalState.userComposer"
      :form="state.userForm"
      :submitting="state.userSubmitting"
      @close="closeUserComposer"
    />

    <DocumentComposerModal
      :open="modalState.documentComposer"
      :form="state.documentForm"
      :submitting="state.documentSubmitting"
      @close="closeDocumentComposer"
    />

    <SignatureComposerModal :open="modalState.signatureComposer" @close="closeSignatureComposer" />

    <Teleport to="body">
      <div
        v-if="globalLoading"
        class="loading-overlay"
        aria-label="در حال بارگذاری"
        aria-live="polite"
        aria-busy="true"
        role="status"
      >
        <div class="app-loading-spinner" aria-hidden="true"></div>
      </div>
    </Teleport>
  </div>
</template>

<style>
.loading-overlay {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.55);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  isolation: isolate;
  z-index: 2147483647;
}

.app-loading-spinner {
  width: 65px;
  height: 65px;
  flex: 0 0 65px;
  position: relative;
  z-index: 1;
  color: #ffffff;
  filter: drop-shadow(0 0 7px rgba(255, 255, 255, 0.55));
}

.app-loading-spinner::before,
.app-loading-spinner::after {
  content: "";
  position: absolute;
  inset: 0;
  display: block;
  border-radius: 50px;
  box-shadow: inset 0 0 0 3px currentColor;
  animation: app-loader-orbit 2.5s linear infinite;
}

.app-loading-spinner::after {
  animation-delay: -1.25s;
}

@keyframes app-loader-orbit {
  0% {
    inset: 0 35px 35px 0;
  }

  12.5% {
    inset: 0 35px 0 0;
  }

  25% {
    inset: 35px 35px 0 0;
  }

  37.5% {
    inset: 35px 0 0 0;
  }

  50% {
    inset: 35px 0 0 35px;
  }

  62.5% {
    inset: 0 0 0 35px;
  }

  75% {
    inset: 0 0 35px 35px;
  }

  87.5% {
    inset: 0 0 35px 0;
  }

  100% {
    inset: 0 35px 35px 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-loading-spinner::before,
  .app-loading-spinner::after {
    animation-duration: 5s;
  }
}
</style>
