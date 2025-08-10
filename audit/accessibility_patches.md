# Accessibility Patches for BITTEN WebApp

## Patch 1: Add Semantic HTML Structure to comprehensive_mission_briefing.html

```diff
--- a/templates/comprehensive_mission_briefing.html
+++ b/templates/comprehensive_mission_briefing.html
@@ -1,6 +1,10 @@
 <!DOCTYPE html>
 <html lang="en">
 <head>
+    <!-- Skip Navigation Link -->
+    <a href="#main-content" class="sr-only skip-link">Skip to main content</a>
+    
     <link rel="stylesheet" href="/static/css/bitten.css">
     <link rel="stylesheet" href="/static/css/hud.css">
     
@@ -34,17 +38,21 @@
         }
 
         /* Header Bar with User Stats and Quick Links */
-        .header-bar {
+        header.header-bar {
             background: linear-gradient(90deg, var(--commander-purple) 0%, #8b5cf6 100%);
             padding: 15px;
             display: flex;
             justify-content: space-between;
             align-items: center;
             flex-wrap: wrap;
             gap: 15px;
         }
+        
+        /* Screen Reader Only Text */
+        .sr-only {
+            position: absolute;
+            width: 1px;
+            height: 1px;
+            padding: 0;
+            margin: -1px;
+            overflow: hidden;
+            clip: rect(0,0,0,0);
+            white-space: nowrap;
+            border: 0;
+        }
+        
+        /* Skip Link Visible on Focus */
+        .skip-link:focus {
+            position: absolute;
+            left: 10px;
+            top: 10px;
+            z-index: 999;
+            padding: 10px;
+            background: var(--commander-purple);
+            color: white;
+            text-decoration: none;
+            border-radius: 4px;
+        }
+        
+        /* Focus Indicators */
+        a:focus-visible,
+        button:focus-visible,
+        input:focus-visible,
+        select:focus-visible,
+        textarea:focus-visible {
+            outline: 3px solid var(--elite-gold);
+            outline-offset: 2px;
+        }
 
         .user-stats-bar {
             display: flex;
@@ -68,7 +76,7 @@
         }
 
-        .quick-links {
+        nav.quick-links {
             display: flex;
             gap: 10px;
         }
@@ -92,11 +100,11 @@
         }
 
         /* Main Container */
-        .mission-container {
+        main.mission-container {
             max-width: 1400px;
             margin: 0 auto;
             padding: 20px;
         }
 </head>
 <body>
-    <div class="header-bar">
-        <div class="user-stats-bar">
-            <div class="stat-item">
-                <div class="stat-label">Your Balance</div>
-                <div class="stat-value">${{ user_balance }}</div>
+    <header class="header-bar" role="banner">
+        <div class="user-stats-bar" role="region" aria-label="User Statistics">
+            <div class="stat-item">
+                <div class="stat-label">Your Balance</div>
+                <div class="stat-value" aria-label="Balance: {{ user_balance }} dollars">${{ user_balance }}</div>
             </div>
             <div class="stat-item">
                 <div class="stat-label">Tier</div>
-                <div class="stat-value">{{ user_tier }}</div>
+                <div class="stat-value" aria-label="Tier: {{ user_tier }}">{{ user_tier }}</div>
             </div>
             <div class="stat-item">
                 <div class="stat-label">Win Rate</div>
-                <div class="stat-value">{{ win_rate }}%</div>
+                <div class="stat-value" aria-label="Win rate: {{ win_rate }} percent">{{ win_rate }}%</div>
             </div>
         </div>
-        <div class="quick-links">
-            <a href="/me" class="quick-link">🏆 War Room</a>
-            <a href="/history" class="quick-link">📊 History</a>
-            <a href="/learn" class="quick-link">📚 Learn</a>
-            <a href="/settings" class="quick-link">⚙️ Settings</a>
-        </div>
-    </div>
+        <nav class="quick-links" role="navigation" aria-label="Main Navigation">
+            <a href="/me" class="quick-link" aria-label="War Room">🏆 War Room</a>
+            <a href="/history" class="quick-link" aria-label="History">📊 History</a>
+            <a href="/learn" class="quick-link" aria-label="Learn">📚 Learn</a>
+            <a href="/settings" class="quick-link" aria-label="Settings">⚙️ Settings</a>
+        </nav>
+    </header>
     
-    <div class="mission-container">
+    <main id="main-content" class="mission-container" role="main">
         <!-- Mission content here -->
-    </div>
+    </main>
+    
+    <footer role="contentinfo" class="site-footer">
+        <p>&copy; 2025 BITTEN Trading. All rights reserved.</p>
+    </footer>
 </body>
 </html>
```

