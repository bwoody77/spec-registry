/**
 * Shared grid utilities for Spec-language grid components.
 *
 * These are thin wrappers around the internal grid-utils primitives, exposing
 * a simple API that DataGridSpec and EditableGridSpec can call via @extern.
 */
import { toggleSort, applySortToRows, applyFilters } from './grid-utils.js';
/** Toggle a single column sort: asc → desc → none (single-column mode). */
export function toggleSortState(sortState, colKey) {
    return toggleSort(sortState, colKey, false);
}
/** Apply sort then per-column filter (filter array → filter map). */
export function applySortAndFilter(rows, sortState, filters) {
    const filterMap = {};
    for (const f of filters) {
        if (f.value)
            filterMap[f.key] = f.value;
    }
    return applyFilters(applySortToRows(rows, sortState), filterMap);
}
//# sourceMappingURL=grid-spec-utils.js.map