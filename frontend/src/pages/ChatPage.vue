<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { formatTehranDateTime } from '../utils/jalali'
import { createLiveEventSource, parseLiveEvent } from '../utils/live'
import { useWorkflowHub } from '../stores/workflowHub'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
const FALLBACK_POLL_MS = 30000

const { state, loadChatUnreadConversations } = useWorkflowHub()

const conversations = ref([])
const users = ref([])
const messages = ref([])
const selectedId = ref(null)
const listSearch = ref('')
const userSearch = ref('')
const composer = ref('')
const pendingFile = ref(null)
const fileInputRef = ref(null)
const loadingList = ref(false)
const loadingThread = ref(false)
const sending = ref(false)
const showNewChat = ref(false)
const newChatMode = ref('direct')
const groupTitle = ref('')
const groupMemberSearch = ref('')
const groupMemberIds = ref([])
const showGroupInfo = ref(false)
const groupEditTitle = ref('')
const groupSaving = ref(false)
const creatingGroup = ref(false)
const lastError = ref('')
const threadRef = ref(null)
const mobileShowThread = ref(false)

let pollTimer = null
let liveStream = null
let liveRefreshTimer = null
let pollInFlight = false

function resolveMediaUrl(rawUrl) {
  const value = String(rawUrl || '').trim()
  if (!value) return ''
  if (/^https?:\/\//i.test(value) || value.startsWith('blob:')) return value
  if (value.startsWith('/')) return `${API_ORIGIN}${value}`
  return `${API_ORIGIN}/${value}`
}

function normalizeMessage(message) {
  if (!message) return message
  const attachment = message.attachment
    ? {
        ...message.attachment,
        fileUrl: resolveMediaUrl(message.attachment.fileUrl || message.attachment.file_url),
      }
    : null
  return { ...message, attachment }
}

async function chatFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (state.authToken) headers.Authorization = `Bearer ${state.authToken}`
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    let detail = 'خطا در ارتباط با سرور'
    try {
      const payload = await response.json()
      detail = payload.detail || payload.message || detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }
  if (response.status === 204) return null
  return response.json()
}

const selectedConversation = computed(() => conversations.value.find((item) => item.id === selectedId.value) || null)
const selectedIsGroup = computed(() => isGroupConversation(selectedConversation.value))

function isGroupConversation(item) {
  return Boolean(item?.isGroup || item?.type === 'group')
}

function conversationName(item) {
  if (!item) return 'همکار'
  return item.displayName || item.title || item.peer?.name || item.peer?.fullName || 'همکار'
}

function conversationSubtitle(item) {
  if (!item) return ''
  if (isGroupConversation(item)) {
    const count = Number(item.memberCount || item.members?.length || 0)
    return `${count.toLocaleString('fa-IR')} عضو`
  }
  return item.peer?.role || item.peer?.department || ''
}

function groupInitials(title) {
  const parts = String(title || 'گ').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return 'گ'
  if (parts.length === 1) return parts[0].slice(0, 2)
  return `${parts[0][0] || ''}${parts[1][0] || ''}`
}

const filteredConversations = computed(() => {
  const q = listSearch.value.trim().toLowerCase()
  if (!q) return conversations.value
  return conversations.value.filter((item) => {
    const name = conversationName(item).toLowerCase()
    const preview = String(item.lastMessage?.body || item.lastPreview || '').toLowerCase()
    const members = (item.members || []).map((member) => `${member.name || ''} ${member.role || ''} ${member.department || ''}`.toLowerCase()).join(' ')
    return name.includes(q) || preview.includes(q) || members.includes(q)
  })
})

