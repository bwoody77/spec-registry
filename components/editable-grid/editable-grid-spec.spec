// ─── Cell key helpers ───────────────────────────────────────────────────────

fn _buildCellKey(rowId: any, colKey: string) -> string {
  return toString(rowId) + "::" + colKey
}

fn _splitCellKey(ck: string) -> list {
  let i = indexOf(ck, "::")
  return [slice(ck, 0, i), slice(ck, i + 2)]
}

// ─── TSV Parsing ────────────────────────────────────────────────────────────

fn _parseTSV(text: string) -> list {
  return split(text, "\n")
    |> filter(line => length(line) > 0)
    |> map(line => split(line, "\t"))
}

// ─── Sort toggle ────────────────────────────────────────────────────────────

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

// ─── Validation ─────────────────────────────────────────────────────────────

fn validateCell(value: any, column: any) -> any {
  if column.required == true && (value == null || value == "") {
    let label = column.header ?? column.key
    return label + " is required"
  }
  return null
}

// ─── Row changes ────────────────────────────────────────────────────────────

fn getRowChanges(rowId: string, editedValues: list) -> any {
  let prefix = rowId + "::"
  let entries = editedValues |> filter(e => startsWith(e.key, prefix))
  if length(entries) > 0 { return entries }
  return null
}

// ─── Display value ──────────────────────────────────────────────────────────

fn getCellDisplayValue(rowIdx: number, colIdx: number, visibleColumns: list, rows: list, rowIdField: string, editedValues: list) -> string {
  if rowIdx < 0 || rowIdx >= length(rows) { return "" }
  if colIdx < 0 || colIdx >= length(visibleColumns) { return "" }
  let row = rows[rowIdx]
  let col = visibleColumns[colIdx]
  let ck = _buildCellKey(row[rowIdField], col.key)
  let edited = editedValues |> find(e => e.key == ck)
  if edited != null { return toString(edited.value) }
  if row[col.key] != null { return toString(row[col.key]) }
  return ""
}

// ─── Undo stack ─────────────────────────────────────────────────────────────

fn pushUndoEntry(stack: list, entry: any, maxDepth: number) -> list {
  let newStack = concat(stack, [entry])
  if length(newStack) > maxDepth {
    return slice(newStack, length(newStack) - maxDepth)
  }
  return newStack
}

// ─── Apply undo / redo ──────────────────────────────────────────────────────

fn applyUndoChanges(direction: string, changes: list, editedValues: list, dirtyCells: list, rows: list, rowIdField: string) -> any {
  let ev = editedValues
  let dc = dirtyCells
  for change in changes {
    let targetValue = direction == "undo" ? change.oldValue : change.newValue
    let parts = _splitCellKey(change.key)
    let rowId = parts[0]
    let colKey = parts[1]
    let row = rows |> find(r => toString(r[rowIdField]) == rowId)
    let originalStr = ""
    if row != null && row[colKey] != null { originalStr = toString(row[colKey]) }
    if targetValue == originalStr {
      ev = ev |> filter(e => e.key != change.key)
      dc = dc |> filter(k => k != change.key)
    } else {
      ev = concat(ev |> filter(e => e.key != change.key), [{ key: change.key, value: targetValue }])
      if !includes(dc, change.key) {
        dc = concat(dc, [change.key])
      }
    }
  }
  return { editedValues: ev, dirtyCells: dc }
}

// ─── Compute paste ──────────────────────────────────────────────────────────

fn computePaste(text: string, activeRow: number, activeCol: number, visibleColumns: list, rows: list, rowIdField: string, editedValues: list, dirtyCells: list) -> any {
  let grid = _parseTSV(text)
  let ev = editedValues
  let dc = dirtyCells
  let undoChanges = []

  for gridRow, r in grid {
    let rowIdx = activeRow + r
    if rowIdx < length(rows) {
      let row = rows[rowIdx]
      let rowId = toString(row[rowIdField])
      let colOffset = 0
      for cell, c in gridRow {
        let targetCol = activeCol + colOffset
        // Skip non-editable columns
        for _ in range(0, length(visibleColumns)) {
          if targetCol < length(visibleColumns) && visibleColumns[targetCol].editable == false {
            colOffset = colOffset + 1
            targetCol = activeCol + colOffset
          }
        }
        if targetCol < length(visibleColumns) {
          let col = visibleColumns[targetCol]
          let ck = _buildCellKey(rowId, col.key)
          let newValue = cell
          let originalStr = ""
          if row[col.key] != null { originalStr = toString(row[col.key]) }
          let existing = ev |> find(e => e.key == ck)
          let oldValue = existing != null ? existing.value : originalStr
          if oldValue != newValue {
            undoChanges = concat(undoChanges, [{ key: ck, oldValue: oldValue, newValue: newValue }])
            if newValue == originalStr {
              ev = ev |> filter(e => e.key != ck)
              dc = dc |> filter(k => k != ck)
            } else {
              ev = concat(ev |> filter(e => e.key != ck), [{ key: ck, value: newValue }])
              if !includes(dc, ck) {
                dc = concat(dc, [ck])
              }
            }
          }
          colOffset = colOffset + 1
        }
      }
    }
  }
  return { editedValues: ev, dirtyCells: dc, undoChanges: undoChanges }
}

