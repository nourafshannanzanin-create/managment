import { computed, markRaw, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { formatAmountInput, normalizeAmountValue } from '../utils/amount'
import { AppError, appErrorFromResponse, createValidationError, hasFieldError, normalizeError } from '../utils/errors'
import { formatJalali, getTodayJalali, isoToJalali, jalaliToIso } from '../utils/jalali'
import { notifyNewChatMessages, notifyNewExpenses, notifyNewSupportTickets, notifyInboxGrowth, playInboxAlertSound, playTicketAlertSound } from '../utils/ticketAlert'
import { notifyInfo, notifySuccess, notifyWarning } from '../utils/notify'
import { repairPayload } from '../utils/stitch'
import { cleanDisplayText } from '../utils/text'
import { prepareUploadFile, UPLOAD_LIMITS, validateUploadFile } from '../utils/uploads'

import { personAvatarUrl, resolveAvatarUrl, resolveApiOrigin } from '../utils/avatar'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const API_ORIGIN = (() => {
  const base = String(API_BASE_URL || '').trim()
  if (!base || base.startsWith('/')) return ''
  try {
    return new URL(base).origin
  } catch {
    return base.replace(/\/api\/v1\/?$/, '')
  }
})()
const TOKEN_KEY = 'workflow-hub-token'
const SUPPORT_SEEN_KEY = 'workflow-hub-support-seen'

function createCurrentUser() {
  return {
    id: null,
    slug: '',
    username: '',
    name: '',
    role: '',
    accessRole: '',
    department: '',
    avatar: '',
    avatarUrl: '',
    avatarFileName: '',
    email: '',
    organization: '',
    bonusAmount: '0',
    bonusAmountRaw: 0,
    penaltyAmount: '0',
    penaltyAmountRaw: 0,
    netAdjustment: '0',
    netAdjustmentRaw: 0,
    canManageUsers: false,
    canAccessUsers: false,
    canAccessExpenses: false,
    canAccessSettings: false,
    canViewReports: false,
    canAccessApprovals: false,
    canApproveDocuments: false,
    isManager: false,
    isHq: false,
    isHqAdmin: false,
    platformRole: '',
    canUseHq: false,
    purchasedMenuAccess: [],
    menuAccess: {},
    attendanceToken: '',
    attendancePath: '',
    licenseStatus: {
      isLocked: false,
      is_locked: false,
      reason: '',
      notice: '',
      amountDue: '0',
      amount_due: '0',
      trialActive: false,
      trial_active: false,
      trialEndsAt: '',
      trial_ends_at: '',
      trialRemainingSeconds: 0,
      trial_remaining_seconds: 0,
      trialHours: 24,
      trial_hours: 24,
    },
  }
}

function createRequestForm() {
  return {
    title: '',
    description: '',
    department: '',
    manager: '',
    managerAssigneeIds: [],
    employeeAssigneeIds: [],
    priority: 'medium',
    requestType: 'general',
    leaveStartDate: formatJalali(getTodayJalali()),
    leaveEndDate: formatJalali(getTodayJalali()),
    leaveStartTime: '09:00',
    leaveEndTime: '13:00',
    deadline: formatJalali(getTodayJalali()),
    attachments: [],
  }
}

function createExpenseForm() {
  return {
    description: '',
    amount: '0',
    expenseDate: formatJalali(getTodayJalali()),
    department: '',
    managerAssigneeIds: [],
    employeeAssigneeIds: [],
    invoice: null,
  }
}

function createUserForm() {
  return {
    fullName: '',
    username: '',
    password: '',
    phone: '',
    accessRole: 'employee',
    department: '',
    managerId: '',
    jobTitle: '',
    avatarFile: null,
    avatarPreview: '',
    bonusAmount: '',
    penaltyAmount: '',
    entrustedItems: [],
    sectionAccess: {
      approvals: false,
      expenses: false,
      reports: false,
      users: false,
      settings: false,
    },
  }
}

function createDocumentForm() {
  return {
    title: '',
    description: '',
    department: '',
    assigneeIds: [],
    documentType: 'سند',
    risk: 'medium',
    file: null,
  }
}

function createSettingsState() {
  return {
    organizationName: '',
    systemId: '',
    security: {
      twoFactorRequired: true,
      recentSessionCount: 0,
      recentSessionLabel: '',
    },
    attendanceLocation: {
      configured: false,
      latitude: null,
      longitude: null,
      label: '',
      radiusMeters: 20,
      provinceId: null,
      provinceName: '',
      cityId: null,
      cityName: '',
    },
    workSchedule: {
      workDayStart: '09:00',
      workDayEnd: '17:00',
      monthlyLeaveHours: 20,
    },
    organizationGeo: {
      provinceId: null,
      provinceName: '',
      cityId: null,
      cityName: '',
    },
    sections: [],
    organizationUsers: [],
    departments: [],
    canEdit: false,
  }
}

function createWalletState() {
  return {
    loaded: false,
    loading: false,
    submitting: false,
    error: '',
    message: '',
    schematic: false,
    schematicNotice: '',
    organization: null,
    summary: {
      totalBalance: '0',
      totalBalanceRaw: 0,
      mainBalance: '0',
      mainBalanceRaw: 0,
      smsBalance: '0',
      smsBalanceRaw: 0,
      smsLowBalanceThreshold: '0',
      smsLowBalanceThresholdRaw: 0,
      smsIsLow: false,
      depositsTotal: '0',
      depositsTotalRaw: 0,
      withdrawalsTotal: '0',
      withdrawalsTotalRaw: 0,
      transactions: 0,
    },
    options: [],
    licenseStatus: {
      isLocked: false,
      is_locked: false,
      reason: '',
      notice: '',
      amountDue: '0',
      amount_due: '0',
      trialActive: false,
      trial_active: false,
      trialEndsAt: '',
      trial_ends_at: '',
      trialRemainingSeconds: 0,
      trial_remaining_seconds: 0,
      trialHours: 24,
      trial_hours: 24,
    },
    wallets: [],
    transactions: [],
  }
}

function createSupportState() {
  return {
    loaded: false,
    loading: false,
    detailLoading: false,
    submitting: false,
    seenVersion: 0,
    error: '',
    message: '',
    tickets: [],
    selectedTicket: null,
    knownTicketIds: [],
    activitySignature: '',
  }
}

function createChatState() {
  return {
    unreadConversations: 0,
    loaded: false,
  }
}

function createTaskingState() {
  return {
    loaded: false,
    loading: false,
    submitting: false,
    error: '',
    date: '',
    settings: null,
    capacity: null,
    stats: {
      todayCount: 0,
      remainingMinutes: 0,
      needsAction: 0,
      completedToday: 0,
      unreadMentions: 0,
      mineCount: 0,
      assignmentCount: 0,
      superviseCount: 0,
    },
    counts: {
      mine: {},
      assignments: {},
      supervise: {},
      mentions: 0,
      mentionsAll: 0,
    },
    badgeCount: 0,
    activeTimer: null,
    mine: {
      today: [],
      upcoming: [],
      inProgress: [],
      pendingReview: [],
      changesRequested: [],
      closed: [],
      all: [],
    },
    assignments: {
      pending: [],
      outbound: [],
      outboundReview: [],
      outboundActive: [],
      accepted: [],
      rejected: [],
      all: [],
    },
    supervise: {
      pendingReview: [],
      inProgress: [],
      overdue: [],
      completed: [],
      all: [],
      summary: {
        pendingReview: 0,
        inProgress: 0,
        overdue: 0,
        changesRequested: 0,
      },
    },
    mentions: {
      unread: [],
      all: [],
    },
    departments: [],
    assigneeOptions: [],
    superviseFocus: null,
    selectedTask: null,
    detailLoading: false,
    schedulePreview: null,
    reports: null,
    reportsLoading: false,
  }
}

function getSupportSeenStorageKey() {
  const userId = state.currentUser.id || 'guest'
  const organization = state.currentUser.organization || 'global'
  return `${SUPPORT_SEEN_KEY}:${userId}:${organization}`
}

function readSupportSeenMap() {
  try {
    return JSON.parse(localStorage.getItem(getSupportSeenStorageKey()) || '{}')
  } catch {
    return {}
  }
}

function writeSupportSeenMap(payload) {
  localStorage.setItem(getSupportSeenStorageKey(), JSON.stringify(payload))
}

const state = reactive({
  authToken: localStorage.getItem(TOKEN_KEY) || '',
  sessionReady: false,
  bootstrapLoaded: false,
  liveSync: {
    initialized: false,
    inFlight: false,
    lastSnapshot: null,
    tick: 0,
    knownExpenseInboxIds: [],
  },
  appLoading: false,
  lastError: '',
  lastErrorDetails: null,
  loginPending: false,
  mobileMenuOpen: false,
  currentUser: createCurrentUser(),
  stats: [],
  chartData: [],
  pipeline: [],
  requests: [],
  approvals: [],
  expenses: [],
  users: [],
  reports: [],
  reportSummary: null,
  reportStatus: {},
  topSubmitters: [],
  activities: [],
  insights: [],
  expenseSummary: [],
  approvalMetrics: { pending: 0, approved: 0, rejected: 0 },
  settings: createSettingsState(),
  hq: createHqState(),
  wallet: createWalletState(),
  support: createSupportState(),
  chat: createChatState(),
  tasking: createTaskingState(),
  settingsCards: [],
  directories: {
    departments: [],
    managers: [],
    users: [],
  },
  requestForm: createRequestForm(),
  expenseForm: createExpenseForm(),
  userForm: createUserForm(),
  documentForm: createDocumentForm(),
  requestSubmitting: false,
  expenseSubmitting: false,
  userSubmitting: false,
  documentSubmitting: false,
  fileUploadPreparing: false,
  filters: {
    requests: { query: '', person: '', startDate: '', endDate: '' },
    expenses: { query: '', person: '', startDate: '', endDate: '' },
    approvals: { query: '', person: '', startDate: '', endDate: '' },
    reports: { query: '', person: '', startDate: '', endDate: '' },
    users: { query: '', person: '', startDate: '', endDate: '' },
  },
})

const modalState = reactive({
  requestDetail: false,
  expenseDetail: false,
  requestComposer: false,
  expenseComposer: false,
  approvalDetail: false,
  userComposer: false,
  documentComposer: false,
  signatureComposer: false,
  taskComposer: false,
  taskDetail: false,
})

const requestDetailState = reactive({
  loading: false,
  items: {},
})

const approvalDetailState = reactive({
  loading: false,
  item: null,
})

const expenseDetailState = reactive({
  loading: false,
  item: null,
})

const signatureState = reactive({
  loading: false,
  hasSignature: false,
  signatureData: '',
  hasStamp: false,
  stampData: '',
})

const selectedState = reactive({
  requestId: '',
  expenseId: '',
  approvalId: '',
})

function resetCurrentUser() {
  Object.assign(state.currentUser, createCurrentUser())
}

function resetRequestForm() {
  Object.assign(state.requestForm, createRequestForm())
}

function resetExpenseForm() {
  Object.assign(state.expenseForm, createExpenseForm())
}

function resetUserForm() {
  if (state.userForm?.avatarPreview && String(state.userForm.avatarPreview).startsWith('blob:')) {
    URL.revokeObjectURL(state.userForm.avatarPreview)
  }
  Object.assign(state.userForm, createUserForm())
}

function resetDocumentForm() {
  Object.assign(state.documentForm, createDocumentForm())
}

function resetSettingsState() {
  Object.assign(state.settings, createSettingsState())
}

function resetHqState() {
  Object.assign(state.hq, createHqState())
}

function resetWalletState() {
  Object.assign(state.wallet, createWalletState())
}

function resetSupportState() {
  Object.assign(state.support, createSupportState())
}

function resetChatState() {
  Object.assign(state.chat, createChatState())
  Object.assign(state.tasking, createTaskingState())
}

function replaceItems(target, items) {
  target.splice(0, target.length, ...(items || []))
}

function clearLastError() {
  state.lastError = ''
  state.lastErrorDetails = null
}

function setLastError(error, fallback = 'خطا در انجام عملیات') {
  const normalized = normalizeError(error, fallback)
  state.lastError = normalized.message
  state.lastErrorDetails = normalized
  return normalized
}

function fieldHasError(field) {
  return hasFieldError(state.lastErrorDetails, field)
}

function resolveAssetUrl(rawUrl) {
  return resolveAvatarUrl(rawUrl)
}

function formatNumber(value) {
  const normalized = normalizeAmountValue(value)
  const number = Number(normalized)
  if (!Number.isFinite(number)) return String(value || '')
  return new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 0 }).format(number)
}

function formatMoneyInputValue(value) {
  return formatAmountInput(value)
}

function normalizeDisplayDate(value) {
  if (!value) return ''
  const raw = String(value).slice(0, 10)
  return /^\d{4}-\d{2}-\d{2}$/.test(raw) ? isoToJalali(raw) : value
}

