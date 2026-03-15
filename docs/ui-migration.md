# UI Migration Guide

Please refer to our UI designs here: [https://www.figma.com/design/UbTpqtrgdtmvlvYvuAzGgd/Diagram-and-UI-Designs?node-id=637-4285&m=dev](https://www.figma.com/design/UbTpqtrgdtmvlvYvuAzGgd/Diagram-and-UI-Designs?node-id=637-4285&m=dev)
---

## Core decisions

### Theme
Global theme values live in:

- `src/index.css`

Use these baseline values:

- brand navy: `#001166`
- page background: light gray-blue
- card background: white
- default border: soft gray
- app font: `Roboto`
- logo font: `Open Sans Bold`

### Shared components
Reusable components live in:

- `src/components/shared/`

Use those instead of creating new one-off page styles where possible.

### Icons
Standard UI icons should come from:

- `src/lib/ui-icons.ts`

That file re-exports the Lucide icons we want to standardize on.

### Custom SVGs / artwork
Only export and store **custom** design assets such as:
- auth illustrations
- project thumbnails
- custom decorative graphics
- logo artwork if not text-based

Do **not** export normal UI icons from Figma if Lucide already has them.

Suggested folder:
- `src/assets/ui/`

---

## Component inventory

## Buttons
Use `AppButton`.

Supported variants:
- `primary`
- `secondary`
- `outline`
- `destructive`
- `ghost`
- `icon`

Supported sizes:
- `sm`
- `default`
- `lg`
- `icon`

### When to use each button
- `primary`: main call to action
- `secondary`: supporting CTA
- `outline`: neutral actions like back, cancel, export trigger
- `destructive`: delete/remove/discard
- `ghost`: subtle inline actions
- `icon`: icon-only controls

---

## Inputs
Use:
- `AppInput`
- `AppTextarea`
- `AppSelect`
- `AppField`

`AppField` is the wrapper for label + field + helper/error text.

---

## Modals
Use:
- `AppDialogShell` for standard create/edit/detail modals
- `ConfirmDialog` for destructive confirmation

Approximate modal design:
- white surface
- rounded corners
- subtle shadow
- close button at top right
- footer actions aligned right

---

## Layout
Use:
- `PageContainer`
- `PageHeader`
- `SectionHeader`
- `SectionCard`
- `Breadcrumbs`

These should be the default structure for new/refactored pages.

---

## Tags / badges
Use:
- `TagPill`

Variants:
- `neutral`
- `primary`
- `success`
- `warning`
- `destructive`

Use these for:
- project type
- project mode
- skills
- status
- category labels

---

## Feature tiles / large cards
Use:
- `FeatureTile`

This is for larger clickable destination cards such as:
- outputs landing tiles
- dashboard shortcuts
- large entry-point cards

---

## Standard icon set

Import from `src/lib/ui-icons.ts`.

Current standardized icons:
- `CircleUserRound` for profile
- `Plus` for create/add
- `Pencil` for edit
- `Trash2` for delete
- `Upload` for upload
- `FileText` for resume/document
- `BriefcaseBusiness` or `Briefcase` for portfolio/work
- `FolderOpen` for project/folder
- `Globe` for web/portfolio
- `ChevronRight`, `ChevronDown` for navigation
- `MoreVertical` for overflow menu
- `Download` for export/download
- `Search` for search
- `SlidersHorizontal` for filters
- `Mail`, `Link`, `Github` for external/contact links
- `AlertTriangle`, `Info`, `CheckCircle2` for status/feedback

---

## Migration rules

### Good
- keep existing page logic as-is
- adopt shared components when touching a page UI
- replace one-off buttons with `AppButton`
- replace one-off modals with `AppDialogShell`
- use Lucide icons instead of exporting standard icons from Figma
- keep the shared theme consistent

### Avoid
- adding more random page-specific button classes
- exporting common UI icons as SVGs
- creating new modal overlay/content styles from scratch
- changing unrelated feature logic inside UI-only PRs

---

## Suggested migration order

1. Shared navigation and shell
2. Buttons, dialogs, and fields
3. Lower-risk pages
4. Feature-heavy pages after active work settles

---

## Approximation note
This baseline is based on the redesigned screenshots and intended visual language, not pixel-perfect Figma token extraction.

If exact spacing or sizing becomes important later, those values can be refined without changing the component names or overall system.