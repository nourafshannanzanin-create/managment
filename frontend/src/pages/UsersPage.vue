<script setup>
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { openUserComposer, state, updateUser } = useWorkflowHub()

const searchQuery = ref('')
const activeCategory = ref('all')
const activeLetter = ref('همه')
const selectedUserId = ref(null)
const savingUser = ref(false)

const editableUser = reactive({
  fullName: '',
  email: '',
  password: '',
  accessRole: 'employee',
  department: '',
  managerId: '',
  jobTitle: '',
  isActive: true,
  sectionAccess: {
    reports: false,
    users: false,
    settings: false,
  },
})

const categoryButtons = [
  { key: 'all', label: 'همه' },
  { key: 'managers', label: 'مدیران' },
  { key: 'employees', label: 'کارمندان' },
  { key: 'inactive', label: 'غیرفعال' },
]

const canManageUsers = computed(() => state.currentUser.canManageUsers)

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
  { label: 'کل کاربران', value: state.users.length, icon: 'group', note: 'ثبت شده', tone: 'is-total' },
  { label: 'فعال', value: state.users.filter((item) => item.isActive).length, icon: 'verified_user', note: 'حساب‌های فعال', tone: 'is-approved' },
  { label: 'مدیران', value: state.users.filter((item) => ['admin', 'executive_manager', 'manager'].includes(item.accessRole)).length, icon: 'badge', note: 'سطح مدیریتی', tone: 'is-pending' },
  { label: 'کارمندان', value: state.users.filter((item) => item.accessRole === 'employee').length, icon: 'person', note: 'نیروی اجرایی', tone: 'is-rejected' },
])

const selectedUser = computed(() => state.users.find((item) => item.id === selectedUserId.value) || null)

watch(selectedUser, (user) => {
  Object.assign(editableUser, {
    fullName: user?.name || '',
    email: user?.email || '',
    password: '',
    accessRole: user?.accessRole || 'employee',
    department: user?.departmentCode || '',
    managerId: user?.managerId || '',
    jobTitle: user?.jobTitle || user?.role || '',
    isActive: Boolean(user?.isActive),
    sectionAccess: {
      reports: Boolean(user?.sectionAccess?.reports),
      users: Boolean(user?.sectionAccess?.users),
      settings: Boolean(user?.sectionAccess?.settings),
    },
  })
}, { immediate: true })

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

async function saveUserChanges() {
  if (!selectedUser.value || savingUser.value || !canManageUsers.value) return
  savingUser.value = true
  try {
    await updateUser(selectedUser.value.id, {
      fullName: editableUser.fullName,
      email: editableUser.email,
      password: editableUser.password,
      accessRole: editableUser.accessRole,
      department: editableUser.department,
      managerId: editableUser.managerId || null,
      jobTitle: editableUser.jobTitle,
      isActive: editableUser.isActive,
      sectionAccess: editableUser.sectionAccess,
    })
    editableUser.password = ''
  } finally {
    savingUser.value = false
  }
}

async function toggleSelectedUserStatus() {
  const previousStatus = editableUser.isActive
  editableUser.isActive = !editableUser.isActive
  try {
    await saveUserChanges()
  } catch {
    editableUser.isActive = previousStatus
  }
}

function userManagerOptions(userId) {
  return state.directories.managers.filter((item) => item.id !== userId)
}
</script>

