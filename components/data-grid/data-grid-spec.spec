@extern { genGridId, wireColumnDrag, wireGroupDrag } from "@spec/components/data-grid-column-drag.js"

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

// Total of every visible column's floor — the width the rows must not shrink
// below. Set on the track so a narrow container scrolls instead of crushing.
fn gridTrackMin(cols: list) -> string {
  let total = cols |> reduce((acc, c) => acc + (c.width != null ? c.width : (c.minWidth != null ? c.minWidth : 100)), 0)
  return (total + '') + 'px'
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
fn gridSegMin(seg: map) -> string {
  let total = seg.cols |> reduce((acc, c) => acc + (c.width != null ? c.width : (c.minWidth != null ? c.minWidth : 100)), 0)
  return (total + '') + 'px'
}

fn gridSegMax(seg: map) -> string {
  let flexible = seg.cols |> some(c => c.width == null)
  if flexible { return '100000px' }
  let total = seg.cols |> reduce((acc, c) => acc + c.width, 0)
  return (total + '') + 'px'
}

// ─── Row kinds ──────────────────────────────────────────────────────────────
// A row may declare `_kind`: 'group' (a collapsible header for the rows that
// name it in `_group`) or 'total' (a pinned-looking summary). Anything else is
// an ordinary row. `_accent` draws a left rail and `_opacity` dims the row.
// A group row may also carry `_toggleLabel` to name its expand/collapse control
// for screen readers (default: "Toggle group").

fn gridRowKind(row: map) -> string {
  if row._kind != null { return row._kind }
  return 'row'
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

component DataGridSpec(
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
  // Controlled sorting. When true the grid never reorders rows itself: header
  // clicks still toggle sortState (so the indicator moves) and still emit
  // `sort`, but the rows render exactly as given — the CALLER sorts. This is
  // what server-side (or paginated) sorting needs: a grid that sorts its own
  // page slice reorders ten rows and calls it a sort, while the real order
  // lives in the full set the caller holds. False preserves today's behaviour
  // for every existing consumer.
  externalSort: boolean = false,
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
    // `allKeysOf` is an ACTION, not the @computed it returns: a @state
    // initialiser runs before the @computed block exists, so naming
    // orderedAllKeys here is a temporal-dead-zone error at mount. The action is
    // called per use, by which time the computed is live — which also keeps the
    // read fresh rather than captured.
    _colDragTeardown: wireColumnDrag(_gridId, onColumnDragReorder, reorderableColumns, allKeysOf)
    // The same drag, one level up: a labelled group's header cell moves the
    // whole run among its sibling segments. Without it a group is the one
    // thing on the grid that cannot be moved, because a group IS a segment and
    // the column wire never crosses one.
    _groupDragTeardown: wireGroupDrag(_gridId, onColumnDragReorder, reorderableColumns, allKeysOf)
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
    // externalSort: the caller owns the order; only the filter pass runs here.
    processedRows: externalSort
      ? applySortAndFilter(rows, [], filters)
      : applySortAndFilter(rows, sortState, filters)
    // Rows whose group is collapsed drop out; group headers and totals remain.
    displayRows: gridVisibleRows(processedRows, openGroups)
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
    pinnedColumns: pinFirst ? gridSizedCols(visibleColumns.slice(0, 1), visibleColumns) : []
    scrollColumns: pinFirst ? gridSizedCols(visibleColumns.slice(1), visibleColumns) : gridSizedCols(visibleColumns, visibleColumns)
    trackMin: gridTrackMin(visibleColumns)
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
    sizedPinnedSegments: pinnedSegments |> map((s, i) => { _seg: s, _min: gridSegMin(s), _max: gridSegMax(s), _cols: gridSizedCols(s.cols, visibleColumns),
      _segId: 'p:' + (pinnedSegRuns[i] + ''),
      _solo: gridGroupSize(visibleColumns, s.label) == 1,
      _soloSortable: gridGroupSize(visibleColumns, s.label) == 1 && s.cols[0].sortable == true,
      _soloKey: gridGroupSize(visibleColumns, s.label) == 1 ? s.cols[0].key : '' })
    sizedScrollSegments: scrollSegments |> map((s, i) => { _seg: s, _min: gridSegMin(s), _max: gridSegMax(s), _cols: gridSizedCols(s.cols, visibleColumns),
      _segId: 's:' + (scrollSegRuns[i] + ''),
      _solo: gridGroupSize(visibleColumns, s.label) == 1,
      _soloSortable: gridGroupSize(visibleColumns, s.label) == 1 && s.cols[0].sortable == true,
      _soloKey: gridGroupSize(visibleColumns, s.label) == 1 ? s.cols[0].key : '' })
    pinBg: pinBackground != "" ? pinBackground : semantic.surface
    groupBg: groupBackground != "" ? groupBackground : semantic.surface-raised
    stripeBg: stripeBackground != "" ? stripeBackground : semantic.surface
    pad: cellPadding != "" ? cellPadding : spacing.2
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
    allSelected: selectedSet.length == displayRows.length && displayRows.length > 0
  }

  @actions {
    toggleGroup(key) {
      openGroups = gridToggleGroup(openGroups, key)
      emit("groupToggle", key)
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
    selectRow(idx) {
      if selection == "single" {
        selectedSet = [idx]
        emit("selectionChange", [idx])
      } else {
        if selection == "multi" {
          if selectedSet.includes(idx) { selectedSet = selectedSet.filter(i => i != idx) }
          else { selectedSet = selectedSet.concat([idx]) }
          emit("selectionChange", selectedSet)
        }
      }
    }
    selectAllRows() {
      selectedSet = processedRows.map((row, i) => i)
      emit("selectionChange", selectedSet)
    }
    clearSelection() {
      selectedSet = []
      emit("selectionChange", [])
    }
    clickRow(row, idx) {
      selectRow(idx)
      emit("rowClick", row, idx)
    }
    moveUp()    { if focusedRow > 0 { focusedRow = focusedRow - 1 } }
    // From "nothing focused", the first Down/Right press lands on the first cell.
    moveDown()  { if focusedRow < displayRows.length - 1 { focusedRow = focusedRow + 1  if focusedCol < 0 { focusedCol = 0 } } }
    moveLeft()  { if focusedCol > 0 { focusedCol = focusedCol - 1 } }
    moveRight() { if focusedCol < visibleColumns.length - 1 { focusedCol = focusedCol + 1  if focusedRow < 0 { focusedRow = 0 } } }
    selectFocused() { if focusedRow >= 0 { selectRow(focusedRow) } }
  }

  block {
    border: borders.default
    border-radius: radius.md
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
        if allSelected { clearSelection() } else { selectAllRows() }
      }
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
      visibility: configurableColumns
      layout: horizontal, justify: end
      padding-x: spacing.2 padding-y: spacing.1
      ColumnChooser(columns: chooserColumns, hiddenColumns: _hidden, columnOrder: _colOrder) {
        on columnVisibilityChange(keys): onChooserHidden(keys)
        on columnOrderChange(keys): onColumnDragReorder(keys)
      }
    }

    block {
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
          position: "sticky"
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
                on change(isChecked): { if isChecked { selectAllRows() } else { clearSelection() } }
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
              border-left: groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
              border-right: groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
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
                    data-grid-col: col._col.key
                    layout: vertical, justify: end
                    on click: col._col.sortable ? toggleSortCol(col._col.key) : {}
                    block {
                      padding: headerPad
                      @slot("header", col._col)
                      block {
                        visibility: !hasSlot("header")
                        layout: horizontal, gap: spacing.1, align: center
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
              border-left: groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
              border-right: groupRules && seg._seg.label != '' && !seg._solo ? bracketRule : "none"
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
                    data-grid-col: col._col.key
                    layout: vertical, justify: end
                    on click: col._col.sortable ? toggleSortCol(col._col.key) : {}
                    block {
                      padding: headerPad
                      @slot("header", col._col)
                      block {
                        visibility: !hasSlot("header")
                        layout: horizontal, gap: spacing.1, align: center
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
              block {
                visibility: col.filterable == true
                textInput(filters.find(f => f.key == col.key) != null ? filters.find(f => f.key == col.key).value : "") {
                  placeholder: "Filter..."
                  border: borders.default
                  border-radius: radius.sm
                  width: 100%
                  on input(e): setFilter(col.key, e.target.value)
                }
              }
            }
          }
        }

        // Body rows \u2014 ordinary rows, group headers and totals all render through
        // this one template, so they cannot disagree about column widths.
        each displayRows as row, rowIdx {
          block {
            layout: horizontal
            border-top: gridRowKind(row) == "total" ? borders.strong : borders.subtle
            background: gridRowKind(row) != "row" ? groupBg : (selectedSet.includes(rowIdx) ? semantic.surface-raised : (striped && rowIdx % 2 == 1 ? stripeBg : "transparent"))
            shadow: gridRowRail(row)
            opacity: gridRowOpacity(row)
            cursor: selection != "none" ? "pointer" : "default"
            // Hover is opt-in via `hoverBackground` and only ever on ORDINARY
            // rows — a group header or a total is not a target, and lighting
            // one up would say it was. `visibility` cannot express this, so it
            // is a guarded style rather than a wrapper.
            on hover {
              background: hasHover && gridRowKind(row) == "row" ? hoverBackground : (gridRowKind(row) != "row" ? groupBg : (selectedSet.includes(rowIdx) ? semantic.surface-raised : (striped && rowIdx % 2 == 1 ? stripeBg : "transparent")))
            }
            // The pinned cell cannot inherit the `on hover` style above — it
            // paints its own opaque sticky background over the row — so the
            // hover is ALSO tracked as state for that cell to read.
            on mouse-enter: { hoveredRow = rowIdx }
            on mouse-leave: { hoveredRow = 0 - 1 }
            on click: {
              clickRow(row, rowIdx)
              rowClickToggle(row)
            }
            data-grid-row: gridRowKind(row) == "row" ? "body" : gridRowKind(row)

            block {
              visibility: selection == "multi"
              width: 40px
              layout: horizontal
              block {
                padding: pad
                grow: true
                layout: horizontal, align: center, justify: center
                Checkbox(label: "", checked: selectedSet.includes(rowIdx)) {
                  on change(isChecked): selectRow(rowIdx)
                }
              }
            }

            each pinnedColumns as col {
              block {
                grow: true
                min-width: col._min
                max-width: col._max
                border-left: groupRules && col._gFirst && !col._gSolo ? bracketRule : "none"
                border-right: groupRules && col._gLast && !col._gSolo ? bracketRule : "none"
                data-grid-col: col._col.key
                position: "sticky"
                left: 0px
                z-index: 2
                // Hover joins the paint order here because this background is
                // what the user actually sees on the pinned column — the row's
                // hover style is underneath it. Same guard as the row: only
                // ordinary rows, only when hoverBackground is set.
                background: gridRowKind(row) != "row" ? groupBg : (hasHover && hoveredRow == rowIdx ? hoverBackground : pinBg)
                // The row's left rail (_accent) is drawn on the row container, but
                // this sticky pinned column's opaque background paints over it — so
                // re-draw the rail here, on top of the pin background, or a
                // provenance accent is invisible whenever the first column is pinned.
                shadow: gridRowRail(row)
                layout: horizontal
                block {
                padding: pad
                grow: true
                layout: horizontal, gap: spacing.1, align: center
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
                  on click: toggleGroup(row._key)
                  text(gridGroupIsOpen(openGroups, row._key) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    font-size: ctrlFont
                    color: semantic.text-secondary
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
                  grow: true
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
                background: focusedRow == rowIdx && focusedCol == colIdx ? "rgba(59,130,246,0.08)" : "transparent"
                // The group bracket's body half: without it the grouping
                // dissolves below the header (mockup: q-first/q-last on td AND th).
                border-left: groupRules && col._gFirst && !col._gSolo ? bracketRule : "none"
                border-right: groupRules && col._gLast && !col._gSolo ? bracketRule : "none"
                data-grid-col: col._col.key
                layout: horizontal
                block {
                padding: pad
                grow: true
                layout: horizontal, gap: spacing.1, align: center
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
                  on click: toggleGroup(row._key)
                  text(gridGroupIsOpen(openGroups, row._key) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    font-size: ctrlFont
                    color: semantic.text-secondary
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
                  grow: true
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
        }
      }

      // Empty state
      block {
        visibility: displayRows.length == 0
        padding: spacing.6
        layout: horizontal, justify: center
        text("No rows") { style: type.body-md, color: semantic.text-tertiary }
      }
    }
  }
}
