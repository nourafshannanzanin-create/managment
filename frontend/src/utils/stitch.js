const SUSPECT_TEXT_RE = /[\u00C3\u00C2\u00D8\u00D9\u00DA\u00DB]/

export function repairText(value) {
  if (typeof value !== 'string' || !SUSPECT_TEXT_RE.test(value)) return value

  let current = value
  for (let index = 0; index < 3; index += 1) {
    try {
      const bytes = Uint8Array.from(current, (char) => char.charCodeAt(0) & 0xff)
      const next = new TextDecoder('utf-8').decode(bytes)
      if (next === current) break
      current = next
      if (!SUSPECT_TEXT_RE.test(current)) break
    } catch {
      break
    }
  }

  return current
}

function normalizeDisplayText(value) {
  return repairText(String(value ?? ''))
    .replaceAll('\u0622\u0631\u0645\u0627\u0646 \u06A9\u0631\u06CC\u0645\u06CC', '\u0627\u0645\u06CC\u062F \u06A9\u0631\u06CC\u0645\u06CC')
    .replaceAll('\u062B\u0628\u062A \u06A9\u0646\u0646\u062F\u0647', '- \u062B\u0628\u062A\u200C\u06A9\u0646\u0646\u062F\u0647 -')
    .replaceAll('\u062B\u0628\u062A\u200C\u06A9\u0646\u0646\u062F\u0647', '- \u062B\u0628\u062A\u200C\u06A9\u0646\u0646\u062F\u0647 -')
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
  if (/\u0631\u062F|\u063A\u06CC\u0631\u0641\u0639\u0627\u0644/.test(label)) return 'bg-error-container text-on-error-container'
  if (/\u062A\u0627\u06CC\u06CC\u062F|\u0641\u0639\u0627\u0644/.test(label)) return 'bg-[rgba(229,195,166,0.32)] text-primary'
  if (/\u0628\u0631\u0631\u0633\u06CC|\u0627\u0646\u062A\u0638\u0627\u0631/.test(label)) return 'bg-[rgba(124,129,173,0.2)] text-[#4B527E]'
  return 'bg-surface-container-highest text-on-surface-variant'
}

export function priorityTone(priority) {
  const label = repairText(String(priority || ''))
  if (/\u0628\u0627\u0644\u0627|\u0628\u062D\u0631\u0627\u0646\u06CC/.test(label)) return 'bg-error'
  if (/\u067E\u0627\u06CC\u06CC\u0646/.test(label)) return 'bg-emerald-500'
  return 'bg-yellow-500'
}

export function wirePageNavigation(root, navigateTo, activePath, items = []) {
  void navigateTo
  void activePath
  void items
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
    const hasOperationsTitle = text.includes('\u0645\u062F\u06CC\u0631\u06CC\u062A \u0639\u0645\u0644\u06CC\u0627\u062A')
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
    const hasTopbarText = text.includes('\u0645\u062F\u06CC\u0631\u06CC\u062A \u0639\u0645\u0644\u06CC\u0627\u062A')
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
    if (text === '\u0645\u062F\u06CC\u0631\u06CC\u062A \u0639\u0645\u0644\u06CC\u0627\u062A') {
      node.textContent = ''
      return
    }
    if (text === '\u0622\u0631\u0645\u0627\u0646 \u06A9\u0631\u06CC\u0645\u06CC') {
      node.textContent = '\u0627\u0645\u06CC\u062F \u06A9\u0631\u06CC\u0645\u06CC'
      return
    }
    if (text === '\u062B\u0628\u062A \u06A9\u0646\u0646\u062F\u0647' || text === '\u062B\u0628\u062A\u200C\u06A9\u0646\u0646\u062F\u0647') {
      node.textContent = '- \u062B\u0628\u062A\u200C\u06A9\u0646\u0646\u062F\u0647 -'
    }
  })

  root.querySelectorAll('header h1, header .font-headline-md, header .text-headline-md').forEach((node) => {
    const text = repairText((node.textContent || '').trim())
    if (text === '\u0645\u062F\u06CC\u0631\u06CC\u062A \u0639\u0645\u0644\u06CC\u0627\u062A') node.textContent = ''
  })

  main.style.minHeight = '100vh'
}

export async function loadStitchBody(stitchId) {
  const response = await fetch('/stitch/' + stitchId + '/code.html', { cache: 'no-store' })
  if (!response.ok) throw new Error('stitch/' + stitchId + '/code.html returned ' + response.status)
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
  const styleTag = inlineStyles ? '<style>' + inlineStyles + '</style>' : ''
  const bodyWrapperOpen = bodyClassName ? '<div class="' + escapeHtml(bodyClassName) + '">' : ''
  const bodyWrapperClose = bodyClassName ? '</div>' : ''

  return {
    html: styleTag + bodyWrapperOpen + documentNode.body.innerHTML + bodyWrapperClose,
    head: {
      title: repairText(documentNode.title || '').replace(/\u0645\u062F\u06CC\u0631\u06CC\u062A \u0639\u0645\u0644\u06CC\u0627\u062A/g, '').replace(/\s+\|\s+/g, ' | ').trim(),
      links,
    },
  }
}