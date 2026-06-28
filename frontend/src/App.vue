<script setup>
import { computed, onMounted, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import ApprovalDetailModal from './components/ApprovalDetailModal.vue'
import AppTopNav from './components/AppTopNav.vue'
import DocumentComposerModal from './components/DocumentComposerModal.vue'
import ExpenseComposerModal from './components/ExpenseComposerModal.vue'
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
  approvalDetailState,
  selectedRequest,
  selectedApproval,
  selectedRequestTimeline,
  restoreSession,
  closeRequestDetail,
  closeApprovalDetail,
  closeRequestComposer,
  closeExpenseComposer,
  closeUserComposer,
  closeDocumentComposer,
  closeSignatureComposer,
} = hub

const isAuthRoute = computed(() => route.path === '/login')
const layoutClass = computed(() => ({
  'is-auth-route': isAuthRoute.value,
}))

watch(
  () => route.fullPath,
  () => {
    state.mobileMenuOpen = false
  },
)

onMounted(() => {
  restoreSession()
})
</script>

<template>
  <div class="app-shell" :class="layoutClass">
    <AppTopNav v-if="!isAuthRoute" />

    <main class="shell-main">
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

    <SignatureComposerModal
      :open="modalState.signatureComposer"
      @close="closeSignatureComposer"
    />
  </div>
</template>
