<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import InfiniteScrollSentinel from '../components/InfiniteScrollSentinel.vue'
import { useInfiniteList } from '../composables/useInfiniteList'
import { computed, markRaw, reactive, ref, watch } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import ErrorNotice from '../components/ErrorNotice.vue'
import ProfileAvatarEditor from '../components/ProfileAvatarEditor.vue'
import SectionHeading from '../components/SectionHeading.vue'
import UserAvatar from '../components/UserAvatar.vue'
import UserEntrustedPanel from '../components/UserEntrustedPanel.vue'
import { formatAmountInput, normalizeAmountValue } from '../utils/amount'
import { useWorkflowHub } from '../stores/workflowHub'

const { availableManagerDirectory, openUserComposer, state, updateUser, addUserEntrustedItem, removeUserEntrustedItem , loadMoreBootstrapCollection } = useWorkflowHub()

const searchQuery = ref('')
const activeCategory = ref('all')
const selectedUserId = ref(null)
const savingUser = ref(false)
const applyingBonus = ref(false)
const applyingPenalty = ref(false)
const applyingEntrusted = ref(false)
const showCurrentPassword = ref(true)
const avatarDraftFile = ref(null)
const avatarDraftPreview = ref('')
const clearAvatarOnSave = ref(false)
const entrustedPanelRef = ref(null)

const editableUser = reactive({
  fullName: '',
  username: '',
  password: '',
  phone: '',
  bonusDelta: '',
  penaltyDelta: '',
  accessRole: 'employee',
  department: '',
  managerId: '',
  jobTitle: '',
  isActive: true,
  sectionAccess: {
    approvals: false,
    expenses: false,
    reports: false,
    users: false,
    settings: false,
    attendance: false,
    archive: false,
  },
})

function revokeAvatarDraftPreview() {
  if (avatarDraftPreview.value && String(avatarDraftPreview.value).startsWith('blob:')) {
    URL.revokeObjectURL(avatarDraftPreview.value)
  }
}

function resetAvatarDraft() {
  revokeAvatarDraftPreview()
  avatarDraftFile.value = null
  avatarDraftPreview.value = ''
  clearAvatarOnSave.value = false
}

const modalAvatarUrl = computed(() => {
  if (avatarDraftPreview.value) return avatarDraftPreview.value
  if (clearAvatarOnSave.value) return ''
  return selectedUser.value?.avatarUrl || ''
})

const modalAvatarFileName = computed(() => {
  if (avatarDraftFile.value?.name) return avatarDraftFile.value.name
  if (clearAvatarOnSave.value) return ''
  return selectedUser.value?.avatarFileName || ''
})

const sectionAccessOptions = [
  { key: 'users', title: 'کاربران' },
  { key: 'expenses', title: 'هزینه‌ها' },
  { key: 'reports', title: 'گزارشات' },
  { key: 'attendance', title: 'ورود و خروج' },
  { key: 'archive', title: 'بایگانی' },
  { key: 'settings', title: 'تنظیمات' },
]

const categoryButtons = [
  { key: 'all', label: 'همه' },
  { key: 'managers', label: 'مدیران' },
  { key: 'employees', label: 'کارمندان' },
  { key: 'inactive', label: 'غیرفعال' },
]

const canManageUsers = computed(() => state.currentUser.canManageUsers)

const filteredUsers = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return state.users.filter((item) => {
    const status = String(item.status || '')
    const matchesCategory =
      activeCategory.value === 'all' ||
      (activeCategory.value === 'managers' && ['admin', 'executive_manager', 'manager'].includes(item.accessRole)) ||
      (activeCategory.value === 'employees' && item.accessRole === 'employee') ||
      (activeCategory.value === 'inactive' && status.includes('غیرفعال'))

    const matchesQuery = !query ||
      ['name', 'role', 'jobTitle', 'department', 'username', 'manager', 'status']
        .some((field) => String(item[field] || '').toLowerCase().includes(query))

    return matchesCategory && matchesQuery
  })
})

