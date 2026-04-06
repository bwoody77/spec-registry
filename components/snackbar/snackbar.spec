component Snackbar(
  open: boolean = false,
  message: string = "",
  duration: number = 4000,
  actionLabel: string = ""
) {
  @state {
    showing: false
  }

  @actions {
    doOpen() {
      showing = true
      delay("auto-close", duration) { doClose() }
    }
    doClose() {
      showing = false
      emit("close")
    }
    doAction() {
      emit("action")
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

  block {
    visibility: showing == true
    position: "fixed"
    bottom: 16px
    left: 16px
    right: 16px
    z-index: 1100
    padding-bottom: env(safe-area-inset-bottom)

    block {
      max-width: 560px
      padding-x: spacing.4
      padding-y: spacing.3
      background: "rgb(30, 30, 30)"
      border-radius: 8px
      shadow: elevation.floating
      layout: horizontal, align: center, gap: 12px
      on swipe-right: doClose()

      text(message) {
        grow: true
        color: "white"
        style: type.body-sm
      }

      block {
        visibility: actionLabel != ""
        cursor: "pointer"
        on click: doAction()

        text(actionLabel) {
          color: semantic.accent
          style: type.label
          weight: 600
        }
      }

      block {
        width: 24px
        height: 24px
        border-radius: 12px
        cursor: "pointer"
        layout: horizontal, align: center, justify: center
        on click: doClose()
        on hover {
          background: "rgba(255, 255, 255, 0.1)"
        }

        text("\u00D7") {
          color: "rgba(255, 255, 255, 0.7)"
        }
      }
    }
  }
}
