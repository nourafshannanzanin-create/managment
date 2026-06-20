<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { filteredUsers, resetPageFilters, state, toggleSidebar, updatePageFilter, userPeople } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader eyebrow="کاربران" title="مدیریت کاربران" description="" @menu="toggleSidebar" />

    <PageFilters
      :query="state.filters.users.query"
      :person="state.filters.users.person"
      :start-date="state.filters.users.startDate"
      :end-date="state.filters.users.endDate"
      :people="userPeople"
      @update:query="updatePageFilter('users', 'query', $event)"
      @update:person="updatePageFilter('users', 'person', $event)"
      @update:start-date="updatePageFilter('users', 'startDate', $event)"
      @update:end-date="updatePageFilter('users', 'endDate', $event)"
      @reset="resetPageFilters('users')"
    />

    <div class="users-grid">
      <article v-for="item in filteredUsers" :key="item.name" class="user-card">
        <div class="user-head">
          <div class="user-inline">
            <div class="avatar-pill subtle">{{ item.name.slice(0, 1) }}</div>
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.role }}</p>
            </div>
          </div>
          <span class="meta-pill">{{ item.department }}</span>
        </div>
        <p>{{ item.kpi }} · {{ item.joinedAt }}</p>
      </article>
    </div>

    <section class="surface-block">
      <div class="section-label-row">
        <h2>فهرست کاربران</h2>
        <small>{{ filteredUsers.length }}</small>
      </div>

      <div class="stack-list">
        <article v-for="item in filteredUsers" :key="item.name" class="list-row">
          <div class="list-row-main user-inline">
            <div class="avatar-pill subtle">{{ item.name.slice(0, 1) }}</div>
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.role }} · {{ item.department }} · {{ item.manager }}</p>
            </div>
          </div>
          <div class="list-row-meta">
            <small>{{ item.joinedAt }}</small>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>
