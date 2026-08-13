/**
 * grid-window-wire.ts — the only part of the windowing feature that touches
 * the DOM.
 *
 * Reached the same way wireColumnDrag is: the .spec mints an id with
 * genGridId(), stamps it as data-grid-id, and hands the id here. This module
 * finds the scroll container, measures it, computes the window, and pushes a
 * COMPLETE render state back. The .spec stores that state and renders it — it
 * never reads the cache, so there is no reactivity bridge to get wrong.
 *
 * Measuring here is also what removes the need for a viewportHeight prop:
 * DataGrid sizes itself height:100% and has no pixel height of its own to
 * pass, but the scroll container knows its clientHeight.
 */
import { computeWindow } from './grid-window.js';
import { createBlockCache, registerCache, unregisterCache, } from './grid-block-cache.js';
/**
 * Live wires, by grid id. Two things need this.
 *
 * DataGrid calls wireGridWindow from a `@computed`, and that computed's deps
 * include `rowCount` — so a caller whose total changes (any filter, any
 * search) re-runs it and gets a SECOND wire on the same grid. Without this map
 * the first one's scroll listener and ResizeObserver are never released and
 * every keystroke in a search box leaks another pair.
 *
 * It is also what makes the re-entry correct rather than merely tidy: the old
 * wire is destroyed BEFORE the new one registers its cache, so the new cache
 * is the one left in the gridId registry.
 */
