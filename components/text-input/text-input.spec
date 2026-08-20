// Input — form text input with label, prefix/suffix, leading icon, trailing icon, segmented unit, error state, focus ring
component TextInput(
  type: string = "text",
  label: string = "",
  placeholder: string = "",
  value: string = "",
  disabled: boolean = false,
  readonly: boolean = false,
  prefix: string = "",
  suffix: string = "",
  icon: string = "",
  // Trailing adornment icon, rendered INSIDE the field's border at its right
  // edge. Exists for combobox wrappers (Autocomplete, Vector's UserPicker)
  // that need Select's caret to sit inside the control rather than floating
  // beside it — the only trailing affordances before this were `suffix`
  // (text) and `unit` (a bordered segment), neither of which can carry a
  // glyph. Purely decorative and aria-hidden: the input container is a
  // <label>, so a click anywhere on the icon focuses the input and the
  // wrapper's own `on focus` handler opens its dropdown. Do NOT give it a
  // click handler — that would double-fire against the label delegation.
  trailingIcon: string = "",
  unit: string = "",
  tone: string = "default",
  error: boolean = false,
  errorMessage: string = "",
  // Normally supplied by the compiler from the visible label rendered
  // beside the field (ast-to-ir inferAccessibleNames), not by hand.
  ariaLabel: string = "",
  // "md" (default, unchanged) | "sm". Mirrors Select's prop of the same name,
  // and lands on the same measured height, so the two sit level in a toolbar
  // or a property grid — which is the gap that motivated this. Select took a
  // `size` in the toolbar-density work and TextInput did not, so every dense
  // surface that used both got a 32px control beside a 38px one, and a
  // fixed-height row holding a TextInput sheared open the moment it was
  // focused.
  size: string = "md"
) {
  @state { focused: false }

  @computed {
    // The input carried NO accessible name at all: a bare <input> whose only
    // label was a sibling text node the browser never associates with it.
    // Prefer the compiler-inferred name, then this component's own rendered
    // `label`, then the placeholder as a last resort.
    // null, never "" — bindAttr REMOVES the attribute on null, whereas an
    // empty aria-label is a real (empty) name and hides whatever the
    // browser would otherwise have used. Falls through to the placeholder
    // only because a weak name beats none.
    inputAriaLabel: ariaLabel != "" ? ariaLabel : (label != "" ? label : (placeholder != "" ? placeholder : null))

    // ── size: "md" (default, unchanged) | "sm" ───────────────────────────────
    //
    // Both of these move together or neither does anything — the same
    // invariant Select's own size prop documents, and the same trap: an
    // earlier attempt at Select's prop changed one, measured no change, and
    // was reverted as a no-op.
    //
    // The container carries the padding and the border; the <input> inside is
    // borderless and transparent. Rendered height is therefore
    // padding×2 + line + 2×border, floored by min-height.
    //
    //   md: 8 + 20 + 8 = 36, +2 border = 38, floor 0  → 38 (what it has always been)
    //   sm: 4 + 20 + 4 = 28, +2 border = 30, floor 30 → 32
    //
    // The floor is not decoration. Without it, anything with a taller line box
    // than a bare input — a leading icon, a prefix, a unit segment — sets the
    // height instead, so the same `size: "sm"` measures differently depending
    // on which adornments a call site happens to pass. The floor makes "sm"
    // mean one number.
    //
    // md's floor is 0 rather than a number, because ANY min-height here would
    // change the default rendering — the point of the prop is that an existing
    // call site is untouched.
    //
    // ⚠ THE UNIT IS LOAD-BEARING, and it is why these are strings.
    //
    // A size property written as a LITERAL in markup (`min-height: 30px`) is
    // resolved by the compiler and emitted with its unit. A size property bound
    // to a COMPUTED gets the raw value: a computed number 30 emits
    // `min-height: 30`, which is not a length, so the browser drops the whole
    // declaration and the floor silently does nothing. Measured, all four
    // forms, on this component:
    //
    //     min-height: 30px            -> "30px"   ✓
    //     min-height: <computed 30>   -> "30"     ✗ dropped
    //     min-height: <computed '30px'> -> "30px" ✓
    //     min-height: size == "sm" ? 30 : 40  -> "30"  ✗ dropped
    //
    // Select's `size` shipped with the number form and its floor therefore
    // never applied. That is how this was found: matching Select's height
    // meant measuring Select, and Select was not the height it claimed.
    // Corrected on the same branch, so the two agree again.
    boxPad: size == "sm" ? spacing.1 : spacing.2
    boxMinHeight: size == "sm" ? '30px' : '0px'
  }

  @actions {
    handleFocus() {
      focused = true
      emit("focus")
    }
    handleBlur() {
      focused = false
      emit("blur")
    }
  }

  block {
    layout: vertical, gap: 6px
    opacity: match disabled { true -> 0.5, _ -> 1 }

    // Label
    block {
      visibility: label != ""
      text(label) {
        style: type.label-md
        color: semantic.text-secondary
      }
    }

    // Input container — label delegates clicks to the input inside
    label {
      layout: horizontal, align: center, gap: 8px
      padding: boxPad
      min-height: boxMinHeight
      border-radius: token.input-radius
      background: match tone {
        "warning" -> semantic.warning-bg,
        "danger"  -> semantic.destructive-bg,
        _ -> token.input-bg
      }
      border: match error {
        true -> token.input-borderWidth + " solid " + semantic.destructive,
        _ -> match tone {
          "warning"   -> token.input-borderWidth + " solid " + semantic.warning,
          "danger"    -> token.input-borderWidth + " solid " + semantic.destructive,
          "highlight" -> token.input-borderWidth + " solid " + semantic.interactive,
          _ -> match focused {
            true  -> token.input-borderWidth + " solid " + token.input-focusBorder,
            _     -> token.input-borderWidth + " solid " + token.input-border
          }
        }
      }
      shadow: match focused {
        true -> "0 0 0 3px " + token.input-focusRing,
        _ -> token.input-shadow
      }
      transition: transition.focus
      cursor: match disabled { true -> "not-allowed", _ -> "text" }

      // Leading icon
      block {
        visibility: icon != ""
        layout: horizontal, align: center
        Icon(name: icon, size: 16, color: semantic.text-tertiary)
      }

      // Prefix
      block {
        visibility: prefix != ""
        text(prefix) {
          style: type.body-md
          color: semantic.text-tertiary
        }
      }

      // Text input (non-textarea)
      block {
        visibility: type != "textarea"
        grow: true
        textInput(value) {
          placeholder: placeholder
          aria-label: inputAriaLabel
          type: type
          disabled: disabled
          readonly: readonly
          border: "none"
          background: "transparent"
          width: 100%
          on input: emit("change", value)
          on focus: handleFocus()
          on blur: handleBlur()
          on key-down(e): emit("keydown", e)
        }
      }

      // Textarea
      block {
        visibility: type == "textarea"
        grow: true
        textArea(value) {
          placeholder: placeholder
          aria-label: inputAriaLabel
          disabled: disabled
          readonly: readonly
          rows: 4
          border: "none"
          background: "transparent"
          width: 100%
          on input: emit("change", value)
          on focus: handleFocus()
          on blur: handleBlur()
          on key-down(e): emit("keydown", e)
        }
      }

      // Suffix (inline)
      block {
        visibility: suffix != ""
        text(suffix) {
          style: type.body-md
          color: semantic.text-tertiary
        }
      }

      // Trailing icon (e.g. a combobox caret). Sits before `unit` because the
      // unit segment draws its own left divider and reads as the field's right
      // edge — a caret outside it would look like it belonged to the unit box.
      // The two are never used together in practice.
      // No aria-hidden here: mountIcon already sets aria-hidden="true" and
      // focusable="false" on the <svg> whenever the Icon has no `label`, so an
      // unlabelled icon is out of the a11y tree on its own. Setting it here as
      // well would also collide with `visibility:` on this same element —
      // bindVisibility clears an aria-hidden it believes it owns, and the
      // runtime marker that would protect an authored one is not in the spec
      // build Vector currently pins.
      block {
        visibility: trailingIcon != ""
        layout: horizontal, align: center
        Icon(name: trailingIcon, size: 16, color: semantic.text-tertiary)
      }

      // Segmented unit (e.g. "qts", "gal") — right-aligned box with a full-height divider
      block {
        visibility: unit != ""
        layout: horizontal, align: center, justify: center
        padding-x: spacing.2
        border-left: match focused {
          true -> "1px solid " + token.input-focusBorder,
          _ -> "1px solid " + token.input-border
        }
        text(unit) {
          style: type.body-sm
          color: semantic.text-tertiary
          weight: 600
        }
      }
    }

    // Error message
    block {
      visibility: error == true
      text(errorMessage) {
        style: type.caption
        color: semantic.destructive
      }
    }
  }
}
