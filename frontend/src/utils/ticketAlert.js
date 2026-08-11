import { notifyInfo } from './notify'

export const HQ_ALERT_SOUND_URL = encodeURI(
  '/ElevenLabs_Soft_chime_new_message_notification,_single_bright_tone.mp3',
)
export const ORG_ALERT_SOUND_URL = '/notif.mp3'

/** @deprecated use HQ_ALERT_SOUND_URL */
export const TICKET_ALERT_SOUND_URL = HQ_ALERT_SOUND_URL

let hqAlertAudio = null
let orgAlertAudio = null
let audioUnlocked = false
let browserPermissionRequested = false

const canUseNotifications = () => typeof window !== 'undefined' && 'Notification' in window

function ensureAudio(kind = 'hq') {
  if (typeof window === 'undefined') return null
  if (kind === 'org') {
    if (!orgAlertAudio) {
      orgAlertAudio = new Audio(ORG_ALERT_SOUND_URL)
      orgAlertAudio.preload = 'auto'
      orgAlertAudio.volume = 0.9
    }
    return orgAlertAudio
  }
  if (!hqAlertAudio) {
    hqAlertAudio = new Audio(HQ_ALERT_SOUND_URL)
    hqAlertAudio.preload = 'auto'
    hqAlertAudio.volume = 0.9
  }
  return hqAlertAudio
}

function unlockOne(audio) {
  if (!audio || audioUnlocked) return
  try {
    audio.muted = true
    const playPromise = audio.play()
    if (playPromise?.then) {
      playPromise
        .then(() => {
          audio.pause()
          audio.currentTime = 0
          audio.muted = false
          audioUnlocked = true
        })
        .catch(() => {
          audio.muted = false
        })
    } else {
      audio.muted = false
      audioUnlocked = true
    }
  } catch (_error) {
    // Autoplay policies can block until a real user gesture.
  }
}

export const unlockTicketAlertAudio = () => {
  if (typeof window === 'undefined' || audioUnlocked) return
  unlockOne(ensureAudio('hq'))
  unlockOne(ensureAudio('org'))
}

export const ensureTicketBrowserPermission = async () => {
  if (!canUseNotifications() || browserPermissionRequested) return Notification.permission
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
  ensureTicketBrowserPermission()
}

function playAudio(kind = 'hq') {
  if (typeof window === 'undefined') return
  try {
    const audio = ensureAudio(kind)
    if (!audio) return
    audio.muted = false
    audio.volume = 0.9
    audio.currentTime = 0
    const playPromise = audio.play()
    if (playPromise?.then) {
      playPromise
        .then(() => {
          audioUnlocked = true
        })
        .catch(() => {})
    } else {
      audioUnlocked = true
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

const showBrowserNotification = ({ title, body, tag }) => {
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
  notifyInfo(message, { title, duration: 7000, source: 'chat' })

  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
    showBrowserNotification({
      title: `کارنومند | ${title}`,
      body: message,
      tag: 'workflow-chat-unread',
    })
  }
}
