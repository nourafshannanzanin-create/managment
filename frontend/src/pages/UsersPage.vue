<script setup>
import { computed, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state } = useWorkflowHub()

const searchQuery = ref('')
const activeCategory = ref('all')
const activeLetter = ref('همه')
const selectedUserId = ref(null)

const categoryButtons = [
  { key: 'all', label: 'همه' },
  { key: 'managers', label: 'مدیران' },
  { key: 'employees', label: 'کارمندان' },
  { key: 'inactive', label: 'غیرفعال' },
]

const availableLetters = computed(() => {
  const letters = new Set(
    state.users
      .map((item) => String(item.name || '').trim().slice(0, 1))
      .filter(Boolean),
  )
  return ['همه', ...[...letters].sort((a, b) => a.localeCompare(b, 'fa'))]
})

const filteredUsers = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return state.users.filter((item) => {
    const status = String(item.status || '')
    const matchesCategory =
      activeCategory.value === 'all' ||
      (activeCategory.value === 'managers' && ['admin', 'executive_manager', 'manager'].includes(item.accessRole)) ||
      (activeCategory.value === 'employees' && item.accessRole === 'employee') ||
      (activeCategory.value === 'inactive' && status.includes('غیرفعال'))

    const firstLetter = String(item.name || '').trim().slice(0, 1)
    const matchesLetter = activeLetter.value === 'همه' || firstLetter === activeLetter.value

    const matchesQuery = !query ||
      ['name', 'role', 'jobTitle', 'department', 'email', 'manager', 'status']
        .some((field) => String(item[field] || '').toLowerCase().includes(query))

    return matchesCategory && matchesLetter && matchesQuery
  })
})

const userStats = computed(() => [
  { label: 'کل کاربران', value: state.users.length },
  { label: 'فعال', value: state.users.filter((item) => String(item.status || '').includes('فعال')).length },
  { label: 'مدیران', value: state.users.filter((item) => ['admin', 'executive_manager', 'manager'].includes(item.accessRole)).length },
  { label: 'کارمندان', value: state.users.filter((item) => item.accessRole === 'employee').length },
])

const selectedUser = computed(() => filteredUsers.value.find((item) => item.id === selectedUserId.value) || null)

function openUserDetails(id) {
  selectedUserId.value = id
}

function closeUserDetails() {
  selectedUserId.value = null
}

function toneForStatus(status) {
  const label = String(status || '')
  if (label.includes('غیرفعال')) return 'is-danger'
  if (label.includes('فعال')) return 'is-success'
  return ''
}
</script>

<template>
  <section v-if="state.currentUser.canAccessUsers || state.currentUser.canManageUsers" class="page-shell enterprise-page">
    <section class="metric-grid metric-grid-4">
      <article v-for="item in userStats" :key="item.label" class="metric-card">
        <span class="metric-label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="surface-block">
      <div class="filter-toolbar users-filter-toolbar">
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

        <div class="alphabet-strip">
          <button
            v-for="letter in availableLetters"
            :key="letter"
            :class="['alphabet-chip', activeLetter === letter && 'is-active']"
            type="button"
            @click="activeLetter = letter"
          >
            {{ letter }}
          </button>
        </div>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>فهرست کاربران</h3>
          <p>در کارت هر کاربر فقط اطلاعات اصلی دیده می‌شود و جزئیات با کلیک باز می‌شوند.</p>
        </div>
        <span class="meta-pill">{{ filteredUsers.length }} نتیجه</span>
      </div>

      <div v-if="filteredUsers.length" class="user-directory-table">
        <button
          v-for="item in filteredUsers"
          :key="item.id || item.email"
          class="user-directory-row"
          type="button"
          @click="openUserDetails(item.id)"
        >
          <div class="user-directory-main">
            <div class="user-avatar">{{ (item.name || '?').slice(0, 1) }}</div>
            <div class="user-card-copy">
              <strong>{{ item.name }}</strong>
              <small>{{ item.jobTitle || item.role }}</small>
            </div>
          </div>
          <div class="user-directory-meta">
            <span>{{ item.department || 'بدون بخش' }}</span>
            <span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span>
          </div>
        </button>
      </div>
      <div v-else class="empty-state-inline">
        <span class="material-symbols-outlined">group_off</span>
        <p>کاربری با این فیلترها پیدا نشد.</p>
      </div>
    </section>
  </section>

  <section v-else class="page-shell">
    <article class="access-denied-card">
      <h2>شما به بخش کاربران دسترسی ندارید</h2>
      <p>برای مشاهده و مدیریت کاربران باید نقش مدیریتی یا دسترسی مناسب داشته باشید.</p>
    </article>
  </section>

  <BaseModal :open="!!selectedUser" size="detail" @close="closeUserDetails">
    <div v-if="selectedUser" class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">جزئیات کاربر</p>
        <h2>{{ selectedUser.name }}</h2>
      </div>

      <section class="detail-meta-grid">
        <div class="detail-meta-item">
          <span>سمت</span>
          <strong>{{ selectedUser.jobTitle || selectedUser.role || '-' }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>وضعیت</span>
          <strong>{{ selectedUser.status || '-' }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>بخش</span>
          <strong>{{ selectedUser.department || '-' }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>ایمیل</span>
          <strong>{{ selectedUser.email || '-' }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>مدیر مستقیم</span>
          <strong>{{ selectedUser.manager || 'ندارد' }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>تاریخ عضویت</span>
          <strong>{{ selectedUser.joinedAt || '-' }}</strong>
        </div>
      </section>

      <div class="detail-note-box">
        <p>این نما برای بررسی سریع کاربر فشرده شده است. در صورت اتصال endpoint ویرایش/غیرفعالسازی، همین پنل بهترین جای اضافه کردن عملیات مستقیم خواهد بود.</p>
      </div>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="closeUserDetails">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
