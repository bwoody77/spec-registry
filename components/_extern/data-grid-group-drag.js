/**
 * DataGrid — drag a labelled GROUP as a block.
 *
 * ── Why this is a second wire, not a flag on the first ──────────────────────
 * `data-grid-column-drag.ts` confines a drag to the source column's SEGMENT.
 * A group IS a segment, so within that model a group can never move at all:
 * columns could be shuffled around Quality, but Quality itself was stuck. The
 * complaint that started this ("I should be able to move it, along with its
 * sub columns, like I would any other column") is one level up — a drag among
 * SIBLING SEGMENTS rather than within one.
 *
 * The maths is the same functions applied one level up: `gapFromX` over
 * segment boxes instead of column boxes, `orderFromGapIndex` over segment ids
 * instead of column keys. What differs is the snapshot (segment containers,
 * not header cells) and the commit (concatenate each segment's member keys).
 *
 * ── Only LABELLED runs are draggable ────────────────────────────────────────
 * The source is the `[data-grid-seg-label]` cell, which DataGrid stamps
 * only on a run whose group label is non-empty. Every ungrouped column in a
 * run shares one segment, so arming that segment would drag all of them at
 * once — which is not what anyone means by moving a column.
 *
 * Pinned and scrolling segments never mix: the drag is confined to siblings
 * sharing the source's `p:` / `s:` prefix, so a group cannot silently pin or
 * unpin itself.
 */