## Patch 2: Add Form Labels and ARIA Attributes

```diff
--- a/templates/forms_example.html
+++ b/templates/forms_example.html
@@ -1,10 +1,30 @@
 <!-- Example form improvements -->
-<form class="trade-form">
-    <input type="text" placeholder="Symbol" id="symbol" required>
-    <input type="number" placeholder="Lot Size" id="lot_size" step="0.01" required>
-    <select id="direction">
+<form class="trade-form" role="form" aria-label="Trade Execution Form">
+    <div class="form-group">
+        <label for="symbol" class="form-label">
+            Trading Symbol
+            <span aria-label="required">*</span>
+        </label>
+        <input type="text" 
+               id="symbol" 
+               name="symbol"
+               placeholder="e.g., EURUSD" 
+               required
+               aria-required="true"
+               aria-describedby="symbol-help">
+        <span id="symbol-help" class="form-help">Enter the currency pair or asset symbol</span>
+    </div>
+    
+    <div class="form-group">
+        <label for="lot_size" class="form-label">
+            Position Size (Lots)
+            <span aria-label="required">*</span>
+        </label>
+        <input type="number" 
+               id="lot_size"
+               name="lot_size"
+               placeholder="0.01" 
+               step="0.01" 
+               min="0.01"
+               max="10"
+               required
+               aria-required="true"
+               aria-describedby="lot-help">
+        <span id="lot-help" class="form-help">Minimum 0.01, Maximum 10.00 lots</span>
+    </div>
+    
+    <div class="form-group">
+        <label for="direction" class="form-label">Trade Direction</label>
+        <select id="direction" name="direction" aria-required="true">
+            <option value="">Select direction</option>
             <option value="BUY">BUY</option>
             <option value="SELL">SELL</option>
-    </select>
-    <button class="fire-btn">🔫 FIRE</button>
+        </select>
+    </div>
+    
+    <button type="submit" 
+            class="fire-btn"
+            aria-label="Execute trade">
+        🔫 FIRE
+    </button>
+    
+    <!-- Add live region for form feedback -->
+    <div role="alert" aria-live="polite" aria-atomic="true" class="form-feedback"></div>
 </form>
```

## Patch 3: Fix Button Types and Add ARIA

```diff
--- a/templates/buttons_example.html
+++ b/templates/buttons_example.html
@@ -1,8 +1,24 @@
 <!-- Button improvements -->
-<button class="action-btn">Execute</button>
-<button class="cancel-btn">Cancel</button>
-<button class="refresh-btn">↻</button>
+<button type="button" 
+        class="action-btn"
+        aria-label="Execute trade">
+    Execute
+</button>
+
+<button type="button" 
+        class="cancel-btn"
+        aria-label="Cancel operation">
+    Cancel
+</button>
+
+<button type="button" 
+        class="refresh-btn"
+        aria-label="Refresh data"
+        title="Refresh data">
+    <span aria-hidden="true">↻</span>
+    <span class="sr-only">Refresh</span>
+</button>
+
+<!-- Form submit button -->
+<button type="submit" 
+        class="submit-btn"
+        aria-label="Submit form">
+    Submit
+</button>
```

## Patch 4: Add Alt Text to Images

