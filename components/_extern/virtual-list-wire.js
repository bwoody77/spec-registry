/**
 * virtual-list-wire.ts — the only part of VirtualList that touches the DOM.
 *
 * It answers ONE question: how tall is the scroll container right now. That is
 * what removes the `viewportHeight: number` prop, which a phone caller cannot
 * honestly supply — the visible height there changes with the software
 * keyboard, with the URL bar collapsing on scroll, and with rotation, and iOS
 * Safari does not reliably fire `resize` for the second of those.
 *
 * ── WHY THIS IS NOT grid-window-wire, AND IS NOT A COPY OF IT ──────────────
 * DataGrid's wire carries ~150 lines of settle logic whose comments each cite a
 * real measured failure. Almost all of it exists for one reason that does NOT
 * apply here: a windowed grid's scroll container gets its height FROM ITS OWN
 * SPACERS, so the first measurement is structurally 0 and the honest height
 * arrives a layout later, via a ResizeObserver that a throttled context may
 * never fire. Hence the bounded rAF settle loop that waits for the scroller to
 * *have* a height.
 *
 * VirtualList's scroller takes an explicit CSS height from a sized parent
 * (`height: 100%` of a flex item, or a pixel value). Its clientHeight is
 * layout-derived, not content-derived, so it is real on the first layout after
 * the element is in the document, whatever the spacers say. That makes this a
 * genuinely smaller problem rather than a second copy of a solved one.
 *
 * The corollary is a REQUIREMENT on the caller, and it is why `height` defaults
 * to a pixel value rather than '100%': give VirtualList a parent with a
 * resolvable height. Hand it `height: 'auto'` inside an unsized box and its
 * clientHeight becomes content-derived, at which point you are in DataGrid's
 * world and this module is not enough.
 *
 * Everything else — the window arithmetic — stays in grid-window.ts, pure and
 * shared with DataGrid. Nothing here computes a window.
 */
/**
 * Live wires by list id.
 *
 * VirtualList calls `wireVirtualList` from a `@computed`, exactly as DataGrid
 * does, and a computed re-runs whenever its deps change — so without this map a
 * caller whose `totalCount` moves would leave the previous wire's
 * ResizeObserver attached and add another. That is the shape of the
 * "listeners added per mount, never removed" leak this package already has
 * history with, so the re-entry is handled here rather than left to callers.
 */
const wires = new Map();
/** Wires whose element may have gone away without anyone telling us. */
const live = new Set();
let reaper = null;
function sweep() {
    // Snapshot: destroy() mutates `live` while we iterate it.
    for (const w of Array.from(live))
        if (w.isDetached())
            w.destroy();
}
function watchForDetach(w) {
    live.add(w);
    if (reaper || typeof MutationObserver === 'undefined')
        return;
    reaper = new MutationObserver(sweep);
    // `document`, not `document.body`: a list need not be under body, and body
    // itself can be replaced.
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
/**
 * Watch the scroll container of the VirtualList stamped `data-virtual-list=id`
 * and report its height whenever it changes.
 *
 * Returns a teardown. Calling it again for the same id destroys the previous
 * wire first, so the truthy arm of a `@computed` cleans up after itself.
 */
export function wireVirtualList(listId, onHeight) {
    releaseVirtualList(listId);
    let destroyed = false;
    let scroller = null;
    let ro = null;
    let timer = null;
    /** The height last pushed. -1 so that a genuine 0 is still reported once. */
    let measured = -1;
    function push() {
        if (destroyed || !scroller)
            return;
        const h = scroller.clientHeight;
        if (h === measured)
            return;
        measured = h;
        onHeight(h);
    }
    /**
     * The element is not in the document when this runs.
     *
     * The compiler emits every `@computed` ABOVE the DOM section of the mount
     * function, and the mount appends its root to the container on its LAST line
     * — so a single query finds nothing, and a wire that queried once and gave up
     * would leave the list permanently unable to size itself. That failure is
     * silent: a viewportHeight of 0 yields an overscan-sized window and spacers
     * that are numerically consistent, so the list renders a handful of rows and
     * simply never responds to a resize.
     */
    const ATTACH_ATTEMPTS = 125; // ~2s at 16ms
    let attempts = 0;
    function tryAttach() {
        if (destroyed)
            return false;
        if (scroller)
            return true;
        scroller = document.querySelector(`[data-virtual-list="${listId}"]`);
        if (!scroller)
            return false;
        // The list's height changes without any scroll — a sibling panel opening,
        // a rotation, the keyboard — and a stale height renders too few rows at
        // the bottom.
        if (typeof ResizeObserver !== 'undefined') {
            ro = new ResizeObserver(() => push());
            ro.observe(scroller);
        }
        push();
        // One frame later as well. The parent that gives this element its height
        // may itself be sized by a layout that has not run yet (a flex sibling
        // still being appended), and unlike DataGrid we are not waiting on our own
        // spacers — one frame is enough, so this is a single rAF rather than a
        // settle loop.
        if (typeof requestAnimationFrame !== 'undefined') {
            requestAnimationFrame(() => push());
        }
        return true;
    }
    function pollAttach() {
        if (destroyed || scroller)
            return;
        if (tryAttach())
            return;
        if (attempts++ >= ATTACH_ATTEMPTS) {
            // Bounded — an unmounted list stops asking. And it TEARS DOWN rather than
            // merely stopping: a wire that gives up still sat in `wires` and `live`
            // with `isDetached()` permanently false (its scroller is null), so the
            // document-wide MutationObserver reaper it registered was kept alive for
            // the rest of the session with nothing left to reap. Given this package's
            // history with per-mount listeners that are never released, giving up has
            // to mean giving up completely.
            wire.destroy();
            return;
        }
        timer = setTimeout(pollAttach, 16);
    }
    const wire = {
        isDetached: () => !!scroller && !scroller.isConnected,
        destroy: () => {
            if (destroyed)
                return;
            destroyed = true;
            if (timer !== null) {
                clearTimeout(timer);
                timer = null;
            }
            if (ro) {
                ro.disconnect();
                ro = null;
            }
            scroller = null;
            unwatchForDetach(wire);
            if (wires.get(listId) === wire)
                wires.delete(listId);
        },
    };
    wires.set(listId, wire);
    watchForDetach(wire);
    // AFTER `wire` exists, because pollAttach() calls wire.destroy() when it
    // gives up and `const` bindings are in the temporal dead zone until then.
    // Mount is synchronous, so the microtask queue is normally all it takes; the
    // bounded poll is the fallback for a container appended a frame late.
    if (!tryAttach()) {
        if (typeof queueMicrotask === 'function')
            queueMicrotask(() => { if (!scroller && !destroyed)
                pollAttach(); });
        else
            pollAttach();
    }
    return wire.destroy;
}
/**
 * Destroy the wire for `listId`, if any.
 *
 * Needed as its own export for the same reason `releaseGridWindow` is: the
 * falsy arm of the caller's `@computed` must not abandon a live wire. Returns
 * null so it can BE that arm.
 */
export function releaseVirtualList(listId) {
    const w = wires.get(listId);
    if (w)
        w.destroy();
    return null;
}
let seq = 0;
/** A DOM-unique id for one VirtualList instance, minted in `@state`. */
export function genVirtualListId() {
    seq += 1;
    return `vl-${seq}-${Math.random().toString(36).slice(2, 8)}`;
}
//# sourceMappingURL=virtual-list-wire.js.map