const usersPaging = computed(() => state.collectionPaging?.users || { total: 0, hasMore: false, loading: false })
const {
  items: visibleUsers,
  hasMore: hasMoreUsers,
  loadingMore: loadingMoreUsers,
  loadMore: loadMoreUsers,
} = useInfiniteList(filteredUsers, {
  resetKey: computed(() => JSON.stringify(state.filters.users || {})),
  hasMoreRemote: computed(() => Boolean(usersPaging.value.hasMore)),
  onLoadMore: () => loadMoreBootstrapCollection('users'),
})


const userStats = computed(() => [
  { label: 'کل کاربران', value: state.users.length, icon: 'group', note: '', tone: 'is-total' },
  { label: 'فعال', value: state.users.filter((item) => item.isActive).length, icon: 'verified_user', note: '', tone: 'is-approved' },
  { label: 'مدیران', value: state.users.filter((item) => ['admin', 'executive_manager', 'manager'].includes(item.accessRole)).length, icon: 'badge', note: '', tone: 'is-pending' },
  { label: 'کارمندان', value: state.users.filter((item) => item.accessRole === 'employee').length, icon: 'person', note: '', tone: 'is-rejected' },
])

const selectedUser = computed(() => state.users.find((item) => item.id === selectedUserId.value) || null)

function syncEditableFromUser(user) {
  resetAvatarDraft()
  Object.assign(editableUser, {
    fullName: user?.name || '',
    username: user?.username || '',
    password: '',
    phone: user?.phone || '',
    bonusDelta: '',
    penaltyDelta: '',
    accessRole: user?.accessRole || 'employee',
    department: user?.departmentCode || '',
    managerId: user?.managerId || '',
    jobTitle: user?.jobTitle || user?.role || '',
    isActive: Boolean(user?.isActive),
    sectionAccess: {
      approvals: Boolean(user?.sectionAccess?.approvals),
      expenses: Boolean(user?.sectionAccess?.expenses),
      reports: Boolean(user?.sectionAccess?.reports),
      users: Boolean(user?.sectionAccess?.users),
      settings: Boolean(user?.sectionAccess?.settings),
      attendance: Boolean(user?.sectionAccess?.attendance),
      archive: Boolean(user?.sectionAccess?.archive),
    },
  })
}

// Only resync when opening another user — soft bootstrap must not wipe in-progress edits.
watch(
  selectedUserId,
  (id) => {
    if (!id) return
    syncEditableFromUser(selectedUser.value)
  },
  { immediate: true },
)

function openUserDetails(id) {
  selectedUserId.value = id
}

function closeUserDetails() {
  resetAvatarDraft()
  selectedUserId.value = null
}

function onUserAvatarSelected(file) {
  if (!canManageUsers.value || !file) return
  revokeAvatarDraftPreview()
  avatarDraftFile.value = markRaw(file)
  avatarDraftPreview.value = URL.createObjectURL(file)
  clearAvatarOnSave.value = false
}

function onUserAvatarCleared() {
  if (!canManageUsers.value) return
  revokeAvatarDraftPreview()
  avatarDraftFile.value = null
  avatarDraftPreview.value = ''
  clearAvatarOnSave.value = Boolean(selectedUser.value?.avatarUrl)
}

function toneForStatus(status) {
  const label = String(status || '')
  if (label.includes('غیرفعال')) return 'is-danger'
  if (label.includes('فعال')) return 'is-success'
  return ''
}

function handleMoneyInput(field, value) {
  editableUser[field] = formatAmountInput(value)
}

async function saveUserChanges() {
  if (!selectedUser.value || savingUser.value || !canManageUsers.value) return
  savingUser.value = true
  try {
    await updateUser(selectedUser.value.id, {
      fullName: editableUser.fullName,
      username: editableUser.username,
      password: editableUser.password,
      phone: editableUser.phone,
      accessRole: editableUser.accessRole,
      department: editableUser.department,
      managerId: editableUser.managerId || null,
      jobTitle: editableUser.jobTitle,
      isActive: editableUser.isActive,
      sectionAccess: editableUser.sectionAccess,
      avatarFile: avatarDraftFile.value || undefined,
      clearAvatar: clearAvatarOnSave.value,
    })
    editableUser.password = ''
    closeUserDetails()
  } catch {
    // ErrorNotice renders the normalized backend/frontend error.
  } finally {
    savingUser.value = false
  }
}

