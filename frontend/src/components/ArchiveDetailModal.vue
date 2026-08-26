<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import UserAvatar from './UserAvatar.vue'
import { isoToJalali } from '../utils/jalali'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  item: { type: Object, default: null },
})

const emit = defineEmits(['close', 'updated', 'deleted'])

const {
  state,
  referArchiveDocument,
  approveArchiveDocument,
  deleteArchiveDocument,
  createProtectedObjectUrl,
  downloadProtectedFile,
  clearLastError,
} = useWorkflowHub()

const referOpen = ref(false)
const previewOpen = ref(false)
const selectedIds = ref([])
const referSearch = ref('')
const busy = ref(false)
const localError = ref('')
const previewObjectUrl = ref('')
const previewLoading = ref(false)

const documentItem = computed(() => props.item || null)
const isImage = computed(() => documentItem.value?.previewKind === 'image')
const isPdf = computed(() => documentItem.value?.previewKind === 'pdf')
const previewSrc = computed(() => {
  if (!previewObjectUrl.value) return ''
  return isPdf.value ? `${previewObjectUrl.value}#page=1` : previewObjectUrl.value
})

const recipients = computed(() => {
  const users = [
    ...(state.directories?.managers || []),
    ...(state.users || []),
    ...(state.directories?.users || []),
  ]
  const existing = new Set((documentItem.value?.referrals || []).map((item) => Number(item.id)))
  const seen = new Set()
  const query = referSearch.value.trim().toLowerCase()
  return users
    .map((item) => ({
      id: Number(item.id),
      name: item.name || item.fullName || item.full_name || '',
      role: item.role || item.jobTitle || '',
      department: typeof item.department === 'string' ? item.department : (item.department?.name || ''),
      avatarUrl: item.avatarUrl || item.avatar_url || '',
      avatar: item.avatar || '',
    }))
    .filter((item) => {
      if (!item.id || !item.name || seen.has(item.id)) return false
      if (item.id === Number(state.currentUser.id)) return false
      if (item.id === Number(documentItem.value?.owner?.id)) return false
      if (existing.has(item.id)) return false
      seen.add(item.id)
      if (!query) return true
      return [item.name, item.role, item.department].some((field) => String(field || '').toLowerCase().includes(query))
    })
})

function revokePreview() {
  if (!previewObjectUrl.value) return
  URL.revokeObjectURL(previewObjectUrl.value)
  previewObjectUrl.value = ''
}

async function loadPreview() {
  const url = documentItem.value?.downloadUrl || documentItem.value?.previewUrl
  if (!props.open || !previewOpen.value || !url || (!isImage.value && !isPdf.value)) return
  previewLoading.value = true
  try {
    revokePreview()
    const inlineUrl = url.includes('?') ? `${url}&inline=1` : `${url}?inline=1`
    previewObjectUrl.value = await createProtectedObjectUrl(inlineUrl)
  } catch (error) {
    localError.value = error?.message || 'پیش‌نمایش فایل در دسترس نیست.'
  } finally {
    previewLoading.value = false
  }
}

watch(
  () => props.open,
  (open) => {
    if (!open) {
      revokePreview()
      return
    }
    clearLastError()
    referOpen.value = false
    previewOpen.value = false
    selectedIds.value = []
    referSearch.value = ''
    localError.value = ''
  },
)

watch(
  () => [props.open, previewOpen.value, documentItem.value?.id, documentItem.value?.previewKind],
  () => {
    if (previewOpen.value) void loadPreview()
    else revokePreview()
  },
)

function shamsi(value) {
  if (!value) return '-'
  return isoToJalali(String(value).slice(0, 10)) || value
}

function toggle(id) {
  const set = new Set(selectedIds.value)
  if (set.has(id)) set.delete(id)
  else set.add(id)
  selectedIds.value = [...set]
}

async function submitRefer() {
  if (!documentItem.value?.id || !selectedIds.value.length) {
    localError.value = 'حداقل یک نفر را برای ارجاع انتخاب کنید.'
    return
  }
  busy.value = true
  localError.value = ''
  try {
    const updated = await referArchiveDocument(documentItem.value.id, selectedIds.value)
    emit('updated', updated)
    referOpen.value = false
    selectedIds.value = []
  } catch (error) {
    localError.value = error?.message || 'ارجاع ناموفق بود.'
  } finally {
    busy.value = false
  }
}