function normalizeUser(item = {}) {
  return {
    ...item,
    name: cleanDisplayText(item?.name),
    username: cleanDisplayText(item?.username),
    role: cleanDisplayText(item?.role),
    department: cleanDisplayText(item?.department),
    manager: cleanDisplayText(item?.manager),
    jobTitle: cleanDisplayText(item?.jobTitle),
    phone: cleanDisplayText(item?.phone),
    status: cleanDisplayText(item?.status),
    avatar: cleanDisplayText(item?.avatar),
    avatarUrl: resolveAvatarUrl(item?.avatarUrl || item?.avatar_url || item?.avatarImage || item?.avatar_image || ''),
    avatarFileName: cleanDisplayText(item?.avatarFileName || item?.avatar_file_name),
    bonusAmount: item?.bonusAmount || '0',
    bonusAmountRaw: Number(item?.bonusAmountRaw || 0),
    penaltyAmount: item?.penaltyAmount || '0',
    penaltyAmountRaw: Number(item?.penaltyAmountRaw || 0),
    netAdjustment: item?.netAdjustment || '0',
    netAdjustmentRaw: Number(item?.netAdjustmentRaw || 0),
    financeUpdatedAt: item?.financeUpdatedAt || '',
    financeUpdatedAtIso: item?.financeUpdatedAtIso || '',
    currentPassword: String(item?.currentPassword || item?.current_password || ''),
    entrustedItems: Array.isArray(item?.entrustedItems || item?.entrusted_items)
      ? (item.entrustedItems || item.entrusted_items).map((entry) => ({
          ...entry,
          title: cleanDisplayText(entry?.title || entry?.name),
          description: cleanDisplayText(entry?.description),
          amount: entry?.amount || '0',
          amountRaw: Number(entry?.amountRaw || entry?.amount_raw || 0),
          entrustedAt: entry?.entrustedAt || entry?.entrusted_at || '',
          entrustedAtIso: entry?.entrustedAtIso || entry?.entrusted_at_iso || entry?.entrustedAt || '',
        }))
      : [],
  }
}

function storeRawFile(file) {
  return file ? markRaw(file) : null
}

function validateAttachmentList(files, { maxCount = UPLOAD_LIMITS.maxAttachments, label = 'پیوست' } = {}) {
  const items = Array.isArray(files) ? files : []
  if (items.length > maxCount) {
    throw createValidationError(`حداکثر ${maxCount} ${label} مجاز است.`, [{
      field: 'attachments',
      message: `تعداد ${label}ها بیش از حد مجاز است.`,
    }])
  }
  items.forEach((file, index) => {
    const message = validateUploadFile(file)
    if (message) {
      throw createValidationError(message, [{
        field: 'attachments',
        message: `${file?.name || `${label} ${index + 1}`}: ${message}`,
      }])
    }
  })
}

function upsertById(target, item) {
  if (!item?.id || !Array.isArray(target)) return
  const index = target.findIndex((entry) => Number(entry?.id) === Number(item.id))
  if (index >= 0) target[index] = { ...target[index], ...item }
  else target.unshift(item)
}

function removeById(target, itemId) {
  if (!itemId || !Array.isArray(target)) return
  const index = target.findIndex((entry) => Number(entry?.id) === Number(itemId))
  if (index >= 0) target.splice(index, 1)
}

function syncUserAcrossState(userPayload, options = {}) {
  const { remove = false } = options
  const userId = Number(userPayload?.id || options.userId)
  if (!userId) return

  if (remove) {
    removeById(state.users, userId)
    removeById(state.settings.organizationUsers || [], userId)
    removeById(state.directories.users || [], userId)
    removeById(state.directories.managers || [], userId)
    if (Number(state.currentUser.id) === userId) {
      Object.assign(state.currentUser, createCurrentUser())
    }
    return
  }

  const normalizedUser = normalizeUser(userPayload)
  upsertById(state.users, normalizedUser)
  upsertById(state.settings.organizationUsers || [], normalizedUser)
  upsertById(state.directories.users || [], normalizedUser)

  const managerEntry = {
    id: Number(normalizedUser.id),
    slug: normalizedUser.username,
    name: normalizedUser.name,
    role: normalizedUser.role,
    accessRole: normalizedUser.accessRole,
  }
  const isManagerRole = ['admin', 'executive_manager', 'manager'].includes(normalizedUser.accessRole)
  if (isManagerRole) upsertById(state.directories.managers || [], managerEntry)
  else removeById(state.directories.managers || [], normalizedUser.id)

  if (Number(state.currentUser.id) === Number(normalizedUser.id)) {
    Object.assign(state.currentUser, {
      username: normalizedUser.username,
      name: normalizedUser.name,
      accessRole: normalizedUser.accessRole,
      role: normalizedUser.role,
      department: normalizedUser.department,
      phone: normalizedUser.phone,
      avatar: normalizedUser.avatar,
      avatarUrl: normalizedUser.avatarUrl,
      avatarFileName: normalizedUser.avatarFileName,
      bonusAmount: normalizedUser.bonusAmount,
      bonusAmountRaw: normalizedUser.bonusAmountRaw,
      penaltyAmount: normalizedUser.penaltyAmount,
      penaltyAmountRaw: normalizedUser.penaltyAmountRaw,
      netAdjustment: normalizedUser.netAdjustment,
      netAdjustmentRaw: normalizedUser.netAdjustmentRaw,
    })
  }
}

function normalizeRequest(item) {
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    description: cleanDisplayText(item?.description),
    owner: cleanDisplayText(item?.owner),
    manager: cleanDisplayText(item?.manager),
    department: cleanDisplayText(item?.department),
    status: cleanDisplayText(item?.status),
    deadline: normalizeDisplayDate(item?.deadline),
    createdAt: normalizeDisplayDate(item?.createdAt),
    managerAssignees: (item?.managerAssignees || []).map((entry) => cleanDisplayText(entry)),
    employeeAssignees: (item?.employeeAssignees || []).map((entry) => cleanDisplayText(entry)),
    attachments: (item?.attachments || []).map((attachment) => ({
      ...attachment,
      originalName: cleanDisplayText(attachment?.originalName),
      fileUrl: resolveAssetUrl(attachment.fileUrl),
    })),
  }
}

function normalizeExpense(item) {
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    description: cleanDisplayText(item?.description),
    owner: cleanDisplayText(item?.owner),
    category: cleanDisplayText(item?.category),
    department: cleanDisplayText(item?.department),
    status: cleanDisplayText(item?.status),
    amount: formatNumber(item?.amountRaw ?? item?.amount),
    submittedAt: normalizeDisplayDate(item?.submittedAt),
    invoiceUrl: resolveAssetUrl(item?.invoiceUrl),
  }
}

