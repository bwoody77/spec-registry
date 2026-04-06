/**
 * Pure utility functions for the EditableGridSpec component (.spec version).
 * Used via @extern from editable-grid-spec.spec.
 *
 * Data shapes (matching Spec arrays-of-objects):
 *   editedValues: Array<{ key: string, value: string }>
 *   dirtyCells:   string[]
 *   undoEntry:    { changes: Array<{ key: string, oldValue: string, newValue: string }> }
 *   validationError: { key: string, message: string }
 */
import { parseTSV, splitCellKey, buildCellKey } from './editable-grid-utils.js';
// ─── Undo / Redo ────────────────────────────────────────────────────────────
/**
 * Apply undo or redo changes to editedValues and dirtyCells.
 * direction: "undo" picks oldValue, "redo" picks newValue.
 */
export function applyUndoChanges(direction, changes, editedValues, dirtyCells, rows, rowIdField) {
    let ev = [...editedValues];
    let dc = [...dirtyCells];
    for (const change of changes) {
        const targetValue = direction === 'undo' ? change.oldValue : change.newValue;
        const [rowId, colKey] = splitCellKey(change.key);
        // Find original value from row data
        const row = rows.find(r => String(r[rowIdField]) === rowId);
        const originalStr = row ? (row[colKey] != null ? String(row[colKey]) : '') : '';
        if (targetValue === originalStr) {
            // Reverted to original — remove from dirty/edited
            ev = ev.filter(e => e.key !== change.key);
            dc = dc.filter(k => k !== change.key);
        }
        else {
            // Upsert edited value
            ev = ev.filter(e => e.key !== change.key).concat([{ key: change.key, value: targetValue }]);
            if (!dc.includes(change.key)) {
                dc = dc.concat([change.key]);
            }
        }
    }
    return { editedValues: ev, dirtyCells: dc };
}
// ─── Clipboard Paste ────────────────────────────────────────────────────────
/**
 * Compute the result of pasting TSV text starting at (activeRow, activeCol).
 * Skips non-editable columns. Returns updated state + undo changes.
 */
export function computePaste(text, activeRow, activeCol, visibleColumns, rows, rowIdField, editedValues, dirtyCells) {
    const grid = parseTSV(text);
    let ev = [...editedValues];
    let dc = [...dirtyCells];
    const undoChanges = [];
    for (let r = 0; r < grid.length; r++) {
        const rowIdx = activeRow + r;
        if (rowIdx >= rows.length)
            break;
        const row = rows[rowIdx];
        const rowId = String(row[rowIdField]);
        let colOffset = 0;
        for (let c = 0; c < grid[r].length; c++) {
            // Find the next editable column
            let targetCol = activeCol + colOffset;
            while (targetCol < visibleColumns.length && visibleColumns[targetCol].editable === false) {
                colOffset++;
                targetCol = activeCol + colOffset;
            }
            if (targetCol >= visibleColumns.length)
                break;
            const col = visibleColumns[targetCol];
            const ck = buildCellKey(rowId, col.key);
            const newValue = grid[r][c];
            const originalStr = row[col.key] != null ? String(row[col.key]) : '';
            const existing = ev.find(e => e.key === ck);
            const oldValue = existing ? existing.value : originalStr;
            if (oldValue !== newValue) {
                undoChanges.push({ key: ck, oldValue, newValue });
                if (newValue === originalStr) {
                    ev = ev.filter(e => e.key !== ck);
                    dc = dc.filter(k => k !== ck);
                }
                else {
                    ev = ev.filter(e => e.key !== ck).concat([{ key: ck, value: newValue }]);
                    if (!dc.includes(ck)) {
                        dc = dc.concat([ck]);
                    }
                }
            }
            colOffset++;
        }
    }
    return { editedValues: ev, dirtyCells: dc, undoChanges };
}
// ─── Fill Down ──────────────────────────────────────────────────────────────
/**
 * Fill the active cell's value down to all rows below it in the same column.
 */
