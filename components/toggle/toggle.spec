// Toggle — custom toggle/switch with event forwarding
//
// Renders a <button role="switch"> carrying aria-checked, so assistive tech
// announces both the control AND its state. Without it this was a plain
// <button> whose accessible name was just the label, and whose on/off state
// existed ONLY as a track colour and a thumb translateX — a screen-reader user
// was told "Include nav databases, button" with no way to know which way it was
// set. Checkbox had already been given the same treatment; this component was
// missed, and the omission reached every call site that adopted it.
//
// role="switch" rather than "checkbox": both announce a binary state, but a
// switch is the on/off control this renders and it has no indeterminate state.
//
// `ariaLabel` (0.5.0): the switch's accessible name when the visible label is
// not it — the same prop Checkbox and Button carry, with the same default.
// Empty means the name is the label, so every existing caller is byte-identical.
// The case it exists for is a row that already names the setting in its own
// title ("Immediate risk / Someone should act now") and mounts the switch at
// the end: with `label` the title printed twice, with `label: ""` the switch
// announced as an unnamed control. Vector's hazard report row rebuilt the
// whole switch by hand to avoid both (2026-10-13); this is the prop that
// makes that unnecessary. The label is still drawn when it is given.
component Toggle(label: text, checked: boolean = false, disabled: boolean = false, ariaLabel: text = "") {
  @computed {
    accessibleName: ariaLabel != "" ? ariaLabel : label
    hasLabel: label != ""
  }
  button {
    disabled: disabled
    border: "none"
    background: "transparent"
    padding: 0
    role: "switch"
    aria-label: accessibleName
    aria-checked: checked
    aria-disabled: disabled
    layout: horizontal, gap: 10px, align: center
    cursor: match disabled {
      true -> "default",
      _ -> "pointer"
    }
    opacity: match disabled {
      true -> 0.5,
      _ -> 1
    }

    on click: emit("change", checked == false)

    text(label) {
      visibility: hasLabel
      style: type.body-md
      weight: 500
      color: semantic.text-secondary
    }

    // Track
    block {
      width: 44px
      height: 24px
      border-radius: token.toggle-radius
      background: match checked { true -> token.toggle-trackBgOn, _ -> token.toggle-trackBg }
      transition: transition.interactive-full
      position: "relative"

      // Thumb — slides via transform
      block {
        width: 18px
        height: 18px
        border-radius: 9999px
        background: token.toggle-thumbBg
        shadow: "0 1px 3px rgba(0,0,0,0.15)"
        position: "absolute"
        top: 3px
        left: 3px
        transition: transition.subtle
        transform: match checked { true -> "translateX(20px)", _ -> "translateX(0)" }
      }
    }
  }
}