// ─── Fill down ──────────────────────────────────────────────────────────────

fn computeFillDown(activeRow: number, activeCol: number, visibleColumns: list, rows: list, rowIdField: string, editedValues: list, dirtyCells: list) -> any {
  if activeCol < 0 || activeCol >= length(visibleColumns) {
    return { editedValues: editedValues, dirtyCells: dirtyCells, undoChanges: [] }
  }
  if activeRow < 0 || activeRow >= length(rows) {
    return { editedValues: editedValues, dirtyCells: dirtyCells, undoChanges: [] }
  }
  let col = visibleColumns[activeCol]
  let sourceRow = rows[activeRow]
  let sourceRowId = toString(sourceRow[rowIdField])
  let sourceCk = _buildCellKey(sourceRowId, col.key)
  let sourceEdited = editedValues |> find(e => e.key == sourceCk)
  let sourceValue = ""
  if sourceEdited != null {
    sourceValue = sourceEdited.value
  } else if sourceRow[col.key] != null {
    sourceValue = toString(sourceRow[col.key])
  }

  let ev = editedValues
  let dc = dirtyCells
  let undoChanges = []

  for r in range(activeRow + 1, length(rows)) {
    let row = rows[r]
    let rowId = toString(row[rowIdField])
    let ck = _buildCellKey(rowId, col.key)
    let originalStr = ""
    if row[col.key] != null { originalStr = toString(row[col.key]) }
    let existing = ev |> find(e => e.key == ck)
    let oldValue = existing != null ? existing.value : originalStr
    if oldValue != sourceValue {
      undoChanges = concat(undoChanges, [{ key: ck, oldValue: oldValue, newValue: sourceValue }])
      if sourceValue == originalStr {
        ev = ev |> filter(e => e.key != ck)
        dc = dc |> filter(k => k != ck)
      } else {
        ev = concat(ev |> filter(e => e.key != ck), [{ key: ck, value: sourceValue }])
        if !includes(dc, ck) {
          dc = concat(dc, [ck])
        }
      }
    }
  }
  return { editedValues: ev, dirtyCells: dc, undoChanges: undoChanges }
}

// ─── Build changeset from edits ─────────────────────────────────────────────

fn buildChangesetFromEdits(editedValues: list, dirtyCells: list, rows: list, rowIdField: string) -> any {
  // Collect distinct rowIds touched by dirty cells
  let rowIds = []
  for ck in dirtyCells {
    let rid = _splitCellKey(ck)[0]
    if !includes(rowIds, rid) {
      rowIds = concat(rowIds, [rid])
    }
  }

  let modified = rowIds |> map(rowId => {
    let row = rows |> find(r => toString(r[rowIdField]) == rowId)
    let myCells = dirtyCells |> filter(ck => _splitCellKey(ck)[0] == rowId)
    let entries = myCells |> map(ck => {
      let colKey = _splitCellKey(ck)[1]
      let edited = editedValues |> find(e => e.key == ck)
      let originalStr = ""
      if row != null && row[colKey] != null { originalStr = toString(row[colKey]) }
      let newVal = edited != null ? edited.value : ""
      return { colKey: colKey, old: originalStr, new: newVal }
    })
    return { rowId: rowId, changes: entries }
  })

  return { modified: modified, added: [], deleted: [] }
}

