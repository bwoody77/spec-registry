// Checkbox — custom visual checkbox with event forwarding
//
// Renders a <button role="checkbox"> carrying aria-checked, so assistive tech
// announces both the control AND its state. Before aria-* state attributes
// existed this was a plain <button> whose accessible name was just the label:
// a screen-reader user was told "Share as house preset, button" with no way to
// know whether it was ticked. Hand-rolled copies in apps had started adding
// role="checkbox" themselves precisely because this component lacked it.
component Checkbox(label: string, checked: boolean = false, disabled: boolean = false) {
  button {
    disabled: disabled
    border: "none"
    background: "transparent"
    padding: 0
    role: "checkbox"
    aria-checked: checked
    aria-disabled: disabled
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
