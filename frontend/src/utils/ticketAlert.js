import { notifyInfo } from './notify'

export const HQ_ALERT_SOUND_URL = encodeURI(
  '/ElevenLabs_Soft_chime_new_message_notification,_single_bright_tone.mp3',
)
export const ORG_ALERT_SOUND_URL = '/notif.mp3'

/** @deprecated use HQ_ALERT_SOUND_URL */
export const TICKET_ALERT_SOUND_URL = HQ_ALERT_SOUND_URL

const audioByKind = {
  hq: null,
  org: null,
}
const unlockedByKind = {
  hq: false,
  org: false,
}
let browserPermissionRequested = false

const canUseNotifications = () => typeof window !== 'undefined' && 'Notification' in window

function ensureAudio(kind = 'hq') {
  if (typeof window === 'undefined') return null
  const key = kind === 'org' ? 'org' : 'hq'
  if (!audioByKind[key]) {
    const audio = new Audio(key === 'org' ? ORG_ALERT_SOUND_URL : HQ_ALERT_SOUND_URL)
    audio.preload = 'auto'
    audio.volume = 0.95
    audioByKind[key] = audio
  }
  return audioByKind[key]
}

function unlockOne(kind = 'hq') {
  if (typeof window === 'undefined') return
  const key = kind === 'org' ? 'org' : 'hq'
  if (unlockedByKind[key]) return
  const audio = ensureAudio(key)
  if (!audio) return
  try {
    audio.muted = true
    const playPromise = audio.play()
    if (playPromise?.then) {
      playPromise
        .then(() => {
          audio.pause()
          audio.currentTime = 0
          audio.muted = false
          unlockedByKind[key] = true
        })
        .catch(() => {
          audio.muted = false
        })
    } else {
      audio.muted = false
      unlockedByKind[key] = true
    }
  } catch (_error) {
    // Autoplay policies can block until a real user gesture.
  }
}

export const unlockTicketAlertAudio = () => {
  if (typeof window === 'undefined') return
  unlockOne('hq')
  unlockOne('org')
}

export const ensureTicketBrowserPermission = async () => {
  if (!canUseNotifications() || browserPermissionRequested) {
    return canUseNotifications() ? Notification.permission : 'denied'
  }
  browserPermissionRequested = true
  if (Notification.permission === 'default') {
    try {
      await Notification.requestPermission()
    } catch (_error) {
      // Ignore permission errors; in-app toast + sound still work.
    }
  }
  return Notification.permission
}

export const unlockTicketAlerts = () => {
  unlockTicketAlertAudio()
  void ensureTicketBrowserPermission()
}

function playAudio(kind = 'hq') {
  if (typeof window === 'undefined') return
  const key = kind === 'org' ? 'org' : 'hq'
  try {
    // Prefer a fresh instance so rapid consecutive alerts are not dropped.
    const base = ensureAudio(key)
    if (!base) return
    const audio = base.cloneNode?.(true) || base
    audio.muted = false
    audio.volume = 0.95
    audio.currentTime = 0
    const playPromise = audio.play()
    if (playPromise?.then) {
      playPromise
        .then(() => {
          unlockedByKind[key] = true
        })
        .catch(() => {
          // Fallback: retry original element after unlock attempt.
          unlockOne(key)
          base.muted = false
          base.currentTime = 0
          void base.play().then(() => {
            unlockedByKind[key] = true
          }).catch(() => {})
        })
    } else {
      unlockedByKind[key] = true
    }
  } catch (_error) {
    // Browser autoplay policies can still block in some cases.
  }
}

export const playTicketAlertSound = () => playAudio('hq')
export const playOrgAlertSound = () => playAudio('org')

export const playInboxAlertSound = ({ isHq = false } = {}) => {
  if (isHq) playTicketAlertSound()
  else playOrgAlertSound()
}

export const showBrowserNotification = ({ title, body, tag }) => {
  if (!canUseNotifications() || Notification.permission !== 'granted') return
  try {
    const notification = new Notification(title, {
      body,
      tag,
      renotify: true,
      silent: false,
      dir: 'rtl',
      lang: 'fa',
    })
    notification.onclick = () => {
      window.focus?.()
      notification.close()
    }
  } catch (_error) {
    // Some browsers block Notification construction outside secure contexts.
  }
}

export const notifyNewSupportTickets = (tickets = []) => {
  const items = (Array.isArray(tickets) ? tickets : []).filter((item) => item && item.id)
  if (!items.length) return

  playTicketAlertSound()

  const first = items[0]
  const count = items.length
  const title = count === 1 ? 'تیکت جدید' : `${count} تیکت جدید`
  const org = first.organization ? ` — ${first.organization}` : ''
  const message = count === 1
    ? `#${first.id} ${first.subject || 'درخواست جدید'}${org}`
    : `آخرین مورد: #${first.id} ${first.subject || 'درخواست جدید'}${org}`

  notifyInfo(message, { title, duration: 7000 })

  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
    showBrowserNotification({
      title: `کارنومند | ${title}`,
      body: message,
      tag: `hq-ticket-${first.id}`,
    })
  }
}

export const notifyNewChatMessages = (count = 1) => {
  const normalizedCount = Math.max(1, Number(count || 1))
  const title = normalizedCount === 1 ? 'پیام جدید' : `${normalizedCount.toLocaleString('fa-IR')} پیام جدید`
  const message = normalizedCount === 1
    ? 'یک پیام خوانده‌نشده در چت سازمانی دارید'
    : `${normalizedCount.toLocaleString('fa-IR')} گفتگوی خوانده‌نشده در چت سازمانی دارید`

  playOrgAlertSound()
  notifyInfo(message, { title, duration: 7000, route: 'chat' })

  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
    showBrowserNotification({
      title: `کارنومند | ${title}`,
      body: message,
      tag: 'workflow-chat-unread',
    })
  }
}

export const notifyInboxGrowth = ({ title, message, isHq = false, tag = 'workflow-inbox' } = {}) => {
  if (!message) return
  playInboxAlertSound({ isHq })
  notifyInfo(message, { title: title || 'اعلان جدید', duration: 6500 })
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
    showBrowserNotification({
      title: `کارنومند | ${title || 'اعلان جدید'}`,
      body: message,
      tag,
    })
  }
}

export const notifyNewExpenses = (expenses = []) => {
  const items = (Array.isArray(expenses) ? expenses : []).filter((item) => item && item.id)
  if (!items.length) return

  playOrgAlertSound()

  const first = items[0]
  const count = items.length
  const title = count === 1 ? 'هزینه جدید' : `${count.toLocaleString('fa-IR')} هزینه جدید`
  const message = count === 1
    ? `${first.title || first.description || 'هزینه جدید'} — ${first.owner || ''}`.trim()
    : `آخرین مورد: ${first.title || first.description || 'هزینه جدید'} — ${first.owner || ''}`.trim()

  notifyInfo(message, { title, duration: 7000, route: 'expenses' })

  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
    showBrowserNotification({
      title: `کارنومند | ${title}`,
      body: message,
      tag: `workflow-expense-${first.id}`,
    })
  }
}
