// A centred panel that slides in over a scrim. NOT an edge-anchored drawer,
// despite the name — the overlay is align:center, so the panel sits in the
// middle of the viewport at its natural height.
//
// The `side` prop was removed. It read as "which edge does this attach to",
// and it never did that: both `side` branches rendered a centred panel of
// identical geometry. All it actually chose was the direction the panel slid
// in from, which is not worth a prop that misdescribes the component. Slide-in
// is now fixed to `translateX(100%)` — the direction five of the six known call
// sites already had, all of which passed `side: "right"` expecting a right-hand
// drawer they were never getting.
//
// If an edge-anchored drawer is wanted, that is a different component (or an
// `align` on the overlay plus a full-height panel), not this prop.
component Drawer(open: boolean = false, title: string = "", width: string = "280px") {
  @state {
    showing: false
  }

  @computed {
    // The open value is `none`, NOT `translateX(0)`. Any transform other than
    // none — including an identity one — makes the panel the containing block
    // for position:fixed descendants, which silently breaks positionDropdown:
    // an anchored popup (Select, DatePicker, Autocomplete, Tooltip, HoverCard)
    // inside the drawer would land offset by the panel's origin and re-enter
    // the panel's scrollable overflow — measured at several hundred pixels off
    // its trigger for a centred panel. Same bug modal.spec had via
    // backdrop-filter.
    //
    // Transitioning TO `none` still animates: transitions interpolate through
    // the identity matrix and then settle on the specified value, so the slide
    // is unchanged and the containing block is released once open. (An
    // `animation` with fill-forwards does NOT work here — it retains the
    // interpolated matrix and the containing block survives. Measured.)
    panelTransform: match showing {
      true -> "none",
      _ -> "translateX(100%)"
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

    // ONE panel, deliberately.
    //
    // This used to be two byte-identical blocks gated on `side == "left"` and
    // `side == "right"`. Nothing in either block depended on `side` — the slide
    // direction comes from panelTransform — so the pair rendered identically and
    // the gate only chose which copy was display:none.
    //
    // That cost real money. `visibility:` compiles to display:none, not removal,
    // so BOTH copies mounted, and each held `@children`: every Drawer in the app
    // mounted the caller's entire content twice. Measured on Vector's
    // /approvals drawer: 293 elements in each panel, two live FlightDetailPanel
    // instances, two "Close drawer" buttons — duplicate fetches, duplicate
    // subscriptions, duplicate ids, and the whole panel announced twice to a
    // screen reader. modal.spec carries a comment warning about exactly this
    // ("Two visibility-gated blocks each holding @children would render the
    // caller's content twice"); Drawer had the bug that comment describes.
    //
    // Collapsing is behaviour-preserving for what was VISIBLE: the surviving
    // block is identical to both originals, and exactly one was ever shown.
    block {
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

        // Close — a real button, so it is keyboard reachable and announced as
        // a control. A `block { on click }` renders a <div>: not tabbable, not
        // in the a11y tree as a control, and invisible to a screen reader. This
        // is the drawer's ONLY close affordance besides backdrop dismiss, so as
        // a div it left keyboard users no way out of an open drawer. `border`
        // and `background` are reset because the button primitive brings the
        // browser's default chrome. Matches modal.spec's close button.
        button {
          width: 32px
          height: 32px
          border-radius: 8px
          border: "none"
          background: "transparent"
          cursor: "pointer"
          aria-label: "Close drawer"
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
