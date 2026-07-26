# Current technical SEO audit — Carnomand

**Audited:** 2026-07-26
**Status:** Audit complete; implementation and post-change verification pending.
**Evidence scope:** Current repository, production HTTP checks, `docs/seo-analyze.md` (historical single-page report), and a production build. No Search Console, CrUX, analytics, or DNS-console access was available.

## 1. Executive summary

Carnomand is a Vue/Vite, history-mode SPA backed by Django, Gunicorn, and MySQL. Its only intended indexable page is the public landing page at `https://carnomand.ir/`; login, tokenized attendance, dashboards, reports, files, APIs, and authenticated workflows must not be indexed.

The repository contains a materially improved but un-deployed SEO implementation: a landing-page fallback, metadata, JSON-LD, robots, sitemap, and Nginx file handling. Production remains critically behind it: live `/robots.txt` and `/sitemap.xml` return the old SPA shell as `text/html`, and the landing page raw HTML lacks the source metadata and content. The initial CSS/JS payload is also large and uncompressed in production.

## 2. Current architecture

| Area | Current implementation |
|---|---|
| Frontend | Vue 3 + Vite + Vue Router `createWebHistory()` |
| Backend | Django / Gunicorn / Python 3.12 + MySQL |
| Delivery | Frontend Nginx, gateway/TLS Nginx, Docker |
| Public route | `/` |
| Public but noindex routes | `/login`, `/attendance/:token` |
| Private routes | `/dashboard`, `/requests`, `/expenses`, `/wallet`, `/attendance`, `/cloud`, `/support`, `/hq`, `/approvals`, `/reports`, `/users`, `/settings` |
| SEO implementation | `frontend/index.html`, `frontend/src/utils/seo.js`, `frontend/public/robots.txt`, `frontend/public/sitemap.xml`, `frontend/nginx/default.conf` |

SEO maturity is **partial in source but not production-ready in deployment**. Client-side route metadata is a useful UX layer, but cannot be the only delivery mechanism for private-route noindex, canonical, or 404 behavior.

## 3. Prioritized findings

| Severity | Issue | Evidence and affected route/file | Why it matters | Proposed fix | Risk | Verification |
|---|---|---|---|---|---|---|
| Critical | Production crawler files are stale/missing | Live `/robots.txt` and `/sitemap.xml` return the SPA HTML with HTTP 200 and `Content-Type: text/html`; source files exist at `frontend/public/robots.txt` and `frontend/public/sitemap.xml`, with exact handling in `frontend/nginx/default.conf`. | Crawlers cannot consume crawl policy or sitemap discovery. | Deploy the current frontend image/config, then submit the real sitemap. | Deployment only. | `curl -I` reports text/plain/XML; bodies are robots/XML, not HTML. |
| Critical | Unknown URLs are soft 404s | `frontend/nginx/default.conf` uses `try_files $uri $uri/ /index.html` for every unmatched route; there is no client catch-all. Live `/does-not-exist` is 200 HTML. | Invalid URLs waste crawl budget and can be indexed as duplicate SPA shells. | Serve the SPA only for declared UI routes; return a real 404 for unknown paths. | Must include every valid application route. | Known deep links still load; `/does-not-exist` returns 404. |
| High | Private-route controls arrive too late | `frontend/src/utils/seo.js` injects noindex/canonical after JavaScript. The raw SPA document starts as the indexable homepage. | Crawlers may act on the initial document; direct private routes cannot rely on a client mutation. | Set `X-Robots-Tag: noindex, nofollow, noarchive` in Nginx for each private route family. | Low when route list is complete. | `curl -I` for login, dashboard, attendance token, and report route. |
| High | Production landing page is client-only and stale | Live document has an empty app mount; source `frontend/index.html` includes the semantic fallback, H1, description, canonical, OG and SoftwareApplication JSON-LD. | The current live page repeats the prior report’s zero-word/no-H1 issue. | Deploy source now; plan static prerendering/SSR for the landing page. | Deploy first; prerendering is a larger architecture decision. | Compare raw source and rendered page; inspect Google URL after deployment. |
| High | Initial assets are large and lack compression in production | Live JS ~493 KB and CSS ~440 KB were served without `Content-Encoding`; `frontend/src/router/index.js` eagerly imports every page module. | Delays rendering and creates LCP/INP risk. | Lazy-load non-landing route components and verify gzip/Brotli at the edge. | Low; route chunks load on navigation. | Production build chunk report and `curl --compressed -I` on assets. |
| High | Public HTML lacks TLS-edge security headers | `deploy/nginx/carnomand.ir.ssl.conf` has no public HTML CSP/XFO/nosniff/referrer policy; Django API settings do. | Security headers reduce rendering and embedding risks; server version is exposed live. | Add safe headers at the TLS-facing vhost; introduce CSP in report-only mode first. | CSP can affect integrations if enforced without observation. | `curl -I https://carnomand.ir/`; test app flows after report-only CSP. |
| Medium | Render-blocking font is requested twice | Material Symbols is linked by `frontend/index.html` and imported again at `frontend/src/styles.css:1`. | Duplicate font work delays first render. | Keep a single preload/link strategy. | Low. | Network waterfall/build output contains one font stylesheet request. |
| Medium | Source robots omits sensitive backend paths | `frontend/public/robots.txt` lists UI routes but not `/api/`, `/uploads/`, or `/healthz`. | Robots is not access control, but explicit rules clarify crawler intent. | Add crawler blocks while retaining response-level noindex for private pages. | Low. | Inspect delivered robots and response headers. |
| Medium | Canonical-host/deployment paths disagree | `deploy/nginx/carnomand.ir.ssl.conf` declares both hosts; live `www.carnomand.ir` has no DNS response. Deployment docs and scripts also name different app paths. | Restoring `www` without a redirect risks duplicate hosts; path drift explains stale deployment. | Keep `www` absent or redirect it to apex at TLS edge; align deployment paths. | Requires DNS/server access. | DNS and `curl -IL` tests after deployment. |
| Low | Mobile menu is slightly undersized | `frontend/src/pages/LandingPage.vue` renders a 44×44px menu control. | Minor mobile accessibility and interaction risk. | Raise to at least 48×48px. | Visual-only. | Mobile viewport review. |

