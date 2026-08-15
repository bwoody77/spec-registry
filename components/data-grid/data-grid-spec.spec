@extern { genGridId, wireColumnDrag, wireGroupDrag } from "@spec/components/data-grid-column-drag.js"
@extern { gridDeriveGroupRows } from "@spec/components/grid-group-derive.js"
@extern { wireGridWindow, gridDataGeneration, gridScrollRowIntoView, releaseGridWindow } from "@spec/components/grid-window-wire.js"
@extern { retryBlock } from "@spec/components/grid-block-cache.js"

fn toggleSortState(sortState: list, colKey: string) -> list {
  let existing = sortState |> find(s => s.key == colKey)
  if existing != null {
    if existing.direction == 'asc' {
      return sortState |> map(s => s.key == colKey ? { key: colKey, direction: 'desc' } : s)
    }
    return sortState |> filter(s => s.key != colKey)
  }
  return [{ key: colKey, direction: 'asc' }]
}

fn applySortAndFilter(rows: list, sortState: list, filters: list) -> list {
  let sorted = _applySortToRows(rows, sortState)
  return _applyFilters(sorted, filters)
}

// ─── Column sizing ──────────────────────────────────────────────────────────
// Every cell is laid out with `grow: true` (a static `flex: 1 1 0%`), so the
// column's real size comes from min-width / max-width: a fixed column pins both
// to the same value, a flexible column sets only a floor and absorbs the slack.
// This is deliberate — `grow` is resolved at parse time and cannot vary per
// column, and it is what keeps the header, body, group and total rows sharing
// ONE width source so their columns cannot drift apart.

// ── THE PADDING INVARIANT ───────────────────────────────────────────────────
// A cell's width-bearing box carries NO padding. Every cell is an outer block
// holding min-width/max-width/grow and an inner block holding `padding` and the
// content.
//
// Spec blocks are content-box and Spec has no `box-sizing`, so padding declared
// beside min-width is ADDED to it: a column declaring `width: 90` rendered
// 106px. Every column drifting equally hid it — until the header-group row,
// whose cells span several columns. A segment covering N columns took ONE
// padding while its N members took N, so the group label sat (N-1) x 2 x padding
// short: 64px adrift over five columns, and every grid 16px-per-column wider
// than it asked for. cf-market's browse table declared 1130px, demanded 1322px,
// and pushed its Price column off screen.
//
// So: if you add padding to a cell, put it on the inner block. Padding on the
// box that carries min-width silently re-breaks alignment for every consumer.
fn gridColMin(col: map) -> string {
  if col.width != null { return (col.width + '') + 'px' }
  if col.minWidth != null { return (col.minWidth + '') + 'px' }
  return '100px'
}

fn gridColMax(col: map) -> string {
  if col.width != null { return (col.width + '') + 'px' }
  return '100000px'
}

// The horizontal half of a `padding` value, for the rows that can only take a
// longhand.
//
// `padding-x:` compiles to the paddingLeft/paddingRight LONGHANDS, and CSSOM
// silently DROPS a multi-value string on a longhand. `cellPadding` is a full
// `padding` value — the data cells take it through the `padding:` shorthand,
// where two values are legal — so a consumer passing `'9.92px 8px'` got
// correctly padded cells and placeholder rows with no horizontal padding at
// all. The skeleton bar then sat flush against the grid edge while every data
// cell started 8px in. Measured in cf's benchmark rate history.
//
// Positional, because that is how the shorthand is defined: one value is all
// four sides, two is `vertical horizontal`, three is `top horizontal bottom`.
// Four (`top right bottom left`) is the one case a single longhand cannot
// represent — left and right may differ — so it takes `right` and is the
// documented limit rather than a silent wrong answer.
fn gridPadX(pad: string) -> string {
  let parts = split(trim(pad), ' ') |> filter(p => p != '')
  if length(parts) < 2 { return pad }
  return parts[1]
}

// How many pixels of `columnRules` border this run of columns draws.
//
// The rule is a 1px `border-left` on every column but the leftmost ON SCREEN,
// and the cells are content-box — so it is width the column occupies, not
// decoration inside width it already had. Every width computed from
// `col.width`/`col.minWidth` has to add it back, or the thing being sized is
// narrower than the cells it must hold.
//
// This exists as its own fn rather than inline because three separate widths
// need the identical count and they drifted apart the first time: the segment
// floor, the segment ceiling, and the scroll track.
fn gridRulePx(cols: list, rules: boolean, firstKey: string) -> number {
  if !rules { return 0 }
  return cols |> reduce((acc, c) => acc + (c.key != firstKey ? 1 : 0), 0)
}

// Total of every visible column's floor — the width the rows must not shrink
// below. Set on the track so a narrow container scrolls instead of crushing.
fn gridTrackMin(cols: list, rules: boolean, firstKey: string) -> string {
  let total = cols |> reduce((acc, c) => acc + (c.width != null ? c.width : (c.minWidth != null ? c.minWidth : 100)), 0)
  return ((total + gridRulePx(cols, rules, firstKey)) + '') + 'px'
}

// ─── Header groups ──────────────────────────────────────────────────────────
// A column may declare `group: "<label>"`. CONSECUTIVE columns sharing a label
// collapse into one spanning segment of the composite header: a vertical stack
// of [group label] over [member headings]. A column with no `group` is its own
// unlabelled segment — a single full-height cell — so the header stays
// column-aligned with the body by construction.
//
// Runs are contiguous by design. A label that reappears after a gap yields two
// separate spans rather than one — merging them would mean silently reordering
// the caller's columns.
//
// ── SOLO GROUPS ─────────────────────────────────────────────────────────────
// A run of ONE is a legitimate and useful thing to declare: it is how a caller
// gets a two-line heading whose first line sits on the group line, level with
// the real groups beside it. cf-market's Shipment column does this — the label
// belongs above its month scale, and the scale is that column's sub-heading in
// the same way Grade/Moist are Quality's.
//
// So a solo group renders as A COLUMN WHOSE HEADING SITS ON THE GROUP LINE,
// not as a group of one:
//
//   · no left/right bracket. The bracket says "these N belong together"; at
//     N=1 it is a box round a single column, asserting nothing.
//   · the label carries the column's click-to-sort. The handler otherwise
//     lives only on the member cell, so lifting a heading onto the group line
//     would quietly cost it the click — a heading that still shows a sort
//     arrow and no longer responds to one.
//
// The bottom rule DOES draw, because that is what puts the label and its
// sub-headings on the same footing as a real group.
fn gridSegmentsOf(cols: list) -> list {
  return cols |> reduce((acc, c) => {
    let label = c.group != null ? c.group : ''
    let n = length(acc)
    if n > 0 && label != '' && acc[n - 1].label == label {
      let last = acc[n - 1]
      return acc.slice(0, n - 1).concat([{ label: label, cols: last.cols.concat([c]) }])
    }
    return acc.concat([{ label: label, cols: [c] }])
  }, [])
}

// ─── Segment run ids (column drag) ──────────────────────────────────────────
// The drag identity each header segment is stamped with. A segment is NOT the
// same thing as a `gridSegmentsOf` container, and it is NOT the group label.
//
// gridSegmentsOf merges a run into one container only when the label is
// non-empty, so every UNGROUPED column gets a container of its own. Stamping
// the LABEL therefore made every ungrouped column in the grid share one value
// — and ungrouped columns on OPPOSITE SIDES of a group then formed a single
// NON-CONTIGUOUS "segment", which the drag's snapshot, gap and slot math all
// assume cannot happen. cf-market's classic view is exactly that shape:
// dragging `port` right set g=1 and drew the placeholder over `ship`, while
// `qty` translated left over the Quality columns.
//
// So the identity is a RUN id: increment on every label change, EXCEPT between
// two consecutive empty-label segments. gridSegmentsOf has already merged
// same-label non-empty runs, so consecutive segments never share a non-empty
// label — the rule reduces to "increment unless BOTH this segment and the
// previous one are unlabelled", which is what keeps a run of ungrouped columns
// in one segment while splitting runs that a group sits between.
//
// The pinned and scrolling loops number independently; the distinct 'p:' / 's:'
// prefixes at the use site keep the two sides apart.
fn gridSegRunIds(segs: list) -> list {
  let runs = segs |> reduce((acc, s) => {
    let n = length(acc)
    if n == 0 { return [{ label: s.label, run: 0 }] }
    let prev = acc[n - 1]
    let same = prev.label == '' && s.label == ''
    return acc.concat([{ label: s.label, run: same ? prev.run : prev.run + 1 }])
  }, [])
  return runs |> map(r => r.run)
}

// Reorder `cols` to match `order`, a list of column keys.
//
// Keys in `order` that no longer name a column are ignored, and columns absent
// from `order` are appended in their declared order. So a saved order that has
// gone stale — a renamed key, a dropped column, a column added since it was
// saved — degrades to a sensible layout instead of stranding a column off the
// grid entirely.
//
// `order` is DE-DUPLICATED first, first occurrence winning. A repeated key
// otherwise survived into `ordered` twice, so `visibleColumns` came back with
// N+1 entries and one column rendered TWICE: two header cells and two body
// cells carrying the same `data-grid-col`, which also breaks every query in
// the column-drag wire. And because the grid re-emits its order through
// `columnOrderChange`, a caller that persists it persisted the corruption.
fn gridApplyColumnOrder(cols: list, order: list) -> list {
  if length(order) == 0 { return cols }
  let uniq = order |> reduce((acc, k) => {
    if (acc |> includes(k)) { return acc }
    return acc.concat([k])
  }, [])
  let known = uniq |> filter(k => cols |> some(c => c.key == k))
  let ordered = known |> map(k => cols |> find(c => c.key == k))
  let rest = cols |> filter(c => !(known |> includes(c.key)))
  return ordered |> concat(rest)
}

// How many columns carry a given group label, across the WHOLE table. Solo-ness
// is a property of the caller's column list, never of a pin-split fragment —
// see the note on `all` in gridSizedCols.
fn gridGroupSize(all: list, label: string) -> number {
  if label == '' { return 0 }
  return all |> reduce((acc, c) => acc + ((c.group != null && c.group == label) ? 1 : 0), 0)
}

// Each column carries its resolved min/max width plus its position at a group
// run's EDGE (`_gFirst` / `_gLast`), which is what `groupRules` draws the
// full-height bracket from: the component already knows where a run starts and
// ends, so a consumer never re-derives group boundaries in its own cells.
//
// `cols` is the pin-split list this cell belongs to; `all` is every visible
// column. The two are deliberately different inputs:
//
//   · _gFirst / _gLast are SPLIT-local. gridSegmentsOf never lets a run
//     straddle the pin boundary, so the body must treat that boundary as a run
//     edge too or header and body disagree about where the bracket falls
//     (the 0.7.1 fix).
//   · _gSolo is GLOBAL. A two-column run straddling the pin boundary leaves a
//     one-column fragment on each side, and judging solo-ness from the fragment
//     would strip the bracket off a real group — which is exactly what the
//     0.7.1 pinned-bracket test caught when this was first written split-local.
fn gridSizedCols(cols: list, all: list) -> list {
  let n = length(cols)
  return cols |> map((c, i) => {
    _col: c,
    _min: gridColMin(c),
    _max: gridColMax(c),
    _gFirst: c.group != null && c.group != '' && (i == 0 || cols[i - 1].group != c.group),
    _gLast: c.group != null && c.group != '' && (i == n - 1 || cols[i + 1].group != c.group),
    _gSolo: c.group != null && c.group != '' && gridGroupSize(all, c.group) == 1
  })
}

// A segment is as wide as the columns it covers. `grow` is resolved at parse
// time and cannot vary per element, so a segment spanning N columns still takes
// ONE share of leftover space while its N members take N: alignment is exact
// only when the grouped columns declare a fixed `width`, and drifts when they
// are flexible. That is why the docs tell callers to give grouped columns a
// width — it is a real constraint, not a style preference.
//
// The segment is the FLEX ITEM; its member cells live inside it. So it must be
// sized to the members' OUTER widths — their declared width plus the
// `columnRules` border each of them draws — and not to the declared widths
// alone. Sized to the bare sum, the header's columns sit 1px closer together
// than the body's for every ruled column, and the two sets of vertical lines
// walk apart down the row (cf's market blotter, 2026-08-15: 4px by the seventh
// column, with the sign flipping halfway because the flexible column absorbs
// whatever the fixed ones saved).
fn gridSegMin(seg: map, rules: boolean, firstKey: string) -> string {
  let total = seg.cols |> reduce((acc, c) => acc + (c.width != null ? c.width : (c.minWidth != null ? c.minWidth : 100)), 0)
  return ((total + gridRulePx(seg.cols, rules, firstKey)) + '') + 'px'
}

fn gridSegMax(seg: map, rules: boolean, firstKey: string) -> string {
  let flexible = seg.cols |> some(c => c.width == null)
  if flexible { return '100000px' }
  let total = seg.cols |> reduce((acc, c) => acc + c.width, 0)
  return ((total + gridRulePx(seg.cols, rules, firstKey)) + '') + 'px'
}

// ─── Row kinds ──────────────────────────────────────────────────────────────
// A row may declare `_kind`: 'group' (a collapsible header for the rows that
// name it in `_group`) or 'total' (a pinned-looking summary). Anything else is
// an ordinary row. `_accent` draws a left rail and `_opacity` dims the row.
// A group row may also carry `_toggleLabel` to name its expand/collapse control
// for screen readers (default: "Toggle group").

// Is this row ticked? In predicate mode the answer is NOT `selectedSet`: the
// user said "all 1043 matching", the grid holds a handful of keys, and reading
// the handful rendered every row on screen unticked while the caller was told
// 1043 were selected. In that mode a row is selected unless it is excluded.
fn gridRowChecked(allMatching: boolean, excluded: list, chosen: list, key: any) -> boolean {
  if allMatching { return !excluded.includes(key) }
  return chosen.includes(key)
}

// Union, order-preserving: the keys already chosen, plus the ones on screen
// that are not among them.
fn gridUnionKeys(chosen: list, adding: list) -> list {
  return chosen.concat(adding.filter(k => !chosen.includes(k)))
}

// The row `focusedRow` names. `focusedRow` is an ABSOLUTE index — the render
// has compared it against gridAbsIdx() since Task 7 — so windowed mode has to
// subtract the window start to reach the rendered row. Returns null when the
// focused row is outside the window (its block has not been fetched, or focus
// has moved ahead of a scroll); selectRow already null-guards, so a keypress
// on an unloaded row does nothing rather than selecting `undefined`.
// Where focus lands from "nothing focused yet". Row 0 is wrong for a windowed
// grid the user has already scrolled: the first arrow key would haul the list
// back to the top. The top of the CURRENT window is what they are looking at.
fn gridFirstFocus(isWindowed: boolean, start: number) -> number {
  if isWindowed { return start }
  return 0
}

fn gridFocusedRow(isWindowed: boolean, rendered: list, shown: list, start: number, idx: number) -> any {
  if !isWindowed { return shown[idx] }
  let rel = idx - start
  if rel < 0 { return null }
  if rel >= rendered.length { return null }
  return rendered[rel]
}

