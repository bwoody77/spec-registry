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
//
// `appearance` (0.6.0): what the control looks like, never what it means.
// "switch" (the default, byte-identical to 0.5.x) is the track and thumb.
// "check" is a round tick at the LEADING edge, for a list row the user ticks
// (a task done, a passenger aboard, an item picked): iOS has no checkbox, and
// a switch in a list row reads as a setting. "button" is a chip that fills
// when on, for a set of restrictions or filters laid out as a grid. On iOS
// all three are a native SwiftUI Toggle: "check" with a ToggleStyle drawing
// `checkmark.circle.fill` / `circle`, "button" with `.toggleStyle(.button)`.
//
// The role follows the look, because `role:` is a compile-time literal: the
// switch announces role="switch", the check role="checkbox", the chip
// aria-pressed. All three carry their state.
//
// A "check" takes CHILDREN, drawn after the tick inside the one button: a row
// whose words are richer than one label (a name over a line, a value column
// at the far end) stays a single control that the whole row toggles, instead
// of a tick plus a second tap target. Children must not be interactive.
//
// `tint` colors the on state (the check's fill, the chip's fill); empty keeps
// the toggle tokens. `fullWidth` stretches a check or chip across its parent.
// Vector #1295.
component Toggle(label: text, checked: boolean = false, disabled: boolean = false, ariaLabel: text = "", appearance: text = "switch", tint: text = "", fullWidth: boolean = false) {
  @computed {
    accessibleName: ariaLabel != "" ? ariaLabel : label
    hasLabel: label != ""
    isCheck: appearance == "check"
    isChip: appearance == "button"
    isSwitch: isCheck == false && isChip == false
    onFill: tint != "" ? tint : token.toggle-trackBgOn
    boxWidth: fullWidth ? "100%" : "auto"
    tickRing: checked ? ("1.5px solid " + onFill) : ("1.5px solid " + semantic.border-strong)
    tickFill: checked ? onFill : "transparent"
    chipBg: checked ? onFill : semantic.surface
    chipFg: checked ? token.toggle-thumbBg : semantic.text-secondary
    chipBorder: checked ? ("1.5px solid " + onFill) : ("1.5px solid " + semantic.border)
    dimmed: disabled ? 0.5 : 1
    pointer: disabled ? "default" : "pointer"
  }
  // One box around the three looks, so the component keeps a single root
  // child: the compiler then dissolves its host to `display: contents`, as it
  // did for 0.5.x's lone button, and this block is the caller's flex item. It
  // carries `fullWidth`, and centers the button on the cross axis so a switch
  // in a row without `align: center` sits where the stretched button put it.
  block {
    width: boxWidth
    layout: vertical, justify: center
    button {
      visibility: isSwitch
      disabled: disabled
      border: "none"
      background: "transparent"
      padding: 0
      role: "switch"
      aria-label: accessibleName
      aria-checked: checked
      aria-disabled: disabled
      layout: horizontal, gap: 10px, align: center
      cursor: pointer
      opacity: dimmed

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
        visibility: hasLabel
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

    // Check: a round tick, then the label, then the caller's children.
    button {
      visibility: isCheck
      disabled: disabled
      width: boxWidth
      border: "none"
      background: "transparent"
      padding: 0
      role: "checkbox"
      aria-label: accessibleName
      aria-checked: checked
      aria-disabled: disabled
      layout: horizontal, gap: 10px, align: center
      cursor: pointer
      opacity: dimmed

      on click: emit("change", checked == false)

      block {
        width: 24px
        height: 24px
        min-width: 24px
        border-radius: 999px
        border: tickRing
        background: tickFill
        transition: transition.interactive-full
        layout: horizontal, justify: center, align: center
        block {
          visibility: checked
          layout: horizontal, justify: center, align: center
          Icon(name: "check", size: 14, color: token.toggle-thumbBg)
        }
      }
      text(label) {
        visibility: hasLabel
        grow: true
        style: type.body-md
        weight: 500
        color: semantic.text-primary
        text-align: start
      }
      @children
    }

    // Chip: the label in a box that fills when on.
    button {
      visibility: isChip
      disabled: disabled
      width: boxWidth
      min-height: 44px
      border: chipBorder
      border-radius: 8px
      background: chipBg
      padding: 6px 10px
      aria-label: accessibleName
      aria-pressed: checked
      aria-disabled: disabled
      layout: horizontal, justify: center, align: center
      cursor: pointer
      opacity: dimmed
      transition: transition.interactive-full

      on click: emit("change", checked == false)

      text(label) { color: chipFg, weight: 600, font-size: 14px, white-space: "nowrap", text-align: center }
    }
  }
}
