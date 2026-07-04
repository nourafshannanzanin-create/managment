---
name: Karomand Warm Enterprise
colors:
  background: '#f7f1eb'
  on-background: '#2e4374'
  surface: '#ffffff'
  surface-bright: '#fffaf6'
  surface-dim: '#e8ddd4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fbf5ef'
  surface-container: '#f6eee6'
  surface-container-high: '#f7efe7'
  surface-container-highest: '#f4ece4'
  surface-variant: '#eedaca'
  on-surface: '#2e4374'
  on-surface-variant: '#7c81ad'
  inverse-surface: '#2e4374'
  inverse-on-surface: '#fbf5ef'
  outline: '#cbb9ab'
  outline-variant: '#ddcec1'
  surface-tint: '#e5c3a6'
  primary: '#2e4374'
  on-primary: '#ffffff'
  primary-container: '#eedaca'
  on-primary-container: '#2e4374'
  inverse-primary: '#eedaca'
  primary-fixed: '#f7ede4'
  primary-fixed-dim: '#d8c0ac'
  on-primary-fixed: '#2e4374'
  on-primary-fixed-variant: '#2e4374'
  secondary: '#4b527e'
  on-secondary: '#ffffff'
  secondary-container: '#f4ece4'
  on-secondary-container: '#6c6f92'
  secondary-fixed: '#f3e8df'
  secondary-fixed-dim: '#e7d9ce'
  on-secondary-fixed: '#2e4374'
  on-secondary-fixed-variant: '#4b527e'
  tertiary: '#e5c3a6'
  on-tertiary: '#ffffff'
  tertiary-container: '#fbf5ef'
  on-tertiary-container: '#2e4374'
  tertiary-fixed: '#fbf5ef'
  tertiary-fixed-dim: '#f2e7dc'
  on-tertiary-fixed: '#2e4374'
  on-tertiary-fixed-variant: '#4b527e'
  error: '#8f3b3b'
  on-error: '#ffffff'
  error-container: '#f4dfdb'
  on-error-container: '#6a2f2f'
typography:
  headline-lg:
    fontFamily: Vazirmatn
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Vazirmatn
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Vazirmatn
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Vazirmatn
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Vazirmatn
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Vazirmatn
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.01em
  stat-value:
    fontFamily: Vazirmatn
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
rounded:
  sm: 10px
  DEFAULT: 16px
  md: 16px
  lg: 22px
  xl: 30px
  full: 9999px
spacing:
  container-padding: 2rem
  gutter: 1.5rem
  section-gap: 3rem
  card-padding: 1.5rem
  sidebar-width: 270px
---

## Brand & Style

This system is no longer modeled as a generic enterprise dashboard. It follows the visual language already present in the product: a warm, premium Persian workflow workspace with soft glass layers, large rounded shapes, and calm navy anchors.

The personality is **formal, humane, and quiet**. It should feel trustworthy for organizational workflows, but never cold or overly technical. The interface must read like an operational salon: warm background, bright paper-like cards, and restrained contrast.

## Colors

The palette is built from the live UI:

- **Primary `#2E4374`** for active states, major actions, strong headings, and navigation focus.
- **Secondary `#4B527E`** for supporting emphasis, icons, and secondary actions.
- **Sand Accent `#E5C3A6`** for tinted surfaces, pills, hover states, and soft highlights.
- **Background `#F7F1EB`** for the global canvas.
- **Surface `#FFFFFF`** and **Soft Surface `#FBF5EF` / `#F4ECE4`** for cards, forms, modals, and grouped content.

Semantic states should stay muted and brand-consistent. Even alerts should avoid neon SaaS colors unless the action is truly destructive.

## Typography

**Vazirmatn** is the primary typeface across headline, body, label, and numeric presentation. The current product already uses it consistently, so the design system should not introduce competing Latin-first font stacks.

- Headlines are bold, compact, and right-aligned.
- Body text is comfortable and spacious for Persian reading.
- Labels and metadata are small but still readable, with minimal tracking.
- Numeric metrics may use the same family with heavier weights rather than switching to a different display font.

## Layout & Flow

The layout language is **RTL-first and card-led**.

- Navigation is horizontal and pill-based in desktop topbar and mobile floating nav.
- Primary content is composed of stacked sections, hero cards, metric cards, modal forms, and list cards.
- Cards should be visually grouped by spacing and background tint, not heavy separators.
- Page rhythm should preserve generous breathing room: 14px, 16px, 18px, 22px, and 28px are recurring practical intervals in the current UI.

## Elevation & Depth

Depth should come from **soft contrast, blur, and tonal layering**, not heavy shadow stacks.

- Surfaces are light and slightly translucent where appropriate.
- Borders are subtle and warm, usually derived from the primary tone at low opacity.
- Modals and login panels can use frosted-glass treatment, but standard content cards should stay crisp and readable.

## Shapes

The shape system is one of the clearest signatures of the product.

- Small controls: `10px`
- Inputs and buttons: `16px`
- Standard cards and grouped nav items: `22px`
- Large feature panels and modals: `30px`
- Pills and filters: `9999px`

Avoid sharp corners unless a highly technical sub-surface explicitly needs contrast.

## Components

### Buttons

Primary buttons use dark navy fills or navy gradients with white text. Secondary buttons use tinted sand or white surfaces with subtle borders. The interaction should feel lifted, not loud.

### Inputs

Inputs sit on soft white surfaces with very light warm borders. Focus uses a low-opacity navy ring or border shift. Labels remain outside the input and right-aligned for clarity in Persian workflows.

### Cards

Cards are the structural backbone of the interface. They use white or warm-soft surfaces, 16px to 22px corner radii, and light outlines. Section headers inside cards may use a faint divider, but large blocks should rely more on spacing than rules.

### Navigation

Navigation elements are rounded pills. Inactive states are muted navy on light/sand backgrounds; active states invert to solid navy with white text. Mobile navigation can float above the page if it preserves touch comfort and readability.

### Status Chips

Status chips should remain soft and low-noise:

- Approved and positive states: tinted sand or muted success treatments
- Pending and review states: pale violet-navy tints
- Rejected states: dusty warm red backgrounds with deeper text

### Tables & Lists

Dense data should feel softened to match the rest of the system. Use warm header fills, low-contrast row dividers, and cardified list treatments on smaller screens.
