component BottomSheet(
  open: boolean = false,
  snapPoints: array = [0.5, 1.0],
  initialSnap: number = 0,
  showHandle: boolean = true,
  backdrop: boolean = true
) {
  @state {
    showing: false
    currentY: 0
    snapIndex: 0
    dragging: false
  }

  @computed {
    sheetTransform: match showing {
      true -> match dragging {
        true -> "translateY(" + currentY + "px)",
        _ -> "translateY(0)"
      },
      _ -> "translateY(100%)"
    }
    sheetHeight: match snapIndex {
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

  block {
    // Backdrop
    block {
      visibility: showing == true && backdrop == true
      position: "fixed"
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 998
      background: "rgba(0, 0, 0, 0.4)"
      on click: doClose()
    }

    // Sheet
    block {
      visibility: showing == true
      position: "fixed"
      bottom: 0px
      left: 0px
      right: 0px
      z-index: 999
      height: sheetHeight
      max-height: 95vh
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
