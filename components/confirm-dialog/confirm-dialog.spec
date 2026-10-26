component ConfirmDialog(open: boolean = false, title: text = "Confirm", message: text = "", confirmLabel: text = "Confirm", cancelLabel: text = "Cancel", destructive: boolean = false, loading: boolean = false, loadingLabel: text = "") {
  @state {
    showing: false
  }

  @actions {
    doOpen() {
      if showing { return }
      showing = true
      lockScroll()
      trapFocus()
    }
    doClose() {
      if !showing { return }
      showing = false
      unlockScroll()
      releaseFocus()
    }
    // While `loading`, the caller owns the close: it sets loading in its
    // `on confirm` handler and closes the dialog through `open` when its
    // request ends. Without loading the dialog closes itself, as it always has.
    confirm() {
      if loading { return }
      emit("confirm")
      if loading { return }
      doClose()
    }
    cancel() {
      if loading { return }
      emit("cancel")
      doClose()
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

  overlay(visible: showing, anchor: "screen", align: "center", backdrop: "scrim") {
    on dismiss: cancel()

    block {
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

        Button(label: cancelLabel, variant: "secondary", disabled: loading) {
          on click: cancel()
        }

        // Non-destructive confirm
        block {
          visibility: destructive == false
          Button(label: confirmLabel, variant: "primary", loading: loading, loadingLabel: loadingLabel) {
            on click: confirm()
          }
        }

        // Destructive confirm
        block {
          visibility: destructive == true
          Button(label: confirmLabel, variant: "destructive", loading: loading, loadingLabel: loadingLabel) {
            on click: confirm()
          }
        }
      }
    }
  }
}
