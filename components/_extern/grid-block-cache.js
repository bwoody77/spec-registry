/**
 * grid-block-cache.ts — which blocks of rows a windowed grid holds, which it
 * has asked for, and which failed.
 *
 * Pure state. It never fetches: it says what should be fetched and accepts
 * what comes back. That is deliberate — DataGrid's own comment reads "the grid
 * never fetches; it asks", and this preserves it.
 *
 * ── Why `failed` is a state and not just "absent" ──────────────────────────
 * A failed block left merely not-held is re-requested by the next scroll
 * event, which re-fails, which leaves it not-held. That is an infinite fetch
 * loop reachable by nothing more exotic than a 500, and it is the same shape
 * check-fetch-trigger-latch.mjs exists to catch in cf: latch on HAVING TRIED,
 * not on the absence of a result. Only retry() clears it.
 */
// ── ONE counter for the whole page, not one per cache ──────────────────────
// A generation ends in two ways: invalidate(), and the grid dropping this
// cache entirely to build a new one (which is what `rowCount` changing does —
// `_windowTeardown` re-runs and wireGridWindow calls createBlockCache again).
// A per-cache counter starting at 0 only guards the first; the second hands
// the NEW cache the same token values the dead one already issued, so a
// response describing the previous filter is accepted as current and the
// block is never re-requested. Monotonic across the module, so no token is
// ever reused by anything.
let nextToken = 1;
/**
 * How many delivered blocks a cache keeps. At the default blockSize of 100 that
 * is 2,400 rows held for a window that shows a few dozen.
 *
 * Without a cap `held` only ever grows: it is cleared on invalidate and never
 * otherwise, so scrolling a 100,000-row list holds 100,000 rows. The DOM has
 * been bounded since windowing landed; the data never was, and this is the one
 * part of that no caller can fix from outside the component.
 *
 * Generous on purpose. Eviction costs a refetch when the user scrolls back, so
 * the cap wants to be far above any plausible window and far below "the whole
 * table" — this is roughly a hundred screens.
 */
