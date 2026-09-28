// Tooltip — small hover-triggered text bubble anchored to a trigger.
//
// Uses the spec runtime's `anchor:` keyword to position the bubble via
// positionDropdown — same mechanism comboboxes use. positionDropdown sets
// `position: fixed` so the bubble escapes any `overflow: hidden | auto`
// ancestor (a common pain point for tooltips inside data grids, dropdown
// menus, or scrolling cards). Auto-flips above/below based on viewport
// space and clamps the right edge.
//
// `anchor: placement` passes the prop through as an expression — evaluated
// when positionDropdown runs (compiler support added 2026-06-10; before
// that a non-literal anchor was silently dropped and the identifier parsed
// as a phantom component).
//
// Caveat: if any ancestor of the trigger has a non-`none` `transform`,
// `filter`, or `perspective`, browsers re-root the bubble's `position:fixed`
// against that ancestor (CSS Transforms spec). For richer hover overlays
// that need to escape transformed ancestors, see HoverCard (which doesn't
// solve this either at the spec level — it's an open Spec limitation).

component Tooltip(text: text = "", placement: string = "top") {
  @state {
    visible: false
  }

  @actions {
    showTip() { delay("show", 300) { visible = true } }
    hideTip() {
      clearDelay("show")
      visible = false
    }
  }

  // Outer wrap groups trigger + bubble so `anchor:` on the bubble resolves
  // to the trigger as previous sibling. `inline: true` keeps Tooltip
  // composable next to inline siblings (the prior version did the same).
  block {
    inline: true
    on mouse-enter: showTip()
    on mouse-leave: hideTip()
    on focus: showTip()
    on blur: hideTip()

    // Trigger — caller-supplied content
    block {
      @children
    }

    // Bubble — anchored to the trigger (previous sibling) via positionDropdown.
    // visibility on the block (not on the text — text() silently ignores
    // visibility per spec compiler quirk).
    //
    // Sized `max-content` capped at 320px, and the text WRAPS. It used to be
    // `white-space: nowrap` with no cap, which is fine for "Due soon" and
    // unreadable for free-form text: a grounding squawk on Vector's schedule
    // rail ran as one line from one edge of the window to the other.
    // `max-content` (not shrink-to-fit) keeps a short tip on one line even when
    // the bubble first lands near the right edge, where shrink-to-fit would
    // wrap it into the little space left before positionDropdown clamps it.
    // A declared width also skips positionDropdown's trigger-width floor,
    // which a tooltip never wanted. `overflow-wrap: anywhere` breaks a long
    // unspaced token (a URL, an id) instead of letting it burst the cap.
    block {
      visibility: visible == true
      anchor: placement
      width: 'max-content'
      max-width: 'min(320px, calc(100vw - 16px))'
      padding: spacing.2
      background: "#1e293b"
      border-radius: 6px
      shadow: elevation.floating
      z-index: 1000

      text(text) {
        style: type.label-sm
        color: "#f1f5f9"
        overflow-wrap: 'anywhere'
      }
    }
  }
}