async function submitApprove() {
  if (!documentItem.value?.id || !documentItem.value?.canApprove) return
  busy.value = true
  localError.value = ''
  try {
    const updated = await approveArchiveDocument(documentItem.value.id)
    emit('updated', updated)
  } catch (error) {
    localError.value = error?.message || 'تأیید سند ناموفق بود.'
  } finally {
    busy.value = false
  }
}

async function removeItem() {
  if (!documentItem.value?.id || !documentItem.value?.canDelete) return
  if (!window.confirm('این سند از بایگانی حذف شود؟')) return
  busy.value = true
  try {
    await deleteArchiveDocument(documentItem.value.id)
    emit('deleted', documentItem.value.id)
    emit('close')
  } catch (error) {
    localError.value = error?.message || 'حذف ناموفق بود.'
  } finally {
    busy.value = false
  }
}

function openPreview() {
  previewOpen.value = true
  referOpen.value = false
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="emit('close')">
    <div v-if="documentItem" class="detail-layout archive-detail">
      <div class="modal-headline">
        <p class="page-eyebrow">{{ documentItem.code }}</p>
        <h2>{{ documentItem.title }}</h2>
        <p>{{ documentItem.description || 'بدون توضیحات' }}</p>
        <span :class="['archive-status-pill', `is-${documentItem.status || 'recorded'}`]">
          {{ documentItem.statusLabel || 'ثبت شده' }}
        </span>
      </div>

      <ErrorNotice v-if="state.lastErrorDetails" :error="state.lastErrorDetails" />
      <p v-if="localError" class="form-inline-error">{{ localError }}</p>

      <div class="archive-meta-grid">
        <article>
          <span>تاریخ سند</span>
          <strong>{{ shamsi(documentItem.documentDate) }}</strong>
        </article>
        <article>
          <span>ثبت‌کننده</span>
          <strong>{{ documentItem.ownerName || documentItem.owner?.name || '-' }}</strong>
        </article>
        <article>
          <span>بخش</span>
          <strong>{{ documentItem.department || '-' }}</strong>
        </article>
        <article>
          <span>فایل</span>
          <strong>{{ documentItem.fileName || '-' }}</strong>
        </article>
      </div>

      <section v-if="previewOpen" class="archive-preview-panel">
        <div class="archive-preview-head">
          <strong>پیش‌نمایش فایل</strong>
          <button class="action-btn tone-soft" type="button" @click="previewOpen = false">بستن پیش‌نمایش</button>
        </div>
        <div class="archive-preview-stage">
          <p v-if="previewLoading" class="empty-hint">در حال آماده‌سازی پیش‌نمایش…</p>
          <img v-else-if="isImage && previewObjectUrl" :src="previewObjectUrl" alt="" class="archive-preview-image" />
          <iframe
            v-else-if="isPdf && previewSrc"
            :src="previewSrc"
            class="archive-preview-frame"
            title="پیش‌نمایش سند"
          />
          <p v-else class="empty-hint">برای این نوع فایل پیش‌نمایش داخلی پشتیبانی نمی‌شود. از دانلود استفاده کنید.</p>
        </div>
      </section>

      <section class="archive-people">
        <strong>افراد ارجاع‌شده</strong>
        <div v-if="documentItem.referrals?.length" class="people-row">
          <span
            v-for="person in documentItem.referrals"
            :key="person.id"
            :class="['person-pill', person.isApproved && 'is-approved']"
          >
            <UserAvatar :person="person" :name="person.name" size="sm" />
            <span class="person-copy">
              <b>{{ person.name }}</b>
              <small>{{ person.statusLabel || 'در حال بررسی' }}</small>
            </span>
          </span>
        </div>
        <p v-else class="empty-hint">هنوز به کسی ارجاع نشده است.</p>
      </section>

      <section v-if="referOpen" class="archive-refer-panel">
        <label class="search-shell">
          <IconlyIcon name="search" decorative />
          <input v-model="referSearch" type="search" placeholder="جستجوی فرد برای ارجاع..." />
        </label>
        <div class="recipient-list">
          <button
            v-for="user in recipients"
            :key="user.id"
            type="button"
            :class="['recipient-card', selectedIds.includes(user.id) && 'is-selected']"
            @click="toggle(user.id)"
          >
            <UserAvatar :person="user" :name="user.name" size="sm" />
            <span>
              <strong>{{ user.name }}</strong>
              <small>{{ user.role || user.department || 'عضو مجموعه' }}</small>
            </span>
          </button>
          <p v-if="!recipients.length" class="empty-hint">فرد قابل ارجاعی باقی نمانده است.</p>
        </div>
        <div class="modal-actions compact">
          <button class="action-btn tone-soft" type="button" @click="referOpen = false">بستن</button>
          <button class="action-btn tone-primary" type="button" :disabled="busy || !selectedIds.length" @click="submitRefer">
            ثبت ارجاع
          </button>
        </div>
      </section>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="emit('close')">بستن</button>
        <button
          v-if="documentItem.canDownload"
          class="action-btn tone-soft"
          type="button"
          @click="openPreview"
        >
          <IconlyIcon name="visibility" decorative />
          <span>مشاهده</span>
        </button>
        <button
          v-if="documentItem.canDownload"
          class="action-btn tone-soft"
          type="button"
          @click="downloadProtectedFile(documentItem.downloadUrl, documentItem.fileName)"
        >
          <IconlyIcon name="download" decorative />
          <span>دانلود</span>
        </button>
        <button
          v-if="documentItem.canApprove"
          class="action-btn tone-primary"
          type="button"
          :disabled="busy"
          @click="submitApprove"
        >
          <IconlyIcon name="verified" decorative />
          <span>تأیید سند</span>
        </button>
        <button
          v-if="documentItem.canRefer && !referOpen"
          class="action-btn tone-primary"
          type="button"
          @click="referOpen = true; previewOpen = false"
        >
          <IconlyIcon name="forward" decorative />
          <span>ارجاع</span>
        </button>
        <button
          v-if="documentItem.canDelete"
          class="action-btn tone-soft is-danger"
          type="button"
          :disabled="busy"
          @click="removeItem"
        >
          <IconlyIcon name="delete" decorative />
          <span>حذف</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.archive-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.archive-meta-grid article {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(52, 144, 139, 0.06);
  border: 1px solid rgba(52, 144, 139, 0.12);
}
.archive-meta-grid span {
  display: block;
  color: #5f7a76;
  font-size: 0.78rem;
  font-weight: 700;
}
.archive-meta-grid strong {
  display: block;
  margin-top: 4px;
  color: #123735;
  overflow-wrap: anywhere;
}
.archive-status-pill {
  display: inline-flex;
  margin-top: 10px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  background: rgba(100, 116, 139, 0.12);
  color: #334155;
}
.archive-status-pill.is-reviewing {
  background: rgba(217, 119, 6, 0.14);
  color: #b45309;
}
.archive-status-pill.is-approved {
  background: rgba(22, 163, 74, 0.14);
  color: #15803d;
}
.archive-people,
.archive-refer-panel,
.archive-preview-panel {
  display: grid;
  gap: 10px;
  margin-top: 4px;
}
.archive-preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.archive-preview-stage {
  min-height: 280px;
  border-radius: 16px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  background: #f4faf8;
  overflow: hidden;
  display: grid;
  place-items: center;
}
.archive-preview-image {
  width: 100%;
  max-height: 420px;
  object-fit: contain;
  display: block;
}
.archive-preview-frame {
  width: 100%;
  min-height: 420px;
  border: 0;
  background: #fff;
}
.people-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.person-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(31, 92, 89, 0.08);
  color: #1f5c59;
  font-size: 0.84rem;
  font-weight: 700;
}
.person-pill.is-approved {
  background: rgba(22, 163, 74, 0.12);
  color: #166534;
}
.person-copy {
  display: grid;
  gap: 1px;
}
.person-copy b {
  font-weight: 800;
}
.person-copy small {
  font-size: 0.7rem;
  font-weight: 700;
  opacity: 0.8;
}
.recipient-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  max-height: 220px;
  overflow: auto;
}
.recipient-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  background: #fff;
  text-align: right;
  cursor: pointer;
  font: inherit;
}
.recipient-card.is-selected {
  border-color: rgba(52, 144, 139, 0.4);
  background: rgba(52, 144, 139, 0.08);
}
.recipient-card strong,
.recipient-card small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recipient-card small { color: #5f7a76; font-size: 0.75rem; }
.empty-hint { margin: 0; color: #5f7a76; }
.form-inline-error {
  color: #b91c1c;
  margin: 0 0 10px;
  font-weight: 700;
}
.modal-actions.compact { margin-top: 4px; }
.action-btn.is-danger { color: #9a3f34; }
@media (max-width: 720px) {
  .archive-meta-grid,
  .recipient-list { grid-template-columns: 1fr; }
  .archive-preview-frame { min-height: 320px; }
}
</style>
