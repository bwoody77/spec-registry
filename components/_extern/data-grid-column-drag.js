/**
 * DataGridSpec per-instance column-drag wire-up.
 *
 * Lets the user drag a column HEADER cell left/right to reorder columns.
 * Designed for grids that share a page — no module-level singletons, so two
 * (or more) DataGridSpec instances never clobber each other. Each call to
 * `wireColumnDrag` creates its own closure-local session, observer, timer and
 * slot element; there is deliberately NO module-level `let session`.
 *
 * Spec usage (DataGridSpec @state, declared AFTER the @action it references):
 *
 *   _gridId:      genGridId()
 *   _colDragInit: wireColumnDrag(_gridId, onColDragReorder, reorderableColumns)
 *
 * The grid ROOT block must carry `data-grid-id: _gridId`.
 * Header cells are `[data-grid-row="header"] [data-grid-col="<key>"]`.
 * Body cells are `[data-grid-col="<key>"]` outside `[data-grid-row="header"]`.
 *
 * `onReorder(newOrder: string[])` is called with the full new VISIBLE column
 * key order when a real drag completes. A plain click (< 5px movement) is not
 * a drag — the source's own onclick fires instead (sort unchanged).
 *
 * Pure math lives in `column-reorder-math.ts` and is unit-tested there; the
 * ghost and drop-slot ELEMENTS are built by `column-ghost.ts`. This file owns
 * the drag session, the geometry snapshot and the DOM writes: happy-dom
 * computes no geometry, so nothing here is meaningfully testable in the
 * component suite — it is exercised by the real-layout Playwright test
 * instead. Keep that boundary.
 *
 * ───────────────────────────────────────────────────────────────────────
 * Visual model — lift the whole column, open a real slot
 * ───────────────────────────────────────────────────────────────────────
 * On grab, the ENTIRE column (header + every body cell) lifts as the drag
 * image — a faithful clone that follows the cursor. The real column is hidden
 * in place (it is "carried" by the ghost). As the pointer moves across the
 * grid, the remaining columns pack to close the lifted column's old slot and
 * PART to open a real, column-width empty slot exactly where the column will
 * land — a shaded placeholder showing the space ready to accept it. Dropping
 * snaps the column into that slot.
 *
 * ───────────────────────────────────────────────────────────────────────
 * Segments — a drag never leaves its own segment
 * ───────────────────────────────────────────────────────────────────────
 * A column's segment is the VALUE of its nearest `[data-grid-col-seg]`
 * ancestor — `'p:<label>'` pinned, `'s:<label>'` scrolling. The drag snapshot,
 * the gap math and the drop are all confined to the cells sharing that value,
 * and columns outside it never move; `applySegmentOrder` splices the segment's
 * new internal order back into the full key list before emitting.
 *
 * By VALUE, never by container identity: `gridSegmentsOf` merges a run into
 * one container only when the group label is non-empty, so every UNGROUPED
 * column sits in a container of its own. Treating the container as the
 * segment would make each of them a size-1 segment, and an ungrouped grid —
 * which is most of them — would be completely undraggable while every test
 * still passed.
 *
 * ───────────────────────────────────────────────────────────────────────
 * Why a region hit-test (not the grid-drag cell hit-test)
 * ───────────────────────────────────────────────────────────────────────
 * The drop slot must land EXACTLY where the placeholder is shown. The generic
 * cell hit-test returns null whenever the pointer is over a column gap, a row
 * gap, or just past the last row — and a null target on pointerup makes the
 * drag engine CANCEL (revert) instead of drop. That produced drops that
 * "didn't go where the slot showed". Here we drive createDragSession directly
 * with a REGION hit-test: any point inside the grid's box maps to a gap index
 * computed straight from the cursor X (against a drag-start snapshot of the
 * original column geometry, so it never oscillates). No dead-zones, so the
 * slot tracks continuously and the drop commits the gap the slot shows.
 */
