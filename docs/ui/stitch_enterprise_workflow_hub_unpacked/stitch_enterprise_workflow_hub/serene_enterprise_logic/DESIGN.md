---
name: Serene Enterprise Logic
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
  tertiary: '#605e59'
  on-tertiary: '#ffffff'
  tertiary-container: '#a6a39d'
  on-tertiary-container: '#3b3935'
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
  tertiary-fixed: '#e6e2db'
  tertiary-fixed-dim: '#cac6bf'
  on-tertiary-fixed: '#1c1c17'
  on-tertiary-fixed-variant: '#484742'
  background: '#fbfaf1'
  on-background: '#1b1c17'
  surface-variant: '#e4e3db'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Inter
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
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.2'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  sidebar-width: 280px
  header-height: 72px
  gutter: 24px
  container-padding: 32px
  gap-md: 16px
  gap-lg: 24px
---

## Brand & Style
The design system is engineered for high-stakes enterprise environments where clarity and focus are paramount. It adopts a **Minimalist Modern** aesthetic, heavily influenced by the precision of contemporary productivity tools and the tactile softness of premium hardware interfaces. 

The personality is professional, calm, and trustworthy. By removing shadows and unnecessary borders, the UI reduces cognitive load, allowing data and workflows to remain the primary focus. The emotional response should be one of "effortless control"—a digital workspace that feels as refined and intentional as a physical executive suite.

## Colors
The palette is built on a sophisticated foundation of warm neutrals and muted cool tones. 

- **Primary (#89A8B2):** Used for key actions, active states, and secondary text that requires a branded feel.
- **Secondary (#B3C8CF):** Applied to decorative elements, hover states on subtle components, and progress indicators.
- **Surface (#F1F0E8):** The primary canvas color. It provides a warmer, more premium feel than pure white, reducing eye strain during long working hours.
- **Component Background (#E5E1DA):** Used to differentiate functional areas (like cards or inputs) from the main surface without relying on borders or shadows.
- **Text:** Deep Charcoal is reserved for high-readability body and header text, while the Primary Blue-Grey is used for metadata and labels to create a clear hierarchy.

## Typography
The system uses **Inter** (as a fallback for IRANSansX in the design tokens) to ensure a systematic, utilitarian, and highly legible experience. For Persian contexts, the typography must prioritize the **IRANSansX** family to maintain the premium enterprise feel.

- **Hierarchy:** Large display titles use heavy weights with tight tracking for a "Linear-style" editorial look.
- **Readability:** Body text maintains a generous 1.6 line-height to ensure comfort in data-heavy views.
- **RTL Considerations:** Letter spacing is disabled for Persian characters. All text alignment is defaulted to the right. 
- **Scale:** Sizes scale down aggressively for mobile to ensure that complex enterprise dashboards remain functional on small screens.

## Layout & Spacing
This design system utilizes a **Fluid Content Model** with fixed structural anchors. 

- **RTL Structure:** The primary navigation sidebar is fixed to the **right** edge. The top header remains fixed at the top, providing global search and user actions.
- **Separation:** Separation is achieved through **whitespace and subtle color shifts** (Surface #F1F0E8 vs. Component Background #E5E1DA) rather than borders. This prevents "box-in-box" clutter.
- **Grid:** A 12-column fluid grid is used for the main content area.
- **Breakpoints:**
  - **Desktop:** 1200px+ (Full sidebar + fluid content).
  - **Tablet:** 768px - 1199px (Sidebar collapses to icons or a drawer).
  - **Mobile:** <767px (Sidebar becomes a bottom-sheet or full-screen overlay; container padding reduces to 16px).

## Elevation & Depth
In alignment with the "Flat UI" principle, this design system **eschews all drop shadows**. Depth is communicated through a logic of **Tonal Layering**:

1.  **Level 0 (Base):** The `Surface` color (#F1F0E8) serves as the background for the entire application.
2.  **Level 1 (Interactive/Container):** Components like cards, input fields, and sidebar items use the `Component Background` (#E5E1DA).
3.  **Level 2 (Active/Emphasis):** Primary buttons and active navigational states use the `Primary` color (#89A8B2) to sit "above" the layout visually through color weight rather than physical projection.

This approach creates a tactile, architectural feel that mimics high-end stationary or minimalist interior design.

## Shapes
The shape language is defined by **Soft Geometricism**. Significant rounding is applied to create a friendly yet professional atmosphere.

- **Cards:** Large 24px radii create a "tablet-within-a-screen" look, helping to group related information clearly without the need for borders.
- **Controls:** Buttons and inputs share a 16px radius, creating a consistent "squircle" language for interactive elements.
- **Consistency:** All nested elements must have a smaller radius than their parent container to maintain visual harmony (the "inner radius" rule).

## Components

- **Buttons:** 16px rounded corners. Primary buttons use #89A8B2 with Deep Charcoal text for a bold look. Secondary buttons use #E5E1DA with #89A8B2 text. No borders, no shadows.
- **Inputs:** Background set to #E5E1DA with 16px rounded corners. On focus, the background shifts slightly or a subtle 1px solid stroke in #89A8B2 appears. 
- **Cards:** Background #E5E1DA, 24px rounded corners. Content inside cards should use generous internal padding (min 24px) to avoid crowding.
- **Sidebar Items:** Right-aligned text. Active state uses a subtle background shift to #B3C8CF or a vertical "pill" indicator on the right edge of the item.
- **Chips:** Fully rounded (pill-shaped) using #B3C8CF background for low-emphasis tagging.
- **Lists:** Clean rows separated by whitespace. High-contrast Charcoal for primary titles, Primary Blue-Grey for secondary metadata. 
- **Checkboxes/Radios:** Soft-rounded squares (4px) for checkboxes and circles for radios, using #89A8B2 for the "selected" state.
- **Data Tables:** No vertical borders. Use horizontal dividers in a very faint version of the Primary color (approx 10% opacity) or simply rely on row hover states in #E5E1DA.