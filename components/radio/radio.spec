// Radio — custom visual radio button with event forwarding
// Group radios by using the same on-change handler and checked expression:
//   Radio(label: "A", value: "a", checked: selected == "a") { on change(v): setSelected(v) }
//   Radio(label: "B", value: "b", checked: selected == "b") { on change(v): setSelected(v) }
component RadioGroup(options: array = [], value: string = "", disabled: boolean = false) {
  block {
    layout: vertical, gap: spacing.2
    role: "radiogroup"

    each options as option {
      Radio(
        label: option.label,
        value: option.value,
        checked: value == option.value,
        disabled: disabled
      ) {
        on change(v): emit("change", v)
      }
    }
  }
}

component Radio(label: string, value: string = "", checked: boolean = false, disabled: boolean = false) {
  button {
    disabled: disabled
    border: "none"
    background: "transparent"
    padding: 0
    layout: horizontal, gap: 10px, align: center
    opacity: match disabled {
      true -> 0.5,
      _ -> 1
    }
    cursor: match disabled {
      true -> "default",
      _ -> "pointer"
    }

    on click: emit("change", value)

    // Radio circle — always round
    block {
      width: 18px
      height: 18px
      border-radius: 9999px
      border: match checked { true -> "none", _ -> token.checkbox-border }
      background: match checked { true -> token.checkbox-checkedBg, _ -> "transparent" }
      layout: horizontal, align: center, justify: center

      // Inner dot visible when selected
      block {
        visibility: checked == true
        width: 8px
        height: 8px
        border-radius: 9999px
        background: "#ffffff"
      }
    }

    text(label) {
      style: type.body-md
      font-weight: token.btn-fontWeight
      color: semantic.text-secondary
    }
  }
}
