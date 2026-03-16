# UI Migration Guide

Please refer to our UI designs here:  
[https://www.figma.com/design/UbTpqtrgdtmvlvYvuAzGgd/Diagram-and-UI-Designs?node-id=637-4285&m=dev](https://www.figma.com/design/UbTpqtrgdtmvlvYvuAzGgd/Diagram-and-UI-Designs?node-id=637-4285&m=dev)

---

## Purpose

This PR adds the shared baseline UI components and theme styles for the redesigned frontend.

It is **not** a full page-by-page refactor.  
The goal is to give everyone a shared source of truth so pages can be migrated gradually without blocking ongoing feature work.

You can preview the shared baseline at:

- `/ui-preview`

---

## Source of truth

### Figma
Figma is the visual source of truth for layout and styling.

### Code
Shared UI styles and tokens live in:

- `src/index.css`

Reusable shared components live in:

- `src/components/shared/`

Standardized icon exports live in:

- `src/lib/ui-icons.ts`

---

## Core decisions

### Theme
Global theme values live in:

- `src/index.css`

Current baseline values:
- brand navy: `#001166`
- text/icon gray: `#6C6C6C`
- border gray: `#ECECEC`
- page background: `#F6F6F6`
- white surface: `#FFFFFF`

### Fonts
- app font: `Roboto`
- logo font: `Open Sans Bold`

### Radius
- buttons: `2px`
- inputs / selects / textareas: `2px`
- tiles / cards / modals / menus: `5px`

---

## Typography scale

Use this as the baseline type scale from the redesign:

- tiniest helper text in dialogs: `13px`
- header/helper text in dialogs: `14px`
- dialog/modal title: `18px`
- all button text: `14px`
- tag pill text: `14px`
- overflow menu items: `12px`
- tile labels: `20px`
- path text / breadcrumb text: `16px`
- top bar nav text: `16px`
- logo: `36px`

### Font weights in use
Use Roboto weights that appear in the designs:
- `light`
- `regular`
- `medium`
- `bold`

Use Open Sans Bold only for the `resuME` wordmark/logo.

---

## Layout rules

### Top bar
Use `TopBar`.

Current baseline:
- height: `64px`
- inner content width: `1140px`
- background: `#001166`
- nav text: `16px`
- logo: `36px`
- profile button uses light gray circular background

### Page container
Use `PageContainer`.

Current baseline:
- max width: `1140px`
- centered layout
- standard page padding handled in component

### Breadcrumbs
Use `Breadcrumbs`.

Formatting:
- use `/` as separator
- example: `Home / Projects`
- text size: `16px`

### Page header
Use `PageHeader` for:
- breadcrumb path
- page title
- optional subtitle
- optional right-side actions

### Section surface
Use `SectionCard` for standard white bordered containers.

---

## Shared component inventory

## Buttons
Use `AppButton`.

Supported variants:
- `primary`
- `outline`
- `ghost`
- `destructive`

Supported sizes:
- `sm`
- `default`
- `lg`
- `icon`

### Usage
- `primary`: main CTA
- `outline`: cancel / back / secondary action
- `ghost`: subtle inline action
- `destructive`: delete/remove/discard
- `icon`: icon-only actions

### Notes
- all button text should be `14px`
- button corner radius should stay `2px`

---

## Fields
Use:
- `AppInput`
- `AppTextarea`
- `AppSelect`
- `AppField`

`AppField` is the wrapper for:
- label
- field
- helper text
- error text

### Notes
- inputs/selects/textareas use `2px` corner radius
- helper/error text in dialogs should use the dialog text scale above

---

## Radio buttons
Use:
- `AppRadio`

### Notes
- should be circular
- should become fully navy when selected
- should match the dialog text sizing

---

## Tabs
Use:
- `SectionTabs`

### Notes
This is the tab pattern with:
- simple text labels
- blue underline for active tab
- no extra pill/badge styling

---

## Overflow / three-dot menu
Use:
- `OverflowMenu`

### Notes
This is the three-dot popup pattern used for settings/thumbnail actions.
- menu text: `12px`
- white surface
- subtle shadow
- no wrapping text

---

## Modals / popups
Base shell:
- `AppDialogShell`

Specific popup components currently included:
- `CreateResumeDialog`
- `ContactDialog`
- `ContributionBulletsDialog`
- `DurationDialog`
- `ConfirmDialog`

### Notes
- modal title: `18px`
- helper/header text in modal: `14px`
- smallest helper text in modal: `13px`
- modal surface radius: `5px`
- modal/footer actions should reuse `AppButton`

---

## Tags / pills
Use:
- `TagPill`

### Important
Use only the neutral pill style currently present in the redesign.

Examples:
- `Code`
- `Individual`

Do **not** introduce extra colored status pill variants unless a page actually needs them later and the design supports it.

---

## Feature tiles
Use:
- `FeatureTile`

### Current baseline
- tile size: `343 x 245`
- tile radius: `5px`
- upper section: light gray background
- lower section: white label row
- label text: `20px`

Use this for:
- outputs landing tiles
- other large destination tiles if the design calls for them

---

## Icons

Import from:

- `src/lib/ui-icons.ts`

Use Lucide for standard UI icons.

Current standardized icons include:
- `CircleUserRound`
- `Plus`
- `Pencil`
- `Trash2`
- `Upload`
- `FileText`
- `BriefcaseBusiness`
- `ChevronDown`
- `MoreVertical`
- `Mail`
- `Link`
- `Github`
- `Globe`

### Custom SVGs / artwork
Only export and store **custom** design assets such as:
- auth illustrations
- project thumbnails
- decorative graphics
- logo artwork if needed

Do **not** export normal UI icons from Figma if Lucide already has them.

Suggested folder:
- `src/assets/ui/`

---

## Preview page

Shared components can be previewed at:

- `/ui-preview`

This page is for internal reference only.  
Use it to check:
- typography
- buttons
- fields
- radios
- pills
- tiles
- tabs
- overflow menu
- popup/modal patterns

---

## Migration rules

### Good
- keep existing page logic as-is
- adopt shared components when touching a page UI
- replace one-off buttons with `AppButton`
- replace one-off modal structures with the shared modal components
- use Lucide icons instead of exporting common icons from Figma
- match the Figma typography/radius/colors before inventing new styles

### Avoid
- adding more page-specific button classes
- exporting standard UI icons as SVGs
- creating new modal structures from scratch when a shared one already exists
- adding colored pills not present in the design
- changing unrelated feature logic in UI-only PRs

---

## Suggested migration order

1. Shared navigation and shell
2. Shared buttons, fields, radios, tabs, and menus
3. Shared modal/popup patterns
4. Lower-risk page migrations
5. Feature-heavy pages after active development settles

---

## Important note

This baseline should follow the Figma designs as closely as possible.

If a shared component does not match the Figma:
- update the shared component
- do not create a one-off local workaround unless absolutely necessary

The goal is for teammates to reuse the shared baseline instead of reinventing styles page by page.