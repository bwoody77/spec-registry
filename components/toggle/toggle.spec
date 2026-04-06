// Toggle — custom toggle/switch with event forwarding
component Toggle(label: string, checked: boolean = false, disabled: boolean = false) {
  button {
    disabled: disabled
    border: "none"
    background: "transparent"
    padding: 0
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
