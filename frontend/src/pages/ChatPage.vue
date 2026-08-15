<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
const POLL_MS = 6000

const { state, loadChatUnreadConversations } = useWorkflowHub()

const conversations = ref([])
const users = ref([])
const messages = ref([])
const selectedId = ref(null)
const listSearch = ref('')
const composer = ref('')
const pendingFile = ref(null)
const fileInputRef = ref(null)
const loadingList = ref(false)
const loadingThread = ref(false)
const sending = ref(false)
const showNewChat = ref(false)
const lastError = ref('')
const threadRef = ref(null)
const mobileShowThread = ref(false)

let pollTimer = null
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

const filteredConversations = computed(() => {
  const q = listSearch.value.trim().toLowerCase()
  if (!q) return conversations.value
  return conversations.value.filter((item) => {
    const name = String(item.peer?.name || item.peer?.fullName || '').toLowerCase()
    const preview = String(item.lastMessage?.body || '').toLowerCase()
    return name.includes(q) || preview.includes(q)
  })
})

const filteredUsers = computed(() => {
  const q = listSearch.value.trim().toLowerCase()
  const existingPeerIds = new Set(
    conversations.value.map((item) => Number(item.peer?.id)).filter(Boolean),
  )
  return users.value.filter((user) => {
    if (existingPeerIds.has(Number(user.id))) return true
    if (!q) return true
    const hay = `${user.name || ''} ${user.role || ''} ${user.department || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('fa-IR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
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
  await loadMessages(conversationId)
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
  if (pollInFlight || sending.value) return
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
    }
  } catch {
    // keep UI
  } finally {
    pollInFlight = false
  }
}

function backToList() {
  mobileShowThread.value = false
  showNewChat.value = false
  composer.value = ''
  clearPendingFile()
}

watch(showNewChat, async (open) => {
  if (open) await loadUsers()
})

onMounted(async () => {
  await loadConversations()
  await loadUsers()
  pollTimer = window.setInterval(refreshQuietly, POLL_MS)
})

onBeforeUnmount(() => {
  if (pollTimer) window.clearInterval(pollTimer)
})
</script>

<template>
  <div class="page-shell chat-page" :class="{ 'show-thread': mobileShowThread && selectedConversation }">
    <aside class="chat-sidebar">
      <header class="chat-sidebar-head">
        <div>
          <p class="page-eyebrow">گفتگوی سازمانی</p>
          <h2>پیام‌ها</h2>
        </div>
        <button class="action-btn tone-primary chat-new-btn" type="button" @click="showNewChat = !showNewChat">
          <IconlyIcon name="chat" decorative />
          <span>{{ showNewChat ? 'بازگشت' : 'چت جدید' }}</span>
        </button>
      </header>

      <label class="search-shell chat-search">
        <IconlyIcon name="search" decorative />
        <input v-model="listSearch" :placeholder="showNewChat ? 'جستجوی کاربر...' : 'جستجوی گفتگو...'" />
      </label>

      <p v-if="lastError" class="inline-error">{{ lastError }}</p>

      <div v-if="showNewChat" class="chat-list">
        <button
          v-for="user in filteredUsers"
          :key="user.id"
          class="chat-list-item"
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

      <div v-else class="chat-list">
        <div v-if="loadingList && !conversations.length" class="chat-empty">در حال بارگذاری...</div>
        <button
          v-for="item in filteredConversations"
          :key="item.id"
          :class="['chat-list-item', selectedId === item.id && 'is-active']"
          type="button"
          @click="openConversation(item.id)"
        >
          <UserAvatar
            :person="item.peer"
            :name="item.peer?.name || 'همکار'"
            size="md"
          />
          <div class="chat-list-copy">
            <div class="chat-list-top">
              <strong>{{ item.peer?.name || 'همکار' }}</strong>
              <small>{{ formatTime(item.lastMessage?.createdAt || item.updatedAt) }}</small>
            </div>
            <p>{{ item.lastMessage?.body || item.lastPreview || (item.lastMessage?.attachment ? 'پیوست' : 'گفتگو را شروع کنید') }}</p>
          </div>
          <span v-if="item.unreadCount" class="chat-unread">{{ item.unreadCount }}</span>
        </button>
        <div v-if="!loadingList && !filteredConversations.length" class="chat-empty">
          هنوز گفتگویی ندارید. با «چت جدید» شروع کنید.
        </div>
      </div>
    </aside>

    <section class="chat-thread">
      <template v-if="selectedConversation">
        <header class="chat-thread-head">
          <button class="chat-back-btn" type="button" aria-label="بازگشت به فهرست" @click="backToList">
            <IconlyIcon name="arrow_back" decorative />
            <span class="chat-back-label">بازگشت</span>
          </button>
          <UserAvatar
            :person="selectedConversation.peer"
            :name="selectedConversation.peer?.name || 'همکار'"
            size="md"
          />
          <div>
            <strong>{{ selectedConversation.peer?.name || 'همکار' }}</strong>
            <small>{{ selectedConversation.peer?.role || selectedConversation.peer?.department || '' }}</small>
          </div>
        </header>

        <div ref="threadRef" class="chat-messages">
          <div v-if="loadingThread && !messages.length" class="chat-empty">در حال بارگذاری پیام‌ها...</div>
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['chat-message-row', message.mine ? 'is-mine' : 'is-peer']"
          >
            <UserAvatar
              v-if="!message.mine"
              class="chat-bubble-avatar"
              :person="selectedConversation?.peer"
              :name="selectedConversation?.peer?.name || 'همکار'"
              size="sm"
            />
            <article :class="['chat-bubble', message.mine ? 'is-mine' : 'is-peer']">
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

        <form class="chat-composer" @submit.prevent="sendMessage">
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
        </form>
      </template>

      <div v-else class="chat-thread-empty">
        <IconlyIcon name="forum" decorative />
        <h3>یک گفتگو انتخاب کنید</h3>
        <p>از فهرست سمت راست گفتگو را باز کنید یا چت جدید بسازید.</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.chat-page {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 0;
  min-height: 0;
  height: calc(100dvh - 140px);
  max-height: calc(100dvh - 140px);
  border: 1px solid rgba(52, 144, 139, 0.14);
  border-radius: 18px;
  overflow: hidden;
  background: #f7fbfa;
}

.chat-sidebar,
.chat-thread {
  display: grid;
  min-height: 0;
}

.chat-sidebar {
  grid-template-rows: auto auto auto minmax(0, 1fr);
  border-left: 1px solid rgba(52, 144, 139, 0.12);
  background: rgba(255, 255, 255, 0.72);
}

.chat-sidebar-head,
.chat-thread-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 18px 10px;
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
}

.chat-search {
  margin: 0 16px 12px;
}

.chat-list {
  grid-row: 4;
  min-height: 0;
  overflow: auto;
  padding: 0 10px 16px;
  display: grid;
  gap: 6px;
  align-content: start;
}

.chat-list-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 12px;
  border: 0;
  border-radius: 16px;
  background: transparent;
  text-align: right;
  cursor: pointer;
  color: inherit;
}

.chat-list-item:hover,
.chat-list-item.is-active {
  background: rgba(45, 122, 110, 0.1);
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
.chat-list-copy p {
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
  background: #2d7a6e;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
}

.chat-empty,
.chat-thread-empty {
  padding: 28px 18px;
  text-align: center;
  color: #5f7a76;
}

.chat-thread {
  grid-template-rows: auto minmax(0, 1fr) auto;
  background: transparent;
}

.chat-thread-head {
  justify-content: flex-start;
  border-bottom: 1px solid rgba(52, 144, 139, 0.1);
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
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-bubble {
  max-width: min(78%, 420px);
  padding: 8px 12px;
  border-radius: 16px;
  display: grid;
  gap: 4px;
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
  background: #2d7a6e;
  color: #fff;
  border-bottom-right-radius: 6px;
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
  background: #fff;
  color: #1d3f3b;
  border: 1px solid rgba(52, 144, 139, 0.12);
  border-bottom-left-radius: 6px;
}

.chat-bubble.is-peer small {
  color: #6a8581;
}

.chat-bubble.is-peer .chat-bubble-meta {
  justify-content: flex-end;
}

.chat-composer {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  min-height: 40px;
  height: 40px;
  max-height: 40px;
  border-top: 1px solid rgba(52, 144, 139, 0.1);
  background: rgba(255, 255, 255, 0.96);
  box-sizing: border-box;
}

.chat-file-input {
  display: none;
}

.chat-attach-btn {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  border: 0;
  border-radius: 10px;
  background: rgba(52, 144, 139, 0.12);
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
  max-height: none;
  padding-block: 6px;
}

.chat-composer:has(.chat-pending-file) .chat-pending-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 2px 6px;
  border-radius: 6px;
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
  min-height: 32px;
  height: 32px;
  max-height: 32px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  border-radius: 10px;
  padding: 0 10px;
  font: inherit;
  font-size: 0.84rem;
  background: #fff;
  color: #1d3f3b;
  box-sizing: border-box;
}

.chat-send-btn {
  min-height: 32px;
  height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: 10px;
  background: #34908b;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
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
  .chat-page {
    grid-template-columns: 1fr;
    height: calc(100dvh - 56px - 76px - env(safe-area-inset-bottom, 0px));
    max-height: calc(100dvh - 56px - 76px - env(safe-area-inset-bottom, 0px));
    min-height: 0;
    border-radius: 0;
    border: 0;
  }

  .chat-page.show-thread .chat-composer {
    position: fixed;
    inset-inline: 0;
    bottom: calc(64px + env(safe-area-inset-bottom, 0px));
    z-index: 56;
    border-top: 1px solid rgba(52, 144, 139, 0.14);
    box-shadow: 0 -8px 24px rgba(31, 92, 89, 0.08);
  }

  .chat-page.show-thread .chat-messages {
    padding-bottom: calc(56px + env(safe-area-inset-bottom, 0px));
  }

  .chat-page.show-thread .chat-sidebar {
    display: none;
  }

  .chat-page:not(.show-thread) .chat-thread {
    display: none;
  }

  .chat-page.show-thread .chat-thread {
    display: grid;
    grid-template-rows: auto minmax(0, 1fr) auto;
  }

  .chat-page:not(.show-thread) .chat-sidebar {
    display: grid;
    grid-template-rows: auto auto auto minmax(0, 1fr);
  }

  .chat-back-btn {
    display: inline-flex;
  }
}
</style>