import { createDragSession } from './drag-core/pointer.js';
import { gapFromX, orderFromGapIndex, applySegmentOrder, } from './column-reorder-math.js';
import { buildColumnGhost, makeSlot } from './column-ghost.js';
// ─── Tunables ─────────────────────────────────────────────────────────────────
const SHIFT_EASE = 'transform 200ms cubic-bezier(0.2, 0, 0, 1)';
const EDGE_MARGIN = 28; // px slack around the grid box
/** `getComputedStyle(...).columnGap` is 'normal' on a gapless flex row → NaN. */
function num(px, fallback) {
    const n = parseFloat(px);
    return Number.isFinite(n) ? n : fallback;
}
const HEADER_CELLS = '[data-grid-row="header"] [data-grid-col]';
function headerCellsFor(root, key) {
    return Array.from(root.querySelectorAll('[data-grid-row="header"] [data-grid-col="' + key + '"]'));
}
/** Body cells of a column: same attribute, anywhere EXCEPT the header row. */
function bodyCellsFor(root, key) {
    return Array.from(root.querySelectorAll('[data-grid-col="' + key + '"]')).filter((el) => el.closest('[data-grid-row="header"]') === null);
}
/**
 * A column's segment is the VALUE of the nearest [data-grid-col-seg] ancestor
 * — 'p:<label>' pinned, 's:<label>' scrolling.
 *
 * By VALUE, never by container identity. gridSegmentsOf merges a run into one
 * container only when the group label is non-empty, so every UNGROUPED column
 * sits in a container of its own. Treating the container as the segment would
 * make each of them a size-1 segment, and an ungrouped grid — which is most of
 * them — would be completely undraggable while every test still passed.
 */
function segOf(cell) {
    const holder = cell.closest('[data-grid-col-seg]');
    return holder ? holder.getAttribute('data-grid-col-seg') : null;
}
/**
 * Only cells belonging to THIS grid. querySelectorAll reaches DOWN into a
 * nested DataGridSpec rendered in a detail slot — whose root sits inside this
 * root — and its header cells would otherwise be counted as this grid's
 * columns, polluting both the key order and segment membership. `closest()`
 * walks up, so the nearest [data-grid-id] ancestor names the owning grid.
 */
function ownedBy(root) {
    return (el) => el.closest('[data-grid-id]') === root;
}
/** Header cells sharing a segment value, in document (visual) order. */
function segmentCells(root, seg) {
    const mine = ownedBy(root);
    return Array.from(root.querySelectorAll('[data-grid-row="header"] [data-grid-col]')).filter((el) => el.offsetParent !== null && mine(el) && segOf(el) === seg);
}
// ─── Main export ──────────────────────────────────────────────────────────────
/**
 * Wire up per-instance header-cell drag-to-reorder for a DataGridSpec.
 *
 * @param gridId    unique ID returned by genGridId() (or a getter for it)
 * @param onReorder called with the full new visible key order on drop
 * @param enabled   `reorderableColumns` — when false, skips wiring entirely
 *                  (a dead affordance is worse than no feature)
 * @returns         destroy/cleanup function (stored in @state)
 */
