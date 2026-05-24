// VirtualList — virtualized scroll container for very large lists.
//
// Renders only the rows currently in the viewport (plus a small overscan
// buffer above and below), keeping the DOM constant-size regardless of how
// many items the list contains. Works with ANY child template — the caller
// keeps their declarative spec row (`PilotRow`, `FleetRow`, etc.) and just
// slices their data by the emitted visible range.
//
// Requires a **fixed row height** — the virtualization math depends on
// knowing each row's pixel height upfront. Pass `rowHeight` in px.
//
// Usage:
//   @state { visStart: 0, visEnd: 20 }
//
//   VirtualList(
//     totalCount: pilots.length,
//     rowHeight: 64,
//     viewportHeight: 600
//   ) {
//     on range(e): { visStart = e.start; visEnd = e.end }
//
//     each (pilots |> slice(visStart, visEnd)) as p (p.id) {
//       PilotRow(p: p, ...)
//     }
//   }
//
// How it works:
//   • The component owns a scroll container of `viewportHeight` px.
//   • Two spacer blocks (above and below the @children slot) preserve the
//     full scrollbar length: top spacer = visStart * rowHeight, bottom
//     spacer = (totalCount - visEnd) * rowHeight. The browser's scrollbar
//     thinks the list is the full height.
//   • On every scroll, scrollTop is read, the new [visStart, visEnd) range
//     is computed, and emit("range", {start, end}) lets the caller update
//     their slice. The caller's `each` re-renders only the new window.
//   • The overscan param (default 5 rows) keeps a few extra rows rendered
//     just outside the viewport so fast scrolling doesn't show whitespace
//     while the next frame computes.
//
// Limitations:
//   • Fixed row height only — variable-height rows would need measurement
//     after each render, which adds complexity. Rows that wrap can break
//     the alignment unless `height: rowHeight` is set on the row template.
//   • Doesn't include scroll-to-row support — caller must compute the
//     scroll offset themselves and set it.

component VirtualList(
  totalCount: number,
  rowHeight: number,
  viewportHeight: number,
  overscan: number = 5
) {
  @state {
    scrollTop: 0
  }

  @computed {
    // Visible window — first row whose top is visible, through last row
    // whose top is below the viewport bottom. Buffered by `overscan` on
    // each side so a fast scroll doesn't expose blank cells.
    rawStart: scrollTop / rowHeight
    rawEnd: (scrollTop + viewportHeight) / rowHeight
    visStart: rawStart - overscan < 0 ? 0 : floor(rawStart - overscan)
    visEnd: rawEnd + overscan > totalCount ? totalCount : ceil(rawEnd + overscan)

    // Spacer heights that compensate for the rows we DON'T render. Together
    // with the rendered slice they preserve the full scrollable length.
    topPadPx: visStart * rowHeight
    botPadPx: (totalCount - visEnd) * rowHeight
    topPad: topPadPx + 'px'
    botPad: botPadPx + 'px'
    viewportPx: viewportHeight + 'px'
  }

  @actions {
    onScrollEvt(e) {
      scrollTop = e.target.scrollTop
      emit("range", { start: visStart, end: visEnd })
    }
  }

  block {
    height: viewportPx
    overflow: auto
    on scroll: onScrollEvt(_e)

    // Top spacer — collapses the rows above the visible window into a
    // single pixel-perfect placeholder so the scrollbar stays accurate.
    block { height: topPad }

    // The caller's rendering — typically an `each` over a sliced subset.
    @children

    // Bottom spacer — same idea, for rows below the visible window.
    block { height: botPad }
  }
}
