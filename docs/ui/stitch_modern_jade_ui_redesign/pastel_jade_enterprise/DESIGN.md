---
name: Pastel Jade Enterprise
colors:
  surface: '#f8fafb'
  surface-dim: '#d8dadb'
  surface-bright: '#f8fafb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f5'
  surface-container: '#eceeef'
  surface-container-high: '#e6e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#414845'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#eff1f2'
  outline: '#717975'
  outline-variant: '#c0c8c3'
  surface-tint: '#3e6658'
  primary: '#3e6658'
  on-primary: '#ffffff'
  primary-container: '#8fb9a8'
  on-primary-container: '#224a3d'
  inverse-primary: '#a5d0be'
  secondary: '#425aa7'
  on-secondary: '#ffffff'
  secondary-container: '#93aafe'
  on-secondary-container: '#223c88'
  tertiary: '#745b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#d0ac3e'
  on-tertiary-container: '#534100'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c0ecda'
  primary-fixed-dim: '#a5d0be'
  on-primary-fixed: '#002117'
  on-primary-fixed-variant: '#264e41'
  secondary-fixed: '#dce1ff'
  secondary-fixed-dim: '#b6c4ff'
  on-secondary-fixed: '#00164f'
  on-secondary-fixed-variant: '#28418e'
  tertiary-fixed: '#ffe08b'
  tertiary-fixed-dim: '#e8c352'
  on-tertiary-fixed: '#241a00'
  on-tertiary-fixed-variant: '#584400'
  background: '#f8fafb'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  display-lg:
    fontFamily: Vazirmatn
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 52px
  headline-lg:
    fontFamily: Vazirmatn
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 44px
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
  label-md:
    fontFamily: Vazirmatn
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  headline-lg-mobile:
    fontFamily: Vazirmatn
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-margin: 2rem
  gutter-md: 1.5rem
  stack-sm: 0.5rem
  stack-md: 1rem
  stack-lg: 2rem
---

## Brand & Style

The brand personality is **composed, premium, and efficient**. It is designed for high-end professional environments where clarity and focus are paramount. The UI evokes a sense of "digital calm" through a restrained color palette and generous breathing room.

The design style follows a **Modern Corporate** aesthetic with a touch of **Soft Minimalism**. It prioritizes legibility and functional hierarchy while using subtle depth markers to guide the user's eye. The interface feels "airy" by avoiding heavy containers and instead relying on whitespace and tonal shifts to define boundaries.

Key brand attributes:
- **Sophisticated:** Muted jade tones replace harsh high-contrast greens.
- **Airy:** Increased margins and gutters to prevent visual clutter.
- **Approachable:** Soft rounded corners on all interactive elements.

## Colors

The palette is anchored by **Pastel Jade Green**, used intentionally for primary actions and status indicators to maintain a high-end, muted feel. 

- **Primary (#8FB9A8):** Soft jade for active states, primary buttons, and positive reinforcement.
- **Secondary (#7289DA):** A dusty periwinkle for informational accents and secondary interactive paths.
- **Neutral (#F8FAFB):** A very cool, almost white grey used for the background to reduce eye strain and provide a clean canvas.
- **Surface:** Pure white (#FFFFFF) is reserved for cards and modals to create a "lift" against the neutral background.
- **Text:** Deep slate (#2D3748) for primary text to ensure high legibility against pastel backgrounds.

## Typography

The design system uses **Vazirmatn** (or a similar high-quality Persian/Arabic sans-serif) to ensure professional legibility across RTL (Right-to-Left) layouts. 

The type scale is generous, with significant contrast between headlines and body text. 
- **Headlines:** Use a semi-bold weight (600) to provide structure without feeling aggressive.
- **Body Text:** Uses a standard weight (400) with increased line-height (1.5x) to ensure long-form data and Persian script remain clear and readable.
- **Data Display:** For financial figures or large numbers, use a slightly tighter letter spacing to maintain a compact, technical feel.

## Layout & Spacing

This design system utilizes a **Fixed Grid** model for desktop to maintain alignment and a **Fluid Grid** for mobile devices. 

- **Sidebar Layout:** A fixed 280px right-hand sidebar for RTL navigation, providing a consistent anchor for the user.
- **Content Area:** A centered container with a maximum width of 1440px, ensuring line lengths remain readable on ultra-wide monitors.
- **Spacing Rhythm:** Based on an 8px (0.5rem) base unit. 
    - **Margins:** 32px (2rem) around the main viewport.
    - **Gutters:** 24px (1.5rem) between cards and major sections.
- **Mobile Adaption:** At the 768px breakpoint, the sidebar collapses into a bottom navigation bar or a hamburger menu, and container margins reduce to 16px.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and **Ambient Shadows**.

- **Background:** The base layer is the neutral surface (#F8FAFB).
- **Cards/Containers:** Elevated by a soft, diffused shadow (`0 4px 20px rgba(0, 0, 0, 0.04)`) and a subtle 1px border (#EDF2F7).
- **Interactive Elements:** Buttons and active inputs use a slightly more pronounced shadow on hover to simulate physical tactility.
- **Overlays:** Modals and dropdowns use a deeper shadow (`0 10px 30px rgba(0, 0, 0, 0.08)`) and a backdrop blur of 8px to isolate the content from the background noise.

## Shapes

The shape language is **Rounded**, conveying a friendly yet professional tone.

- **Standard Elements:** Buttons, inputs, and small cards use a 0.5rem (8px) radius.
- **Large Containers:** Dashboard widgets and main content blocks use a 1rem (16px) radius to soften the overall layout.
- **Selection Indicators:** Pill-shaped (fully rounded) tags and chips are used for status labels and filters to distinguish them from functional buttons.

## Components

### Buttons
- **Primary:** Solid Pastel Jade (#8FB9A8) with white text. No harsh borders.
- **Secondary:** Transparent background with a 1px border of the Primary color.
- **Icon Buttons:** Circular or soft-square backgrounds with 10% opacity of the primary color.

### Inputs & Fields
- **Search Bars:** Background #F1F4F6 with no border. Placeholder text in a light slate. 
- **Form Fields:** White background with a 1px soft grey border. On focus, the border transitions to the Pastel Jade color with a subtle outer glow.

### Cards & Stats
- **Summary Cards:** High-polish white surfaces. Use a thin colored bar (Jade, Blue, or Gold) at the bottom or side to denote category without overwhelming the card.
- **Dashboard Widgets:** Large headings followed by centered, high-contrast data values.

### Navigation (RTL)
- **Active State:** A soft Jade background (10% opacity) with a vertical 4px Jade bar on the right edge of the menu item.
- **Icons:** Consistent stroke weight (1.5px) and monochrome slate color, switching to Primary color when active.

### Chips & Badges
- **Status Badges:** Use very light pastel versions of the status color (e.g., Light Jade for "Active") with dark text of the same hue for maximum contrast and high-end feel.