const filteredUsers = computed(() => {
  const q = userSearch.value.trim().toLowerCase()
  return users.value.filter((user) => {
    if (!q) return true
    const hay = `${user.name || ''} ${user.role || ''} ${user.department || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

const groupPickerUsers = computed(() => {
  const q = groupMemberSearch.value.trim().toLowerCase()
  return users.value.filter((user) => {
    if (!q) return true
    const hay = `${user.name || ''} ${user.role || ''} ${user.department || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

const canCreateGroup = computed(() =>
  groupTitle.value.trim().length >= 2 && groupMemberIds.value.length >= 1,
)

const groupCreateHint = computed(() => {
  if (groupTitle.value.trim().length < 2) return 'نام گروه را وارد کنید (حداقل ۲ کاراکتر).'
  if (groupMemberIds.value.length < 1) return 'حداقل یک عضو انتخاب کنید.'
  return ''
})

function formatTime(value) {
  if (!value) return ''
  return formatTehranDateTime(value)
}

async function scrollToBottom() {
  await nextTick()
  if (threadRef.value) threadRef.value.scrollTop = threadRef.value.scrollHeight
}

async function loadConversations(quiet = false) {
  if (!quiet) loadingList.value = true
  try {
    const payload = await chatFetch('/chat/conversations')
    conversations.value = Array.isArray(payload) ? payload : []
    lastError.value = ''
  } catch (error) {
    if (!quiet) lastError.value = error.message || 'بارگذاری گفتگوها ناموفق بود.'
  } finally {
    if (!quiet) loadingList.value = false
  }
}

async function loadUsers() {
  try {
    const payload = await chatFetch('/chat/users')
    users.value = Array.isArray(payload) ? payload : []
  } catch {
    users.value = []
  }
}

async function loadMessages(conversationId, soft = false) {
  if (!conversationId) return
  if (!soft) loadingThread.value = true
  try {
    const payload = await chatFetch(`/chat/conversations/${conversationId}/messages`)
    messages.value = (Array.isArray(payload) ? payload : []).map(normalizeMessage)
    await chatFetch(`/chat/conversations/${conversationId}/read`, {
      method: 'POST',
      body: '{}',
    })
    await loadConversations(true)
    void loadChatUnreadConversations()
    if (!soft) await scrollToBottom()
    lastError.value = ''
  } catch (error) {
    if (!soft) lastError.value = error.message || 'بارگذاری پیام‌ها ناموفق بود.'
  } finally {
    if (!soft) loadingThread.value = false
  }
}

async function openConversation(conversationId) {
  selectedId.value = conversationId
  mobileShowThread.value = true
  showNewChat.value = false
  showGroupInfo.value = false
  await loadMessages(conversationId)
}

function resetGroupComposer() {
  groupTitle.value = ''
  groupMemberSearch.value = ''
  groupMemberIds.value = []
}

function toggleGroupMember(userId) {
  const id = Number(userId)
  if (!id) return
  if (groupMemberIds.value.includes(id)) {
    groupMemberIds.value = groupMemberIds.value.filter((item) => item !== id)
  } else {
    groupMemberIds.value = [...groupMemberIds.value, id]
  }
}

const selectedGroupMembers = computed(() =>
  users.value.filter((user) => groupMemberIds.value.includes(Number(user.id))),
)

async function createGroupChat() {
  if (creatingGroup.value) return
  const title = groupTitle.value.trim()
  if (title.length < 2) {
    lastError.value = 'نام گروه باید حداقل ۲ کاراکتر باشد.'
    return
  }
  if (groupMemberIds.value.length < 1) {
    lastError.value = 'حداقل یک عضو دیگر انتخاب کنید.'
    return
  }
  creatingGroup.value = true
  lastError.value = ''
  try {
    const conversation = await chatFetch('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({
        title,
        memberIds: groupMemberIds.value.map(Number),
      }),
    })
    resetGroupComposer()
    newChatMode.value = 'direct'
    await loadConversations(true)
    if (conversation?.id) await openConversation(conversation.id)
    showNewChat.value = false
  } catch (error) {
    lastError.value = error.message || 'ساخت گروه ناموفق بود.'
  } finally {
    creatingGroup.value = false
  }
}

async function refreshSelectedConversation() {
  if (!selectedId.value) return
  try {
    const conversation = await chatFetch(`/chat/conversations/${selectedId.value}`)
    conversations.value = conversations.value.map((item) => (item.id === conversation.id ? conversation : item))
    if (isGroupConversation(conversation)) {
      groupEditTitle.value = conversation.title || conversation.displayName || ''
    }
  } catch {
    await loadConversations(true)
  }
}

async function saveGroupSettings() {
  if (!selectedId.value || !selectedIsGroup.value || groupSaving.value) return
  groupSaving.value = true
  try {
    const conversation = await chatFetch(`/chat/conversations/${selectedId.value}`, {
      method: 'PATCH',
      body: JSON.stringify({ title: groupEditTitle.value.trim() }),
    })
    conversations.value = conversations.value.map((item) => (item.id === conversation.id ? conversation : item))
    lastError.value = ''
  } catch (error) {
    lastError.value = error.message || 'ذخیره گروه ناموفق بود.'
  } finally {
    groupSaving.value = false
  }
}

async function addGroupMember(userId) {
  if (!selectedId.value || !selectedIsGroup.value) return
  try {
    const conversation = await chatFetch(`/chat/conversations/${selectedId.value}`, {
      method: 'PATCH',
      body: JSON.stringify({ addMemberIds: [Number(userId)] }),
    })
    conversations.value = conversations.value.map((item) => (item.id === conversation.id ? conversation : item))
    await loadUsers()
  } catch (error) {
    lastError.value = error.message || 'افزودن عضو ناموفق بود.'
  }
}

async function removeGroupMember(userId) {
  if (!selectedId.value || !selectedIsGroup.value) return
  try {
    const conversation = await chatFetch(`/chat/conversations/${selectedId.value}`, {
      method: 'PATCH',
      body: JSON.stringify({ removeMemberIds: [Number(userId)] }),
    })
    conversations.value = conversations.value.map((item) => (item.id === conversation.id ? conversation : item))
  } catch (error) {
    lastError.value = error.message || 'حذف عضو ناموفق بود.'
  }
}

function openGroupInfo() {
  if (!selectedIsGroup.value) return
  groupEditTitle.value = selectedConversation.value?.title || selectedConversation.value?.displayName || ''
  showGroupInfo.value = true
  void loadUsers()
}

async function startChatWith(userId) {
  try {
    const conversation = await chatFetch('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ userId }),
    })
    await loadConversations(true)
    if (conversation?.id) await openConversation(conversation.id)
    showNewChat.value = false
  } catch (error) {
    lastError.value = error.message || 'شروع گفتگو ناموفق بود.'
  }
}

async function sendMessage() {
  const body = composer.value.trim()
  if (!selectedId.value || (!body && !pendingFile.value) || sending.value) return
  sending.value = true
  try {
    let message
    if (pendingFile.value) {
      const formData = new FormData()
      formData.append('body', body)
      formData.append('attachment', pendingFile.value)
      message = await chatFetch(`/chat/conversations/${selectedId.value}/messages`, {
        method: 'POST',
        body: formData,
      })
    } else {
      message = await chatFetch(`/chat/conversations/${selectedId.value}/messages`, {
        method: 'POST',
        body: JSON.stringify({ body }),
      })
    }
    composer.value = ''
    clearPendingFile()
    if (message) messages.value = [...messages.value, normalizeMessage(message)]
    await loadConversations(true)
    await scrollToBottom()
    void loadChatUnreadConversations()
    lastError.value = ''
  } catch (error) {
    lastError.value = error.message || 'ارسال پیام ناموفق بود.'
  } finally {
    sending.value = false
  }
}

function onFilePicked(event) {
  const file = event.target?.files?.[0]
  pendingFile.value = file ? markRaw(file) : null
}

function clearPendingFile() {
  pendingFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

async function refreshQuietly() {
  if (pollInFlight || sending.value || document.visibilityState === 'hidden') return
  pollInFlight = true
  try {
    const beforeUnread = conversations.value.reduce((sum, item) => sum + Number(item.unreadCount || 0), 0)
    await loadConversations(true)
    const afterUnread = conversations.value.reduce((sum, item) => sum + Number(item.unreadCount || 0), 0)
    if (afterUnread > beforeUnread) {
      void loadChatUnreadConversations()
    }
    if (selectedId.value && !composer.value.trim() && !pendingFile.value) {
      await loadMessages(selectedId.value, true)
      if (selectedIsGroup.value) await refreshSelectedConversation()
    }
  } catch {
    // keep UI
  } finally {
    pollInFlight = false
  }
}

function scheduleLiveRefresh() {
  if (liveRefreshTimer) window.clearTimeout(liveRefreshTimer)
  liveRefreshTimer = window.setTimeout(refreshQuietly, 350)
}

function stopLiveRefresh() {
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
  if (liveRefreshTimer) {
    window.clearTimeout(liveRefreshTimer)
    liveRefreshTimer = null
  }
  if (liveStream) {
    liveStream.close()
    liveStream = null
  }
}

function startLiveRefresh() {
  stopLiveRefresh()
  liveStream = createLiveEventSource(state.authToken)
  liveStream?.addEventListener('open', scheduleLiveRefresh)
  liveStream?.addEventListener('message', (event) => {
    const payload = parseLiveEvent(event.data)
    if (payload?.type !== 'chat.message.created') return
    scheduleLiveRefresh()
  })
  pollTimer = window.setInterval(refreshQuietly, FALLBACK_POLL_MS)
}

function backToList() {
  mobileShowThread.value = false
  showNewChat.value = false
  showGroupInfo.value = false
  composer.value = ''
  clearPendingFile()
}

watch(showNewChat, async (open) => {
  if (open) {
    userSearch.value = ''
    await loadUsers()
    if (newChatMode.value === 'group') resetGroupComposer()
  }
})

watch(newChatMode, (mode) => {
  userSearch.value = ''
  if (mode === 'group') resetGroupComposer()
})

onMounted(async () => {
  await loadConversations()
  await loadUsers()
  startLiveRefresh()
})

onBeforeUnmount(() => {
  stopLiveRefresh()
})
</script>

<template>
  <div class="page-shell chat-page chat-page-luxe" :class="{ 'show-thread': mobileShowThread && selectedConversation }">
    <aside class="chat-sidebar">
      <div class="chat-sidebar-accent" aria-hidden="true" />
      <header class="chat-sidebar-head">
        <div class="chat-sidebar-title">
          <p class="page-eyebrow">گفتگوی سازمانی</p>
          <h2>پیام‌ها</h2>
        </div>
        <button class="action-btn tone-primary chat-new-btn" type="button" @click="showNewChat = !showNewChat">
          <IconlyIcon :name="showNewChat ? 'arrow_back' : 'chat'" decorative />
          <span>{{ showNewChat ? 'بازگشت' : 'گفتگوی جدید' }}</span>
        </button>
      </header>

      <div v-if="showNewChat" class="chat-mode-tabs">
        <button type="button" :class="['chat-mode-tab', newChatMode === 'direct' && 'is-active']" @click="newChatMode = 'direct'">
          <IconlyIcon name="chat" decorative />
          <span>خصوصی</span>
        </button>
        <button type="button" :class="['chat-mode-tab', newChatMode === 'group' && 'is-active']" @click="newChatMode = 'group'">
          <IconlyIcon name="groups" decorative />
          <span>گروه</span>
        </button>
      </div>

      <p v-if="lastError && showNewChat" class="inline-error">{{ lastError }}</p>

      <div v-if="showNewChat && newChatMode === 'group'" class="chat-sidebar-body chat-group-compose">
        <div class="chat-group-field">
          <label class="chat-group-label" for="chat-group-title">نام گروه</label>
          <input
            id="chat-group-title"
            v-model.trim="groupTitle"
            class="chat-group-input"
            type="text"
            placeholder="مثلاً تیم مالی"
            maxlength="80"
            autocomplete="off"
          />
        </div>

        <div class="chat-group-field">
          <label class="chat-group-label" for="chat-group-member-search">جستجوی اعضا</label>
          <div class="chat-group-search">
            <IconlyIcon name="search" decorative />
            <input
              id="chat-group-member-search"
              v-model="groupMemberSearch"
              type="search"
              placeholder="نام همکار را بنویسید"
              autocomplete="off"
            />
          </div>
        </div>

        <div v-if="selectedGroupMembers.length" class="chat-member-chips">
          <button
            v-for="member in selectedGroupMembers"
            :key="member.id"
            class="chat-member-chip"
            type="button"
            :title="member.name"
            @click="toggleGroupMember(member.id)"
          >
            <UserAvatar :person="member" :name="member.name" size="sm" />
            <span>{{ member.name }}</span>
            <small>×</small>
          </button>
        </div>

        <p class="chat-group-section-title">انتخاب اعضا</p>
        <div class="chat-picker-list">
          <button
            v-for="user in groupPickerUsers"
            :key="`pick-${user.id}`"
            class="chat-picker-item"
            type="button"
            @click="toggleGroupMember(user.id)"
          >
            <UserAvatar :person="user" :name="user.name" size="md" />
            <div class="chat-list-copy">
              <strong>{{ user.name }}</strong>
              <small>{{ user.role || user.department || 'همکار' }}</small>
            </div>
            <span class="chat-picker-check" :class="{ 'is-on': groupMemberIds.includes(Number(user.id)) }">
              {{ groupMemberIds.includes(Number(user.id)) ? '✓' : '+' }}
            </span>
          </button>
          <div v-if="!groupPickerUsers.length" class="chat-empty">کاربری برای افزودن به گروه پیدا نشد.</div>
        </div>

        <div class="chat-group-compose-footer">
          <small v-if="groupCreateHint" class="chat-create-hint">{{ groupCreateHint }}</small>
          <button
            class="action-btn tone-primary chat-create-group-btn"
            type="button"
            :disabled="creatingGroup"
            @click="createGroupChat"
          >
            <IconlyIcon name="group_add" decorative />
            <span>{{ creatingGroup ? 'در حال ساخت...' : `ساخت گروه (${groupMemberIds.length.toLocaleString('fa-IR')} عضو)` }}</span>
          </button>
        </div>
      </div>

      <div v-else-if="showNewChat" class="chat-sidebar-body chat-direct-compose">
        <div class="chat-group-field chat-search-field">
          <label class="chat-group-label" for="chat-direct-search">جستجوی کاربر</label>
          <div class="chat-group-search">
            <IconlyIcon name="search" decorative />
            <input
              id="chat-direct-search"
              v-model="userSearch"
              type="search"
              placeholder="نام، سمت یا بخش همکار"
              autocomplete="off"
            />
          </div>
        </div>
        <p class="chat-group-section-title">انتخاب کاربر</p>
        <div class="chat-picker-list">
          <button
            v-for="user in filteredUsers"
            :key="user.id"
            class="chat-picker-item"
            type="button"
            @click="startChatWith(user.id)"
          >
            <UserAvatar :person="user" :name="user.name" size="md" />
            <div class="chat-list-copy">
              <strong>{{ user.name }}</strong>
              <small>{{ user.role || user.department || 'همکار' }}</small>
            </div>
          </button>
          <div v-if="!filteredUsers.length" class="chat-empty">کاربری برای شروع گفتگو پیدا نشد.</div>
        </div>
      </div>

      <div v-else class="chat-sidebar-body chat-direct-compose">
        <div class="chat-group-field chat-search-field">
          <label class="chat-group-label" for="chat-list-search">جستجوی گفتگو</label>
          <div class="chat-group-search">
            <IconlyIcon name="search" decorative />
            <input
              id="chat-list-search"
              v-model="listSearch"
              type="search"
              placeholder="نام گفتگو را بنویسید"
              autocomplete="off"
            />
          </div>
        </div>
        <div class="chat-list">
        <div v-if="loadingList && !conversations.length" class="chat-empty">در حال بارگذاری...</div>
        <button
          v-for="item in filteredConversations"
          :key="item.id"
          :class="['chat-list-item', selectedId === item.id && 'is-active']"
          type="button"
          @click="openConversation(item.id)"
        >
          <div v-if="isGroupConversation(item)" class="chat-group-avatar" :title="conversationName(item)">
            <span>{{ groupInitials(conversationName(item)) }}</span>
          </div>
          <UserAvatar
            v-else
            :person="item.peer"
            :name="item.peer?.name || 'همکار'"
            size="md"
          />
          <div class="chat-list-copy">
            <div class="chat-list-top">
              <strong>{{ conversationName(item) }}</strong>
              <small>{{ formatTime(item.lastMessage?.createdAt || item.updatedAt) }}</small>
            </div>
            <p>{{ item.lastPreview || item.lastMessage?.body || (item.lastMessage?.attachment ? 'پیوست' : 'گفتگو را شروع کنید') }}</p>
            <small v-if="isGroupConversation(item)" class="chat-group-meta">{{ conversationSubtitle(item) }}</small>
          </div>
          <span v-if="item.unreadCount" class="chat-unread">{{ item.unreadCount }}</span>
        </button>
        <div v-if="!loadingList && !filteredConversations.length" class="chat-empty">
          هنوز گفتگویی ندارید. با «چت جدید» شروع کنید.
        </div>
        </div>
      </div>
    </aside>

    <section class="chat-thread">
      <div class="chat-thread-frame">
      <template v-if="selectedConversation">
        <header class="chat-thread-head">
          <div class="chat-thread-head-accent" aria-hidden="true" />
          <button class="chat-back-btn" type="button" aria-label="بازگشت به فهرست" @click="backToList">
            <IconlyIcon name="arrow_back" decorative />
            <span class="chat-back-label">بازگشت</span>
          </button>
          <div v-if="selectedIsGroup" class="chat-group-avatar chat-group-avatar-lg" @click="openGroupInfo">
            <span>{{ groupInitials(conversationName(selectedConversation)) }}</span>
          </div>
          <UserAvatar
            v-else
            :person="selectedConversation.peer"
            :name="selectedConversation.peer?.name || 'همکار'"
            size="md"
          />
          <div class="chat-thread-heading" @click="selectedIsGroup ? openGroupInfo() : null">
            <strong>{{ conversationName(selectedConversation) }}</strong>
            <small>{{ conversationSubtitle(selectedConversation) }}</small>
          </div>
          <button
            v-if="selectedIsGroup"
            class="chat-info-btn"
            type="button"
            aria-label="اطلاعات گروه"
            @click="openGroupInfo"
          >
            <IconlyIcon name="group" decorative />
          </button>
        </header>

        <aside v-if="showGroupInfo && selectedIsGroup" class="chat-group-panel">
          <div class="chat-group-panel-head">
            <button type="button" class="chat-panel-close" aria-label="بستن" @click="showGroupInfo = false">×</button>
          </div>

          <div class="chat-group-hero">
            <div class="chat-group-hero-avatar">
              <span>{{ groupInitials(groupEditTitle || conversationName(selectedConversation)) }}</span>
            </div>
            <div class="chat-group-hero-copy">
              <span class="chat-group-hero-kicker">جزئیات گروه</span>
              <strong>{{ groupEditTitle || conversationName(selectedConversation) }}</strong>
              <small>{{ (selectedConversation.members || []).length.toLocaleString('fa-IR') }} عضو</small>
            </div>
          </div>

          <div class="chat-group-stats">
            <article>
              <small>اعضا</small>
              <strong>{{ (selectedConversation.members || []).length.toLocaleString('fa-IR') }}</strong>
            </article>
            <article>
              <small>نوع</small>
              <strong>گروهی</strong>
            </article>
          </div>

          <section class="chat-group-section">
            <div class="chat-group-section-head">
              <h3>نام گروه</h3>
              <small>عنوان نمایشی برای همه اعضا</small>
            </div>
            <label class="field-shell chat-group-name-field">
              <span>نام</span>
              <input v-model.trim="groupEditTitle" type="text" maxlength="120" placeholder="نام گروه" />
            </label>
            <button class="action-btn tone-primary chat-group-save" type="button" :disabled="groupSaving" @click="saveGroupSettings">
              {{ groupSaving ? 'در حال ذخیره...' : 'ذخیره نام' }}
            </button>
          </section>

          <section class="chat-group-section">
            <div class="chat-group-section-head">
              <h3>اعضای گروه</h3>
              <span class="meta-pill">{{ (selectedConversation.members || []).length }} نفر</span>
            </div>
            <div class="chat-group-members">
              <article v-for="member in selectedConversation.members || []" :key="member.id" class="chat-group-member-row">
                <UserAvatar :person="member" :name="member.name" size="sm" />
                <div class="chat-group-member-copy">
                  <strong>{{ member.name }}</strong>
                  <small>{{ member.role || member.department || 'عضو' }}</small>
                </div>
                <button
                  v-if="Number(member.id) !== Number(state.currentUser.id) && (selectedConversation.members || []).length > 2"
                  class="chat-member-remove"
                  type="button"
                  @click="removeGroupMember(member.id)"
                >
                  حذف
                </button>
              </article>
            </div>
          </section>

          <section class="chat-group-section">
            <div class="chat-group-section-head">
              <h3>افزودن عضو</h3>
              <small>همکاران قابل افزودن به گروه</small>
            </div>
            <div class="chat-group-add">
              <button
                v-for="user in users.filter((item) => !(selectedConversation.members || []).some((member) => Number(member.id) === Number(item.id)))"
                :key="`add-${user.id}`"
                class="chat-group-add-item"
                type="button"
                @click="addGroupMember(user.id)"
              >
                <UserAvatar :person="user" :name="user.name" size="sm" />
                <div class="chat-list-copy">
                  <strong>{{ user.name }}</strong>
                  <small>{{ user.role || user.department || 'همکار' }}</small>
                </div>
                <span class="chat-picker-check">+</span>
              </button>
              <div
                v-if="!users.filter((item) => !(selectedConversation.members || []).some((member) => Number(member.id) === Number(item.id))).length"
                class="chat-group-empty-add"
              >
                همه همکاران در این گروه هستند.
              </div>
            </div>
          </section>
        </aside>

        <div ref="threadRef" class="chat-messages">
          <div class="chat-messages-inner">
          <div v-if="loadingThread && !messages.length" class="chat-empty chat-empty-state">در حال بارگذاری پیام‌ها...</div>
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['chat-message-row', message.mine ? 'is-mine' : 'is-peer']"
          >
            <UserAvatar
              v-if="!message.mine"
              class="chat-bubble-avatar"
              :person="selectedIsGroup ? { name: message.senderName } : selectedConversation?.peer"
              :name="message.senderName || selectedConversation?.peer?.name || 'همکار'"
              size="sm"
            />
            <article :class="['chat-bubble', message.mine ? 'is-mine' : 'is-peer']">
            <small v-if="selectedIsGroup && !message.mine" class="chat-sender-name">{{ message.senderName }}</small>
            <a
              v-if="message.attachment?.isImage && message.attachment?.fileUrl"
              class="chat-attach-image"
              :href="message.attachment.fileUrl"
              target="_blank"
              rel="noopener"
            >
              <img :src="message.attachment.fileUrl" :alt="message.attachment.originalName || 'پیوست'" />
            </a>
            <a
              v-else-if="message.attachment?.fileUrl"
              class="chat-attach-file"
              :href="message.attachment.fileUrl"
              target="_blank"
              rel="noopener"
            >
              <IconlyIcon name="attach_file" decorative />
              <span>{{ message.attachment.originalName || 'دانلود پیوست' }}</span>
            </a>
            <p v-if="message.body">{{ message.body }}</p>
            <div class="chat-bubble-meta">
              <small>{{ formatTime(message.createdAt) }}</small>
              <span
                v-if="message.mine"
                class="chat-ticks"
                :class="message.read ? 'is-read' : 'is-sent'"
                :title="message.read ? 'خوانده شد' : 'ارسال شد'"
                aria-hidden="true"
              >{{ message.read ? '✓✓' : '✓' }}</span>
            </div>
            </article>
          </div>
          </div>
        </div>

        <form class="chat-composer" @submit.prevent="sendMessage">
          <div class="chat-composer-shell">
          <input
            ref="fileInputRef"
            class="chat-file-input"
            type="file"
            @change="onFilePicked"
          />
          <button class="chat-attach-btn" type="button" title="پیوست فایل" @click="fileInputRef?.click()">
            <IconlyIcon name="attach_file" decorative />
          </button>
          <div class="chat-composer-main">
            <div v-if="pendingFile" class="chat-pending-file">
              <span>{{ pendingFile.name }}</span>
              <button type="button" @click="clearPendingFile">×</button>
            </div>
            <input
              v-model="composer"
              type="text"
              placeholder="پیام خود را بنویسید..."
              @keydown.enter.exact.prevent="sendMessage"
            />
          </div>
          <button
            class="chat-send-btn"
            type="submit"
            :disabled="sending || (!composer.trim() && !pendingFile)"
          >
            <IconlyIcon name="send" decorative />
            <span class="chat-send-label">ارسال</span>
          </button>
          </div>
        </form>
      </template>

      <div v-else class="chat-thread-empty">
        <div class="chat-thread-empty-card">
          <div class="chat-empty-ornament" aria-hidden="true">
            <span /><span /><span />
          </div>
          <IconlyIcon name="forum" decorative />
          <h3>یک گفتگو انتخاب کنید</h3>
          <p>از فهرست سمت راست گفتگو را باز کنید یا چت جدید بسازید.</p>
        </div>
      </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.chat-page-luxe {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 0;
  min-height: 0;
  height: calc(100dvh - 140px);
  max-height: calc(100dvh - 140px);
  border: 1px solid rgba(52, 144, 139, 0.22);
  border-radius: 22px;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 0%, rgba(72, 103, 183, 0.12), transparent 34%),
    radial-gradient(circle at 88% 100%, rgba(52, 144, 139, 0.14), transparent 38%),
    linear-gradient(145deg, #f8fcfb 0%, #eef6f4 48%, #f4f7fb 100%);
  box-shadow:
    0 24px 60px rgba(31, 92, 89, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.85);
  position: relative;
}

.chat-page-luxe::before {
  content: '';
  position: absolute;
  inset: 10px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 16px;
  pointer-events: none;
  z-index: 0;
}

.chat-sidebar,
.chat-thread {
  display: grid;
  min-height: 0;
  position: relative;
  z-index: 1;
}

.chat-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-left: 1px solid rgba(52, 144, 139, 0.14);
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(14px);
}

.chat-sidebar-accent {
  height: 4px;
  background: linear-gradient(90deg, #34908b, #4867b7 58%, rgba(72, 103, 183, 0.35));
  flex: 0 0 auto;
}

.chat-sidebar-title {
  display: grid;
  gap: 2px;
}

.chat-sidebar-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-group-compose,
.chat-direct-compose {
  gap: 10px;
  padding: 0 16px 12px;
  overflow: hidden;
}

.chat-direct-compose .chat-search-field {
  gap: 4px;
  margin: 0;
  padding: 0;
  min-height: 0;
}

.chat-group-field.chat-search-field {
  gap: 4px;
  margin: 0;
  padding: 0;
  min-height: 0;
}

.chat-group-label {
  font-size: 11px;
  font-weight: 800;
  color: #5f7a76;
  line-height: 1.2;
  margin: 0;
}

.chat-group-input {
  width: 100%;
  min-width: 0;
  height: 40px;
  box-sizing: border-box;
  border: 1px solid rgba(52, 144, 139, 0.18);
  border-radius: 12px;
  background: #fff;
  color: #1d3f3b;
  padding: 0 12px;
  font: inherit;
  font-size: 0.9rem;
}

.chat-group-search {
  width: 100%;
  min-width: 0;
  height: 36px;
  min-height: 36px;
  max-height: 36px;
  box-sizing: border-box;
  border: 1px solid rgba(52, 144, 139, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  color: #1d3f3b;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.chat-group-search :deep(.iconly-shell) {
  flex: 0 0 auto;
  width: 16px;
  height: 16px;
  font-size: 14px;
  line-height: 1;
  color: #5f7a76;
}

.chat-group-search input {
  flex: 1 1 auto;
  width: 100%;
  min-width: 0;
  height: 100%;
  min-height: 0;
  max-height: none;
  margin: 0;
  padding: 0;
  border: 0;
  outline: none;
  background: transparent;
  box-shadow: none;
  font: inherit;
  font-size: 0.82rem;
  line-height: 1.2;
  color: inherit;
  appearance: none;
  -webkit-appearance: none;
}

.chat-group-search input::-webkit-search-decoration,
.chat-group-search input::-webkit-search-cancel-button {
  display: none;
}

.chat-group-section-title {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  color: #5f7a76;
  line-height: 1.2;
}

.chat-direct-compose .chat-search-field,
.chat-direct-compose .chat-group-field,
.chat-direct-compose .chat-group-section-title {
  flex: 0 0 auto;
}

.chat-direct-compose .chat-list,
.chat-direct-compose .chat-picker-list {
  flex: 1;
  min-height: 0;
}

.chat-group-field {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.chat-group-compose-footer {
  flex: 0 0 auto;
  display: grid;
  gap: 8px;
  padding-top: 4px;
}

.chat-create-hint {
  color: #b45309;
  font-size: 12px;
  line-height: 1.5;
}

.chat-picker-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: grid;
  gap: 8px;
  align-content: start;
  padding: 8px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.chat-picker-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 11px 12px;
  border: 1px solid transparent;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  text-align: right;
  cursor: pointer;
  color: inherit;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.chat-picker-item:hover {
  background: rgba(45, 122, 110, 0.08);
  border-color: rgba(52, 144, 139, 0.18);
  transform: translateY(-1px);
}

.chat-member-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chat-member-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  border: 0;
  border-radius: 999px;
  padding: 4px 10px 4px 4px;
  background: rgba(45, 122, 110, 0.12);
  color: #1f5c59;
  cursor: pointer;
  font: inherit;
}

.chat-member-chip span {
  min-width: 0;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-member-chip small {
  opacity: 0.7;
  flex: 0 0 auto;
}

.chat-picker-check {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  background: rgba(52, 144, 139, 0.12);
  color: #2d7a6e;
  font-weight: 800;
}

.chat-picker-check.is-on {
  background: #2d7a6e;
  color: #fff;
}

.chat-create-group-btn {
  width: 100%;
  justify-content: center;
}

.chat-create-group-btn:disabled {
  opacity: 0.72;
}

.chat-create-group-btn span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-sidebar-head,
.chat-thread-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 18px 12px;
  position: relative;
}

.chat-sidebar-head {
  border-bottom: 1px solid rgba(52, 144, 139, 0.1);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.55));
}

.chat-sidebar-head h2,
.chat-thread-head strong {
  margin: 0;
  color: #1d3f3b;
}

.chat-sidebar-head .page-eyebrow,
.chat-thread-head small,
.chat-list-copy small {
  color: #5f7a76;
}

.chat-new-btn {
  flex: 0 0 auto;
  max-width: 46%;
}

.chat-new-btn span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-search-wrap {
  flex: 0 0 auto;
  padding: 0 16px 12px;
  min-width: 0;
}

.chat-search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  min-width: 0;
  height: 32px;
  min-height: 32px;
  max-height: 32px;
  padding: 0 8px;
  box-sizing: border-box;
  border: 1px solid rgba(52, 144, 139, 0.18);
  border-radius: 10px;
  background: #fff;
  color: #1d3f3b;
  overflow: hidden;
}

