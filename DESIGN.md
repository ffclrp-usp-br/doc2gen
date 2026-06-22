# Design

## Color Palette

Brand colors from the organization's graphic standards manual.

```css
:root {
  /* Primary — Azul Primário */
  --color-primary: #1094ab;
  --color-primary-hover: #0d7a8f;
  --color-primary-active: #0a6172;

  /* Accent — Amarelo */
  --color-accent: #fcb421;
  --color-accent-hover: #e5a31d;

  /* Secondary — Azul Secundário */
  --color-secondary: #64c4d2;
  --color-secondary-hover: #4fb8c8;

  /* Surface scale */
  --color-bg: #ffffff;
  --color-surface: #f4f7f8;
  --color-surface-raised: #ffffff;
  --color-border: #dce3e5;
  --color-border-strong: #b8c7cb;

  /* Ink scale */
  --color-ink: #1a2b32;
  --color-ink-secondary: #3d5a66;
  --color-ink-muted: #6b8a94;

  /* Semantic */
  --color-success: #2e7d5a;
  --color-success-text: #ffffff;
  --color-danger: #c0392b;
  --color-danger-text: #ffffff;
  --color-warning: #fcb421;
  --color-warning-text: #1a2b32;
  --color-info: #64c4d2;
  --color-info-text: #1a2b32;
}
```

## Typography

Open Sans from Google Fonts. Fixed rem scale.

```css
:root {
  --font-sans: 'Open Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SFMono-Regular', Menlo, Consolas, monospace;

  --text-xs: 0.75rem;
  --text-sm: 0.8125rem;
  --text-base: 0.875rem;
  --text-lg: 1rem;
  --text-xl: 1.125rem;
  --text-2xl: 1.25rem;
  --text-3xl: 1.5rem;
  --text-4xl: 1.875rem;

  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
}
```

## Spacing

Bootstrap 5 rem-based scale, consistent application.

```css
:root {
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
}
```

## Radius

Consistent border radius.

```css
:root {
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
}
```

## Shadows

Minimal, functional shadows.

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
```

## Component Tokens

### Cards

- Border-radius: `--radius-lg`
- Border: `1px solid var(--color-border)`
- Header: `var(--color-surface)` background, bottom border only
- Body padding: `var(--space-6)`

### Tables

- Header: `var(--color-primary)` bg, white text, `var(--font-semibold)` weight
- Row hover: `var(--color-surface)`
- Border: `var(--color-border)` horizontal lines only
- Cell padding: `var(--space-3) var(--space-4)`

### Buttons

- Primary: `var(--color-primary)` bg, white text
- Secondary: `var(--color-border)` bg, `var(--color-ink)` text
- Danger: `var(--color-danger)` bg, white text
- Outline variants: transparent bg, colored border + text
- Border-radius: `--radius-md`
- Padding: `var(--space-2) var(--space-4)`
- Focus: `2px solid var(--color-primary)`, `2px offset`

### Forms

- Input border: `1px solid var(--color-border-strong)`
- Focus ring: `0 0 0 2px var(--color-primary)` with 20% opacity
- Label: `var(--font-medium)`, `var(--color-ink)`
- Error: `var(--color-danger)`, `var(--text-sm)`

### Navigation

- Header: `var(--color-primary)` background, white text
- Accent bar: `var(--color-accent)` 3px stripe
- Nav bar: white background, `var(--color-primary)` text links
- Active link: `var(--color-primary)` with bottom accent
- Hover: `var(--color-surface)` background
- Height: `var(--space-10)`

## Layout

- Max content width: 1200px
- Container padding: `var(--space-6)`
- Section spacing: `var(--space-8)`
- Card spacing: `var(--space-6)` gap

## Motion

- Transitions: 150ms ease-out
- Focus animation: 150ms ease-out
- No page-load animations
- Reduced motion: respect `prefers-reduced-motion`

## Icons

Bootstrap Icons via CDN. Consistent sizing:
- Navigation: 1rem
- Buttons: 1rem with `gap-2`
- Status indicators: 0.875rem
