component ConfirmDialog(open: boolean = false, title: string = "Confirm", message: string = "", confirmLabel: string = "Confirm", cancelLabel: string = "Cancel", destructive: boolean = false) {
  @state {
    showing: false
  }

  @actions {
    doOpen() {
      showing = true
      lockScroll()
      trapFocus()
    }
    doClose() {
      showing = false
      unlockScroll()
      releaseFocus()
    }
    confirm() {
      doClose()
      emit("confirm")
    }
    cancel() {
      doClose()
      emit("cancel")
    }
  }

  @watch {
    open: {
      match open {
        true -> doOpen()
        _ -> doClose()
      }
    }
  }

  block {
    // Backdrop
    block {
      visibility: showing == true
      position: "fixed"
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 1000
      background: "rgba(0, 0, 0, 0.5)"
    }

    // Dialog
    block {
      visibility: showing == true
      position: "fixed"
      top: 50%
      left: 50%
      transform: "translate(-50%, -50%)"
      z-index: 1001
      width: 440px
      max-width: 95vw
      padding: spacing.5
      background: semantic.surface
      border-radius: 12px
      shadow: elevation.floating
      role: "dialog"
      aria-label: "Confirm dialog"

      layout: vertical, gap: spacing.3

      // Title
      text(title) {
        style: type.heading-sm
        color: semantic.text-primary
      }

      // Message
      text(message) {
        style: type.body-md
        color: semantic.text-secondary
      }

      // Actions
      block {
        layout: horizontal, justify: end, gap: spacing.2
        margin: spacing.2

        Button(label: cancelLabel, variant: "secondary") {
          on click: cancel()
        }

        // Non-destructive confirm
        block {
          visibility: destructive == false
          Button(label: confirmLabel, variant: "primary") {
            on click: confirm()
          }
        }

        // Destructive confirm
        block {
          visibility: destructive == true
          Button(label: confirmLabel, variant: "destructive") {
            on click: confirm()
          }
        }
      }
    }
  }
}
