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
  ariaLabel: string = ""
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
      padding: spacing.2
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
