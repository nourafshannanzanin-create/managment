/**
 * Central app navigation — slim sidebar hubs + in-page tabs.
 * Keeps route paths stable (/users, /tasking, …) while grouping UX.
 */

export const PEOPLE_HUB_ID = 'people'
export const DOCUMENTS_HUB_ID = 'documents'

const PEOPLE_PATHS = ['/users', '/tasking', '/chat', '/attendance']
const DOCUMENT_PATHS = ['/expenses', '/approvals', '/archive']

function userOf(state) {
  return state?.currentUser || {}
}

function canSeeUsers(user) {
  return Boolean(user.canAccessUsers || user.canManageUsers)
}

function canSeeAttendance(user) {
  return Boolean(
    user.isHq ||
    (user.canAccessAttendance !== false && user.menuAccess?.attendance === true),
  )
}

function canSeeExpenses(user) {
  return user.canAccessExpenses !== false
}

function canSeeArchive(user) {
  return user.canAccessArchive !== false
}

function canSeeWallet(user) {
  return Boolean(user.isManager || user.canUseHq)
}

function canSeeReports(user) {
  return Boolean(user.canViewReports)
}

function canSeeSettings(user) {
  return Boolean(user.canAccessSettings || user.canManageUsers)
}

function canSeeSupport(user) {
  return Boolean(user.isHq || user.accessRole === 'admin')
}

function formatBadge(value) {
  const n = Number(value || 0)
  if (!n) return ''
  if (n > 99) return '۹۹+'
  return String(n)
}

export function isPeopleHubPath(path = '') {
  return PEOPLE_PATHS.some((p) => path === p || path.startsWith(`${p}/`))
}

export function isDocumentsHubPath(path = '') {
  return DOCUMENT_PATHS.some((p) => path === p || path.startsWith(`${p}/`))
}

export function buildPeopleTabs(state, badges = {}) {
  const user = userOf(state)
  const tabs = []

  if (canSeeUsers(user)) {
    tabs.push({ id: 'users', to: '/users', label: 'کاربران', icon: 'groups' })
  }

  tabs.push({
    id: 'tasking',
    to: '/tasking',
    label: 'تسکینگ',
    icon: 'task_alt',
    badge: badges.tasking,
  })
  tabs.push({
    id: 'chat',
    to: '/chat',
    label: 'گفتگو',
    icon: 'forum',
    badge: badges.chat,
  })

  if (canSeeAttendance(user)) {
    tabs.push({ id: 'attendance', to: '/attendance', label: 'ورود و خروج', icon: 'badge' })
  }

  return tabs.map((tab) => ({ ...tab, badgeLabel: formatBadge(tab.badge) }))
}

export function buildDocumentsTabs(state, badges = {}) {
  const user = userOf(state)
  const tabs = []

  if (canSeeExpenses(user)) {
    tabs.push({
      id: 'expenses',
      to: '/expenses',
      label: 'هزینه‌ها',
      icon: 'payments',
      badge: badges.expenses,
    })
  }

  tabs.push({
    id: 'approvals',
    to: '/approvals',
    label: 'تاییدیه‌ها',
    icon: 'fact_check',
    badge: badges.approvals,
  })

  if (canSeeArchive(user)) {
    tabs.push({ id: 'archive', to: '/archive', label: 'بایگانی', icon: 'folder_open' })
  }

  return tabs.map((tab) => ({ ...tab, badgeLabel: formatBadge(tab.badge) }))
}

export function peopleHubEntry(state, badges = {}) {
  const tabs = buildPeopleTabs(state, badges)
  return tabs[0]?.to || '/tasking'
}

export function documentsHubEntry(state, badges = {}) {
  const tabs = buildDocumentsTabs(state, badges)
  return tabs[0]?.to || '/approvals'
}

export function resolveActiveHub(path = '') {
  if (isPeopleHubPath(path)) return PEOPLE_HUB_ID
  if (isDocumentsHubPath(path)) return DOCUMENTS_HUB_ID
  return null
}

/**
 * Slim primary sidebar (desktop).
 */
