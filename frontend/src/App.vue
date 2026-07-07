<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
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

const isAuthRoute = computed(() => route.path === '/login')
const globalLoading = computed(() =>
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

async function refreshRouteData(path) {
  if (!state.authToken || path === '/login') return

  await loadBootstrapData(true)

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
    state.mobileMenuOpen = false

    if (!state.sessionReady) return
    await refreshRouteData(route.path)
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

    <div v-if="globalLoading" class="app-loader-overlay" aria-live="polite" aria-busy="true">
      <div class="loader"></div>
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
  background: rgba(18, 27, 46, 0.42);
  backdrop-filter: blur(8px);
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
  animation: app-loader-spin 2.5s infinite;
}

.loader::after {
  animation-delay: -1.25s;
}

@keyframes app-loader-spin {
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
</style>
