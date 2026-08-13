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
//# sourceMappingURL=grid-window.js.map