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
import { computeWindow, firstVisibleSlot } from './grid-window.js';
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
    // Adopt the outgoing wire's cache rather than dropping it on the floor.
    //
    // wireGridWindow is called from a @computed BODY, so every re-evaluation of
    // its deps builds a new wire — and at mount the deps settle in two steps
    // under the `source` contract (source arriving is itself a dep change, and
    // rowCount goes 0 -> total once the count probe answers). A fresh cache has
    // an empty `held` and an empty `inflight`, so the second wire re-asked for
    // block 0 while the first wire's request for it was still on the network:
    // two full page fetches, 1ms apart, measured on Vector's /my-logbook as
    // 45 KB of the page's 90 KB.
    //
    // Inheriting the same cache OBJECT is what makes the saving real rather than
    // merely deferred: the in-flight request's token still matches, so the first
    // fetch's response is accepted when it lands. The duplicate is not deduped,
    // it is never issued.
    //
    // A rowCount change must NOT drop the cache — the blocks still describe the
    // same rows, and surviving that change is the entire point. handOff() judges
    // block size, which is the thing that would make them describe different
    // rows.
    const prev = wires.get(gridId);
    const handed = prev ? prev.handOff(opts.blockSize) : null;
    prev?.destroy();
    const cache = handed ? handed.cache : createBlockCache(opts.blockSize);
    // Unconditional: prev.destroy() above unregistered this id while it was
    // still the live one, so even an adopted cache has to be put back.
    registerCache(gridId, cache);
    let rowCount = opts.rowCount;
    let last = null;
    // Compared alongside `last` — see the note at its use in recomputeInner.
    let lastFirstVisible = -1;
    let scroller = null;
    let ro;
    let waitTimer = null;
    let destroyed = false;
    // What the caller's data currently IS — sort, filters, and the caller's own
    // `dataVersion`, flattened to one string. It lives on the wire rather than in
    // a module map so it stays PAIRED with the cache it describes — the two are
    // inherited together by handOff() or not at all.
    //
    // (This used to say the pairing meant it "resets with the cache", back when a
    // rowCount change rebuilt both. It now travels with the cache across that
    // rebuild instead, which is the same invariant reaching the opposite
    // conclusion: what must never happen is a generation outliving the cache it
    // was measured against, in either direction.)
    let generation = handed ? handed.generation : null;
    /**
     * Measures the two geometric facts `firstVisibleSlot` needs and hands them to
     * it. The arithmetic itself is pure and tested in grid-window-first-visible
     * — it had a term missing once, and nothing in a happy-dom test could see it
     * because happy-dom reports every header as 0px tall.
     */
    function measureFirstVisible(w, rowH) {
        const rendered = w.end - w.start;
        if (!scroller)
            return 0;
        const header = opts.stickyHeader !== false
            ? scroller.querySelector('[data-grid-row="header"]')
            : null;
        const headerH = header ? header.getBoundingClientRect().height : 0;
        // Row 0's conceptual position — the same measurement, for the same reason,
        // as gridScrollRowIntoView below. It already covers the filter strip and
        // any future chrome above the rows without naming them.
        const pad = scroller.querySelector('[data-grid-pad-top]');
        const virtualTop = pad
            ? pad.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop
            : 0;
        return firstVisibleSlot({
            scrollTop: scroller.scrollTop,
            headerH,
            virtualTop,
            rowHeight: rowH,
            start: w.start,
            rendered,
        });
    }
    function project(w, firstVisible) {
        const rows = [];
        const failed = [];
        for (let i = w.start; i < w.end; i++) {
            rows.push(cache.rowAt(i));
            failed.push(cache.isFailedAt(i));
        }
        return {
            rows, failed, start: w.start, end: w.end, topPad: w.topPad, botPad: w.botPad,
            firstVisible,
        };
    }
    // Guards the synchronous cycle deliver → notify → recompute → request →
    // deliver. It terminates on its own (an accepted block is `held`, a failed
    // one is latched, so no block is ever asked for twice), but a caller serving
    // from a warm cache nests one frame per block and the re-entrant recompute
    // would re-measure and re-push a window nothing has moved. The outer frame
    // is the one whose window is authoritative.
    /**
     * The clientHeight the last recompute was based on; -1 until one has run.
     * Declared up here with the rest of the wire's state because `recomputeInner`
     * writes it and runs during attach, which is before the settle section below
     * is reached — a `let` down there would be in its temporal dead zone.
     */
    let measuredViewport = -1;
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
    /**
     * ── A DECLARATION CAN BE WRONG; A MEASUREMENT CANNOT ──────────────────────
     * `rowHeight` is what the caller declares, and the component forces it onto
     * the row — but `box-sizing` is content-box and Spec cannot set it (the
     * property appears nowhere in the compiler), so a 1px row border makes the
     * real row `rowHeight + 1`. Everything here is computed from the
     * declaration, so every row compounds a pixel of error.
     *
     * Measured in cf on a 783-row curve: rows rendered 41px against a declared
     * 40, the scroll range under-reported by ~780px, and arrowing down put the
     * focused row 18px BELOW the fold — 17px of drift by row 25. The drift
     * warning never fired, because 1px is inside its 2px tolerance.
     *
     * So: measure a real row the first time one exists, and use that from then
     * on. Re-measured only while uncalibrated, so this costs one layout read in
     * the life of the wire, not one per scroll.
     */
    let measuredRowHeight = 0;
    function calibrate() {
        if (measuredRowHeight > 0)
            return measuredRowHeight;
        if (!scroller)
            return opts.rowHeight;
        // EVERY row, not the first. `data-grid-row-index` sits on the same block
        // as `visibility: row._unloaded != true`, so an undelivered slot carries
        // the attribute and reports a ZERO box — and in a real grid the first
        // match is very often exactly that. 1.5.1 used querySelector here and so
        // never calibrated at all in cf, where a window opens on placeholders
        // while its first block is in flight.
        //
        // Hidden and rendered rows are indistinguishable by selector; only the box
        // tells them apart. This is the second measurement in this file that the
        // zero-box placeholder has broken.
        for (const row of scroller.querySelectorAll('[data-grid-row-index]')) {
            const h = row.getBoundingClientRect().height;
            if (h > 0) {
                measuredRowHeight = h;
                return h;
            }
        }
        return opts.rowHeight;
    }
    function recomputeInner(force) {
        const rowH = calibrate();
        // Remembered so `settle` can tell a height this wire has ALREADY measured
        // from one it has not. Without it the settle loop can only recognise the
        // zero case, and a stale non-zero height looks identical to a correct one.
        measuredViewport = scroller ? scroller.clientHeight : 0;
        const w = computeWindow({
            scrollTop: scroller ? scroller.scrollTop : 0,
            viewportHeight: measuredViewport,
            rowHeight: rowH,
            totalCount: rowCount,
            overscan: opts.overscan,
        });
        // Push only when the window actually moved. Without this the grid
        // re-renders on every scroll pixel, remounting every cell component 30
        // times per row of travel.
        // Measured ONCE per recompute and threaded through, rather than computed
        // again inside project(): it reads getBoundingClientRect twice, and this
        // runs on every scroll event.
        const fv = measureFirstVisible(w, rowH);
        // `firstVisible` is in the comparison because it can move while the window
        // does not: at the top of the list `start` is clamped at 0 while the first
        // on-screen row keeps climbing, and a stale value would leave the failed
        // block's only message behind the sticky header.
        //
        // ...but ONLY when something in the window has actually failed. `fv` is out
        // of phase with `start` whenever in-flow chrome sits above the rows (a
        // filter strip), so counting it unconditionally adds a push per row of
        // travel — measured at 40 -> 60 over 600px — and every push rebuilds the
        // whole window, which is the cost the `moved` guard exists to avoid.
        // Nothing but the failed-block message reads `winFirstVisible`.
        let anyFailed = false;
        for (let i = w.start; i < w.end && !anyFailed; i++) {
            if (cache.isFailedAt(i))
                anyFailed = true;
        }
        const moved = !last || last.start !== w.start || last.end !== w.end
            || (anyFailed && lastFirstVisible !== fv);
        if (!moved && !force)
            return;
        last = w;
        lastFirstVisible = fv;
        const reqs = cache.requestBlocksFor(w.start, w.end);
        onWindow(project(w, fv));
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
    // ~2s at 16ms. The old budget was 32 attempts — and `attempts` was consumed
    // by TWO chains at once (see below), so the real budget was ~256ms. A mount
    // delayed past that by a busy main thread or a container appended a frame
    // late left the grid permanently unscrollable, silently.
    const ATTACH_ATTEMPTS = 125;
    let attempts = 0;
    /** One try. Returns whether the scroll container was found and wired. */
    function tryAttach() {
        if (destroyed)
            return false;
        if (scroller)
            return true;
        scroller = document.querySelector(`[data-grid-id="${gridId}"] [data-grid-scroll]`);
        if (!scroller)
            return false;
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
        // ...except it is not, quite, and this is the second one that is.
        //
        // A windowed grid's scroll container gets its height from the SPACERS —
        // padTop/padBot are what stand in for the rows outside the window — and
        // those spacers are only written by the `onWindow` push inside the
        // recompute above. So at the moment that recompute measures, the scroller
        // holds nothing yet: clientHeight is 0, `computeWindow` returns just the
        // overscan, and the grid settles on a five-row window over a list of nine
        // hundred. The spacers it then writes give the scroller its real height,
        // one layout too late to be measured.
        //
        // The ResizeObserver above is supposed to catch exactly that, and usually
        // does — which is why this went unnoticed: the bug is invisible wherever RO
        // fires, and total wherever it does not. Measured 2026-08-26 on a
        // 900-flight logbook in a context with RO throttled: clientHeight 530px,
        // five rows rendered, and no scroll or resize ever correcting it.
        //
        // So this waits for the scroller to HAVE a height rather than for a fixed
        // number of frames. One rAF is not enough: the caller writes the spacers
        // through its own reactive layer, which batches, so the height can be two
        // or three frames out — and a fixed count would be a guess that is wrong on
        // a slow frame.
        //
        // Bounded, and it stops the moment it has something real to measure, so the
        // normal case costs one extra recompute. `moved` makes it a no-op when the
        // first measurement was already right.
        scheduleSettle();
        return true;
    }
    /**
     * Re-measure until the scroll container reports a height, or we run out of
     * patience. See the note in tryAttach for why the first measurement cannot be
     * trusted; this is what makes the second one honest without depending on a
     * ResizeObserver that a throttled or offscreen context may never fire.
     */
    const SETTLE_FRAMES = 30;
    let settleFrames = 0;
    /** Arm the settle watch. Always looks at least one frame into the future. */
    function scheduleSettle() {
        settleFrames = 0;
        if (typeof requestAnimationFrame === 'undefined')
            return;
        requestAnimationFrame(settle);
    }
    function settle() {
        if (destroyed || !scroller)
            return;
        const h = scroller.clientHeight;
        // A height nobody has measured yet. Two ways to get one, and the loop has
        // to cover both:
        //   0 -> real     the first attach, before any spacer has been written
        //   real -> real  a generation change. The caller's filter shrank or grew
        //                 the list, `invalidate` re-measured in the SAME layout,
        //                 and the container still had its old height; the spacers
        //                 that give it the new one are written a layout later.
        // The second is why this compares against `measuredViewport` rather than
        // testing `> 0`. Measured on a 900-flight logbook: deselecting an aircraft
        // filter left the wire holding the filtered container's 98px and rendering
        // one row into a 254px viewport, corrected only wherever RO happens to fire.
        if (h !== measuredViewport) {
            recompute(true);
        }
        else if (h > 0) {
            return; // stable, and real: nothing left to wait for
        }
        if (settleFrames++ >= SETTLE_FRAMES)
            return;
        if (typeof requestAnimationFrame === 'undefined')
            return;
        requestAnimationFrame(settle);
    }
    /**
     * THE ONLY thing that re-arms the timer. `attach()` used to schedule itself
     * on failure while the caller ALSO queued a microtask attempt — and that
     * microtask's run armed a second timer, overwriting the first id while the
     * first was still pending. Two live chains: `attempts` consumed twice per
     * tick, and `destroy()` able to clear only one of the two ids, so the other
     * kept firing after teardown.
     */
    function pollAttach() {
        waitTimer = null;
        if (destroyed || tryAttach())
            return;
        if (attempts++ >= ATTACH_ATTEMPTS) {
            // LOUD, and released. Silence here is what made this so hard to see: the
            // grid renders an overscan-sized window with numerically correct
            // spacers and simply never responds to a scroll again.
            console.error(`DataGrid: window wire for grid ${gridId} never found its scroll container ` +
                `([data-grid-id="${gridId}"] [data-grid-scroll]) after ${ATTACH_ATTEMPTS} attempts; ` +
                `giving up. The grid will not respond to scrolling.`);
            // Release rather than linger. `isDetached` reads `scroller != null &&
            // !scroller.isConnected`, which is false forever when the scroller was
            // never found — so the reaper could never collect this wire, and it held
            // its cache, its rows and its registry slot for the life of the page.
            handle.destroy();
            return;
        }
        waitTimer = setTimeout(pollAttach, 16);
    }
    const attached = tryAttach();
    if (!attached) {
        // Nothing to measure yet. Push a provisional window anyway so the grid
        // renders its spacers and asks for block 0 immediately rather than waiting
        // a turn; the poll forces a second push once it has a real clientHeight.
        //
        // The microtask is the FIRST attempt of the single chain, not a second
        // chain beside it — mount is synchronous, so one turn is normally all it
        // takes and the timer never arms at all.
        recompute(true);
        queueMicrotask(pollAttach);
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
                // Grid ids are minted per mount, so without this a route carrying a
                // windowed grid leaks one dead string per visit for the life of the
                // page.
                warnedRowHeight.delete(gridId);
            }
        },
        setRowCount(n) { rowCount = n; last = null; recompute(true); },
        // scheduleSettle because this recompute measures a container that is still
        // the PREVIOUS row set's size — see the note in `settle`.
        invalidate() { cache.invalidate(); last = null; recompute(true); scheduleSettle(); },
        refresh() { recompute(true); },
        // The FIRST key is adopted silently. There is nothing held to drop yet,
        // and invalidating here would burn a token before the opening request.
        effectiveRowHeight() { return calibrate(); },
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
        handOff(nextBlockSize) {
            // A destroyed wire has already released its listeners and may have been
            // reaped; its cache is not ours to lend.
            if (destroyed)
                return null;
            if (nextBlockSize !== opts.blockSize)
                return null;
            return { cache, generation };
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
    handle.stickyHeader = opts.stickyHeader !== false;
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
 * Release whatever wire is registered under `gridId`.
 *
 * `_windowTeardown` destroys the previous wire only INSIDE wireGridWindow, so
 * the `: null` branch — taken the moment `windowed && !guarded` becomes false,
 * which any filter returning zero rows does — used to destroy nothing. The
 * wire kept its scroll listener, its ResizeObserver and its registered cache,
 * and the reaper could not collect it because an unguarded grid still has its
 * scroll container in the document, so `isDetached` stays false. Worse, the
 * orphan's internal `rowCount` was still the old total, so scrolling kept
 * emitting `rangeNeeded` — making the caller fetch a hundred rows to feed a
 * cache nothing on screen reads.
 *
 * Returns null so it can be the other arm of that `@computed`.
 */
export function releaseGridWindow(gridId) {
    wires.get(gridId)?.destroy();
    return null;
}
/**
 * A windowed grid's whole geometry — spacer heights, which rows the window
 * covers, and therefore what the scrollbar represents — is computed from the
 * DECLARED `rowHeight`. Nothing makes the body row honour it: only the
 * skeleton and failed rows set an explicit height, so cell padding decides the
 * real one. In the reference harness a declared 30 renders at 41.
 *
 * The consequence is a scrollbar that lies about the size of the list, by
 * (actual - declared) x rowCount — roughly 11,000px over 1,043 rows there.
 * Task 11 measured the symptom and mis-attributed it: it recorded scrollHeight
 * 31,598 against 31,290 of "bare rows" and put the 308px difference down to
 * "sticky header + borders", when it was 30 rendered rows each 11px taller
 * than declared.
 *
 * Warned once per grid rather than fixed here: making the row honour
 * `rowHeight` changes rendering for every windowed consumer and wants its own
 * change. Silence is worse — the failure is purely geometric, so no test that
 * cannot lay out will ever see it.
 */
const warnedRowHeight = new Set();
function warnOnRowHeightDrift(gridId, declared, measured) {
    if (warnedRowHeight.has(gridId))
        return;
    // A pixel of border is expected and harmless; 11 is not.
    if (Math.abs(measured - declared) <= 2)
        return;
    warnedRowHeight.add(gridId);
    console.error(`DataGrid: grid ${gridId} declares rowHeight ${declared} but renders rows at ` +
        `${Math.round(measured)}px. Windowing computes spacers and the scroll range from the ` +
        `declared value, so the scrollbar misrepresents the list by about ` +
        `${Math.round(Math.abs(measured - declared))}px per row. Set rowHeight to the height the ` +
        `row actually renders at, or reduce cell padding.`);
}
/**
 * Scroll a windowed grid so that absolute row `index` is on screen.
 *
 * Keyboard navigation walks the whole grid, not the window, so arrowing off
 * the edge must move the window — otherwise focus advances into rows that are
 * not rendered and the highlight simply disappears, which reads as a broken
 * grid rather than a scrolled one.
 *
 * Nudges by the minimum needed (the row's top when going up, its bottom when
 * going down) rather than centring, so held-down arrow keys travel one row at
 * a time instead of jumping half a viewport. Already-visible rows are left
 * alone, so this is safe to call on every keystroke.
 *
 * Unknown id, no scroller, or a non-positive rowHeight: no-op. An unwindowed
 * or guarded grid has no wire, and both reach this through the same action.
 */
export function gridScrollRowIntoView(gridId, index, rowHeight) {
    if (!(rowHeight > 0) || !(index >= 0))
        return null;
    // The CALIBRATED height for the estimate below, not the declared one. This
    // path is taken precisely when the target row is not rendered — which is
    // every keypress that walks past the edge of the window — so a declaration
    // that is 1px out lands the row a row-per-25 below the fold. Measured in cf
    // before this: 17px of drift by row 25, and the focused row off screen.
    rowHeight = wires.get(gridId)?.effectiveRowHeight() ?? rowHeight;
    const root = document.querySelector(`[data-grid-id="${gridId}"]`);
    const scroller = root?.querySelector('[data-grid-scroll]');
    if (!scroller)
        return null;
    const viewTop = scroller.scrollTop;
    const viewBottom = viewTop + scroller.clientHeight;
    // MEASURED when the row is on screen, computed only when it is not.
    //
    // `rowHeight` describes what the caller declared, and the body row does not
    // enforce it — cell padding makes the rendered row taller, by 11px on 30 in
    // the reference harness. Scrolling from the declaration alone therefore
    // lands short by (actual - declared) x index, which is hundreds of pixels a
    // page down: the row is "scrolled to" and still off screen.
    //
    // A row outside the window has no element to measure, so the arithmetic is
    // the estimate that gets the window close; the caller calls again once it
    // has rendered, and that pass measures.
    // Scoped to THIS grid: a DataGrid nested inside a cell stamps the same
    // attribute, and its rows precede the outer grid's later rows in document
    // order, so an unscoped query can measure the inner grid's row.
    const el = Array.from(root.querySelectorAll(`[data-grid-row-index="${index}"]`)).find((n) => n.closest('[data-grid-id]') === root);
    // A row with NO LAYOUT BOX is not a measurable row. `data-grid-row-index`
    // sits on the same block as `visibility: row._unloaded != true`, and
    // `visibility:` compiles to display:none — it hides, it does not omit — so
    // an undelivered slot is still found here and reports a rect of all zeros.
    // Measuring that gives `top = 0 - scrollerTop + viewTop`, always less than
    // viewTop, so the grid scrolls BACKWARDS; the next keypress finds nothing,
    // takes the estimate, and scrolls forward again. Focus advances while the
    // viewport oscillates toward 0, on any grid whose fetch is slower than a
    // held-down arrow key.
    const rect = el ? el.getBoundingClientRect() : null;
    const measurable = rect !== null && rect.height > 0;
    let top;
    let bottom;
    if (measurable) {
        // offsetTop is relative to the offset parent, which is not necessarily the
        // scroller — go through the rects and add the scroll position back.
        const r = rect;
        const s = scroller.getBoundingClientRect();
        top = r.top - s.top + viewTop;
        bottom = top + r.height;
        warnOnRowHeightDrift(gridId, rowHeight, r.height);
    }
    else {
        // ROW 0 IS NOT AT OFFSET 0. The composite header — and the filter strip,
        // when there is one — live INSIDE `[data-grid-scroll]`, so the virtual
        // area starts below them. `index * rowHeight` is short by exactly that
        // much, which put every fallback scroll one header-height too high: the
        // row was "scrolled to" and sitting just under the fold.
        //
        // The top spacer marks where the virtual area begins, and its own height
        // is already the rows above the window, so its TOP is row 0's conceptual
        // position. Measuring it covers the filter strip and any future chrome
        // without naming them.
        const pad = scroller.querySelector('[data-grid-pad-top]');
        const virtualTop = pad
            ? pad.getBoundingClientRect().top - scroller.getBoundingClientRect().top + viewTop
            : 0;
        top = virtualTop + index * rowHeight;
        bottom = top + rowHeight;
    }
    // The header scrolls WITH the content and sits above row 0 inside the same
    // container, so a row aligned to `top` hides underneath a sticky one.
    //
    // ...and only underneath a STICKY one. With `stickyHeader: false` the header
    // scrolls away like any other content and occludes nothing, so subtracting it
    // over-scrolls by a full header on every keypress that reaches the top edge.
    // Same fact, same fix as measureFirstVisible above.
    const sticky = wires.get(gridId)?.stickyHeader !== false;
    const header = sticky
        ? scroller.querySelector('[data-grid-row="header"]')
        : null;
    const headerH = header ? header.getBoundingClientRect().height : 0;
    if (top - headerH < viewTop)
        scroller.scrollTop = Math.max(0, top - headerH);
    else if (bottom > viewBottom)
        scroller.scrollTop = bottom - scroller.clientHeight;
    else
        return null;
    // The scroll listener fires asynchronously; the window the caller is about
    // to render from must reflect the new position NOW, or the keypress renders
    // one frame behind its own scroll.
    wires.get(gridId)?.refresh();
    return null;
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