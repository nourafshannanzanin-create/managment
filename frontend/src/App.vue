<script setup>
import { computed, onMounted, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import ApprovalDetailModal from './components/ApprovalDetailModal.vue'
import AppSidebar from './components/AppSidebar.vue'
import DocumentComposerModal from './components/DocumentComposerModal.vue'
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
  selectedRequest,
  selectedExpense,
  selectedApproval,
  selectedRequestTimeline,
  restoreSession,
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
  <div class="app-shell" :class="{ 'is-auth-route': isAuthRoute }">
    <template v-if="!isAuthRoute">
      <div class="shell-backdrop" :class="{ 'is-open': state.mobileMenuOpen }" @click="toggleSidebar"></div>
      <button class="shell-menu-fab" type="button" @click="toggleSidebar">
        <span class="material-symbols-outlined">menu</span>
      </button>
      <AppSidebar :mobile-menu-open="state.mobileMenuOpen" :toggle-sidebar="toggleSidebar" />

      <div class="shell-main">
        <main class="shell-content">
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
  </div>
</template>