async function applyBonusDelta() {
  if (!selectedUser.value || applyingBonus.value || !canManageUsers.value) return

  const amount = normalizeAmountValue(editableUser.bonusDelta || 0)
  if (!amount || Number(amount) <= 0) return

  applyingBonus.value = true
  try {
    await updateUser(selectedUser.value.id, { bonusDelta: amount })
    editableUser.bonusDelta = ''
  } finally {
    applyingBonus.value = false
  }
}

async function applyPenaltyDelta() {
  if (!selectedUser.value || applyingPenalty.value || !canManageUsers.value) return

  const amount = normalizeAmountValue(editableUser.penaltyDelta || 0)
  if (!amount || Number(amount) <= 0) return

  applyingPenalty.value = true
  try {
    await updateUser(selectedUser.value.id, { penaltyDelta: amount })
    editableUser.penaltyDelta = ''
  } finally {
    applyingPenalty.value = false
  }
}

async function onAddEntrustedItem(payload) {
  if (!selectedUser.value || applyingEntrusted.value || !canManageUsers.value) return
  applyingEntrusted.value = true
  try {
    await addUserEntrustedItem(selectedUser.value.id, payload)
    entrustedPanelRef.value?.onDraftAddedExternally?.()
  } finally {
    applyingEntrusted.value = false
  }
}

