<script setup>
import { computed, onMounted, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import AppSidebar from './components/AppSidebar.vue'
import ApprovalDetailModal from './components/ApprovalDetailModal.vue'
import RequestComposerModal from './components/RequestComposerModal.vue'
import RequestDetailModal from './components/RequestDetailModal.vue'
import { useWorkflowHub } from './stores/workflowHub'

const route = useRoute()
const hub = useWorkflowHub()

const {
  state,
  modalState,
  requestDetailState,
  selectedRequest,
  selectedApproval,
  selectedRequestTimeline,
  loadBootstrapData,
  closeRequestDetail,
  closeApprovalDetail,
  closeComposer,
  toggleSidebar,
} = hub

const layoutClass = computed(() => ({
  'is-auth-route': route.path === '/login',
  'mobile-nav-hidden': modalState.composer || modalState.requestDetail || modalState.approvalDetail,
}))

watch(
  () => route.fullPath,
  () => {
    state.mobileMenuOpen = false
  },
)

onMounted(() => {
  loadBootstrapData()
})
</script>

<template>
  <div class="app-shell" :class="layoutClass">
    <AppSidebar
      v-if="route.path !== '/login'"
      :mobile-menu-open="state.mobileMenuOpen"
      :toggle-sidebar="toggleSidebar"
    />

    <main class="shell-main">
      <div class="shell-content">
        <RouterView v-slot="{ Component }">
          <Transition name="route-fade" mode="out-in">
            <component :is="Component" />
          </Transition>
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
      @close="closeApprovalDetail"
    />

    <RequestComposerModal
      :open="modalState.composer"
      :form="state.requestForm"
      :step="state.composerStep"
      :submitting="state.requestSubmitting"
      @close="closeComposer"
    />
  </div>
</template>
