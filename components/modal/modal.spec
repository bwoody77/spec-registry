// Modal — centred overlay dialog for focused content and actions.
//
// Handles the things every dialog needs and most hand-rolled ones forget:
// scroll lock and focus trap while open, focus release on close, Escape /
// backdrop dismiss, and a labelled `role="dialog"`.
//
// Props:
//   open      — controlled visibility
//   title     — header text; also the default accessible name
//   width     — dialog width (capped at 95vw)
//   chrome    — true (default) renders the built-in header and body padding.
//               Pass false when the caller supplies its own header — otherwise
//               the dialog shows two. With chrome: false the children fill the
//               dialog and own their padding.
//   ariaLabel — accessible name. Defaults to `title`, then "Dialog". Set this
//               when chrome is false, since there is no title to fall back on.
//   dialogShadow — shadow for the dialog. Defaults to elevation.floating. Apps
//               whose design system specifies a heavier dialog shadow can pass
//               their own rather than having every dialog flatten on adoption.
//               Named dialogShadow, not shadow, so it cannot be confused with
//               the `shadow:` style key it feeds.
//
// Emits: close()
//
// NO `align` PROP, deliberately. `overlay(align: …)` is compiled into a static
// cssText, so it only accepts a literal — a prop silently resolves to "center"
// and the dialog stays centred no matter what the caller passes. The compiler
// now rejects a non-literal there rather than quietly ignoring it. Bottom-sheet
// dialogs therefore need their own component with its own `align: "bottom"`
// overlay; they cannot be a variant of this one, because two overlays inside
// one component would each hold `@children` and render the caller's content
// twice.
component Modal(
  open: boolean = false,
  title: string = "",
  width: string = "500px",
  chrome: boolean = true,
  ariaLabel: string = "",
  dialogShadow: string = ""
) {
  @state {
    showing: false
  }

  @computed {
    // A generic "Dialog" tells a screen-reader user nothing about which dialog
    // they are in. Prefer the caller's label, then the visible title.
    label: ariaLabel != "" ? ariaLabel : (title != "" ? title : "Dialog")

    // Conditional styling is hoisted: an inline ternary on a prop is evaluated
    // once at mount and never re-read.
    bodyPadding: chrome ? spacing.5 : "0"
    shadowValue: dialogShadow != "" ? dialogShadow : elevation.floating
  }

  @actions {
    // Both guards are load-bearing now that the watch below is IMMEDIATE:
    // it runs once at construction, so whichever arm matches must be a no-op
    // when the dialog is already in that state.
    doOpen() {
      if showing { return }
      showing = true
      lockScroll()
      trapFocus()
    }
    doClose() {
      // Without this, a dialog constructed CLOSED would run the `_` arm at
      // mount: one phantom `close` emitted to a caller that wired real work to
      // it, and — worse — an `unlockScroll()` that releases the lock a
      // DIFFERENT, genuinely open dialog is holding.
      if !showing { return }
      showing = false
      unlockScroll()
      releaseFocus()
      emit("close")
    }
  }

  // IMMEDIATE (`open!:`) — it must also run at construction with the value the
  // caller passed, not only on later changes.
  //
  // The natural way to write a dialog is to gate it so it is not built until
  // it is needed:
  //
  //   block { visibility: isOpen   Modal(open: isOpen) { … } }
  //
  // A `visibility:`-gated subtree containing a component compiles to a
  // `lazyMount`, so the Modal is constructed at the exact moment `isOpen` turns
  // true — born with `open == true`. A plain `@watch` fires on a CHANGE and
  // never at construction, so `showing` stayed false, the overlay never
  // rendered, and clicking the trigger did nothing at all. Five dialogs shipped
  // permanently unopenable that way, with no error anywhere (Vector #646). The
  // gate was not a failed optimisation, it was the cause — so the fix belongs
  // here rather than in a rule asking every caller not to write the obvious
  // thing.
  @watch {
    open!: {
      match open {
        true -> doOpen()
        _ -> doClose()
      }
    }
  }

  overlay(visible: showing, anchor: "screen", align: "center", backdrop: "scrim") {
    on dismiss: doClose()

    // Dialog
    block {
      width: width
      max-width: 95vw
      max-height: 90vh
      overflow: "auto"
      background: semantic.surface
      border-radius: 14px
      shadow: shadowValue
      // NO backdrop-filter on this element. It used to carry blur(4px), which was
      // visually inert (semantic.surface is opaque, so it blurred a backdrop
      // nobody could see through) and silently broke every anchored popup inside
      // a dialog.
      //
      // A backdrop-filter other than none makes this element the containing block
      // for position:fixed descendants. positionDropdown writes viewport
      // coordinates, so a DatePicker/Select/Autocomplete popup landed offset by
      // exactly this box's origin, and — because it was no longer viewport-fixed —
      // started counting toward this box's scrollable overflow. Opening a calendar
      // grew scrollHeight by the popup's height and the browser then scrolled the
      // focused day cell into view, pushing the form out of sight.
      //
      // Measured in Chromium: scrollHeight 487 -> 959 and popup offset by
      // (dialog.top, dialog.left) with the filter; both zero without it.
      // If a blur is ever wanted here, put it on an element that is NOT an
      // ancestor of anchored popups.
      role: "dialog"
      aria-label: label

      layout: vertical

      // Header — suppressed when the caller supplies its own.
      block {
        visibility: chrome
        layout: horizontal, justify: between, align: center
        padding: spacing.4
        border-bottom: borders.default

        text(title) {
          visibility: title != ""
          style: type.heading-sm
          color: semantic.text-primary
        }

        // Close — a real button, so it is keyboard reachable and announced as a
        // control. A div with an on-click is invisible to assistive tech.
        button {
          width: 32px
          height: 32px
          border-radius: 8px
          border: "none"
          background: "transparent"
          cursor: "pointer"
          aria-label: "Close dialog"
          layout: horizontal, align: center, justify: center
          on click: doClose()
          on hover {
            background: semantic.surface-raised
          }

          text("×") {
            style: type.heading-sm
            color: semantic.text-tertiary
          }
        }
      }

      // Body — one slot, padding computed. Two visibility-gated blocks each
      // holding @children would render the caller's content twice, since
      // visibility is display:none rather than removal.
      block {
        padding: bodyPadding
        grow: true
        overflow: "auto"
        @children
      }
    }
  }
}
