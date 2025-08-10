# BITTEN WebApp Style Guide

**Version**: 1.0  
**Last Updated**: August 10, 2025  
**Theme**: Military/Tactical Trading Interface

---

## 🎨 Design Tokens

### Color Palette

```css
:root {
    /* Primary Colors */
    --color-primary: #00D4AA;        /* Bright tactical green */
    --color-primary-dark: #00B896;   /* Darker green for hovers */
    --color-secondary: #7c3aed;      /* Commander purple */
    
    /* Semantic Colors */
    --color-success: #10b981;        /* Profit/success green */
    --color-warning: #f59e0b;        /* Caution amber */
    --color-danger: #ef4444;         /* Loss/danger red */
    
    /* Background Colors */
    --color-bg-dark: #0f172a;        /* Deep space navy */
    --color-bg-light: #1e293b;       /* Lighter panel background */
    --color-panel: rgba(15, 23, 42, 0.95); /* Semi-transparent panels */
    
    /* Text Colors */
    --color-text-primary: #f1f5f9;   /* Primary white text */
    --color-text-secondary: #94a3b8;  /* Muted gray text */
    
    /* UI Colors */
    --color-border: #334155;         /* Subtle borders */
    --color-accent-gold: #fbbf24;    /* Elite gold accent */
}
```

### Typography Scale

```css
:root {
    /* Font Sizes */
    --font-xs: 0.75rem;     /* 12px - Help text */
    --font-sm: 0.875rem;    /* 14px - Labels */
    --font-base: 1rem;      /* 16px - Body text */
    --font-lg: 1.125rem;    /* 18px - Subheadings */
    --font-xl: 1.25rem;     /* 20px - Headings */
    --font-2xl: 1.5rem;     /* 24px - Large headings */
    --font-3xl: 2rem;       /* 32px - Hero text */
    
    /* Font Families */
    --font-primary: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --font-display: 'Orbitron', sans-serif; /* For tactical headings */
}
```

### Spacing Scale

```css
:root {
    /* Spacing System (based on 4px grid) */
    --space-xs: 0.25rem;    /* 4px */
    --space-sm: 0.5rem;     /* 8px */
    --space-md: 1rem;       /* 16px */
    --space-lg: 1.5rem;     /* 24px */
    --space-xl: 2rem;       /* 32px */
    --space-2xl: 3rem;      /* 48px */
    --space-3xl: 4rem;      /* 64px */
}
```

### Border Radius

```css
:root {
    --radius-sm: 0.25rem;   /* 4px - Small elements */
    --radius-md: 0.5rem;    /* 8px - Inputs, cards */
    --radius-lg: 1rem;      /* 16px - Large cards */
    --radius-full: 9999px;  /* Fully rounded */
}
```

### Shadows

```css
:root {
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.15);
    --shadow-card: 0 6px 24px rgba(0, 0, 0, 0.1);
    --shadow-glow: 0 0 20px rgba(0, 212, 170, 0.3);
}
```

---

## 🧩 Component Library

### Buttons

#### Primary Button
```html
<button type="button" class="btn btn--primary btn--md">
    Execute Mission
</button>
```

#### Variants
- `btn--primary` - Main action (tactical green)
- `btn--secondary` - Secondary action (purple)
- `btn--danger` - Destructive action (red)
- `btn--ghost` - Subtle action (transparent)

#### Sizes
- `btn--xs` - 28px height
- `btn--sm` - 36px height
- `btn--md` - 44px height (default)
- `btn--lg` - 52px height

### Cards

#### Basic Card
```html
<div class="card card--default card--padding-md">
    <div class="card__header">
        <h3 class="card__title">Mission Brief</h3>
        <p class="card__subtitle">EURUSD Analysis</p>
    </div>
    <div class="card__content">
        <!-- Card content -->
    </div>
</div>
```

#### Variants
- `card--success` - Success state (green accent)
- `card--warning` - Warning state (amber accent)
- `card--danger` - Error state (red accent)
- `card--primary` - Primary state (tactical green)

### Forms

#### Form Group
```html
<div class="form-group">
    <label for="symbol" class="form-label">
        Symbol <span class="form-required">*</span>
    </label>
    <input type="text" 
           id="symbol" 
           name="symbol"
           class="form-input"
           placeholder="e.g., EURUSD"
           required>
    <div class="form-help">Enter the trading symbol</div>
</div>
```

---

## 🌐 Layout System

### Container Classes

```css
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 var(--space-md);
}

.container--sm { max-width: 640px; }
.container--md { max-width: 768px; }
.container--lg { max-width: 1024px; }
.container--xl { max-width: 1280px; }
```

