/**
 * grid-window.ts — the window calculation shared by VirtualList and DataGrid.
 *
 * Lifted verbatim from virtual-list.spec's @computed block so the two cannot
 * drift. Pure: no DOM, no state, no time. Everything geometric that a browser
 * would have to tell us arrives as an argument.
 */
const EMPTY = { start: 0, end: 0, topPad: 0, botPad: 0 };
export function computeWindow(input) {
    const { scrollTop, viewportHeight, rowHeight, totalCount, overscan } = input;
    // A zero pitch would divide by zero; zero rows has no window to compute.
    // Both are ordinary states (windowing off, empty result), not errors.
    if (rowHeight <= 0 || totalCount <= 0)
        return EMPTY;
    const rawStart = scrollTop / rowHeight;
    const rawEnd = (scrollTop + viewportHeight) / rowHeight;
    // Clamped at BOTH ends: a shrinking totalCount can leave scrollTop past the
    // end of the list, and an unclamped start would invert the slice.
    const start = Math.min(totalCount, Math.max(0, Math.floor(rawStart - overscan)));
    const end = Math.max(start, Math.min(totalCount, Math.ceil(rawEnd + overscan)));
    return {
        start,
        end,
        topPad: start * rowHeight,
        botPad: (totalCount - end) * rowHeight,
    };
}
/**
 * The first slot of the window that is clear of the sticky header, as an index
 * into the rendered rows.
 *
 * ── WHY `headerH` AND `virtualTop` BOTH APPEAR, AND MOSTLY CANCEL ──────────
 * Row j sits at `virtualTop + j*rowHeight`; the header covers the viewport
 * from `scrollTop` to `scrollTop + headerH`. So j is clear once
 * `virtualTop + j*rowHeight >= scrollTop + headerH`.
 *
 * With a sticky header and no filter strip, `virtualTop == headerH` and the
 * two cancel to plain `ceil(scrollTop / rowHeight)`. Adding `headerH` WITHOUT
 * subtracting `virtualTop` overshoots by roughly one header of rows, which is
 * not merely cosmetic: overshoot past the last failed slot of a block leaves
 * that block with no message and no Retry at all — the dead end this whole
 * mechanism exists to prevent. That shipped once; hence this is a pure
 * function with tests rather than three terms inline in a DOM callback.
 *
 * Clamped into the rendered range, so a window shorter than the overscan — a
 * rowCount that shrank under a stale scrollTop — still names a real slot.
 */
export function firstVisibleSlot(input) {
    const { scrollTop, headerH, virtualTop, rowHeight, start, rendered } = input;
    if (rendered <= 0)
        return 0;
    if (rowHeight <= 0)
        return 0;
    const abs = Math.ceil((scrollTop + headerH - virtualTop) / rowHeight);
    return Math.min(Math.max(abs - start, 0), rendered - 1);
}
//# sourceMappingURL=grid-window.js.map