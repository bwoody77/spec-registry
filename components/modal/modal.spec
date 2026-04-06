component Modal(open: boolean = false, title: string = "", width: string = "500px") {
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
      emit("close")
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
      background: "rgba(15, 23, 42, 0.5)"
      backdrop-filter: "blur(4px)"
      on click: doClose()
    }

    // Dialog
    block {
      visibility: showing == true
      position: "fixed"
      top: 50%
      left: 50%
      transform: "translate(-50%, -50%)"
      z-index: 1001
      width: width
      max-width: 95vw
      max-height: 90vh
      overflow: "auto"
      background: semantic.surface
      border-radius: 14px
      shadow: elevation.floating
      role: "dialog"
      aria-label: "Dialog"

      layout: vertical

      // Header
      block {
        layout: horizontal, justify: between, align: center
        padding: spacing.4
        border-bottom: borders.default

        text(title) {
          visibility: title != ""
          style: type.heading-sm
          color: semantic.text-primary
        }

        // Close button
        block {
          width: 32px
          height: 32px
          border-radius: 8px
          cursor: "pointer"
          layout: horizontal, align: center, justify: center
          on click: doClose()
          on hover {
            background: semantic.surface-raised
          }

          text("\u00D7") {
            style: type.heading-sm
            color: semantic.text-tertiary
          }
        }
      }

      // Body
      block {
        padding: spacing.5
        grow: true
        overflow: "auto"
        @children
      }
    }
  }
}
