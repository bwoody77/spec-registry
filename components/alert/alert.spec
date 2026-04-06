component Alert(message: string, severity: string = "info", title: string = "", dismissible: boolean = false) {
  block {
    layout: horizontal, gap: spacing.2, align: start
    padding: spacing.3
    border-radius: token.alert-radius
    shadow: token.alert-shadow
    background: match severity {
      "info" -> token.alert-info-bg,
      "success" -> token.alert-success-bg,
      "warning" -> token.alert-warning-bg,
      "error" -> token.alert-error-bg,
      _ -> token.alert-info-bg
    }
    border: match severity {
      "info" -> token.alert-info-border-css,
      "success" -> token.alert-success-border-css,
      "warning" -> token.alert-warning-border-css,
      "error" -> token.alert-error-border-css,
      _ -> token.alert-info-border-css
    }
    role: "alert"

    // Severity icon
    Icon(name: match severity {
      "info" -> "info",
      "success" -> "circle-check",
      "warning" -> "alert-triangle",
      "error" -> "circle-x",
      _ -> "info"
    }, size: icon.xs, color: match severity {
      "info" -> token.alert-info-text,
      "success" -> token.alert-success-text,
      "warning" -> token.alert-warning-text,
      "error" -> token.alert-error-text,
      _ -> token.alert-info-text
    })

    // Content
    block {
      grow: true
      layout: vertical, gap: 2px

      text(title) {
        visibility: title != ""
        style: type.body-md
        weight: 600
        color: match severity {
          "info" -> token.alert-info-text,
          "success" -> token.alert-success-text,
          "warning" -> token.alert-warning-text,
          "error" -> token.alert-error-text,
          _ -> token.alert-info-text
        }
      }

      text(message) {
        style: type.body-md
        color: match severity {
          "info" -> token.alert-info-text,
          "success" -> token.alert-success-text,
          "warning" -> token.alert-warning-text,
          "error" -> token.alert-error-text,
          _ -> token.alert-info-text
        }
      }
    }

    // Dismiss button
    block {
      visibility: dismissible == true
      width: 24px
      height: 24px
      min-width: 24px
      border-radius: radius.sm
      cursor: "pointer"
      layout: horizontal, align: center, justify: center
      on click: emit("dismiss")
      on hover { background: "rgba(0,0,0,0.08)" }
      text("\u00D7") {
        style: type.body-md
        color: match severity {
          "info" -> token.alert-info-text,
          "success" -> token.alert-success-text,
          "warning" -> token.alert-warning-text,
          "error" -> token.alert-error-text,
          _ -> token.alert-info-text
        }
      }
    }
  }
}