export function wireColumnDrag(gridId, onReorder, enabled) {
    if (!enabled)
        return function noop() { };
    let session = null;
    let mutationObserver = null;
    let waitTimer = null;
    let slot = null;
    function resolveId() {
        return typeof gridId === 'function' ? gridId() : gridId;
    }
    function findRoot() {
        const id = resolveId();
        return id ? document.querySelector('[data-grid-id="' + id + '"]') : null;
    }
    function teardown() {
        if (session) {
            try {
                session.destroy();
            }
            catch {
                /* noop */
            }
            session = null;
        }
        if (mutationObserver) {
            mutationObserver.disconnect();
            mutationObserver = null;
        }
        if (waitTimer != null) {
            clearTimeout(waitTimer);
            waitTimer = null;
        }
        if (slot) {
            try {
                slot.remove();
            }
            catch {
                /* noop */
            }
            slot = null;
        }
    }
    function tryMount() {
        // The scope root IS the [data-grid-id] element — every query below is
        // scoped to it, so sibling grids on the same page never see each other.
        const found = findRoot();
        if (!found) {
            waitTimer = setTimeout(tryMount, 80);
            return;
        }
        // Re-bound as a non-nullable const: TypeScript does not carry a narrowing
        // into the function declarations below, and `root!` everywhere reads worse.
        const root = found;
        waitTimer = null;
        const dropSlot = makeSlot();
        slot = dropSlot;
        // ── Per-drag snapshot (original, untransformed geometry) ───────────────
        let snap = null;
        let moved = false;
        let curGap = -1;
        let touched = new Set();
        let lastX = null; // for drag-direction detection
        let dir = 1; // +1 dragging right, -1 dragging left
        function captureSnapshot(srcEl, srcKey) {
            const seg = segOf(srcEl) ?? '';
            const cols = segmentCells(root, seg).map((el) => {
                const r = el.getBoundingClientRect();
                return { key: el.getAttribute('data-grid-col') ?? '', left: r.left, width: r.width };
            });
            const srcIdx = cols.findIndex((c) => c.key === srcKey);
            if (srcIdx < 0)
                return null;
            const gr = root.getBoundingClientRect();
            // The header is a plain flex row with no gap, where columnGap computes
            // to 'normal' — hence a 0 fallback, not Vector's 12, which would inject
            // 12px of phantom spacing into every shift transform.
            const headerRow = root.querySelector('[data-grid-row="header"]');
            const G = headerRow ? num(getComputedStyle(headerRow).columnGap, 0) : 0;
            return {
                cols,
                srcIdx,
                W: cols[srcIdx].width,
                G,
                base: cols[0].left,
                seg,
                top: gr.top,
                height: gr.height,
                left: gr.left,
                right: gr.right,
            };
        }
        // Inside the grid's box (with slack)? Off-box releases cancel (revert).
        function withinGrid(s, x, y) {
            return (x >= s.left - EDGE_MARGIN &&
                x <= s.right + EDGE_MARGIN &&
                y >= s.top - EDGE_MARGIN &&
                y <= s.top + s.height + EDGE_MARGIN);
        }
        // Cursor X → packed gap index, tracking drag direction as it goes. The
        // threshold follows the direction the cursor ENTERS a column from, which
        // gives a dead band in the column's middle so the slot cannot flicker.
        // The counting itself is pure — see column-reorder-math.ts.
        function trackedGapFromX(s, clientX) {
            if (lastX != null) {
                if (clientX > lastX)
                    dir = 1;
                else if (clientX < lastX)
                    dir = -1;
            }
            lastX = clientX;
            return gapFromX(s.cols, s.srcIdx, clientX, dir);
        }
        function applyGap(s, g) {
            if (g === curGap)
                return;
            clearTransforms();
            curGap = g;
            const { cols, srcIdx, W, G } = s;
            const step = W + G;
            for (let i = 0; i < cols.length; i++) {
                if (i === srcIdx)
                    continue;
                const packedPos = i < srcIdx ? i : i - 1;
                const close = i > srcIdx ? -step : 0;
                const open = packedPos >= g ? step : 0;
                const tx = close + open;
                if (tx !== 0)
                    translateCol(cols[i].key, tx);
            }
            positionSlot(s, g);
        }
        function translateCol(key, tx) {
            const t = 'translateX(' + tx + 'px)';
            for (const el of headerCellsFor(root, key)) {
                el.style.transition = SHIFT_EASE;
                el.style.transform = t;
                touched.add(el);
            }
            for (const el of bodyCellsFor(root, key)) {
                el.style.transition = SHIFT_EASE;
                el.style.transform = t;
                touched.add(el);
            }
        }
        function positionSlot(s, g) {
            const { cols, srcIdx, W, G, base, top, height } = s;
            const packed = cols.filter((_, i) => i !== srcIdx);
            let left = base;
            for (let q = 0; q < g && q < packed.length; q++)
                left += packed[q].width + G;
            dropSlot.style.left = Math.round(left) + 'px';
            dropSlot.style.top = Math.round(top) + 'px';
            dropSlot.style.width = Math.round(W) + 'px';
            dropSlot.style.height = Math.round(height) + 'px';
            dropSlot.style.opacity = '1';
        }
        function clearTransforms() {
            for (const el of touched) {
                el.style.transform = '';
                el.style.transition = '';
            }
            touched.clear();
        }
        function setSourceHidden(srcKey, hidden) {
            const v = hidden ? '0' : '';
            for (const el of [...headerCellsFor(root, srcKey), ...bodyCellsFor(root, srcKey)]) {
                el.style.transition = 'opacity 120ms ease';
                el.style.opacity = v;
            }
        }
        function resetVisuals(srcKey) {
            clearTransforms();
            dropSlot.style.opacity = '0';
            if (srcKey)
                setSourceHidden(srcKey, false);
            curGap = -1;
        }
        /** Every visible column key of the whole grid, in visual order. */
        function readKeyOrder() {
            const mine = ownedBy(root);
            return Array.from(root.querySelectorAll(HEADER_CELLS))
                .filter((el) => el.offsetParent !== null && mine(el))
                .map((el) => el.getAttribute('data-grid-col') ?? '')
                .filter(Boolean);
        }
        function swallowNextClick() {
            const handler = (e) => {
                e.stopPropagation();
                e.preventDefault();
                root.removeEventListener('click', handler, true);
            };
            root.addEventListener('click', handler, true);
            setTimeout(() => root.removeEventListener('click', handler, true), 400);
        }
        const s = createDragSession({
            getSrcId: (el) => el.getAttribute('data-grid-col'),
            mouseMoveStart: 5,
            // The drag image is the whole column — built by column-ghost.ts, which
            // is handed the cells rather than the selectors that find them.
            ghost: (srcEl) => buildColumnGhost(srcEl, bodyCellsFor(root, srcEl.getAttribute('data-grid-col') ?? '')),
            onStart: (srcId, srcEl) => {
                moved = false;
                curGap = -1;
                touched = new Set();
                snap = captureSnapshot(srcEl, srcId);
                // Seed direction tracking from the grabbed column's center so the very
                // first move resolves a correct drag direction.
                lastX = snap ? snap.cols[snap.srcIdx].left + snap.cols[snap.srcIdx].width / 2 : null;
                dir = 1;
                if (snap)
                    setSourceHidden(srcId, true);
            },
            // Region hit-test: any in-box point yields a gap index; out-of-box → null
            // (so a release outside the grid cancels). Pure read of the snapshot.
            hitTest: (x, y) => {
                if (!snap)
                    return null;
                if (!withinGrid(snap, x, y))
                    return null;
                return { g: trackedGapFromX(snap, x) };
            },
            onTargetChange: (target) => {
                moved = true;
                const cur = snap;
                if (!cur)
                    return;
                if (target && typeof target.g === 'number')
                    applyGap(cur, target.g);
                else {
                    clearTransforms();
                    dropSlot.style.opacity = '0';
                    curGap = -1;
                }
            },
            // Commit the gap the slot is currently showing (curGap), so the column
            // always lands exactly where the placeholder was.
            onDrop: (srcId) => {
                const g = curGap;
                const segKeys = snap ? snap.cols.map((c) => c.key) : null;
                resetVisuals(srcId);
                snap = null;
                if (!moved || g < 0 || !segKeys)
                    return;
                swallowNextClick();
                // The drag was confined to one segment, but the grid emits the FULL
                // key order — splice the segment's new order back into the whole list.
                const nextSeg = orderFromGapIndex(segKeys, srcId, g);
                if (nextSeg)
                    onReorder(applySegmentOrder(readKeyOrder(), segKeys, nextSeg));
            },
            onCancel: (srcId) => {
                resetVisuals(srcId);
                snap = null;
                if (moved)
                    swallowNextClick();
            },
        });
        session = s;
        // Attach every header cell as a drag source; re-attach when the grid
        // re-renders (column hide/show changes the cell set).
        function attachSources() {
            const mine = ownedBy(root);
            for (const cell of Array.from(root.querySelectorAll(HEADER_CELLS)).filter(mine)) {
                // A segment of one has nowhere to drop. Registering it anyway would
                // give the user a grab cursor on a column that cannot move — worse
                // than no feature.
                if (segmentCells(root, segOf(cell) ?? '').length < 2)
                    continue;
                cell.style.cursor = 'grab';
                s.attach(cell);
            }
        }
        attachSources();
        mutationObserver = new MutationObserver(attachSources);
        mutationObserver.observe(root, { childList: true, subtree: true });
    }
    tryMount();
    return teardown;
}
export { genGridId } from './column-reorder-math.js';
//# sourceMappingURL=data-grid-column-drag.js.map