.chat-search-box :deep(.iconly-shell) {
  flex: 0 0 auto;
  width: 16px;
  height: 16px;
  font-size: 14px;
  line-height: 1;
  color: #5f7a76;
}

.chat-search-box input {
  flex: 1 1 auto;
  min-width: 0;
  width: 100%;
  height: 100%;
  min-height: 0;
  margin: 0;
  padding: 0;
  border: 0 !important;
  outline: none;
  background: transparent !important;
  box-shadow: none !important;
  font: inherit;
  font-size: 0.82rem;
  line-height: 1.2;
  color: inherit;
  appearance: none;
  -webkit-appearance: none;
}

.chat-search-box input::placeholder {
  color: #7a9490;
  opacity: 1;
}

.chat-list {
  min-height: 0;
  overflow: auto;
  padding: 8px 12px 16px;
  display: grid;
  gap: 8px;
  align-content: start;
}

.chat-list-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 12px 12px 12px 14px;
  border: 1px solid rgba(52, 144, 139, 0.1);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  text-align: right;
  cursor: pointer;
  color: inherit;
  box-shadow: 0 6px 18px rgba(31, 92, 89, 0.04);
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
  position: relative;
  overflow: hidden;
}

.chat-list-item::before {
  content: '';
  position: absolute;
  inset-inline-start: 0;
  top: 10px;
  bottom: 10px;
  width: 3px;
  border-radius: 999px;
  background: transparent;
  transition: background 0.18s ease;
}

