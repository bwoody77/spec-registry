// Checkbox — custom visual checkbox with event forwarding
component Checkbox(label: string, checked: boolean = false, disabled: boolean = false) {
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

    on click: emit("change", checked == false)

    // Single box — always present, style changes based on checked
    block {
      width: 18px
      height: 18px
      border-radius: token.checkbox-radius
      border: match checked { true -> "none", _ -> token.checkbox-border }
      background: match checked { true -> token.checkbox-checkedBg, _ -> "transparent" }
      layout: horizontal, align: center, justify: center

      // Check icon only visible when checked
      block {
        visibility: checked == true
        Icon(name: "check", size: "14px", color: "#ffffff")
      }
    }

    text(label) {
      style: type.body-md
      weight: 500
      color: semantic.text-secondary
    }
  }
}
