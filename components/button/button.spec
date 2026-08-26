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
//   pressed        the "on" position — visual by default, announced when
//                  `toggle` or `disclosure` says what it MEANS
//   toggle         opt in: announce `pressed` as aria-pressed (a toggle button)
//   disclosure     opt in: announce `pressed` as aria-expanded (show/hide)
//   iconLeft       icon name rendered before label (Icon component name)
//   iconRight      icon name rendered after label
//   iconOnly       icon name; renders square button with label as aria-label
//   ariaLabel      overrides the accessible name; the visible label is unchanged
//
// PRESSED IS A PAINT UNTIL YOU SAY WHAT IT MEANS.
//   `pressed` darkens the background and insets the shadow. That is all it did:
//   a screen reader announced the "Night" filter chip identically in both
//   positions, exactly the way Toggle used to (see toggle.spec's header). The
//   obvious fix — always emit `aria-pressed: pressed` — is worse than the gap,
//   because the default is `false` and every ordinary Save/Cancel/Delete button
//   in the app would then announce itself as an UNPRESSED TOGGLE BUTTON. A
//   component cannot tell "the caller passed false" from "the caller never
//   mentioned pressed", so the semantics have to be opted into:
//
//     Button(label: 'Night', pressed: isNight, toggle: true)        // aria-pressed
//     Button(label: 'Config', pressed: cfgOpen, disclosure: true)   // aria-expanded
//     Button(label: 'Save')                                         // neither attribute
//
//   A plain button emits NEITHER attribute — the bindings evaluate to `null`,
//   which removes the attribute (ai-reference.md §31b; same idiom as
//   bottom-tab-bar.spec's `aria-current: … ? "page" : null`). Absence is the
//   correct announcement for a button that is not a toggle; "false" is not.
//
//   `disclosure` wins if both are set. A show/hide button is the more specific
//   claim, and aria-pressed + aria-expanded on one control announces two
//   different state machines for a single boolean.
//
// ariaLabel exists for the case where the visible label is the right length for
// the layout but too terse for someone who cannot see the surrounding context —
// most often a button whose meaning is carried by an icon the screen reader
// ignores. `Button(label: 'Open documents', iconRight: 'external-link',
// ariaLabel: 'Open documents (opens in a new tab)')` renders the short label and
// announces the long one. Leave it empty and the accessible name is the visible
// label, exactly as before.
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
  toggle:       boolean = false,
  disclosure:   boolean = false,
  // "xs" | "sm" | "md" | "lg". NOTE that until xs was added, `size` only
  // ever changed PADDING — the label is type.label-md at sm, md and lg
  // alike, so a `size:"sm"` button still renders a 16px label. A dense
  // list of them therefore reads as a list of headlines. Redefining "sm"
  // would restyle every small button in every consuming app, so "xs" is a
  // new value that shrinks BOTH, and nothing existing moves.
  size:         string  = "md",
  shape:        string  = "rect",
  iconLeft:     string  = "",
  iconRight:    string  = "",
  iconOnly:     string  = "",
  loadingLabel: string  = "",
  ariaLabel:    string  = "",
  // Where the content sits along the button's own main axis:
  // "start" | "center" | "end" | "between" | "around" | "evenly". Defaults to
  // "center", which is what every Button rendered before this prop existed, so
  // a call site that never mentions it does not move.
  //
  // It exists because a Button is not always the width of its label. The
  // compiler dissolves a component root that wraps a single inert child to
  // `display: contents`, and Button's root IS one `button {}` — so inside a
  // `layout: vertical` block the <button> becomes the column's flex item and
  // stretches to the container's full width. `justify: center` then parks the
  // label dead centre of whatever width it got. That is right for a full-width
  // CTA in a phone sheet and wrong for a dropdown menu, where four ghost
  // buttons stacked in a 200px panel each centre their label and the menu
  // stops reading as a list.
  //
  // The call site could not reach this. Spec has no style override on a
  // component invocation, so the only escape was to wrap the Button in
  // `block { layout: horizontal }` — which sizes the item to its label,
  // correcting the alignment but also throwing away the full-width row, so a
  // menu item ends up clickable only across its text. `justify: "start"` keeps
  // the row and moves the label:
  //
  //     Button(label: 'Alert config', variant: 'ghost', justify: 'start')
  //
  // Named `justify`, not `align`, deliberately. It sets the MAIN axis of a
  // horizontal row; `align:` is Spec's cross-axis word and still means what it
  // always did. Stat carried an `align: string` prop that silently did nothing
  // for exactly this class of confusion (see stat.spec's header) — that one
  // also predated the compiler accepting an expression here at all.
  justify:      string  = "center"
) {
  @computed {
    isIconOnly: iconOnly != ""
    hasIconLeft: iconLeft != ""
    hasIconRight: iconRight != ""
    effectiveLabel: loading && loadingLabel != "" ? loadingLabel : label

    // Always a non-empty string. `aria-label=""` is not "no override" — the
    // accname spec tells browsers to ignore an empty one and fall back to
    // content, so emitting it conditionally would mean two different code
    // paths for the same outcome. Falling back to the visible label keeps
    // every existing caller's accessible name byte-identical.
    accessibleName: ariaLabel != "" ? ariaLabel : effectiveLabel

    // null (not false) is what an ordinary button emits — see the header. The
    // value is the BOOLEAN, never a string: a binding removes the attribute
    // only on null, so `false` sets "false", which is what ARIA wants for a
    // toggle that is currently up (ai-reference.md §31b).
    ariaPressed: (toggle && !disclosure) ? pressed : null
    ariaExpanded: disclosure ? pressed : null

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
      (isIconOnly ? (size == "xs" ? spacing.1 : (size == "sm" ? spacing.1 : (size == "lg" ? spacing.3 : spacing.2))) :
       (size == "xs" ? spacing.1 : (size == "sm" ? spacing.2 : (size == "lg" ? spacing.6 : token.btn-paddingH))))

    padY:
      variant == "link" ? 0 :
      (size == "xs" ? spacing.1 : (size == "sm" ? spacing.1 : (size == "lg" ? spacing.3 : token.btn-paddingV)))

    // The label style, which used to be type.label-md unconditionally.
    // Only "xs" reads anything else, so sm/md/lg are byte-identical to what
    // they rendered before.
    labelStyle: size == "xs" ? type.label-sm : type.label-md
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
    // Dynamic `aria-label:` compiles to a reactive bindAttr (ai-reference.md
    // rule 31), so this tracks `loading` flipping the label the same way the
    // visible text does.
    aria-label: accessibleName
    aria-pressed: ariaPressed
    aria-expanded: ariaExpanded
    // `justify:` takes an expression (ast-to-ir.ts `buildMappedAlignment`),
    // which lowers to a bindStyle carrying Spec's word→CSS table inline — so
    // "start" reaches the element as `flex-start` and "between" as
    // `space-between`, matching what a literal keyword emits. `align:` stays
    // the static `center`: the cross axis of a one-line row has nothing to
    // decide.
    layout: horizontal, align: center, justify: justify, gap: spacing.2
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

    // Forward the DOM event as the payload. Consumers that need it write
    // `on click(event): { event.stopPropagation() ... }`; without a payload
    // their `event` is undefined and the handler throws on first use, killing
    // every statement after it. Handlers that declare no parameter simply
    // ignore the extra argument.
    on click(event): emit("click", event)

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
        style: labelStyle
        font-weight: token.btn-fontWeight
        // Button labels must never wrap to a second line — a button squeezed
        // by a flex sibling should keep its width and let the sibling reflow,
        // not break "Reload saved" across two lines.
        white-space: 'nowrap'
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