.chat-list-item:hover {
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(52, 144, 139, 0.22);
  box-shadow: 0 10px 24px rgba(31, 92, 89, 0.08);
  transform: translateY(-1px);
}

.chat-list-item.is-active {
  background: linear-gradient(135deg, rgba(52, 144, 139, 0.12), rgba(72, 103, 183, 0.08));
  border-color: rgba(52, 144, 139, 0.28);
  box-shadow: 0 12px 28px rgba(31, 92, 89, 0.1);
}

.chat-list-item.is-active::before {
  background: linear-gradient(180deg, #34908b, #4867b7);
}

.chat-avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  color: #1f4f48;
  background: rgba(45, 122, 110, 0.14);
}

.chat-list-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.chat-list-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.chat-list-copy strong,
.chat-list-copy p,
.chat-list-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-list-copy p {
  margin: 0;
  color: #5f7a76;
  font-size: 12px;
}

.chat-unread {
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  background: linear-gradient(135deg, #34908b, #2d7a6e);
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(45, 122, 110, 0.28);
}

.chat-thread-empty {
  display: grid;
  place-items: center;
  min-height: 100%;
  padding: 32px 20px;
}

.chat-thread-empty-card {
  max-width: 360px;
  padding: 28px 24px;
  border-radius: 22px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 40px rgba(31, 92, 89, 0.08);
  text-align: center;
}

.chat-empty-ornament {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 14px;
}

.chat-empty-ornament span {
  width: 28px;
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, #34908b, #4867b7);
  opacity: 0.55;
}

.chat-empty-ornament span:nth-child(2) {
  width: 42px;
  opacity: 1;
}

.chat-thread-empty-card :deep(.iconly-shell) {
  font-size: 42px;
  color: #34908b;
  margin-bottom: 8px;
}

.chat-thread-empty-card h3 {
  margin: 0 0 8px;
  color: #1f3b55;
}

.chat-thread-empty-card p {
  margin: 0;
  color: #667085;
  line-height: 1.8;
}

.chat-empty {
  padding: 20px 12px;
  text-align: center;
  color: #5f7a76;
  font-size: 0.88rem;
}

.chat-thread {
  grid-template-rows: minmax(0, 1fr);
  background: transparent;
  position: relative;
}

.chat-thread-frame {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-height: 0;
  height: 100%;
  margin: 12px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.42);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.chat-mode-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 0 16px 10px;
  padding: 5px;
  border-radius: 16px;
  background: rgba(52, 144, 139, 0.08);
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.chat-mode-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 0;
  border-radius: 10px;
  padding: 10px 12px;
  background: transparent;
  color: #5f7a76;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.chat-mode-tab.is-active {
  background: #fff;
  color: #1f5c59;
  box-shadow: 0 4px 14px rgba(31, 92, 89, 0.08);
}

