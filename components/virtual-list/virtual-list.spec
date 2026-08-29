@extern { computeWindow } from "@spec/components/grid-window.js"
@extern { wireVirtualList, useFixedHeight, genVirtualListId } from "@spec/components/virtual-list-wire.js"

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
// Usage — SIZED BY CSS (preferred):
//   @state { visStart: 0, visEnd: 20 }
//
//   VirtualList(
//     totalCount: pilots.length,
//     rowHeight: 64,
//     height: '100%'          // any CSS length; the list measures itself
//   ) {
//     on range(e): { visStart = e.start; visEnd = e.end }
//
//     each (pilots |> slice(visStart, visEnd)) as p (p.id) {
//       PilotRow(p: p, ...)
//     }
//   }
//
// ── `height` VS `viewportHeight` ──────────────────────────────────────────
// `height` is a CSS length and the list measures its own scroller, the way
// DataGrid does. `viewportHeight` is the older pixel prop and still works
// unchanged, for a caller that genuinely knows its height.
//
// Prefer `height`. A caller on a phone CANNOT honestly supply a pixel number:
// the visible height moves with the software keyboard, with the URL bar
// collapsing on scroll, and with rotation — and iOS Safari does not reliably
// fire `resize` for the second of those. Passing a stale number renders too
// few rows at the bottom of the list, which looks like a data bug.
//
// `viewportHeight` is still useful ALONGSIDE `height`: it seeds the very first
// window, before a measurement exists, so the opening screen is not empty for
// a frame. It is an estimate, not a contract — the measured value replaces it.
//
// **Give the list a parent with a resolvable height.** `height: '100%'` inside
// a box that sizes to its content makes clientHeight content-derived, and the
// list will measure the full stack rather than the visible window — i.e.
// windowing silently does nothing. In a flex column that means the usual
// `grow: true` + `min-height: 0` on the parent.
//
// How it works:
//   • The component owns a scroll container of `height`.
//   • Two spacer blocks (above and below the @children slot) preserve the
//     full scrollbar length: top spacer = visStart * rowHeight, bottom
//     spacer = (totalCount - visEnd) * rowHeight. The browser's scrollbar
//     thinks the list is the full height.
//   • On every scroll, scrollTop is read, the new [visStart, visEnd) range
//     is computed, and emit("range", {start, end}) lets the caller update
//     their slice. The caller's `each` re-renders only the new window.
//   • `range` is ALSO emitted when the measured height changes, because a
//     taller viewport needs more rows and nothing else would ask for them.
//
// Limitations:
//   • Fixed row height only — variable-height rows would need measurement
//     after each render, which adds complexity. Rows that wrap can break
//     the alignment unless `height: rowHeight` is set on the row template.
//     A list of SECTIONS (a header at one height, rows at another) is not
//     addressable by this component at all: the spacers are `start *
//     rowHeight`, so a mixed pitch puts the scrollbar out by the difference.
//   • Doesn't include scroll-to-row support — caller must compute the
//     scroll offset themselves and set it.

component VirtualList(
  totalCount: number,
  rowHeight: number,
  viewportHeight: number = 0,
  height: string = "",
  overscan: number = 5
) {
  @state {
    scrollTop: 0
    // Identity in the DOM, so the wire can find this instance's scroller.
    // Minted once per mount, exactly as DataGrid mints its grid id.
    _vlId: genVirtualListId()
    // The last height the wire reported. -1, NOT 0, because 0 is a real answer
    // — a display:none ancestor, a collapsed section, an iOS keyboard — and the
    // wire deliberately reports it. With 0 as the sentinel, a genuinely
    // zero-height list fell back to the `viewportHeight` seed and windowed a
    // screenful of rows into a box nobody can see.
    measuredHeight: -1
  }

  @computed {
    // Measured wins once there is one; `viewportHeight` is the seed that keeps
    // the first frame from being empty. A caller using the legacy pixel prop
    // alone never measures, and this resolves to exactly what they passed.
    effHeight: measuredHeight >= 0 ? measuredHeight : viewportHeight

    // The scroller's CSS height: the caller's `height` when given, otherwise
    // the legacy pixel prop rendered as one.
    outerHeight: height != '' ? height : (viewportHeight + 'px')

    // Attach the height wire — only when sizing by CSS, since a caller who
    // passed a pixel height has already told us what we would measure.
    //
    // In a @computed, like DataGrid's `_windowTeardown`, so it re-attaches if
    // the caller's `height` changes. The falsy arm is `releaseVirtualList`, NOT
    // null: switching from CSS sizing to a pixel height must not abandon a live
    // wire with its ResizeObserver still attached.
    _vlTeardown: height != ''
      ? wireVirtualList(_vlId, onMeasuredHeight)
      : useFixedHeight(_vlId, viewportHeight)

    // The window calculation lives in grid-window.js, shared with DataGrid.
    // Two components computing the same thing is how they drift.
    win: computeWindow({
      scrollTop: scrollTop,
      viewportHeight: effHeight,
      rowHeight: rowHeight,
      totalCount: totalCount,
      overscan: overscan
    })
    visStart: win.start
    visEnd: win.end
    topPad: win.topPad + 'px'
    botPad: win.botPad + 'px'
  }

  @actions {
    onScrollEvt(e) {
      scrollTop = e.target.scrollTop
      emit("range", { start: visStart, end: visEnd })
    }

    // A taller viewport needs more rows, and no scroll has happened to ask for
    // them — the list would sit under-filled until the reader moved it.
    onMeasuredHeight(h) {
      measuredHeight = h
      emit("range", { start: visStart, end: visEnd })
    }

    // Same reason, for the other input that can arrive late.
    //
    // On a cold load the wire measures within a microtask, while `totalCount`
    // is still 0 — computeWindow returns EMPTY for a zero count, so that first
    // emit tells the caller its range is [0, 0) and overwrites whatever it had
    // seeded. When the real count lands there is no scroll and no resize, so
    // nothing asks again and the list renders nothing at all.
    //
    // It survived review because removing a loading placeholder happens to
    // resize the scroller and trip the ResizeObserver; a caller whose
    // placeholder is styled differently gets an empty list.
    onCountChange() {
      emit("range", { start: visStart, end: visEnd })
    }

    // Sizing by CSS again after a spell on the pixel prop. The measurement from
    // last time is stale and must not be believed: without this the window
    // stayed pinned to it forever, because nothing else ever writes
    // `measuredHeight` down. A caller toggling `height: ready ? '100%' : ''`
    // could never get `viewportHeight` back.
    onHeightModeChange() {
      measuredHeight = -1
    }
  }

  @watch {
    // EVERY input computeWindow takes, not just the count.
    //
    // `computeWindow` reads scrollTop, viewportHeight, rowHeight, totalCount
    // and overscan. Scroll and the measured height already emit; these three
    // are the rest, and they move the window exactly as much. Measured at 1043
    // rows in a 600px viewport, `rowHeight` 30 -> 15 widened the window from
    // [0,25) to [0,45) and halved the bottom spacer — while emitting nothing,
    // so the caller kept rendering 25 rows into space reserved for 45 and left
    // ~300px blank under a perfectly correct scrollbar.
    totalCount: { onCountChange() }
    rowHeight: { onCountChange() }
    overscan: { onCountChange() }
    height: { onHeightModeChange() }
  }

  block {
    // How the wire finds this instance. Static per mount.
    data-virtual-list: _vlId
    height: outerHeight
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
