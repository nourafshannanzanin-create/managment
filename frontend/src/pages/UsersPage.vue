<script setup>
import { computed, ref } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const searchQuery = ref('')
const activeCategory = ref('all')

const { openUserComposer, state } = useWorkflowHub()

const categoryButtons = computed(() => [
  { key: 'all', label: 'همه افراد' },
  { key: 'managers', label: 'مدیران' },
  { key: 'experts', label: 'کارشناسان' },
  { key: 'it', label: 'فناوری اطلاعات' },
])

const filteredUsers = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return state.users.filter((item) => {
    const matchesCategory =
      activeCategory.value === 'all' ||
      (activeCategory.value === 'managers' && ['admin', 'executive_manager', 'manager'].includes(item.accessRole)) ||
      (activeCategory.value === 'experts' && item.accessRole === 'employee') ||
      (activeCategory.value === 'it' && String(item.department || '').includes('فناوری'))

    if (!matchesCategory) return false
    if (!query) return true

    return ['name', 'email', 'role', 'department', 'manager', 'status']
      .some((field) => String(item[field] || '').toLowerCase().includes(query))
  })
})

const userStats = computed(() => [
  { label: 'کل کاربران', value: filteredUsers.value.length },
  { label: 'کاربران فعال', value: filteredUsers.value.filter((item) => String(item.status || '').includes('فعال')).length },
  { label: 'مدیران', value: filteredUsers.value.filter((item) => ['admin', 'executive_manager', 'manager'].includes(item.accessRole)).length },
  { label: 'کارشناسان', value: filteredUsers.value.filter((item) => item.accessRole === 'employee').length },
])

function toneForStatus(status) {
  const label = String(status || '')
  if (label.includes('غیرفعال')) return 'is-danger'
  if (label.includes('فعال')) return 'is-success'
  return ''
}
</script>

<template>
  <section v-if="state.currentUser.canAccessUsers || state.currentUser.canManageUsers" class="page-shell enterprise-page">
    <PageHeader
      eyebrow="سرمایه انسانی"
      title="کاربران و نقش‌های دسترسی"
      action-label="افزودن کاربر"
      action-icon="person_add"
      @action="openUserComposer"
    />

    <section class="metric-grid metric-grid-4">
      <article v-for="item in userStats" :key="item.label" class="metric-card">
        <span class="metric-label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="surface-block">
      <div class="filter-toolbar">
        <label class="search-shell search-shell-wide">
          <span class="material-symbols-outlined">search</span>
          <input v-model="searchQuery" type="text" placeholder="جستجو در کاربران..." />
        </label>

        <div class="chip-row">
          <button
            v-for="item in categoryButtons"
            :key="item.key"
            :class="['filter-chip', activeCategory === item.key && 'is-active']"
            type="button"
            @click="activeCategory = item.key"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>فهرست کاربران</h3>
          <p>{{ filteredUsers.length }} کاربر مطابق این فیلترها یافت شد.</p>
        </div>
      </div>

      <div class="card-grid">
        <article v-for="item in filteredUsers" :key="item.id || item.email" class="user-card">
          <div class="user-card-head">
            <div class="user-avatar">{{ (item.name || '?').slice(0, 1) }}</div>
            <div class="user-card-copy">
              <strong>{{ item.name }}</strong>
              <small>{{ item.role }}</small>
            </div>
            <span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span>
          </div>

          <div class="user-card-grid">
            <div><span>ایمیل</span><strong>{{ item.email }}</strong></div>
            <div><span>بخش</span><strong>{{ item.department }}</strong></div>
            <div><span>مدیر مستقیم</span><strong>{{ item.manager || 'ندارد' }}</strong></div>
            <div><span>تاریخ عضویت</span><strong>{{ item.joinedAt || '-' }}</strong></div>
          </div>
        </article>
      </div>
    </section>
  </section>

  <section v-else class="page-shell">
    <article class="access-denied-card">
      <h2>شما به بخش کاربران دسترسی ندارید</h2>
      <p>برای مشاهده و مدیریت کاربران باید نقش مدیریتی یا دسترسی مناسب داشته باشید.</p>
    </article>
  </section>
</template>
