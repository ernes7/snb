# DESIGN.md — Serie Nacional de Béisbol

> The official digital home of Cuban baseball. Dense with data, blazing fast, serious but warm.

---

## 1. Design Philosophy

**"The Scoreboard, Elevated."**

This is a stats-first interface built for fans who live and breathe baseball numbers. Every pixel earns its place. No decorative fluff, no emoji, no gimmicks — just clean, confident information density wrapped in a design that feels like opening a fresh box score in the morning paper.

Think: ESPN data density meets the warmth of a well-worn leather glove.

---

## 2. Color Palette

Classic baseball. Navy anchors authority, red signals energy, cream softens the blow of dense tables.

| Token | Hex | Role |
|---|---|---|
| `--navy-900` | `#0C1A2E` | Primary background, nav, headers |
| `--navy-700` | `#1B3254` | Hover states, active nav backgrounds |
| `--navy-500` | `#2D4F7E` | Secondary text, borders |
| `--red-600` | `#C62828` | Primary CTA, alerts, emphasis |
| `--red-700` | `#A51C1C` | CTA hover/pressed state |
| `--cream-50` | `#FDF8F0` | Page background (light mode) |
| `--cream-100` | `#F5EDE0` | Card backgrounds, table alternating rows |
| `--cream-200` | `#E8DCC8` | Borders, dividers |
| `--white` | `#FFFFFF` | Card surfaces, input fields |
| `--gray-600` | `#5A5A5A` | Body text on light backgrounds |
| `--gray-400` | `#9E9E9E` | Muted/secondary labels |
| `--green-600` | `#2E7D32` | Win indicators, positive stats |
| `--gold-500` | `#D4A017` | Highlights, awards, leader badges |

### Usage Rules
- Navy + cream is the default pairing. Red is reserved for action and emphasis only.
- Never use red for body text or large surfaces.
- Team-specific accent colors override `--red-600` on team profile pages only.

---

## 3. Typography

Two fonts. No more.

| Role | Font | Weight | Fallback |
|---|---|---|---|
| Display / Headers | **Barlow Condensed** | 700, 800 | Arial Narrow, sans-serif |
| Body / Data / UI | **Source Sans 3** | 400, 600, 700 | system-ui, sans-serif |

### Scale (rem, base 16px)

| Token | Size | Use |
|---|---|---|
| `--text-xs` | 0.6875rem (11px) | Fine print, stat footnotes |
| `--text-sm` | 0.75rem (12px) | Table cells, secondary labels |
| `--text-base` | 0.875rem (14px) | Body text, nav items |
| `--text-lg` | 1rem (16px) | Card titles, form labels |
| `--text-xl` | 1.25rem (20px) | Section headers |
| `--text-2xl` | 1.75rem (28px) | Page titles |
| `--text-3xl` | 2.25rem (36px) | Hero scores, big numbers |
| `--text-4xl` | 3rem (48px) | Splash stats, landing hero |

### Rules
- Barlow Condensed is for headlines, scores, and standings column headers only.
- Source Sans 3 handles everything else — it's legible at 11px for dense stat tables.
- Numbers in tables use `font-variant-numeric: tabular-nums` for column alignment.
- ALL CAPS on Barlow headers. Mixed case on Source Sans body.

---

## 4. Spacing & Layout

### Grid
- 12-column grid, max-width `1360px`, center-aligned.
- Gutter: `16px`. Outer padding: `24px` (desktop), `16px` (mobile).
- Sidebar nav: fixed `240px` on desktop, collapsible drawer on tablet/mobile.

### Spacing Scale

| Token | Value |
|---|---|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 24px |
| `--space-6` | 32px |
| `--space-7` | 48px |
| `--space-8` | 64px |

### Density Principle
- Default to tight spacing (`--space-2` to `--space-3` inside data components).
- Use `--space-5` or more only between major sections.
- Stat tables: row height `36px`, cell padding `8px 12px`.