const wires = new Map();
const live = new Set();
let reaper = null;
function sweep() {
    // Snapshot: destroy() removes from `live` while we are iterating it.
    for (const w of Array.from(live))
        if (w.isDetached())
            w.destroy();
}
function watchForDetach(w) {
    live.add(w);
    if (reaper || typeof MutationObserver === 'undefined')
        return;
    reaper = new MutationObserver(sweep);
    // `document`, not `document.body`: body itself can be replaced, and a grid
    // need not be under it at all.
    reaper.observe(document, { childList: true, subtree: true });
}
function unwatchForDetach(w) {
    if (!live.delete(w))
        return;
    if (live.size > 0 || !reaper)
        return;
    reaper.disconnect();
    reaper = null;
}
export function wireGridWindow(gridId, opts, onWindow, onRangeNeeded) {
    wires.get(gridId)?.destroy();
    const cache = createBlockCache(opts.blockSize);
    registerCache(gridId, cache);
    let rowCount = opts.rowCount;
    let last = null;
    let scroller = null;
    let ro;
    let waitTimer = null;
    let destroyed = false;
    // What the caller's data currently IS — sort, filters, and the caller's own
    // `dataVersion`, flattened to one string. It lives on the wire rather than in
    // a module map so it resets with the cache it describes: a `rowCount` change
    // rebuilds both, and a generation remembered across that would compare the
    // new cache's first key against a dead one's.
    let generation = null;
    function project(w) {
        const rows = [];
        const failed = [];
        for (let i = w.start; i < w.end; i++) {
            rows.push(cache.rowAt(i));
            failed.push(cache.isFailedAt(i));
        }
        return { rows, failed, start: w.start, end: w.end, topPad: w.topPad, botPad: w.botPad };
    }
    // Guards the synchronous cycle deliver → notify → recompute → request →
    // deliver. It terminates on its own (an accepted block is `held`, a failed
    // one is latched, so no block is ever asked for twice), but a caller serving
    // from a warm cache nests one frame per block and the re-entrant recompute
    // would re-measure and re-push a window nothing has moved. The outer frame
    // is the one whose window is authoritative.
    let inRecompute = false;
    let pending = false;
    function recompute(force) {
        if (inRecompute) {
            // DEFERRED, never dropped. `onWindow` fires before `onRangeNeeded`, so
            // the projection already pushed by the outer frame predates whatever the
            // caller just delivered — dropping this would leave a synchronous caller
            // staring at skeletons of rows the cache already holds.
            pending = true;
            return;
        }
        inRecompute = true;
        try {
            recomputeInner(force);
            // Drain. Bounded because each pass can only make blocks held or failed,
            // and both are skipped by requestBlocksFor — so a pass that requests
            // nothing new delivers nothing new and sets no further `pending`. The
            // cap is a backstop against a caller whose delivery itself mutates the
            // window, not a load-bearing limit.
            for (let i = 0; pending && i < 8; i++) {
                pending = false;
                recomputeInner(true);
            }
            pending = false;
        }
        finally {
            inRecompute = false;
        }
    }
    function recomputeInner(force) {
        const w = computeWindow({
            scrollTop: scroller ? scroller.scrollTop : 0,
            viewportHeight: scroller ? scroller.clientHeight : 0,
            rowHeight: opts.rowHeight,
            totalCount: rowCount,
            overscan: opts.overscan,
        });
        // Push only when the window actually moved. Without this the grid
        // re-renders on every scroll pixel, remounting every cell component 30
        // times per row of travel.
        const moved = !last || last.start !== w.start || last.end !== w.end;
        if (!moved && !force)
            return;
        last = w;
        const reqs = cache.requestBlocksFor(w.start, w.end);
        onWindow(project(w));
        // Stamped with the grid id, because deliverBlock(gridId, …) needs one and
        // the request is the only thing the caller receives. Without it a caller
        // can only scrape [data-grid-id] out of the DOM, and a page with two
        // windowed grids cannot tell which one asked.
        if (reqs.length)
            onRangeNeeded(reqs.map((r) => ({ ...r, gridId })));
    }
    // A block landing (or failing) changes what the CURRENT window renders
    // without changing the window itself, so this push is forced.
    //
    // It goes through `recompute` rather than pushing a projection directly,
    // because a cache change can also make a block REQUESTABLE again — retry()
    // clears the failed mark, invalidate() drops everything — and
    // requestBlocksFor lives only inside recompute. Pushing just the projection
    // meant a retried block re-rendered as a skeleton and was never asked for:
    // the Retry button replaced an actionable error with a permanent stall. The
    // infinite-refetch latch is unaffected — a failed block is still skipped by
    // requestBlocksFor, so `fail` → onChange → recompute asks for nothing.
    cache.onChange(() => { if (last)
        recompute(true); });
    const onScroll = () => recompute(false);
    /**
     * ── WHY THIS CANNOT JUST querySelector ONCE ──────────────────────────────
     * DataGrid calls this from a `@computed`, and the compiler emits every
     * @computed ABOVE the DOM section of the mount function, which appends its
     * root to the container on its LAST line. So at the moment this runs, the
     * grid — scroll container included — is not in the document, and neither is
     * any ancestor of it. A single query finds nothing.
     *
     * That failure is silent and total: `recompute` falls back to scrollTop 0 /
     * viewportHeight 0, which yields a plausible-looking overscan-sized window
     * and spacers that are numerically correct, so the grid renders and simply
     * never responds to a scroll or a resize again. Under happy-dom, where
     * clientHeight is 0 anyway, that fallback is INDISTINGUISHABLE from a
     * successful attach — a structural test cannot see it.
     *
     * @state is no better: it runs earlier still. wireColumnDrag hits the same
     * wall and answers it with an 80ms poll that never stops. This tries the
     * microtask queue first (mount is synchronous, so one turn is normally all
     * it takes) and only then falls back to a BOUNDED poll, so a grid that is
     * never mounted stops asking instead of retrying forever — the shape behind
     * this package's known post-teardown unhandled errors.
     */
    let attempts = 0;
    function attach() {
        if (destroyed || scroller)
            return;
        scroller = document.querySelector(`[data-grid-id="${gridId}"] [data-grid-scroll]`);
        if (!scroller) {
            if (attempts++ >= 32)
                return;
            waitTimer = setTimeout(attach, 16);
            return;
        }
        waitTimer = null;
        scroller.addEventListener('scroll', onScroll, { passive: true });
        // The grid's height can change without a scroll — a sibling panel opening,
        // the window resizing — and a stale viewportHeight renders too few rows.
        if (typeof ResizeObserver !== 'undefined') {
            ro = new ResizeObserver(() => recompute(true));
            ro.observe(scroller);
        }
        // The first measurement anyone can trust: until now viewportHeight was a
        // guess of 0.
        recompute(true);
    }
    attach();
    if (!scroller) {
        // Nothing to measure yet. Push a provisional window anyway so the grid
        // renders its spacers and asks for block 0 immediately rather than waiting
        // a turn; `attach` forces a second push once it has a real clientHeight.
        recompute(true);
        queueMicrotask(attach);
    }
    const handle = {
        destroy() {
            // Idempotent: destroy() is reachable from the reaper AND from a caller,
            // and both may run for the same wire.
            if (destroyed)
                return;
            destroyed = true;
            if (waitTimer != null) {
                clearTimeout(waitTimer);
                waitTimer = null;
            }
            scroller?.removeEventListener('scroll', onScroll);
            ro?.disconnect();
            unwatchForDetach(reapable);
            // Release the gridId registry entry only while it is still OURS. The
            // reaper can fire after a replacement wire has already registered its
            // own cache under the same id, and an unconditional unregisterCache
            // would then delete the LIVE grid's cache.
            if (wires.get(gridId) === handle) {
                wires.delete(gridId);
                unregisterCache(gridId);
            }
        },
        setRowCount(n) { rowCount = n; last = null; recompute(true); },
        invalidate() { cache.invalidate(); last = null; recompute(true); },
        refresh() { recompute(true); },
        // The FIRST key is adopted silently. There is nothing held to drop yet,
        // and invalidating here would burn a token before the opening request.
        setGeneration(key) {
            if (generation === null) {
                generation = key;
                return;
            }
            if (generation === key)
                return;
            generation = key;
            handle.invalidate();
        },
    };
    // A wire that has not attached yet is PENDING, not detached — `attach` polls
    // precisely because the grid is not in the document when this runs, and
    // reaping on a null scroller would destroy every wire before it ever found
    // its grid.
    const reapable = {
        isDetached: () => scroller != null && !scroller.isConnected,
        destroy: () => handle.destroy(),
    };
    wires.set(gridId, handle);
    watchForDetach(reapable);
    return handle;
}
/**
 * Tell a windowed grid what generation its data is in. Called by DataGrid from
 * a `@computed` over `dataVersion`, `sortState` and `filters`, so any of them
 * changing drops every held block and re-asks with a fresh token.
 *
 * Without it the grid had NO way to notice a change that left `rowCount`
 * alone. Sorting is the case that cannot be argued away: a windowed grid
 * requires `externalSort`, so the caller refetches server-side and the count
 * is identical — every block stayed `held` and the grid rendered the previous
 * order permanently. `dataVersion` existed for exactly this and was read by
 * nothing.
 *
 * Unknown ids are ignored rather than throwing: an unwindowed or guarded grid
 * has no wire, and both call this.
 */
export function setGridGeneration(gridId, key) {
    wires.get(gridId)?.setGeneration(key);
}
/**
 * Key-order-stable stringify. `filters` is a map built by user interaction, so
 * two equal filter sets can serialise differently depending on the order the
 * user touched the columns — which would read as a data change and throw away
 * a whole cache for nothing.
 */
function stableKey(v) {
    if (v === null || typeof v !== 'object')
        return JSON.stringify(v) ?? 'null';
    if (Array.isArray(v))
        return '[' + v.map(stableKey).join(',') + ']';
    const o = v;
    return '{' + Object.keys(o).sort().map((k) => JSON.stringify(k) + ':' + stableKey(o[k])).join(',') + '}';
}
/**
 * DataGrid's entry point: the three things that change what a row INDEX means
 * without necessarily changing how many rows there are.
 *
 * Returns null so it can sit in a `@computed`, whose deps are what make this
 * run at all.
 */
export function gridDataGeneration(gridId, dataVersion, sortState, filters) {
    setGridGeneration(gridId, `${String(dataVersion)}|${stableKey(sortState)}|${stableKey(filters)}`);
    return null;
}
//# sourceMappingURL=grid-window-wire.js.map