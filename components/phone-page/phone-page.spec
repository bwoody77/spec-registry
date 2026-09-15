// PhonePage — the shared phone page layout: an optional sticky top bar, a
// scrolling body, an optional pinned bottom bar.
//
// The bars are ALWAYS sticky and the component never learns which scroll mode
// its host is in. While the host keeps the page height-locked, scrolling
// happens in the body BETWEEN the bars, so sticky resolves against a scroller
// the bars are not inside and does nothing. When the host releases the body's
// scroll so the document scrolls (which is what lets a mobile browser collapse
// its toolbars), the same bars hold their positions.
//
// `topOffset` / `bottomOffset` are where the bars park — a host with its own
// chrome passes its header and tab-bar heights; the default parks them at the
// viewport edges.
//
// An omitted bar is HIDDEN, not absent. `visibility:` emits `display: none` +
// `aria-hidden="true"` and leaves the node in the DOM, so `[data-page-top-bar]`
// matches on every page whether or not it has a top bar. Anything reading this
// component's DOM — a test, a host CSS rule, a Playwright locator — must judge
// a bar by its computed display, never by whether the selector matched.
// `phone-page.test.ts` carries the `isShown` helper for that; it is the same
// rule `data-grid-detail-slot.test.ts` documents for the grid's detail row.
//
// The three blocks live inside a root `block {}` rather than directly in the
// component body: a component body takes statements, not style declarations,
// so `width:` at that level is a parse error.
//
// The BARS own their inset too (0.2.0). `barPadX` / `barPadTop` /
// `barPadBottom` pad the top bar and `bottomPad` pads the bottom one, and all
// four default to the values Vector's `my-students-mobile` renders — 14px
// across, 10px above the field and 12px below it, 12px around the bottom
// bar — so adopting them changes nothing visually. 0.1.0 supplied the bars'
// background, border and position but no padding, which left every calling
// page to wrap its slot content in a padding block of its own: nineteen
// identical wrappers waiting to be written, and identical only until one of
// them drifted.
component PhonePage(
  topBar: string = "sticky",
  bottomBar: string = "pinned",
  topOffset: string = "0px",
  bottomOffset: string = "0px",
  gap: string = "12px",
  padX: string = "14px",
  padTop: string = "14px",
  padBottom: string = "24px",
  barPadX: string = "14px",
  barPadTop: string = "10px",
  barPadBottom: string = "12px",
  bottomPad: string = "12px"
) {
  block {
    width: 100%
    height: 100%
    layout: vertical, gap: 0px
    background: semantic.background

    block {
      visibility: hasSlot("topBar")
      data-page-top-bar: topBar
      position: topBar == "sticky" ? "sticky" : "static"
      top: topOffset
      z-index: 5
      background: semantic.surface
      border-bottom: borders.default
      padding-x: barPadX
      padding-top: barPadTop
      padding-bottom: barPadBottom
      @slot("topBar")
    }

    block {
      data-page-body: "true"
      grow: true
      min-height: 0
      overflow: "auto"
      layout: vertical, gap: gap
      padding-x: padX
      padding-top: padTop
      padding-bottom: padBottom
      @children
    }

    block {
      visibility: hasSlot("bottomBar")
      data-page-bottom-bar: bottomBar
      position: bottomBar == "pinned" ? "sticky" : "static"
      bottom: bottomOffset
      z-index: 5
      background: semantic.surface
      border-top: borders.default
      padding: bottomPad
      @slot("bottomBar")
    }
  }
}
