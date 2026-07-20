<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import ApprovalDetailModal from './components/ApprovalDetailModal.vue'
import AppSidebar from './components/AppSidebar.vue'
import AppTopNav from './components/AppTopNav.vue'
import DocumentComposerModal from './components/DocumentComposerModal.vue'
import ErrorNotice from './components/ErrorNotice.vue'
import ExpenseComposerModal from './components/ExpenseComposerModal.vue'
import ExpenseDetailModal from './components/ExpenseDetailModal.vue'
import RequestComposerModal from './components/RequestComposerModal.vue'
import RequestDetailModal from './components/RequestDetailModal.vue'
import SignatureComposerModal from './components/SignatureComposerModal.vue'
import UserComposerModal from './components/UserComposerModal.vue'
import { useWorkflowHub } from './stores/workflowHub'

const route = useRoute()
const hub = useWorkflowHub()
const routeLoading = ref(false)

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
  selectedRequestTimeline,
  restoreSession,
  loadBootstrapData,
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

const isAuthRoute = computed(() => route.path === '/login' || route.meta.publicCanvas)
const licenseSafeRoutes = new Set(['/dashboard', '/wallet', '/support', '/login'])
const isLicenseLocked = computed(() => Boolean(state.currentUser.licenseStatus?.isLocked || state.currentUser.licenseStatus?.is_locked))
const showSmsBalanceWarning = computed(() =>
  !isAuthRoute.value &&
  state.authToken &&
  state.bootstrapLoaded &&
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
const globalLoading = computed(() =>
  routeLoading.value ||
  !state.sessionReady ||
  state.appLoading ||
  state.loginPending ||
  requestDetailState.loading ||
  expenseDetailState.loading ||
  approvalDetailState.loading ||
  state.requestSubmitting ||
  state.expenseSubmitting ||
  state.userSubmitting ||
  state.documentSubmitting ||
  state.support.loading ||
  state.wallet.loading ||
  state.hq.loading ||
  signatureState.loading,
)
let hqSupportRefreshTimer = null
let routeLoadingTimer = null

function showRouteLoading() {
  if (routeLoadingTimer) {
    window.clearTimeout(routeLoadingTimer)
    routeLoadingTimer = null
  }
  routeLoading.value = true
}

function hideRouteLoading() {
  if (routeLoadingTimer) window.clearTimeout(routeLoadingTimer)
  routeLoadingTimer = window.setTimeout(() => {
    routeLoading.value = false
    routeLoadingTimer = null
  }, 220)
}

async function refreshRouteData(path) {
  if (!state.authToken || path === '/login') return

  await loadBootstrapData(true)

  if (isLicenseLocked.value && !licenseSafeRoutes.has(path)) {
    await hub.navigateTo('/wallet')
    return
  }

  if (path === '/support') {
    await loadSupportTickets(true)
    return
  }

  if (path === '/wallet') {
    await loadWalletDashboard(true)
    return
  }

  if (path === '/hq') {
    await loadHqPanel(true)
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
    showRouteLoading()
    state.mobileMenuOpen = false

    try {
      if (!state.sessionReady) return
      await refreshRouteData(route.path)
    } finally {
      hideRouteLoading()
    }
  },
)

onMounted(async () => {
  await restoreSession()
  await refreshRouteData(route.path)
  hqSupportRefreshTimer = window.setInterval(() => {
    if (!state.authToken || !state.currentUser.isHq || state.support.loading) return
    void loadSupportTickets(true)
  }, 30000)
})

onUnmounted(() => {
  if (hqSupportRefreshTimer) {
    window.clearInterval(hqSupportRefreshTimer)
  }
  if (routeLoadingTimer) {
    window.clearTimeout(routeLoadingTimer)
  }
})
</script>

<template>
  <div class="app-shell" :class="{ 'is-auth-route': isAuthRoute }">
    <template v-if="!isAuthRoute">
      <div class="shell-backdrop" :class="{ 'is-open': state.mobileMenuOpen }" @click="toggleSidebar"></div>
      <AppSidebar :mobile-menu-open="state.mobileMenuOpen" :toggle-sidebar="toggleSidebar" />

      <div class="shell-main">
        <AppTopNav />
        <main class="shell-content">
          <div v-if="showSmsBalanceWarning" class="global-sms-warning">
            <span class="material-symbols-outlined">sms_failed</span>
            <strong>{{ smsBalanceWarningText }}</strong>
          </div>
          <ErrorNotice
            v-if="state.lastErrorDetails && !modalState.requestComposer && !modalState.expenseComposer && !modalState.userComposer && !modalState.documentComposer"
            :error="state.lastErrorDetails"
          />
          <RouterView v-slot="{ Component }">
            <component :is="Component" :key="route.fullPath" />
          </RouterView>
        </main>
      </div>
    </template>

    <main v-else class="shell-main auth-main">
      <div class="shell-content">
        <RouterView v-slot="{ Component }">
          <component :is="Component" :key="route.fullPath" />
        </RouterView>
      </div>
    </main>

    <RequestDetailModal
      :open="modalState.requestDetail"
      :request="selectedRequest"
      :timeline="selectedRequestTimeline"
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

    <div v-if="globalLoading" class="app-loader-overlay" aria-label="در حال بارگذاری" aria-live="polite" aria-busy="true" role="status">
      <div class="loader" aria-hidden="true"></div>
    </div>
  </div>
</template>

<style scoped>
.app-loader-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.36);
}

.loader {
  width: 65px;
  aspect-ratio: 1;
  position: relative;
}

.loader::before,
.loader::after {
  content: '';
  position: absolute;
  border-radius: 50px;
  box-shadow: 0 0 0 3px inset #fff;
  animation: l4 2.5s infinite;
}

.loader::after {
  animation-delay: -1.25s;
}

@keyframes l4 {
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
  .loader::before,
  .loader::after {
    animation-duration: 1ms;
  }
}
</style>