const MAX_HELD_BLOCKS = 24;
export function createBlockCache(blockSize, maxBlocks = MAX_HELD_BLOCKS) {
    const held = new Map();
    const inflight = new Set();
    const failed = new Set();
    let token = nextToken++;
    let changed = null;
    // The block range the most recent window asked about — the anchor eviction
    // measures distance from.
    let winFirst = 0;
    let winLast = 0;
    const notify = () => { if (changed)
        changed(); };
    /**
     * Drop the blocks furthest from the window until we are back under the cap.
     *
     * Distance from the WINDOW, not least-recently-used: a reader scrolling up
     * and down a page wants the blocks either side of them kept, and LRU by clock
     * would evict the one they are about to scroll back into. A block inside the
     * window is never evicted at any size — that would thrash, since the very
     * next recompute re-requests it, and the rows it holds are on screen.
     */
    const evictFar = () => {
        if (held.size <= maxBlocks)
            return;
        const ranked = Array.from(held.keys())
            .map((b) => ({ b, d: b < winFirst ? winFirst - b : b > winLast ? b - winLast : 0 }))
            .sort((x, y) => y.d - x.d);
        for (const { b, d } of ranked) {
            if (held.size <= maxBlocks)
                break;
            if (d === 0)
                break;
            held.delete(b);
        }
    };
    return {
        blockSize,
        requestBlocksFor(start, end) {
            const out = [];
            if (end <= start)
                return out;
            const first = Math.floor(start / blockSize);
            const last = Math.floor((end - 1) / blockSize);
            // Remembered for evictFar. Recorded even when every block is already
            // held, because that is exactly the scroll that moves the window.
            winFirst = first;
            winLast = last;
            for (let b = first; b <= last; b++) {
                if (held.has(b) || inflight.has(b) || failed.has(b))
                    continue;
                inflight.add(b);
                out.push({ blockIndex: b, start: b * blockSize, end: (b + 1) * blockSize, token });
            }
            return out;
        },
        accept(blockIndex, rows, t) {
            // A response that predates an invalidate describes a filter the user has
            // already left. Dropping it is the point of the token.
            if (t !== token)
                return false;
            inflight.delete(blockIndex);
            failed.delete(blockIndex);
            held.set(blockIndex, rows);
            evictFar();
            notify();
            return true;
        },
        fail(blockIndex, t) {
            if (t !== token)
                return false;
            inflight.delete(blockIndex);
            failed.add(blockIndex);
            notify();
            return true;
        },
        retry(blockIndex) {
            failed.delete(blockIndex);
            notify();
        },
        rowAt(index) {
            const b = Math.floor(index / blockSize);
            const rows = held.get(b);
            if (!rows)
                return null;
            const row = rows[index - b * blockSize];
            return row === undefined ? null : row;
        },
        isFailedAt(index) {
            return failed.has(Math.floor(index / blockSize));
        },
        invalidate() {
            held.clear();
            inflight.clear();
            failed.clear();
            token = nextToken++;
            notify();
        },
        onChange(cb) { changed = cb; },
    };
}
// ── The gridId registry ────────────────────────────────────────────────────
// How a CALLER hands a fetched block back. The grid emits rangeNeeded with its
// gridId; the caller fetches and calls deliverBlock with the same id. Every
// entry point returns false rather than throwing for an unknown id: a grid
// unmounting while a fetch is in flight is ordinary, not exceptional.
const caches = new Map();
export function registerCache(gridId, cache) {
    caches.set(gridId, cache);
}
export function unregisterCache(gridId) {
    caches.delete(gridId);
}
export function deliverBlock(gridId, blockIndex, rows, token) {
    const c = caches.get(gridId);
    if (!c)
        return false;
    // A group header or a total row has no fixed pitch, so it cannot appear in a
    // windowed grid: the spacers stand in for a height those rows do not have,
    // and the scrollbar then lies by the difference.
    //
    // Checked HERE rather than against the grid's `rows` prop, which windowed
    // mode ignores entirely — a prop-side check would pass every single time and
    // catch nothing. `r &&` before the typeof: `typeof null === 'object'`, and
    // `'_kind' in null` throws, so one sparse block would take the whole
    // delivery path down.
    for (const r of rows) {
        if (r && typeof r === 'object' && '_kind' in r) {
            console.error(`DataGrid: block ${blockIndex} contains a _kind row; group and total rows cannot be windowed.`);
            // Refused, and marked failed rather than left in flight. requestBlocksFor
            // set the in-flight mark on the way out; returning without clearing it
            // means the block is never asked for again, so those rows stay skeletons
            // forever with no retry and no explanation on screen. `failed` is the
            // state that has a way out — and, unlike absence, it is not re-requested
            // by the next scroll event.
            c.fail(blockIndex, token);
            return false;
        }
    }
    return c.accept(blockIndex, rows, token);
}
/**
 * Answer as many of a windowed grid's outstanding requests as `rows` can, and
 * return the ones that must be HELD until more rows arrive.
 *
 * This exists because both of Vector's windowed grids hand-rolled it and both
 * got it wrong, in different ways, on lists the other one never sees. Three
 * things have to be true at once and none of them is obvious from the request:
 *
 * 1. `req.end` is the block's NOMINAL end — `(blockIndex + 1) * blockSize` —
 *    and it is emitted UNCLAMPED. On any list shorter than one block it is
 *    larger than the list will ever be, so a `rows.length >= req.end` guard is
 *    never satisfied and the only block is held forever. Symptom: a 12-row
 *    logbook, and a 20-user roster, sitting on a full screen of skeletons.
 *    The fix is to stop guarding on it — NOT to clamp the slice, which
 *    `Array.slice` does anyway.
 *
 * 2. Clamping alone is not enough either. On a filter change the caller's
 *    `rows` can still be the PREVIOUS list while `rowCount` already describes
 *    the new one, and a clamped slice of the stale list is accepted happily —
 *    wrong rows, cemented, because a delivered block is never re-requested.
 *    `rows.length === rowCount` is the honest test that they describe the same
 *    list; it is cheap, and it is the only signal available here.
 *
 * 3. An unanswerable request must be HELD, not dropped. It has already been
 *    marked in flight, so nothing asks again once the rows land, and the grid
 *    keeps the skeletons instead of showing wrong data — a quieter failure but
 *    a permanent one. Callers re-drain from a @watch on their rows.
 *
 * A short FINAL block is correct and is delivered: when `rowCount` is the
 * number of rows the caller holds, a block ending at the last row is whole.
 */
export function deliverWindow(reqs, rows, rowCount) {
    const list = Array.isArray(reqs) ? reqs : [];
    if (!Array.isArray(rows) || rows.length !== rowCount)
        return list;
    const held = [];
    for (const r of list) {
        if (!r)
            continue;
        // NOT clamped by hand: `Array.slice` already stops at the end of the array,
        // so `slice(0, 100)` of a 20-row list is those 20 rows. The unclamped
        // `req.end` was never the thing that broke — the callers' `rows.length >=
        // req.end` GUARD was, by refusing to deliver at all. Writing the clamp out
        // longhand here reads as though it is load-bearing; a mutation test proved
        // it is not, so it is gone and this note is in its place.
        if (r.start < rows.length) {
            deliverBlock(r.gridId, r.blockIndex, rows.slice(r.start, r.end), r.token);
        }
        else {
            // A start past the end of the list would slice to nothing, and an empty
            // delivery still marks the block held — the block would never be asked
            // for again and those rows would stay skeletons.
            held.push(r);
        }
    }
    return held;
}
/**
 * Whether any of these requests reaches the end of the rows the caller holds.
 *
 * This is the infinite-scroll trigger for a caller that pages: it means the
 * window has arrived at the last loaded row, so the next page is worth
 * fetching. Deliberately separate from deliverWindow — whether to prefetch is
 * the caller's policy, and a caller holding its whole list wants no part of it.
 */
export function windowReachedEnd(reqs, rowCount) {
    if (!Array.isArray(reqs))
        return false;
    for (const r of reqs) {
        if (r && r.end >= rowCount)
            return true;
    }
    return false;
}
export function failBlock(gridId, blockIndex, token) {
    const c = caches.get(gridId);
    return c ? c.fail(blockIndex, token) : false;
}
export function retryBlock(gridId, blockIndex) {
    caches.get(gridId)?.retry(blockIndex);
}
//# sourceMappingURL=grid-block-cache.js.map