component Toast(message: string, severity: string = "info", duration: number = 5000) {
  @state {
    hovered: false
  }

  @actions {
    startDismiss() { delay("dismiss", duration) { emit("dismiss") } }
    pauseDismiss() { clearDelay("dismiss") }
    resumeDismiss() { delay("dismiss", duration) { emit("dismiss") } }
  }

  block {
    layout: horizontal, gap: spacing.3, align: center
    padding: spacing.3
    border-radius: 8px
    shadow: elevation.floating
    min-width: 300px
    role: "status"
    aria-live: "polite"
    background: match severity {
      "success" -> "#f0fdf4",
      "error" -> "#fef2f2",
      "warning" -> "#fffbeb",
      _ -> "#eff6ff"
    }
    border: match severity {
      "success" -> "1px solid #bbf7d0",
      "error" -> "1px solid #fecaca",
      "warning" -> "1px solid #fde68a",
      _ -> "1px solid #bfdbfe"
    }
    on mouse-enter: pauseDismiss()
    on mouse-leave: resumeDismiss()

    // Severity icon
    text(match severity {
      "success" -> "✓",
      "error" -> "✕",
      "warning" -> "⚠",
      _ -> "ℹ"
    }) {
      style: type.label-md
      color: match severity {
        "success" -> "#16a34a",
        "error" -> "#dc2626",
        "warning" -> "#d97706",
        _ -> "#2563eb"
      }
    }

    // Message
    text(message) {
      style: type.body-md
      color: match severity {
        "success" -> "#166534",
        "error" -> "#991b1b",
        "warning" -> "#92400e",
        _ -> "#1e40af"
      }
      grow: true
    }

    // Dismiss button
    block {
      cursor: "pointer"
      padding: spacing.2
      min-width: 24px
      min-height: 24px
      layout: horizontal, justify: center, align: center
      aria-label: "Dismiss notification"
      on click: emit("dismiss")
      text("✕") {
        style: type.body-lg
        color: semantic.text-tertiary
      }
    }
  }
}
