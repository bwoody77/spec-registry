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
//   HoverCard(placement: 'top'|'bottom'|'left'|'right', showDelay: ms,
//             hideDelay: ms, tapAndFocus: boolean) {
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
//   tapAndFocus (default false — hover-only, the pre-0.3 behavior) adds
//   three trigger modes for touch and keyboard reachability:
//     • keyboard focus opens the card immediately; blur closes it (via the
//       normal hideDelay so a focus→card-hover sweep doesn't flicker).
//     • click/tap toggles a STICKY open: a click while hover-open pins the
//       card instead of closing it (so a desktop click never feels like it
//       "closed" the card); a second click unpins and closes.
//     • while sticky, a fullscreen backdrop (same idiom as Popover's) closes
//       the card on outside tap — this is what makes tap-away work on touch
//       devices, where blur is unreliable. NOTE: while the backdrop is up it
//       swallows hover on other triggers; the user dismisses first, exactly
//       like Popover. The trigger's click stops propagation, so a HoverCard
//       inside a clickable row never fires the row's own click.
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
  hideDelay: number = 80,
  tapAndFocus: boolean = false
) {
  @state {
    visible: false
    // Set by a click/tap (tapAndFocus mode): the card is pinned open and
    // ignores mouse-leave/blur until unpinned by a second click or a
    // backdrop tap.
    sticky: false
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
      if !sticky {
        delay("hc-hide", hideDelay) { visible = false }
      }
    }
    // Called from the card's own mouse-enter so moving from trigger into
    // the card doesn't trip the trigger's mouse-leave → hideCard chain.
    keepOpen() {
      clearDelay("hc-hide")
    }

    // ── tapAndFocus mode ─────────────────────────────────────────────────
    // Keyboard focus shows immediately (no showDelay — a keyboard user has
    // already committed; the delay only exists to filter accidental hovers).
    focusShow() {
      if !tapAndFocus { return }
      clearDelay("hc-hide")
      visible = true
    }
    blurHide() {
      if !tapAndFocus { return }
      clearDelay("hc-show")
      if !sticky {
        delay("hc-hide", hideDelay) { visible = false }
      }
    }
    // Click/tap sticky-toggle. stopPropagation keeps a HoverCard inside a
    // clickable row (table rows opening a detail view) from firing the row.
    tapToggle(ev) {
      if !tapAndFocus { return }
      ev.stopPropagation()
      clearDelay("hc-show")
      clearDelay("hc-hide")
      if sticky {
        sticky = false
        visible = false
      } else {
        sticky = true
        visible = true
      }
    }
    // Backdrop + card clicks must NOT bubble: both blocks are DOM
    // descendants of the trigger's ancestors, so inside a clickable row a
    // bubbled click would fire the row's own handler (navigate/open) the
    // moment the user dismisses the card. (Popover has the same structure
    // but its consumers don't sit inside clickable rows, so it never bit.)
    closeSticky(ev) {
      ev.stopPropagation()
      sticky = false
      visible = false
    }
    swallowCardTap(ev) {
      ev.stopPropagation()
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
    // The focus/blur/click handlers are no-ops unless tapAndFocus is set
    // (each checks the prop first), preserving pre-0.3 behavior exactly.
    //
    // focus-in/focus-out (the BUBBLING variants), not focus/blur: plain
    // focus never bubbles, so a listener on this wrapper would only fire
    // for the wrapper itself, not for the caller's button inside the slot.
    // tabindex "-1" keeps this wrapper OUT of the tab order — without it
    // the compiler's kbActivate rule (any div with `on click`) adds
    // tabindex="0" and keyboard users hit TWO tab stops per trigger, only
    // one of which works. The caller's slot content must be natively
    // focusable (a `button {}` or Button) for keyboard access: Enter/Space
    // fire its native click, which bubbles here to tapToggle.
    block {
      tabindex: "-1"
      on mouse-enter: showCard()
      on mouse-leave: hideCard()
      on focus-in: focusShow()
      on focus-out: blurHide()
      on click(event): tapToggle(event)
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
      on click(event): swallowCardTap(event)
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

    // Outside-tap backdrop — only while sticky (tapAndFocus mode). Same
    // idiom as Popover's: a fixed fullscreen sibling BELOW the card in
    // z-order; a click on it unpins and closes. Order matters: this block
    // MUST come AFTER the card so `anchor:` on the card resolves to the
    // trigger (the card's previous sibling), not to the backdrop.
    block {
      visibility: sticky
      position: 'fixed'
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 990
      on click(event): closeSticky(event)
    }
  }
}
