<script setup>
import IconlyIcon from './components/base/IconlyIcon.vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import ApprovalDetailModal from './components/ApprovalDetailModal.vue'
import ArchiveComposerModal from './components/ArchiveComposerModal.vue'
import ArchiveDetailModal from './components/ArchiveDetailModal.vue'
import AppSidebar from './components/AppSidebar.vue'
import AppTopNav from './components/AppTopNav.vue'
import HubTabBar from './components/HubTabBar.vue'
import DocumentComposerModal from './components/DocumentComposerModal.vue'
import ErrorNotice from './components/ErrorNotice.vue'
import ExpenseComposerModal from './components/ExpenseComposerModal.vue'
import ExpenseDetailModal from './components/ExpenseDetailModal.vue'
import MobileBottomNav from './components/MobileBottomNav.vue'
import RequestComposerModal from './components/RequestComposerModal.vue'
import RequestDetailModal from './components/RequestDetailModal.vue'
import SignatureComposerModal from './components/SignatureComposerModal.vue'
import TrialBanner from './components/TrialBanner.vue'
import UserComposerModal from './components/UserComposerModal.vue'
import ToastHost from './components/ToastHost.vue'
import { unlockTicketAlerts } from './utils/ticketAlert'
import { createLiveEventSource, parseLiveEvent } from './utils/live'
import { prefetchCommonRoutes } from './utils/prefetchRoute'
import { useWorkflowHub } from './stores/workflowHub'

const route = useRoute()
const router = useRouter()
const hub = useWorkflowHub()
const routeLoading = ref(false)
let trialExpiryHandled = false
let liveSyncTimer = null
let liveStream = null
let liveRefreshTimer = null

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
  loadArchiveDocuments,
  closeRequestDetail,
  closeExpenseDetail,
  closeApprovalDetail,
  closeRequestComposer,
  closeExpenseComposer,
  closeUserComposer,
  closeDocumentComposer,
  closeSignatureComposer,
  closeArchiveComposer,
  closeArchiveDetail,
  openArchiveDetail,
  toggleSidebar,
} = hub

const isAuthRoute = computed(() => Boolean(route.meta.publicCanvas || route.meta.landing || route.meta.public) || route.path === '/login' || route.path === '/')
const isLandingRoute = computed(() => route.name === 'landing' || route.path === '/' || Boolean(route.meta.landing))
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

const trialEndsAt = computed(
  () => licenseStatus.value?.trialEndsAt || licenseStatus.value?.trial_ends_at || '',
)
const trialHours = computed(
  () => Number(licenseStatus.value?.trialHours || licenseStatus.value?.trial_hours || 24) || 24,
)
const showTrialBanner = computed(() =>
  !isAuthRoute.value &&
  Boolean(state.authToken) &&
  Boolean(state.bootstrapLoaded) &&
  !state.currentUser.isHq &&
  Boolean(licenseStatus.value?.trialActive || licenseStatus.value?.trial_active) &&
  Boolean(trialEndsAt.value),
)

function stopLiveSync() {
  if (liveSyncTimer) {
    window.clearInterval(liveSyncTimer)
    liveSyncTimer = null
  }
  if (liveRefreshTimer) {
    window.clearTimeout(liveRefreshTimer)
    liveRefreshTimer = null
  }
  if (liveStream) {
    liveStream.close()
    liveStream = null
  }
}

const workflowLiveTypes = new Set([
  'request.created',
  'request.updated',
  'expense.created',
  'expense.updated',
  'document.created',
  'document.updated',
  'support.ticket.created',
  'support.ticket.updated',
  'support.message.created',
  'chat.message.created',
  'task.created',
  'task.updated',
  'task.comment.created',
  'attendance.created',
  'wallet.transaction.created',
  'wallet.transaction.updated',
])

function scheduleLiveSync() {
  if (!state.authToken || state.liveSync.inFlight) return
  if (liveRefreshTimer) window.clearTimeout(liveRefreshTimer)
  liveRefreshTimer = window.setTimeout(() => {
    void softLiveSync({ includeSupport: true })
  }, 800)
}

function startLiveSync() {
  stopLiveSync()
  if (!state.authToken) return
  liveStream = createLiveEventSource(state.authToken)
  liveStream?.addEventListener('open', scheduleLiveSync)
  liveStream?.addEventListener('message', (event) => {
    const payload = parseLiveEvent(event.data)
    if (!payload?.type || (payload.type !== 'system.full_resync_required' && !workflowLiveTypes.has(payload.type))) return
    scheduleLiveSync()
  })
  liveSyncTimer = window.setInterval(() => {
    if (!state.authToken || state.liveSync.inFlight || document.visibilityState !== 'visible') return
    void softLiveSync({ includeSupport: true })
  }, 90000)
}

async function handleTrialExpiry() {
  if (trialExpiryHandled) return
  trialExpiryHandled = true
  try {
    await loadBootstrapData(true)
  } finally {
    if (isLicenseLocked.value && !licenseSafeRoutes.has(route.path)) {
      await hub.navigateTo('/wallet')
    }
  }
}
const globalLoading = computed(() =>
  (!state.sessionReady && !state.bootstrapLoaded) ||
  (state.appLoading && !state.bootstrapLoaded) ||
  state.loginPending
)