---

## 5. Component Library

### 5.1 Cards
- Background: `--white`
- Border-radius: `12px`
- Shadow: `0 1px 3px rgba(0,0,0,0.08)` at rest
- Shadow hover: `0 4px 12px rgba(0,0,0,0.12)`
- Padding: `--space-4` to `--space-5`
- No visible border by default. Use `1px solid --cream-200` only when cards sit on `--cream-50`.

### 5.2 Buttons (CTAs)

**Primary (Red)**
- Background: `--red-600`, text: `--white`
- Border-radius: `8px`
- Padding: `10px 20px`
- Font: Source Sans 3, 600, `--text-base`
- Hover: `--red-700`, `translateY(-1px)`, shadow `0 4px 8px rgba(198,40,40,0.3)`
- Active/pressed: `translateY(1px)`, shadow `0 1px 2px rgba(198,40,40,0.3)` — the "elevated click" feel
- Transition: `all 150ms ease`

**Secondary (Navy outline)**
- Background: transparent, border `1.5px solid --navy-700`, text `--navy-700`
- Hover: fill `--navy-700`, text `--white`
- Same radius/padding/pressed behavior as primary.

**Ghost**
- No background, no border, text `--navy-500`
- Hover: background `--cream-100`
- Use for tertiary actions and toolbar icons.

### 5.3 Navigation (Sidebar)
- Fixed left sidebar, `240px` wide, background `--navy-900`.
- Nav items: Source Sans 3 600, `--text-base`, `--white` at 70% opacity.
- Active item: 100% opacity, left `3px` accent bar in `--red-600`, background `rgba(255,255,255,0.08)`.
- Hover: background `rgba(255,255,255,0.05)`.
- Item padding: `12px 20px`, border-radius `8px` (right side only to hug the left edge).
- Logo + "Serie Nacional" lockup pinned top, `--space-6` margin bottom.
- Collapse to icon-only rail at `<1024px`, full drawer overlay at `<768px`.

### 5.4 Stat Tables
- This is the heart of the product. Tables must be scannable at a glance.
- Header row: `--navy-900` background, `--white` text, Barlow Condensed 700 uppercase `--text-sm`.
- Body rows: alternating `--white` / `--cream-100`.
- Row hover: `--cream-200` highlight.
- Sticky first column (player/team name) on horizontal scroll.
- Sticky header on vertical scroll.
- Sortable columns: click header to sort, subtle chevron indicator. Use `data-sort="num"` or `data-sort="text"` on `<th>` elements + call `initSortableTable()` in `{% block scripts %}` (after app.js loads).
- Leader highlight: `--gold-500` left border on top-3 rows for leaderboard tables.
- Cell alignment: text left, numbers right, consistent `tabular-nums`.

### 5.4.1 Standings Table
- **Bold numbers**: Barlow Condensed at `--text-2xl`, font-weight 700 — the biggest numbers on any table.
- **Logo bleed column**: First column is a dedicated logo cell (no header text, 90px wide). Logo is 90x90px at 90% opacity, positioned left-aligned with `-10px` offset so the left edge gets cropped. Vertically cropped by the row height via `overflow: hidden` wrapper. This creates a bold branded feel — the logo peeks through the row, partially cut on three sides (left, top, bottom).
- No rank `#` column — the standings order speaks for itself.
- No owner/PCT columns — keep it clean: Equipo, G, P, GB, CA, CL, DIF.

### 5.5 Logo Bleed Pattern
A signature design pattern used across the app. Team logos are oversized and partially cropped by their container's `overflow: hidden`, creating a bold branded feel.

**Three sizes (via `logo_img` component):**
| Class | Size | Use |
|---|---|---|
| `inline-logo` (default) | 64px | Large contexts: team headers, player pages |
| `inline-logo-md` | 32px | Dense tables: leaderboards, linescore, box scores |
| `inline-logo-sm` | 16px | Compact inline: schedule rows, small labels |