function normalizeApproval(item) {
  const hqDownloadQuery = state.currentUser.isHq && state.hq.selectedOrganizationId && item?.downloadUrl
    ? `${item.downloadUrl.includes('?') ? '&' : '?'}organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    owner: cleanDisplayText(item?.owner),
    type: cleanDisplayText(item?.type),
    status: cleanDisplayText(item?.status),
    department: cleanDisplayText(item?.department),
    risk: cleanDisplayText(item?.risk),
    summary: cleanDisplayText(item?.summary),
    decisionNote: cleanDisplayText(item?.decisionNote),
    assignees: (item?.assignees || []).map((entry) => cleanDisplayText(entry)),
    uploadedAt: normalizeDisplayDate(item?.uploadedAt),
    previewUrl: resolveAssetUrl(item?.previewUrl),
    downloadUrl: resolveAssetUrl(`${item?.downloadUrl || ''}${hqDownloadQuery}`),
  }
}

function createHqState() {
  return {
    loaded: false,
    loading: false,
    saving: false,
    activeTable: 'organizations',
    activeTab: 'tickets',
    selectedOrganizationId: '',
    selectedOrganization: null,
    selectedType: '',
    selectedItem: null,
    query: '',
    summary: {},
    organizations: [],
    users: [],
    requests: [],
    payments: [],
    documents: [],
    tickets: [],
    team: [],
    audits: [],
    segments: { roles: [], payments: [], requests: [], documents: [], tickets: [] },
    directories: {
      organizations: [],
      departments: [],
      users: [],
      roles: [],
      requestStatuses: [],
      expenseStatuses: [],
      documentStatuses: [],
    },
  }
}

function normalizeReport(item) {
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    description: cleanDisplayText(item?.description),
    owner: cleanDisplayText(item?.owner),
    downloadUrl: resolveAssetUrl(item?.downloadUrl),
  }
}

function parseDownloadFilename(disposition = '') {
  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utfMatch?.[1]) {
    try {
      return decodeURIComponent(utfMatch[1])
    } catch {
      // ignore malformed header encoding
    }
  }

  const asciiMatch = disposition.match(/filename="([^"]+)"|filename=([^;]+)/i)
  return asciiMatch?.[1] || asciiMatch?.[2] || ''
}

function fallbackFilenameFromUrl(rawUrl = '', fallback = 'download') {
  try {
    const url = new URL(rawUrl, resolveApiOrigin() || API_ORIGIN || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost'))
    const fileName = decodeURIComponent(url.pathname.split('/').filter(Boolean).pop() || '')
    return fileName || fallback
  } catch {
    return fallback
  }
}

async function authorizedFetchUrl(rawUrl, options = {}) {
  const requestUrl = /^https?:\/\//i.test(rawUrl) ? rawUrl : resolveAssetUrl(rawUrl)
  const response = await fetch(requestUrl, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {}),
    },
  })

  if (response.status === 401) {
    clearSessionState()
    throw new AppError({
      status: 401,
      title: 'نشست منقضی شده است',
      message: 'برای ادامه کار دوباره وارد سامانه شوید.',
      suggestion: 'صفحه ورود را باز کنید و دوباره وارد حساب شوید.',
    })
  }

  if (!response.ok) {
    let payload = null
    try {
      payload = repairPayload(await response.json())
    } catch {
      // ignore parse failure
    }
    throw appErrorFromResponse(payload || {}, response.status)
  }

  return response
}

async function downloadProtectedFile(rawUrl, fallbackName = 'download') {
  if (!rawUrl) return
  const response = await authorizedFetchUrl(rawUrl)
  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') || ''
  const fileName = parseDownloadFilename(disposition) || fallbackFilenameFromUrl(rawUrl, fallbackName)
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 2000)
}

async function openProtectedFile(rawUrl, fallbackName = 'preview') {
  if (!rawUrl) return
  const response = await authorizedFetchUrl(rawUrl)
  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const popup = window.open(objectUrl, '_blank', 'noopener,noreferrer')

  if (!popup) {
    const link = document.createElement('a')
    link.href = objectUrl
    link.target = '_blank'
    link.rel = 'noreferrer'
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  const revokeDelay = /\.(pdf|png|jpe?g|webp|gif|bmp)$/i.test(fallbackFilenameFromUrl(rawUrl, fallbackName)) ? 60000 : 15000
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), revokeDelay)
}

async function createProtectedObjectUrl(rawUrl) {
  if (!rawUrl) return ''
  const response = await authorizedFetchUrl(rawUrl)
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}

function clearSessionState() {
  state.authToken = ''
  state.bootstrapLoaded = false
  state.sessionReady = true
  state.liveSync.initialized = false
  state.liveSync.knownExpenseInboxIds = []
  clearLastError()
  resetCurrentUser()
  replaceItems(state.stats, [])
  replaceItems(state.chartData, [])
  replaceItems(state.pipeline, [])
  replaceItems(state.requests, [])
  replaceItems(state.expenses, [])
  replaceItems(state.approvals, [])
  replaceItems(state.users, [])
  replaceItems(state.reports, [])
  replaceItems(state.activities, [])
  replaceItems(state.expenseSummary, [])
  replaceItems(state.settingsCards, [])
  resetSettingsState()
  resetHqState()
  resetWalletState()
  resetSupportState()
  resetChatState()
  state.directories.departments = []
  state.directories.managers = []
  state.directories.users = []
  state.reportSummary = null
  state.reportStatus = {}
  state.topSubmitters = []
  signatureState.hasSignature = false
  signatureState.signatureData = ''
  signatureState.hasStamp = false
  signatureState.stampData = ''
  approvalDetailState.item = null
  expenseDetailState.item = null
  selectedState.requestId = ''
  selectedState.expenseId = ''
  selectedState.approvalId = ''
  localStorage.removeItem(TOKEN_KEY)
}

function inDateRange(rawValue, startDate, endDate) {
  if (!startDate && !endDate) return true
  const value = String(rawValue || '')
  if (!value) return false
  if (startDate && value < startDate) return false
  if (endDate && value > endDate) return false
  return true
}

function matchesQuery(item, fields, query) {
  if (!query) return true
  return fields.some((field) => String(item[field] || '').toLowerCase().includes(query))
}

function matchesPerson(item, fields, person) {
  if (!person) return true
  return fields.some((field) => String(item[field] || '') === person)
}

const selectedRequest = computed(
  () => state.requests.find((item) => item.id === selectedState.requestId) ?? state.requests[0] ?? null,
)

const selectedApproval = computed(
  () => approvalDetailState.item ?? state.approvals.find((item) => item.id === selectedState.approvalId) ?? null,
)

const selectedExpense = computed(
  () => expenseDetailState.item ?? state.expenses.find((item) => item.id === selectedState.expenseId) ?? null,
)

const selectedRequestTimeline = computed(() => requestDetailState.items[selectedState.requestId]?.timeline ?? [])

const canApproveSelectedRequest = computed(() => Boolean(selectedRequest.value?.canApprove))

const canApproveSelectedExpense = computed(() => Boolean(selectedExpense.value?.canApprove))

const canManageUsers = computed(() => state.currentUser.canManageUsers)
const canAccessUsers = computed(() => state.currentUser.canAccessUsers || canManageUsers.value)
const canViewReports = computed(() => state.currentUser.canViewReports)
const canAccessApprovals = computed(() => state.currentUser.canAccessApprovals || state.currentUser.canApproveDocuments)
const canApproveDocuments = computed(() => state.currentUser.canApproveDocuments)
const isLicenseLocked = computed(() => Boolean(state.currentUser.licenseStatus?.isLocked || state.currentUser.licenseStatus?.is_locked))
const canAccessCloud = computed(() => state.currentUser.isHq || state.currentUser.menuAccess?.cloud_storage === true)

const visibleNavItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'داشبورد', icon: 'dashboard' },
    { to: '/tasking', label: 'تسکینگ', icon: 'task_alt' },
    { to: '/requests', label: 'درخواست‌ها', icon: 'assignment' },
    { to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check' },
  ]
  if (canViewReports.value) items.push({ to: '/reports', label: 'گزارشات', icon: 'monitoring' })
  if (canAccessUsers.value) items.push({ to: '/users', label: 'کاربران', icon: 'group' })

  if (state.currentUser.canAccessSettings || canManageUsers.value) {
    items.push({ to: '/settings', label: 'تنظیمات', icon: 'settings' })
  }
  return items
})

const filteredRequests = computed(() => {
  const filter = state.filters.requests
  const query = filter.query.trim().toLowerCase()
  return state.requests.filter((item) =>
    matchesQuery(item, ['title', 'owner', 'manager', 'department', 'status', 'id', 'description'], query) &&
    matchesPerson(item, ['owner', 'manager'], filter.person) &&
    inDateRange(item.deadlineIso || item.createdAtIso, filter.startDate, filter.endDate),
  )
})

const filteredExpenses = computed(() => {
  const filter = state.filters.expenses
  const query = filter.query.trim().toLowerCase()
  return state.expenses.filter((item) =>
    matchesQuery(item, ['title', 'description', 'category', 'owner', 'status', 'id', 'department'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.createdAtIso, filter.startDate, filter.endDate),
  )
})

const filteredApprovals = computed(() => {
  const filter = state.filters.approvals
  const query = filter.query.trim().toLowerCase()
  return state.approvals.filter((item) =>
    matchesQuery(item, ['title', 'type', 'owner', 'department', 'status', 'id', 'summary'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.uploadedAtIso, filter.startDate, filter.endDate),
  )
})

const approvalInbox = computed(() => filteredApprovals.value.filter((item) => item.bucket === 'pending'))
const approvalHistory = computed(() => filteredApprovals.value.filter((item) => item.bucket !== 'pending'))

const filteredReports = computed(() => {
  const filter = state.filters.reports
  const query = filter.query.trim().toLowerCase()
  return state.reports.filter((item) =>
    matchesQuery(item, ['title', 'description', 'export', 'owner'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.generatedAtIso, filter.startDate, filter.endDate),
  )
})

const filteredUsers = computed(() => {
  const filter = state.filters.users
  const query = filter.query.trim().toLowerCase()
  return state.users.filter((item) =>
    matchesQuery(item, ['name', 'username', 'role', 'department', 'manager', 'status'], query) &&
    matchesPerson(item, ['name', 'manager'], filter.person) &&
    inDateRange(item.joinedAtIso, filter.startDate, filter.endDate),
  )
})

const requestPeople = computed(() => [...new Set(state.requests.flatMap((item) => [item.owner, item.manager, ...(item.managerAssignees || [])]).filter(Boolean))])
const expensePeople = computed(() => [...new Set(state.expenses.map((item) => item.owner).filter(Boolean))])
const approvalPeople = computed(() => [...new Set(state.approvals.map((item) => item.owner).filter(Boolean))])
const reportPeople = computed(() => [...new Set(state.reports.map((item) => item.owner).filter(Boolean))])
const userPeople = computed(() => [...new Set(state.users.flatMap((item) => [item.name, item.manager]).filter(Boolean))])

function priorityLabel(value) {
  return {
    low: 'پایین',
    medium: 'متوسط',
    high: 'بالا',
    critical: 'بحرانی',
  }[value] || 'متوسط'
}

function departmentLabel(value) {
  return state.directories.departments.find((item) => item.code === value)?.name || 'بدون واحد'
}

function managerLabel(value) {
  return state.directories.managers.find((item) => item.slug === value)?.name || 'تعیین نشده'
}

function availableManagerDirectory(excludeId = null) {
  const seen = new Set()
  return [...state.directories.managers, ...state.users
    .filter((item) => ['admin', 'executive_manager', 'manager'].includes(item.accessRole))
    .map((item) => ({ id: Number(item.id), slug: item.username, name: item.name, role: item.role }))]
    .filter((item) => {
      const id = Number(item?.id)
      if (!id || (excludeId && id === Number(excludeId)) || seen.has(id)) return false
      seen.add(id)
      return true
    })
}

function availableRecipientUsers() {
  return Array.isArray(state.directories.users) && state.directories.users.length
    ? state.directories.users
    : state.users
}

const requestManagerAssigneeOptions = computed(() => {
  if (!state.requestForm.manager) return []
  return availableManagerDirectory().filter((item) => item.slug !== state.requestForm.manager)
})

function requestManagerAssigneeNames(ids = state.requestForm.managerAssigneeIds) {
  const normalizedIds = (ids || []).map((item) => Number(item))
  const names = availableManagerDirectory()
    .filter((item) => normalizedIds.includes(item.id))
    .map((item) => item.name)
  return names.length ? names.join('، ') : 'تعیین نشده'
}

function requestEmployeeAssigneeNames(ids = state.requestForm.employeeAssigneeIds) {
  const normalizedIds = (ids || []).map((item) => Number(item))
  const names = availableRecipientUsers()
    .filter((item) => item.accessRole === 'employee' && normalizedIds.includes(Number(item.id)))
    .map((item) => item.name)
  return names.length ? names.join('، ') : 'تعیین نشده'
}

function setRequestManager(value) {
  state.requestForm.manager = value
  if (!value) {
    state.requestForm.managerAssigneeIds = []
    return
  }

  const allowedIds = requestManagerAssigneeOptions.value.map((item) => item.id)
  state.requestForm.managerAssigneeIds = state.requestForm.managerAssigneeIds
    .map((item) => Number(item))
    .filter((item) => allowedIds.includes(item))
}

async function authorizedFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {}),
    },
  })

  if (response.status === 401) {
    clearSessionState()
    throw new AppError({
      status: 401,
      title: 'نشست منقضی شده است',
      message: 'برای ادامه کار دوباره وارد سامانه شوید.',
      suggestion: 'صفحه ورود را باز کنید و دوباره وارد حساب شوید.',
    })
  }

  if (!response.ok) {
    let payload = null
    try {
      payload = repairPayload(await response.json())
    } catch {
      // ignore parse failure
    }
    throw appErrorFromResponse(payload || {}, response.status)
  }

  return response
}

function hydrateBootstrap(payload) {
  if (!payload) return

  Object.assign(state.currentUser, createCurrentUser(), payload.currentUser || {})
  state.currentUser.avatarUrl = resolveAvatarUrl(state.currentUser.avatarUrl || state.currentUser.avatar_url || '')
  state.currentUser.avatarFileName = cleanDisplayText(state.currentUser.avatarFileName || state.currentUser.avatar_file_name)
  replaceItems(state.stats, payload.stats)
  replaceItems(state.chartData, payload.chartData)
  replaceItems(state.pipeline, payload.pipeline)
  replaceItems(state.requests, (payload.requests || []).map(normalizeRequest))
  replaceItems(state.expenses, (payload.expenses || []).map(normalizeExpense))
  replaceItems(state.approvals, (payload.approvals || []).map(normalizeApproval))
  replaceItems(state.users, (payload.users || []).map(normalizeUser))
  replaceItems(state.reports, (payload.reports || []).map(normalizeReport))
  replaceItems(state.activities, payload.activities)
  replaceItems(state.insights, payload.insights)
  replaceItems(state.expenseSummary, payload.expenseSummary)
  replaceItems(state.settingsCards, payload.settingsCards)
  if (payload.settings) Object.assign(state.settings, createSettingsState(), payload.settings)
  if (Array.isArray(payload.hqOrganizations)) {
    replaceItems(state.hq.directories.organizations, payload.hqOrganizations)
  }
  state.hq.selectedOrganization = payload.selectedOrganization || null
  Object.assign(state.approvalMetrics, payload.approvalMetrics || {})
  state.directories.departments = payload.directories?.departments || []
  state.directories.managers = payload.directories?.managers || []
  state.directories.users = (payload.directories?.users || []).map(normalizeUser)
  if (payload.wallet?.summary) {
    Object.assign(state.wallet.summary, payload.wallet.summary)
  }
  if (payload.wallet) {
    state.wallet.schematic = Boolean(payload.wallet.schematic)
    state.wallet.schematicNotice = payload.wallet.schematicNotice || payload.wallet.schematic_notice || ''
  }

  // Preserve open selections during soft/live refresh so drafts and modals stay stable.
  if (!selectedState.requestId || !state.requests.some((item) => item.id === selectedState.requestId)) {
    selectedState.requestId = state.requests[0]?.id || ''
  }
  if (!expenseDetailState.item) {
    if (!selectedState.expenseId || !state.expenses.some((item) => item.id === selectedState.expenseId)) {
      selectedState.expenseId = state.expenses[0]?.id || ''
    }
  }
  if (!approvalDetailState.item) {
    if (!selectedState.approvalId || !state.approvals.some((item) => item.id === selectedState.approvalId)) {
      selectedState.approvalId = state.approvals[0]?.id || ''
    }
  }
}

function hydrateHq(payload) {
  if (!payload) return
  Object.assign(state.hq.summary, payload.summary || {})
  replaceItems(state.hq.organizations, payload.organizations)
  replaceItems(state.hq.users, payload.users)
  replaceItems(state.hq.requests, payload.requests)
  replaceItems(state.hq.payments, payload.payments)
  replaceItems(state.hq.documents, payload.documents)
  replaceItems(state.hq.tickets, payload.tickets)
  replaceItems(state.hq.audits, payload.audits)
  state.hq.segments = payload.segments || createHqState().segments
  state.hq.directories = payload.directories || createHqState().directories
  state.hq.loaded = true
}

function hydrateWallet(payload) {
  if (!payload) return
  state.wallet.organization = payload.organization || null
  state.wallet.schematic = Boolean(payload.schematic)
  state.wallet.schematicNotice = payload.schematicNotice || payload.schematic_notice || ''
  Object.assign(state.wallet.summary, createWalletState().summary, payload.summary || {})
  Object.assign(state.wallet.licenseStatus, createWalletState().licenseStatus, payload.licenseStatus || payload.license_status || {})
  replaceItems(state.wallet.options, payload.options || [])
  replaceItems(state.wallet.wallets, payload.wallets || [])
  replaceItems(state.wallet.transactions, payload.transactions || [])
  state.wallet.loaded = true
}

function hydrateSupportTickets(payload) {
  replaceItems(state.support.tickets, Array.isArray(payload) ? payload : [])
  state.support.loaded = true
}

function hydrateSupportTicket(payload) {
  state.support.selectedTicket = payload || null
  if (!payload?.id) return
  const index = state.support.tickets.findIndex((item) => Number(item.id) === Number(payload.id))
  if (index >= 0) state.support.tickets[index] = { ...state.support.tickets[index], ...payload }
  else state.support.tickets.unshift(payload)
}

const supportUnreadCount = computed(() => {
  if (state.currentUser.isHq) {
    const tickets = (state.support.tickets?.length ? state.support.tickets : state.hq.tickets) || []
    const actionableTickets = tickets.filter((ticket) => ['open', 'pending'].includes(ticket.status)).length
    if (actionableTickets) return actionableTickets
    return Number(state.hq.summary.openTickets || 0) + Number(state.hq.summary.pendingTickets || 0)
  }
  void state.support.seenVersion
  const seenMap = readSupportSeenMap()
  return (state.support.tickets || []).filter((ticket) => {
    if (ticket.status !== 'answered') return false
    const seenAt = seenMap[String(ticket.id)]
    return seenAt !== ticket.updatedAt
  }).length
})

const chatUnreadCount = computed(() => Number(state.chat.unreadConversations || 0))

async function loadChatUnreadConversations() {
  if (!state.authToken) return
  try {
    const response = await authorizedFetch('/chat/conversations')
    const payload = repairPayload(await response.json())
    const list = Array.isArray(payload) ? payload : []
    state.chat.unreadConversations = list.filter((item) => Number(item.unreadCount || 0) > 0).length
    state.chat.loaded = true
  } catch {
    // keep previous badge
  }
}

const requestInboxCount = computed(() => state.requests.filter((item) => item.canApprove).length)
const expenseInboxCount = computed(() => state.expenses.filter((item) => item.canApprove).length)
const approvalInboxCount = computed(() => state.approvals.filter((item) => item.canApprove).length)

function captureInboxSnapshot() {
  return {
    requests: Number(requestInboxCount.value || 0),
    expenses: Number(expenseInboxCount.value || 0),
    approvals: Number(approvalInboxCount.value || 0),
    chat: Number(chatUnreadCount.value || 0),
    support: Number(supportUnreadCount.value || 0),
    tasking: Number(state.tasking.badgeCount || 0),
  }
}

function notifyIfInboxIncreased(previous, next, options = {}) {
  if (!previous || !next) return false
  const labels = {
    requests: 'درخواست نیازمند بررسی',
    expenses: 'هزینه نیازمند تایید',
    approvals: 'تاییدیه نیازمند تصمیم',
    chat: 'پیام گفتگوی جدید',
    support: 'به‌روزرسانی تیکت پشتیبانی',
    tasking: 'تسک نیازمند اقدام',
  }
  const keys = options.excludeChat
    ? ['requests', 'expenses', 'approvals', 'support', 'tasking']
    : ['requests', 'expenses', 'approvals', 'chat', 'support', 'tasking']
  const grewMessages = []
  keys.forEach((key) => {
    const delta = Number(next[key] || 0) - Number(previous[key] || 0)
    if (delta > 0) {
      grewMessages.push(`${labels[key] || 'اعلان جدید'}${delta > 1 ? ` (${delta.toLocaleString('fa-IR')})` : ''}`)
    }
  })
  if (!grewMessages.length) return false
  notifyInboxGrowth({
    title: 'اعلان جدید',
    message: grewMessages.join(' · '),
    isHq: Boolean(state.currentUser.isHq),
    tag: 'workflow-inbox-delta',
  })
  return true
}

async function softLiveSync(options = {}) {
  if (!state.authToken || !state.sessionReady || state.liveSync.inFlight) return

  state.liveSync.inFlight = true
  const previous = state.liveSync.initialized ? captureInboxSnapshot() : null
  try {
    state.liveSync.tick = Number(state.liveSync.tick || 0) + 1
    // Always refresh badge sources (even when tab is backgrounded) so notifs stay alive.
    await loadChatUnreadConversations()
    await loadTaskingDashboard(true, '', { soft: true, quiet: true }).catch(() => {})

    if (
      options.includeSupport !== false &&
      (state.currentUser.isHq || state.currentUser.canUseHq || state.currentUser.accessRole === 'admin')
    ) {
      if (state.liveSync.tick % 2 === 0 || options.forceSupport) {
        await loadSupportTickets(true, {
          soft: true,
          notifyNew: Boolean(state.liveSync.initialized && (state.currentUser.isHq || state.currentUser.canUseHq)),
        })
      }
    }

    // Bootstrap feeds request/expense/approval badges — keep it frequent enough for counters.
    const shouldBootstrap =
      options.includeBootstrap === true ||
      (options.includeBootstrap !== false && state.liveSync.tick % 2 === 0)
    if (shouldBootstrap) {
      await loadBootstrapData(true, { soft: true })
    }

    const next = captureInboxSnapshot()
    if (state.liveSync.initialized && previous) {
      const newChatCount = Number(next.chat || 0) - Number(previous.chat || 0)
      if (newChatCount > 0) {
        notifyNewChatMessages(newChatCount)
      }
      notifyIfInboxIncreased(previous, next, { excludeChat: true })
    }
    state.liveSync.lastSnapshot = next
    state.liveSync.initialized = true
  } catch {
    // keep UI stable during quiet sync
  } finally {
    state.liveSync.inFlight = false
  }
}

function markSupportTicketsSeen(ticketIds = []) {
  if (state.currentUser.isHq) return
  const seenMap = readSupportSeenMap()
  const ids = ticketIds.length ? ticketIds.map((item) => String(item)) : (state.support.tickets || []).map((item) => String(item.id))
  ids.forEach((id) => {
    const ticket = (state.support.tickets || []).find((item) => String(item.id) === id)
    if (ticket?.status === 'answered' && ticket.updatedAt) {
      seenMap[id] = ticket.updatedAt
    }
  })
  writeSupportSeenMap(seenMap)
  state.support.seenVersion += 1
}

function scopedApiPath(path) {
  if (!state.currentUser.isHq || !state.hq.selectedOrganizationId) return path
  const separator = path.includes('?') ? '&' : '?'
  return `${path}${separator}organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
}