.chat-group-avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #34908b, #1f5c59);
  flex: 0 0 auto;
}

.chat-group-avatar-lg {
  width: 46px;
  height: 46px;
  cursor: pointer;
}

.chat-group-meta {
  color: #6a8581;
}

.chat-thread-heading {
  display: grid;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.chat-info-btn {
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 12px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
}

.chat-group-panel {
  position: absolute;
  inset: 64px 0 56px 0;
  z-index: 4;
  background: linear-gradient(180deg, rgba(248, 252, 251, 0.98) 0%, rgba(255, 255, 255, 0.98) 28%);
  border-top: 1px solid rgba(52, 144, 139, 0.12);
  padding: 14px 16px 20px;
  overflow: auto;
  display: grid;
  gap: 14px;
  align-content: start;
}

.chat-group-panel-head {
  display: flex;
  justify-content: flex-end;
}

.chat-group-hero {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(52, 144, 139, 0.14), rgba(72, 103, 183, 0.08));
  border: 1px solid rgba(52, 144, 139, 0.12);
}

.chat-group-hero-avatar {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #34908b, #4867b7);
  color: #fff;
  font-weight: 800;
  font-size: 1.1rem;
}

.chat-group-hero-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.chat-group-hero-kicker {
  font-size: 11px;
  font-weight: 800;
  color: #34908b;
}

