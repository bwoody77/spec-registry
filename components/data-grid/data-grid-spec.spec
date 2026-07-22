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
) {
  @state {
    sortState: sort
    selectedSet: selected
    filters: []
    focusedRow: 0
    focusedCol: 0
    openGroups: defaultOpen
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
    sizedColumns: visibleColumns |> map(c => { _col: c, _min: gridColMin(c), _max: gridColMax(c) })
    // The pinned column is split out of the loop; both lists still come from
    // `sizedColumns`, so header and body cannot disagree about widths.
    pinnedColumns: pinFirst ? sizedColumns.slice(0, 1) : []
    scrollColumns: pinFirst ? sizedColumns.slice(1) : sizedColumns
    trackMin: gridTrackMin(visibleColumns)
    pinBg: pinBackground != "" ? pinBackground : semantic.surface
    groupBg: groupBackground != "" ? groupBackground : semantic.surface-raised
    hasFilters: columns.some(c => c.filterable == true)
    allSelected: selectedSet.length == displayRows.length && displayRows.length > 0
  }

  @actions {
    toggleGroup(key) {
      openGroups = gridToggleGroup(openGroups, key)
      emit("groupToggle", key)
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
    moveDown()  { if focusedRow < processedRows.length - 1 { focusedRow = focusedRow + 1 } }
    moveLeft()  { if focusedCol > 0 { focusedCol = focusedCol - 1 } }
    moveRight() { if focusedCol < visibleColumns.length - 1 { focusedCol = focusedCol + 1 } }
    selectFocused() { selectRow(focusedRow) }
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
      data-grid-scroll: "true"

      // Width track. Every row is a 100%-wide child of this one element, so a
      // flexible column resolves ONCE here rather than per row \u2014 without it,
      // each row sizes its flexible column against its own content and the
      // columns drift apart (the bug this grid exists to prevent). The track's
      // min-width is also what makes a narrow container scroll horizontally
      // instead of crushing the columns.
      block {
        min-width: trackMin

        // Sticky header
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
            padding: spacing.2
            layout: horizontal, align: center, justify: center
            Checkbox(label: "", checked: allSelected) {
              on change(isChecked): { if isChecked { selectAllRows() } else { clearSelection() } }
            }
          }

          each pinnedColumns as col {
            block {
              padding: spacing.2
              grow: true
              min-width: col._min
              max-width: col._max
              position: "sticky"
              left: 0px
              z-index: 5
              background: semantic.surface-raised
              cursor: col._col.sortable ? "pointer" : "default"
              data-grid-col: col._col.key
              on click: col._col.sortable ? toggleSortCol(col._col.key) : {}
              @slot("header", col._col)
              block {
                visibility: !hasSlot("header")
                layout: horizontal, gap: spacing.1, align: center
                text(col._col.header != null ? col._col.header : (col._col.label != null ? col._col.label : col._col.key)) {
                  style: type.label-sm
                  weight: 600
                }
              }
            }
          }

          each scrollColumns as col {
            block {
              padding: spacing.2
              grow: true
              min-width: col._min
              max-width: col._max
              cursor: col._col.sortable ? "pointer" : "default"
              data-grid-col: col._col.key
              on click: col._col.sortable ? toggleSortCol(col._col.key) : {}
              @slot("header", col._col)
              block {
                visibility: !hasSlot("header")
                layout: horizontal, gap: spacing.1, align: center
                text(col._col.header != null ? col._col.header : (col._col.label != null ? col._col.label : col._col.key)) {
                  style: type.label-sm
                  weight: 600
                }
                text(sortState.find(s => s.key == col.key) != null ? (sortState.find(s => s.key == col.key).direction == "asc" ? "\u2191" : "\u2193") : "") {
                  style: type.caption
                  color: semantic.interactive
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
            background: gridRowKind(row) != "row" ? groupBg : (selectedSet.includes(rowIdx) ? semantic.surface-raised : (striped && rowIdx % 2 == 1 ? semantic.surface : "transparent"))
            shadow: gridRowRail(row)
            opacity: gridRowOpacity(row)
            cursor: selection != "none" ? "pointer" : "default"
            on click: clickRow(row, rowIdx)
            data-grid-row: gridRowKind(row) == "row" ? "body" : gridRowKind(row)

            block {
              visibility: selection == "multi"
              width: 40px
              padding: spacing.2
              layout: horizontal, align: center, justify: center
              Checkbox(label: "", checked: selectedSet.includes(rowIdx)) {
                on change(isChecked): selectRow(rowIdx)
              }
            }

            each pinnedColumns as col {
              block {
                padding: spacing.2
                grow: true
                min-width: col._min
                max-width: col._max
                data-grid-col: col._col.key
                position: "sticky"
                left: 0px
                z-index: 2
                background: gridRowKind(row) != "row" ? groupBg : pinBg
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
                  aria-label: "Toggle group"
                  on click: toggleGroup(row._key)
                  text(gridGroupIsOpen(openGroups, row._key) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    color: semantic.text-secondary
                  }
                }
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

            each scrollColumns as col, colIdx {
              block {
                padding: spacing.2
                grow: true
                min-width: col._min
                max-width: col._max
                background: focusedRow == rowIdx && focusedCol == colIdx ? "rgba(59,130,246,0.08)" : "transparent"
                data-grid-col: col._col.key
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
                  aria-label: "Toggle group"
                  on click: toggleGroup(row._key)
                  text(gridGroupIsOpen(openGroups, row._key) ? "\u25be" : "\u25b8") {
                    style: type.label-xs
                    color: semantic.text-secondary
                  }
                }
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