```diff
--- a/templates/images_example.html
+++ b/templates/images_example.html
@@ -1,5 +1,14 @@
 <!-- Image improvements -->
-<img src="/static/icons/logo.png">
-<img src="/static/icons/chart.svg">
-<img src="/static/icons/user.jpg">
+<img src="/static/icons/logo.png" 
+     alt="BITTEN Trading Logo"
+     role="img">
+
+<img src="/static/icons/chart.svg" 
+     alt="Trading chart showing price movement"
+     role="img">
+
+<img src="/static/icons/user.jpg" 
+     alt="User profile picture"
+     role="img">
+
+<!-- Decorative images -->
+<img src="/static/icons/decoration.png" 
+     alt=""
+     role="presentation">
```

## Patch 5: Enhanced CSS with Accessibility Features

```diff
--- a/static/css/bitten.css
+++ b/static/css/bitten.css
@@ -1,5 +1,85 @@
 /* BITTEN Core CSS with Accessibility Enhancements */
 
+/* CSS Custom Properties for Consistent Design */
+:root {
+    /* Colors with WCAG AA compliant contrast ratios */
+    --color-primary: #00D4AA;
+    --color-primary-dark: #00B896;
+    --color-secondary: #7c3aed;
+    --color-success: #10b981;
+    --color-warning: #f59e0b;
+    --color-danger: #ef4444;
+    --color-bg-dark: #0f172a;
+    --color-bg-light: #1e293b;
+    --color-text-primary: #f1f5f9;
+    --color-text-secondary: #94a3b8;
+    --color-border: #334155;
+    
+    /* Spacing Scale */
+    --space-xs: 0.25rem;
+    --space-sm: 0.5rem;
+    --space-md: 1rem;
+    --space-lg: 1.5rem;
+    --space-xl: 2rem;
+    --space-2xl: 3rem;
+    
+    /* Typography Scale */
+    --font-xs: 0.75rem;
+    --font-sm: 0.875rem;
+    --font-base: 1rem;
+    --font-lg: 1.125rem;
+    --font-xl: 1.25rem;
+    --font-2xl: 1.5rem;
+    --font-3xl: 2rem;
+    
+    /* Border Radius */
+    --radius-sm: 0.25rem;
+    --radius-md: 0.5rem;
+    --radius-lg: 1rem;
+    --radius-full: 9999px;
+    
+    /* Shadows */
+    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
+    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
+    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.15);
+    
+    /* Z-index Scale */
+    --z-dropdown: 1000;
+    --z-modal: 2000;
+    --z-popover: 3000;
+    --z-tooltip: 4000;
+    --z-notification: 5000;
+}
+
+/* Screen Reader Only Utility */
+.sr-only {
+    position: absolute;
+    width: 1px;
+    height: 1px;
+    padding: 0;
+    margin: -1px;
+    overflow: hidden;
+    clip: rect(0, 0, 0, 0);
+    white-space: nowrap;
+    border: 0;
+}
+
+/* Focus Visible for Keyboard Navigation */
+*:focus-visible {
+    outline: 3px solid var(--color-primary);
+    outline-offset: 2px;
+}
+
+/* Remove default focus for mouse users */
+*:focus:not(:focus-visible) {
+    outline: none;
+}
+
+/* Skip to Content Link */
+.skip-link {
+    position: absolute;
+    top: -40px;
+    left: 0;
+    background: var(--color-primary);
+    color: var(--color-bg-dark);
+    padding: var(--space-sm) var(--space-md);
+    text-decoration: none;
+    z-index: var(--z-tooltip);
+}
+
+.skip-link:focus {
+    top: 0;
+}
+
+/* Reduced Motion Support */
+@media (prefers-reduced-motion: reduce) {
+    *,
+    *::before,
+    *::after {
+        animation-duration: 0.01ms !important;
+        animation-iteration-count: 1 !important;
+        transition-duration: 0.01ms !important;
+        scroll-behavior: auto !important;
+    }
+}
+
+/* High Contrast Mode Support */
+@media (prefers-contrast: high) {
+    :root {
+        --color-primary: #00ff00;
+        --color-danger: #ff0000;
+        --color-warning: #ffff00;
+    }
+}
+
+/* Dark Mode Support (already default) */
+@media (prefers-color-scheme: light) {
+    /* Provide light mode alternative if needed */
+}
+
 /* Existing styles with improvements... */
```