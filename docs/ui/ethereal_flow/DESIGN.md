---
name: Ethereal Flow
colors:
  surface: '#fbfaf1'
  surface-dim: '#dbdad3'
  surface-bright: '#fbfaf1'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f4ec'
  surface-container: '#efeee6'
  surface-container-high: '#e9e8e0'
  surface-container-highest: '#e4e3db'
  on-surface: '#1b1c17'
  on-surface-variant: '#41484a'
  inverse-surface: '#30312c'
  inverse-on-surface: '#f2f1e9'
  outline: '#72787a'
  outline-variant: '#c1c7ca'
  surface-tint: '#45636c'
  primary: '#45636c'
  on-primary: '#ffffff'
  primary-container: '#89a8b2'
  on-primary-container: '#1f3d46'
  inverse-primary: '#acccd6'
  secondary: '#4e6268'
  on-secondary: '#ffffff'
  secondary-container: '#cee3ea'
  on-secondary-container: '#52666c'
  tertiary: '#795740'
  on-tertiary: '#ffffff'
  tertiary-container: '#c49a80'
  on-tertiary-container: '#4f321e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c8e8f3'
  primary-fixed-dim: '#acccd6'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#2d4b54'
  secondary-fixed: '#d1e6ed'
  secondary-fixed-dim: '#b5cad1'
  on-secondary-fixed: '#0a1e24'
  on-secondary-fixed-variant: '#364a50'
  tertiary-fixed: '#ffdcc7'
  tertiary-fixed-dim: '#ebbda2'
  on-tertiary-fixed: '#2d1505'
  on-tertiary-fixed-variant: '#5f402b'
  background: '#fbfaf1'
  on-background: '#1b1c17'
  surface-variant: '#e4e3db'
  surface-substrate: '#E5E1DA'
  text-primary: '#2D3436'
  text-secondary: '#636E72'
  accent-success: '#4FAC9B'
  accent-warning: '#E1A95F'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: '1.3'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 32px
  gutter: 24px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
  section-margin: 64px
---

## Brand & Style

The brand identity centers on "Orchestrated Clarity"—transforming complex enterprise workflows into serene, manageable experiences. The target audience includes high-velocity engineering teams, product managers, and operations directors who value precision and speed.

The design style is **Corporate Modern with Glassmorphism**. It draws inspiration from high-fidelity utility tools, utilizing a "Layered Quartz" aesthetic. This involves high-transparency surfaces, subtle background blurs, and a meticulous attention to light and shadow to create a sense of physical depth in a digital space. The interface should feel expensive, calm, and hyper-functional, minimizing cognitive load through generous whitespace and a strictly governed color hierarchy.

## Colors

The palette is rooted in a sophisticated range of atmospheric blues and warm neutrals to avoid the clinical coldness of pure grayscale.

- **Primary (#89A8B2):** Used for key action states, active navigation indicators, and primary brand touchpoints.
- **Secondary (#B3C8CF):** Used for supporting UI elements, hover states, and illustrative iconography.
- **Neutral/Background (#F1F0E8):** The base canvas color, providing a soft, paper-like warmth that reduces eye strain.
- **Surface Substrate (#E5E1DA):** Used for non-interactive containers and secondary backgrounds to create subtle contrast against the main canvas.

All interactive elements must maintain a minimum 4.5:1 contrast ratio. For Persian typography, slightly increase weight or saturation to ensure legibility against light backgrounds.

## Typography

The typography system is designed for a bilingual environment (Persian/English). While the tokens specify **Hanken Grotesk** and **Inter** for global/technical terms, ensure the implementation utilizes **IRANSansX** for Persian strings to maintain a consistent visual weight.

- **Headlines:** Use Hanken Grotesk with tighter letter-spacing to create a "technical-premium" feel.
- **Body:** Inter is used for its exceptional legibility in data-dense environments.
- **Bilingual Treatment:** When English technical terms appear within Persian sentences, the English font size should be reduced by 1px to visually align the x-heights.
- **Hierarchy:** Use weight (Medium to Bold) rather than color to distinguish importance, keeping the palette monochromatic and professional.

## Layout & Spacing

The layout follows a **Fixed-Fluid Hybrid** model. Navigation and sidebars are fixed-width, while the main content area (Workflow Hub) uses a fluid 12-column grid to maximize data visibility.

- **Grid:** 12 columns on Desktop (1440px+), 8 columns on Tablet, and 4 columns on Mobile.
- **Rhythm:** An 8px base unit (softened to 4px for tight components) governs all spatial relationships.
- **Margins:** Desktop views should maintain a minimum 32px outer margin to provide visual "breathing room," reinforcing the premium aesthetic.
- **Bilingual Flow:** The layout must support seamless RTL (Right-to-Left) mirroring for Persian. Sidebars switch to the right, and chevron directions are inverted.

## Elevation & Depth

Hierarchy is established through **Glassmorphism and Ambient Shadows**. Rather than using stark black shadows, this design system uses "tinted depth."

1.  **Level 0 (Canvas):** The base `#F1F0E8` surface.
2.  **Level 1 (Cards):** Soft `#E5E1DA` background with a 1px solid border (`rgba(255,255,255,0.5)`) and a very diffuse 20px blur shadow with 4% opacity of the primary color.
3.  **Level 2 (Modals/Popovers):** Real-time backdrop blur (20px) with a semi-transparent white overlay (`rgba(255,255,255,0.7)`).
4.  **Interactive States:** When hovered, elements should "lift" by increasing shadow spread and slightly lightening the background color.

## Shapes

The geometry is deliberately soft to counteract the "coldness" of enterprise data. 

- **Cards/Modules:** 24px corner radius. This large radius is the signature of the premium "Apple-style" dashboard aesthetic.
- **Buttons:** 16px corner radius, creating a friendly but professional "squircle" look.
- **Inputs:** 12px corner radius to differentiate form elements from action elements.
- **Badges/Status:** Fully pill-shaped (rounded-full) to signify they are non-clickable meta-information.

## Components

### Buttons
- **Primary:** Solid `#89A8B2` with white text. 16px radius. High contrast is essential.
- **Secondary:** Transparent background with a 1.5px border of `#89A8B2`.
- **Ghost:** No background, `#636E72` text, used for tertiary actions.

### Tables (Data Dense)
- **Header:** Sticky headers with a subtle `#E5E1DA` background and 1px bottom border.
- **Row:** 64px minimum height to maintain readability. Use alternating row subtle tints rather than borders to separate data.
- **Typography:** Use `label-md` for table data to ensure high information density without clutter.

### Inputs
- **Style:** 12px radius, `#F1F0E8` background with a subtle inner shadow. On focus, the border transitions to `#89A8B2` with a 2px outer glow.
- **Labels:** Always positioned above the field in `label-sm` (uppercase).

### Navigation
- **Sidebar:** Fixed width (280px). Uses a subtle gradient from `#F1F0E8` to `#E5E1DA`. Active links use a glassmorphic "pill" highlight behind the text.

### Status Badges
- Used for workflow states (e.g., "In Progress," "Completed"). 
- Small, pill-shaped, using low-saturation versions of semantic colors (Success Green, Warning Gold) with 10% opacity backgrounds.