// NOTE: the `backdrop` prop was removed because it never worked. It was wired
// to `overlay(backdrop: match backdrop { … })`, but overlay compiles its
// backdrop into a static cssText and only reads a string literal — a non-literal
// silently resolved to the default, so the scrim always rendered no matter what
// a caller passed. The compiler now rejects a non-literal there instead of
// ignoring it. Removing the prop changes no behaviour; it only stops the
// component advertising an option it never honoured. A scrim-less sheet needs a
// second component with its own `backdrop: "none"` overlay.
component BottomSheet(
  open: boolean = false,
  snapPoints: array = [0.5, 1.0],
  initialSnap: number = 0,
  showHandle: boolean = true,
  // Size to the content instead of to a snap point.
  //
  // The snap-point model assumes a sheet you drag between heights — a map, a
  // media player. The other common sheet is a short menu or confirm step that
  // should be exactly as tall as what is in it; forcing that to 50vh leaves
  // half a screen of empty surface under four rows. `max-height: 95vh` still
  // applies, so a long fit-content sheet caps and scrolls rather than running
  // off the top.
  //
  // With fitContent the sheet does not snap, so `snapPoints` / `initialSnap`
  // are ignored and the drag gesture only dismisses.
  fitContent: boolean = false,
  // Cap the sheet's width and centre it. Full-bleed by default, which is right
  // on a phone; on a tablet or a desktop breakpoint a sheet spanning 1200px
  // reads as a broken dialog. '' keeps the full-bleed behaviour.
  maxWidth: string = ""
) {
  @state {
    showing: false
    currentY: 0
    snapIndex: 0
    dragging: false
  }

  @computed {
    // The settled-open value is `none`, NOT `translateY(0)`. Any transform
    // other than none — including an identity one — makes the sheet the
    // containing block for position:fixed descendants, which silently breaks
    // positionDropdown: an anchored popup (Select, DatePicker, Autocomplete,
    // Tooltip) inside the sheet would land offset by the sheet's origin and
    // re-enter the sheet's scrollable overflow. Same bug modal.spec had via
    // backdrop-filter, and drawer.spec via translateX(0).
    //
    // Transitioning TO `none` still animates: transitions interpolate through
    // the identity matrix and settle on the specified value, so the slide is
    // unchanged. Mid-drag keeps a real translate, which is correct — the sheet
    // is genuinely offset then, and the drag ends in the settled `none`.
    sheetTransform: match showing {
      true -> match dragging {
        true -> "translateY(" + currentY + "px)",
        _ -> "none"
      },
      _ -> "translateY(100%)"
    }
    sheetHeight: match fitContent {
      true -> "auto",
      _ -> match snapIndex {
        0 -> match snapPoints.length > 0 {
          true -> (snapPoints[0] * 100) + "vh",
          _ -> "50vh"
        },
        _ -> match snapPoints.length > snapIndex {
          true -> (snapPoints[snapIndex] * 100) + "vh",
          _ -> "100vh"
        }
      }
    }
    // The overlay container is `display:flex; justify-content:center`, so a
    // capped sheet centres itself — no margin trickery needed.
    sheetMaxWidth: maxWidth != "" ? maxWidth : "100%"
  }

  @actions {
    doOpen() {
      showing = true
      snapIndex = initialSnap
      lockScroll()
    }
    doClose() {
      showing = false
      dragging = false
      currentY = 0
      unlockScroll()
      emit("close")
    }
    handleDrag(delta) {
      dragging = true
      currentY = match delta.y > 0 {
        true -> delta.y,
        _ -> 0
      }
    }
    handleDragEnd(delta) {
      dragging = false
      match delta.velocityY > 500 || currentY > 150 {
        true -> doClose()
        _ -> resetPosition()
      }
    }
    resetPosition() {
      currentY = 0
    }
    snapTo(index) {
      snapIndex = index
      emit("snap", index)
    }
  }

  @watch {
    open: {
      match open {
        true -> doOpen(),
        _ -> doClose()
      }
    }
  }

  overlay(visible: showing, anchor: "screen", align: "bottom", backdrop: "scrim") {
    on dismiss: doClose()

    // Sheet
    block {
      height: sheetHeight
      max-height: 95vh
      // A sheet is full-bleed on a phone; `maxWidth` caps it on a wider
      // viewport. Without an explicit width the sheet is a row-flex item and
      // would size to its content, which reads as a floating card rather than
      // a sheet attached to the bottom edge.
      width: 100%
      max-width: sheetMaxWidth
      background: semantic.surface
      border-radius: "16px 16px 0 0"
      shadow: elevation.floating
      transform: sheetTransform
      transition: match dragging {
        true -> "none",
        _ -> "transform 300ms cubic-bezier(0.32, 0.72, 0, 1), height 300ms cubic-bezier(0.32, 0.72, 0, 1)"
      }
      overflow: "hidden"
      scroll-boundary: "contain"

      layout: vertical

      // Drag handle
      block {
        visibility: showHandle == true
        padding-top: spacing.2
        padding-bottom: spacing.2
        layout: horizontal, justify: center
        cursor: "grab"
        on drag(delta): handleDrag(delta)
        on drag-end(delta): handleDragEnd(delta)

        block {
          width: 36px
          height: 4px
          border-radius: 2px
          background: semantic.text-tertiary
          opacity: 0.4
        }
      }

      // Content
      block {
        grow: true
        overflow: "auto"
        padding-bottom: env(safe-area-inset-bottom)
        scroll-boundary: "contain"
        @children
      }
    }
  }
}