function trackExpenseInboxNotifications(previousIds = []) {
  const current = (state.expenses || []).filter((item) => item.canApprove)
  const known = new Set((previousIds.length ? previousIds : state.liveSync.knownExpenseInboxIds || []).map(String))
  const fresh = current.filter((item) => !known.has(String(item.id)))
  state.liveSync.knownExpenseInboxIds = current.map((item) => String(item.id))
  if (fresh.length && state.liveSync.initialized) {
    notifyNewExpenses(fresh)
  }
}

async function loadBootstrapData(force = false, options = {}) {
  if (!state.authToken) {
    state.sessionReady = true
    return
  }
  if (state.bootstrapLoaded && !force) return

  const soft = Boolean(options.soft)
  const previousExpenseInboxIds = soft ? [...(state.liveSync.knownExpenseInboxIds || [])] : []
  if (!soft) {
    state.appLoading = true
    clearLastError()
  }
  try {
    const organizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
      ? `?organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
      : ''
    const response = await authorizedFetch(`/bootstrap${organizationQuery}`)
    const payload = repairPayload(await response.json())
    hydrateBootstrap(payload)
    if (soft) {
      trackExpenseInboxNotifications(previousExpenseInboxIds)
    } else {
      state.liveSync.knownExpenseInboxIds = (state.expenses || [])
        .filter((item) => item.canApprove)
        .map((item) => String(item.id))
    }
    state.bootstrapLoaded = true
    void loadChatUnreadConversations()
  } catch (error) {
    if (!soft) setLastError(error, 'خطا در بارگذاری')
    if (error.status === 401) throw error
  } finally {
    if (!soft) state.appLoading = false
    state.sessionReady = true
  }
}

async function loadReports(force = false) {
  if (!state.authToken || !canViewReports.value) return
  if (state.currentUser.isHq) {
    if (!state.hq.selectedOrganizationId) {
      state.reportSummary = null
      return
    }
    state.reportSummary = {
      users: state.users.length,
      requests: state.requests.length,
      expenses: state.expenses.length,
      approvals: state.approvals.length,
      expenseTotal: state.expenseSummary[2]?.value || '0',
    }
    return
  }
  if (state.reportSummary && !force) return
  const response = await authorizedFetch('/reports')
  const payload = repairPayload(await response.json())
  state.reportSummary = payload.summary
  state.reportStatus = payload.requestStatus
  state.topSubmitters = payload.topSubmitters
  replaceItems(state.reports, (payload.reports || []).map(normalizeReport))
  replaceItems(state.requests, (payload.requests || state.requests || []).map(normalizeRequest))
  replaceItems(state.expenses, (payload.expenses || state.expenses || []).map(normalizeExpense))
  replaceItems(state.approvals, (payload.approvals || state.approvals || []).map(normalizeApproval))
  replaceItems(state.users, (payload.users || state.users || []).map(normalizeUser))
}

async function loadSettings(force = false) {
  if (!state.authToken) return
  if (state.currentUser.isHq && !state.hq.selectedOrganizationId) {
    resetSettingsState()
    return
  }
  if (state.settings.systemId && !force) return
  const organizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
    ? `?organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  const response = await authorizedFetch(`/settings/profile${organizationQuery}`)
  const payload = repairPayload(await response.json())
  Object.assign(state.settings, createSettingsState(), payload)
  replaceItems(state.settingsCards, payload.sections || [])
  state.settings.organizationUsers = (payload.organizationUsers || []).map(normalizeUser)
  state.settings.departments = payload.departments || []
  state.settings.attendanceLocation = {
    ...createSettingsState().attendanceLocation,
    ...(payload.attendanceLocation || payload.attendance_location || {}),
    radiusMeters:
      payload.attendanceLocation?.radiusMeters ??
      payload.attendanceLocation?.radius_meters ??
      payload.attendance_location?.radiusMeters ??
      payload.attendance_location?.radius_meters ??
      20,
    provinceId:
      payload.attendanceLocation?.provinceId ??
      payload.attendanceLocation?.province_id ??
      payload.organizationGeo?.provinceId ??
      payload.organization_geo?.province_id ??
      null,
    provinceName:
      payload.attendanceLocation?.provinceName ??
      payload.attendanceLocation?.province_name ??
      payload.organizationGeo?.provinceName ??
      payload.organization_geo?.province_name ??
      '',
    cityId:
      payload.attendanceLocation?.cityId ??
      payload.attendanceLocation?.city_id ??
      payload.organizationGeo?.cityId ??
      payload.organization_geo?.city_id ??
      null,
    cityName:
      payload.attendanceLocation?.cityName ??
      payload.attendanceLocation?.city_name ??
      payload.organizationGeo?.cityName ??
      payload.organization_geo?.city_name ??
      '',
  }
  state.settings.workSchedule = {
    ...createSettingsState().workSchedule,
    ...(payload.workSchedule || payload.work_schedule || {}),
    workDayStart:
      payload.workSchedule?.workDayStart ||
      payload.workSchedule?.work_day_start ||
      payload.work_schedule?.workDayStart ||
      '09:00',
    workDayEnd:
      payload.workSchedule?.workDayEnd ||
      payload.workSchedule?.work_day_end ||
      payload.work_schedule?.workDayEnd ||
      '17:00',
    monthlyLeaveHours: Number(
      payload.workSchedule?.monthlyLeaveHours ??
        payload.workSchedule?.monthly_leave_hours ??
        payload.work_schedule?.monthlyLeaveHours ??
        20,
    ),
  }
  state.settings.organizationGeo = {
    ...createSettingsState().organizationGeo,
    ...(payload.organizationGeo || payload.organization_geo || {}),
    provinceId:
      payload.organizationGeo?.provinceId ??
      payload.organizationGeo?.province_id ??
      payload.organization_geo?.provinceId ??
      payload.organization_geo?.province_id ??
      null,
    provinceName:
      payload.organizationGeo?.provinceName ??
      payload.organizationGeo?.province_name ??
      payload.organization_geo?.provinceName ??
      payload.organization_geo?.province_name ??
      '',
    cityId:
      payload.organizationGeo?.cityId ??
      payload.organizationGeo?.city_id ??
      payload.organization_geo?.cityId ??
      payload.organization_geo?.city_id ??
      null,
    cityName:
      payload.organizationGeo?.cityName ??
      payload.organizationGeo?.city_name ??
      payload.organization_geo?.cityName ??
      payload.organization_geo?.city_name ??
      '',
  }
  state.directories.departments = payload.departments || state.directories.departments
  state.currentUser.organization = payload.organizationName || state.currentUser.organization
}

async function loadWalletDashboard(force = false) {
  if (!state.authToken) return
  if (!state.currentUser.isManager && !state.currentUser.canUseHq) {
    resetWalletState()
    return
  }
  if (state.currentUser.isHq && !state.hq.selectedOrganizationId) {
    resetWalletState()
    return
  }
  if (state.wallet.loaded && !force) return

  state.wallet.loading = true
  state.wallet.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet'))
    hydrateWallet(repairPayload(await response.json()))
  } catch (error) {
    state.wallet.error = error.message || 'Wallet load failed.'
    throw error
  } finally {
    state.wallet.loading = false
  }
}

async function loadWalletOptions(force = false) {
  if (!state.authToken) return
  if (state.wallet.options.length && !force) return
  state.wallet.loading = true
  state.wallet.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet/options'))
    const payload = repairPayload(await response.json())
    Object.assign(state.wallet.licenseStatus, createWalletState().licenseStatus, payload.licenseStatus || payload.license_status || {})
    replaceItems(state.wallet.options, payload.options || [])
  } catch (error) {
    state.wallet.error = error.message || 'Wallet options load failed.'
    throw error
  } finally {
    state.wallet.loading = false
  }
}

async function loadSupportTickets(force = false, options = {}) {
  if (!state.authToken) return
  const canSupport = Boolean(
    state.currentUser.isHq ||
    state.currentUser.canUseHq ||
    state.currentUser.accessRole === 'admin',
  )
  if (!canSupport) {
    state.support.loaded = true
    state.support.loading = false
    return
  }
  if (state.support.loaded && !force) return
  const soft = Boolean(options.soft)
  if (!soft) {
    state.support.loading = true
    state.support.error = ''
  }
  try {
    if (state.currentUser.isHq) {
      await loadHqTickets(force || true, options)
    } else {
      const response = await authorizedFetch(scopedApiPath('/support/tickets'))
      const list = repairPayload(await response.json())
      const tickets = Array.isArray(list) ? list : []
      if (options.notifyNew && state.liveSync.initialized) {
        const previous = Number(supportUnreadCount.value || 0)
        hydrateSupportTickets(tickets)
        if (Number(supportUnreadCount.value || 0) > previous) {
          playInboxAlertSound({ isHq: false })
        }
      } else {
        hydrateSupportTickets(tickets)
      }
    }
  } catch (error) {
    if (!soft) {
      state.support.error = error.message || 'Support load failed.'
      throw error
    }
  } finally {
    if (!soft) state.support.loading = false
  }
}

function ticketActivitySignature(tickets = []) {
  return (tickets || [])
    .map((item) => `${item.id}:${item.status}:${item.updatedAt || ''}:${item.lastMessageAt || ''}:${item.messagesCount || 0}`)
    .sort()
    .join('|')
}

async function loadHqTickets(force = true, options = {}) {
  if (!state.authToken || !state.currentUser.isHq) return
  const params = new URLSearchParams()
  if (options.q) params.set('q', options.q)
  if (options.status) params.set('status', options.status)
  if (options.priority) params.set('priority', options.priority)
  if (options.organizationId) params.set('organizationId', options.organizationId)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await authorizedFetch(`/hq/tickets${query}`)
  const tickets = repairPayload(await response.json())
  const list = Array.isArray(tickets) ? tickets : []

  if (options.notifyNew && state.support.knownTicketIds.length) {
    const known = new Set(state.support.knownTicketIds.map(Number))
    const fresh = list.filter((item) => !known.has(Number(item.id)))
    if (fresh.length) {
      notifyNewSupportTickets(fresh)
    } else {
      const nextSignature = ticketActivitySignature(list)
      if (state.support.activitySignature && nextSignature !== state.support.activitySignature) {
        playTicketAlertSound()
      }
      state.support.activitySignature = nextSignature
    }
  } else {
    state.support.activitySignature = ticketActivitySignature(list)
  }

  state.support.knownTicketIds = list.map((item) => item.id)
  hydrateSupportTickets(list)
  replaceItems(state.hq.tickets, list)
  state.support.loaded = true
}

