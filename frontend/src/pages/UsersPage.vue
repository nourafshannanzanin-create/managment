<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { filteredUsers, openUserComposer, resetPageFilters, state, toggleSidebar, updatePageFilter, userPeople } = useWorkflowHub()
</script>

<template>
  <section v-if="state.currentUser.canManageUsers" class="page-shell">
    <PageHeader
      eyebrow="کاربران"
      title="مدیریت کاربران سازمان"
      description="مدیرعامل می تواند مدیرها و کارمندان را تعریف کند و دسترسی آن ها را کنترل کند."
      action-label="کاربر جدید"
      action-icon="person_add"
      @action="openUserComposer"
      @menu="toggleSidebar"
    />

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

    <section class="surface-block">
      <div class="section-label-row">
        <h2>فهرست کاربران</h2>
        <small>{{ filteredUsers.length }} ردیف</small>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>نام</th>
              <th>ایمیل</th>
              <th>نقش</th>
              <th>بخش</th>
              <th>مدیر مستقیم</th>
              <th>عنوان</th>
              <th>تاریخ عضویت</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredUsers" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.email }}</td>
              <td><span class="meta-pill">{{ item.role }}</span></td>
              <td>{{ item.department }}</td>
              <td>{{ item.manager }}</td>
              <td>{{ item.kpi }}</td>
              <td>{{ item.joinedAt }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
  <section v-else class="page-shell">
    <PageHeader eyebrow="کاربران" title="دسترسی محدود" description="این بخش فقط برای مدیرعامل فعال است." @menu="toggleSidebar" />
  </section>
</template>
