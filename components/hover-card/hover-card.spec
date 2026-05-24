// HoverCard — hover-triggered popover that escapes overflow:auto ancestors.
//
// Purpose:
//   A trigger-anchored overlay positioned via the runtime's `positionDropdown`
//   helper (`anchor:` keyword). Because positionDropdown sets `position: fixed`
//   with viewport-relative coordinates, the card is NOT clipped by any
//   `overflow: hidden | auto` ancestor — the recurring pain point that
//   Tooltip's `position: absolute` and Popover's `overlay(anchor: "parent")`
//   both suffer from.
//
// API:
//   HoverCard(placement: 'top'|'bottom'|'left'|'right', showDelay: ms, hideDelay: ms) {
//     slot("trigger") { ... }   // element the user hovers
//     slot("content") { ... }   // card body (your styled chrome inside)
//   }
//
//   placement defaults to 'top' with auto-flip to 'bottom' when there's
//   insufficient space above (handled by positionDropdown). showDelay
//   defaults to 200ms — long enough that brushing past a trigger doesn't
//   flash the card, short enough to feel responsive on deliberate hover.
//   hideDelay defaults to 80ms so the user can sweep from trigger into
//   the card without crossing a "dead zone" that closes the card mid-move.
//
// Caveat (web target):
//   positionDropdown anchors via `position: fixed`. If ANY ancestor of the
//   HoverCard has a non-`none` `transform`, `filter`, or `perspective` value,
//   browsers re-root fixed-positioned descendants against that ancestor (CSS
//   Transforms spec) and the card lands relative to that ancestor instead
//   of the viewport. If you hit clipping despite using HoverCard, audit
//   ancestors for `transform: translateY(...)` etc. on hover handlers.
//
//   Long-term fix: positionDropdown could physically reparent the card to
//   document.body. That's a bigger runtime change — out of scope here.

component HoverCard(
  placement: string = 'top',
  showDelay: number = 200,
  hideDelay: number = 80
) {
  @state {
    visible: false
  }

  @actions {
    showCard() {
      // clearDelay covers the "user hovers in, hovers out, hovers back in
      // within hideDelay" case — without it the hide fires after they've
      // already moved back over the trigger.
      clearDelay("hc-hide")
      delay("hc-show", showDelay) { visible = true }
    }
    hideCard() {
      clearDelay("hc-show")
      delay("hc-hide", hideDelay) { visible = false }
    }
    // Called from the card's own mouse-enter so moving from trigger into
    // the card doesn't trip the trigger's mouse-leave → hideCard chain.
    keepOpen() {
      clearDelay("hc-hide")
    }
  }

  // Outer wrap groups the trigger and card so `anchor: <placement>` on the
  // card resolves to the trigger (the previous sibling). Without this outer
  // block the two siblings would be at the component root, which the
  // compiler's emitChildren may not treat as a sibling pair for anchor
  // resolution. The outer wrap is inline-block so the component slots into
  // normal text flow next to siblings instead of stretching to its parent.
  block {
    inline: true

    // Trigger — wraps the user-supplied content with hover handlers.
    block {
      on mouse-enter: showCard()
      on mouse-leave: hideCard()
      @slot("trigger")
    }

    // Card — `anchor: <placement>` invokes positionDropdown when visibility
    // flips true. positionDropdown sets `position: fixed`, computes top/left
    // from the previous sibling's getBoundingClientRect(), and auto-flips
    // above/below if there isn't enough space in the requested direction.
    block {
      visibility: visible
      anchor: placement
      on mouse-enter: keepOpen()
      on mouse-leave: hideCard()
      min-width: 240px
      max-width: 90vw
      padding: spacing.3
      background: semantic.surface
      border: borders.default
      border-radius: 12px
      shadow: elevation.floating
      z-index: 1000
      layout: vertical, gap: spacing.2
      @slot("content")
    }
  }
}
