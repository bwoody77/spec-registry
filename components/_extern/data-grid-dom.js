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
/** Between looks for a grid root that is not in the document yet. */
export const GRID_ROOT_POLL_MS = 80;
/** Retries before a wire stops looking for its grid: ~10 s at 80ms. */
export const GRID_ROOT_POLL_LIMIT = 125;
/**
 * Hand `onRoot` this grid's `[data-grid-id]` element once it is in the
 * document, and return a cancel. Shared by the two drag wires.
 *
 * DataGrid creates both wires from @state initialisers, which run before the
 * grid's DOM exists, so the synchronous look below always misses there. Mount
 * is synchronous and stamps `data-grid-id` as it builds, so a microtask later
 * the grid is normally in place and no timer is ever armed. Only a grid that
 * arrives later than that (a container attached after mount) falls through to
 * the poll.
 *
 * The poll is BOUNDED. It used to re-arm itself until the grid appeared, with
 * nothing to stop it: a grid unmounted before its first retry polled for the
 * life of the page, and under vitest the timer outlived the test environment,
 * where `document` no longer exists — up to 52 "document is not defined …
 * caught after test environment was torn down" errors on an all-green
 * components run. So a retry also does nothing once the document is gone, and
 * a wire that never finds its grid says so and stops.
 */
export function whenGridRoot(gridId, onRoot, 
/** Names the wire in the give-up warning: 'column drag', 'group drag'. */
what) {
    let done = false;
    let timer = null;
    let retries = 0;
    function attempt() {
        const id = gridId();
        const root = id
            ? document.querySelector('[data-grid-id="' + id + '"]')
            : null;
        if (!root)
            return false;
        done = true;
        onRoot(root);
        return true;
    }
    function retry() {
        timer = null;
        // Cancelled, or the environment that owned this grid is gone — a torn-down
        // test environment deletes `document`, and `attempt()` would throw.
        if (done || typeof document === 'undefined')
            return;
        if (attempt())
            return;
        if (retries++ >= GRID_ROOT_POLL_LIMIT) {
            done = true;
            console.warn(`DataGrid: the ${what} wire never found [data-grid-id="${gridId()}"] after ` +
                `${GRID_ROOT_POLL_LIMIT} retries and stopped looking. Dragging will not work on that grid.`);
            return;
        }
        timer = setTimeout(retry, GRID_ROOT_POLL_MS);
    }
    if (typeof document === 'undefined' || !attempt())
        queueMicrotask(retry);
    return () => {
        done = true;
        if (timer != null) {
            clearTimeout(timer);
            timer = null;
        }
    };
}
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