export function buildMainNavItems(state, badges = {}) {
  const user = userOf(state)
  const items = []

  if (user.isHq && !user.isHqAdmin) {
    items.push({ id: 'hq', to: '/hq', label: 'میز پشتیبانی', icon: 'support_agent', badge: badges.support })
    items.push({ id: 'chat', to: '/chat', label: 'گفتگو', icon: 'forum', badge: badges.chat })
    return items.map((item) => ({ ...item, badgeLabel: formatBadge(item.badge) }))
  }

  items.push({ id: 'dashboard', to: '/dashboard', label: 'داشبورد', icon: 'space_dashboard' })

  const licenseLocked = Boolean(user.licenseStatus?.isLocked || user.licenseStatus?.is_locked)
  if (licenseLocked) {
    items.push({ id: 'wallet', to: '/wallet', label: 'خرید نرم‌افزار', icon: 'shopping_cart' })
    if (canSeeSettings(user) || canSeeSupport(user)) {
      items.push({ id: 'settings', to: '/settings', label: 'تنظیمات', icon: 'settings', badge: badges.support })
    }
    return items.map((item) => ({ ...item, badgeLabel: formatBadge(item.badge) }))
  }

  const peopleTabs = buildPeopleTabs(state, badges)
  if (peopleTabs.length) {
    const peopleBadge = Number(badges.tasking || 0) + Number(badges.chat || 0)
    items.push({
      id: PEOPLE_HUB_ID,
      to: peopleHubEntry(state, badges),
      label: 'کارمندان',
      icon: 'groups',
      hub: PEOPLE_HUB_ID,
      matchPaths: PEOPLE_PATHS,
      badge: peopleBadge || undefined,
    })
  }

  items.push({
    id: 'requests',
    to: '/requests',
    label: 'درخواست‌ها',
    icon: 'assignment',
    badge: badges.requests,
  })

  const docTabs = buildDocumentsTabs(state, badges)
  if (docTabs.length) {
    const docsBadge = Number(badges.approvals || 0) + Number(badges.expenses || 0)
    items.push({
      id: DOCUMENTS_HUB_ID,
      to: documentsHubEntry(state, badges),
      label: 'اسناد',
      icon: 'folder_copy',
      hub: DOCUMENTS_HUB_ID,
      matchPaths: DOCUMENT_PATHS,
      badge: docsBadge || undefined,
    })
  }

  if (canSeeWallet(user)) {
    items.push({ id: 'wallet', to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' })
  }

  if (canSeeReports(user)) {
    items.push({ id: 'reports', to: '/reports', label: 'گزارشات', icon: 'monitoring' })
  }

  if (canSeeSettings(user)) {
    items.push({
      id: 'settings',
      to: '/settings',
      label: 'تنظیمات',
      icon: 'settings',
      badge: canSeeSupport(user) ? badges.support : undefined,
    })
  }

  if (user.canUseHq) {
    items.push({ id: 'hq', to: '/hq', label: 'HQ', icon: 'admin_panel_settings', badge: badges.support })
  }

  return items.map((item) => ({ ...item, badgeLabel: formatBadge(item.badge) }))
}

/**
 * Mobile dock — max 5 slots, aligned with hubs.
 */
export function buildMobileNavItems(state, badges = {}) {
  const user = userOf(state)

  if (user.isHq && !user.isHqAdmin) {
    return [
      { to: '/hq', label: 'پشتیبانی', shortLabel: 'HQ', icon: 'support_agent', badge: badges.support },
      { to: '/chat', label: 'گفتگو', shortLabel: 'گفتگو', icon: 'forum', badge: badges.chat },
    ].map((item) => ({ ...item, badgeLabel: formatBadge(item.badge) }))
  }

  const licenseLocked = Boolean(user.licenseStatus?.isLocked || user.licenseStatus?.is_locked)
  if (licenseLocked) {
    return [
      { to: '/dashboard', label: 'خانه', shortLabel: 'خانه', icon: 'home' },
      { to: '/wallet', label: 'کیف', shortLabel: 'کیف', icon: 'account_balance_wallet' },
      { to: '/settings', label: 'تنظیمات', shortLabel: 'تنظیم', icon: 'settings', badge: badges.support },
    ].map((item) => ({ ...item, badgeLabel: formatBadge(item.badge) }))
  }

  const items = [
    { to: '/dashboard', label: 'داشبورد', shortLabel: 'خانه', icon: 'home' },
    {
      to: peopleHubEntry(state, badges),
      label: 'کارمندان',
      shortLabel: 'کارمند',
      icon: 'groups',
      matchPaths: PEOPLE_PATHS,
      badge: Number(badges.tasking || 0) + Number(badges.chat || 0) || undefined,
    },
    {
      to: '/requests',
      label: 'درخواست‌ها',
      shortLabel: 'درخواست',
      icon: 'assignment',
      badge: badges.requests,
    },
    {
      to: documentsHubEntry(state, badges),
      label: 'اسناد',
      shortLabel: 'اسناد',
      icon: 'folder_copy',
      matchPaths: DOCUMENT_PATHS,
      badge: Number(badges.approvals || 0) + Number(badges.expenses || 0) || undefined,
    },
  ]

  if (canSeeSettings(user)) {
    items.push({
      to: '/settings',
      label: 'تنظیمات',
      shortLabel: 'تنظیم',
      icon: 'settings',
      badge: canSeeSupport(user) ? badges.support : undefined,
    })
  } else if (canSeeWallet(user)) {
    items.push({ to: '/wallet', label: 'کیف پول', shortLabel: 'کیف', icon: 'account_balance_wallet' })
  } else if (canSeeReports(user)) {
    items.push({ to: '/reports', label: 'گزارشات', shortLabel: 'گزارش', icon: 'monitoring' })
  }

  return items.slice(0, 5).map((item) => ({ ...item, badgeLabel: formatBadge(item.badge) }))
}

export function isNavItemActive(item, path = '') {
  if (!item) return false
  if (Array.isArray(item.matchPaths) && item.matchPaths.length) {
    return item.matchPaths.some((p) => path === p || path.startsWith(`${p}/`))
  }
  if (path === item.to) return true
  return item.to !== '/dashboard' && path.startsWith(`${item.to}/`)
}

export function hubTabsForPath(path, state, badges = {}) {
  if (isPeopleHubPath(path)) return { hub: PEOPLE_HUB_ID, title: 'کارمندان', tabs: buildPeopleTabs(state, badges) }
  if (isDocumentsHubPath(path)) {
    return { hub: DOCUMENTS_HUB_ID, title: 'اسناد', tabs: buildDocumentsTabs(state, badges) }
  }
  return null
}

export function canOpenSupport(state) {
  return canSeeSupport(userOf(state))
}
