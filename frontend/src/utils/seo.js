const SITE_URL = 'https://carnomand.ir'

const DEFAULT_META = {
  title: 'کارنومند',
  description: 'سامانه کارنومند',
  robots: 'noindex, nofollow',
  canonicalPath: false,
}

function upsertMeta(selector, attrs) {
  let element = document.head.querySelector(selector)
  if (!element) {
    element = document.createElement('meta')
    document.head.appendChild(element)
  }
  Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value))
}

function upsertCanonical(href) {
  let element = document.head.querySelector('link[rel="canonical"]')
  if (!element) {
    element = document.createElement('link')
    element.setAttribute('rel', 'canonical')
    document.head.appendChild(element)
  }
  element.setAttribute('href', href)
}

export function applyRouteSeo(route) {
  const meta = { ...DEFAULT_META, ...(route.meta?.seo || {}) }
  const canonicalUrl = meta.canonicalPath === false
    ? null
    : new URL(meta.canonicalPath || route.path || '/', SITE_URL).toString()

  document.title = meta.title
  upsertMeta('meta[name="description"]', { name: 'description', content: meta.description })
  upsertMeta('meta[name="robots"]', { name: 'robots', content: meta.robots })
  if (canonicalUrl) {
    upsertCanonical(canonicalUrl)
  } else {
    document.head.querySelector('link[rel="canonical"]')?.remove()
  }
  upsertMeta('meta[property="og:title"]', { property: 'og:title', content: meta.title })
  upsertMeta('meta[property="og:description"]', { property: 'og:description', content: meta.description })
  if (canonicalUrl) {
    upsertMeta('meta[property="og:url"]', { property: 'og:url', content: canonicalUrl })
  } else {
    document.head.querySelector('meta[property="og:url"]')?.remove()
  }
}
