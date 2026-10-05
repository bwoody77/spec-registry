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
component Toggle(label: text, checked: boolean = false, disabled: boolean = false) {
  button {
    disabled: disabled
    border: "none"
    background: "transparent"
    padding: 0
    role: "switch"
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

    // `text-align: start` is load-bearing. The root is a <button>, and the UA
    // stylesheet gives every button `text-align: center`, which inherits into
    // this label. While the button shrink-wraps the box hugs the glyphs and
    // nothing looks wrong; once the label is long enough to WRAP, both lines
    // center themselves. Seen in Vector on "Only show to members whose tier
    // includes this aircraft". Checkbox 0.5.1 carries the same fix for the
    // same reason. The property cannot go on the `button` itself (Spec rejects
    // it there), and only logical values are accepted, so `start`, not `left`.
    text(label) {
      style: type.body-md
      weight: 500
      color: semantic.text-secondary
      text-align: start
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
