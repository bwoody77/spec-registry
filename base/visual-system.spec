// Design tokens — baseline visual system + 9 Ant Design-style themes
//
// Canonical design token file. Imported by app.spec via bare import:
//   @import "../visual-system.spec"

@visual-system {
  spacing: 4px-unit
  type-scale: 1.25-ratio, base 14px
  palette: slate(neutral), indigo(primary), red(danger), emerald(success), amber(warning)
  radius: 6px(sm), 8px(md), 12px(lg), 9999px(full)
  motion: 150ms ease(default), 100ms ease(quick), 300ms ease(slow)

  // Semantic colors — text
  semantic.text-primary: "#202732"
  semantic.text-secondary: "#496183"
  semantic.text-tertiary: "#92a2b9"
  semantic.text-disabled: "#bdc5d1"
  semantic.text-muted: "#5c7aa3"
  semantic.text-strong: "#3b4e68"

  // Semantic colors — surfaces
  semantic.surface: "#f7f7f8"
  semantic.surface-raised: "#ffffff"
  semantic.surface-hover: "#eeeff1"
  semantic.surface-unread: "#f0f9ff"
  semantic.background: "#ffffff"
  semantic.border: "#dce0e5"
  semantic.border-strong: "#92a2b9"

  // Semantic colors — interactive
  semantic.interactive: "#1677ff"
  semantic.interactive-hover: "#0958d9"
  semantic.interactive-active: "#003eb3"
  semantic.focus-ring: "#91caff"
  semantic.info-bg: "#e6f4ff"
  semantic.on-interactive: "#ffffff"
  semantic.focus-ring-shadow: "rgba(22,119,255,.12)"
  // Aliases — semantic.primary and semantic.accent map to semantic.interactive
  semantic.primary: "#1677ff"
  semantic.accent: "#1677ff"

  // Semantic colors — destructive/error
  semantic.destructive: "#ff4d4f"
  semantic.destructive-hover: "#cf1322"
  semantic.error: "#cf1322"
  semantic.error-bg: "#fff2f0"
  semantic.on-destructive: "#ffffff"

  // Semantic colors — success
  semantic.success: "#52c41a"
  semantic.success-light: "#f6ffed"
  semantic.success-muted: "#d9f7be"
  semantic.success-text: "#135200"
  semantic.success-mid: "#389e0d"

  // Semantic colors — warning
  semantic.warning: "#faad14"
  semantic.warning-light: "#fffbe6"
  semantic.warning-muted: "#fff1b8"
  semantic.warning-text: "#614700"

  // Severity tokens (shared between badges + alerts)
  severity.info-bg: "#e6f4ff"
  severity.info-color: "#1677ff"
  severity.info-border: "#91caff"
  severity.success-bg: "#f6ffed"
  severity.success-color: "#52c41a"
  severity.success-border: "#d9f7be"
  severity.warning-bg: "#fffbe6"
  severity.warning-color: "#faad14"
  severity.warning-border: "#fff1b8"
  severity.error-bg: "#fff2f0"
  severity.error-color: "#ff4d4f"
  severity.error-border: "#ffccc7"

  // Borders
  borders.default: "1px solid #dce0e5"
  borders.strong: "1px solid #92a2b9"
  borders.accent-error: "3px solid #ff4d4f"
  borders.accent-warning: "3px solid #faad14"
  borders.accent-success: "3px solid #52c41a"
  borders.accent-interactive: "3px solid #1677ff"
  borders.accent-interactive-strong: "4px solid #1677ff"
  borders.accent-none: "3px solid transparent"
  borders.success: "1px solid #d9f7be"
  borders.section-accent: "2px solid #1677ff30"

  // Gradients
  gradient.stat-primary: "linear-gradient(135deg, #e6f4ff, #91caff)"
  gradient.stat-primary-subtle: "linear-gradient(135deg, #e6f4ff, #bae0ff)"
  gradient.stat-success: "linear-gradient(135deg, #f6ffed, #d9f7be)"
  gradient.stat-success-subtle: "linear-gradient(135deg, #f6ffed, #b7eb8f)"
  gradient.stat-warning: "linear-gradient(135deg, #fffbe6, #fff1b8)"
  gradient.stat-warning-subtle: "linear-gradient(135deg, #fffbe6, #ffe58f)"
  gradient.stat-neutral: "linear-gradient(135deg, #f7f7f8, #bdc5d1)"
  gradient.stat-neutral-subtle: "linear-gradient(135deg, #f7f7f8, #dce0e5)"
  gradient.header-accent: "linear-gradient(135deg, #1677ff15, #1677ff05)"
  gradient.app-background: "none"

  // Transitions
  transition.card-lift: "transform 200ms ease, box-shadow 200ms ease"
  transition.subtle: "transform 150ms ease"
  transition.scale: "transform 200ms ease"
  transition.interactive: "box-shadow 150ms ease, transform 150ms ease"
  transition.interactive-full: "box-shadow 150ms ease, background-color 150ms ease, transform 150ms ease"
  transition.row-hover: "background-color 150ms ease, box-shadow 150ms ease, border-left 150ms ease, transform 150ms ease"
  transition.shadow: "box-shadow 150ms ease"
  transition.shadow-slow: "box-shadow 200ms ease"
  transition.shadow-slower: "box-shadow 300ms ease"
  transition.focus: "border-color 150ms ease, box-shadow 150ms ease"
  transition.expand: "max-height 250ms ease, transform 250ms ease"
  transition.fill: "width 300ms ease"
  transition.fade: "opacity 150ms ease"

  // Transforms
  transform.lift-xs: "translateY(-1px)"
  transform.lift-sm: "translateY(-2px)"
  transform.lift-md: "translateY(-3px)"
  transform.lift-lg: "translateY(-4px)"
  transform.nudge-right: "translateX(4px)"
  transform.nudge-right-sm: "translateX(2px)"
  transform.grow-sm: "scale(1.02)"

  // Icon sizes
  icon.xs: "16px"
  icon.sm: "18px"
  icon.md: "20px"
  icon.lg: "24px"
  icon.xl: "32px"
  icon.xxl: "48px"

  // Elevation
  elevation.flat: "none"
  elevation.raised: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)"
  elevation.layered: "0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)"
  elevation.floating: "0 10px 25px rgba(0,0,0,0.1), 0 4px 10px rgba(0,0,0,0.05)"
  elevation.overlay: "0 8px 32px rgba(0,0,0,0.12)"
  elevation.inset: "inset 0 2px 4px rgba(0,0,0,0.06)"
}

// ---------------------------------------------------------------------------
// 1. Dark — dark surfaces, light text, indigo interactive
// ---------------------------------------------------------------------------
