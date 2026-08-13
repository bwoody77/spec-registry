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
export function createBlockCache(blockSize) {
    const held = new Map();
    const inflight = new Set();
    const failed = new Set();
    let token = nextToken++;
    let changed = null;
    const notify = () => { if (changed)
        changed(); };
    return {
        blockSize,
        requestBlocksFor(start, end) {
            const out = [];
            if (end <= start)
                return out;
            const first = Math.floor(start / blockSize);
            const last = Math.floor((end - 1) / blockSize);
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
export function failBlock(gridId, blockIndex, token) {
    const c = caches.get(gridId);
    return c ? c.fail(blockIndex, token) : false;
}
export function retryBlock(gridId, blockIndex) {
    caches.get(gridId)?.retry(blockIndex);
}
//# sourceMappingURL=grid-block-cache.js.map