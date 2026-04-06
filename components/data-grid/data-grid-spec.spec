@extern { toggleSortState, applySortAndFilter } from "@spec/components/grid-spec-utils.js"

component DataGridSpec(
  columns: array,
  rows: array,
  selection: string = "none",
  selected: array = [],
  sort: array = [],
  height: string = "",
  striped: boolean = false,
) {
  @state {
    sortState: sort
    selectedSet: selected
    filters: []
    focusedRow: 0
    focusedCol: 0
  }

  @computed {
    visibleColumns: columns.filter(c => c.visible != false)
    processedRows: applySortAndFilter(rows, sortState, filters)
    hasFilters: columns.some(c => c.filterable == true)
    allSelected: selectedSet.length == processedRows.length && processedRows.length > 0
  }

  @actions {
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

      // Sticky header
      block {
        layout: horizontal
        background: semantic.surface-raised
        border-bottom: borders.heavy
        position: "sticky"
        top: 0px
        z-index: 2

        block {
          visibility: selection == "multi"
          width: 40px
          padding: spacing.2
          layout: horizontal, align: center, justify: center
          Checkbox(label: "", checked: allSelected) {
            on change(isChecked): { if isChecked { selectAllRows() } else { clearSelection() } }
          }
        }

        each visibleColumns as col {
          block {
            padding: spacing.2
            grow: true
            min-width: 100px
            cursor: col.sortable ? "pointer" : "default"
            on click: col.sortable ? toggleSortCol(col.key) : {}
            layout: horizontal, gap: spacing.1, align: center
            text(col.header != null ? col.header : (col.label != null ? col.label : col.key)) {
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

      // Filter row (only when any column is filterable)
      block {
        visibility: hasFilters
        layout: horizontal
        background: semantic.surface
        border-bottom: borders.subtle
        block {
          visibility: selection == "multi"
          width: 40px
        }
        each visibleColumns as col {
          block {
            padding: spacing.1
            grow: true
            min-width: 100px
            block {
              visibility: col.filterable == true
              textInput(filters.find(f => f.key == col.key) != null ? filters.find(f => f.key == col.key).value : "") {
                placeholder: "Filter\u2026"
                border: borders.default
                border-radius: radius.sm
                width: 100%
                on change(v): setFilter(col.key, v)
              }
            }
          }
        }
      }

      // Body rows
      each processedRows as row, rowIdx {
        block {
          layout: horizontal
          border-bottom: borders.subtle
          background: selectedSet.includes(rowIdx) ? semantic.surface-raised : (striped && rowIdx % 2 == 1 ? semantic.surface : "transparent")
          cursor: selection != "none" ? "pointer" : "default"
          on click: clickRow(row, rowIdx)
          on hover { background: semantic.surface-raised }

          block {
            visibility: selection == "multi"
            width: 40px
            padding: spacing.2
            layout: horizontal, align: center, justify: center
            Checkbox(label: "", checked: selectedSet.includes(rowIdx)) {
              on change(isChecked): selectRow(rowIdx)
            }
          }

          each visibleColumns as col, colIdx {
            block {
              padding: spacing.2
              grow: true
              min-width: 100px
              background: focusedRow == rowIdx && focusedCol == colIdx ? "rgba(59,130,246,0.08)" : "transparent"
              @slot("cell", col, row)
              text(row[col.key] != null ? row[col.key] + "" : "") {
                style: type.body-sm
                color: semantic.text-primary
              }
            }
          }
        }
      }

      // Empty state
      block {
        visibility: processedRows.length == 0
        padding: spacing.6
        layout: horizontal, justify: center
        text("No rows") { style: type.body-md, color: semantic.text-tertiary }
      }
    }
  }
}
