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
// Keyboard dismissal (Vector #2726): focus leaving trigger and panel closes
// the popover (the backdrop only hears the mouse, so Tab past an open one
// left the backdrop over the page), and Escape closes it and puts focus back
// on the trigger, not on <body>. The DOM half is anchored-menu.js; on iOS and
// Android its stand-ins answer null, which reads as "stay open".
//
// `lazy: true` builds the content the first time the popover opens instead of
// at mount (Vector #3603: a closed DataGrid column chooser was 391 of the 786
// hidden elements on /fleet). Once built it stays, hidden while closed, so its
// state survives a close. Positioning still lands right: the panel's
// ResizeObserver re-places it when the content arrives after the open.
// Default false, because a caller may read its closed content from the DOM.
//
// Caveat: if any ancestor of the trigger has a non-`none` `transform`,
// `filter`, or `perspective`, browsers re-root the panel's `position:fixed`
// against that ancestor (CSS Transforms spec). Audit ancestors if the panel
// lands at the wrong coordinates.

@extern { menuFocusLeft, menuFocusTrigger } from "@spec/components/anchored-menu.js"

component Popover(placement: string = "bottom", closeOnContentClick: boolean = false, lazy: boolean = false) {
  @state {
    open: false
  }

  @computed {
    // True from the first open on (a match arm is keep-alive), or always when
    // the caller wants the content built at mount.
    contentLive: open || lazy == false
  }

  @actions {
    toggle() { open = open == false }
    close() { open = false }
    // Escape is consumed only when it closed something: stopped here, so an
    // enclosing dialog or page does not close too; while closed it bubbles.
    onKey(event) {
      if event.key != 'Escape' || open == false { return }
      event.stopPropagation()
      close()
      menuFocusTrigger(event)
    }
    onFocusOut(event) {
      if open && menuFocusLeft(event) { close() }
    }
  }

  block {
    inline: true

    // Escape closes while focus is inside the trigger or panel — the common
    // keyboard flow (click/Enter the trigger, then Escape). Keydown bubbles
    // from the focused child to this root block; there is no document-level
    // listener, so Escape with focus elsewhere on the page is the caller's
    // responsibility (see Vector's bubble-to-root pattern for pages).
    // focus-out BUBBLES (plain blur does not), so this hears focus leaving
    // any of the three children; menuFocusLeft says whether it left them all.
    on key-down(event): onKey(event)
    on focus-out(event): onFocusOut(event)

    // Trigger — caller-supplied content via @slot("trigger")
    // data-menu-trigger is where Escape sends focus back to.
    // tabindex "-1" keeps this wrapper OUT of the tab order (Vector #2781):
    // the caller's button is the single tab stop, and its click bubbles here.
    // Without it the click handler makes the compiler add tabindex="0", an
    // unnamed stop before every trigger. So the slot must be focusable (a
    // Button or `button {}`), as HoverCard's is. The explicit cursor keeps
    // the pointer the compiler's default gave.
    block {
      data-menu-trigger: 'true'
      tabindex: "-1"
      cursor: 'pointer'
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

      match contentLive {
        true -> { @slot("content") }
        _ -> {}
      }
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
      // Without these two, the click handler makes the compiler add
      // tabindex="0" + Enter/Space activation + cursor:pointer — an invisible
      // fullscreen tab stop with a pointer cursor. Explicit tabindex/cursor
      // suppress those defaults (the backdrop must stay unreachable by Tab).
      tabindex: "-1"
      cursor: 'default'
      on click: close()
    }
  }
}
