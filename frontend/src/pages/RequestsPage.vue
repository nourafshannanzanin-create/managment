<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  filteredRequests,
  navigateTo,
  openRequestDetail,
  requestPeople,
  resetPageFilters,
  toggleSidebar,
  updatePageFilter,
} = useWorkflowHub()
</script>

<template>
  <section class="page-shell requests-page">
    <PageHeader
      eyebrow="درخواست‌ها"
      title="مدیریت درخواست‌ها"
      action-label="درخواست جدید"
      action-icon="add"
      @action="navigateTo('/requests/new')"
      @menu="toggleSidebar"
    />

    <PageFilters
      :query="state.filters.requests.query"
      :person="state.filters.requests.person"
      :start-date="state.filters.requests.startDate"
      :end-date="state.filters.requests.endDate"
      :people="requestPeople"
      @update:query="updatePageFilter('requests', 'query', $event)"
      @update:person="updatePageFilter('requests', 'person', $event)"
      @update:start-date="updatePageFilter('requests', 'startDate', $event)"
      @update:end-date="updatePageFilter('requests', 'endDate', $event)"
      @reset="resetPageFilters('requests')"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>{{ filteredRequests.length }} درخواست</h2>
      </div>

      <div class="stack-list">
        <button
          v-for="item in filteredRequests"
          :key="item.id"
          class="list-row interactive-row"
          @click="openRequestDetail(item.id)"
        >
          <div class="list-row-main">
            <strong>{{ item.title }}</strong>
            <p>{{ item.id }} · {{ item.owner }} · {{ item.department }} · {{ item.manager }}</p>
          </div>
          <div class="list-row-meta">
            <span class="meta-pill">{{ item.priority }}</span>
            <span>{{ item.status }}</span>
            <small>{{ item.deadline }}</small>
          </div>
        </button>
      </div>
    </section>
  </section>
</template>
