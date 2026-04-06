// Button — native <button> with event forwarding
component Button(label: string, variant: string = "primary", disabled: boolean = false, loading: boolean = false, pressed: boolean = false, size: string = "md") {
  button {
    disabled: disabled
    layout: horizontal, align: center, justify: center
    padding-x: match size { "sm" -> spacing.2, "lg" -> spacing.6, _ -> token.btn-paddingH }
    padding-y: match size { "sm" -> spacing.1, "lg" -> spacing.3, _ -> token.btn-paddingV }
    border-radius: token.btn-radius
    shadow: match pressed {
      true -> "inset 0 1px 3px rgba(0,0,0,0.2)",
      _ -> token.btn-shadow
    }
    font-weight: token.btn-fontWeight
    text-transform: token.btn-textTransform
    letter-spacing: token.btn-letterSpacing
    transition: transition.interactive-full
    cursor: match disabled {
      true -> "default",
      _ -> "pointer"
    }
    opacity: match loading {
      true -> 0.7,
      _ -> match disabled {
        true -> 0.5,
        _ -> 1
      }
    }
    background: match pressed {
      true -> match variant {
        "primary" -> token.btn-primary-hover,
        "secondary" -> token.btn-secondary-hover,
        "ghost" -> token.btn-ghost-hover,
        "destructive" -> token.btn-destructive-hover,
        _ -> token.btn-primary-hover
      },
      _ -> match variant {
        "primary" -> token.btn-primary-bg,
        "secondary" -> token.btn-secondary-bg,
        "ghost" -> "transparent",
        "destructive" -> token.btn-destructive-bg,
        _ -> token.btn-primary-bg
      }
    }
    border: match variant {
      "secondary" -> token.btn-secondary-border,
      _ -> "none"
    }

    on hover {
      background: match variant {
        "primary" -> token.btn-primary-hover,
        "secondary" -> token.btn-secondary-hover,
        "ghost" -> token.btn-ghost-hover,
        "destructive" -> token.btn-destructive-hover,
        _ -> token.btn-primary-hover
      }
    }

    on active {
      transform: "scale(.97)"
    }

    on click: emit("click")

    text(label) {
      style: type.label-md
      font-weight: token.btn-fontWeight
      color: match variant {
        "primary" -> token.btn-primary-color,
        "secondary" -> token.btn-secondary-color,
        "ghost" -> token.btn-ghost-color,
        "destructive" -> token.btn-destructive-color,
        _ -> token.btn-primary-color
      }
    }
  }
}