async function onRemoveEntrustedItem(item) {
  if (!selectedUser.value || applyingEntrusted.value || !canManageUsers.value || !item?.id) return
  applyingEntrusted.value = true
  try {
    await removeUserEntrustedItem(selectedUser.value.id, item.id)
  } finally {
    applyingEntrusted.value = false
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
  return availableManagerDirectory(userId)
}
</script>

<template>
  <section v-if="state.currentUser.canAccessUsers || state.currentUser.canManageUsers" class="page-shell enterprise-page">
    <section class="metric-grid metric-grid-4">
      <article v-for="item in userStats" :key="item.label" :class="['metric-card', 'approval-metric-card', item.tone]">
        <div class="metric-card-headline">
          <span class="metric-label">{{ item.label }}</span>
          <IconlyIcon :name="item.icon" class="approval-metric-icon" decorative />
        </div>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="surface-block users-toolbar-panel">
      <div class="users-toolbar-stack">
        <div class="users-toolbar-head">
          <SectionHeading
            title="فهرست کاربران"
            description="جستجو، فیلتر و مدیریت کاربران سازمان"
          />

          <div class="users-header-actions">
            <span class="meta-pill">{{ filteredUsers.length }} نتیجه</span>
            <button
              v-if="canManageUsers"
              class="action-btn tone-primary users-add-btn"
              type="button"
              @click="openUserComposer"
            >
              <IconlyIcon name="person_add" decorative />
              <span>افزودن کاربر</span>
            </button>
          </div>
        </div>

        <div class="users-toolbar-primary">
          <label class="users-search-shell">
            <IconlyIcon name="search" size="sm" decorative />
            <input v-model="searchQuery" type="search" placeholder="جستجوی نام، سمت یا بخش..." autocomplete="off" />
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
      </div>
    </section>

    <section class="surface-block users-grid-panel">
      <div v-if="visibleUsers.length" class="user-directory-grid">
        <button
          v-for="item in visibleUsers"
          :key="item.id || item.username"
          class="compact-user-card"
          type="button"
          @click="openUserDetails(item.id)"
        >
          <div class="user-card-head">
            <div class="user-directory-main">
              <UserAvatar
                :person="item"
                :name="item.name"
                :avatar="item.avatar"
                size="md"
              />
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
      <InfiniteScrollSentinel
        :disabled="!hasMoreUsers || loadingMoreUsers"
        @reach-end="loadMoreUsers"
      >
        <small v-if="loadingMoreUsers" class="list-loading-more">در حال بارگذاری...</small>
        <small v-else-if="hasMoreUsers" class="list-loading-more">برای ادامه اسکرول کنید</small>
      </InfiniteScrollSentinel>

      <div v-else class="empty-state-inline">
        <IconlyIcon name="group_off" decorative />
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
          <div class="user-hero-identity">
            <UserAvatar
              :name="selectedUser.name"
              :avatar="selectedUser.avatar"
              :avatar-url="modalAvatarUrl"
              size="lg"
            />
            <div>
              <p class="page-eyebrow">جزئیات کاربر</p>
              <h2>{{ selectedUser.name }}</h2>
            </div>
          </div>
          <div class="user-hero-meta">
            <span class="user-role-pill">{{ selectedUser.jobTitle || selectedUser.role || '-' }}</span>
            <span class="user-meta-divider"></span>
            <span>{{ selectedUser.department || 'بدون بخش' }}</span>
            <span class="user-meta-divider"></span>
            <span dir="ltr">{{ selectedUser.username || '-' }}</span>
          </div>
        </div>

        <div class="user-status-panel">
          <div class="user-status-icon">
            <IconlyIcon :name="selectedUser.isActive ? 'verified_user' : 'person_off'" decorative />
          </div>
          <div class="user-status-copy">
            <strong>{{ selectedUser.status || '-' }}</strong>
          </div>
        </div>
      </section>

      <ProfileAvatarEditor
        :name="editableUser.fullName || selectedUser.name"
        :avatar="selectedUser.avatar"
        :avatar-url="modalAvatarUrl"
        :avatar-file-name="modalAvatarFileName"
        :preview-url="avatarDraftPreview"
        size="lg"
        :busy="savingUser"
        :disabled="!canManageUsers"
        title="افزودن پروفایل"
        description="عکس انتخاب‌شده پس از ذخیره در فهرست کاربران، تنظیمات و ورود/خروج نمایش داده می‌شود."
        @select="onUserAvatarSelected"
        @clear="onUserAvatarCleared"
      />

      <section class="user-meta-board">
        <article class="user-meta-card">
          <div class="user-meta-icon"><IconlyIcon name="badge" decorative /></div>
          <div class="user-meta-copy"><span>سمت</span><strong>{{ selectedUser.jobTitle || selectedUser.role || '-' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><IconlyIcon name="apartment" decorative /></div>
          <div class="user-meta-copy"><span>بخش</span><strong>{{ selectedUser.department || '-' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><IconlyIcon name="mail" decorative /></div>
          <div class="user-meta-copy"><span>نام کاربری</span><strong dir="ltr">{{ selectedUser.username || '-' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><IconlyIcon name="smartphone" decorative /></div>
          <div class="user-meta-copy"><span>موبایل</span><strong dir="ltr">{{ selectedUser.phone || '-' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><IconlyIcon name="supervisor_account" decorative /></div>
          <div class="user-meta-copy"><span>مدیر مستقیم</span><strong>{{ selectedUser.manager || 'ندارد' }}</strong></div>
        </article>
        <article class="user-meta-card">
          <div class="user-meta-icon"><IconlyIcon :name="selectedUser.isActive ? 'verified_user' : 'person_off'" decorative /></div>
          <div class="user-meta-copy"><span>وضعیت حساب</span><strong>{{ selectedUser.status || '-' }}</strong></div>
        </article>
      </section>

      <section class="surface-inline user-form-panel">
        <div class="section-label-row">
          <SectionHeading
            title="ویرایش کاربر"
            description="اطلاعات هویتی، دسترسی و وضعیت حساب کاربر انتخاب‌شده را از این بخش بروزرسانی کنید."
          />
        </div>

        <div class="modal-grid two-col">
          <label class="field-shell">
            <span>نام کامل</span>
            <input v-model="editableUser.fullName" type="text" :disabled="!canManageUsers" />
          </label>

          <label class="field-shell">
            <span>نام کاربری</span>
            <input v-model="editableUser.username" type="text" dir="ltr" :disabled="!canManageUsers" />
          </label>

          <label class="field-shell">
            <span>رمز عبور فعلی</span>
            <div class="password-field-row">
              <input
                :value="selectedUser.currentPassword || 'ثبت نشده'"
                :type="showCurrentPassword ? 'text' : 'password'"
                dir="ltr"
                readonly
              />
              <button
                class="icon-btn"
                type="button"
                :title="showCurrentPassword ? 'مخفی کردن' : 'نمایش رمز'"
                @click="showCurrentPassword = !showCurrentPassword"
              >
                <IconlyIcon :name="showCurrentPassword ? 'close' : 'show'" decorative />
              </button>
            </div>
          </label>

          <label class="field-shell">
            <span>رمز عبور جدید</span>
            <input v-model="editableUser.password" type="password" placeholder="در صورت نیاز تغییر دهید" :disabled="!canManageUsers" />
          </label>

          <label class="field-shell">
            <span>موبایل</span>
            <input v-model="editableUser.phone" type="text" dir="ltr" :disabled="!canManageUsers" />
          </label>

          <label class="field-shell">
            <span>نوع دسترسی</span>
            <select v-model="editableUser.accessRole" :disabled="!canManageUsers">
              <option value="admin">مدیرعامل</option>
              <option value="executive_manager">مدیر ارشد</option>
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

          <label class="field-shell">
            <span>عنوان شغلی</span>
            <input v-model="editableUser.jobTitle" type="text" :disabled="!canManageUsers" />
          </label>
        </div>

        <div class="user-finance-stack">
          <section class="surface-inline user-finance-panel">
            <div class="section-label-row">
              <SectionHeading
                title="پاداش و جریمه"
                description="ثبت یا تعدیل پاداش و جریمه برای کاربر انتخاب‌شده."
              />
            </div>

            <div class="modal-grid two-col finance-duo">
              <div class="field-shell finance-field-shell is-bonus">
                <span>پاداش</span>
                <strong class="finance-current-value">{{ selectedUser.bonusAmount || '0' }}</strong>
                <div class="finance-input-row">
                  <input
                    :value="editableUser.bonusDelta"
                    type="text"
                    inputmode="numeric"
                    placeholder="مبلغ جدید"
                    :disabled="!canManageUsers || applyingBonus"
                    @input="handleMoneyInput('bonusDelta', $event.target.value)"
                  />
                  <button
                    class="action-btn tone-primary finance-apply-btn"
                    type="button"
                    :disabled="!canManageUsers || applyingBonus"
                    @click="applyBonusDelta"
                  >
                    <IconlyIcon name="add_circle" decorative />
                    <span>{{ applyingBonus ? '...' : 'افزودن' }}</span>
                  </button>
                </div>
              </div>

              <div class="field-shell finance-field-shell is-penalty">
                <span>جریمه</span>
                <strong class="finance-current-value">{{ selectedUser.penaltyAmount || '0' }}</strong>
                <div class="finance-input-row">
                  <input
                    :value="editableUser.penaltyDelta"
                    type="text"
                    inputmode="numeric"
                    placeholder="مبلغ جدید"
                    :disabled="!canManageUsers || applyingPenalty"
                    @input="handleMoneyInput('penaltyDelta', $event.target.value)"
                  />
                  <button
                    class="action-btn tone-primary finance-apply-btn"
                    type="button"
                    :disabled="!canManageUsers || applyingPenalty"
                    @click="applyPenaltyDelta"
                  >
                    <IconlyIcon name="add_circle" decorative />
                    <span>{{ applyingPenalty ? '...' : 'افزودن' }}</span>
                  </button>
                </div>
              </div>
            </div>
          </section>

          <UserEntrustedPanel
            ref="entrustedPanelRef"
            mode="remote"
            :items="selectedUser.entrustedItems || []"
            :disabled="!canManageUsers"
            :busy="applyingEntrusted"
            @add="onAddEntrustedItem"
            @remove="onRemoveEntrustedItem"
          />
        </div>

        <div class="user-access-grid">
          <label
            v-for="item in sectionAccessOptions"
            :key="item.key"
            :class="['check-tile', editableUser.sectionAccess[item.key] && 'is-checked']"
          >
            <input v-model="editableUser.sectionAccess[item.key]" type="checkbox" :disabled="!canManageUsers" />
            <IconlyIcon :name="editableUser.sectionAccess[item.key] ? 'check_circle' : 'radio_button_unchecked'" class="check-state" decorative />
            <div>
              <strong>{{ item.title }}</strong>
            </div>
            <span class="check-tile-badge">انتخاب شده</span>
          </label>
        </div>
      </section>

      <ErrorNotice :error="state.lastErrorDetails" compact />

      <section class="user-modal-actions">
        <button class="action-btn tone-soft" type="button" @click="closeUserDetails">
          <IconlyIcon name="close" decorative />
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
          <IconlyIcon :name="editableUser.isActive ? 'person_off' : 'person_check'" decorative />
          <span>{{ savingUser ? 'در حال ذخیره...' : editableUser.isActive ? 'غیرفعال‌سازی' : 'فعال‌سازی' }}</span>
        </button>

        <button
          v-if="canManageUsers"
          class="action-btn tone-primary"
          type="button"
          :disabled="savingUser"
          @click="saveUserChanges"
        >
          <IconlyIcon name="save" decorative />
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
  background: #f7fbfa;
  border-radius: 16px;
  box-shadow: 0 8px 22px rgba(40, 110, 105, 0.12);
}

.users-toolbar-stack {
  display: grid;
  gap: 14px;
}

.users-toolbar-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(52, 144, 139, 0.14);
}

.users-toolbar-head h3,
.users-toolbar-head p {
  margin: 0;
}

.users-toolbar-head h3 {
  color: #152523;
  font-size: 1rem;
}

.users-toolbar-head p {
  margin-top: 4px;
  color: #45605c;
  font-size: 0.78rem;
}

.users-header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex: 0 1 auto;
  min-width: 0;
  max-width: 100%;
}

.users-header-actions .meta-pill {
  flex: 0 0 auto;
}

.users-add-btn {
  width: auto;
  min-width: 0;
  min-height: 42px !important;
  justify-content: center;
  white-space: nowrap;
}

.users-toolbar-primary {
  display: grid;
  grid-template-columns: minmax(0, 280px) minmax(0, 1fr);
  align-items: center;
  gap: 10px 14px;
}

.users-search-shell {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 38px;
  max-width: 280px;
  padding: 0 12px;
  border-radius: 10px;
  background: #eef6f4;
  border: 1px solid rgba(52, 144, 139, 0.18);
  box-shadow: none;
}

.users-search-shell:focus-within {
  background: #fff;
  border-color: #34908B;
  box-shadow: 0 0 0 3px rgba(52, 144, 139, 0.14);
}

.users-search-shell input {
  width: 100%;
  min-width: 0;
  height: 36px;
  border: 0;
  outline: none;
  background: transparent;
  color: #152523;
  font: inherit;
  font-size: 0.86rem;
}

.users-search-shell input::placeholder {
  color: #6d8a85;
}

.users-chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.user-directory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.compact-user-card {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: 14px;
  border: 0;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 4px 14px rgba(40, 110, 105, 0.1);
  transition: transform 160ms ease, box-shadow 160ms ease;
  text-align: right;
}

.compact-user-card:hover {
  transform: translateY(-2px);
  border-color: transparent;
  box-shadow: 0 8px 20px rgba(40, 110, 105, 0.14);
}

.user-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.user-directory-main {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  flex: 1 1 auto;
  min-width: 0;
}

.user-directory-main :deep(.user-avatar-face) {
  flex: 0 0 auto;
  position: relative;
  z-index: 2;
}

.user-avatar {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #dcefec;
  color: #1f5c59;
  font-weight: 800;
}

.user-card-copy {
  display: grid;
  gap: 3px;
  flex: 1 1 auto;
  min-width: 0;
}

.user-card-copy strong,
.user-card-copy small,
.user-card-details span,
.user-meta-copy strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow-wrap: normal;
  word-break: normal;
}

.user-card-details span,
.user-meta-copy strong {
  white-space: normal;
  overflow-wrap: break-word;
}

.user-card-copy strong {
  color: #152523;
  font-size: 0.9rem;
}

.user-card-copy small {
  color: #45605c;
  font-size: 0.75rem;
}

.user-card-details {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  color: #1f5c59;
  font-size: 0.72rem;
}

.user-card-details span {
  padding: 6px 8px;
  border-radius: 8px;
  background: #e4f4f2;
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
  background: var(--surface, #fff);
  box-shadow: none;
}

.user-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 24px;
  border-radius: 12px;
}

.user-hero-copy,
.user-status-copy,
.user-meta-copy {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.user-hero-identity {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.user-hero-identity > div {
  min-width: 0;
}

.user-hero-identity h2 {
  margin: 0;
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
  border-radius: 12px;
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
  border-radius: 12px;
  font-size: 28px;
  color: #fff;
  background: var(--surface, #fff);
}

.user-modal-shell.is-rejected .user-status-icon {
  background: var(--surface, #fff);
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.user-meta-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
  padding: 18px;
  border-radius: 12px;
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

.password-field-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.password-field-row input {
  width: 100%;
}

.user-finance-stack {
  display: grid;
  gap: 14px;
}

.user-finance-panel {
  display: grid;
  gap: 14px;
  padding: 16px;
  border-radius: 16px;
  background:
    linear-gradient(160deg, rgba(248, 250, 252, 0.98), rgba(232, 240, 248, 0.9));
  border: 1px solid rgba(36, 59, 107, 0.1);
}

.finance-field-shell {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(36, 59, 107, 0.08);
}

.finance-field-shell.is-bonus {
  border-color: rgba(52, 144, 139, 0.22);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(220, 239, 236, 0.55));
}

.finance-field-shell.is-penalty {
  border-color: rgba(171, 67, 67, 0.18);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 232, 232, 0.55));
}

.finance-field-shell > span {
  color: #45605c;
  font-size: 0.82rem;
  font-weight: 700;
}

.finance-field-shell.is-penalty > span {
  color: #8a3d3d;
}

.finance-current-value {
  color: #152523;
  font-size: 1.25rem;
  line-height: 1.4;
  font-weight: 800;
  direction: ltr;
  text-align: right;
}

.finance-field-shell.is-penalty .finance-current-value {
  color: #8a3d3d;
}

.finance-field-shell.is-bonus .finance-current-value {
  color: #1f5c59;
}

.finance-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.finance-apply-btn {
  min-height: 44px;
  white-space: nowrap;
}

.user-access-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.user-modal-shell :deep(.modal-grid.two-col),
.user-modal-shell .modal-grid.two-col,
.user-modal-shell .user-meta-board,
.user-modal-shell .user-access-grid,
.user-modal-shell .user-finance-panel .modal-grid.two-col {
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
}

.check-tile {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(36, 59, 107, 0.1);
  background: rgba(255, 255, 255, 0.76);
  color: #203255;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.check-tile input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.check-tile.is-checked {
  border-color: #34908B;
  background: #dcefec;
  box-shadow: inset 0 0 0 2px #34908B;
}

.check-state {
  color: #5f7a76;
  font-size: 22px;
}

.check-tile.is-checked .check-state,
.check-tile.is-checked strong {
  color: #1f5c59;
}

.check-tile strong,
.check-tile small {
  display: block;
}

.check-tile small {
  margin-top: 4px;
  color: var(--muted);
  overflow-wrap: break-word;
  word-break: normal;
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
}

@media (max-width: 760px) {
  .users-toolbar-head {
    align-items: stretch;
    flex-direction: column;
  }

  .users-header-actions {
    width: 100%;
    justify-content: stretch;
  }

  .users-add-btn {
    width: 100%;
    flex: 1 1 100%;
  }

  .user-card-head {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
  }

  .user-directory-main {
    flex: 1 1 calc(100% - 72px);
    min-width: 0;
  }

  .user-card-head > .status-badge {
    flex: 0 0 auto;
    max-width: 100%;
  }

  .users-toolbar-primary {
    grid-template-columns: 1fr;
  }

  .users-search-shell {
    max-width: none;
  }

  .user-directory-grid,
  .user-card-details {
    grid-template-columns: 1fr;
  }

  .user-modal-shell {
    gap: 16px;
    padding: 0;
  }

  .user-hero {
    padding: 16px;
    border-radius: 12px;
  }

  .finance-input-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .user-status-panel,
  .user-modal-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .user-modal-actions .action-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 420px) {
  .user-directory-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .user-modal-shell :deep(.modal-grid.two-col),
  .user-modal-shell .modal-grid.two-col,
  .user-modal-shell .user-meta-board,
  .user-modal-shell .user-access-grid,
  .user-modal-shell .user-finance-panel .modal-grid.two-col {
    grid-template-columns: minmax(0, 1fr) !important;
  }
}
</style>