import { createDragSession } from './drag-core/pointer.js';
import { gapFromX, orderFromGapIndex, mergeHiddenKeys, } from './column-reorder-math.js';
import { HEADER_CELLS, ownedBy, segOf } from './data-grid-dom.js';
/** Bound by DataGrid to `reorderableColumns`; see wireColumnDrag. */
const ENABLED_ATTR = 'data-grid-reorderable';
const SEG_LABEL = '[data-grid-seg-label]';
const SEG = '[data-grid-col-seg]';
export function wireGroupDrag(gridId, onReorder, enabled, allKeys) {
    let session = null;
    let mutationObserver = null;
    let waitTimer = null;
    let teardownSources = null;
    function resolveId() {
        return typeof gridId === 'function' ? gridId() : gridId;
    }
    function resolveEnabled() {
        return typeof enabled === 'function' ? enabled() === true : enabled === true;
    }
    function resolveAllKeys() {
        const k = typeof allKeys === 'function' ? allKeys() : allKeys;
        return Array.isArray(k) ? k : [];
    }
    function findRoot() {
        const id = resolveId();
        return id ? document.querySelector('[data-grid-id="' + id + '"]') : null;
    }
    function teardown() {
        if (teardownSources) {
            try {
                teardownSources();
            }
            catch {
                /* noop */
            }
            teardownSources = null;
        }
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
    }
    function tryMount() {
        const found = findRoot();
        if (!found) {
            waitTimer = setTimeout(tryMount, 80);
            return;
        }
        const root = found;
        waitTimer = null;
        const mine = ownedBy(root);
        /** Segment containers on the source's side, in visual order. */
        function siblingSegments(side) {
            return Array.from(root.querySelectorAll(SEG)).filter((el) => mine(el) &&
                (el.getAttribute('data-grid-col-seg') ?? '').startsWith(side));
        }
        /** The member keys of each segment id, in current visual order. */
        function keysBySegment() {
            const out = new Map();
            for (const cell of Array.from(root.querySelectorAll(HEADER_CELLS))) {
                if (!mine(cell) || cell.offsetParent === null)
                    continue;
                const seg = segOf(cell);
                const key = cell.getAttribute('data-grid-col');
                if (!seg || !key)
                    continue;
                const bucket = out.get(seg);
                if (bucket)
                    bucket.push(key);
                else
                    out.set(seg, [key]);
            }
            return out;
        }
        let snap = null;
        let moved = false;
        let curGap = -1;
        let lastX = null;
        let dir = 1;
        function captureSnapshot(srcSeg) {
            const side = srcSeg.slice(0, 2); // 'p:' or 's:'
            const els = siblingSegments(side);
            // One segment on this side has nowhere to go. Same rule as the column
            // wire's size-1 segment: no grab cursor on something that cannot move.
            if (els.length < 2)
                return null;
            const segs = els.map((el) => {
                const r = el.getBoundingClientRect();
                return {
                    key: el.getAttribute('data-grid-col-seg') ?? '',
                    left: r.left,
                    width: r.width,
                };
            });
            const srcIdx = segs.findIndex((s) => s.key === srcSeg);
            if (srcIdx < 0)
                return null;
            const gr = root.getBoundingClientRect();
            return {
                segs,
                srcIdx,
                top: gr.top,
                height: gr.height,
                left: gr.left,
                right: gr.right,
            };
        }
        function withinGrid(s, x, y) {
            const M = 28;
            return (x >= s.left - M && x <= s.right + M && y >= s.top - M && y <= s.top + s.height + M);
        }
        function trackedGap(s, x) {
            if (lastX != null && Math.abs(x - lastX) > 1)
                dir = x > lastX ? 1 : -1;
            lastX = x;
            return gapFromX(s.segs, s.srcIdx, x, dir);
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
            getSrcId: (el) => el.getAttribute('data-grid-seg-label'),
            mouseMoveStart: 5,
            // The ghost is the whole segment container — label strip and member
            // headings together, which is what the user grabbed.
            ghost: (srcEl) => {
                const holder = srcEl.closest(SEG);
                const src = holder ?? srcEl;
                const clone = src.cloneNode(true);
                clone.style.width = src.getBoundingClientRect().width + 'px';
                return clone;
            },
            onStart: (srcId) => {
                moved = false;
                curGap = -1;
                snap = captureSnapshot(srcId);
                lastX = snap ? snap.segs[snap.srcIdx].left + snap.segs[snap.srcIdx].width / 2 : null;
                dir = 1;
            },
            hitTest: (x, y) => {
                if (!snap)
                    return null;
                if (!withinGrid(snap, x, y))
                    return null;
                return { g: trackedGap(snap, x) };
            },
            onTargetChange: (target) => {
                moved = true;
                if (!snap)
                    return;
                curGap = target && typeof target.g === 'number' ? target.g : -1;
            },
            onDrop: (srcId) => {
                const g = curGap;
                const cur = snap;
                snap = null;
                curGap = -1;
                if (!moved || g < 0 || !cur)
                    return;
                swallowNextClick();
                const segIds = cur.segs.map((seg) => seg.key);
                const nextSegs = orderFromGapIndex(segIds, srcId, g);
                if (!nextSegs)
                    return;
                // Rebuild the key order by walking the new segment order and
                // concatenating each segment's members. Segments on the OTHER side
                // keep their place: the pinned and scrolling runs never interleave.
                const bySeg = keysBySegment();
                const side = srcId.slice(0, 2);
                const visible = [];
                let moving = 0;
                for (const cell of Array.from(root.querySelectorAll(HEADER_CELLS))) {
                    if (!mine(cell) || cell.offsetParent === null)
                        continue;
                    const seg = segOf(cell);
                    if (!seg)
                        continue;
                    if (!seg.startsWith(side)) {
                        const key = cell.getAttribute('data-grid-col');
                        if (key)
                            visible.push(key);
                        continue;
                    }
                    // The first cell of this side stands in for the whole reordered run.
                    if (moving === 0) {
                        for (const id of nextSegs) {
                            for (const key of bySeg.get(id) ?? [])
                                visible.push(key);
                        }
                    }
                    moving += 1;
                }
                onReorder(mergeHiddenKeys(resolveAllKeys(), visible));
            },
            onCancel: () => {
                snap = null;
                curGap = -1;
                if (moved)
                    swallowNextClick();
            },
        });
        session = s;
        const armed = new Map();
        function disarmSources() {
            for (const [cell, prevCursor] of armed) {
                s.detach(cell);
                cell.style.cursor = prevCursor;
            }
            armed.clear();
        }
        function attachSources() {
            if (!resolveEnabled()) {
                disarmSources();
                return;
            }
            for (const cell of Array.from(root.querySelectorAll(SEG_LABEL)).filter(mine)) {
                const segId = cell.getAttribute('data-grid-seg-label') ?? '';
                // A side with one segment has nowhere to drop.
                if (siblingSegments(segId.slice(0, 2)).length < 2)
                    continue;
                if (!armed.has(cell))
                    armed.set(cell, cell.style.cursor);
                cell.style.cursor = 'grab';
                s.attach(cell);
            }
        }
        attachSources();
        mutationObserver = new MutationObserver(attachSources);
        // attributeFilter is load-bearing: attachSources writes `style` on the
        // cells it arms, so an unfiltered attribute observer would schedule
        // another pass forever.
        mutationObserver.observe(root, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: [ENABLED_ATTR],
        });
        teardownSources = disarmSources;
    }
    tryMount();
    return teardown;
}
//# sourceMappingURL=data-grid-group-drag.js.map