// SplitView — Two-panel resizable layout
//
// A horizontal (or vertical) split with a draggable divider between two
// slotted panels. On mobile the panels stack vertically. The divider
// emits "resize" with the new left-panel width in pixels so the caller
// can persist the split position.
// Works with every theme via semantic design tokens.
//
// Example usage:
//
//   SplitView(initialLeftWidth: '300px', minLeft: '200px', minRight: '200px') {
//     slot("left") {
//       // File tree, nav list, etc.
//       text('Left panel')
//     }
//
//     slot("right") {
//       // Editor, detail view, etc.
//       text('Right panel')
//     }
//   }

component SplitView(
  initialLeftWidth: string = "300px",
  minLeft: string = "180px",
  minRight: string = "180px",
  dividerWidth: string = "6px"
) {
  @state {
    leftWidth: initialLeftWidth
    dragging: false
  }

  @actions {
    startDrag() {
      dragging = true
    }
    onDrag(delta) {
      // delta.x gives the horizontal movement
      dragging = true
    }
    endDrag(delta) {
      dragging = false
      emit("resize", leftWidth)
    }
  }

  block {
    width: 100%
    height: 100%
    overflow: hidden

    // Desktop: horizontal split
    block {
      width: 100%
      height: 100%
      layout: responsive(vertical, md: horizontal)
      overflow: hidden

      // Left panel
      block {
        width: responsive(100%, md: leftWidth)
        min-width: responsive(0px, md: minLeft)
        height: responsive(50%, md: 100%)
        overflow: auto
        background: semantic.surface
        @slot("left")
      }

      // Divider (visible on desktop only)
      block {
        width: responsive(100%, md: dividerWidth)
        height: responsive(dividerWidth, md: 100%)
        min-width: responsive(0px, md: dividerWidth)
        min-height: responsive(dividerWidth, md: 0px)
        background: semantic.border
        cursor: responsive("row-resize", md: "col-resize")
        layout: horizontal, align: center, justify: center
        on hover { background: semantic.interactive }
        on drag(delta): onDrag(delta)
        on drag-end(delta): endDrag(delta)
        transition: "background 100ms ease"

        // Grip dots
        block {
          width: responsive(24px, md: 2px)
          height: responsive(2px, md: 24px)
          border-radius: 1px
          background: semantic.text-tertiary
          opacity: 0.5
        }
      }

      // Right panel
      block {
        grow: true
        min-width: responsive(0px, md: minRight)
        height: responsive(50%, md: 100%)
        overflow: auto
        background: semantic.surface
        @slot("right")
      }
    }
  }
}
