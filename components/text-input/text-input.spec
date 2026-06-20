// Input — form text input with label, prefix/suffix, leading icon, segmented unit, error state, focus ring
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
  unit: string = "",
  tone: string = "default",
  error: boolean = false,
  errorMessage: string = ""
) {
  @state { focused: false }

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
