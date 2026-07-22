import home from '../assets/iconly/home.svg'
import users3 from '../assets/iconly/users-3.svg'
import document from '../assets/iconly/document.svg'
import calendar from '../assets/iconly/calendar.svg'
import setting from '../assets/iconly/setting.svg'
import wallet from '../assets/iconly/wallet.svg'
import chat from '../assets/iconly/chat.svg'
import search from '../assets/iconly/search.svg'
import filter from '../assets/iconly/filter.svg'
import plus from '../assets/iconly/plus.svg'
import editSquare from '../assets/iconly/edit-square.svg'
import trash from '../assets/iconly/delete.svg'
import logout from '../assets/iconly/logout.svg'
import profile from '../assets/iconly/profile.svg'
import graph from '../assets/iconly/graph.svg'
import category from '../assets/iconly/category.svg'
import message from '../assets/iconly/message.svg'
import show from '../assets/iconly/show.svg'
import buy from '../assets/iconly/buy.svg'
import paperPlus from '../assets/iconly/paper-plus.svg'

export const iconlyIcons = {
  home,
  users3,
  document,
  calendar,
  setting,
  wallet,
  chat,
  search,
  filter,
  plus,
  editSquare,
  trash,
  logout,
  profile,
  graph,
  category,
  message,
  show,
  buy,
  paperPlus,
}

export const materialToIconly = {
  account_balance: 'wallet',
  account_balance_wallet: 'wallet',
  add: 'plus',
  add_card: 'wallet',
  add_circle: 'plus',
  admin_panel_settings: 'setting',
  apartment: 'category',
  approval: 'paperPlus',
  arrow_back: 'category',
  assignment: 'document',
  assignment_late: 'document',
  attach_file: 'document',
  attach_file_off: 'document',
  award_star: 'graph',
  badge: 'profile',
  balance: 'wallet',
  bolt: 'graph',
  business: 'category',
  calendar_month: 'calendar',
  cancel: 'trash',
  category: 'category',
  chat: 'chat',
  check: 'plus',
  check_circle: 'plus',
  chevron_left: 'category',
  chevron_right: 'category',
  close: 'trash',
  cloud: 'document',
  cloud_upload: 'paperPlus',
  content_copy: 'document',
  corporate_fare: 'category',
  credit_card: 'wallet',
  dashboard: 'home',
  database: 'document',
  date_range: 'calendar',
  delete: 'trash',
  description: 'document',
  domain: 'category',
  domain_add: 'plus',
  download: 'document',
  draw: 'editSquare',
  edit_document: 'editSquare',
  error: 'message',
  event_available: 'calendar',
  event_upcoming: 'calendar',
  expand_more: 'category',
  fact_check: 'paperPlus',
  filter_alt_off: 'filter',
  flag: 'category',
  folder_copy: 'document',
  folder_managed: 'document',
  folder_open: 'document',
  forum: 'chat',
  forward: 'message',
  gavel: 'setting',
  gesture: 'editSquare',
  group: 'users3',
  group_add: 'users3',
  group_off: 'users3',
  groups: 'users3',
  home: 'home',
  hourglass_empty: 'calendar',
  hourglass_top: 'calendar',
  inbox: 'message',
  ink_eraser: 'editSquare',
  input: 'document',
  list_alt: 'document',
  lock: 'setting',
  login: 'logout',
  logout: 'logout',
  mail: 'message',
  manage_search: 'search',
  mark_chat_read: 'chat',
  menu: 'category',
  monitoring: 'graph',
  north_east: 'wallet',
  open_in_new: 'show',
  paper_plus: 'paperPlus',
  payments: 'wallet',
  pending_actions: 'calendar',
  person: 'profile',
  person_add: 'users3',
  person_check: 'profile',
  person_off: 'profile',
  person_search: 'search',
  picture_as_pdf: 'document',
  priority_high: 'category',
  progress_activity: 'calendar',
  radio_button_checked: 'plus',
  radio_button_unchecked: 'category',
  receipt_long: 'document',
  refresh: 'filter',
  restart_alt: 'filter',
  rule: 'setting',
  save: 'paperPlus',
  schedule: 'calendar',
  search: 'search',
  sell: 'buy',
  send: 'message',
  settings: 'setting',
  shopping_cart: 'buy',
  shopping_cart_checkout: 'buy',
  smart_phone: 'profile',
  smartphone: 'profile',
  sms: 'message',
  sms_failed: 'message',
  south_west: 'wallet',
  space_dashboard: 'home',
  supervisor_account: 'users3',
  support_agent: 'chat',
  sync: 'filter',
  table_chart: 'graph',
  task: 'paperPlus',
  task_alt: 'plus',
  today: 'calendar',
  upload_file: 'paperPlus',
  verified: 'plus',
  verified_user: 'profile',
  visibility: 'show',
  warning: 'message',
  workspace_premium: 'graph',
}

export function resolveIconName(name) {
  const iconName = String(name || '').trim()
  if (Object.prototype.hasOwnProperty.call(iconlyIcons, iconName)) return iconName
  return materialToIconly[iconName] || 'category'
}

export function iconSrc(name) {
  return iconlyIcons[resolveIconName(name)]
}