async function loadHqTicketDetail(ticketId) {
  if (!ticketId) return
  state.support.detailLoading = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(`/hq/tickets/${ticketId}`)
    hydrateSupportTicket(repairPayload(await response.json()))
  } catch (error) {
    state.support.error = error.message || 'HQ ticket detail failed.'
    throw error
  } finally {
    state.support.detailLoading = false
  }
}

async function submitHqTicketReply(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(`/hq/tickets/${ticketId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadHqTickets(true)
  } catch (error) {
    state.support.error = error.message || 'HQ reply failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function loadHqTeam(force = false) {
  if (!state.authToken || !state.currentUser.isHq) return
  if (state.hq.team.length && !force) return
  const response = await authorizedFetch('/hq/team')
  replaceItems(state.hq.team, repairPayload(await response.json()) || [])
}

async function createHqTeamMember(payload) {
  const response = await authorizedFetch('/hq/team', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const member = repairPayload(await response.json())
  await loadHqTeam(true)
  return member
}

async function updateHqTeamMember(userId, payload) {
  const response = await authorizedFetch(`/hq/team/${userId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const member = repairPayload(await response.json())
  await loadHqTeam(true)
  return member
}

async function deleteHqTeamMember(userId) {
  await authorizedFetch(`/hq/team/${userId}`, { method: 'DELETE' })
  await loadHqTeam(true)
}

async function loadSupportTicketDetail(ticketId) {
  if (!ticketId) return
  if (state.currentUser.isHq) {
    return loadHqTicketDetail(ticketId)
  }
  state.support.detailLoading = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath(`/support/tickets/${ticketId}`))
    hydrateSupportTicket(repairPayload(await response.json()))
  } catch (error) {
    state.support.error = error.message || 'Support detail failed.'
    throw error
  } finally {
    state.support.detailLoading = false
  }
}

async function createSupportTicket(payload) {
  state.support.submitting = true
  state.support.error = ''
  state.support.message = ''
  try {
    const formData = new FormData()
    formData.append('subject', payload.subject || '')
    formData.append('message', payload.message || '')
    formData.append('category', payload.category || 'technical')
    formData.append('priority', payload.priority || 'medium')
    validateAttachmentList(payload.attachments || [])
    ;(payload.attachments || []).forEach((file) => formData.append('attachments', file))
    const response = await authorizedFetch(scopedApiPath('/support/tickets'), { method: 'POST', body: formData })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    state.support.message = 'تیکت ثبت شد.'
  } catch (error) {
    state.support.error = error.message || 'Support submit failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitSupportReply(ticketId, payload) {
  if (state.currentUser.isHq) {
    return submitHqTicketReply(ticketId, {
      body: payload.body,
      status: payload.close ? 'closed' : payload.status,
      isInternal: payload.isInternal,
      assignToUserId: payload.assignToUserId,
    })
  }
  state.support.submitting = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath(`/support/tickets/${ticketId}/messages`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
  } catch (error) {
    state.support.error = error.message || 'Support reply failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitSupportFeedback(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath(`/support/tickets/${ticketId}/feedback`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
  } catch (error) {
    state.support.error = error.message || 'Support feedback failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitSupportWalletDeposit(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const requestPayload = { ...payload, amount: normalizeAmountValue(payload?.amount) }
    const response = await authorizedFetch(`/support/tickets/${ticketId}/wallet-deposit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    await loadWalletDashboard(true)
  } catch (error) {
    state.support.error = error.message || 'Support wallet deposit failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitWalletTransaction(payload) {
  if (!payload) return
  state.wallet.submitting = true
  state.wallet.error = ''
  state.wallet.message = ''
  try {
    const requestPayload = { ...payload, amount: normalizeAmountValue(payload.amount) }
    const response = await authorizedFetch(scopedApiPath('/wallet/transactions'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateWallet(repairPayload(await response.json()))
    state.wallet.message = payload.direction === 'out' || payload.type === 'withdraw'
      ? 'برداشت ثبت شد.'
      : 'واریز ثبت شد.'
  } catch (error) {
    const normalized = setLastError(error, 'ثبت تراکنش کیف پول ناموفق بود.')
    state.wallet.error = normalized.message
    throw error
  } finally {
    state.wallet.submitting = false
  }
}

async function submitFeaturePurchase(payload) {
  if (!payload) return false
  state.wallet.submitting = true
  state.wallet.error = ''
  state.wallet.message = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet/purchases'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const responsePayload = repairPayload(await response.json())
    if (responsePayload.wallets || responsePayload.summary) {
      hydrateWallet(responsePayload)
      state.wallet.message = 'خرید با موفقیت از کیف پول انجام شد.'
    }
    else {
      Object.assign(state.wallet.licenseStatus, createWalletState().licenseStatus, responsePayload.licenseStatus || responsePayload.license_status || {})
      replaceItems(state.wallet.options, responsePayload.options || [])
      state.wallet.message = responsePayload.message || 'خرید ثبت شد.'
    }
    await loadBootstrapData(true)
    return true
  } catch (error) {
    const normalized = setLastError(error, 'خرید قابلیت ناموفق بود.')
    state.wallet.error = normalized.message
    return false
  } finally {
    state.wallet.submitting = false
  }
}

async function payFeatureInstallment(featureKey) {
  const key = String(featureKey || '').trim()
  if (!key) return false
  state.wallet.submitting = true
  state.wallet.error = ''
  state.wallet.message = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet/purchases'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'pay_installment', featureKey: key }),
    })
    hydrateWallet(repairPayload(await response.json()))
    state.wallet.message = 'قسط با موفقیت پرداخت شد.'
    await loadBootstrapData(true)
    return true
  } catch (error) {
    const normalized = setLastError(error, 'پرداخت قسط ناموفق بود.')
    state.wallet.error = normalized.message
    return false
  } finally {
    state.wallet.submitting = false
  }
}

async function loadHqPanel(force = false, options = {}) {
  if (!state.authToken || !state.currentUser.canUseHq) return
  if (state.hq.loaded && !force) return
  const soft = Boolean(options.soft)
  if (!soft) {
    state.hq.loading = true
    state.lastError = ''
  }
  try {
    const response = await authorizedFetch('/hq')
    hydrateHq(repairPayload(await response.json()))
  } catch (error) {
    if (!soft) {
      state.lastError = error.message || 'HQ load failed.'
      throw error
    }
  } finally {
    if (!soft) state.hq.loading = false
  }
}

async function selectHqOrganization(organizationId) {
  state.hq.selectedOrganizationId = organizationId ? String(organizationId) : ''
  state.bootstrapLoaded = false
  state.reportSummary = null
  resetSettingsState()
  resetWalletState()
  resetSupportState()
  await loadBootstrapData(true)
}

async function saveHqEntity(type, id, payload) {
  const endpoints = {
    organization: `/hq/organizations/${id}`,
    user: `/hq/users/${id}`,
    request: `/hq/requests/${id}`,
    payment: `/hq/payments/${id}`,
    document: `/hq/documents/${id}`,
  }
  if (!endpoints[type]) return
  state.hq.saving = true
  state.lastError = ''
  try {
    const requestPayload = type === 'payment' && 'amount' in payload
      ? { ...payload, amount: normalizeAmountValue(payload.amount) }
      : payload
    const response = await authorizedFetch(endpoints[type], {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateHq(repairPayload(await response.json()))
  } catch (error) {
    state.lastError = error.message || 'HQ save failed.'
    throw error
  } finally {
    state.hq.saving = false
  }
}

async function createHqOrganization(payload) {
  if (!state.authToken || !state.currentUser.canUseHq) return
  state.hq.saving = true
  state.lastError = ''
  try {
    const response = await authorizedFetch('/hq/organizations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateHq(repairPayload(await response.json()))
  } catch (error) {
    state.lastError = error.message || 'ساخت مجموعه ناموفق بود.'
    throw error
  } finally {
    state.hq.saving = false
  }
}

async function exportReport(reportId, format = 'csv', downloadUrl = '') {
  const hqOrganizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
    ? `&organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  let requestPath = downloadUrl || (reportId ? `/reports/${reportId}/export?format=${encodeURIComponent(format)}` : '')
  if (requestPath && hqOrganizationQuery) {
    requestPath += requestPath.includes('?') ? hqOrganizationQuery : `?${hqOrganizationQuery.slice(1)}`
  }
  if (!requestPath) return
  const response = await authorizedFetch(requestPath)
  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') || ''
  const fileName = parseDownloadFilename(disposition) || `${reportId || 'report'}-report.${format === 'csv' ? 'csv' : 'xlsx'}`
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
}

async function saveSettings(nextSettings) {
  const organizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
    ? `?organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  const response = await authorizedFetch(`/settings/profile${organizationQuery}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...nextSettings,
      ...(state.currentUser.isHq && state.hq.selectedOrganizationId ? { organizationId: state.hq.selectedOrganizationId } : {}),
    }),
  })
  const payload = repairPayload(await response.json())
  Object.assign(state.settings, createSettingsState(), payload)
  replaceItems(state.settingsCards, payload.sections || [])
  state.settings.organizationUsers = (payload.organizationUsers || []).map(normalizeUser)
  state.settings.departments = payload.departments || []
  state.settings.attendanceLocation = {
    ...createSettingsState().attendanceLocation,
    ...(payload.attendanceLocation || payload.attendance_location || {}),
    radiusMeters:
      payload.attendanceLocation?.radiusMeters ??
      payload.attendanceLocation?.radius_meters ??
      payload.attendance_location?.radiusMeters ??
      payload.attendance_location?.radius_meters ??
      20,
    provinceId:
      payload.attendanceLocation?.provinceId ??
      payload.attendanceLocation?.province_id ??
      payload.organizationGeo?.provinceId ??
      payload.organization_geo?.province_id ??
      null,
    provinceName:
      payload.attendanceLocation?.provinceName ??
      payload.attendanceLocation?.province_name ??
      payload.organizationGeo?.provinceName ??
      payload.organization_geo?.province_name ??
      '',
    cityId:
      payload.attendanceLocation?.cityId ??
      payload.attendanceLocation?.city_id ??
      payload.organizationGeo?.cityId ??
      payload.organization_geo?.city_id ??
      null,
    cityName:
      payload.attendanceLocation?.cityName ??
      payload.attendanceLocation?.city_name ??
      payload.organizationGeo?.cityName ??
      payload.organization_geo?.city_name ??
      '',
  }
  state.settings.workSchedule = {
    ...createSettingsState().workSchedule,
    ...(payload.workSchedule || payload.work_schedule || {}),
    workDayStart:
      payload.workSchedule?.workDayStart ||
      payload.workSchedule?.work_day_start ||
      payload.work_schedule?.workDayStart ||
      '09:00',
    workDayEnd:
      payload.workSchedule?.workDayEnd ||
      payload.workSchedule?.work_day_end ||
      payload.work_schedule?.workDayEnd ||
      '17:00',
    monthlyLeaveHours: Number(
      payload.workSchedule?.monthlyLeaveHours ??
        payload.workSchedule?.monthly_leave_hours ??
        payload.work_schedule?.monthlyLeaveHours ??
        20,
    ),
  }
  state.settings.organizationGeo = {
    ...createSettingsState().organizationGeo,
    ...(payload.organizationGeo || payload.organization_geo || {}),
    provinceId:
      payload.organizationGeo?.provinceId ??
      payload.organizationGeo?.province_id ??
      payload.organization_geo?.provinceId ??
      payload.organization_geo?.province_id ??
      null,
    provinceName:
      payload.organizationGeo?.provinceName ??
      payload.organizationGeo?.province_name ??
      payload.organization_geo?.provinceName ??
      payload.organization_geo?.province_name ??
      '',
    cityId:
      payload.organizationGeo?.cityId ??
      payload.organizationGeo?.city_id ??
      payload.organization_geo?.cityId ??
      payload.organization_geo?.city_id ??
      null,
    cityName:
      payload.organizationGeo?.cityName ??
      payload.organizationGeo?.city_name ??
      payload.organization_geo?.cityName ??
      payload.organization_geo?.city_name ??
      '',
  }
  state.directories.departments = payload.departments || state.directories.departments
  state.currentUser.organization = payload.organizationName || state.currentUser.organization
}

async function restoreSession() {
  state.sessionReady = false
  if (!state.authToken) {
    state.sessionReady = true
    return
  }
  await loadBootstrapData(true)
  try {
    await loadSupportTickets(true)
  } catch (error) {
    state.lastError = error.message || state.lastError
  }
  if (canViewReports.value) {
    try {
      await loadReports(true)
    } catch (error) {
      state.lastError = error.message || state.lastError
    }
  }
}