.chat-group-hero-copy strong {
  font-size: 1.05rem;
  color: #1f3b55;
  overflow-wrap: anywhere;
}

.chat-group-hero-copy small {
  color: #667085;
}

.chat-group-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.chat-group-stats article {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(52, 144, 139, 0.1);
  display: grid;
  gap: 4px;
}

.chat-group-stats small {
  color: #667085;
  font-size: 11px;
  font-weight: 700;
}

.chat-group-stats strong {
  color: #1f3b55;
  font-size: 1rem;
}

.chat-group-section {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(52, 144, 139, 0.08);
}

.chat-group-section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.chat-group-section-head h3 {
  margin: 0;
  font-size: 0.95rem;
  color: #1f3b55;
}

.chat-group-section-head small {
  display: block;
  margin-top: 4px;
  color: #667085;
  font-size: 11px;
}

.chat-group-name-field {
  margin: 0;
}

.chat-group-save {
  justify-self: start;
}

.chat-group-members {
  display: grid;
  gap: 8px;
  max-height: 220px;
  overflow: auto;
}

.chat-group-member-row,
.chat-group-add-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.chat-group-member-row {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(72, 103, 183, 0.05);
}

.chat-group-member-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.chat-group-add {
  display: grid;
  gap: 8px;
  max-height: 220px;
  overflow: auto;
}