const bootstrapBlocking = computed(() =>
  Boolean(state.authToken) && (
    (!state.sessionReady && !state.bootstrapLoaded) ||
    (state.appLoading && !state.bootstrapLoaded) ||
    state.loginPending
  ),
)

let loadingWatchdogTimer = null
watch(bootstrapBlocking, (blocked) => {
  if (loadingWatchdogTimer) {
    window.clearTimeout(loadingWatchdogTimer)
    loadingWatchdogTimer = null
  }
  if (!blocked) return
  loadingWatchdogTimer = window.setTimeout(() => {
    state.appLoading = false
    state.loginPending = false
    state.sessionReady = true
    if (!state.bootstrapLoaded) {
      state.lastError = 'بارگذاری اولیه طولانی شد. صفحه را تازه کنید یا اتصال را بررسی کنید.'
    }
  }, 45000)
})

watch(showTrialBanner, (active) => {
  if (active) trialExpiryHandled = false
})

async function refreshRouteData(path, { soft = false } = {}) {
  if (!state.authToken || path === '/login' || path === '/') return

  // Only block on bootstrap when it has never loaded; soft navigations must stay instant.
  if (!state.bootstrapLoaded) {
    await loadBootstrapData(true, { soft: false })
  } else if (!soft) {
    await loadBootstrapData(true, { soft: true })
  }

  if (isLicenseLocked.value && !licenseSafeRoutes.has(path)) {
    await hub.navigateTo('/wallet')
    return
  }

  // Soft menu navigations: each page loads its own data on mount.
  // Re-fetching here doubles network + reactive work and makes the shell feel laggy.
  if (soft) {
    if (path === '/hq') unlockTicketAlerts()
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

  if (path === '/expenses') {
    return
  }

  if (path === '/archive') {
    await loadArchiveDocuments(true)
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
  () => route.path,
  () => {
    state.mobileMenuOpen = false
    if (!state.sessionReady) return
    const soft = Boolean(state.bootstrapLoaded)
    // Never await route data in the watcher — keep menu clicks responsive.
    if (!soft) {
      routeLoading.value = true
      void refreshRouteData(route.path, { soft: false }).finally(() => {
        routeLoading.value = false
      })
      return
    }
    void refreshRouteData(route.path, { soft: true })
  },
)

watch(
  () => state.authToken,
  (token) => {
    if (token) {
      startLiveSync()
      return
    }
    stopLiveSync()
    // Public surfaces (landing, login, attendance) must stay put.
    if (isAuthRoute.value || isLandingRoute.value || isPublicAttendanceRoute.value) return
    if (route.path !== '/login' && route.path !== '/') {
      window.location.replace('/login')
    }
  },
)

onMounted(async () => {
  window.addEventListener('pointerdown', unlockTicketAlerts, { once: true })
  window.addEventListener('keydown', unlockTicketAlerts, { once: true })

  // Attach live stream before awaits so navigation mid-load cannot leak listeners.
  if (state.authToken) startLiveSync()

  await restoreSession()
  // Route extras only — bootstrap already loaded in restoreSession.
  await refreshRouteData(route.path, { soft: true })
  if (state.currentUser.isHq) {
    unlockTicketAlerts()
  }
  if (state.authToken) startLiveSync()
  // Background badge sync — never block first paint.
  void softLiveSync({ includeSupport: true, includeBootstrap: false })

  const warmRoutes = () => {
    prefetchCommonRoutes(router, [
      '/dashboard',
      '/requests',
      '/expenses',
      '/approvals',
      '/tasking',
      '/reports',
      '/users',
      '/settings',
      '/wallet',
      '/archive',
      '/chat',
      '/attendance',
    ])
  }
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(warmRoutes, { timeout: 4000 })
  } else {
    window.setTimeout(warmRoutes, 800)
  }
})

onUnmounted(() => {
  stopLiveSync()
  if (loadingWatchdogTimer) {
    window.clearTimeout(loadingWatchdogTimer)
    loadingWatchdogTimer = null
  }
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
        <TrialBanner
          :active="showTrialBanner"
          :trial-ends-at="trialEndsAt"
          :trial-hours="trialHours"
          @expired="handleTrialExpiry"
        />
        <main class="shell-content">
          <AppTopNav />
          <div class="shell-content-body">
            <ToastHost />
            <div v-if="showSmsBalanceWarning" class="global-sms-warning">
              <IconlyIcon name="sms_failed" decorative />
              <strong>{{ smsBalanceWarningText }}</strong>
            </div>
            <ErrorNotice
              v-if="state.lastErrorDetails && !modalState.requestComposer && !modalState.expenseComposer && !modalState.userComposer && !modalState.documentComposer && !modalState.archiveComposer"
              :error="state.lastErrorDetails"
            />
            <HubTabBar />
            <RouterView v-slot="{ Component }">
              <component :is="Component" :key="route.path" />
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
          <component :is="Component" :key="route.path" />
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

    <ArchiveComposerModal
      :open="modalState.archiveComposer"
      :form="state.archiveForm"
      :submitting="state.archiveSubmitting"
      @close="closeArchiveComposer"
    />

    <ArchiveDetailModal
      :open="modalState.archiveDetail"
      :item="state.archive.selected"
      @close="closeArchiveDetail"
      @updated="(item) => item && openArchiveDetail(item)"
      @deleted="closeArchiveDetail"
    />

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
