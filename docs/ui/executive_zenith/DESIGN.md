---
name: Executive Zenith
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#3f4949'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#6f797a'
  outline-variant: '#bec8c9'
  surface-tint: '#14686d'
  primary: '#026166'
  on-primary: '#ffffff'
  primary-container: '#2d7a7f'
  on-primary-container: '#d2fcff'
  inverse-primary: '#8ad3d8'
  secondary: '#4d6169'
  on-secondary: '#ffffff'
  secondary-container: '#d0e6ef'
  on-secondary-container: '#53676f'
  tertiary: '#545857'
  on-tertiary: '#ffffff'
  tertiary-container: '#6c706f'
  on-tertiary-container: '#f1f4f3'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a6eff4'
  primary-fixed-dim: '#8ad3d8'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f53'
  secondary-fixed: '#d0e6ef'
  secondary-fixed-dim: '#b4cad3'
  on-secondary-fixed: '#091e25'
  on-secondary-fixed-variant: '#364a51'
  tertiary-fixed: '#e0e3e2'
  tertiary-fixed-dim: '#c4c7c6'
  on-tertiary-fixed: '#181c1c'
  on-tertiary-fixed-variant: '#434847'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  stat-value:
    fontFamily: Hanken Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-padding: 2rem
  gutter: 1.5rem
  section-gap: 3rem
  card-padding: 1.5rem
  sidebar-width: 280px
---

## Brand & Style

The design system embodies a **Corporate Modern** aesthetic tailored for high-stakes enterprise management. It conveys authority, precision, and luxury through a disciplined application of whitespace and a refined color palette. The personality is "Quietly Powerful"—it doesn't shout for attention but earns it through flawless execution and technical sophistication.

The interface prioritizes clarity and a sense of "premium space," drawing inspiration from world-class SaaS platforms. It utilizes a layered approach to depth, where subtle shadows and tonal changes replace heavy borders, creating an environment that feels breathable yet structured. For the RTL context, every element is mirrored to ensure a natural reading flow that feels native and intentional, rather than an afterthought.

## Colors

The palette is anchored by a deep **Executive Teal** (Primary), which provides a professional yet distinctive brand signal. This is paired with **Slate Onyx** (Secondary) for high-contrast typography and iconography, ensuring maximum legibility.

- **Primary (#2D7A7F):** Used for primary actions, active navigation states, and key data visualizations.
- **Secondary (#1A2E35):** Reserved for primary headings and critical UI anchors to provide a sense of weight.
- **Background/Surface (#F4F7F6):** A custom off-white/grey tint that reduces eye strain and provides a luxury "paper" feel compared to pure white.
- **Success/Info/Warning:** These are derived as tonal variations of the primary teal and a muted gold to maintain the professional sobriety of the system.

## Typography

The typographic scale is designed for complex data environments. **Hanken Grotesk** provides a sharp, geometric clarity for headlines and financial figures. **Be Vietnam Pro** is used for body copy due to its exceptional readability and modern, friendly proportions. 

For technical labels, metadata, and ID numbers (like REQ-codes), **JetBrains Mono** is introduced to provide a "developer-grade" precision feel. In the RTL (Persian/Arabic) context, ensure the selected font weights are balanced to maintain the same visual hierarchy as the English counterparts.

## Layout & Spacing

This design system utilizes a **Fixed Grid** philosophy for dashboard content to maintain a high-end, editorial feel, while the internal card structures remain fluid. 

- **Grid:** A 12-column grid is standard for desktop, transitioning to a single-column stack for mobile.
- **RTL Flow:** The layout is strictly right-to-left. The sidebar is anchored to the right, and the main content area flows to the left. Form labels are right-aligned above their inputs.
- **Rhythm:** An 8px base unit governs all spacing. Premium "breathability" is achieved by doubling standard margins (using 32px instead of 16px) for major section breaks.

## Elevation & Depth

Depth is conveyed through **Tonal Layering** and **Ambient Shadows**. Instead of traditional borders, cards sit on the surface with a very soft, multi-layered shadow (0px 4px 20px rgba(0,0,0,0.04)).

- **Level 0 (Background):** The base `#F4F7F6` surface.
- **Level 1 (Cards/Containers):** Pure white `#FFFFFF` surfaces with rounded corners and ambient shadows.
- **Level 2 (Dropdowns/Modals):** Increased shadow spread and a subtle 1px stroke in a lightened primary tint to define boundaries against Level 1.
- **Interactive Depth:** Buttons use a subtle inner-shadow when pressed to simulate a tactile "click" into the interface.

## Shapes

The shape language is **Rounded**, striking a balance between approachable and professional. 

- **Primary Containers:** Use `rounded-lg` (16px) to create a soft, modern frame for data.
- **Interactive Elements:** Buttons and input fields use `rounded-md` (8px) for a more disciplined, precise look.
- **Avatars & Status Indicators:** Use full circles (`rounded-full`) to differentiate "human" or "status" elements from "structural" ones.

## Components

### Buttons
Primary buttons feature a subtle vertical gradient (Primary Main to a 10% darker shade) to give them a premium, tactile feel. Label text is always `label-sm` weight but slightly upscaled for visibility.

### Inputs
Input fields are "Ghost Style" by default: a light grey background with no border, which transitions to a 2px Primary Teal bottom-border or full-border on focus. Labels are placed inside the field area for a modern, compact look.

### Cards
Cards are the primary vehicle for information. They must include a `card-padding` of 24px. Headers within cards should be separated by a light horizontal rule (1px, 5% opacity Secondary color).

### Data Tables
Tables use a "Zebra" striping that is extremely subtle (2% opacity Secondary). The header row uses a slightly darker tint of the background color with uppercase (or bolded RTL) labels to provide a strong anchor.

### Chips & Tags
Status chips (e.g., "Approved", "Pending") use a low-saturation background with high-saturation text of the same hue, ensuring they are readable without being visually noisy.