<template>
  <section v-if="state.currentUser.canAccessUsers || state.currentUser.canManageUsers" class="page-shell enterprise-page">
    <section class="metric-grid metric-grid-4">
      <article v-for="item in userStats" :key="item.label" :class="['metric-card', 'approval-metric-card', item.tone]">
        <div class="metric-card-headline">
          <span class="metric-label">{{ item.label }}</span>
          <span class="material-symbols-outlined approval-metric-icon">{{ item.icon }}</span>
        </div>
        <strong>{{ item.value }}</strong>
        <small class="approval-metric-note">{{ item.note }}</small>
      </article>
    </section>

    <section class="surface-block users-toolbar-panel">
      <div class="users-toolbar-stack">
        <div class="users-toolbar-head">
          <div>
            <h3>فهرست کاربران</h3>
            <p>کارت‌های کوچک، جمع‌وجور و مناسب برای مرور سریع اعضای سازمان.</p>
          </div>

          <div class="users-header-actions">
            <span class="meta-pill">{{ filteredUsers.length }} نتیجه</span>
            <button v-if="canManageUsers" class="action-btn tone-primary" type="button" @click="openUserComposer">
              <span class="material-symbols-outlined">person_add</span>
              <span>افزودن کاربر</span>
            </button>
          </div>
        </div>

        <div class="filter-toolbar users-toolbar-primary">
          <label class="search-shell search-shell-wide users-search-shell">
            <span class="material-symbols-outlined">search</span>
            <input v-model="searchQuery" type="text" placeholder="جستجو در کاربران..." />
          </label>

          <div class="chip-row users-chip-row">
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

        <div class="alphabet-strip users-toolbar-secondary">
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

    <section class="surface-block users-grid-panel">
      <div v-if="filteredUsers.length" class="user-directory-grid">
        <button
          v-for="item in filteredUsers"
          :key="item.id || item.email"
          class="compact-user-card"
          type="button"
          @click="openUserDetails(item.id)"
        >
          <div class="user-card-head">
            <div class="user-directory-main">
              <div class="user-avatar">{{ (item.name || '?').slice(0, 1) }}</div>
              <div class="user-card-copy">
                <strong>{{ item.name }}</strong>
                <small>{{ item.jobTitle || item.role }}</small>
              </div>
            </div>

            <span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span>
          </div>

          <div class="user-card-details">
            <span>{{ item.department || 'بدون بخش' }}</span>
            <span>{{ item.manager || 'بدون مدیر' }}</span>
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
    <div v-if="selectedUser" class="user-modal-shell" :class="selectedUser.isActive ? 'is-approved' : 'is-rejected'">
      <section class="user-hero">
        <div class="user-hero-copy">
          <p class="page-eyebrow">جزئیات کاربر</p>
          <h2>{{ selectedUser.name }}</h2>
          <div class="user-hero-meta">
            <span class="user-role-pill">{{ selectedUser.jobTitle || selectedUser.role || '-' }}</span>
            <span class="user-meta-divider"></span>
            <span>{{ selectedUser.department || 'بدون بخش' }}</span>
            <span class="user-meta-divider"></span>
            <span>{{ selectedUser.email || '-' }}</span>
          </div>
        </div>

        <div class="user-status-panel">
          <div class="user-status-icon">
            <span class="material-symbols-outlined">{{ selectedUser.isActive ? 'verified_user' : 'person_off' }}</span>
          </div>
          <div class="user-status-copy">
            <strong>{{ selectedUser.status || '-' }}</strong>
            <p>همه گزینه‌های ویرایش، تغییر دسترسی و فعال‌سازی یا غیرفعال‌سازی از همین پنجره در دسترس هستند.</p>
          </div>
        </div>
      </section>

      <section class="user-meta-board">
        <article class="user-meta-card">
          <div class="user-meta-icon"><span class="material-symbols-outlined">badge</span></div>
          <div class="user-meta-copy"><span>سمت</span><strong>{{ selectedUser.jobTitle || selectedUser.role || '-' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><span class="material-symbols-outlined">apartment</span></div>
          <div class="user-meta-copy"><span>بخش</span><strong>{{ selectedUser.department || '-' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><span class="material-symbols-outlined">mail</span></div>
          <div class="user-meta-copy"><span>ایمیل</span><strong>{{ selectedUser.email || '-' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><span class="material-symbols-outlined">supervisor_account</span></div>
          <div class="user-meta-copy"><span>مدیر مستقیم</span><strong>{{ selectedUser.manager || 'ندارد' }}</strong></div>
        </article>
      </section>

      <section class="surface-inline user-form-panel">
        <div class="section-label-row">
          <div>
            <h3>ویرایش کاربر</h3>
            <p>در صورت نیاز اطلاعات، نقش، دسترسی‌ها و وضعیت این کاربر را به‌روزرسانی کنید.</p>
          </div>
        </div>

        <div class="modal-grid two-col">
          <label class="field-shell">
            <span>نام کامل</span>
            <input v-model="editableUser.fullName" type="text" :disabled="!canManageUsers" />
          </label>

          <label class="field-shell">
            <span>ایمیل</span>
            <input v-model="editableUser.email" type="email" :disabled="!canManageUsers" />
          </label>

          <label class="field-shell">
            <span>رمز عبور جدید</span>
            <input v-model="editableUser.password" type="password" placeholder="در صورت نیاز تغییر دهید" :disabled="!canManageUsers" />
          </label>

          <label class="field-shell">
            <span>نوع دسترسی</span>
            <select v-model="editableUser.accessRole" :disabled="!canManageUsers">
              <option value="manager">مدیر</option>
              <option value="employee">کارمند</option>
            </select>
          </label>

          <label class="field-shell">
            <span>بخش</span>
            <select v-model="editableUser.department" :disabled="!canManageUsers">
              <option value="">انتخاب بخش</option>
              <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option>
            </select>
          </label>

          <label class="field-shell">
            <span>مدیر مستقیم</span>
            <select v-model="editableUser.managerId" :disabled="!canManageUsers">
              <option value="">بدون مدیر</option>
              <option v-for="item in userManagerOptions(selectedUser.id)" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </label>
        </div>

        <label class="field-shell">
          <span>عنوان شغلی</span>
          <input v-model="editableUser.jobTitle" type="text" :disabled="!canManageUsers" />
        </label>

        <div class="user-access-grid">
          <label class="check-tile">
            <input v-model="editableUser.sectionAccess.reports" type="checkbox" :disabled="!canManageUsers" />
            <div>
              <strong>گزارشات</strong>
              <small>نمایش گزارش‌های مدیریتی</small>
            </div>
          </label>

          <label class="check-tile">
            <input v-model="editableUser.sectionAccess.users" type="checkbox" :disabled="!canManageUsers" />
            <div>
              <strong>کاربران</strong>
              <small>دسترسی به لیست و مدیریت کاربران</small>
            </div>
          </label>

          <label class="check-tile">
            <input v-model="editableUser.sectionAccess.settings" type="checkbox" :disabled="!canManageUsers" />
            <div>
              <strong>تنظیمات</strong>
              <small>ورود به تنظیمات و سطح دسترسی‌ها</small>
            </div>
          </label>
        </div>
      </section>

      <section class="user-modal-actions">
        <button class="action-btn tone-soft" type="button" @click="closeUserDetails">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>

        <button
          v-if="canManageUsers"
          class="action-btn"
          :class="editableUser.isActive ? 'tone-danger' : 'tone-primary'"
          type="button"
          :disabled="savingUser"
          @click="toggleSelectedUserStatus"
        >
          <span class="material-symbols-outlined">{{ editableUser.isActive ? 'person_off' : 'person_check' }}</span>
          <span>{{ savingUser ? 'در حال ذخیره...' : editableUser.isActive ? 'غیرفعال‌سازی' : 'فعال‌سازی' }}</span>
        </button>

        <button
          v-if="canManageUsers"
          class="action-btn tone-primary"
          type="button"
          :disabled="savingUser"
          @click="saveUserChanges"
        >
          <span class="material-symbols-outlined">save</span>
          <span>{{ savingUser ? 'در حال ذخیره...' : 'ذخیره تغییرات' }}</span>
        </button>
      </section>
    </div>
  </BaseModal>
</template>

<style scoped>
.users-toolbar-panel,
.users-grid-panel {
  overflow: hidden;
}

.users-toolbar-stack {
  display: grid;
  gap: 14px;
}

.users-toolbar-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.users-toolbar-head h3,
.users-toolbar-head p {
  margin: 0;
}

.users-toolbar-head p {
  color: var(--muted);
}

.users-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.users-toolbar-primary {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.users-search-shell {
  min-width: min(100%, 320px);
  flex: 1 1 280px;
}

.users-chip-row,
.users-toolbar-secondary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.user-directory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.compact-user-card {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 14px;
  border: 1px solid rgba(38, 56, 92, 0.08);
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.95)),
    var(--surface);
  box-shadow: 0 16px 34px rgba(28, 42, 76, 0.08);
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
  text-align: right;
}

.compact-user-card:hover {
  transform: translateY(-2px);
  border-color: rgba(72, 103, 183, 0.18);
  box-shadow: 0 20px 38px rgba(28, 42, 76, 0.12);
}

.user-card-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 10px;
}

.user-directory-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.user-avatar {
  width: 46px;
  height: 46px;
  flex: 0 0 46px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(72, 103, 183, 0.14), rgba(216, 175, 140, 0.22));
  color: #203255;
  font-weight: 900;
}

.user-card-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.user-card-copy strong,
.user-card-copy small,
.user-card-details span,
.user-meta-copy strong {
  min-width: 0;
  overflow-wrap: anywhere;
}

.user-card-copy strong {
  color: #203255;
  font-size: 15px;
}

.user-card-copy small {
  color: var(--muted);
  font-size: 12px;
}

.user-card-details {
  display: grid;
  gap: 6px;
  color: #59657f;
  font-size: 12px;
}

.user-modal-shell {
  display: grid;
  gap: 22px;
  padding: 8px 4px 4px;
}

.user-hero,
.user-meta-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(38, 56, 92, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.96)),
    var(--surface);
  box-shadow: 0 22px 50px rgba(28, 42, 76, 0.08);
}

.user-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 24px;
  border-radius: 30px;
}