### Grid System

```css
.grid {
    display: grid;
    gap: var(--space-md);
}

.grid--2 { grid-template-columns: repeat(2, 1fr); }
.grid--3 { grid-template-columns: repeat(3, 1fr); }
.grid--4 { grid-template-columns: repeat(4, 1fr); }

@media (max-width: 768px) {
    .grid--2,
    .grid--3,
    .grid--4 {
        grid-template-columns: 1fr;
    }
}
```

### Flexbox Utilities

```css
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-sm { gap: var(--space-sm); }
.gap-md { gap: var(--space-md); }
.gap-lg { gap: var(--space-lg); }
```

---

## ♿ Accessibility Standards

### Screen Reader Support

```css
/* Screen Reader Only Text */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
```

### Focus Management

```css
/* Focus Indicators */
*:focus-visible {
    outline: 3px solid var(--color-primary);
    outline-offset: 2px;
}

/* Remove focus for mouse users */
*:focus:not(:focus-visible) {
    outline: none;
}

/* Skip to Content Link */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--color-primary);
    color: var(--color-bg-dark);
    padding: var(--space-sm) var(--space-md);
    text-decoration: none;
    z-index: 9999;
    border-radius: 0 0 var(--radius-md) 0;
}

.skip-link:focus {
    top: 0;
}
```

### ARIA Patterns

#### Form Validation
```html
<input aria-describedby="email-error" aria-invalid="true">
<div id="email-error" role="alert">Invalid email format</div>
```

#### Loading States
```html
<button aria-describedby="loading-msg">
    Submit
</button>
<div id="loading-msg" aria-live="polite" aria-atomic="true">
    <!-- Dynamically updated with loading state -->
</div>
```

---

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile First Approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

### Mobile-Specific Rules

```css
@media (max-width: 640px) {
    /* Increase tap targets */
    .btn {
        min-height: 44px;
        min-width: 44px;
    }
    
    /* Prevent iOS zoom */
    input, select, textarea {
        font-size: 16px;
    }
    
    /* Stack navigation */
    .header-bar {
        flex-direction: column;
        gap: var(--space-sm);
    }
}
```

---

## 🎯 Component Usage Guidelines

### File Organization

```
/components/
  ├── button.html          # Reusable button component
  ├── card.html           # Card component
  ├── form-group.html     # Form input group
  └── modal.html          # Modal component

/templates/
  ├── base.html           # Base template with common structure
  ├── hud.html            # Mission HUD page
  └── me.html             # User profile page

/static/css/
  ├── bitten.css          # Core styles and tokens
  ├── components.css      # Component-specific styles
  └── utilities.css       # Utility classes
```

### Naming Conventions

#### CSS Classes
- **Block**: `.card`
- **Element**: `.card__header`
- **Modifier**: `.card--primary`

#### Component Props
- Use descriptive names: `aria_label`, `is_disabled`
- Boolean props prefix with `is_` or `has_`
- Size variants: `xs`, `sm`, `md`, `lg`, `xl`

### Accessibility Checklist

- ✅ All images have alt text
- ✅ Forms have proper labels
- ✅ Interactive elements are keyboard accessible
- ✅ Color contrast meets WCAG AA standards
- ✅ Focus indicators are visible
- ✅ Screen reader content is properly marked
- ✅ Page structure uses semantic HTML
- ✅ Loading states are announced
- ✅ Error messages are associated with inputs

---

## 🔄 Migration Path

### Phase 1: Foundation (Immediate)
1. Add accessibility CSS utilities
2. Update form templates with proper labels
3. Add semantic HTML structure
4. Implement focus indicators

### Phase 2: Components (Week 1)
1. Create reusable component library
2. Update existing templates to use components
3. Implement consistent spacing and colors
4. Add responsive breakpoints

### Phase 3: Enhancement (Week 2)
1. Add loading states and animations
2. Implement error handling patterns
3. Add progressive enhancement features
4. Optimize performance

### Phase 4: Polish (Week 3)
1. Comprehensive testing
2. User feedback integration
3. Performance optimization
4. Documentation completion

---

## 🧪 Testing Strategy

### Accessibility Testing
- Use axe-core for automated testing
- Test with keyboard navigation
- Validate with screen readers
- Check color contrast ratios

### Performance Testing
- Lighthouse scores > 80
- First Contentful Paint < 1.5s
- Cumulative Layout Shift < 0.1

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

**Remember**: The military/tactical theme should be maintained throughout all components while ensuring maximum accessibility and usability. Every element should feel purposeful and mission-critical.