async function login(email, password) {
  state.loginPending = true
  clearLastError()
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!response.ok) {
      const payload = repairPayload(await response.json())
      throw appErrorFromResponse(payload, response.status, 'ورود ناموفق بود.')
    }
    const payload = repairPayload(await response.json())
    state.authToken = payload.access_token
    localStorage.setItem(TOKEN_KEY, payload.access_token)
    state.bootstrapLoaded = false
    await loadBootstrapData(true)
    return true
  } catch (error) {
    setLastError(error, 'ورود ناموفق بود.')
    return false
  } finally {
    state.loginPending = false
    state.sessionReady = true
  }
}

async function submitSupportBankWithdrawComplete(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const requestPayload = { ...payload, amount: normalizeAmountValue(payload?.amount) }
    const response = await authorizedFetch(`/support/tickets/${ticketId}/bank-withdraw-complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    await loadWalletDashboard(true)
  } catch (error) {
    state.support.error = error.message || 'Support bank withdrawal failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function registerOrganization(payload) {
  state.loginPending = true
  clearLastError()
  try {
    const formData = new FormData()
    Object.entries(payload).forEach(([key, value]) => {
      if (key !== 'documents' && value !== undefined && value !== null) formData.append(key, value)
    })
    ;(payload.documents || []).forEach((file) => formData.append('documents', file))
    const response = await fetch(`${API_BASE_URL}/auth/register`, { method: 'POST', body: formData })
    if (!response.ok) {
      const errorPayload = repairPayload(await response.json())
      throw appErrorFromResponse(errorPayload, response.status, 'ثبت نام ناموفق بود.')
    }
    await response.json()
    return true
  } catch (error) {
    setLastError(error, 'ثبت نام ناموفق بود.')
    return false
  } finally {
    state.loginPending = false
  }
}

async function submitSupportRegistrationApproval(ticketId, companyCode) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(`/support/tickets/${ticketId}/approve-registration`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ companyCode }),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    return true
  } catch (error) {
    state.support.error = error.message || 'ثبت مجموعه ناموفق بود.'
    return false
  } finally {
    state.support.submitting = false
  }
}

let singleton

export function useWorkflowHub() {
  const router = useRouter()

  if (singleton) return singleton

  function ensureAuthenticatedRedirect() {
    if (!state.authToken) router.push('/')
  }

  async function logout() {
    try {
      if (state.authToken) {
        await authorizedFetch('/auth/logout', { method: 'POST' })
      }
    } catch {
      // Local session cleanup must still happen if the server cannot record logout.
    } finally {
      clearSessionState()
      router.push('/')
    }
  }

  function navigateTo(path) {
    router.push(path)
    state.mobileMenuOpen = false
  }

  function toggleSidebar() {
    state.mobileMenuOpen = !state.mobileMenuOpen
  }

  function updatePageFilter(page, key, value) {
    if (!state.filters[page]) return
    state.filters[page][key] = value
  }

  function resetPageFilters(page) {
    if (!state.filters[page]) return
    Object.assign(state.filters[page], { query: '', person: '', startDate: '', endDate: '' })
  }

  function hqScopedPath(path) {
    if (!state.currentUser.isHq || !state.hq.selectedOrganizationId) return path
    const separator = path.includes('?') ? '&' : '?'
    return `${path}${separator}organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
  }

  async function loadRequestDetail(requestId) {
    if (!requestId) return
    if (requestDetailState.items[requestId]) return
    requestDetailState.loading = true
    try {
      const response = await authorizedFetch(hqScopedPath(`/requests/${requestId}`))
      requestDetailState.items[requestId] = repairPayload(await response.json())
    } finally {
      requestDetailState.loading = false
    }
  }

  function openRequestDetail(id) {
    selectedState.requestId = id
    modalState.requestDetail = true
    void loadRequestDetail(id)
  }

  function closeRequestDetail() {
    modalState.requestDetail = false
  }

  async function loadExpenseDetail(id) {
    expenseDetailState.loading = true
    try {
      const response = await authorizedFetch(hqScopedPath(`/expenses/${id}`))
      expenseDetailState.item = normalizeExpense(repairPayload(await response.json()))
      selectedState.expenseId = id
    } finally {
      expenseDetailState.loading = false
    }
  }

  function openExpenseDetail(id) {
    modalState.expenseDetail = true
    void loadExpenseDetail(id)
  }

  function closeExpenseDetail() {
    modalState.expenseDetail = false
    expenseDetailState.item = null
  }

  async function loadApprovalDetail(id) {
    approvalDetailState.loading = true
    try {
      const response = await authorizedFetch(hqScopedPath(`/approvals/${id}`))
      approvalDetailState.item = normalizeApproval(repairPayload(await response.json()))
      selectedState.approvalId = id
    } finally {
      approvalDetailState.loading = false
    }
  }

  function openApprovalDetail(id) {
    modalState.approvalDetail = true
    void loadApprovalDetail(id)
  }

  function closeApprovalDetail() {
    modalState.approvalDetail = false
    approvalDetailState.item = null
  }

  function openRequestComposer() {
    clearLastError()
    resetRequestForm()
    modalState.requestComposer = true
  }

  function closeRequestComposer() {
    clearLastError()
    modalState.requestComposer = false
    resetRequestForm()
  }

  function openExpenseComposer() {
    clearLastError()
    resetExpenseForm()
    modalState.expenseComposer = true
  }

  function closeExpenseComposer() {
    clearLastError()
    modalState.expenseComposer = false
    resetExpenseForm()
  }

  function openUserComposer() {
    clearLastError()
    resetUserForm()
    modalState.userComposer = true
  }

  function closeUserComposer() {
    clearLastError()
    modalState.userComposer = false
    resetUserForm()
  }

  function openDocumentComposer() {
    clearLastError()
    resetDocumentForm()
    if (state.directories.managers.length === 1) {
      state.documentForm.assigneeIds = [state.directories.managers[0].id]
    }
    if (!state.documentForm.department && state.directories.departments.length === 1) {
      state.documentForm.department = state.directories.departments[0].code
    }
    modalState.documentComposer = true
  }

  function closeDocumentComposer() {
    clearLastError()
    modalState.documentComposer = false
    resetDocumentForm()
  }

  async function loadSignature() {
    if (!canApproveDocuments.value) return
    signatureState.loading = true
    try {
      const response = await authorizedFetch('/approvals/signature')
      const payload = repairPayload(await response.json())
      signatureState.hasSignature = payload.hasSignature
      signatureState.signatureData = payload.signatureData || ''
      signatureState.hasStamp = Boolean(payload.hasStamp)
      signatureState.stampData = payload.stampData || ''
      return true
    } catch (error) {
      signatureState.hasSignature = false
      signatureState.signatureData = ''
      signatureState.hasStamp = false
      signatureState.stampData = ''
      state.lastError = error.message || 'بارگذاری امضا انجام نشد.'
      return false
    } finally {
      signatureState.loading = false
    }
  }

  async function openSignatureComposer() {
    clearLastError()
    modalState.signatureComposer = true
    await loadSignature()
  }

  function closeSignatureComposer() {
    clearLastError()
    modalState.signatureComposer = false
  }

  async function setRequestFiles(files) {
    const incoming = Array.from(files || [])
    if (!incoming.length) return
    state.fileUploadPreparing = true
    clearLastError()
    try {
      const nextAttachments = [...state.requestForm.attachments]
      if (nextAttachments.length + incoming.length > UPLOAD_LIMITS.maxAttachments) {
        throw createValidationError(`حداکثر ${UPLOAD_LIMITS.maxAttachments} پیوست مجاز است.`, [{
          field: 'attachments',
          message: 'تعداد پیوست‌ها بیش از حد مجاز است.',
        }])
      }
      for (const file of incoming) {
        nextAttachments.push(storeRawFile(await prepareUploadFile(file)))
      }
      state.requestForm.attachments = nextAttachments
    } catch (error) {
      setLastError(error, 'انتخاب فایل پیوست ناموفق بود.')
      throw error
    } finally {
      state.fileUploadPreparing = false
    }
  }

  function removeAttachment(index) {
    state.requestForm.attachments = state.requestForm.attachments.filter((_, itemIndex) => itemIndex !== index)
  }

  async function setExpenseInvoice(file) {
    if (!file) {
      state.expenseForm.invoice = null
      return
    }
    state.fileUploadPreparing = true
    clearLastError()
    try {
      state.expenseForm.invoice = storeRawFile(await prepareUploadFile(file))
    } catch (error) {
      state.expenseForm.invoice = null
      setLastError(error, 'انتخاب فاکتور ناموفق بود.')
      throw error
    } finally {
      state.fileUploadPreparing = false
    }
  }

  async function setDocumentFile(file) {
    if (!file) {
      state.documentForm.file = null
      return
    }
    state.fileUploadPreparing = true
    clearLastError()
    try {
      state.documentForm.file = storeRawFile(await prepareUploadFile(file))
    } catch (error) {
      state.documentForm.file = null
      setLastError(error, 'انتخاب فایل سند ناموفق بود.')
      throw error
    } finally {
      state.fileUploadPreparing = false
    }
  }

  async function submitRequest() {
    state.requestSubmitting = true
    clearLastError()
    try {
      if (!String(state.requestForm.title || '').trim()) {
        throw createValidationError('عنوان درخواست الزامی است.', [{ field: 'title', message: 'عنوان درخواست را وارد کنید.' }])
      }
      if (!state.requestForm.manager) {
        throw createValidationError('حداقل یک مدیر ارجاع گیرنده باید انتخاب شود.', [{ field: 'manager', message: 'از بخش ارجاع گیرنده یک مدیر انتخاب کنید.' }])
      }

      const formData = new FormData()
      const primaryManagerId = state.directories.managers.find((item) => item.slug === state.requestForm.manager)?.id
      const managerAssigneeIds = (state.requestForm.managerAssigneeIds || [])
        .map((item) => Number(item))
        .filter((item) => item && item !== Number(primaryManagerId))
      formData.append('title', state.requestForm.title)
      formData.append('description', state.requestForm.description)
      formData.append('department', state.requestForm.department)
      formData.append('manager', state.requestForm.manager)
      formData.append('managerAssigneeIds', managerAssigneeIds.join(','))
      formData.append('employeeAssigneeIds', state.requestForm.employeeAssigneeIds.join(','))
      formData.append('priority', state.requestForm.priority)
      formData.append('requestType', state.requestForm.requestType || 'general')
      formData.append('action', 'refer')
      if (state.requestForm.deadline) formData.append('deadline', jalaliToIso(state.requestForm.deadline))
      const requestType = state.requestForm.requestType || 'general'
      if (requestType === 'leave_hourly' || requestType === 'leave_daily') {
        const startIso = jalaliToIso(state.requestForm.leaveStartDate)
        const endIso = jalaliToIso(state.requestForm.leaveEndDate || state.requestForm.leaveStartDate)
        if (!startIso || !endIso) {
          throw createValidationError('بازه مرخصی الزامی است.', [{ field: 'leaveStartDate', message: 'تاریخ مرخصی را مشخص کنید.' }])
        }
        if (requestType === 'leave_daily') {
          formData.append('leaveStartDate', startIso)
          formData.append('leaveEndDate', endIso)
        } else {
          const startTime = String(state.requestForm.leaveStartTime || '09:00').trim()
          const endTime = String(state.requestForm.leaveEndTime || '13:00').trim()
          formData.append('leaveStartsAt', `${startIso}T${startTime}:00`)
          formData.append('leaveEndsAt', `${endIso}T${endTime}:00`)
        }
      }
      validateAttachmentList(state.requestForm.attachments)
      state.requestForm.attachments.forEach((file) => formData.append('attachments', file))
      await authorizedFetch('/requests', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeRequestComposer()
    } catch (error) {
      setLastError(error, 'ثبت درخواست ناموفق بود.')
      throw error
    } finally {
      state.requestSubmitting = false
    }
  }

  async function submitExpense(action = 'refer') {
    state.expenseSubmitting = true
    clearLastError()
    try {
      const amountValue = normalizeAmountValue(state.expenseForm.amount)
      if (!Number(amountValue || 0)) {
        throw createValidationError('مبلغ هزینه باید بیشتر از صفر باشد.', [{ field: 'amount', message: 'یک مبلغ معتبر و بزرگ تر از صفر وارد کنید.' }])
      }
      if (!String(state.expenseForm.description || '').trim()) {
        throw createValidationError('شرح هزینه الزامی است.', [{ field: 'description', message: 'شرح هزینه را وارد کنید.' }])
      }
      const formData = new FormData()
      formData.append('description', state.expenseForm.description)
      formData.append('amount', amountValue)
      formData.append('expenseDate', jalaliToIso(state.expenseForm.expenseDate))
      formData.append('department', state.expenseForm.department)
      formData.append('action', 'refer')
      formData.append('managerAssigneeIds', (state.expenseForm.managerAssigneeIds || []).join(','))
      formData.append('employeeAssigneeIds', (state.expenseForm.employeeAssigneeIds || []).join(','))
      if (state.expenseForm.invoice) {
        validateAttachmentList([state.expenseForm.invoice], { maxCount: 1, label: 'فاکتور' })
        formData.append('invoice', state.expenseForm.invoice)
      }
      await authorizedFetch('/expenses', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeExpenseComposer()
    } catch (error) {
      setLastError(error, 'ثبت هزینه ناموفق بود.')
      throw error
    } finally {
      state.expenseSubmitting = false
    }
  }

  async function submitUser() {
    state.userSubmitting = true
    clearLastError()
    try {
      if (!String(state.userForm.fullName || '').trim()) {
        throw createValidationError('نام کامل کاربر الزامی است.', [{ field: 'fullName', message: 'نام و نام خانوادگی را وارد کنید.' }])
      }
      if (!String(state.userForm.username || '').trim()) {
        throw createValidationError('نام کاربری الزامی است.', [{ field: 'username', message: 'نام کاربری کاربر را وارد کنید.' }])
      }
      if (state.userForm.password && String(state.userForm.password).length < 6) {
        throw createValidationError('رمز عبور باید حداقل 6 کاراکتر باشد.', [{ field: 'password', message: 'رمز عبور کوتاه است.' }])
      }
      const phoneDigits = String(state.userForm.phone || '')
        .replace(/[۰-۹]/g, (d) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)))
        .replace(/\D/g, '')
      const phoneNormalized =
        phoneDigits.length === 10 && phoneDigits.startsWith('9')
          ? `0${phoneDigits}`
          : phoneDigits.startsWith('98') && phoneDigits.length >= 12
            ? `0${phoneDigits.slice(2)}`
            : phoneDigits
      if (!(phoneNormalized.length === 11 && phoneNormalized.startsWith('09'))) {
        throw createValidationError('شماره موبایل برای ارسال مشخصات ورود الزامی است.', [
          { field: 'phone', message: 'شماره موبایل معتبر وارد کنید (مثال: 09121234567).' },
        ])
      }

      const formData = new FormData()
      formData.append('fullName', String(state.userForm.fullName || '').trim())
      formData.append('username', String(state.userForm.username || '').trim())
      formData.append('password', String(state.userForm.password || ''))
      formData.append('phone', phoneNormalized)
      formData.append('accessRole', state.userForm.accessRole || 'employee')
      formData.append('department', state.userForm.department || '')
      formData.append('managerId', state.userForm.managerId ? String(state.userForm.managerId) : '')
      formData.append('jobTitle', String(state.userForm.jobTitle || '').trim())
      formData.append('sectionAccess', JSON.stringify(state.userForm.sectionAccess || {}))
      formData.append('entrustedItems', JSON.stringify(state.userForm.entrustedItems || []))
      formData.append('bonusAmount', String(state.userForm.bonusAmount || '0'))
      formData.append('penaltyAmount', String(state.userForm.penaltyAmount || '0'))
      if (state.userForm.avatarFile) formData.append('avatar', state.userForm.avatarFile)

      const response = await authorizedFetch('/users', { method: 'POST', body: formData })
      const created = repairPayload(await response.json())
      const sms = created?.credentialsSms
      if (sms?.ok) {
        notifySuccess(`کاربر ساخته شد و پیامک ورود به ${sms.phone || phoneNormalized} ارسال شد.`)
      } else if (sms?.message) {
        notifyWarning(`کاربر ساخته شد، اما پیامک ارسال نشد: ${sms.message}`)
      } else {
        notifyInfo('کاربر جدید ثبت شد.')
      }
      await loadBootstrapData(true)
      if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
        await loadSettings(true)
      }
      closeUserComposer()
    } catch (error) {
      setLastError(error, 'ایجاد کاربر ناموفق بود.')
      throw error
    } finally {
      state.userSubmitting = false
    }
  }

  async function uploadOwnAvatar(file) {
    clearLastError()
    if (!file) {
      throw createValidationError('فایل تصویر پروفایل الزامی است.', [{ field: 'avatar', message: 'یک تصویر انتخاب کنید.' }])
    }
    if (!String(file.type || '').startsWith('image/')) {
      throw createValidationError('فقط فایل تصویری مجاز است.', [{ field: 'avatar', message: 'فرمت تصویر معتبر نیست.' }])
    }
    const formData = new FormData()
    formData.append('avatar', file)
    const response = await authorizedFetch('/me/avatar', { method: 'POST', body: formData })
    const payload = repairPayload(await response.json())
    Object.assign(state.currentUser, createCurrentUser(), payload || {})
    state.currentUser.avatarUrl = resolveAvatarUrl(state.currentUser.avatarUrl || state.currentUser.avatar_url || '')
    state.currentUser.avatarFileName = cleanDisplayText(state.currentUser.avatarFileName || state.currentUser.avatar_file_name)
    patchUserAvatarInLists(state.currentUser.id, state.currentUser.avatar, state.currentUser.avatarUrl, {
      avatarFileName: state.currentUser.avatarFileName,
    })
    return state.currentUser
  }

  async function clearOwnAvatar() {
    clearLastError()
    const response = await authorizedFetch('/me/avatar', { method: 'DELETE' })
    const payload = repairPayload(await response.json())
    Object.assign(state.currentUser, createCurrentUser(), payload || {})
    state.currentUser.avatarUrl = resolveAvatarUrl(state.currentUser.avatarUrl || state.currentUser.avatar_url || '')
    state.currentUser.avatarFileName = ''
    patchUserAvatarInLists(state.currentUser.id, state.currentUser.avatar, state.currentUser.avatarUrl, {
      avatarFileName: '',
    })
    return state.currentUser
  }

  function patchUserAvatarInLists(userId, avatar, avatarUrl, options = {}) {
    const id = Number(userId)
    if (!id) return
    ;[state.users, state.settings.organizationUsers, state.directories.users, state.directories.managers]
      .filter(Array.isArray)
      .forEach((list) => {
        const index = list.findIndex((entry) => Number(entry?.id) === id)
        if (index >= 0) {
          list[index] = {
            ...list[index],
            avatar: avatar || list[index].avatar,
            avatarUrl: avatarUrl || '',
            avatarFileName: options.avatarFileName ?? (avatarUrl ? list[index].avatarFileName : ''),
          }
        }
      })
  }

  async function submitDocument() {
    state.documentSubmitting = true
    clearLastError()
    try {
      if (!String(state.documentForm.title || '').trim()) {
        throw createValidationError('عنوان سند الزامی است.', [{ field: 'title', message: 'عنوان سند را وارد کنید.' }])
      }
      if (!state.documentForm.file) {
        throw createValidationError('فایل سند الزامی است.', [{ field: 'file', message: 'فایل سند را انتخاب کنید.' }])
      }
      if (!state.documentForm.assigneeIds.length) {
        throw createValidationError('حداقل یک دریافت کننده را انتخاب کنید.', [{ field: 'assigneeIds', message: 'حداقل یک دریافت کننده برای سند انتخاب کنید.' }])
      }
      const formData = new FormData()
      formData.append('title', state.documentForm.title)
      formData.append('description', state.documentForm.description)
      formData.append('department', state.documentForm.department)
      formData.append('documentType', state.documentForm.documentType)
      formData.append('risk', state.documentForm.risk)
      formData.append('assigneeIds', state.documentForm.assigneeIds.join(','))
      validateAttachmentList([state.documentForm.file], { maxCount: 1, label: 'فایل سند' })
      formData.append('file', state.documentForm.file)
      await authorizedFetch('/approvals/documents', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeDocumentComposer()
    } catch (error) {
      setLastError(error, 'ثبت سند ناموفق بود.')
      throw error
    } finally {
      state.documentSubmitting = false
    }
  }

  async function saveSignature(signatureData, stampData = '') {
    signatureState.loading = true
    state.lastError = ''
    try {
      const response = await authorizedFetch('/approvals/signature', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signatureData, stampData }),
      })
      const payload = repairPayload(await response.json())
      signatureState.hasSignature = payload.hasSignature
      signatureState.signatureData = payload.signatureData
      signatureState.hasStamp = Boolean(payload.hasStamp)
      signatureState.stampData = payload.stampData || ''
      closeSignatureComposer()
      await loadBootstrapData(true)
    } catch (error) {
      state.lastError = error.message || 'ثبت امضا ناموفق بود.'
      throw error
    } finally {
      signatureState.loading = false
    }
  }

  async function approveSelectedDocument() {
    if (!selectedApproval.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/approvals/${selectedApproval.value.id}/approve`), { method: 'POST' })
      closeApprovalDetail()
      notifyInfo('سند تایید شد.')
      await loadBootstrapData(true, { soft: true })
    } catch (error) {
      state.lastError = error.message || 'تایید سند ناموفق بود.'
      throw error
    }
  }

  async function rejectSelectedDocument(reason = '') {
    if (!selectedApproval.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/approvals/${selectedApproval.value.id}/reject`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      })
      closeApprovalDetail()
      notifyInfo('سند رد شد.')
      await loadBootstrapData(true, { soft: true })
    } catch (error) {
      state.lastError = error.message || 'رد سند ناموفق بود.'
      throw error
    }
  }

  async function approveSelectedRequest() {
    if (!selectedRequest.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/approve`), { method: 'POST' })
      closeRequestDetail()
      notifyInfo('درخواست تایید شد.')
      await loadBootstrapData(true, { soft: true })
    } catch (error) {
      state.lastError = error.message || 'تایید درخواست ناموفق بود.'
      throw error
    }
  }

  async function rejectSelectedRequest(reason = '') {
    if (!selectedRequest.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/reject`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      })
      closeRequestDetail()
      notifyInfo('درخواست رد شد.')
      await loadBootstrapData(true, { soft: true })
    } catch (error) {
      state.lastError = error.message || 'رد درخواست ناموفق بود.'
      throw error
    }
  }

  async function referSelectedRequest(payload) {
    if (!selectedRequest.value) return
    state.lastError = ''
    await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/refer`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    await loadBootstrapData(true)
    closeRequestDetail()
  }

  async function approveSelectedExpense() {
    if (!selectedExpense.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/approve`), { method: 'POST' })
      closeExpenseDetail()
      notifyInfo('هزینه تایید شد.')
      await loadBootstrapData(true, { soft: true })
    } catch (error) {
      state.lastError = error.message || 'تایید هزینه ناموفق بود.'
      throw error
    }
  }

  async function rejectSelectedExpense(reason = '') {
    if (!selectedExpense.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/reject`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      })
      closeExpenseDetail()
      notifyInfo('هزینه رد شد.')
      await loadBootstrapData(true, { soft: true })
    } catch (error) {
      state.lastError = error.message || 'رد هزینه ناموفق بود.'
      throw error
    }
  }

  async function referSelectedExpense(payload) {
    if (!selectedExpense.value) return
    state.lastError = ''
    await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/refer`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    await loadBootstrapData(true)
    closeExpenseDetail()
  }

async function updateUser(userId, payload) {
  clearLastError()
  try {
    const hasAvatarFile = payload?.avatarFile instanceof File
    const clearAvatar = Boolean(payload?.clearAvatar)
    let response
    if (hasAvatarFile || clearAvatar) {
      const formData = new FormData()
      Object.entries(payload || {}).forEach(([key, value]) => {
        if (key === 'avatarFile' || key === 'clearAvatar') return
        if (value === undefined || value === null) return
        if (key === 'sectionAccess') {
          formData.append(key, JSON.stringify(value))
          return
        }
        if (key === 'managerId') {
          formData.append(key, value ? String(value) : '')
          return
        }
        if (typeof value === 'boolean') {
          formData.append(key, value ? '1' : '0')
          return
        }
        formData.append(key, String(value))
      })
      if (hasAvatarFile) formData.append('avatar', payload.avatarFile)
      if (clearAvatar) formData.append('clearAvatar', '1')
      response = await authorizedFetch(`/users/${userId}`, { method: 'PATCH', body: formData })
    } else {
      const body = {
        ...payload,
        managerId: payload.managerId ? Number(payload.managerId) : null,
      }
      if (!String(body.password || '').trim()) delete body.password
      if (body.avatarFile) delete body.avatarFile
      if (body.clearAvatar !== undefined) delete body.clearAvatar
      response = await authorizedFetch(`/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    }
    const updatedUser = normalizeUser(repairPayload(await response.json()))
    syncUserAcrossState(updatedUser)
    if (Number(state.currentUser.id) === Number(updatedUser.id)) {
      state.currentUser.avatar = updatedUser.avatar || state.currentUser.avatar
      state.currentUser.avatarUrl = updatedUser.avatarUrl || ''
      state.currentUser.avatarFileName = updatedUser.avatarFileName || ''
    }
    if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
      try {
        await loadSettings(true)
      } catch (error) {
        setLastError(error, 'کاربر ذخیره شد اما تازه‌سازی تنظیمات انجام نشد.')
      }
    }
    return updatedUser
  } catch (error) {
    setLastError(error, 'ذخیره تغییرات کاربر ناموفق بود.')
    throw error
  }
}

async function addUserEntrustedItem(userId, payload) {
  clearLastError()
  try {
    const response = await authorizedFetch(`/users/${userId}/entrusted-items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = repairPayload(await response.json())
    const updatedUser = normalizeUser(data.user || data)
    syncUserAcrossState(updatedUser)
    return { item: data.item, user: updatedUser }
  } catch (error) {
    setLastError(error, 'افزودن امانت ناموفق بود.')
    throw error
  }
}

async function removeUserEntrustedItem(userId, itemId) {
  clearLastError()
  try {
    const response = await authorizedFetch(`/users/${userId}/entrusted-items/${itemId}`, {
      method: 'DELETE',
    })
    const data = repairPayload(await response.json())
    const updatedUser = normalizeUser(data.user || data)
    syncUserAcrossState(updatedUser)
    return updatedUser
  } catch (error) {
    setLastError(error, 'حذف امانت ناموفق بود.')
    throw error
  }
}

  async function referSelectedDocument(payload) {
    if (!selectedApproval.value) return
    state.lastError = ''
    await authorizedFetch(hqScopedPath(`/approvals/${selectedApproval.value.id}/refer`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    await loadBootstrapData(true)
    closeApprovalDetail()
  }

  function openTaskComposer() {
    clearLastError()
    state.tasking.schedulePreview = null
    modalState.taskComposer = true
  }

  function closeTaskComposer() {
    modalState.taskComposer = false
  }

  function openTaskDetail() {
    modalState.taskDetail = true
  }

  function closeTaskDetail() {
    modalState.taskDetail = false
    state.tasking.selectedTask = null
  }

  const taskingBadgeCount = computed(() => Number(state.tasking.badgeCount || 0))

  async function loadTaskingDashboard(force = false, dateIso = '', options = {}) {
    const soft = Boolean(options.soft)
    if (state.tasking.loading && !soft) return state.tasking
    if (state.tasking.loaded && !force && !dateIso) return state.tasking
    if (!soft) {
      state.tasking.loading = true
      state.tasking.error = ''
    }
    const previousBadge = Number(state.tasking.badgeCount || 0)
    const previousMentions = Number(state.tasking.stats?.unreadMentions || 0)
    const hadLoaded = Boolean(state.tasking.loaded)
    try {
      const params = new URLSearchParams()
      const resolvedDate = dateIso || state.tasking.date || ''
      if (resolvedDate) params.set('date', resolvedDate)
      const ownerId = String(options.superviseOwnerId || '').trim()
      if (ownerId) params.set('ownerId', ownerId)
      const query = params.toString() ? `?${params.toString()}` : ''
      const response = await authorizedFetch(`/tasking/dashboard${query}`)
      const payload = repairPayload(await response.json())
      state.tasking.loaded = true
      state.tasking.date = payload.date || state.tasking.date
      state.tasking.settings = payload.settings || null
      state.tasking.capacity = payload.capacity || null
      state.tasking.stats = { ...createTaskingState().stats, ...(payload.stats || {}) }
      state.tasking.counts = { ...createTaskingState().counts, ...(payload.counts || {}) }
      state.tasking.badgeCount = Number(payload.badgeCount || 0)
      state.tasking.activeTimer = payload.activeTimer || null
      state.tasking.mine = payload.mine || createTaskingState().mine
      state.tasking.assignments = payload.assignments || createTaskingState().assignments
      state.tasking.supervise = payload.supervise || createTaskingState().supervise
      state.tasking.mentions = payload.mentions || createTaskingState().mentions
      state.tasking.departments = payload.departments || []
      state.tasking.assigneeOptions = payload.assigneeOptions || []
      state.tasking.superviseFocus = payload.superviseFocus || null
      if (hadLoaded && soft && !options.quiet) {
        const badgeDelta = Number(state.tasking.badgeCount) - previousBadge
        const mentionDelta = Number(state.tasking.stats.unreadMentions || 0) - previousMentions
        if (badgeDelta > 0) {
          notifyInfo(`تسکینگ: ${badgeDelta} مورد جدید نیازمند توجه`)
          playInboxAlertSound({ isHq: Boolean(state.currentUser.isHq) })
        } else if (mentionDelta > 0) {
          notifyInfo(`منشن جدید در تسکینگ: ${mentionDelta}`)
        }
      } else if (hadLoaded && !soft && Number(state.tasking.badgeCount) > previousBadge) {
        const delta = Number(state.tasking.badgeCount) - previousBadge
        notifyInfo(`تسکینگ: ${delta} مورد جدید نیازمند توجه`)
        playInboxAlertSound({ isHq: Boolean(state.currentUser.isHq) })
      }
      return state.tasking
    } catch (error) {
      if (!soft) {
        state.tasking.error = error.message || 'بارگذاری تسکینگ ناموفق بود.'
        setLastError(error, 'بارگذاری تسکینگ ناموفق بود.')
        throw error
      }
      return state.tasking
    } finally {
      if (!soft) state.tasking.loading = false
    }
  }

  async function loadTaskDetail(taskId) {
    state.tasking.detailLoading = true
    try {
      const response = await authorizedFetch(`/tasking/tasks/${taskId}`)
      state.tasking.selectedTask = repairPayload(await response.json())
      modalState.taskDetail = true
      return state.tasking.selectedTask
    } catch (error) {
      setLastError(error, 'جزئیات تسک بارگذاری نشد.')
      throw error
    } finally {
      state.tasking.detailLoading = false
    }
  }

  async function previewTaskSchedule(payload) {
    const response = await authorizedFetch('/tasking/schedule/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    state.tasking.schedulePreview = repairPayload(await response.json())
    return state.tasking.schedulePreview
  }

  async function createTaskingTask(payload, files = []) {
    state.tasking.submitting = true
    clearLastError()
    try {
      const hasFiles = Array.isArray(files) && files.length > 0
      let response
      if (hasFiles) {
        const formData = new FormData()
        Object.entries(payload || {}).forEach(([key, value]) => {
          if (value === undefined || value === null || value === '') return
          if (Array.isArray(value)) {
            formData.append(key, JSON.stringify(value))
            return
          }
          if (typeof value === 'boolean') {
            formData.append(key, value ? '1' : '0')
            return
          }
          formData.append(key, String(value))
        })
        files.forEach((file) => formData.append('attachments', file))
        response = await authorizedFetch('/tasking/tasks', { method: 'POST', body: formData })
      } else {
        response = await authorizedFetch('/tasking/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload || {}),
        })
      }
      const task = repairPayload(await response.json())
      await loadTaskingDashboard(true)
      return task
    } catch (error) {
      setLastError(error, 'ثبت تسک ناموفق بود.')
      throw error
    } finally {
      state.tasking.submitting = false
    }
  }

  async function taskingAction(taskId, action, body = {}) {
    clearLastError()
    state.tasking.submitting = true
    try {
      const response = await authorizedFetch(`/tasking/tasks/${taskId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const task = repairPayload(await response.json())
      state.tasking.selectedTask = task
      await loadTaskingDashboard(true)
      return task
    } catch (error) {
      setLastError(error, 'انجام عملیات تسک ناموفق بود.')
      throw error
    } finally {
      state.tasking.submitting = false
    }
  }

  async function acceptTask(taskId, additionalMinutes = 0) {
    return taskingAction(taskId, 'accept', { additionalMinutes: Number(additionalMinutes || 0) })
  }

  async function rejectTask(taskId, reason) {
    return taskingAction(taskId, 'reject', { reason })
  }

  async function startTask(taskId, stopOther = false, additionalMinutes = 0) {
    return taskingAction(taskId, 'start', {
      stopOther,
      additionalMinutes: Number(additionalMinutes || 0),
    })
  }

  async function pauseTask(taskId) {
    return taskingAction(taskId, 'pause')
  }

  async function resumeTask(taskId, stopOther = true, additionalMinutes = 0) {
    return taskingAction(taskId, 'resume', {
      stopOther,
      additionalMinutes: Number(additionalMinutes || 0),
    })
  }

  async function submitTaskReview(taskId, deliveryNote = '') {
    return taskingAction(taskId, 'submit-review', { deliveryNote })
  }

  async function approveTask(taskId, comment = '', additionalMinutes = 0) {
    return taskingAction(taskId, 'approve', {
      comment,
      additionalMinutes: Number(additionalMinutes || 0),
    })
  }

  async function requestTaskChanges(taskId, comment = '', additionalMinutes = 0) {
    return taskingAction(taskId, 'request-changes', {
      comment,
      additionalMinutes: Number(additionalMinutes || 0),
    })
  }

  async function addTaskComment(taskId, body, mentionIds = [], parentId = null) {
    const response = await authorizedFetch(`/tasking/tasks/${taskId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body, mentionIds, parentId }),
    })
    const comment = repairPayload(await response.json())
    if (state.tasking.selectedTask?.id === Number(taskId)) {
      await loadTaskDetail(taskId)
    }
    await loadTaskingDashboard(true)
    return comment
  }

  async function markTaskMentionsRead(taskId) {
    const response = await authorizedFetch(`/tasking/tasks/${taskId}/mentions/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    const payload = repairPayload(await response.json())
    if (payload.task) {
      state.tasking.selectedTask = payload.task
    }
    await loadTaskingDashboard(true)
    return payload
  }

  async function updateTaskingTask(taskId, payload = {}) {
    clearLastError()
    state.tasking.submitting = true
    try {
      const response = await authorizedFetch(`/tasking/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const task = repairPayload(await response.json())
      state.tasking.selectedTask = task
      await loadTaskingDashboard(true, '', { soft: true })
      return task
    } catch (error) {
      setLastError(error, 'به‌روزرسانی تسک ناموفق بود.')
      throw error
    } finally {
      state.tasking.submitting = false
    }
  }

  async function loadTaskingSettings() {
    const response = await authorizedFetch('/tasking/settings')
    state.tasking.settings = repairPayload(await response.json())
    return state.tasking.settings
  }

  async function saveTaskingSettings(payload) {
    const response = await authorizedFetch('/tasking/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    state.tasking.settings = repairPayload(await response.json())
    return state.tasking.settings
  }

  async function loadTaskingReports(params = {}) {
    state.tasking.reportsLoading = true
    try {
      const query = new URLSearchParams()
      if (params.start) query.set('start', params.start)
      if (params.end) query.set('end', params.end)
      if (params.userId) query.set('userId', params.userId)
      const response = await authorizedFetch(`/tasking/reports?${query.toString()}`)
      state.tasking.reports = repairPayload(await response.json())
      return state.tasking.reports
    } finally {
      state.tasking.reportsLoading = false
    }
  }

  singleton = {
    state,
    modalState,
    requestDetailState,
    expenseDetailState,
    approvalDetailState,
    signatureState,
    selectedRequest,
    selectedExpense,
    selectedApproval,
    selectedRequestTimeline,
    canApproveSelectedRequest,
    canApproveSelectedExpense,
    filteredRequests,
    filteredExpenses,
    filteredApprovals,
    approvalInbox,
    approvalHistory,
    filteredReports,
    filteredUsers,
    requestPeople,
    requestManagerAssigneeOptions,
    expensePeople,
    approvalPeople,
    reportPeople,
    userPeople,
    canManageUsers,
    canViewReports,
    canAccessApprovals,
    canApproveDocuments,
    isLicenseLocked,
    canAccessCloud,
    visibleNavItems,
    priorityLabel,
    departmentLabel,
    managerLabel,
    availableManagerDirectory,
    availableRecipientUsers,
    requestManagerAssigneeNames,
    requestEmployeeAssigneeNames,
    setRequestManager,
    navigateTo,
    toggleSidebar,
    updatePageFilter,
    resetPageFilters,
    clearLastError,
    setLastError,
    fieldHasError,
    login,
    registerOrganization,
    submitSupportRegistrationApproval,
    logout,
    restoreSession,
    ensureAuthenticatedRedirect,
    loadBootstrapData,
    softLiveSync,
    loadReports,
    loadSettings,
    loadWalletDashboard,
    loadWalletOptions,
    submitFeaturePurchase,
    payFeatureInstallment,
    submitWalletTransaction,
    loadSupportTickets,
    loadSupportTicketDetail,
    createSupportTicket,
    submitSupportReply,
    submitSupportFeedback,
    submitSupportWalletDeposit,
    submitSupportBankWithdrawComplete,
    loadHqTickets,
    loadHqTicketDetail,
    submitHqTicketReply,
    loadHqTeam,
    createHqTeamMember,
    updateHqTeamMember,
    deleteHqTeamMember,
    supportUnreadCount,
    chatUnreadCount,
    taskingBadgeCount,
    loadChatUnreadConversations,
    loadTaskingDashboard,
    loadTaskDetail,
    openTaskComposer,
    closeTaskComposer,
    openTaskDetail,
    closeTaskDetail,
    previewTaskSchedule,
    createTaskingTask,
    acceptTask,
    rejectTask,
    startTask,
    pauseTask,
    resumeTask,
    submitTaskReview,
    approveTask,
    requestTaskChanges,
    addTaskComment,
    markTaskMentionsRead,
    updateTaskingTask,
    loadTaskingSettings,
    saveTaskingSettings,
    loadTaskingReports,
    requestInboxCount,
    expenseInboxCount,
    approvalInboxCount,
    markSupportTicketsSeen,
    loadHqPanel,
    selectHqOrganization,
    createHqOrganization,
    saveSettings,
    saveHqEntity,
    exportReport,
    openProtectedFile,
    downloadProtectedFile,
    createProtectedObjectUrl,
    openRequestDetail,
    closeRequestDetail,
    openExpenseDetail,
    closeExpenseDetail,
    openApprovalDetail,
    closeApprovalDetail,
    openRequestComposer,
    closeRequestComposer,
    openExpenseComposer,
    closeExpenseComposer,
    openUserComposer,
    closeUserComposer,
    openDocumentComposer,
    closeDocumentComposer,
    openSignatureComposer,
    closeSignatureComposer,
    loadSignature,
    setRequestFiles,
    removeAttachment,
    setExpenseInvoice,
    setDocumentFile,
    submitRequest,
    submitExpense,
    submitUser,
    uploadOwnAvatar,
    clearOwnAvatar,
    submitDocument,
    saveSignature,
    approveSelectedRequest,
    rejectSelectedRequest,
    referSelectedRequest,
    approveSelectedExpense,
    rejectSelectedExpense,
    referSelectedExpense,
    updateUser,
    addUserEntrustedItem,
    removeUserEntrustedItem,
    formatMoneyInputValue,
    approveSelectedDocument,
    rejectSelectedDocument,
    referSelectedDocument,
  }

  return singleton
}





