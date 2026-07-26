# SEO roadmap — Carnomand

Audited: 2026-07-26. Previous evidence: `docs/seo-analyze.md`; live checks confirmed that `/robots.txt` and `/sitemap.xml` were being served as the SPA shell. Stack: Vue 3, Vite, Vue Router history mode, Nginx, and a separate backend. The public SEO surface is deliberately limited to the landing page; application and tokenized attendance routes are private.

## Current score

**47/100 at audit baseline.** This reflects the live page before the fixes in this change set, not an imagined post-deploy score. Technical/indexability was the limiting factor; the landing copy is client-rendered in a Vite SPA.

## Implemented in this audit

- Added crawlable `robots.txt` and a one-URL XML sitemap; Nginx now serves each as its actual file rather than the SPA HTML.
- Added canonical, description, Open Graph, Twitter, theme color and `SoftwareApplication` JSON-LD to the public entry document.
- Added a semantic HTML fallback for the marketing landing page, while the authenticated Vue application replaces it after startup.
- Added route-aware metadata and `noindex, nofollow` to login, private application and tokenized attendance routes.
- Added XML-aware routing and gzip compression in Nginx.

## Critical / high priority

1. Deploy these frontend changes, then submit `https://carnomand.ir/sitemap.xml` in Search Console and request a homepage recrawl. Expected impact: restores index discovery and prevents private-route indexing.
2. Configure canonical-host redirects (`www` to `https://carnomand.ir`) at the edge/load balancer. This cannot be safely inferred in the generic container Nginx config. Expected impact: eliminates host-level duplicate URLs flagged by the prior audit.
3. Replace client-only marketing delivery with SSR or static prerendering for `/`. The fallback is a safe bridge, not a substitute for a real rendered marketing document. Expected impact: more dependable indexing and faster first contentful paint for crawlers and low-end devices.

## Medium priority

- Split the 502 kB initial JavaScript and 446 kB CSS bundles; load authenticated modules after login. The build confirms both are material render/performance risks.
- Add immutable caching only to hashed assets and keep HTML short-lived; validate LCP, INP and CLS with PageSpeed Insights/CrUX after deployment.
- Produce a dedicated 1200×630 social image instead of reusing the logo. Keep each meaningful landing image descriptive and give decorative images an empty `alt`.
- Add non-sensitive, indexable feature/use-case pages only when they contain distinct first-party content; add them to the sitemap and link them from the landing page.

## Long-term strategy

Build a small public content layer around organizational workflow management: feature pages, implementation guides, role-based use cases and customer evidence. Keep all dashboards, reports, files, attendance tokens and account screens excluded from crawling. Review titles, canonicals, robots rules, schema, sitemap coverage and Core Web Vitals before every release.

## Implementation order and expected impact

| Order | Work | Expected impact |
|---:|---|---|
| 1 | Deploy, verify robots/sitemap MIME types and submit sitemap | Critical crawl/index readiness |
| 2 | Enforce the canonical host at the edge | Removes duplicate-host signals |
| 3 | Prerender the public landing page | High indexing and rendering reliability |
| 4 | Split app bundles and measure CWV | Better LCP/INP potential |
| 5 | Publish unique public feature pages | Sustainable organic-growth capacity |

## Monitoring checklist

- On each release: fetch `/`, `/robots.txt`, `/sitemap.xml`, `/login` and one authenticated route; confirm expected status, MIME type, canonical and `X-Robots-Tag`.
- Monthly: inspect Search Console coverage, sitemap errors, canonical selection and mobile CWV.
- Before adding a public route: require a unique title, description, self-canonical, visible H1, internal link, sitemap decision, image alt text and appropriate schema.
