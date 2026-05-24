// Input — form text input with label, prefix/suffix, error state, and focus ring
component TextInput(
  type: string = "text",
  label: string = "",
  placeholder: string = "",
  value: string = "",
  disabled: boolean = false,
  readonly: boolean = false,
  prefix: string = "",
  suffix: string = "",
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
      background: token.input-bg
      border: match error {
        true -> token.input-borderWidth + " solid " + semantic.destructive,
        _ -> match focused {
          true -> token.input-borderWidth + " solid " + token.input-focusBorder,
          _ -> token.input-borderWidth + " solid " + token.input-border
        }
      }
      shadow: match focused {
        true -> "0 0 0 3px " + token.input-focusRing,
        _ -> token.input-shadow
      }
      transition: transition.focus
      cursor: match disabled { true -> "not-allowed", _ -> "text" }

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
        }
      }

      // Suffix
      block {
        visibility: suffix != ""
        text(suffix) {
          style: type.body-md
          color: semantic.text-tertiary
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
