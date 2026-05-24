component Popover(placement: string = "bottom") {
  @state {
    open: false
  }

  @actions {
    toggle() { open = open == false }
    close() { open = false }
  }

  block {
    // Trigger
    block {
      on click: toggle()
      @slot("trigger")
    }

    // Popover content
    overlay(visible: open, anchor: "parent", backdrop: "transparent", dismissOnTapOutside: true) {
      on dismiss: close()

      block {
        visibility: placement == "bottom"
        min-width: 240px
        max-width: 90vw
        margin: spacing.1
        padding: spacing.4
        background: semantic.surface
        border: borders.default
        border-radius: 12px
        shadow: elevation.floating
        layout: vertical, gap: spacing.2

        @slot("content")
      }

      block {
        visibility: placement == "top"
        min-width: 240px
        max-width: 90vw
        margin: spacing.1
        padding: spacing.4
        background: semantic.surface
        border: borders.default
        border-radius: 12px
        shadow: elevation.floating
        layout: vertical, gap: spacing.2

        @slot("content")
      }

      block {
        visibility: placement == "left"
        min-width: 240px
        max-width: 90vw
        margin: spacing.1
        padding: spacing.4
        background: semantic.surface
        border: borders.default
        border-radius: 12px
        shadow: elevation.floating
        layout: vertical, gap: spacing.2

        @slot("content")
      }

      block {
        visibility: placement == "right"
        min-width: 240px
        max-width: 90vw
        margin: spacing.1
        padding: spacing.4
        background: semantic.surface
        border: borders.default
        border-radius: 12px
        shadow: elevation.floating
        layout: vertical, gap: spacing.2

        @slot("content")
      }
    }
  }
}
