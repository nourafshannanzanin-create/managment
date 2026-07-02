<script setup>
import { ref, watch } from 'vue'

import StitchRuntimePage from '../components/StitchRuntimePage.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { formatMetric, wirePageNavigation } from '../utils/stitch'

const runtime = ref(null)
const { navigateTo, state, visibleNavItems } = useWorkflowHub()

function hydrate(root) {
  const monthly = state.stats.find((item) => item.id === 'monthly')?.value || state.expenseSummary[2]?.value || '0'
  const summaryValues = root.querySelectorAll('.text-primary.font-stat-value, .text-on-surface.font-headline-md.text-headline-md')
  if (summaryValues[0]) summaryValues[0].textContent = formatMetric(monthly)
  if (summaryValues[1]) summaryValues[1].textContent = String(state.requests.length)
  if (summaryValues[2]) summaryValues[2].textContent = String(state.approvalMetrics.pending || 0)

  const welcome = root.querySelector('main section p')
  if (welcome) welcome.textContent = 'کارنومند'

  const cardTitles = Array.from(root.querySelectorAll('main > div h3'))
  const trendCardTitle = cardTitles.find((title) => title.textContent?.includes('روند هزینه'))
  const trendCard = trendCardTitle?.closest('.bg-surface-container-lowest')
  if (trendCard) trendCard.remove()

  wirePageNavigation(root, navigateTo, '/dashboard', visibleNavItems.value)
}

function rehydrate() {
  const root = runtime.value?.getRoot?.()
  if (root) hydrate(root)
}

watch(() => [state.stats, state.requests.length, state.approvalMetrics.pending, state.expenseSummary, state.currentUser.name], rehydrate, { deep: true })
</script>

<template>
  <StitchRuntimePage ref="runtime" stitch-id="_5" @ready="hydrate" />
</template>