**Bleed applications:**
- **Game cards** (horizontal bleed): Logos at card left/right edges, cropped by card's `overflow: hidden`. Fully opaque.
- **Standings rows** (vertical + left bleed): 90px logo in a narrow cell, offset left by `-10px`, cropped top/bottom by row height and left by cell edge. 90% opacity.
- Prefer this clipped-logo pattern whenever logos appear as decorative elements in compact containers.

### 5.6 Recent Games Strip
- Horizontal row of recent game result cards at top of homepage.
- Each card: final score (large), W/L pitcher credits. No team abbreviation text.
- Uses logo bleed pattern (see 5.5) — logos at card edges, cropped horizontally.
- Click navigates to game detail / box score.
- Static content — no polling, no live updates.

### 5.6 Tabs
- Underline style. Active tab: `--navy-900` text + `2px` bottom border `--red-600`.
- Inactive: `--gray-400` text, no border.
- Font: Source Sans 3 600, `--text-base`.
- Use for switching between stat categories (Batting / Pitching / Fielding).

### 5.7 Badges & Tags
- Border-radius: `6px`, padding `2px 8px`.
- "FINAL": `--gray-400` bg, white text. Applied to all completed game cards.
- Team tags: team accent color bg, white text.
- Stat leader: `--gold-500` bg, `--navy-900` text.

---

## 6. Interface Principle — Read-Only, Data-Rich

This is a **consumption-only** interface. No forms, no editing, no CRUD, no live tracking. The app reads from a `.db` file populated with box scores after each game. Users check in after a game or at the end of a week (4-game series). The entire UX is built around viewing, filtering, searching, and sorting static data. Every page should feel like opening a dense, well-organized stat sheet.

### Interaction Model
- **Search**: Global search bar in top nav — searches players, teams, games. Instant results dropdown.
- **Filters**: Dropdowns and toggle chips (by team, by season, by stat category). Always visible, never hidden behind a "Filter" button.
- **Sorting**: Click any table column header to sort. Visual chevron indicator.
- **No modals for data**. Everything navigates to a dedicated page. Modals only for search overlay.

---

## 7. Page Map

| Route | Page | Purpose | Key Data on Page |
|---|---|---|---|
| `/` | **Homepage** | Season snapshot | Standings table, last 10 games with scores, stat leaders sidebar, season progress bar |
| `/team/<short>` | **Team Detail** | Single team hub | Team header (logo, record, streak), roster table, batting & pitching leaders, recent results, team accent color on header |
| `/player/<int:id>` | **Player Detail** | Individual player | Bio card (photo, team, pos, bats/throws), career stats table, season splits, sortable game log, draft info badge |
| `/jugadores` | **Player Database** | Full player index | Filterable/sortable table — name, team, pos, age, AVG/HR/RBI or ERA/W/K. Search bar + position/team filters |
| `/schedule` | **Schedule** | 96-game season | Calendar grid or list view toggle, scores for completed games, team filter, month/week nav |
| `/game/new/<id>` | **Game Detail** | Single game box score | Linescore, batting box (both teams), pitching box, scoring plays timeline, W/L/SV pitcher callout |
| `/draft` | **Draft** | Draft picks tracker | Round-by-round pick table, team filter, player links, team draft ranking sidebar |
| `/playoffs` | **Playoffs** | Postseason bracket | Visual bracket (Semi A, Semi B, Final), series scores, elimination badges, click-through to game detail |
| `/leaders` | **Stat Leaders** | Leaderboards | Category tabs (AVG, HR, RBI, ERA, W, K, SB, OPS), top-20 tables, season selector, qualifier note |
| `/antesala` | **Antesala** | Analyst show hub | Prediction cards (analyst picks + records), embedded posts, weekly poll results, hot takes feed |
| `/weekly` | **Weekly Recap** | Week in review | POTW card, power rankings 1–16 with movement arrows, analyst tweet roundup, stat highlights |