component EditableGrid(
  rowIdField: string = "id",
  activation: string = "enter",
  saveMode: string = "batch",
  undoDepth: number = 50
) extends DataGrid {
  @state {
    activeRow: 0
    activeCol: 0
    editing: false
    editValue: ""
    dirtyCells: []
    editedValues: []
    focusTrigger: false
    justCommitted: false
    undoStack: []
    redoStack: []
    validationErrors: []
  }

  @computed {
    // Override: editable grid emits sort event, rows pre-sorted by caller
    processedRows: rows
    activeRowData: processedRows[activeRow]
    activeColDef: visibleColumns[activeCol]
    cellKey: activeRowData != null && activeColDef != null ? (activeRowData[rowIdField] + "::" + activeColDef.key) : ""
    hasDirty: dirtyCells.length > 0
    canUndo: undoStack.length > 0
    canRedo: redoStack.length > 0
    hasErrors: validationErrors.length > 0
    changeset: buildChangesetFromEdits(editedValues, dirtyCells, processedRows, rowIdField)
    isSelectEditing: editing == true && activeColDef != null && activeColDef.type == "select"
    selectOptions: isSelectEditing && activeColDef.options != null ? activeColDef.options : []
  }

  @actions {
    // Override navigation actions to commit before moving
    moveUp() {
      if activeRow > 0 {
        checkRowBlur(activeRow)
        editing = false
        justCommitted = false
        activeRow = activeRow - 1
        focusTrigger = false
      }
    }
    moveDown() {
      if activeRow < processedRows.length - 1 {
        checkRowBlur(activeRow)
        editing = false
        justCommitted = false
        activeRow = activeRow + 1
        focusTrigger = false
      }
    }
    moveLeft() {
      if activeCol > 0 {
        editing = false
        justCommitted = false
        activeCol = activeCol - 1
        focusTrigger = false
      }
    }
    moveRight() {
      if activeCol < visibleColumns.length - 1 {
        editing = false
        justCommitted = false
        activeCol = activeCol + 1
        focusTrigger = false
      }
    }

    // Override toggleSort to use shared utility
    toggleSort(colKey) {
      sortState = toggleSortState(sortState, colKey)
      emit("sort", sortState)
    }

    activateEdit() {
      if activeRowData != null && activeColDef != null {
        let ck = activeRowData[rowIdField] + "::" + activeColDef.key
        let prev = editedValues.find(e => e.key == ck)
        editValue = prev != null ? prev.value : (activeRowData[activeColDef.key] != null ? activeRowData[activeColDef.key] + "" : "")
        editing = true
        focusTrigger = true
      }
    }
    setEditValue(v) { editValue = v }
    selectOption(val) {
      editValue = val
      commitEdit()
    }
    commitEdit() {
      if editing == true && activeRowData != null && activeColDef != null {
        let ck = activeRowData[rowIdField] + "::" + activeColDef.key
        let originalValue = activeRowData[activeColDef.key]
        let originalStr = originalValue != null ? originalValue + "" : ""
        let prev = editedValues.find(e => e.key == ck)
        let currentValue = prev != null ? prev.value : originalStr
        if currentValue != editValue {
          // Push undo entry
          undoStack = pushUndoEntry(undoStack, {changes: [{key: ck, oldValue: currentValue, newValue: editValue}]}, undoDepth)
          redoStack = []

          if originalStr == editValue {
            dirtyCells = dirtyCells.filter(k => k != ck)
            editedValues = editedValues.filter(e => e.key != ck)
          } else {
            if dirtyCells.includes(ck) == false {
              dirtyCells = dirtyCells.concat([ck])
            }
            editedValues = editedValues.filter(e => e.key != ck).concat([{key: ck, value: editValue}])
          }

          // Validate
          let err = validateCell(editValue, activeColDef)
          if err != null {
            validationErrors = validationErrors.filter(e => e.key != ck).concat([{key: ck, message: err}])
          } else {
            validationErrors = validationErrors.filter(e => e.key != ck)
          }

          emit("cellEdit", activeRowData[rowIdField], activeColDef.key, editValue, originalValue)

          // Save mode emits
          if saveMode == "auto" {
            emit("cellSave", activeRowData[rowIdField], activeColDef.key, editValue)
          }
        }
        editing = false
        justCommitted = true
        focusTrigger = false
      }
    }
    cancelEdit() {
      editing = false
      justCommitted = true
      focusTrigger = false
    }
    commitAndMoveDown() {
      commitEdit()
      moveDown()
    }
    commitAndMoveRight() {
      commitEdit()
      moveRight()
    }

    // Undo / Redo
    doUndo() {
      if undoStack.length > 0 {
        let entry = undoStack[undoStack.length - 1]
        undoStack = undoStack.slice(0, undoStack.length - 1)
        let result = applyUndoChanges('undo', entry.changes, editedValues, dirtyCells, processedRows, rowIdField)
        editedValues = result.editedValues
        dirtyCells = result.dirtyCells
        redoStack = redoStack.concat([entry])
      }
    }
    doRedo() {
      if redoStack.length > 0 {
        let entry = redoStack[redoStack.length - 1]
        redoStack = redoStack.slice(0, redoStack.length - 1)
        let result = applyUndoChanges('redo', entry.changes, editedValues, dirtyCells, processedRows, rowIdField)
        editedValues = result.editedValues
        dirtyCells = result.dirtyCells
        undoStack = undoStack.concat([entry])
      }
    }

    // Clipboard
    copyCell() {
      if activeRowData != null && activeColDef != null {
        let val = getCellDisplayValue(activeRow, activeCol, visibleColumns, processedRows, rowIdField, editedValues)
        writeClipboard(val)
      }
    }
    pasteClipboard() {
      let text = await readClipboard()
      let result = computePaste(text, activeRow, activeCol, visibleColumns, processedRows, rowIdField, editedValues, dirtyCells)
      editedValues = result.editedValues
      dirtyCells = result.dirtyCells
      if result.undoChanges.length > 0 {
        undoStack = pushUndoEntry(undoStack, {changes: result.undoChanges}, undoDepth)
        redoStack = []
      }
    }

    // Fill Down
    fillDown() {
      let result = computeFillDown(activeRow, activeCol, visibleColumns, processedRows, rowIdField, editedValues, dirtyCells)
      editedValues = result.editedValues
      dirtyCells = result.dirtyCells
      if result.undoChanges.length > 0 {
        undoStack = pushUndoEntry(undoStack, {changes: result.undoChanges}, undoDepth)
        redoStack = []
      }
    }

    // Row-blur save mode
    checkRowBlur(prevRowIdx) {
      if saveMode == "row-blur" && prevRowIdx >= 0 && prevRowIdx < processedRows.length {
        let rowData = processedRows[prevRowIdx]
        if rowData != null {
          let rowId = rowData[rowIdField] + ""
          let changes = getRowChanges(rowId, editedValues)
          if changes != null {
            emit("rowSave", rowId, changes)
          }
        }
      }
    }

    clickCell(rowIdx, colIdx) {
      if activeRow != rowIdx || activeCol != colIdx || editing == false {
        if editing == true { commitEdit() }
        checkRowBlur(activeRow)
        justCommitted = false
        activeRow = rowIdx
        activeCol = colIdx
        if activation == "click" {
          activateEdit()
        }
      }
    }
    dblClickCell(rowIdx, colIdx) {
      if activeRow != rowIdx || activeCol != colIdx || editing == false {
        if editing == true { commitEdit() }
        checkRowBlur(activeRow)
        justCommitted = false
        activeRow = rowIdx
        activeCol = colIdx
        if activation == "dblclick" {
          activateEdit()
        }
      }
    }
  }

  block {
    height: height != "" ? height : "auto"

    // Grid container
    block {
      border: borders.default
      border-radius: radius.md
      overflow: hidden
      height: 100%
      role: "grid"
      tabindex: "0"

      on key-down(event): {
        // Ctrl/Cmd shortcuts — only when not editing
        if editing == false && (event.ctrlKey == true || event.metaKey == true) {
          if event.key == "z" && event.shiftKey != true {
            event.preventDefault()
            doUndo()
          }
          if (event.key == "Z" && event.shiftKey == true) || event.key == "y" {
            event.preventDefault()
            doRedo()
          }
          if event.key == "c" {
            copyCell()
          }
          if event.key == "v" {
            event.preventDefault()
            pasteClipboard()
          }
          if event.key == "d" {
            event.preventDefault()
            fillDown()
          }
        }

        // Navigation keys
        if editing == false && justCommitted == false && event.ctrlKey != true && event.metaKey != true {
          match event.key {
            "ArrowDown" -> moveDown(),
            "ArrowUp" -> moveUp(),
            "ArrowLeft" -> moveLeft(),
            "ArrowRight" -> moveRight(),
            "Enter" -> activateEdit(),
            "F2" -> activateEdit(),
            _ -> {}
          }
        }
      }

      block {
        overflow: auto
        height: 100%

        // Header
        block {
          layout: horizontal
          background: semantic.surface
          border-bottom: borders.strong
          position: "sticky"
          top: 0px
          z-index: 2

          each visibleColumns as col {
            block {
              padding: spacing.2
              min-width: 100px
              grow: true
              cursor: col.sortable ? "pointer" : "default"
              on click: col.sortable ? toggleSort(col.key) : {}
              layout: horizontal, gap: spacing.1, align: center

              text(col.header != null ? col.header : col.key) {
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

        // Body rows
        each processedRows as row, rowIdx {
          block {
            layout: horizontal
            border-bottom: borders.subtle
            background: selectedSet.includes(rowIdx) ? semantic.surface-raised : "transparent"

            each visibleColumns as col, colIdx {
              block {
                padding: spacing.2
                min-width: 100px
                grow: true
                position: "relative"
                border: validationErrors.find(e => e.key == row[rowIdField] + "::" + col.key) != null ? "2px solid #ef4444" : ((rowIdx == activeRow && colIdx == activeCol && editing == false) ? "2px solid #3b82f6" : "2px solid transparent")
                background: dirtyCells.includes(row[rowIdField] + "::" + col.key) ? "rgba(245,158,11,0.08)" : "transparent"
                on click: clickCell(rowIdx, colIdx)
                on dbl-click: dblClickCell(rowIdx, colIdx)
                on key-down(event): {
                  if editing == true && rowIdx == activeRow && colIdx == activeCol {
                    match event.key {
                      "Enter" -> commitEdit(),
                      "Escape" -> cancelEdit(),
                      _ -> {}
                    }
                  }
                }

                // Editing mode — raw textInput for non-select columns
                block {
                  visibility: rowIdx == activeRow && colIdx == activeCol && editing == true && col.type != "select"
                  position: "absolute"
                  top: 0px
                  left: 0px
                  right: 0px
                  bottom: 0px
                  z-index: 1
                  background: semantic.surface
                  textInput(editValue) {
                    placeholder: col.header != null ? col.header : col.key
                    border: "none"
                    background: "transparent"
                    width: 100%
                    height: 100%
                    focus: focusTrigger
                  }
                }

                // Editing mode — show current value for select columns (dropdown is outside)
                block {
                  visibility: rowIdx == activeRow && colIdx == activeCol && editing == true && col.type == "select"
                  text(editValue) {
                    style: type.body-sm
                    color: semantic.interactive
                    weight: 600
                  }
                }

                // Display mode
                block {
                  visibility: rowIdx != activeRow || colIdx != activeCol || editing == false
                  text(editedValues.find(e => e.key == row[rowIdField] + "::" + col.key) != null ? editedValues.find(e => e.key == row[rowIdField] + "::" + col.key).value : (row[col.key] != null ? row[col.key] + "" : "")) {
                    style: type.body-sm
                    color: semantic.text-primary
                  }
                }

                // Dirty indicator (yellow triangle, top-left)
                block {
                  visibility: dirtyCells.includes(row[rowIdField] + "::" + col.key)
                  position: "absolute"
                  top: 0px
                  left: 0px
                  width: 0px
                  height: 0px
                  border-left: "6px solid #f59e0b"
                  border-bottom: "6px solid transparent"
                }

                // Validation error indicator (red triangle, bottom-right)
                block {
                  visibility: validationErrors.find(e => e.key == row[rowIdField] + "::" + col.key) != null
                  position: "absolute"
                  bottom: 0px
                  right: 0px
                  width: 0px
                  height: 0px
                  border-right: "6px solid #ef4444"
                  border-top: "6px solid transparent"
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
          text('No rows') { style: type.body-md, color: semantic.text-tertiary }
        }
      }
    }

    // Select overlay
    overlay(visible: isSelectEditing, backdrop: "scrim", anchor: "parent") {
      on dismiss: cancelEdit()

      block {
        min-width: 180px
        max-height: 200px
        overflow: auto
        background: semantic.surface
        border: borders.default
        border-radius: radius.md
        shadow: elevation.floating
        padding: spacing.1
        layout: vertical

        each selectOptions as opt {
          block {
            padding: spacing.2
            padding-left: spacing.3
            padding-right: spacing.3
            border-radius: radius.sm
            cursor: "pointer"
            background: opt.value == editValue ? semantic.interactive : "transparent"
            on hover { background: opt.value == editValue ? semantic.interactive : semantic.surface-raised }
            on click: selectOption(opt.value)

            text(opt.label) {
              style: type.body-md
              color: opt.value == editValue ? semantic.surface : semantic.text-primary
            }
          }
        }
      }
    }
  }
}
