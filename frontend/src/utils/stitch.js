export function repairText(value) {
  if (typeof value !== 'string' || !/[Ã˜Ã™Ã›]/.test(value)) return value
  try {
    const bytes = Uint8Array.from(value, (char) => char.charCodeAt(0) & 0xff)
    return new TextDecoder('utf-8').decode(bytes)
  } catch {
    return value
  }
}

function normalizeDisplayText(value) {
  return String(value ?? '')
    .replaceAll('آرمان کریمی', 'امید کریمی')
    .replaceAll('ثبت کننده', '- ثبت‌کننده -')
    .replaceAll('ثبت‌کننده', '- ثبت‌کننده -')
}

export function repairPayload(value) {
  if (typeof value === 'string') return repairText(value)
  if (Array.isArray(value)) return value.map((item) => repairPayload(item))
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, repairPayload(item)]))
  }
  return value
}

export function escapeHtml(value) {
  return normalizeDisplayText(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

export function statusTone(status) {
  const label = repairText(String(status || ''))
  if (/رد|غیرفعال/.test(label)) return 'bg-error-container text-on-error-container'
  if (/تایید|فعال/.test(label)) return 'bg-[#e7f3f3] text-primary'
  if (/بررسی|انتظار/.test(label)) return 'bg-[#fff9e6] text-[#b48900]'
  return 'bg-surface-container-highest text-on-surface-variant'
}

export function priorityTone(priority) {
  const label = repairText(String(priority || ''))
  if (/بالا|بحرانی/.test(label)) return 'bg-error'
  if (/پایین/.test(label)) return 'bg-emerald-500'
  return 'bg-yellow-500'
}

export function wirePageNavigation(root, navigateTo, activePath, items = []) {
  root.querySelectorAll('.runtime-page-nav, nav.fixed.bottom-0, nav[class*="bottom-0"]').forEach((node) => node.remove())
}

export function setSearchValue(root, selector, value, onInput) {
  const input = root.querySelector(selector)
  if (!input) return
  input.value = value || ''
  input.oninput = (event) => onInput(event.target.value)
}

export function formatMetric(value, fallback = '0') {
  return repairText(String(value || fallback))
}

let activeStitchHeadNodes = []

export function applyStitchHead(head = {}) {
  activeStitchHeadNodes.forEach((node) => node.remove())
  activeStitchHeadNodes = []

  if (head.title) document.title = head.title

  ;(head.links || []).forEach((href) => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = href
    link.dataset.stitchHead = 'true'
    document.head.appendChild(link)
    activeStitchHeadNodes.push(link)
  })
}

export function prepareStitchShell(root) {
  root.querySelectorAll('nav.fixed.bottom-0, nav[class*="bottom-0"]').forEach((node) => node.remove())
  root
    .querySelectorAll(
      'header.fixed.top-0, header[class*="top-0"][class*="fixed"], header.sticky.top-0, header[class*="top-0"][class*="sticky"], header[class*="h-16"][class*="shadow-sm"]',
    )
    .forEach((node) => node.remove())
  root.querySelectorAll('header').forEach((node) => {
    const text = repairText((node.textContent || '').trim())
    const hasOperationsTitle = text.includes('مدیریت عملیات') || text.includes('مدیرت عملیات')
    const hasNotificationIcon = /(notifications)/.test(
      Array.from(node.querySelectorAll('[data-icon], .material-symbols-outlined'))
        .map((item) => item.textContent || item.getAttribute('data-icon') || '')
        .join(' '),
    )
    const isTopHeader =
      node.classList.contains('sticky') ||
      node.classList.contains('fixed') ||
      Array.from(node.classList).some((item) => item.includes('top-0'))
    if (isTopHeader && hasOperationsTitle && hasNotificationIcon) node.remove()
  })
  root.querySelectorAll('header > div, section > div > header > div').forEach((node) => {
    const text = repairText((node.textContent || '').trim())
    const hasTopbarText = text.includes('مدیریت عملیات') || text.includes('مدیرت عملیات')
    const hasActionIcons =
      node.querySelector('button') &&
      /(notifications|search)/.test(Array.from(node.querySelectorAll('button')).map((item) => item.textContent || '').join(' '))
    if (hasTopbarText && hasActionIcons) node.remove()
  })

  const main = root.querySelector(':scope > main')
  if (!main) return

  root.querySelectorAll('h1, h2, h3, h4, p, span, small, strong, title').forEach((node) => {
    if (node.children.length) return
    const text = repairText((node.textContent || '').trim())
    if (text === 'مدیریت عملیات' || text === 'مدیرت عملیات') {
      node.textContent = ''
      return
    }
    if (text === 'آرمان کریمی') {
      node.textContent = 'امید کریمی'
      return
    }
    if (text === 'ثبت کننده' || text === 'ثبت‌کننده') {
      node.textContent = '- ثبت‌کننده -'
    }
  })

  root.querySelectorAll('header h1, header .font-headline-md, header .text-headline-md').forEach((node) => {
    const text = repairText((node.textContent || '').trim())
    if (text === 'مدیریت عملیات' || text === 'مدیرت عملیات') node.textContent = ''
  })

  main.style.minHeight = '100vh'
}

export async function loadStitchBody(stitchId) {
  const response = await fetch(`/stitch/${stitchId}/code.html`, { cache: 'no-store' })
  if (!response.ok) throw new Error(`stitch/${stitchId}/code.html returned ${response.status}`)
  const html = repairText(await response.text())
  const documentNode = new DOMParser().parseFromString(html, 'text/html')
  documentNode.querySelectorAll('script').forEach((node) => node.remove())

  const links = Array.from(documentNode.querySelectorAll('link[rel="stylesheet"]'))
    .map((node) => node.getAttribute('href') || '')
    .filter(Boolean)

  const inlineStyles = Array.from(documentNode.querySelectorAll('style'))
    .map((node) => node.textContent || '')
    .filter(Boolean)
    .join('\n')

  const bodyClassName = documentNode.body.getAttribute('class') || ''
  const styleTag = inlineStyles ? `<style>${inlineStyles}</style>` : ''
  const bodyWrapperOpen = bodyClassName ? `<div class="${escapeHtml(bodyClassName)}">` : ''
  const bodyWrapperClose = bodyClassName ? '</div>' : ''

  return {
    html: `${styleTag}${bodyWrapperOpen}${documentNode.body.innerHTML}${bodyWrapperClose}`,
    head: {
      title: repairText(documentNode.title || '').replace(/مدیریت عملیات/g, '').replace(/\s+\|\s+/g, ' | ').trim(),
      links,
    },
  }
}