.chat-group-add-item {
  width: 100%;
  border: 1px dashed rgba(52, 144, 139, 0.22);
  border-radius: 12px;
  background: rgba(52, 144, 139, 0.04);
  padding: 10px 12px;
  cursor: pointer;
  text-align: right;
}

.chat-group-add-item:hover {
  background: rgba(52, 144, 139, 0.08);
}

.chat-group-empty-add {
  padding: 12px;
  border-radius: 12px;
  background: rgba(72, 103, 183, 0.05);
  color: #667085;
  font-size: 12px;
  text-align: center;
}

.chat-member-remove,
.chat-panel-close {
  border: 0;
  background: transparent;
  color: #b42318;
  cursor: pointer;
  font: inherit;
}

.chat-panel-close {
  color: #5f7a76;
  font-size: 24px;
  line-height: 1;
}

.chat-sender-name {
  display: block;
  margin-bottom: 2px;
  color: #2d7a6e;
  font-size: 11px;
  font-weight: 800;
}

.chat-thread-head {
  justify-content: flex-start;
  border-bottom: 1px solid rgba(52, 144, 139, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.72));
  padding-top: 14px;
}

.chat-thread-head-accent {
  position: absolute;
  inset-inline: 18px;
  top: 0;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(52, 144, 139, 0.15), #34908b 42%, #4867b7 100%);
}

.chat-thread-head > div {
  display: grid;
  gap: 2px;
}

.chat-back-btn {
  display: none;
  align-items: center;
  gap: 4px;
  border: 0;
  background: transparent;
  color: #2d7a6e;
  cursor: pointer;
  padding: 6px 8px 6px 0;
  font: inherit;
  font-size: 0.88rem;
  font-weight: 700;
}

.chat-back-label {
  line-height: 1;
}

.chat-messages {
  min-height: 0;
  overflow: auto;
  padding: 16px 14px;
  background:
    radial-gradient(circle at 20% 10%, rgba(72, 103, 183, 0.06), transparent 28%),
    radial-gradient(circle at 80% 90%, rgba(52, 144, 139, 0.08), transparent 32%),
    linear-gradient(180deg, rgba(248, 252, 251, 0.65), rgba(255, 255, 255, 0.35));
}

.chat-messages-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
}

.chat-bubble {
  max-width: min(78%, 420px);
  padding: 10px 14px;
  border-radius: 18px;
  display: grid;
  gap: 6px;
  box-shadow: 0 8px 22px rgba(31, 92, 89, 0.08);
}

.chat-message-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  max-width: 100%;
}

.chat-message-row.is-mine {
  align-self: flex-start;
  justify-content: flex-start;
}

.chat-message-row.is-peer {
  align-self: flex-end;
  justify-content: flex-end;
  flex-direction: row-reverse;
}

.chat-bubble-avatar {
  margin-bottom: 2px;
}

.chat-bubble p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.7;
}

.chat-bubble-meta {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
}

.chat-bubble small {
  font-size: 11px;
}

.chat-ticks {
  font-size: 11px;
  line-height: 1;
  letter-spacing: -1px;
  font-weight: 700;
}