fn gridRowKind(row: map) -> string {
  if row._kind != null { return row._kind }
  return 'row'
}

// Window-relative loop index → absolute row index. Identity when windowing is
// off, which is what keeps the 16 existing consumers byte-identical. Task 7
// threads it through stripe parity, hover, row click and cell focus, all of
// which read the loop index and every one of which is wrong by `winStart`
// while a window is scrolled away from the top.
fn gridAbsIdx(isWindowed: boolean, start: number, idx: number) -> number {
  if isWindowed { return start + idx }
  return idx
}

// Did the block behind this rendered row fail? `winFailed` is a parallel array
// pushed alongside `winRows`, so this is written to tolerate a SHORT or absent
// one: unwindowed rendering leaves it empty and every index reads out of range,
// and a window that has grown is briefly longer than the flags it was pushed
// with. Out of range means "not failed", never "undefined" leaking into a
// `visibility:`.
fn gridBlockFailed(failed: list, idx: number) -> boolean {
  if idx < 0 { return false }
  if idx >= length(failed) { return false }
  return failed[idx] == true
}

// Which BLOCK a rendered row belongs to — the argument `blockRetry` carries.
// Three plausible values sit within one expression of each other here (the loop
// index, the absolute row index, the block index) and only this one can be fed
// back to retryBlock(). `size <= 0` cannot happen through the prop's default,
// but a caller passing 0 would divide by zero and emit Infinity.
fn gridBlockOf(start: number, idx: number, size: number) -> number {
  if size <= 0 { return 0 }
  return floor((start + idx) / size)
}

// Does the failure message and its Retry button belong on slot `idx`? Exactly
// one slot per failed block gets them, so a failed block states itself once
// instead of once per row.
//
// ── WHY THIS IS NOT "the block boundary", AND NOT "slot 0" EITHER ──────────
//
// Both simpler rules put the message somewhere the user cannot see, which is
// strictly worse than the repetition they replace: a screen of blank rows with
// no error on it and no way back.
//
//   `(start + idx) % size == 0` — a user scrolled into the middle of a failed
//   block has its boundary up to `size` rows above; nothing renders at all.
//
//   `idx == 0` — slot 0 is the top of the RENDERED window, which sits `over`
//   rows above the top of the VIEWPORT. Measured in Chrome, 2026-08-15: scrolled
//   into a failed block, 21 failed rows on screen and the message on none of
//   them, parked in the overscan. happy-dom reports every rendered row as
//   on-screen — it lays nothing out — so no unit test in this file can see it.
//
// So the message rides the first slot of its block AT OR AFTER the first
// VISIBLE slot, which pins it to the top of the viewport for a block the user
// is scrolled inside, and leaves it on the boundary for one that begins on
// screen. The block comparison is what separates two ADJACENT failed blocks —
// two distinct things to retry, one message each.
//
// `firstVisible` is measured and pushed by the wire (see WindowState) rather
// than derived here. Deriving it as `start > 0 ? overscan : 0` is wrong twice:
// it is off by the clamp at the top of the list, and — the one that actually
// hides the message — it ignores the composite header, which is `position:
// sticky` INSIDE the scroll container, so the row aligned to `scrollTop` sits
// UNDER it. The wire already measures that header for gridScrollRowIntoView.
// SkeletonRow's rendered height: a 38px SkeletonCircle is its tallest child and
// it adds no padding. The bar variant of the first-load placeholder matches it
// so the two variants stand in for the same box — a fallback that guessed
// differently would make `skeletonVariant` change the panel's height.
fn SKELETON_ROW_HEIGHT() -> string {
  return '38px'
}

// Is any slot of the current window a failed one? Drives the single live
// region — see its use site. A per-ROW live region cannot do this job: the
// message row moves from slot to slot as the user scrolls, so it announces
// either never (its text never changes) or once per row of travel.
fn gridAnyFailed(failed: list) -> boolean {
  for f in failed {
    if f == true { return true }
  }
  return false
}

fn gridBlockMsgSlot(failed: list, start: number, idx: number, size: number, firstVisible: number) -> boolean {
  if !gridBlockFailed(failed, idx) { return false }
  if idx < firstVisible { return false }
  if idx == firstVisible { return true }
  return gridBlockOf(start, idx, size) != gridBlockOf(start, idx - 1, size)
}

fn gridGroupIsOpen(openGroups: list, key: string) -> boolean {
  return openGroups |> some(k => k == key)
}

fn gridToggleGroup(openGroups: list, key: string) -> list {
  if gridGroupIsOpen(openGroups, key) { return openGroups |> filter(k => k != key) }
  return openGroups |> concat([key])
}

// Row-detail expansion. Deliberately a mirror of gridGroupIsOpen /
// gridToggleGroup rather than a second idiom for the same shape — this file
// already answers "is this key in that list" one way.
fn gridRowIsExpanded(expandedSet: list, key: string) -> boolean {
  return expandedSet |> some(k => k == key)
}

fn gridToggleExpanded(expandedSet: list, key: string) -> list {
  if gridRowIsExpanded(expandedSet, key) { return expandedSet |> filter(k => k != key) }
  return expandedSet |> concat([key])
}

// Drop rows belonging to a collapsed group. Group headers and totals always show.
fn gridVisibleRows(rows: list, openGroups: list) -> list {
  return rows |> filter(r => r._group == null || gridGroupIsOpen(openGroups, r._group))
}

// The DERIVED model's visibility rule, and the inverse of the one above.
//
// Structural grouping lists what is OPEN and defaults to closed; derived
// grouping lists what is CLOSED and defaults to open. Inverting either would
// move every existing consumer, so the two rules sit side by side and
// `groupBy` picks between them.
fn gridDerivedIsOpen(collapsed: list, key: string) -> boolean {
  return !(collapsed |> some(k => (k + '') == key))
}

fn gridVisibleDerivedRows(rows: list, collapsed: list) -> list {
  return rows |> filter(r => r._kind != null || r._group == null || gridDerivedIsOpen(collapsed, r._group))
}

fn gridRowRail(row: map) -> string {
  if row._accent != null { return 'inset 3px 0 0 ' + row._accent }
  return 'none'
}

fn gridRowOpacity(row: map) -> number {
  if row._opacity != null { return row._opacity }
  return 1.0
}

// True when the row set uses group/total rows. Sorting is suppressed for those
// grids: reordering would tear group headers away from their members.
fn gridHasStructuralRows(rows: list) -> boolean {
  return rows |> some(r => r._kind != null)
}

fn _applySortToRows(rows: list, sortState: list) -> list {
  if length(sortState) == 0 { return rows }
  if gridHasStructuralRows(rows) { return rows }
  return sort(rows, (a, b) => {
    for { key, direction } in sortState {
      let aVal = a[key]
      let bVal = b[key]
      let cmp = 0
      if aVal == null && bVal == null { cmp = 0 }
      else if aVal == null { cmp = 0 - 1 }
      else if bVal == null { cmp = 1 }
      else if typeOf(aVal) == 'number' && typeOf(bVal) == 'number' { cmp = aVal - bVal }
      else { cmp = localeCompare(toString(aVal), toString(bVal)) }
      if cmp != 0 { return direction == 'asc' ? cmp : 0 - cmp }
    }
    return 0
  })
}

fn _applyFilters(rows: list, filters: list) -> list {
  let activeFilters = filters |> filter(f => f.value != null && length(f.value) > 0)
  if length(activeFilters) == 0 { return rows }
  return rows |> filter(row => {
    for { key, value } in activeFilters {
      let val = row[key]
      if val == null { return false }
      if !(toString(val) |> toLowerCase() |> includes(value |> toLowerCase())) { return false }
    }
    return true
  })
}

// ─── Keyboard scope ─────────────────────────────────────────────────────────
// A key event that started inside a form control belongs to that control, not
// to the grid.
//
// `on key-down` is bound to the grid ROOT, so every keystroke anywhere inside
// reaches it — and the grid claims SPACE (toggle the focused row) and ctrl-A
// (select every row), preventDefaulting both. Inside a text field that means a
// space cannot be typed and ctrl-A cannot select the field's text.
//
// This has always applied to the column-filter inputs; the toolbar slot merely
// made it reachable for a caller's search box, which is what the slot is FOR.
fn gridKeyFromField(target: map) -> boolean {
  if target == null { return false }
  if target.isContentEditable == true { return true }
  let tag = target.tagName
  return tag == "INPUT" || tag == "TEXTAREA" || tag == "SELECT"
}

