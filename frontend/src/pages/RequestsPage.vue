<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  filteredRequests,
  openRequestComposer,
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
      eyebrow="درخواست ها"
      title="مدیریت درخواست ها"
      description="کارمندان فقط درخواست های خودشان را می بینند و مدیرها می توانند همه درخواست های سازمان را بررسی کنند."
      action-label="درخواست جدید"
      action-icon="edit_square"
      @action="openRequestComposer"
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
        <h2>فهرست درخواست ها</h2>
        <small>{{ filteredRequests.length }} ردیف</small>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>کد</th>
              <th>عنوان</th>
              <th>ثبت کننده</th>
              <th>ارجاع به</th>
              <th>بخش</th>
              <th>اولویت</th>
              <th>تاریخ</th>
              <th>وضعیت</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredRequests" :key="item.id" class="clickable-row" @click="openRequestDetail(item.id)">
              <td>{{ item.id }}</td>
              <td>
                <strong>{{ item.title }}</strong>
                <small>{{ item.description }}</small>
              </td>
              <td>{{ item.owner }}</td>
              <td>{{ item.manager }}</td>
              <td>{{ item.department }}</td>
              <td><span class="meta-pill">{{ item.priority }}</span></td>
              <td>{{ item.deadline || item.createdAt }}</td>
              <td><span class="meta-pill">{{ item.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>
