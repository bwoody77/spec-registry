component Drawer(open: boolean = false, title: string = "", side: string = "left", width: string = "280px") {
  @state {
    showing: false
  }

  @computed {
    panelTransform: match showing {
      true -> "translateX(0)",
      _ -> match side {
        "right" -> "translateX(100%)",
        _ -> "translateX(-100%)"
      }
    }
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

  overlay(visible: showing, anchor: "screen", backdrop: "scrim") {
    on dismiss: doClose()

    // Panel (left side)
    block {
      visibility: side == "left"
      width: width
      max-width: 90vw
      background: semantic.surface
      shadow: elevation.floating
      overflow: "auto"
      transition: transition.expand
      transform: panelTransform
      role: "dialog"
      aria-label: "Drawer"

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
        padding: spacing.4
        grow: true
        overflow: "auto"
        @children
      }
    }

    // Panel (right side)
    block {
      visibility: side == "right"
      width: width
      max-width: 90vw
      background: semantic.surface
      shadow: elevation.floating
      overflow: "auto"
      transition: transition.expand
      transform: panelTransform
      role: "dialog"
      aria-label: "Drawer"

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
        padding: spacing.4
        grow: true
        overflow: "auto"
        @children
      }
    }
  }
}