.chat-bubble.is-mine {
  align-self: flex-start;
  background: linear-gradient(145deg, #34908b, #2d7a6e);
  color: #fff;
  border-bottom-right-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.chat-bubble.is-mine,
.chat-bubble.is-mine *,
.chat-bubble.is-mine p,
.chat-bubble.is-mine small,
.chat-bubble.is-mine .chat-ticks,
.chat-bubble.is-mine .chat-bubble-meta,
.chat-bubble.is-mine .chat-bubble-meta small {
  color: #ffffff !important;
}

.chat-bubble.is-mine .chat-ticks.is-read {
  color: #e8fff8 !important;
  opacity: 1;
}

.chat-bubble.is-peer {
  align-self: flex-end;
  background: rgba(255, 255, 255, 0.94);
  color: #1d3f3b;
  border: 1px solid rgba(52, 144, 139, 0.16);
  border-bottom-left-radius: 6px;
}

.chat-bubble.is-peer small {
  color: #6a8581;
}

.chat-bubble.is-peer .chat-bubble-meta {
  justify-content: flex-end;
}

.chat-composer {
  display: block;
  padding: 10px 12px 12px;
  border-top: 1px solid rgba(52, 144, 139, 0.1);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.94));
  box-sizing: border-box;
}

.chat-composer-shell {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 6px 8px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow:
    0 10px 28px rgba(31, 92, 89, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.chat-file-input {
  display: none;
}

.chat-attach-btn {
  width: 36px;
  height: 36px;
  min-width: 36px;
  min-height: 36px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 12px;
  background: rgba(52, 144, 139, 0.1);
  color: #1f5c59;
  padding: 0;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
}

.chat-attach-btn :deep(.iconly-shell) {
  font-size: 15px;
}

.chat-composer-main {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.chat-pending-file {
  display: none;
}

.chat-composer:has(.chat-pending-file) {
  height: auto;
}

.chat-composer:has(.chat-pending-file) .chat-composer-shell {
  align-items: stretch;
}

.chat-composer:has(.chat-pending-file) .chat-pending-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 10px;
  background: rgba(52, 144, 139, 0.1);
  font-size: 11px;
  color: #2d7a6e;
}

.chat-pending-file button {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}

.chat-attach-image {
  display: block;
  overflow: hidden;
  border-radius: 12px;
}

.chat-attach-image img {
  display: block;
  max-width: 220px;
  max-height: 180px;
  object-fit: cover;
}

.chat-attach-file {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.16);
  color: inherit;
  text-decoration: none;
  font-size: 0.86rem;
}

.chat-bubble.is-peer .chat-attach-file {
  background: rgba(52, 144, 139, 0.08);
}

.chat-composer input {
  width: 100%;
  min-height: 36px;
  height: 36px;
  max-height: 36px;
  border: 1px solid rgba(52, 144, 139, 0.12);
  border-radius: 12px;
  padding: 0 12px;
  font: inherit;
  font-size: 0.88rem;
  background: rgba(248, 252, 251, 0.9);
  color: #1d3f3b;
  box-sizing: border-box;
}

.chat-send-btn {
  min-height: 36px;
  height: 36px;
  padding: 0 14px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #34908b, #2d7a6e);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(45, 122, 110, 0.24);
}

.chat-send-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.chat-send-btn :deep(.iconly-shell) {
  font-size: 15px;
}

.chat-send-label {
  display: none;
}

.inline-error {
  margin: 0 16px 8px;
  color: #b42318;
  font-size: 13px;
}

@media (max-width: 920px) {
  .chat-page-luxe {
    grid-template-columns: 1fr;
    height: calc(100dvh - 56px - 76px - env(safe-area-inset-bottom, 0px));
    max-height: calc(100dvh - 56px - 76px - env(safe-area-inset-bottom, 0px));
    min-height: 0;
    border-radius: 0;
    border: 0;
    box-shadow: none;
  }

  .chat-page-luxe::before {
    display: none;
  }

  .chat-thread-frame {
    margin: 0;
    border: 0;
    border-radius: 0;
    box-shadow: none;
    background: transparent;
  }

  .chat-page-luxe.show-thread .chat-composer {
    position: fixed;
    inset-inline: 10px;
    bottom: calc(102px + env(safe-area-inset-bottom, 0px));
    z-index: 60;
    border-top: 0;
    border-radius: 16px;
    border: 1px solid rgba(52, 144, 139, 0.14);
    box-shadow: 0 10px 28px rgba(31, 92, 89, 0.12);
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
  }

  .chat-page-luxe.show-thread .chat-messages {
    padding-bottom: calc(140px + env(safe-area-inset-bottom, 0px));
  }

  .chat-page-luxe.show-thread .chat-sidebar {
    display: none;
  }

  .chat-page-luxe:not(.show-thread) .chat-thread {
    display: none;
  }

  .chat-page-luxe.show-thread .chat-thread {
    display: grid;
  }

  .chat-page-luxe:not(.show-thread) .chat-sidebar {
    display: flex;
    flex-direction: column;
  }

  .chat-back-btn {
    display: inline-flex;
  }
}
</style>

<style>
#app .app-shell:not(.is-auth-route) .chat-page .chat-search-box,
#app .app-shell:not(.is-auth-route) .chat-page .chat-group-search {
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
  min-height: 32px !important;
  max-height: 32px !important;
  height: 32px !important;
  padding: 0 8px !important;
  margin: 0 !important;
  border: 1px solid rgba(52, 144, 139, 0.18) !important;
  border-radius: 10px !important;
  background: #fff !important;
  box-shadow: none !important;
  overflow: hidden !important;
}

#app .app-shell:not(.is-auth-route) .chat-page .chat-search-box input,
#app .app-shell:not(.is-auth-route) .chat-page .chat-group-search input {
  flex: 1 1 auto !important;
  width: 100% !important;
  min-width: 0 !important;
  min-height: 0 !important;
  max-height: none !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  font-size: 0.82rem !important;
  line-height: 1.2 !important;
  appearance: none !important;
  -webkit-appearance: none !important;
}

#app .app-shell:not(.is-auth-route) .chat-page .chat-search-box input:focus,
#app .app-shell:not(.is-auth-route) .chat-page .chat-group-search input:focus {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  outline: none !important;
}

#app .app-shell:not(.is-auth-route) .chat-page .chat-group-search .iconly-shell,
#app .app-shell:not(.is-auth-route) .chat-page .chat-search-box .iconly-shell {
  width: 16px !important;
  height: 16px !important;
  min-height: 0 !important;
  font-size: 14px !important;
  line-height: 1 !important;
}

#app .app-shell:not(.is-auth-route) .chat-page .chat-group-field.chat-search-field {
  gap: 4px !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

#app .app-shell:not(.is-auth-route) .chat-page .chat-group-input {
  min-height: 0 !important;
  height: 40px !important;
  padding-inline: 12px !important;
  border: 1px solid rgba(52, 144, 139, 0.18) !important;
  background: #fff !important;
  box-shadow: none !important;
}
</style>