export function computeFillDown(activeRow, activeCol, visibleColumns, rows, rowIdField, editedValues, dirtyCells) {
    if (activeCol < 0 || activeCol >= visibleColumns.length) {
        return { editedValues, dirtyCells, undoChanges: [] };
    }
    const col = visibleColumns[activeCol];
    if (activeRow < 0 || activeRow >= rows.length) {
        return { editedValues, dirtyCells, undoChanges: [] };
    }
    // Get source value (from editedValues or original row data)
    const sourceRow = rows[activeRow];
    const sourceRowId = String(sourceRow[rowIdField]);
    const sourceCk = buildCellKey(sourceRowId, col.key);
    const sourceEdited = editedValues.find(e => e.key === sourceCk);
    const sourceValue = sourceEdited ? sourceEdited.value : (sourceRow[col.key] != null ? String(sourceRow[col.key]) : '');
    let ev = [...editedValues];
    let dc = [...dirtyCells];
    const undoChanges = [];
    for (let r = activeRow + 1; r < rows.length; r++) {
        const row = rows[r];
        const rowId = String(row[rowIdField]);
        const ck = buildCellKey(rowId, col.key);
        const originalStr = row[col.key] != null ? String(row[col.key]) : '';
        const existing = ev.find(e => e.key === ck);
        const oldValue = existing ? existing.value : originalStr;
        if (oldValue !== sourceValue) {
            undoChanges.push({ key: ck, oldValue, newValue: sourceValue });
            if (sourceValue === originalStr) {
                ev = ev.filter(e => e.key !== ck);
                dc = dc.filter(k => k !== ck);
            }
            else {
                ev = ev.filter(e => e.key !== ck).concat([{ key: ck, value: sourceValue }]);
                if (!dc.includes(ck)) {
                    dc = dc.concat([ck]);
                }
            }
        }
    }
    return { editedValues: ev, dirtyCells: dc, undoChanges };
}
// ─── Changeset ──────────────────────────────────────────────────────────────
/**
 * Build a changeset from editedValues and dirtyCells.
 * Groups by row, provides old/new for each field.
 */
export function buildChangesetFromEdits(editedValues, dirtyCells, rows, rowIdField) {
    const rowMap = new Map();
    for (const ck of dirtyCells) {
        const [rowId, colKey] = splitCellKey(ck);
        const edited = editedValues.find(e => e.key === ck);
        if (!edited)
            continue;
        const row = rows.find(r => String(r[rowIdField]) === rowId);
        const originalStr = row ? (row[colKey] != null ? String(row[colKey]) : '') : '';
        if (!rowMap.has(rowId))
            rowMap.set(rowId, {});
        rowMap.get(rowId)[colKey] = { old: originalStr, new: edited.value };
    }
    const modified = [];
    for (const [rowId, changes] of rowMap) {
        modified.push({ rowId, changes });
    }
    return { modified, added: [], deleted: [] };
}
// ─── Validation ─────────────────────────────────────────────────────────────
/**
 * Validate a cell value against column constraints.
 * Returns error message string or null if valid.
 */
export function validateCell(value, column) {
    if (column.required && (value == null || value === '')) {
        const label = column.header ?? column.key;
        return `${label} is required`;
    }
    if (typeof column.validate === 'function') {
        return column.validate(value);
    }
    return null;
}
// ─── Row Changes ────────────────────────────────────────────────────────────
/**
 * Get all edited entries for a given row, or null if none.
 */
export function getRowChanges(rowId, editedValues) {
    const prefix = rowId + '::';
    const entries = editedValues.filter(e => e.key.startsWith(prefix));
    return entries.length > 0 ? entries : null;
}
// ─── Display Value ──────────────────────────────────────────────────────────
/**
 * Get the display value for a cell (from editedValues overlay or original row data).
 */
export function getCellDisplayValue(rowIdx, colIdx, visibleColumns, rows, rowIdField, editedValues) {
    if (rowIdx < 0 || rowIdx >= rows.length || colIdx < 0 || colIdx >= visibleColumns.length)
        return '';
    const row = rows[rowIdx];
    const col = visibleColumns[colIdx];
    const ck = buildCellKey(String(row[rowIdField]), col.key);
    const edited = editedValues.find(e => e.key === ck);
    if (edited)
        return edited.value;
    return row[col.key] != null ? String(row[col.key]) : '';
}
// ─── Undo Stack ─────────────────────────────────────────────────────────────
/**
 * Push an entry onto an undo/redo stack, enforcing max depth.
 * Returns the new stack array.
 */
export function pushUndoEntry(stack, entry, maxDepth) {
    const newStack = stack.concat([entry]);
    if (newStack.length > maxDepth) {
        return newStack.slice(newStack.length - maxDepth);
    }
    return newStack;
}
//# sourceMappingURL=editable-grid-spec-utils.js.map