component DataGrid(
  columns: array,
  rows: array,
  selection: string = "none",
  selected: array = [],
  sort: array = [],
  height: string = "",
  striped: boolean = false,
  // The tint an odd row takes when `striped`. Defaulted to semantic.surface,
  // which is what shipped before — but on a surface-coloured container that
  // resolves to the SAME colour as the unstriped rows, so `striped: true` could
  // not produce a visible stripe at any setting. A caller on a white card needs
  // to name a tint a shade off it.
  stripeBackground: string = "",
  // Row hover. Empty keeps the previous behaviour: none at all, which on a grid
  // whose rows are clickable left nothing to say a row was a target.
  hoverBackground: string = "",
  // Cell padding, for callers whose design system is denser or looser than
  // spacing.2. Applies to every cell in every row so the columns cannot drift.
  cellPadding: string = "",
  // Header-only padding. Empty = cellPadding. A blotter header is denser than
  // its rows (the mockup precedent: ~half the vertical padding), and with a
  // grouped run the label strip and the member row EACH pay it, so a header
  // stuck at cell padding is a third taller than designed.
  headerPadding: string = "",
  // Full-height rules bracketing each labelled group run, drawn on the header
  // segment AND on every body cell at a run's edge — without the body half the
  // grouping dissolves below the header. Opt-in: existing grouped consumers
  // keep their rendering.
  groupRules: boolean = false,
  // A rule between EVERY pair of columns, not just at a group's edges — the
  // blotter treatment, where a dense table of figures reads as a grid rather
  // than as rows of floating numbers.
  //
  // Opt-in, and deliberately separate from `groupRules`: this draws the same
  // 1px `bracketRule`, so with both on the group's own right edge would sit
  // adjacent to the next column's left edge and paint 2px. When columnRules is
  // on it therefore SUPPRESSES the group's right rule — the left rules already
  // delineate every run, and the spanning label is what names it.
  //
  // The leftmost visible column gets no left rule: it would land on the card's
  // own edge.
  columnRules: boolean = false,
  // Freeze the first visible column horizontally. It renders outside the column
  // loop because `position` is resolved at parse time and cannot vary per column.
  pinFirst: boolean = false,
  // Keys of the `_kind: 'group'` rows that start expanded.
  defaultOpen: array = [],
  // Opaque backing for the pinned column (it must not let rows scroll under it).
  // Empty = the default surface token, resolved at the use site: a token cannot
  // be a prop default.
  pinBackground: string = "",
  // Backing for group / total rows. Empty = the platform's raised surface;
  // `semantic.surface-sunken` is not a platform token, so it cannot be assumed.
  groupBackground: string = "",
  // Row detail. `expandable: false` keeps 0.4.0 rendering exactly — no detail
  // row, no toggle. When true, a full-width `detail` slot renders beneath any
  // row whose `rowKeyField` value is in the expanded set, and clicking a row
  // toggles it. The open set is the grid's own state, mirroring `openGroups`:
  // a caller cannot own it without re-implementing the row loop.
  expandable: boolean = false,
  defaultExpanded: array = [],
  rowKeyField: string = "id",
  // The grid's own frame. True keeps what every consumer renders today: a
  // 1px border at radius.md around the whole grid.
  //
  // A grid mounted inside a card that already draws a frame needs this OFF, or
  // the two frames stack — same border colour, different radii, 1px apart,
  // which reads as a rendering fault rather than a design. Measured on cf's
  // Deals list inside the shell's TableCard: 1px/8px nested in 1px/12px.
  //
  // This turns off the BORDER only. `overflow: hidden` stays either way: it is
  // not chrome, it is what keeps the sticky header and the horizontal scroller
  // inside the grid, and dropping it would let rows escape their card at
  // narrow widths.
  bordered: boolean = true,
  // Whether an ordinary row is a click target, for the cursor only.
  //
  // The row cursor used to key off `selection != "none"`, which misses the
  // commonest case there is: a master-detail list that navigates on `rowClick`
  // and enables no selection at all. Every row is a target and every row
  // renders the default arrow.
  //
  // The grid cannot infer this. There is no `hasListener()` in the language —
  // only `hasSlot()` — so a consumer that binds `on rowClick` is
  // indistinguishable from one that does not, and it has to say so.
  //
  // Ordinary rows only, matching `hoverBackground`: a group header or a total
  // is not a navigation target, and pointing at one would claim it was.
  rowsClickable: boolean = false,
  // Controlled sorting. When true the grid never reorders rows itself: header
  // clicks still toggle sortState (so the indicator moves) and still emit
  // `sort`, but the rows render exactly as given — the CALLER sorts. This is
  // what server-side (or paginated) sorting needs: a grid that sorts its own
  // page slice reorders ten rows and calls it a sort, while the real order
  // lives in the full set the caller holds. False preserves today's behaviour
  // for every existing consumer.
  externalSort: boolean = false,
  // The filter twin of externalSort, and needed for the same reason. The header
  // still opens its popover, still tracks filter state and still emits
  // `filter`; the grid just stops applying the predicate.
  //
  // A server-paginated caller re-queries its FULL dataset when a filter
  // changes. A grid that instead filters the page slice it happens to hold
  // returns a subset of a subset — and does it silently, because rows come
  // back either way. False preserves today's behaviour for every consumer.
  externalFilter: boolean = false,
  // The square size of the grid's own row controls (the group-collapse caret
  // and the row-detail expand caret), px. 22 was hard-coded; at dense blotter
  // type it read as a speck. The glyph scales with the box.
  controlSize: number = 22,
  // WHAT opens a row's detail.
  //
  //   'row'     — clicking anywhere on the row toggles it. The 0.9.0 behaviour,
  //               and the default, so no existing consumer moves.
  //   'control' — the row click no longer toggles; the grid renders its own
  //               caret and only that caret toggles.
  //
  // 'control' exists because 'row' and a NAVIGATING `rowClick` are mutually
  // exclusive, silently. The row handler fires `clickRow` (which emits
  // `rowClick`) and `toggleExpanded` unconditionally, so a consumer that routes
  // `rowClick` to a page navigation toggles the detail open and then throws it
  // away in the same gesture — the detail row is unreachable and nothing
  // errors. cf's market blotter is exactly that consumer: the row opens a
  // listing, and the caret opens the quality spec in place.
  expandTrigger: string = "row",
  // Which column hosts the caret. Empty = the first visible column, which is
  // the pinned one when `pinFirst` is set.
  expandColumn: string = "",
  // Column drag-to-reorder. Off by default: a grid whose caller does not
  // handle columnOrderChange must not show a grab cursor on a column that
  // will not move.
  reorderableColumns: boolean = false,
  // Caller-owned column order, as a list of column keys. [] = the grid owns
  // its own order, seeded from `columns`. Mirrors externalSort's position:
  // the real state lives with the caller, who persists it.
  columnOrder: array = [],
  // Keys to hide, ANDed with each column's own `visible`. Caller-owned and
  // persisted exactly like columnOrder, and mirrored locally for the same
  // reason: a hide must paint before the round-trip returns.
  hiddenColumns: array = [],
  // Mount the column chooser in a strip above the header. Off by default — a
  // grid whose caller does not handle the two events must not offer controls
  // that appear to do nothing.
  configurableColumns: boolean = false,

  // ─── P4: the three states a fetching grid needs ───────────────────────────
  // Fetching the FIRST page. This also fixes a latent bug: the empty state was
  // gated on "no rows" and nothing else, so a grid that was still loading
  // rendered "No rows" at the user while the data was in flight.
  loading: boolean = false,
  // More rows exist beyond the ones given. Renders one Load more control; the
  // grid never fetches, it asks.
  hasMore: boolean = false,
  emptyText: string = "No rows",

  // ─── P5: derived row grouping ─────────────────────────────────────────────
  // Group rows by a FIELD, rather than by the caller injecting `_kind: 'group'`
  // rows itself. Setting this selects the derived path; leaving it empty is
  // today's structural behaviour, untouched.
  //
  // The two models differ in who owns collapse AND in polarity — structural is
  // grid-owned and lists what is OPEN, derived is caller-owned and lists what
  // is CLOSED — so they do not merge. Derived wins when both are present.
  groupBy: string = "",
  // Caller-supplied counts per group value, for a paginated grid where the
  // rows present are a fraction of the group. Falls back to counting the rows
  // that are here. Keys are matched as strings, so a numeric-keyed map works.
  groupCounts: object = {},
  // Group values that are CLOSED. Everything else is open.
  collapsedGroups: array = [],

  // ─── P6: parity oddments ──────────────────────────────────────────────────
  // Stamped as data-testid on every body row. "" stamps nothing at all.
  rowTestId: string = "",
  // The header pins to the scroll container by default. Vector's DataTable
  // carries a comment claiming a dynamic `position:` compiles to `static`;
  // that was fixed (ast-to-ir.ts routes positionExpr through buildExprStyle),
  // so this really is one binding.
  stickyHeader: boolean = true,

  // ─── Windowed rendering ───────────────────────────────────────────────────
  // Active iff rowHeight > 0 AND rowCount > 0. Every default below reproduces
  // the previous behaviour exactly, so no existing consumer changes.
  //
  // `rows` is IGNORED while windowing is active: the block cache is the sole
  // source and block 0 is fetched like any other. A caller passing its first
  // page through `rows` and the rest through blocks would have two sources
  // that disagree the moment a filter changed.
  rowCount: number = 0,
  rowHeight: number = 0,
  blockSize: number = 100,
  overscan: number = 5,
  // Bumped by the caller to drop the cache — needed because the grid cannot
  // see a filter control that lives outside it.
  dataVersion: number = 0,
  // The shape a not-yet-arrived row takes. "avatar" is SkeletonRow — a 38px
  // circle, two stacked lines and a pill — which is right for a list of people
  // and reads as a PERSON in a dense table of figures. "bar" is a single
  // shimmer line at the row's own height, for numeric grids.
  //
  // Defaulted to "avatar" so all 16 existing consumers render byte-identically;
  // anything other than "bar" is the avatar, so a typo degrades to today's
  // behaviour rather than to a blank row.
  skeletonVariant: string = "avatar",

  // ─── The second step of select-all ────────────────────────────────────────
  // Selection over a window cannot enumerate keys it has not fetched, so "all"
  // becomes a PREDICATE: everything matching the current sort/filter, minus
  // `excludedKeys`. Both live with the caller — only the caller can turn a
  // predicate into rows — so the grid emits `selectAllMatchingChange` and reads
  // the answer back through these props.
  //
  // `selected` keeps its existing meaning untouched: a list of row KEYS, which
  // is what all 16 consumers pass and what `selectionChange` still carries.
  selectAllMatching: boolean = false,
  excludedKeys: array = [],
) {
  @state {
    // Per-instance id, so two grids on one page never share a drag session.
    // Generated once at mount — @state initialisers do not re-run.
    _gridId: genGridId()
    // Live column order. Seeded from the prop; replaced on drop and re-seeded
    // by the @watch below when the caller supplies a new one.
    _colOrder: columnOrder
    // Live hidden set, same shape and same reasons as _colOrder.
    _hidden: hiddenColumns
    // Returns a teardown fn. Declared after _gridId (it reads it) and after
    // the action it calls back into.
    // `allKeysOf` is an ACTION, not the @computed it returns, so the read is
    // taken per use and stays fresh rather than being captured at mount.
    // `() => reorderableColumns` is a THUNK on purpose: the affordance arms and
    // disarms when the prop flips after mount, so the wire needs a live read,
    // and a @state initialiser is a one-shot snapshot. This used to be spelled
    // as the bare `reorderableColumns` and worked only because the compiler
    // mis-lowered a @state initialiser's references into the signal itself
    // (spec#164); the thunk says the same thing deliberately.
    _colDragTeardown: wireColumnDrag(_gridId, onColumnDragReorder, () => reorderableColumns, allKeysOf)
    // The same drag, one level up: a labelled group's header cell moves the
    // whole run among its sibling segments. Without it a group is the one
    // thing on the grid that cannot be moved, because a group IS a segment and
    // the column wire never crosses one.
    _groupDragTeardown: wireGroupDrag(_gridId, onColumnDragReorder, () => reorderableColumns, allKeysOf)
    sortState: sort
    selectedSet: selected
    filters: []
    // -1 = nothing focused yet. Starting at 0,0 painted a focus tint on the
    // first cell of every freshly-rendered grid, which reads as a selection the
    // user did not make. Arrow-key navigation moves off -1 on the first press.
    focusedRow: 0 - 1
    focusedCol: 0 - 1
    openGroups: defaultOpen
    expandedSet: defaultExpanded
    // Which row the pointer is over, for the PINNED column's hover paint. The
    // row container's own `on hover {}` style cannot reach the pinned cell:
    // that cell is sticky with an opaque `pinBg` painted OVER the row, so with
    // `hoverBackground` set the row lit up while its pinned cell stayed
    // opaque — the one column guaranteed on screen was the one column that
    // ignored the hover. -1 = none.
    hoveredRow: 0 - 1
    // ─── The windowed render state ──────────────────────────────────────────
    // Pushed WHOLESALE by wireGridWindow through applyWindow. The grid never
    // reads the block cache itself, so there is no reactivity bridge to get
    // wrong: what is here is what renders.
    winRows: []
    winFailed: []
    winStart: 0
    winEnd: 0
    // The first ON-SCREEN slot of the window, measured by the wire. See
    // WindowState.firstVisible — it is neither 0 nor `overscan`, because the
    // sticky header covers the row aligned to scrollTop.
    winFirstVisible: 0
    padTopPx: 0
    padBotPx: 0
  }

  @watch {
    // A caller recomputing its group set (paging, filtering) re-seeds the open
    // state. Without this the seed happened once at mount, so a group that
    // first APPEARED after mount was absent from openGroups and rendered
    // permanently collapsed — its members looked like missing data. Static
    // defaultOpen (every pre-existing consumer) never fires this.
    defaultOpen: {
      openGroups = defaultOpen
    }
    // hoveredRow is an INDEX; when the rows under a stationary pointer change
    // (sort toggle, page change, refresh) the index would name a different
    // row and paint the wrong pinned cell as hovered. mouse-enter re-fires on
    // real movement, so clearing on data change is always safe.
    processedRows: {
      hoveredRow = 0 - 1
    }
    // ...and the windowed half of the same rule. `processedRows` derives from
    // the `rows` prop, which windowed mode IGNORES — so in a windowed grid the
    // watch above is a constant and never fires, while a block landing swaps
    // every row in the window under a stationary pointer. That is the ordinary
    // case during a scroll, not an edge case, and it leaves the highlight on a
    // row the pointer is no longer over. Invisible to every unwindowed test,
    // because there the watch above already covers it.
    //
    // `winRows` and not `padTopPx`/`winStart`: those change when the window
    // MOVES, and a block landing under a stationary pointer moves nothing.
    winRows: {
      hoveredRow = 0 - 1
    }
    // A caller that persists the order and feeds it back re-seeds here.
    // Without this the seed happens once at mount and never again — the exact
    // shape of the sort-indicator bug recorded at market-page.spec:601, where
    // a narrowed prop moved the header while the grid kept ordering by stale
    // state.
    columnOrder: {
      _colOrder = columnOrder
    }
    // Same seed-once hazard as columnOrder: a caller that persists the hidden
    // set and feeds it back needs the grid to re-read it.
    hiddenColumns: {
      _hidden = hiddenColumns
    }
    // P6.1. `sortState` seeded ONCE at mount and never again, so a caller
    // narrowing or replacing `sort` moved the header arrow while the grid went
    // on ordering rows by its stale state — a sort indicator naming a column
    // the rows are not ordered by. Recorded live at market-page.spec:601, and
    // worked around there by mounting two grids and letting the incoming one
    // re-seed; that workaround can now go.
    //
    // This CHANGES BEHAVIOUR for every existing consumer that mutates `sort`
    // after mount, which is why it is its own commit rather than part of the
    // parity batch. A consumer that never touches `sort` sees nothing.
    sort: {
      sortState = sort
    }
    // The same seed-once hazard as sort/columnOrder/hiddenColumns, and the one
    // prop that got missed. Vector's pilots page does
    // `if !selectMode { selectedIds = [] }`, so leaving select mode cleared the
    // PAGE's array while the grid kept its own — and the bulk-actions bar is
    // gated on the grid's set, so it stayed on screen holding keys nothing on
    // the page still showed as selected.
    selected: {
      selectedSet = selected
    }
  }

  @computed {
    // The single chokepoint: pinnedColumns, scrollColumns, both segment lists
    // and every width derive from this and nothing else, so applying the order
    // here reorders the whole grid — header, body, groups and sizing together.
    visibleColumns: gridApplyColumnOrder(columns.filter(c => c.visible != false && !(_hidden |> includes(c.key))), _colOrder)
    // Every key the grid knows about, hidden included, in current order.
    //
    // The drag wire reads header CELLS and so sees only what is on screen;
    // without this a drag performed while a column was hidden emitted an order
    // that had silently dropped it, and showing the column again appended it at
    // the end — throwing away wherever the user had put it. cf had to work
    // around exactly this in market-column-order.js.
    orderedAllKeys: gridApplyColumnOrder(columns, _colOrder) |> map(c => c.key)
    // The chooser's view of the columns. NOT `columns` raw: with pinFirst the
    // first VISIBLE column is pinned by POSITION, so hiding or moving it would
    // silently re-pin a different one. It renders locked instead — the panel's
    // echo of the wire's "a segment of size 1 gets no affordance".
    pinnedKey: pinFirst && visibleColumns.length > 0 ? visibleColumns[0].key : ''
    chooserColumns: columns |> map(c => c.key == pinnedKey
      ? { key: c.key, label: c.label, group: c.group, hideable: false, movable: false }
      : c)
    // The caret only exists in 'control' mode, and only when there is a detail
    // to open at all. Named once so both cell render sites (pinned and
    // scrolling) test the same thing.
    hasExpandControl: expandable && expandTrigger == "control"
    // Resolved once rather than per cell: an empty `expandColumn` means the
    // first VISIBLE column, which is not necessarily `columns[0]`.
    expandColKey: expandColumn != "" ? expandColumn
      : (visibleColumns.length > 0 ? visibleColumns[0].key : "")
    // Either axis can be delegated to the caller, independently. Passing an
    // EMPTY list rather than branching to `rows` keeps one call shape, so the
    // two flags compose instead of multiplying into four branches.
    processedRows: applySortAndFilter(
      rows,
      externalSort ? [] : sortState,
      externalFilter ? [] : filters
    )
    // `groupBy` selects the model. The derived path builds the SAME
    // `_kind: 'group'` rows the structural path renders, so everything
    // downstream — the caret, the collapse, the group background — is the code
    // that already ships. One render path, two sources.
    isGrouped: groupBy != ""
    groupedRows: isGrouped ? gridDeriveGroupRows(processedRows, groupBy, groupCounts) : processedRows
    // Rows whose group is collapsed drop out; group headers and totals remain.
    displayRows: isGrouped
      ? gridVisibleDerivedRows(groupedRows, collapsedGroups)
      : gridVisibleRows(processedRows, openGroups)
    // P4 states. The empty text renders only when there is nothing to show AND
    // nothing on its way — the condition the old empty state was missing.
    // Declared HERE, above its first consumer, not down with the other window
    // computeds: @computed evaluates in declaration order and a forward
    // reference throws at runtime, rendering the whole grid blank. It depends
    // only on props, so it is free to sit anywhere above its readers.
    windowed: rowHeight > 0 && rowCount > 0

    // ─── The loud refusal ───────────────────────────────────────────────────
    // Four prop combinations cannot be windowed, and every one of them fails
    // SILENTLY if it is merely tolerated: groupBy and expandable give rows no
    // fixed pitch, so the spacers stand in for a height the rows do not have
    // and the scrollbar lies; a client sort or filter over a window orders or
    // matches only the rows the client happens to hold, which is green against
    // any fully-loaded fixture and wrong against every real one.
    //
    // Rendered IN PLACE of the grid, and not dev-only: a developer error that
    // renders normally in production is one nobody ever sees. Each message
    // names BOTH props — the offending one and `rowHeight`, which is what
    // turned windowing on — because the fix is always to drop one of the two.
    //
    // Declared here, immediately below `windowed`: @computed evaluates in
    // DECLARATION ORDER and a forward reference throws at mount, blanking the
    // whole grid. Everything else read here is a prop.
    guardMsg: !windowed ? ""
      : (groupBy != "" ? "DataGrid: rowHeight cannot be combined with groupBy - grouped rows have no fixed pitch, so a window cannot be sized."
      : (expandable ? "DataGrid: rowHeight cannot be combined with expandable - an open detail panel has no fixed pitch, so a window cannot be sized."
      : (!externalSort ? "DataGrid: rowHeight (windowed mode) requires externalSort - a client sort would order only the rows currently loaded."
      : (!externalFilter ? "DataGrid: rowHeight (windowed mode) requires externalFilter - a client filter would match only the rows currently loaded."
      // Measured in a browser, 2026-08-13: without `height` the scroll
      // container is unbounded, so clientHeight == scrollHeight, the window
      // spans every row, and the grid renders all 1,043 of them. Windowing is
      // silently inert - exactly the freeze this feature exists to prevent.
      // Wrapping the grid in a fixed-height parent is NOT enough; `height` is
      // the mechanism, because it is what sets the scroller's max-height.
      // Invisible to every happy-dom test, where clientHeight is 0 regardless.
      : (height == "" ? "DataGrid: rowHeight (windowed mode) requires height - an unbounded scroll container renders every row, so windowing does nothing."
      : "")))))
    guarded: guardMsg != ""

    // `!windowed` because windowed mode ignores the `rows` prop, leaving
    // displayRows permanently empty — so without this the empty state and the
    // first-load skeletons render UNDERNEATH every populated windowed grid.
    // `windowed` is itself `rowHeight > 0 && rowCount > 0`, so a windowed grid
    // always has rows by definition; rowCount 0 makes windowed false and falls
    // through to the check below, which is what still reports a genuinely
    // empty result.
    isEmpty: !loading && !windowed && displayRows.length == 0
    isFirstLoad: loading && !windowed && displayRows.length == 0
    // "" must stamp NO attribute; a binding removes one only for null.
    rowTestIdAttr: rowTestId != "" ? rowTestId : null
    headerPosition: stickyHeader ? "sticky" : "static"
    // Each column carries its resolved min/max width. `min-width:` will not
    // parse a function call, so the sizes are computed here, once, and read as
    // plain member access at the use site — which also keeps every row reading
    // the SAME width source. `_col` is the caller's original column def, passed
    // untouched to the slots so caller-defined fields survive.
    // Pinned and scrolling columns are sized (and edge-flagged) over the SAME
    // pin-split lists the header segments use — gridSegmentsOf never lets a
    // run straddle the pin boundary, so the body's _gFirst/_gLast must treat
    // that boundary as a run edge too, or header and body disagree about
    // where the groupRules bracket falls.
    // Which column is leftmost ON SCREEN, by key. columnRules skips it, and a
    // key is the only handle available in all four cell sites — the two header
    // loops run inside a segment (`each seg._cols`) where the column's global
    // position is not in scope.
    //
    // Declared HERE, above the widths, because they now read it: an entry that
    // reads a later one in this block is the cascade-staleness trap, not a
    // forward reference the compiler resolves.
    firstColKey: visibleColumns.length > 0 ? visibleColumns[0].key : ''
    pinnedColumns: pinFirst ? gridSizedCols(visibleColumns.slice(0, 1), visibleColumns) : []
    scrollColumns: pinFirst ? gridSizedCols(visibleColumns.slice(1), visibleColumns) : gridSizedCols(visibleColumns, visibleColumns)
    trackMin: gridTrackMin(visibleColumns, columnRules, firstColKey)
    // Header segments. The pinned column renders outside the scrolling loop, so
    // a segment may never straddle that boundary — with pinFirst the first
    // column is segmented on its own. `_cols` sizes each segment's members from
    // the same fns as the body, so the two cannot disagree about widths.
    pinnedSegments: pinFirst ? gridSegmentsOf(visibleColumns.slice(0, 1)) : []
    scrollSegments: pinFirst ? gridSegmentsOf(visibleColumns.slice(1)) : gridSegmentsOf(visibleColumns)
    // Column-drag segment identity, per side. See gridSegRunIds: a run id, not
    // the group label — a label would merge ungrouped columns lying on
    // opposite sides of a group into one NON-CONTIGUOUS segment.
    pinnedSegRuns: gridSegRunIds(pinnedSegments)
    scrollSegRuns: gridSegRunIds(scrollSegments)
    // `_solo` and the two `_solo*` fields are precomputed here because a style
    // binding will not parse a function call — the same reason the widths are
    // resolved in this block rather than at the use site. `_segId` is here for
    // the same reason: it is read by an attribute binding.
    sizedPinnedSegments: pinnedSegments |> map((s, i) => { _seg: s, _min: gridSegMin(s, columnRules, firstColKey), _max: gridSegMax(s, columnRules, firstColKey), _cols: gridSizedCols(s.cols, visibleColumns),
      _segId: 'p:' + (pinnedSegRuns[i] + ''),
      _solo: gridGroupSize(visibleColumns, s.label) == 1,
      _soloSortable: gridGroupSize(visibleColumns, s.label) == 1 && s.cols[0].sortable == true,
      _soloKey: gridGroupSize(visibleColumns, s.label) == 1 ? s.cols[0].key : '' })
    sizedScrollSegments: scrollSegments |> map((s, i) => { _seg: s, _min: gridSegMin(s, columnRules, firstColKey), _max: gridSegMax(s, columnRules, firstColKey), _cols: gridSizedCols(s.cols, visibleColumns),
      _segId: 's:' + (scrollSegRuns[i] + ''),
      _solo: gridGroupSize(visibleColumns, s.label) == 1,
      _soloSortable: gridGroupSize(visibleColumns, s.label) == 1 && s.cols[0].sortable == true,
      _soloKey: gridGroupSize(visibleColumns, s.label) == 1 ? s.cols[0].key : '' })
    pinBg: pinBackground != "" ? pinBackground : semantic.surface
    groupBg: groupBackground != "" ? groupBackground : semantic.surface-raised
    stripeBg: stripeBackground != "" ? stripeBackground : semantic.surface
    pad: cellPadding != "" ? cellPadding : spacing.2
    // `pad`'s horizontal component, for the placeholder rows — see gridPadX.
    padX: gridPadX(pad)
    headerPad: headerPadding != "" ? headerPadding : pad
    // The group bracket, as a ready border string: a `borders.*` token cannot
    // be picked by a ternary in a style position on every target, but a plain
    // string can.
    bracketRule: '1px solid ' + semantic.border
    hasHover: hoverBackground != ""
    // The grid's own control buttons (group + expand carets), sized once.
    ctrlPx: controlSize + 'px'
    ctrlFont: ((controlSize * 6) / 10) + 'px'
    // `height` bounds the grid so its body scrolls internally (sticky header +
    // always-visible horizontal scrollbar); '' = grow to content, no bound.
    gridMaxH: height != "" ? height : "none"
    hasFilters: columns.some(c => c.filterable == true)
    // Selection identity is the row KEY, never the index. An index means a
    // different row the moment the grid re-sorts, filters or takes its next
    // page — and this grid does all three — so an index-keyed selection goes
    // wrong silently, with the checkboxes still looking right.
    //
    // `displayRows` is also the wrong denominator: it carries group-header
    // rows, which have no key and can never be selected, so the old
    // count-comparison could not reach true on ANY grouped grid.
    //
    // The definition itself moved BELOW `renderRows` — see the note there.

    // ─── Windowed rendering ─────────────────────────────────────────────────
    // Windowing is opt-in by ARITHMETIC, not by a flag: a consumer that passes
    // neither prop keeps every byte of its previous rendering.
    padTop: padTopPx + 'px'
    padBot: padBotPx + 'px'
    // The pitch a placeholder row has to hold. A skeleton or a failed-block row
    // that sized itself to its content would make the rendered rows a different
    // height from the ones the spacers are standing in for, and the scrollbar
    // would then lie by exactly the difference.
    rowHeightPx: rowHeight + 'px'
    // `isFirstLoad` is `!windowed`, and an unwindowed grid usually leaves
    // `rowHeight` at its 0 default — so `rowHeightPx` is "0px" on the one path
    // the first-load placeholder ever renders. The avatar branch is unaffected
    // (SkeletonRow brings its own height); a bare SkeletonLine collapses, and
    // six of them overlap inside a gap'd column. 38px matches SkeletonRow.
    // The first-load placeholder's height. NOT `rowHeightPx`: `isFirstLoad`
    // requires `!windowed`, and an unwindowed grid's loaded rows are
    // `height: auto`, so a declared rowHeight describes nothing that will
    // actually render — including the legal `rowHeight: 30, rowCount: 0`, which
    // is unwindowed WITH a pitch. SkeletonRow's own height is the honest
    // stand-in for both branches, since the avatar branch is literally that.
    skelRowPx: SKELETON_ROW_HEIGHT()
    // The live region's whole content. Empty when nothing is failed, so the
    // change from '' to a sentence is the mutation a reader announces on.
    failureAnnouncement: gridAnyFailed(winFailed) ? 'Some rows could not be loaded. Use the Retry button in the grid to try again.' : ''
    // The windowed loop's collection. A row the cache has not delivered yet
    // arrives as null, and a null cannot go through the row template: the
    // template reads row[rowKeyField], row._kind and row._toggleLabel, and
    // `visibility:` compiles to bindVisibility on the block WITHOUT deferring
    // the block's own bindings — only a component mount is deferred. So the
    // null is replaced by a sentinel here, and the gate reads that sentinel
    // off the very object the loop is iterating rather than off a parallel
    // array that could be one recompute behind it.
    winDisplayRows: winRows |> map(r => r != null ? r : { _unloaded: true })
    // ONE body renders both modes. winDisplayRows already carries an
    // `_unloaded` sentinel OBJECT rather than null, so the shared body never
    // sees a null row. Two bodies would be ~330 duplicated lines inside one
    // file, free to drift exactly the way CfDealTab drifted from Tabs — and
    // check-kit-duplication cannot see it, because it compares ACROSS files.
    renderRows: windowed ? winDisplayRows : displayRows

    // ─── Selection identity ─────────────────────────────────────────────────
    // Declared HERE rather than up with the other selection computeds because
    // it reads `renderRows`, and @computed evaluates in DECLARATION ORDER: a
    // forward reference throws at mount and blanks the whole grid.
    //
    // `renderRows`, not `displayRows`. Windowed mode ignores the `rows` prop,
    // so `displayRows` is permanently empty there — which made the header
    // checkbox on a windowed grid emit `[]`, never tick, and leave `allSelected`
    // unable to reach true no matter how many rows were on screen. Measured:
    // five delivered rows, five ticked-able boxes, zero keys emitted. Unwindowed
    // `renderRows` IS `displayRows`, so nothing moves for the 16 consumers.
    //
    // `_unloaded` rows are excluded for the same reason group headers are: a
    // sentinel has no `rowKeyField`, so sweeping one in would put an undefined
    // into `selectionChange`. It is also what keeps `allSelected` honest — a
    // window half-filled with skeletons is not "all selected".
    selectableKeys: renderRows
      |> filter(r => gridRowKind(r) == "row" && r._unloaded != true)
      |> map(r => r[rowKeyField])
    allSelected: selectableKeys.length > 0 && selectableKeys.every(k => selectedSet.includes(k))

    // What keyboard navigation walks. Windowed, that is every row in the grid
    // — `displayRows` is empty there, which is what made arrow keys inert.
    navRowCount: windowed ? rowCount : displayRows.length

    // ─── The two-step select-all ────────────────────────────────────────────
    // What a bulk action needs to know, and what `selectedSet` alone cannot
    // say: in predicate mode the grid holds a handful of keys and the caller
    // means 1041 rows. A consumer reading `sel.length` would report the
    // handful.
    selectionSummary: { mode: selectAllMatching ? 'allMatching' : 'some', count: selectAllMatching ? rowCount - excludedKeys.length : selectedSet.length, excludedKeys: excludedKeys }
    // Offered only once every LOADED row is selected — before that the ordinary
    // checkbox is still the more likely intent. `!selectAllMatching` because
    // re-offering a mode already in force is a control that does nothing;
    // `!guarded` because a refused grid renders its diagnostic and nothing
    // else, exactly like its four sibling blocks.
    offerAllMatching: windowed && allSelected && !selectAllMatching && !guarded
    allMatchingLabel: 'Select all ' + toString(rowCount) + ' matching'
    // The wire lives HERE and not in @state, even though the other two wires
    // (wireColumnDrag / wireGroupDrag) are @state initialisers. It predates
    // spec#164, which fixed the @state-prop-ref trap this was avoiding: a
    // @state initialiser's references used to arrive as SIGNALS rather than
    // values, so `rowHeight > 0` there compared a function to a number and was
    // false forever. Both places read props as values now, so this could move —
    // but it does not need to, and a @computed is still the better home because
    // `windowed` should re-evaluate when its inputs change, which a one-shot
    // @state initialiser would not do.
    //
    // wireGridWindow is called with the DOM not yet built: the compiler emits
    // every @computed ABOVE the DOM section, and the mount function appends
    // its root to the container on its LAST line. So the wire cannot find its
    // scroll container synchronously and defers its own attach — see the note
    // in grid-window-wire.ts. Nothing here can fix that; a wire that queried
    // once and gave up would leave windowing silently inert.
    //
    // `&& !guarded` is part of the refusal, not decoration. A guarded grid
    // still stamps its data-grid-id and still contains a (hidden) scroll
    // container, so the wire attaches happily, measures a display:none element
    // as zero-height, and asks for block 0 regardless — making the caller
    // fetch a hundred rows to feed a cache that nothing on screen reads.
    _windowTeardown: windowed && !guarded
      ? wireGridWindow(_gridId, { rowHeight: rowHeight, overscan: overscan, blockSize: blockSize, rowCount: rowCount, stickyHeader: stickyHeader }, applyWindow, emitRangeNeeded)
      // NOT `null`. wireGridWindow destroys the previous wire for this id, so
      // the truthy arm cleans up after itself — but this arm is taken whenever
      // windowing switches OFF (a filter returning zero rows, a caller
      // enabling `expandable`), and it used to abandon the live wire with its
      // scroll listener, its ResizeObserver and its cache still registered.
      // The reaper cannot help: an unguarded grid keeps its scroll container
      // in the document, so the wire never looks detached.
      : releaseGridWindow(_gridId)

    // ─── What generation the held blocks describe ───────────────────────────
    // `rowCount` is the only change the wire could see for itself, and it is
    // not the only change that matters. Sorting is the airtight case: a
    // windowed grid REQUIRES externalSort, so a header click emits `sort`, the
    // caller refetches server-side, and the count is unchanged — every block
    // stayed `held` and the grid rendered the previous order forever. Filters
    // that happen to return the same count do the same thing, and `dataVersion`
    // was declared for a caller-side change the grid cannot see at all and was
    // read by NOTHING.
    //
    // Declared AFTER _windowTeardown because it needs the wire that computed
    // creates; the first key is adopted without invalidating.
    _windowGeneration: windowed && !guarded
      ? gridDataGeneration(_gridId, dataVersion, sortState, filters)
      : null
  }

  @actions {
    toggleGroup(key) {
      openGroups = gridToggleGroup(openGroups, key)
      emit("groupToggle", key)
    }
    // The control on a group row, routed to whichever model is active. In the
    // derived model the grid owns NOTHING: it emits the raw group value and
    // the caller decides, because `collapsedGroups` is the caller's state.
    toggleGroupRow(row) {
      if isGrouped {
        emit("groupToggle", row._groupValue)
      } else {
        toggleGroup(row._key)
      }
    }
    groupRowIsOpen(row) {
      if isGrouped { return gridDerivedIsOpen(collapsedGroups, row._group) }
      return gridGroupIsOpen(openGroups, row._key)
    }
    loadMore() {
      emit("loadMore")
    }
    // The active value of a column's filter, "" when none. Named once because
    // the option list tests it four times per option.
    filterValueOf(key) {
      let f = filters.find(x => x.key == key)
      if f == null { return "" }
      return f.value
    }
    // No emit(), unlike toggleGroup: nothing consumes an expansion event, and
    // an unused event is API surface that has to be kept working forever.
    toggleExpanded(row) {
      if !expandable { return }
      let k = row[rowKeyField]
      if k == null { return }
      expandedSet = gridToggleExpanded(expandedSet, k)
    }
    // The row's share of the toggle, gated on `expandTrigger`. Split out of the
    // row handler so 'control' mode can drop it without touching `clickRow` —
    // `rowClick` must keep firing in BOTH modes, because that is the consumer's
    // navigation and it is not what this prop is about.
    rowClickToggle(row) {
      if expandTrigger != "row" { return }
      toggleExpanded(row)
    }
    // The caret's toggle. `stopPropagation` is the whole reason this is its own
    // action: without it the click bubbles to the row container and fires
    // `clickRow`, so opening the quality spec would ALSO navigate away from the
    // page showing it — which is the exact bug 'control' mode exists to avoid.
    caretToggle(event, row) {
      event.stopPropagation()
      toggleExpanded(row)
    }
    // The row checkbox needs the same guard as the caret above, and for longer:
    // its click bubbled to the row container, so `clickRow` called `selectRow`
    // a SECOND time and untoggled what the checkbox had just toggled. In multi
    // mode the two cancelled and the box would not tick at all; in single mode
    // the second call was idempotent, which is why it looked like it worked.
    swallowRowClick(event) {
      event.stopPropagation()
    }
    toggleSortCol(colKey) {
      sortState = toggleSortState(sortState, colKey)
      emit("sort", sortState)
    }
    // Called by wireColumnDrag with the full key order after a completed drag.
    // The wire has already confined the move to one segment and spliced the
    // result back into the full order, so this is the caller's new order
    // verbatim — nothing to merge here.
    // Read back by the drag wire on every drop. See the note at the @state
    // declaration for why this is an action rather than the computed itself.
    allKeysOf() { return orderedAllKeys }
    onColumnDragReorder(nextKeys) {
      _colOrder = nextKeys
      emit("columnOrderChange", nextKeys)
    }
    // The chooser's visibility change. Local first, then the emit — the same
    // rule the order takes: making the grid wait for a round-trip to agree
    // with a gesture the user already completed is how a control comes to feel
    // like it snapped back.
    onChooserHidden(keys) {
      _hidden = keys
      emit("columnVisibilityChange", keys)
    }
    setFilter(colKey, value) {
      let existing = filters.find(f => f.key == colKey)
      if existing != null {
        if value == "" { filters = filters.filter(f => f.key != colKey) }
        else { filters = filters.map(f => f.key == colKey ? {key: colKey, value: value} : f) }
      } else {
        if value != "" { filters = filters.concat([{key: colKey, value: value}]) }
      }
      emit("filter", filters)
    }
    // Takes the ROW, not its index. A group-header row has no key, so the null
    // guard is what stops select-all-by-click sweeping one into the payload.
    selectRow(row) {
      let k = row != null ? row[rowKeyField] : null
      if k != null {
        // In predicate mode the selection is "everything matching, minus
        // these", so un-ticking a row EXCLUDES it. Editing `selectedSet` here
        // instead — which is what used to happen — changed a set the summary
        // does not read in this mode: the row went blank on screen while the
        // count stayed at rowCount, so a bulk delete still took the row the
        // user had just removed.
        if selectAllMatching {
          if excludedKeys.includes(k) {
            emit("excludedKeysChange", excludedKeys.filter(x => x != k))
          } else {
            emit("excludedKeysChange", excludedKeys.concat([k]))
          }
          return
        }
        if selection == "single" {
          selectedSet = [k]
          emit("selectionChange", [k])
        } else {
          if selection == "multi" {
            if selectedSet.includes(k) { selectedSet = selectedSet.filter(x => x != k) }
            else { selectedSet = selectedSet.concat([k]) }
            emit("selectionChange", selectedSet)
          }
        }
      }
    }
    // `selectableKeys` excludes group headers and reads `renderRows` — so
    // select-all takes what the user can actually see, not the rows hidden
    // inside a collapsed group.
    //
    // It used to read `displayRows`, which was the WHOLE list, and replacing
    // `selectedSet` with it was right. Task 6b re-pointed it at `renderRows`;
    // in windowed mode that is only the ~25 rows on screen, so replacing
    // became silent data loss — tick the header at the top, scroll, tick
    // again, and the first window's keys were gone from the payload the caller
    // acts on. Unwindowed, `renderRows` IS `displayRows`, so the union is
    // identical to the replacement and the 16 existing consumers do not move.
    selectAllRows() {
      selectedSet = windowed ? gridUnionKeys(selectedSet, selectableKeys) : selectableKeys
      emit("selectionChange", selectedSet)
    }
    // The inverse of the above, and only the inverse: un-ticking the header of
    // a windowed grid drops the rows on screen, not a selection the user built
    // up over four other windows.
    deselectRenderedRows() {
      selectedSet = selectedSet.filter(k => !selectableKeys.includes(k))
      emit("selectionChange", selectedSet)
    }
    // Leaves predicate mode as well as emptying the set — otherwise "clear"
    // clears what is on screen and the caller still believes 1043 are chosen.
    exitAllMatching() {
      emit("selectAllMatchingChange", false)
      emit("excludedKeysChange", [])
      clearSelection()
    }
    clearSelection() {
      selectedSet = []
      emit("selectionChange", [])
    }
    // Retry CLEARS THE MARK ITSELF, then tells the caller. Emitting alone left
    // the block latched failed unless the caller called retryBlock by hand —
    // an undocumented second step no consumer performed — so the click swapped
    // an actionable error row for a permanent skeleton. Clearing it here makes
    // the wire ask again through the ordinary rangeNeeded path, which every
    // caller already answers; `blockRetry` stays for observability, and is now
    // a notification rather than a contract the grid depends on.
    retryFailedBlock(b) {
      retryBlock(_gridId, b)
      emit("blockRetry", b)
    }
    clickRow(row, idx) {
      // A row that has not arrived is not a row. `winDisplayRows` substitutes
      // an `{ _unloaded: true }` sentinel, and a consumer navigating on
      // `rowClick` would open `row.id === undefined` — cf does exactly that.
      //
      // Not currently reachable by a user: this handler lives on the block
      // gated by `visibility: row._unloaded != true`, which compiles to
      // display:none, and a display:none element receives no pointer events.
      // Verified in Chrome — in stall mode, elementFromPoint at a skeleton's
      // centre lands outside any clickable row and a real click there emits
      // nothing. The guard is here so that safety stops depending on a CSS
      // side effect: swap `visibility:` for an opacity or a pointer-events
      // rule, or reach this programmatically, and the sentinel would go out.
      if row._unloaded == true { return }
      selectRow(row)
      emit("rowClick", row, idx)
    }
    // ─── Keyboard navigation spans the WHOLE grid, not the window ───────────
    // `focusedRow` is an absolute index (the render has compared it against
    // gridAbsIdx since Task 7), but the movement was still bounded by
    // `displayRows.length` — which windowed mode leaves EMPTY, so `moveDown`
    // evaluated `-1 < -1`, false, and focus never moved at all. The grid
    // supplies role="grid", tabindex="0" and this handler itself, so every
    // windowed consumer inherited a focusable grid whose arrow keys were dead.
    //
    // `navRowCount` is the length of the thing being navigated: every row in
    // windowed mode, only what is displayed otherwise.
    moveUp()    { if focusedRow > 0 { focusedRow = focusedRow - 1  revealFocusedRow() } }
    // From "nothing focused", the first Down/Right press lands on the first cell.
    moveDown()  { if focusedRow < 0 { focusedRow = gridFirstFocus(windowed, winStart)  if focusedCol < 0 { focusedCol = 0 }  revealFocusedRow() } else { if focusedRow < navRowCount - 1 { focusedRow = focusedRow + 1  if focusedCol < 0 { focusedCol = 0 }  revealFocusedRow() } } }
    moveLeft()  { if focusedCol > 0 { focusedCol = focusedCol - 1 } }
    // Both entry points from "nothing focused" seed from the TOP OF THE
    // WINDOW, not row 0. After a mouse scroll to row 500, seeding 0 made the
    // first ArrowDown yank the list back to the very top; and moveRight seeded
    // 0 without revealing at all, putting focus on an off-screen row with no
    // scroll — the vanishing highlight this task set out to remove, in a
    // different key.
    moveRight() { if focusedCol < visibleColumns.length - 1 { focusedCol = focusedCol + 1  if focusedRow < 0 { focusedRow = gridFirstFocus(windowed, winStart)  revealFocusedRow() } } }
    // Arrowing off the edge of the window has to move the WINDOW. Without
    // this, focus walks into rows that are not rendered and the highlight
    // simply vanishes — the grid looks broken rather than scrolled.
    // No-op when unwindowed, and when the row is already on screen.
    revealFocusedRow() {
      if windowed { gridScrollRowIntoView(_gridId, focusedRow, rowHeight) }
    }
    selectFocused() {
      if focusedRow >= 0 {
        selectRow(gridFocusedRow(windowed, renderRows, displayRows, winStart, focusedRow))
      }
    }

    // Called by wireGridWindow with a COMPLETE render state. Values arrive as
    // arguments and are never read back out of a @computed here: an action
    // called from a computed sees other computeds one cascade position stale.
    applyWindow(s) {
      winRows = s.rows
      winFailed = s.failed
      winStart = s.start
      winEnd = s.end
      winFirstVisible = s.firstVisible
      padTopPx = s.topPad
      padBotPx = s.botPad
    }
    emitRangeNeeded(reqs) {
      emit("rangeNeeded", reqs)
    }
  }

  block {
    // See `bordered`. `overflow: hidden` is deliberately NOT conditional —
    // it is the grid's clip, not its chrome.
    border: bordered ? borders.default : 'none'
    border-radius: bordered ? radius.md : '0'
    overflow: hidden
    role: "grid"
    tabindex: "0"
    data-grid-id: _gridId
    // The column-drag wire's re-arm trigger. It mounts once from a @state
    // initialiser that never re-runs, so a page that flips reorderableColumns
    // after mount (a permission or a setting resolving) has no other way to
    // tell it: a MutationObserver on this attribute is how plain DOM code
    // learns a Spec signal changed. The wire reads the live prop for the
    // VALUE, not this attribute — which is also why no @watch is needed here,
    // the binding itself is the reactive hook.
    data-grid-reorderable: reorderableColumns ? 'true' : 'false'

    on key-down(event): {
      if !gridKeyFromField(event.target) {
        match event.key {
          "ArrowDown"  -> moveDown(),
          "ArrowUp"    -> moveUp(),
          "ArrowRight" -> moveRight(),
          "ArrowLeft"  -> moveLeft(),
          " "          -> selectFocused(),
          _            -> {}
        }
        if event.key == "a" && event.ctrlKey == true && selection == "multi" {
          event.preventDefault()
          if allSelected { if windowed { deselectRenderedRows() } else { clearSelection() } } else { selectAllRows() }
        }
      }
    }

    // Caller-owned toolbar (search box, facet chips, view toggle), above the
    // grid's own chrome. Always rendered: an unprovided slot mounts nothing, so
    // this collapses to a zero-height container.
    //
    // Deliberately NOT gated on a hasSlot() check — that gate compiles
    // unreliably for parameterized slots, and a wrong gate here hides a toolbar
    // the caller did supply, which is a far worse failure than an empty div.
    //
    // ─── `!guarded` on this and its three siblings ─────────────────────────
    // A refused grid is REPLACED by its diagnostic, not annotated with one: a
    // banner above a grid that is still silently mis-sorting a window teaches
    // the reader to scroll past the banner. The four direct children of the
    // root are gated individually rather than wrapped in one `!guarded` block
    // because a wrapper would put a DOM level between this root and the scroll
    // container below — whose `height: 100%` resolves against its parent — and
    // that layout change would land on all 16 existing consumers to buy
    // nothing. Gated this way, an unguarded grid renders byte-identically.
    block {
      visibility: !guarded
      @slot("toolbar")
    }

    // ── THE FAILURE, ANNOUNCED ────────────────────────────────────────────
    // OUTSIDE `[data-grid-scroll]`, and permanently mounted. Three things went
    // wrong the first time it was written, all of them worth stating:
    //
    //  - Inside the scroller it was a sibling of the bottom spacer, so its text
    //    painted after ~30,000px of virtual padding — visible only by scrolling
    //    to the very end of the list, and lengthening scrollHeight while it was
    //    shown.
    //  - Gated with `visibility:` it announced by being UN-HIDDEN. Readers
    //    announce a content MUTATION inside a region that is already rendered;
    //    revealing a region whose text was always there typically says nothing.
    //    So the region is always present and its TEXT is what changes.
    //  - It must not be visible chrome: this grid's failure is already stated
    //    on screen by the message row. This is the same fact for a reader that
    //    cannot see it, hence the 1px clip rather than a second banner.
    //
    // Window-scoped on purpose: it says "there are unloadable rows in view",
    // so scrolling a failed block back into view saying so again is correct.
    block {
      position: "absolute"
      width: 1px
      height: 1px
      overflow: hidden
      role: "status"
      aria-live: "polite"
      data-grid-failed-announce: "true"
      text(failureAnnouncement)
    }

    // The column chooser, in a strip of the grid's own chrome. A page that
    // already has a toolbar should leave this off and mount ColumnChooser
    // itself — it is a registry component in its own right, and two Columns
    // buttons on one screen is worse than none.
    //
    // The handlers live INSIDE the braces: emit() never reaches an
    // `on <event>:` written outside them, and the dangling form compiles to a
    // listener that never fires.
    block {
      visibility: configurableColumns && !guarded
      layout: horizontal, justify: end
      padding-x: spacing.2 padding-y: spacing.1
      ColumnChooser(columns: chooserColumns, hiddenColumns: _hidden, columnOrder: _colOrder) {
        on columnVisibilityChange(keys): onChooserHidden(keys)
        on columnOrderChange(keys): onColumnDragReorder(keys)
      }
    }

    // The SECOND step of select-all. The header checkbox means "the rows that
    // are loaded"; this is how the user says "everything matching", which the
    // grid cannot hold and so hands back to the caller as a predicate.
    //
    // A sibling of the scroll container, NOT a child of it — the same reason
    // the bulk-actions bar is one: inside the width track it would slide out of
    // view on a horizontal scroll, taking the only route to the second step
    // with it. The plan placed it under the header checkbox, which is a 40px
    // column; a full-width offer does not fit there and would scroll away.
    //
    // Gated individually rather than wrapped, like its four sibling blocks, so
    // an unguarded grid renders byte-identically. `offerAllMatching` carries
    // `windowed`, so it is inert for every existing consumer.
    block {
      visibility: offerAllMatching
      data-grid-selectall: "true"
      padding-y: spacing.2
      padding-x: spacing.3
      border-bottom: borders.default
      background: groupBg
      layout: horizontal, gap: spacing.2, align: center
      button {
        background: 'transparent'
        border: borders.default
        border-radius: radius.md
        padding-y: 4px
        padding-x: 12px
        cursor: 'pointer'
        on click: emit("selectAllMatchingChange", true)
        text(allMatchingLabel) { style: type.label-sm, weight: 700, color: semantic.text-secondary }
      }
    }

    block {
      visibility: !guarded
      overflow: auto
      height: 100%
      max-height: gridMaxH
      data-grid-scroll: "true"

      // Width track. Every row is a 100%-wide child of this one element, so a
      // flexible column resolves ONCE here rather than per row \u2014 without it,
      // each row sizes its flexible column against its own content and the
      // columns drift apart (the bug this grid exists to prevent). The track's
      // min-width is also what makes a narrow container scroll horizontally
      // instead of crushing the columns.
      block {
        min-width: trackMin

        // ─── Composite header (0.7.0) ───
        // ONE sticky row of column-GROUPS, replacing the former two sibling
        // rows (a non-sticky group row over a sticky header row). An ungrouped
        // column is a single full-height cell whose heading sits on the shared
        // bottom baseline; a grouped run stacks its label over its members'
        // headings. Every width still comes from the same gridColMin/Max fns
        // as the body, so alignment holds by construction — and because the
        // composite is one sticky element, group labels no longer scroll away
        // from the columns they describe (the old design's stated limitation).
        //
        // Markers: `data-grid-row="header"` is the composite; each labelled
        // run's label strip is `data-grid-row="header-group"` (still never
        // "group", which the row-grouping feature owns). An unlabelled
        // segment's strip renders hidden rather than absent, matching the
        // filter row's contract for a conditional element.
        block {
          layout: horizontal
          background: semantic.surface-raised
          border-bottom: borders.strong
          position: headerPosition
          top: 0px
          z-index: 4
          data-grid-row: "header"

          block {
            visibility: selection == "multi"
            width: 40px
            layout: vertical, justify: center
            block {
              padding: headerPad
              layout: horizontal, align: center, justify: center
              Checkbox(label: "", checked: allSelected) {
                on change(isChecked): { if isChecked { selectAllRows() } else { if windowed { deselectRenderedRows() } else { clearSelection() } } }
              }
            }
          }

          each sizedPinnedSegments as seg {
            block {
              grow: true
              min-width: seg._min
              max-width: seg._max
              position: "sticky"
              left: 0px
              z-index: 5
              background: semantic.surface-raised
              layout: vertical
              border-left: !columnRules && groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
              border-right: !columnRules && groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
              data-grid-col-group: seg._seg.label
              // Segment identity for column drag. 'p:' = pinned side, then the
              // RUN id (see gridSegRunIds). Grouped by VALUE, not by container:
              // gridSegmentsOf gives every ungrouped column a container of its
              // own, so container identity would make each one a size-1 segment
              // and nothing would drag — while the LABEL would merge ungrouped
              // columns either side of a group into one non-contiguous segment.
              data-grid-col-seg: seg._segId

              block {
                visibility: seg._seg.label != ''
                padding: headerPad
                layout: horizontal, justify: center
                // Closes the bracket along the top. Without it the group label
                // and its member headings run together as one block of text and
                // the label stops reading as spanning them. Part of the same
                // `groupRules` treatment as the left/right edges, so a caller
                // that has not opted into the bracket is unaffected.
                border-bottom: groupRules ? bracketRule : "none"
                // A solo group's label IS its column's heading, so it carries
                // the column's click target. Without this, giving a column a
                // group to lift its heading onto the group line silently costs
                // it click-to-sort: the handler lives on the member cell below,
                // and the caller is left with a heading that looks sortable and
                // is not.
                cursor: seg._soloSortable ? "pointer" : "default"
                on click: seg._soloSortable ? toggleSortCol(seg._soloKey) : {}
                data-grid-row: "header-group"
                // The group drag's anchor: this cell is the handle that moves
                // the whole run among its sibling segments. NULL when the run
                // has no label — the ungrouped columns share one segment, and
                // making that draggable would move all of them at once. ('' is
                // not null: a binding only REMOVES an attribute for null.)
                data-grid-seg-label: seg._seg.label != '' ? seg._segId : null
                @slot("group-header", seg._seg)
                block {
                  visibility: !hasSlot("group-header")
                  text(seg._seg.label) {
                    style: type.label-sm
                    weight: 700
                    color: semantic.text-secondary
                    text-transform: 'uppercase'
                    letter-spacing: '0.09em'
                  }
                }
              }

              block {
                layout: horizontal
                grow: true
                each seg._cols as col {
                  block {
                    grow: true
                    min-width: col._min
                    max-width: col._max
                    cursor: col._col.sortable ? "pointer" : "default"
                    border-left: columnRules && col._col.key != firstColKey ? bracketRule : "none"
                    data-grid-col: col._col.key
                    // Per-column horizontal alignment, header half. This cell is
                    // a COLUMN flex (it stacks a group label over the heading),
                    // so the horizontal axis here is `align` — `justify: end`
                    // below is already spoken for and means BOTTOM. Getting that
                    // backwards produces a test that passes against unfixed code.
                    //
                    // Anything other than end/center resolves to `stretch`, NOT
                    // `start`: the heading block is a plain child that currently
                    // fills this cell, and shrink-wrapping it would stop a
                    // caller's header slot from spanning the column — the exact
                    // regression the `grow` note on the body cell describes.
                    // `start` and `stretch` are visually identical for a heading.
                    layout: vertical, justify: end, align: col._col.align == "end" ? "end" : (col._col.align == "center" ? "center" : "stretch")
                    // NO `on click` on the cell. The control is the button
                    // below; a handler here too would fire a second toggle as
                    // the button's click bubbled, flipping asc->desc->asc so
                    // the rows never moved.
                    block {
                      padding: headerPad
                      @slot("header", col._col)
                      // Sortable: a REAL button. This was a block carrying an
                      // `on click` — a div with a click handler — so the one
                      // interactive thing in the header was unreachable by
                      // keyboard and unannounced by a screen reader. Vector's
                      // DataTable rendered a real button, and its e2e asserts
                      // getByRole('button', { name: 'STUDENT' }).
                      block {
                        visibility: !hasSlot("header") && col._col.sortable
                        button {
                          background: "transparent"
                          border: "none"
                          padding: 0px
                          width: 100%
                          cursor: "pointer"
                          layout: horizontal, gap: spacing.1, align: center
                          on click: toggleSortCol(col._col.key)
                          text(col._col.header != null ? col._col.header : (col._col.label != null ? col._col.label : col._col.key)) {
                            style: type.label-sm
                            weight: 600
                          }
                          text(sortState.find(s => s.key == col._col.key) != null ? (sortState.find(s => s.key == col._col.key).direction == "asc" ? "↑" : "↓") : "") {
                            style: type.caption
                            color: semantic.interactive
                          }
                        }
                      }
                      // Not sortable: inert text. Exposing it as a control too
                      // would be a different a11y bug, not a fix — activating
                      // it does nothing.
                      block {
                        visibility: !hasSlot("header") && !col._col.sortable
                        layout: horizontal, gap: spacing.1, align: center
                        text(col._col.header != null ? col._col.header : (col._col.label != null ? col._col.label : col._col.key)) {
                          style: type.label-sm
                          weight: 600
                        }
                      }
                    }
                  }
                }
              }
            }
          }

          each sizedScrollSegments as seg {
            block {
              grow: true
              min-width: seg._min
              max-width: seg._max
              layout: vertical
              border-left: !columnRules && groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
              border-right: !columnRules && groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
              data-grid-col-group: seg._seg.label
              // Segment identity for column drag. 's:' = scrolling side, then
              // the RUN id. See the pinned loop above for why this is by VALUE
              // and why the value is a run id rather than the group label.
              data-grid-col-seg: seg._segId

              block {
                visibility: seg._seg.label != ''
                padding: headerPad
                layout: horizontal, justify: center
                // Closes the bracket along the top. Without it the group label
                // and its member headings run together as one block of text and
                // the label stops reading as spanning them. Part of the same
                // `groupRules` treatment as the left/right edges, so a caller
                // that has not opted into the bracket is unaffected.
                border-bottom: groupRules ? bracketRule : "none"
                // A solo group's label IS its column's heading, so it carries
                // the column's click target. Without this, giving a column a
                // group to lift its heading onto the group line silently costs
                // it click-to-sort: the handler lives on the member cell below,
                // and the caller is left with a heading that looks sortable and
                // is not.
                cursor: seg._soloSortable ? "pointer" : "default"
                on click: seg._soloSortable ? toggleSortCol(seg._soloKey) : {}
                data-grid-row: "header-group"
                // The group drag's anchor: this cell is the handle that moves
                // the whole run among its sibling segments. NULL when the run
                // has no label — the ungrouped columns share one segment, and
                // making that draggable would move all of them at once. ('' is
                // not null: a binding only REMOVES an attribute for null.)
                data-grid-seg-label: seg._seg.label != '' ? seg._segId : null
                @slot("group-header", seg._seg)
                block {
                  visibility: !hasSlot("group-header")
                  text(seg._seg.label) {
                    style: type.label-sm
                    weight: 700
                    color: semantic.text-secondary
                    text-transform: 'uppercase'
                    letter-spacing: '0.09em'
                  }
                }
              }

              block {
                layout: horizontal
                grow: true
                each seg._cols as col {
                  block {
                    grow: true
                    min-width: col._min
                    max-width: col._max
                    cursor: col._col.sortable ? "pointer" : "default"
                    border-left: columnRules && col._col.key != firstColKey ? bracketRule : "none"
                    data-grid-col: col._col.key
                    // Per-column horizontal alignment, header half. This cell is
                    // a COLUMN flex (it stacks a group label over the heading),
                    // so the horizontal axis here is `align` — `justify: end`
                    // below is already spoken for and means BOTTOM. Getting that
                    // backwards produces a test that passes against unfixed code.
                    //
                    // Anything other than end/center resolves to `stretch`, NOT
                    // `start`: the heading block is a plain child that currently
                    // fills this cell, and shrink-wrapping it would stop a
                    // caller's header slot from spanning the column — the exact
                    // regression the `grow` note on the body cell describes.
                    // `start` and `stretch` are visually identical for a heading.
                    layout: vertical, justify: end, align: col._col.align == "end" ? "end" : (col._col.align == "center" ? "center" : "stretch")
                    // NO `on click` on the cell. The control is the button
                    // below; a handler here too would fire a second toggle as
                    // the button's click bubbled, flipping asc->desc->asc so
                    // the rows never moved.
                    block {
                      padding: headerPad
                      @slot("header", col._col)
                      // Sortable: a REAL button. This was a block carrying an
                      // `on click` — a div with a click handler — so the one
                      // interactive thing in the header was unreachable by
                      // keyboard and unannounced by a screen reader. Vector's
                      // DataTable rendered a real button, and its e2e asserts
                      // getByRole('button', { name: 'STUDENT' }).
                      block {
                        visibility: !hasSlot("header") && col._col.sortable
                        button {
                          background: "transparent"
                          border: "none"
                          padding: 0px
                          width: 100%
                          cursor: "pointer"
                          layout: horizontal, gap: spacing.1, align: center
                          on click: toggleSortCol(col._col.key)
                          text(col._col.header != null ? col._col.header : (col._col.label != null ? col._col.label : col._col.key)) {
                            style: type.label-sm
                            weight: 600
                          }
                          text(sortState.find(s => s.key == col._col.key) != null ? (sortState.find(s => s.key == col._col.key).direction == "asc" ? "↑" : "↓") : "") {
                            style: type.caption
                            color: semantic.interactive
                          }
                        }
                      }
                      // Not sortable: inert text. Exposing it as a control too
                      // would be a different a11y bug, not a fix — activating
                      // it does nothing.
                      block {
                        visibility: !hasSlot("header") && !col._col.sortable
                        layout: horizontal, gap: spacing.1, align: center
                        text(col._col.header != null ? col._col.header : (col._col.label != null ? col._col.label : col._col.key)) {
                          style: type.label-sm
                          weight: 600
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }

        // Filter row (only when any column is filterable)
        block {
          visibility: hasFilters
          layout: horizontal
          background: semantic.surface
          border-bottom: borders.subtle
          data-grid-row: "filter"
          block {
            visibility: selection == "multi"
            width: 40px
          }
          each visibleColumns as col {
            block {
              padding: spacing.1
              grow: true
              min-width: col._min
              max-width: col._max
              // Free-text filter — the default, and everything that does not
              // opt into the option list below.
              block {
                visibility: col.filterable == true && col.filter != "select"
                textInput(filters.find(f => f.key == col.key) != null ? filters.find(f => f.key == col.key).value : "") {
                  placeholder: "Filter..."
                  border: borders.default
                  border-radius: radius.sm
                  width: 100%
                  on input(e): setFilter(col.key, e.target.value)
                }
              }
              // Option-list filter: `filter: "select"` plus `filterOptions`.
              // Runs through the SAME setFilter / `filter` event as the text
              // variant — a preset is a filter value, not a second mechanism.
              block {
                visibility: col.filterable == true && col.filter == "select"
                layout: horizontal, gap: spacing.1, align: center, wrap
                // "All" is the reset, and carries the empty value so the
                // active-option test is one comparison rather than a special case.
                button {
                  data-grid-filter-option: ""
                  background: filterValueOf(col.key) == "" ? semantic.interactive-bg : 'transparent'
                  border: 'none'
                  border-radius: radius.sm
                  padding-y: 4px
                  padding-x: 8px
                  cursor: 'pointer'
                  on click: setFilter(col.key, "")
                  text("All") {
                    style: type.body-sm
                    weight: filterValueOf(col.key) == "" ? 700 : 400
                    color: filterValueOf(col.key) == "" ? semantic.interactive-text : semantic.text-primary
                  }
                }
                each col.filterOptions as opt (opt.value) {
                  button {
                    data-grid-filter-option: opt.value
                    background: filterValueOf(col.key) == opt.value ? semantic.interactive-bg : 'transparent'
                    border: 'none'
                    border-radius: radius.sm
                    padding-y: 4px
                    padding-x: 8px
                    cursor: 'pointer'
                    on click: setFilter(col.key, opt.value)
                    text(opt.label) {
                      style: type.body-sm
                      weight: filterValueOf(col.key) == opt.value ? 700 : 400
                      color: filterValueOf(col.key) == opt.value ? semantic.interactive-text : semantic.text-primary
                    }
                  }
                }
              }
            }
          }
        }

        // Windowed rendering: a spacer standing in for the rows above the
        // window, so the scrollbar reports the full list height.
        block {
          visibility: windowed
          height: padTop
          data-grid-pad-top: "true"
        }

        // ONE body for both modes, over `renderRows`. It was split in two
        // for exactly one commit; two copies of ~330 lines inside a single
        // file is the CfDealTab-vs-Tabs failure mode, and no duplication
        // check can see it because they all compare across files.
        // Body rows \u2014 ordinary rows, group headers and totals all render through
        // this one template, so they cannot disagree about column widths.
        each renderRows as row, rowIdx {
          block {
            // Not arrived yet. `_unloaded` is a sentinel this grid puts in
            // place of a null so every `row.` access below stays safe —
            // `visibility:` does NOT defer a plain block's own bindings, it
            // only defers a component mount, so a literal null here would
            // throw in the background binding before anything could hide it.
            // Constant-true when windowing is off: no unwindowed row can carry
            // the sentinel, so the 16 existing consumers see no change. Task 8
            // replaces this gate with the skeleton/failed branches.
            visibility: row._unloaded != true
            layout: horizontal
            // ─── A WINDOWED ROW HONOURS THE HEIGHT IT DECLARED ──────────────
            // Every windowed geometry — the spacers, which rows the window
            // covers, what the scrollbar represents — is computed from
            // `rowHeight`, and nothing used to make the row obey it. Cell
            // padding decided the real height instead: a declared 30 rendered
            // at 41 in the reference harness.
            //
            // The grid was inconsistent with ITSELF, not merely with the
            // declaration — the skeleton and failed rows have always set
            // `height: rowHeightPx`, so a window of unloaded rows was 30px a
            // row and the same window loaded was 41. Rows therefore moved
            // under the user as blocks arrived, the scrollbar misreported the
            // list by (actual - declared) x rowCount, and scrolling a row to
            // an absolute offset could not land: the mapping changed every
            // time the window did.
            //
            // Only when windowed. `auto` is what every unwindowed row has
            // always had, so the 16 existing consumers are untouched — and
            // windowing already refuses the variable-height modes (expandable,
            // groupBy), so uniform rows are a contract it states, not a new
            // restriction.
            // `max-height` and NOT `overflow: hidden`. The pinned cell is a
            // direct child of this block with `position: sticky; left: 0`, and
            // an ancestor with `overflow: hidden` becomes that sticky
            // element's scroll container — an ancestor which never scrolls, so
            // the pin stops pinning. Measured in Chrome on this grid's own
            // structure: at scrollLeft 300 an ordinary row's pinned cell sat
            // at offset 0 from the scroller, and an `overflow:hidden` row's
            // sat at -300, fully scrolled away. The composite header did not
            // get the clip, so a windowed pinFirst grid would have frozen its
            // header's first column while every body row's slid out from
            // under it. `pinFirst` is not among the refused configurations,
            // so that combination is supported and must work.
            height: windowed ? rowHeightPx : 'auto'
            max-height: windowed ? rowHeightPx : 'none'
            border-top: gridRowKind(row) == "total" ? borders.strong : borders.subtle
            background: gridRowKind(row) != "row" ? groupBg : (selectedSet.includes(row[rowKeyField]) ? semantic.surface-raised : (striped && gridAbsIdx(windowed, winStart, rowIdx) % 2 == 1 ? stripeBg : "transparent"))
            shadow: gridRowRail(row)
            opacity: gridRowOpacity(row)
            // `rowsClickable` is scoped to ordinary rows (see the prop): a
            // group header or a total is not a navigation target. `selection`
            // keeps its existing, unscoped meaning so no current consumer's
            // cursor moves.
            cursor: selection != "none" || (rowsClickable && gridRowKind(row) == "row") ? "pointer" : "default"
            // Hover is opt-in via `hoverBackground` and only ever on ORDINARY
            // rows — a group header or a total is not a target, and lighting
            // one up would say it was. `visibility` cannot express this, so it
            // is a guarded style rather than a wrapper.
            on hover {
              background: hasHover && gridRowKind(row) == "row" ? hoverBackground : (gridRowKind(row) != "row" ? groupBg : (selectedSet.includes(row[rowKeyField]) ? semantic.surface-raised : (striped && gridAbsIdx(windowed, winStart, rowIdx) % 2 == 1 ? stripeBg : "transparent")))
            }
            // The pinned cell cannot inherit the `on hover` style above — it
            // paints its own opaque sticky background over the row — so the
            // hover is ALSO tracked as state for that cell to read.
            on mouse-enter: { hoveredRow = gridAbsIdx(windowed, winStart, rowIdx) }
            on mouse-leave: { hoveredRow = 0 - 1 }
            on click: {
              clickRow(row, gridAbsIdx(windowed, winStart, rowIdx))
              rowClickToggle(row)
            }
            // `_unloaded` FIRST. `visibility:` hides rather than omits, so this
            // block stays in the DOM for a row that has not arrived — and an
            // `_unloaded` sentinel carries no `_kind`, so it read as an
            // ordinary row and stamped "body". Consumers count
            // `[data-grid-row="body"]` without filtering for display (cf and
            // Vector both do), so every undelivered slot inflated their count
            // by one, varying with fetch timing. The skeleton beside it still
            // stamps "unloaded"; this one is inert scaffolding and says so.
            data-grid-row: row._unloaded == true ? "placeholder" : (gridRowKind(row) == "row" ? "body" : gridRowKind(row))
            // The ABSOLUTE index, so the wire can find a specific row in the
            // DOM and measure it. Scrolling a row into view from `rowHeight`
            // alone lands wrong whenever the rendered height differs from the
            // declared one — which it does here by 11px a row — so the wire
            // measures the real element when it has one.
            // WINDOWED ONLY. Stamped unconditionally this reached all 16
            // existing consumers, and gave every unwindowed row's attribute
            // binding a dependency on the `winStart` signal it never had —
            // their path has to stay byte-identical. `null` omits the
            // attribute, as the `data-testid` line below already relies on.
            data-grid-row-index: windowed ? gridAbsIdx(windowed, winStart, rowIdx) + '' : null
            data-testid: gridRowKind(row) == "row" ? rowTestIdAttr : null

            block {
              visibility: selection == "multi"
              width: 40px
              layout: horizontal
              block {
                padding: pad
                grow: true
                layout: horizontal, align: center, justify: center
                on click(event): swallowRowClick(event)
                Checkbox(label: "", checked: gridRowChecked(selectAllMatching, excludedKeys, selectedSet, row[rowKeyField])) {
                  on change(isChecked): selectRow(row)
                }
              }
            }

            each pinnedColumns as col {
              block {
                grow: true
                min-width: col._min
                max-width: col._max
                border-left: columnRules && col._col.key != firstColKey ? bracketRule
                  : (groupRules && col._gFirst && !col._gSolo ? bracketRule : "none")
                border-right: !columnRules && groupRules && col._gLast && !col._gSolo ? bracketRule : "none"
                data-grid-col: col._col.key
                position: "sticky"
                left: 0px
                z-index: 2
                // Hover joins the paint order here because this background is
                // what the user actually sees on the pinned column — the row's
                // hover style is underneath it. Same guard as the row: only
                // ordinary rows, only when hoverBackground is set.
                background: gridRowKind(row) != "row" ? groupBg : (hasHover && hoveredRow == gridAbsIdx(windowed, winStart, rowIdx) ? hoverBackground : pinBg)
                // The row's left rail (_accent) is drawn on the row container, but
                // this sticky pinned column's opaque background paints over it — so
                // re-draw the rail here, on top of the pin background, or a
                // provenance accent is invisible whenever the first column is pinned.
                shadow: gridRowRail(row)
                layout: horizontal
                block {
                padding: pad
                grow: true
                // Per-column horizontal alignment. This is a ROW flex, so the
                // horizontal axis is `justify`. It goes HERE and not on the
                // cell above because `grow: true` makes this box fill the cell
                // — aligning the cell would move a child that already spans it.
                // Absent `align` resolves to "start", which is the flex default,
                // so an undeclared column renders exactly as before.
                data-grid-cell-content: col._col.key
                layout: horizontal, gap: spacing.1, align: center, justify: col._col.align != null ? col._col.align : "start"
                // Group rows carry the expand/collapse control: the open state
                // is the grid's, so the caller's cell slot cannot own it.
                button {
                  visibility: gridRowKind(row) == "group"
                  background: 'transparent'
                  border: borders.default
                  border-radius: radius.sm
                  width: ctrlPx
                  height: ctrlPx
                  cursor: 'pointer'
                  layout: horizontal, justify: center, align: center
                  aria-label: row._toggleLabel != null ? row._toggleLabel : "Toggle group"
                  on click: toggleGroupRow(row)
                  text(groupRowIsOpen(row) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    font-size: ctrlFont
                    color: semantic.text-secondary
                  }
                }
                // A DERIVED group row has no caller cell content \u2014 the grid
                // made it \u2014 so it names itself. A structural group row still
                // takes its label from the caller's `cell` slot, untouched.
                block {
                  visibility: isGrouped && gridRowKind(row) == "group"
                  layout: horizontal, gap: spacing.1, align: center
                  text(row._groupLabel != null ? row._groupLabel : "") {
                    style: type.label-sm
                    weight: 700
                    color: semantic.text-secondary
                  }
                  // Guarded: a row with no count must render nothing, not the
                  // string "undefined". The block above is visibility-gated, so
                  // an unguarded concat is invisible \u2014 and still sits in the
                  // DOM's textContent for anything that reads it.
                  text(row._groupCount != null ? ("\u00b7 " + (row._groupCount + "")) : "") {
                    style: type.label-sm
                    color: semantic.text-tertiary
                  }
                }
                // The row-detail caret, for the same reason the group control
                // above is here: `expandedSet` is the grid's state, so a caller
                // drawing its own caret in the cell slot would have nothing to
                // toggle. A real `button`, not a clickable block \u2014 it is an
                // action, and it has to be keyboard-reachable.
                button {
                  visibility: hasExpandControl && gridRowKind(row) == "row" && col._col.key == expandColKey
                  data-grid-expand: "toggle"
                  background: 'transparent'
                  border: borders.default
                  border-radius: radius.sm
                  width: ctrlPx
                  height: ctrlPx
                  cursor: 'pointer'
                  layout: horizontal, justify: center, align: center
                  aria-expanded: gridRowIsExpanded(expandedSet, row[rowKeyField]) ? "true" : "false"
                  aria-label: gridRowIsExpanded(expandedSet, row[rowKeyField]) ? "Collapse row" : "Expand row"
                  on click(event): caretToggle(event, row)
                  text(gridRowIsExpanded(expandedSet, row[rowKeyField]) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    font-size: ctrlFont
                    color: semantic.text-secondary
                  }
                }
                // The cell's content fills the cell. Without this the slot's own
                // wrapper is a `flex: 0 1 auto` item in this row and shrink-fits
                // to its text, so a caller CANNOT align content to the cell's
                // right edge -- the header cell is a plain block and does fill,
                // so every right-aligned column came out with its heading and
                // its values on different edges. `grow` here, not `width: 100%`
                // on the caller's root: a component's root styling applies
                // inside its mount wrapper, never to the wrapper itself.
                block {
                  // Fills the cell so the caller's content can size to it —
                  // EXCEPT when the column asks to be aligned, because that fill
                  // is what makes alignment impossible. This box spans the
                  // content box, so the content box's `justify` has nothing left
                  // to push and `align: "end"` sets a style that does nothing.
                  // Measured in a browser; happy-dom computes no layout, so no
                  // unit test can see it.
                  //
                  // Conditional here rather than making this box a flex row:
                  // a flex row would turn the caller's mount wrapper into a flex
                  // item and shrink-wrap it for EVERY column, and cf's
                  // MktListingCell fills its cell to clamp a counterparty name
                  // to one line. Gating on `align` is opt-in by construction —
                  // a column that declares none renders exactly as before, and
                  // one that declares it gives up the fill, which is what asking
                  // to be aligned means.
                  grow: col._col.align == null
                  @slot("cell", col._col, row)
                  block {
                    visibility: !hasSlot("cell")
                    text(row[col._col.key] != null ? row[col._col.key] + "" : "") {
                      style: type.body-sm
                      color: semantic.text-primary
                    }
                  }
                }
                }
              }
            }

            each scrollColumns as col, colIdx {
              block {
                grow: true
                min-width: col._min
                max-width: col._max
                background: focusedRow == gridAbsIdx(windowed, winStart, rowIdx) && focusedCol == colIdx ? "rgba(59,130,246,0.08)" : "transparent"
                // The group bracket's body half: without it the grouping
                // dissolves below the header (mockup: q-first/q-last on td AND th).
                border-left: columnRules && col._col.key != firstColKey ? bracketRule
                  : (groupRules && col._gFirst && !col._gSolo ? bracketRule : "none")
                border-right: !columnRules && groupRules && col._gLast && !col._gSolo ? bracketRule : "none"
                data-grid-col: col._col.key
                layout: horizontal
                block {
                padding: pad
                grow: true
                // Per-column horizontal alignment. This is a ROW flex, so the
                // horizontal axis is `justify`. It goes HERE and not on the
                // cell above because `grow: true` makes this box fill the cell
                // — aligning the cell would move a child that already spans it.
                // Absent `align` resolves to "start", which is the flex default,
                // so an undeclared column renders exactly as before.
                data-grid-cell-content: col._col.key
                layout: horizontal, gap: spacing.1, align: center, justify: col._col.align != null ? col._col.align : "start"
                // Same control for an unpinned grid, where column 0 is here.
                button {
                  visibility: gridRowKind(row) == "group" && colIdx == 0 && !pinFirst
                  background: 'transparent'
                  border: borders.default
                  border-radius: radius.sm
                  width: ctrlPx
                  height: ctrlPx
                  cursor: 'pointer'
                  layout: horizontal, justify: center, align: center
                  aria-label: row._toggleLabel != null ? row._toggleLabel : "Toggle group"
                  on click: toggleGroupRow(row)
                  text(groupRowIsOpen(row) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    font-size: ctrlFont
                    color: semantic.text-secondary
                  }
                }
                // A DERIVED group row has no caller cell content \u2014 the grid
                // made it \u2014 so it names itself. A structural group row still
                // takes its label from the caller's `cell` slot, untouched.
                block {
                  visibility: isGrouped && gridRowKind(row) == "group"
                  layout: horizontal, gap: spacing.1, align: center
                  text(row._groupLabel != null ? row._groupLabel : "") {
                    style: type.label-sm
                    weight: 700
                    color: semantic.text-secondary
                  }
                  // Guarded: a row with no count must render nothing, not the
                  // string "undefined". The block above is visibility-gated, so
                  // an unguarded concat is invisible \u2014 and still sits in the
                  // DOM's textContent for anything that reads it.
                  text(row._groupCount != null ? ("\u00b7 " + (row._groupCount + "")) : "") {
                    style: type.label-sm
                    color: semantic.text-tertiary
                  }
                }
                // The row-detail caret again, for the scrolling columns. The
                // `!pinFirst` guard the group control carries is deliberately
                // ABSENT: `expandColumn` can name any column, so on a pinned
                // grid the caret legitimately lands out here whenever the
                // caller points it at something other than the pinned one.
                // Matching on the key rather than on colIdx is what makes the
                // two sites mutually exclusive without needing to agree on
                // which columns are pinned.
                button {
                  visibility: hasExpandControl && gridRowKind(row) == "row" && col._col.key == expandColKey
                  data-grid-expand: "toggle"
                  background: 'transparent'
                  border: borders.default
                  border-radius: radius.sm
                  width: ctrlPx
                  height: ctrlPx
                  cursor: 'pointer'
                  layout: horizontal, justify: center, align: center
                  aria-expanded: gridRowIsExpanded(expandedSet, row[rowKeyField]) ? "true" : "false"
                  aria-label: gridRowIsExpanded(expandedSet, row[rowKeyField]) ? "Collapse row" : "Expand row"
                  on click(event): caretToggle(event, row)
                  text(gridRowIsExpanded(expandedSet, row[rowKeyField]) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    font-size: ctrlFont
                    color: semantic.text-secondary
                  }
                }
                // The cell's content fills the cell. Without this the slot's own
                // wrapper is a `flex: 0 1 auto` item in this row and shrink-fits
                // to its text, so a caller CANNOT align content to the cell's
                // right edge -- the header cell is a plain block and does fill,
                // so every right-aligned column came out with its heading and
                // its values on different edges. `grow` here, not `width: 100%`
                // on the caller's root: a component's root styling applies
                // inside its mount wrapper, never to the wrapper itself.
                block {
                  // Fills the cell so the caller's content can size to it —
                  // EXCEPT when the column asks to be aligned, because that fill
                  // is what makes alignment impossible. This box spans the
                  // content box, so the content box's `justify` has nothing left
                  // to push and `align: "end"` sets a style that does nothing.
                  // Measured in a browser; happy-dom computes no layout, so no
                  // unit test can see it.
                  //
                  // Conditional here rather than making this box a flex row:
                  // a flex row would turn the caller's mount wrapper into a flex
                  // item and shrink-wrap it for EVERY column, and cf's
                  // MktListingCell fills its cell to clamp a counterparty name
                  // to one line. Gating on `align` is opt-in by construction —
                  // a column that declares none renders exactly as before, and
                  // one that declares it gives up the fill, which is what asking
                  // to be aligned means.
                  grow: col._col.align == null
                  @slot("cell", col._col, row)
                  block {
                    visibility: !hasSlot("cell")
                    text(row[col._col.key] != null ? row[col._col.key] + "" : "") {
                      style: type.body-sm
                      color: semantic.text-primary
                    }
                  }
                }
                }
              }
            }
          }

          // Full-width detail row. Outside the column loop on purpose: it spans
          // every column, so it must not take a column's width source. Only
          // ordinary rows expand — a group header or a total has no detail.
          block {
            visibility: expandable
              && gridRowKind(row) == "row"
              && row[rowKeyField] != null
              && gridRowIsExpanded(expandedSet, row[rowKeyField])
            layout: horizontal
            border-top: borders.subtle
            background: semantic.surface
            min-width: trackMin
            data-grid-row: "detail"
            block {
              grow: true
              @slot("detail", row)
            }
          }

          // ─── The two windowed placeholders ────────────────────────────────
          // Siblings of the row block above, and mutually exclusive with it and
          // with each other. The row block's gate is `row._unloaded != true`,
          // and a failed block is never HELD — the cache clears `failed` on
          // accept and never sets both — so a failed row is always an unloaded
          // one and the three gates partition the loop exactly.
          //
          // Both are inert when windowing is off: no unwindowed row can carry
          // the sentinel, and `winFailed` is empty so every index is out of
          // range. The 16 existing consumers render byte-identically.

          // Not arrived yet. SkeletonRow is what this grid already renders for
          // its own first load; a second placeholder would only be a second
          // thing to keep consistent.
          //
          // ── WHY THIS IS TWO WHOLE ROWS AND NOT ONE ROW WITH TWO INSIDES ───
          // The compiler only mounts a block's contents LAZILY when the block
          // carries a `visibility:` AND a component invocation as a DIRECT
          // child (ast-to-ir.ts, `hasVisibility && hasSurfaceRef`). Nesting the
          // two shapes one level down to save a node cost the outer gate its
          // laziness and left each inner gate on the STATIC `skeletonVariant`,
          // so every row of every grid — windowed or not, loaded or not —
          // eagerly mounted a whole SkeletonRow tree. Measured before this was
          // put right: +19 DOM nodes and one SkeletonRow mount PER ROW on a
          // fully-loaded grid, on a component that does not virtualise.
          // Duplicating the row's chrome is the cheaper of the two.
          block {
            visibility: row._unloaded == true && !gridBlockFailed(winFailed, rowIdx) && skeletonVariant != "bar"
            height: rowHeightPx
            padding-x: padX
            layout: horizontal, align: center
            overflow: hidden
            border-top: borders.subtle
            // Mirrors the gate above, for the same reason the body row does:
            // `visibility:` leaves this block in the DOM once the rows arrive,
            // and a consumer counting `[data-grid-row="unloaded"]` raw would
            // read the whole window as still loading, forever. It mirrors the
            // WHOLE gate, variant included — with two of these rows per slot, a
            // stamp on the shared half would count every unloaded row twice.
            data-grid-row: row._unloaded == true && !gridBlockFailed(winFailed, rowIdx) && skeletonVariant != "bar" ? "unloaded" : "placeholder"
            SkeletonRow()
          }

          // The dense-table shape: one shimmer line, no avatar, no pill.
          // SkeletonLine is the registry primitive SkeletonRow itself is built
          // from — not a hand-rolled bar.
          block {
            visibility: row._unloaded == true && !gridBlockFailed(winFailed, rowIdx) && skeletonVariant == "bar"
            height: rowHeightPx
            padding-x: padX
            // COLUMN, not row, and the difference is the whole variant.
            //
            // `layout: horizontal, align: center` — what this was, and what the
            // avatar row above still is — makes the child a flex item in a ROW.
            // A block flex item with no basis sizes to its content, and its
            // content is SkeletonLine at width 60%, so the percentage resolves
            // against a width that is itself waiting on the content: it
            // collapses to 0. The row rendered EMPTY. It shipped that way in
            // 1.7.0 and survived four review rounds and a harness screenshot,
            // because a blank row and a very pale bar look identical to a
            // person scrolling past, and happy-dom computes no layout at all.
            // Measured in Chrome against cf's rate history: bar width 0px, and
            // 770px the moment the item is given a basis.
            //
            // A column flex container leaves align-items at its `stretch`
            // default, so the item fills the row's width and 60% has something
            // to be 60% OF; `justify: center` then does the vertical centering
            // `align: center` was there for. The alternative — wrapping
            // SkeletonLine in a growing block — costs the gate above its
            // laziness, because the compiler only mounts lazily when a
            // component invocation is a DIRECT child of the block carrying
            // `visibility:`. That is the regression documented on the avatar
            // row; this shape avoids it by not adding a node at all.
            layout: vertical, justify: center
            overflow: hidden
            border-top: borders.subtle
            data-grid-row: row._unloaded == true && !gridBlockFailed(winFailed, rowIdx) && skeletonVariant == "bar" ? "unloaded" : "placeholder"
            SkeletonLine(width: "60%", height: "10px")
          }

          // The block failed. A failed block is NEVER re-requested on its own —
          // the next scroll event would re-fire and re-fail it, forever, which
          // is the fetch-trigger-latch shape — so this button is the only way
          // back. It emits the BLOCK index, which is what retryBlock() takes;
          // the row index and the absolute row index are both one small
          // expression away and both wrong.
          //
          // ONCE PER BLOCK, not once per row. Rendering it on every slot put 12
          // identical messages and 12 Retry buttons on screen at a 520px
          // viewport (measured against cf's benchmark-rates page, 2026-08-15) —
          // a wall of errors for a single failure. Every slot below stays
          // stamped `failed`, because the block really is dead for its whole
          // height; only the message and the affordance collapse.
          block {
            visibility: gridBlockMsgSlot(winFailed, winStart, rowIdx, blockSize, winFirstVisible)
            height: rowHeightPx
            padding-x: padX
            layout: horizontal, gap: spacing.2, align: center
            overflow: hidden
            border-top: borders.subtle
            // Mirrors THIS block's gate, not the block-level one. Both this row
            // and the filler below stamp `failed`, and only one of them is ever
            // shown — stamping both on the shared `gridBlockFailed` doubled a
            // raw `[data-grid-row="failed"]` count (5 rows read as 10). The
            // tests could not see it because they filter through `isShown`.
            data-grid-row: gridBlockMsgSlot(winFailed, winStart, rowIdx, blockSize, winFirstVisible) ? "failed" : "placeholder"
            // NO `role="status"` here, deliberately. This row is per-SLOT and it
            // moves as the user scrolls, so a live region on it announces either
            // never (the text never changes, which several readers ignore) or on
            // every row of travel, as each new slot is un-hidden. The message is
            // ordinary text in the accessibility tree, which is what the filler
            // rows below are aria-hidden to keep unambiguous. One live region
            // declared outside the row loop is the fix if announcement is wanted.
            text('Could not load these rows') {
              style: type.body-sm
              color: semantic.destructive
            }
            button {
              background: 'transparent'
              border: borders.default
              border-radius: radius.sm
              padding-y: 2px
              padding-x: 8px
              cursor: 'pointer'
              data-grid-block-retry: "true"
              on click: retryFailedBlock(gridBlockOf(winStart, rowIdx, blockSize))
              text('Retry') { style: type.label-sm, weight: 500, color: semantic.text-secondary }
            }
          }

          // The REST of a failed block: its height, its rule, its stamp, and
          // nothing else. Deliberately not a skeleton — a shimmer says "still
          // loading", and this block has stopped asking; the permanent-skeleton
          // reading is the exact confusion the failed branch exists to end.
          // Deliberately not empty of stamp either: a consumer counting failed
          // rows must still see the whole block, and the row loop's three gates
          // have to keep partitioning it (unloaded / failed / body).
          block {
            visibility: gridBlockFailed(winFailed, rowIdx) && !gridBlockMsgSlot(winFailed, winStart, rowIdx, blockSize, winFirstVisible)
            height: rowHeightPx
            padding-x: padX
            layout: horizontal, align: center
            overflow: hidden
            border-top: borders.subtle
            data-grid-row: gridBlockFailed(winFailed, rowIdx) && !gridBlockMsgSlot(winFailed, winStart, rowIdx, blockSize, winFirstVisible) ? "failed" : "placeholder"
            // Nothing to say: the one message row above says it for the whole
            // block. Silent empty rows in the a11y tree are worse than absent
            // ones — they read as rows that simply have no content.
            aria-hidden: "true"
          }
        }

        block {
          visibility: windowed
          height: padBot
          data-grid-pad-bot: "true"
        }
      }

      // Empty state. Gated on `isEmpty`, NOT on "no rows": a grid that is
      // still fetching used to render this at the user while the data was in
      // flight, which every consumer papered over with a spinner of its own.
      block {
        visibility: isEmpty
        padding: spacing.6
        layout: horizontal, justify: center
        text(emptyText) { style: type.body-md, color: semantic.text-tertiary }
      }

      // First-load skeletons — only when there is nothing to show yet. A
      // refresh of a populated grid must not blank the rows being read.
      block {
        visibility: isFirstLoad
        padding: spacing.3
        layout: vertical, gap: spacing.2
        data-grid-row: "skeleton"
        // SkeletonRow is the registry component, and the one Vector's DataTable
        // uses for this exact state — not a hand-rolled shimmer. (There is no
        // `SkeletonLines`; the file exports SkeletonLine / Block / Circle / Row.)
        each [1, 2, 3, 4, 5, 6] as n (n) {
          block {
            visibility: skeletonVariant != "bar"
            SkeletonRow()
          }
          block {
            visibility: skeletonVariant == "bar"
            // The same row box the avatar branch gets from SkeletonRow's own
            // content. Without it this is a bare 10px line, so six of them stand
            // in for a table a third their height and the panel jumps when the
            // rows land. `skelRowPx`, not `rowHeightPx` — see its declaration.
            height: skelRowPx
            padding-x: padX
            // COLUMN, for the reason spelled out on the windowed bar row above:
            // a block flex ITEM in a row container sizes to its content, and
            // this one's content asks for 60% of the width the item is supposed
            // to be establishing, so it collapses to zero and the row renders
            // BLANK. 1.7.5 fixed that on the windowed row and left this branch
            // — the only bar an UNWINDOWED grid can reach — still broken, so
            // `>= 1.7.5` meant "the bar works" only if you happened to window.
            layout: vertical, justify: center
            SkeletonLine(width: "60%", height: "10px")
          }
        }
      }

      // Load more. The grid never fetches; it asks.
      block {
        visibility: hasMore
        padding-y: spacing.3
        layout: horizontal, justify: center
        data-grid-loadmore: "true"
        button {
          background: 'transparent'
          border: borders.default
          border-radius: radius.md
          padding-y: 6px
          padding-x: 16px
          cursor: 'pointer'
          on click: loadMore()
          text('Load more') { style: type.body-md, weight: 500, color: semantic.text-secondary }
        }
      }
    }

    // Bulk-actions bar. A sibling of the scroll container, NOT a child of it —
    // inside, it would slide out of view with a horizontal scroll, taking the
    // only route to the actions with it.
    //
    // The count is the grid's, the buttons are the caller's, and an unprovided
    // slot still leaves a usable bar. `selectedSet` holds row KEYS (see
    // selectRow), so a caller can act on them without a lookup.
    // Gated on `selection` as well as the set: a caller may seed `selected` to
    // TINT rows without opting into selection UI, and an action bar it never
    // asked for has no control on screen able to clear it.
    block {
      // `selectAllMatching` is its own reason to be here. In predicate mode
      // `selectedSet` is normally EMPTY — the whole point is that the grid
      // does not hold the keys — so gating on its length hid the bar entirely
      // while the caller still believed every matching row was selected,
      // leaving no control on screen able to say otherwise.
      visibility: selection != "none" && (selectedSet.length > 0 || selectAllMatching) && !guarded
      data-grid-row: "bulk"
      padding-y: spacing.2
      padding-x: spacing.3
      border-top: borders.default
      background: groupBg
      layout: horizontal, gap: spacing.3, align: center
      // The SUMMARY's count, not the held keys: in predicate mode those are
      // two very different numbers and the held one is meaningless.
      text(toString(selectionSummary.count) + " selected") {
        weight: 700
        style: type.label-sm
        color: semantic.text-secondary
      }
      // The way out. Without it, predicate mode was one-way: nothing anywhere
      // emitted selectAllMatchingChange(false), so once the user opted in
      // there was no control that could take them back out.
      block {
        visibility: selectAllMatching
        button {
          // The marker sits on the BUTTON, not the wrapper — the wrapper is
          // only the visibility gate, and a click on it reaches no handler.
          data-grid-clear-matching: "true"
          background: 'transparent'
          border: borders.default
          border-radius: radius.sm
          padding-y: 2px
          padding-x: 8px
          cursor: 'pointer'
          on click: exitAllMatching()
          text('Clear selection') { style: type.label-sm, weight: 500, color: semantic.text-secondary }
        }
      }
      // TWO arguments since 1.3.0. `selectedSet` is unchanged and stays first,
      // so a caller destructuring one still binds — a slot callback compiles to
      // a plain arrow function, and JS drops the extra argument. The second
      // carries what `selectedSet` cannot say: in predicate mode the grid holds
      // a handful of keys and the caller means every matching row.
      @slot("bulkActions", selectedSet, selectionSummary)
    }

    // The refusal itself — the only thing this grid renders when a windowed
    // configuration cannot be honoured. It is a sibling of the four blocks
    // above rather than a replacement for them, and every one of those carries
    // `!guarded`, so exactly one of the two states is ever on screen.
    block {
      visibility: guarded
      data-grid-guard: "true"
      role: "alert"
      padding: spacing.3
      border: borders.strong
      background: semantic.destructive-bg
      text(guardMsg) {
        style: type.body-sm
        weight: 500
        color: semantic.destructive
      }
    }
  }
}