.user-hero-copy,
.user-status-copy,
.user-meta-copy {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.user-hero-copy h2 {
  margin: 0;
  font-size: clamp(28px, 2.3vw, 38px);
  line-height: 1.3;
  color: #203255;
}

.user-hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 13px;
}

.user-role-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(72, 103, 183, 0.1);
  color: var(--primary);
  font-weight: 800;
}

.user-meta-divider {
  width: 5px;
  height: 5px;
  border-radius: 999px;
  background: rgba(82, 96, 126, 0.4);
}

.user-status-panel {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16px;
  align-items: start;
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.66);
}

.user-status-icon,
.user-meta-icon {
  display: grid;
  place-items: center;
}

.user-status-icon {
  width: 64px;
  height: 64px;
  border-radius: 22px;
  font-size: 28px;
  color: #fff;
  background: linear-gradient(135deg, #23936d, #176f52);
}

.user-modal-shell.is-rejected .user-status-icon {
  background: linear-gradient(135deg, #d36363, #ab4343);
}

.user-status-copy strong {
  font-size: 20px;
  color: #203255;
}

.user-status-copy p {
  margin: 0;
  line-height: 1.9;
  color: var(--muted);
}

.user-meta-board {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.user-meta-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
  padding: 18px;
  border-radius: 24px;
}

.user-meta-icon {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background: rgba(72, 103, 183, 0.08);
  color: var(--primary);
}

.user-meta-copy span {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.user-meta-copy strong {
  margin: 0;
  font-size: 16px;
  color: #203255;
  line-height: 1.55;
}

.user-form-panel {
  display: grid;
  gap: 16px;
}

.user-access-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.check-tile {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(36, 59, 107, 0.1);
  background: rgba(255, 255, 255, 0.76);
}

.check-tile input {
  margin-top: 4px;
}

.check-tile strong,
.check-tile small {
  display: block;
}

.check-tile small {
  margin-top: 4px;
  color: var(--muted);
  overflow-wrap: anywhere;
}

.user-modal-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1100px) {
  .user-hero {
    grid-template-columns: minmax(0, 1fr);
  }

  .user-meta-board,
  .user-access-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .users-toolbar-head,
  .user-card-head {
    align-items: stretch;
    flex-direction: column;
  }

  .user-directory-grid,
  .user-meta-board,
  .user-access-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .user-modal-shell {
    gap: 16px;
    padding: 0;
  }

  .user-hero {
    padding: 18px;
    border-radius: 22px;
  }

  .user-status-panel,
  .user-modal-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
