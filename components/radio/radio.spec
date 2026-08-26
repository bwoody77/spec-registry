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

// Renders a <button role="radio"> carrying aria-checked, so assistive tech
// announces which option in the group is selected. RadioGroup already wraps
// these in role="radiogroup"; without aria-checked on the items that grouping
// described a set whose state could not be read.
component Radio(label: string, value: string = "", checked: boolean = false, disabled: boolean = false) {
  button {
    disabled: disabled
    border: "none"
    background: "transparent"
    padding: 0
    role: "radio"
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

    on click: emit("change", value)

    // Radio circle — always round
    block {
      width: 18px
      height: 18px
      border-radius: 9999px
      // See checkbox.spec — checkbox-border is a colour, composed explicitly
      // so it does not depend on the compiler's runtime-only border guard.
      border: match checked { true -> "none", _ -> "1px solid " + token.checkbox-border }
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

    // `text-align: start` is load-bearing, and only on a LONG label.
    //
    // A <button> carries the UA `text-align: center`, which inherits into every
    // text box inside it. A short label hugs its glyphs, so nothing moves and
    // this looks unnecessary. A label long enough to WRAP does not: the box
    // becomes the full width available in the row and the lines centre inside
    // it. RadioGroup makes that reachable on its own — its `layout: vertical`
    // stretches each Radio to the group's width, so the row is as wide as the
    // widest option regardless of what any single label needs.
    //
    // Measured in Vector at 390px (/gift-certificates/new): "Same as buyer
    // (self-redeem / discovery flights)" wrapped into a 268px box with 209px of
    // glyphs, sitting 30px in, while the option below it started somewhere else
    // again. `start` rather than `left` so RTL flips.
    text(label) {
      style: type.body-md
      font-weight: token.btn-fontWeight
      color: semantic.text-secondary
      text-align: start
    }
  }
}
