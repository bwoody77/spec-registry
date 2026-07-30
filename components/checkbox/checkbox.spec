// Checkbox — custom visual checkbox with event forwarding
//
// Renders a <button role="checkbox"> carrying aria-checked, so assistive tech
// announces both the control AND its state. Before aria-* state attributes
// existed this was a plain <button> whose accessible name was just the label:
// a screen-reader user was told "Share as house preset, button" with no way to
// know whether it was ticked. Hand-rolled copies in apps had started adding
// role="checkbox" themselves precisely because this component lacked it.
//
// `size` exists so dense contexts (filter bars, compact panels) can adopt this
// component without their label text growing. Vector had ~50 hand-rolled
// checkboxes, nearly all of them a body-sm label beside a 15-16px box; forcing
// them all up to body-md on adoption would have reflowed real layouts. Default
// stays "md" so existing call sites are untouched.
component Checkbox(label: string, checked: boolean = false, disabled: boolean = false, size: string = "md") {
  @computed {
    isSm:      size == "sm"
    boxSize:   isSm ? 16px : 18px
    iconSize:  isSm ? "12px" : "14px"
    labelType: isSm ? type.body-sm : type.body-md
    rowGap:    isSm ? 8px : 10px
  }
  button {
    disabled: disabled
    border: "none"
    background: "transparent"
    padding: 0
    role: "checkbox"
    aria-checked: checked
    aria-disabled: disabled
    layout: horizontal, gap: rowGap, align: center
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
      width: boxSize
      height: boxSize
      border-radius: token.checkbox-radius
      // checkbox-border is a COLOUR; compose it into a full shorthand, the way
      // date-picker and multi-select already do with input-border.
      //
      // The bare form also worked: for a runtime token lookup the compiler
      // wraps border values in a guard that turns a space-less value into
      // "1px solid " + value. But that guard is only emitted on the runtime
      // path — with no @theme in the program the token resolves statically to
      // a bare "#d1d5db", which CSS reads as colour-only and renders NO border
      // at all. Being explicit does not depend on which path a consumer hits.
      border: match checked { true -> "none", _ -> "1px solid " + token.checkbox-border }
      background: match checked { true -> token.checkbox-checkedBg, _ -> "transparent" }
      layout: horizontal, align: center, justify: center

      // Check icon only visible when checked
      block {
        visibility: checked == true
        Icon(name: "check", size: iconSize, color: "#ffffff")
      }
    }

    text(label) {
      style: labelType
      weight: 500
      color: semantic.text-secondary
    }
  }
}
