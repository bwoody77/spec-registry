@extern { applyUndoChanges, computePaste, computeFillDown, buildChangesetFromEdits, validateCell, getRowChanges, getCellDisplayValue, pushUndoEntry } from "@spec/components/editable-grid-spec-utils.js"
@extern { toggleSortState } from "@spec/components/grid-spec-utils.js"

component EditableGridSpec(
  rowIdField: string = "id",
  activation: string = "enter",
  saveMode: string = "batch",
  undoDepth: number = 50
) extends DataGridSpec {
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

  // Wrapper with position:relative so the select overlay can escape the scroll container
  block {
    position: "relative"
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
          border-bottom: borders.heavy
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

    // Select overlay — rendered OUTSIDE the grid scroll container to avoid clipping
    block {
      visibility: isSelectEditing
      position: "absolute"
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 10
      background: "rgba(0,0,0,0.15)"
      on click: cancelEdit()

      // Options panel
      block {
        position: "absolute"
        top: 50%
        left: 50%
        transform: "translate(-50%, -50%)"
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
