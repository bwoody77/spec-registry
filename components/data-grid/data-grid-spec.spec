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

// Each column carries its resolved min/max width plus its position at a group
// run's EDGE (`_gFirst` / `_gLast`), which is what `groupRules` draws the
// full-height bracket from: the component already knows where a run starts and
// ends, so a consumer never re-derives group boundaries in its own cells.
fn gridSizedCols(cols: list) -> list {
  let n = length(cols)
  return cols |> map((c, i) => {
    _col: c,
    _min: gridColMin(c),
    _max: gridColMax(c),
    _gFirst: c.group != null && c.group != '' && (i == 0 || cols[i - 1].group != c.group),
    _gLast: c.group != null && c.group != '' && (i == n - 1 || cols[i + 1].group != c.group)
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
) {
  @state {
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
  }

  @computed {
    visibleColumns: columns.filter(c => c.visible != false)
    processedRows: applySortAndFilter(rows, sortState, filters)
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
    pinnedColumns: pinFirst ? gridSizedCols(visibleColumns.slice(0, 1)) : []
    scrollColumns: pinFirst ? gridSizedCols(visibleColumns.slice(1)) : gridSizedCols(visibleColumns)
    trackMin: gridTrackMin(visibleColumns)
    // Header segments. The pinned column renders outside the scrolling loop, so
    // a segment may never straddle that boundary — with pinFirst the first
    // column is segmented on its own. `_cols` sizes each segment's members from
    // the same fns as the body, so the two cannot disagree about widths.
    pinnedSegments: pinFirst ? gridSegmentsOf(visibleColumns.slice(0, 1)) : []
    scrollSegments: pinFirst ? gridSegmentsOf(visibleColumns.slice(1)) : gridSegmentsOf(visibleColumns)
    sizedPinnedSegments: pinnedSegments |> map(s => { _seg: s, _min: gridSegMin(s), _max: gridSegMax(s), _cols: gridSizedCols(s.cols) })
    sizedScrollSegments: scrollSegments |> map(s => { _seg: s, _min: gridSegMin(s), _max: gridSegMax(s), _cols: gridSizedCols(s.cols) })
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
    toggleSortCol(colKey) {
      sortState = toggleSortState(sortState, colKey)
      emit("sort", sortState)
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
              border-left: groupRules && seg._seg.label != '' ? bracketRule : "none"
              border-right: groupRules && seg._seg.label != '' ? bracketRule : "none"
              data-grid-col-group: seg._seg.label

              block {
                visibility: seg._seg.label != ''
                padding: headerPad
                layout: horizontal, justify: center
                data-grid-row: "header-group"
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
              border-left: groupRules && seg._seg.label != '' ? bracketRule : "none"
              border-right: groupRules && seg._seg.label != '' ? bracketRule : "none"
              data-grid-col-group: seg._seg.label

              block {
                visibility: seg._seg.label != ''
                padding: headerPad
                layout: horizontal, justify: center
                data-grid-row: "header-group"
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
            on click: {
              clickRow(row, rowIdx)
              toggleExpanded(row)
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
                border-left: groupRules && col._gFirst ? bracketRule : "none"
                border-right: groupRules && col._gLast ? bracketRule : "none"
                data-grid-col: col._col.key
                position: "sticky"
                left: 0px
                z-index: 2
                background: gridRowKind(row) != "row" ? groupBg : pinBg
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
                  width: 22px
                  height: 22px
                  cursor: 'pointer'
                  layout: horizontal, justify: center, align: center
                  aria-label: row._toggleLabel != null ? row._toggleLabel : "Toggle group"
                  on click: toggleGroup(row._key)
                  text(gridGroupIsOpen(openGroups, row._key) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
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
                border-left: groupRules && col._gFirst ? bracketRule : "none"
                border-right: groupRules && col._gLast ? bracketRule : "none"
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
                  width: 22px
                  height: 22px
                  cursor: 'pointer'
                  layout: horizontal, justify: center, align: center
                  aria-label: row._toggleLabel != null ? row._toggleLabel : "Toggle group"
                  on click: toggleGroup(row._key)
                  text(gridGroupIsOpen(openGroups, row._key) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
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
