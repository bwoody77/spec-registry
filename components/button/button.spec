// Button — native <button> with event forwarding.
//
// Renders the `button` primitive (compiler emits <button>). Accepts:
//   label          text label (or aria-label when iconOnly is set)
//   variant        primary | secondary | ghost | destructive | link | warning
//   size           sm | md | lg
//   shape          rect | pill
//   disabled       disables interaction
//   loading        shows loading state; also disables
//   loadingLabel   text shown when loading (falls back to label if empty)
//   pressed        toggle/pressed visual
//   iconLeft       icon name rendered before label (Icon component name)
//   iconRight      icon name rendered after label
//   iconOnly       icon name; renders square button with label as aria-label
//
// Color tokens:
//   The Button reads its colors from the app's `semantic.*` palette
//   (`semantic.interactive`, `semantic.on-interactive`, `semantic.destructive`,
//   etc.) rather than from `token.btn-*`. This makes every Button automatically
//   pick up the app's configured interactive palette — primary buttons in an
//   indigo-themed app render indigo; in a blue-themed app render blue; in an
//   amber-themed dark mode render amber — with no per-app token overrides.
//   Shape tokens (radius, padding, font-weight, shadow) still come from
//   `token.btn-*` because those don't change between themes.
//
// Layout rules:
//   - Icons sit on the same horizontal line as the label, gap=spacing.2.
//   - iconOnly forces square padding (matches size).
//   - link variant has no padding-y (sits inline with text) and no bg/border.
component Button(
  label:        string,
  variant:      string  = "primary",
  disabled:     boolean = false,
  loading:      boolean = false,
  pressed:      boolean = false,
  size:         string  = "md",
  shape:        string  = "rect",
  iconLeft:     string  = "",
  iconRight:    string  = "",
  iconOnly:     string  = "",
  loadingLabel: string  = ""
) {
  @computed {
    isIconOnly: iconOnly != ""
    hasIconLeft: iconLeft != ""
    hasIconRight: iconRight != ""
    effectiveLabel: loading && loadingLabel != "" ? loadingLabel : label

    iconSize: size == "sm" ? 14 : (size == "lg" ? 20 : 16)

    iconColor:
      variant == "primary"     ? semantic.on-interactive :
      variant == "secondary"   ? semantic.text-primary :
      variant == "ghost"       ? semantic.text-secondary :
      variant == "destructive" ? semantic.on-destructive :
      variant == "warning"     ? semantic.warning-text :
      variant == "link"        ? semantic.interactive-text :
      semantic.on-interactive

    isInactive: disabled || loading

    radius: shape == "pill" ? 999px : token.btn-radius

    padX:
      variant == "link" ? 0 :
      (isIconOnly ? (size == "sm" ? spacing.1 : (size == "lg" ? spacing.3 : spacing.2)) :
       (size == "sm" ? spacing.2 : (size == "lg" ? spacing.6 : token.btn-paddingH)))

    padY:
      variant == "link" ? 0 :
      (size == "sm" ? spacing.1 : (size == "lg" ? spacing.3 : token.btn-paddingV))
  }

  // NOTE: Conditional rendering uses `visibility:` on always-emitted nodes
  // rather than `if isIconOnly { ... } else { ... }`. The `if` construct is
  // only valid inside `@actions` bodies — at the surface/component-body level
  // the parser rejects it.
  //
  // CRITICAL: `visibility:` MUST be on a `block { }` wrapper, NOT directly on
  // a Component call (e.g., `Icon(...) { visibility: X }`). Putting visibility
  // on a Component invocation compiles to `lazyMount(parent, signal, ...)` —
  // and `lazyMount` toggles the PARENT's `display` based on the signal. With
  // multiple conditionally-mounted Component children of the same parent, the
  // last lazyMount's false condition wins and hides the entire parent. The
  // block-wrapper form compiles to `bindVisibility(wrapperDiv, signal)` which
  // correctly affects only the wrapper. Empty `Icon(name: "")` calls (when
  // iconLeft/Right are not set) are tolerated by the Icon component (renders
  // a decorative aria-hidden SVG with no path).
  button {
    disabled: disabled || loading
    layout: horizontal, align: center, justify: center, gap: spacing.2
    padding-x: padX
    padding-y: padY
    border-radius: radius
    shadow: match pressed {
      true -> "inset 0 1px 3px rgba(0,0,0,0.2)",
      _ -> match variant {
        "link" -> "none",
        _ -> token.btn-shadow
      }
    }
    font-weight: token.btn-fontWeight
    text-transform: token.btn-textTransform
    letter-spacing: token.btn-letterSpacing
    transition: transition.interactive-full
    cursor: match isInactive {
      true -> "default",
      _ -> "pointer"
    }
    opacity: match loading {
      true -> 0.7,
      _ -> match disabled {
        true -> 0.5,
        _ -> 1
      }
    }
    background: match pressed {
      true -> match variant {
        "primary" -> semantic.interactive-hover,
        "secondary" -> semantic.surface-hover,
        "ghost" -> semantic.surface-hover,
        "destructive" -> semantic.destructive-hover,
        "warning" -> semantic.warning-hover,
        "link" -> "transparent",
        _ -> semantic.interactive-hover
      },
      _ -> match variant {
        "primary" -> semantic.interactive,
        "secondary" -> semantic.surface,
        "ghost" -> "transparent",
        "destructive" -> semantic.destructive,
        "warning" -> semantic.warning-bg,
        "link" -> "transparent",
        _ -> semantic.interactive
      }
    }
    border: match variant {
      "secondary" -> borders.default,
      "warning"   -> borders.warning,
      _ -> "none"
    }

    on hover {
      background: match variant {
        "primary" -> semantic.interactive-hover,
        "secondary" -> semantic.surface-hover,
        "ghost" -> semantic.surface-hover,
        "destructive" -> semantic.destructive-hover,
        "warning" -> semantic.warning-hover,
        "link" -> "transparent",
        _ -> semantic.interactive-hover
      }
    }

    on active {
      transform: "scale(.97)"
    }

    on click: emit("click")

    // Icon-only mode
    block {
      visibility: isIconOnly
      layout: horizontal, align: center, justify: center
      Icon(name: iconOnly, size: iconSize, color: iconColor, label: label)
    }

    // Label mode: optional left icon + text + optional right icon
    block {
      visibility: !isIconOnly && hasIconLeft
      layout: horizontal, align: center, justify: center
      Icon(name: iconLeft, size: iconSize, color: iconColor)
    }

    block {
      visibility: !isIconOnly
      layout: horizontal, align: center, justify: center

      text(effectiveLabel) {
        style: type.label-md
        font-weight: token.btn-fontWeight
        color: match variant {
          "primary" -> semantic.on-interactive,
          "secondary" -> semantic.text-primary,
          "ghost" -> semantic.text-secondary,
          "destructive" -> semantic.on-destructive,
          "warning" -> semantic.warning-text,
          "link" -> semantic.interactive-text,
          _ -> semantic.on-interactive
        }
      }
    }

    block {
      visibility: !isIconOnly && hasIconRight
      layout: horizontal, align: center, justify: center
      Icon(name: iconRight, size: iconSize, color: iconColor)
    }
  }
}
