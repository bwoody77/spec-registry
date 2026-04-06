component Popover(placement: string = "bottom") {
  @state {
    open: false
  }

  @actions {
    toggle() { open = open == false }
    close() { open = false }
  }

  block {
    position: "relative"

    // Trigger
    block {
      on click: toggle()
      @slot("trigger")
    }

    // Transparent backdrop — click to dismiss
    block {
      visibility: open == true
      position: "fixed"
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 899
      on click: close()
    }

    // Panel — bottom placement
    block {
      visibility: open == true && placement == "bottom"
      position: "absolute"
      top: 100%
      left: 0px
      z-index: 900
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

    // Panel — top placement
    block {
      visibility: open == true && placement == "top"
      position: "absolute"
      bottom: 100%
      left: 0px
      z-index: 900
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

    // Panel — left placement
    block {
      visibility: open == true && placement == "left"
      position: "absolute"
      right: 100%
      top: 0px
      z-index: 900
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

    // Panel — right placement
    block {
      visibility: open == true && placement == "right"
      position: "absolute"
      left: 100%
      top: 0px
      z-index: 900
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