## 4. Route indexability matrix

| Route family | Classification | Required directive |
|---|---|---|
| `/` | Index | 200, self-canonical, `index, follow`, sitemap entry |
| `/login` | Noindex | 200 + `X-Robots-Tag: noindex, nofollow, noarchive` |
| `/attendance/:token` | Noindex | 200 + response-level noindex; never sitemap |
| Authenticated application routes listed above | Noindex | Response-level noindex; never sitemap |
| `/api/`, `/uploads/`, `/healthz` | Block from crawling / noindex | Do not expose as content; no sitemap |
| `/robots.txt`, `/sitemap.xml` | Indexing infrastructure | Correct MIME type and 200 |
| Unknown paths | Remove | HTTP 404, no SPA fallback |

## 5. Metadata matrix

| Indexable route | Title / description | Canonical | Robots | Social metadata | Status |
|---|---|---|---|---|---|
| `/` source | Unique Persian title and description in `frontend/index.html` | `https://carnomand.ir/` | `index, follow` | OG/Twitter present | Good in source; not live |
| `/` production | Old title only | Missing | Missing | Missing | Critical deployment drift |
| All private routes | Client-generated fallback metadata only | Client mutation | Client mutation | Inherits until JS | Must move noindex to HTTP response |

## 6. Structured data status

`frontend/index.html` contains `SoftwareApplication` JSON-LD for the landing page. It is syntactically valid on source inspection and appropriate only for the public product landing page. No private route should emit schema. Production currently does not serve the source markup. Validate with Google’s Rich Results Test after deployment; no rich-result eligibility is implied by this audit.

## 7. Performance and Core Web Vitals

No field CWV data was available. A single live fetch is not a CWV measurement. Source and production evidence show a performance risk: eager imports create a large initial app bundle, CSS is large, and production did not return compression. Images in the public landing source have dimensions and responsive behavior, which lowers CLS risk. The correct next measurement is PageSpeed Insights/CrUX after deployment; targets are LCP ≤2.5 s, INP ≤200 ms, and CLS ≤0.1 at the 75th percentile.

## 8. Content, internal links, images, accessibility, and AI visibility

- The source fallback provides one H1, semantic sections, Persian `lang="fa"`/`dir="rtl"`, product links, and contact context; the live HTML does not yet provide it.
- The public page has useful cross-product links, but only one indexable URL exists. New feature/use-case pages must be substantive before sitemap inclusion.
- Source image dimensions and alt behavior are broadly sound; a dedicated 1200×630 social card remains an improvement over a logo.
- Current robots allow general and AI crawlers to access the public landing page. This is compatible with AI-search visibility; private routes remain excluded. No `llms.txt` is present, which is optional and should not replace crawlable HTML.

## 9. Recommended implementation order

1. Deploy current crawler-file and landing-source changes.
2. Add Nginx route-level noindex and true 404 behavior.
3. Lazy-load private routes, remove the duplicate font import, and verify compression.
4. Add / verify TLS-edge headers and canonical-host behavior.
5. Measure CWV and plan static prerendering for the public landing page.

## 10. Files requiring modification

- `frontend/nginx/default.conf`
- `frontend/public/robots.txt`
- `frontend/src/router/index.js`
- `frontend/src/styles.css`
- `deploy/nginx/carnomand.ir.ssl.conf` (security/canonical-host changes requiring deployment validation)
- deployment documentation / automation paths, if path drift is confirmed

## 11. Risks and verification checklist

Do not block private pages in robots before their response-level noindex is live; Google must be able to crawl the page to see noindex. Do not add schema to internal workflows. Do not assume an edge host or DNS behavior without testing.

- [ ] Production `/`, robots, sitemap, login, a tokenized attendance URL, a private app URL, and an unknown URL return their expected status/MIME/robots headers.
- [ ] Sitemap is valid XML and contains only the canonical landing URL.
- [ ] Production raw homepage has the expected title, description, canonical, H1 fallback, and JSON-LD.
- [ ] Route chunks build and load successfully; public initial payload shrinks.
- [ ] gzip/Brotli and security headers are present in production.
- [ ] Google Search Console sitemap and URL Inspection checks are completed by an authorized operator.

## Completion status — 2026-07-26

**Implemented locally:** explicit noindex headers for login/private route families and health check; true 404 behavior for unknown frontend paths; crawler blocks for API, uploads, and health endpoints; lazy-loaded non-landing route components; removal of the duplicate Material Symbols stylesheet import; canonical-host redirects in the deployment Nginx source; and standards-only sitemap cleanup.

**Still requires production action:** deploy the frontend and TLS gateway configuration, verify headers/statuses externally, configure/verify compression and public HTML security headers at the TLS edge, submit the sitemap, and collect real CWV/Search Console data. SoftwareApplication rich-result eligibility is not claimed because truthful public price/review data was not available.