### Page Density Guidelines
- Homepage: minimum 3 data widgets visible above the fold (standings + scores + leaders).
- Team/Player detail: lead with numbers, bio is secondary. No paragraph walls.
- Tables are the primary content type. Every page has at least one sortable table.
- Leaderboards show top 20 minimum. No "Show more" for fewer than 50 rows — just render them.

---

## 8. Interaction & Motion

### Principles
- Speed is the feature. Target `<100ms` perceived response on all interactions.
- No page-level transitions. Instant route swaps.
- Subtle component-level animation only where it communicates state change.

### Specifics
- **Page load**: Cards stagger in with `opacity 0→1`, `translateY(8px→0)`, `200ms` each, `40ms` delay between. One pass only, no repeat on scroll.
- **Button press**: `translateY` shift (see 5.2). `150ms ease`.
- **Table sort**: Rows crossfade reorder, `150ms`.
- **Tab switch**: Content fades, `120ms`. No slide.
- **Hover states**: `120ms` transitions on all interactive elements.
- **No parallax. No scroll-jacking. No skeleton loaders longer than 200ms.**

---

## 9. Responsive Breakpoints

| Token | Width | Layout Shift |
|---|---|---|
| `--bp-desktop` | ≥1280px | Full sidebar + 12-col grid |
| `--bp-laptop` | 1024–1279px | Collapsed icon rail + 12-col |
| `--bp-tablet` | 768–1023px | Drawer nav + 8-col grid, tables scroll horizontally |
| `--bp-mobile` | <768px | Bottom tab bar + single column, recent games strip stacks vertically |

### Mobile-Specific
- Stat tables become horizontally scrollable with sticky name column.
- Cards stack single-column with `--space-3` gap.
- Recent games strip becomes swipeable carousel.
- Bottom tab bar: 5 icons max (Home, Scores, Standings, Stats, Menu).

---

## 10. Performance Targets

| Metric | Target |
|---|---|
| LCP | < 1.2s |
| FID | < 50ms |
| CLS | < 0.05 |
| TTI | < 2.0s |
| Bundle (initial) | < 120KB gzipped |
| Font load | Preload critical weights, swap display |

### Rules
- No client-side data fetching waterfalls. Prefetch next-likely routes.
- Images: WebP/AVIF, lazy-loaded below fold, explicit `width`/`height` on all `<img>`.
- Tables virtualize rows beyond 50. No full DOM render for 500-row stat sheets.
- Team logos: single SVG sprite sheet, inline critical ones.

---

## 11. Accessibility

- WCAG 2.1 AA minimum across all pages.
- All navy-on-cream and red-on-white combos verified at 4.5:1+ contrast ratio.
- `--red-600` on `--white` = 5.2:1 (passes).
- `--navy-900` on `--cream-50` = 13.8:1 (passes).
- Focus rings: `2px solid --red-600`, `2px` offset. Never remove outline.
- All tables use proper `<th scope>`, `<caption>`, and `aria-sort`.
- Skip-to-content link on every page.
- Keyboard navigable: all interactive elements reachable via Tab, activated via Enter/Space.

---

## 12. Iconography

- Style: 1.5px stroke, rounded caps and joins. Consistent 24x24 grid.
- Source: Lucide icon set as base, custom icons for baseball-specific concepts (diamond, bat, glove, pitcher silhouette).
- Color: inherit from parent text color. Never multi-color icons.
- Active nav icons: filled variant. Inactive: stroke only.

---

## 13. Voice & Tone (UI Copy)

- Direct. Confident. No exclamation marks in UI labels.
- Spanish-first, with language toggle to English.
- Stats abbreviations follow standard baseball convention (AVG, HR, ERA, WHIP, OPS).
- Date format: `11 sep 2023` or `11/09/2023` — day first, always.
- Time format: 24h (`19:00`) with timezone label.
- No "Welcome back!" or chatty microcopy. The data speaks.
