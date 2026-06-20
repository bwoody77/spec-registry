// Popover — click-triggered overlay anchored to a trigger.
//
// Uses the spec runtime's `anchor:` keyword to position the panel via
// positionDropdown (position:fixed, viewport-relative, auto-flip,
// right-edge clamp). The panel escapes any `overflow: hidden | auto`
// ancestor — the recurring pain point for popovers inside data grids,
// scrollable cards, or other clipping containers.
//
// Outside-click dismiss is handled by a sibling fixed-position backdrop
// (z-index below the panel) instead of `overlay(...)` so the panel's
// positioning stays in the same `anchor:` mechanism comboboxes use.
//
// Caveat: if any ancestor of the trigger has a non-`none` `transform`,
// `filter`, or `perspective`, browsers re-root the panel's `position:fixed`
// against that ancestor (CSS Transforms spec). Audit ancestors if the panel
// lands at the wrong coordinates.

component Popover(placement: string = "bottom", closeOnContentClick: boolean = false) {
  @state {
    open: false
  }

  @actions {
    toggle() { open = open == false }
    close() { open = false }
  }

  block {
    inline: true

    // Trigger — caller-supplied content via @slot("trigger")
    block {
      on click: toggle()
      @slot("trigger")
    }

    // Panel — anchored to the trigger (previous sibling). `anchor:` invokes
    // positionDropdown which sets position:fixed + viewport-relative coords.
    // When closeOnContentClick is true, any click inside the panel (e.g. on
    // a select option) bubbles up to this block and calls close(). The child's
    // own handler fires first (event propagation order), so the selection
    // action completes before the panel closes.
    block {
      visibility: open
      anchor: placement
      min-width: 240px
      max-width: 90vw
      padding: spacing.4
      background: semantic.surface
      border: borders.default
      border-radius: 12px
      shadow: elevation.floating
      z-index: 200
      layout: vertical, gap: spacing.2
      on click: closeOnContentClick ? close() : {}

      @slot("content")
    }

    // Outside-click backdrop — a fixed-position fullscreen sibling sitting
    // BELOW the panel in z-order. A click on the backdrop closes the panel.
    // Without this, an opened popover stays sticky and the user has to
    // click the trigger a second time to dismiss. z-index 190 < panel's 200.
    // Order matters: this block MUST come AFTER the panel so `anchor:` on
    // the panel resolves to the trigger (the panel's previous sibling), not
    // to the backdrop.
    block {
      visibility: open
      position: 'fixed'
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 190
      on click: close()
    }
  }
}
