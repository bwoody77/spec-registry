/**
 * DataGrid DOM queries, shared by the two drag wires.
 *
 * `data-grid-column-drag.ts` moves a COLUMN within its segment;
 * `data-grid-group-drag.ts` moves a whole labelled SEGMENT among its siblings.
 * They ask the same questions of the same markup, and the answers below encode
 * two bugs' worth of hard-won detail — so they live in one place rather than
 * being asked twice.
 */
/** Header cells, anywhere in the grid. */
export const HEADER_CELLS = '[data-grid-row="header"] [data-grid-col]';
/**
 * Only cells belonging to THIS grid. querySelectorAll reaches DOWN into a
 * nested DataGrid rendered in a detail slot — whose root sits inside this
 * root — and its header cells would otherwise be counted as this grid's
 * columns, polluting both the key order and segment membership. `closest()`
 * walks up, so the nearest [data-grid-id] ancestor names the owning grid.
 */
export function ownedBy(root) {
    return (el) => el.closest('[data-grid-id]') === root;
}
/**
 * A column's segment is the VALUE of the nearest [data-grid-col-seg] ancestor
 * — 'p:<run>' pinned, 's:<run>' scrolling, where <run> is a run id and NOT the
 * group label.
 *
 * By VALUE, never by container identity. gridSegmentsOf merges a run into one
 * container only when the group label is non-empty, so every UNGROUPED column
 * sits in a container of its own. Treating the container as the segment would
 * make each of them a size-1 segment, and an ungrouped grid — which is most of
 * them — would be completely undraggable while every test still passed.
 */
export function segOf(cell) {
    const holder = cell.closest('[data-grid-col-seg]');
    return holder ? holder.getAttribute('data-grid-col-seg') : null;
}
/** Header cells sharing a segment value, in document (visual) order. */
export function segmentCells(root, seg) {
    const mine = ownedBy(root);
    return Array.from(root.querySelectorAll(HEADER_CELLS)).filter((el) => el.offsetParent !== null && mine(el) && segOf(el) === seg);
}
/**
 * Header cells of a column, in THIS grid only.
 *
 * Exported for the test suite: this and `bodyCellsFor` are the DOM-WRITING
 * queries — `buildColumnGhost` clones what they return into the drag image and
 * `setSourceHidden` / `translateCol` write inline styles onto it — so the
 * `ownedBy` filter matters more here than anywhere else, and asserting a
 * replica of the expression in a test would not have caught its absence.
 */
export function headerCellsFor(root, key) {
    return Array.from(root.querySelectorAll('[data-grid-row="header"] [data-grid-col="' + key + '"]')).filter(ownedBy(root));
}
/** Body cells of a column: same attribute, anywhere EXCEPT the header row. */
export function bodyCellsFor(root, key) {
    return Array.from(root.querySelectorAll('[data-grid-col="' + key + '"]'))
        .filter((el) => el.closest('[data-grid-row="header"]') === null)
        .filter(ownedBy(root));
}
//# sourceMappingURL=data-grid-dom.js.map