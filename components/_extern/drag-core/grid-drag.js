/**
 * grid-drag — high-level drag helper for 2D grid surfaces.
 *
 * Use cases: scheduling grids (aircraft × time), Gantt charts (resource × day),
 * hangar-layout planners (slot × time), seating charts, etc. Anywhere the
 * drop target is a fixed cell in a 2D layout, this helper owns the cell
 * snap, optional auto-scroll, and the click-vs-drag distinction so callers
 * can focus on commit logic.
 *
 * Built on top of `./pointer` — in-window only. If you need to drag grid
 * cells out of the browser, use `./html5` directly with a custom hit-test.
 *
 * ───────────────────────────────────────────────────────────────────────
 * Cell convention
 * ───────────────────────────────────────────────────────────────────────
 * Each drop target cell in your DOM should carry data attributes that
 * uniquely identify the cell. Default convention is `data-grid-row` and
 * `data-grid-col`, but callers can configure any selector + extractor.
 *
 *   <div data-ac-id="N2845P" data-hour="9">…</div>
 *
 * grid-drag uses `document.elementFromPoint(x, y)` on each move and walks
 * up to find the nearest cell matching the configured selector — that
 * means cells can be ANYWHERE in the DOM (no constraint that they share
 * a parent), and they don't have to be children of the drag's container.
 *
 * ───────────────────────────────────────────────────────────────────────
 * Auto-scroll
 * ───────────────────────────────────────────────────────────────────────
 * Pass `scrollContainer` to enable edge-scrolling — when the pointer is
 * within `scrollEdgePx` of the container's edge, the container scrolls
 * by `scrollSpeedPx` per animation frame in that direction. Useful for
 * grids wider than the viewport.
 */
import { createDragSession } from './pointer.js';
// ─── Implementation ─────────────────────────────────────────────────────────
/**
 * Mount a grid-drag helper. Returns a handle with `refresh()` for use when
 * the source set changes (e.g. items added/removed) and `destroy()` for
 * teardown on unmount.
 */
export function mountGridDrag(opts) {
    const cellSelector = opts.cellSelector ?? '[data-grid-row][data-grid-col]';
    // ─── Auto-scroll loop ─────────────────────────────────────────────────
    const scrollContainer = opts.scrollContainer ?? null;
    const scrollEdgePx = opts.scrollEdgePx ?? 40;
    const scrollSpeedPx = opts.scrollSpeedPx ?? 8;
    let scrollRafId = null;
    let lastPointerX = 0;
    let lastPointerY = 0;
    function scrollTick() {
        if (!scrollContainer)
            return;
        const rect = scrollContainer.getBoundingClientRect();
        const x = lastPointerX;
        const y = lastPointerY;
        let dx = 0;
        let dy = 0;
        if (x - rect.left < scrollEdgePx)
            dx = -scrollSpeedPx;
        else if (rect.right - x < scrollEdgePx)
            dx = scrollSpeedPx;
        if (y - rect.top < scrollEdgePx)
            dy = -scrollSpeedPx;
        else if (rect.bottom - y < scrollEdgePx)
            dy = scrollSpeedPx;
        if (dx !== 0 || dy !== 0) {
            scrollContainer.scrollLeft += dx;
            scrollContainer.scrollTop += dy;
        }
        scrollRafId = requestAnimationFrame(scrollTick);
    }
    function startScrollLoop() {
        if (!scrollContainer || scrollRafId != null)
            return;
        scrollRafId = requestAnimationFrame(scrollTick);
    }
    function stopScrollLoop() {
        if (scrollRafId != null) {
            cancelAnimationFrame(scrollRafId);
            scrollRafId = null;
        }
    }
    // ─── Hit-test ────────────────────────────────────────────────────────
    // Use elementsFromPoint (plural) so we walk past overlapping draggable
    // sources (the dragged block sits ON TOP of the cells underneath it —
    // single elementFromPoint would return the block, whose closest() up
    // doesn't find a cell). The first ancestor matching cellSelector among
    // the layered elements is the cell underneath any source/preview/ghost.
    function hitTest(x, y) {
        lastPointerX = x;
        lastPointerY = y;
        const stack = document.elementsFromPoint(x, y);
        for (const el of stack) {
            const cell = el.closest(cellSelector);
            if (cell)
                return opts.cellToTarget(cell, x, y);
        }
        return null;
    }
    // ─── Underlying drag session ─────────────────────────────────────────
    const session = createDragSession({
        getSrcId: opts.getSrcId,
        handle: opts.handle,
        ghost: opts.ghost ?? 'none',
        ghostStyle: opts.ghostStyle,
        touchHoldMs: opts.touchHoldMs,
        touchMoveCancel: opts.touchMoveCancel,
        mouseMoveStart: opts.mouseMoveStart,
        cancelOnEsc: opts.cancelOnEsc,
        onStart(srcId, srcEl) {
            startScrollLoop();
            opts.onDragStart?.(srcId, srcEl);
        },
        hitTest,
        onTargetChange: opts.onTargetChange,
        onDrop: opts.onDrop,
        onCancel: opts.onCancel,
        onEnd(srcId) {
            stopScrollLoop();
            opts.onDragEnd?.(srcId);
        },
    });
    // ─── Source attachment ───────────────────────────────────────────────
    const attached = new Set();
    function resolveSources() {
        if (Array.isArray(opts.sources))
            return opts.sources;
        return Array.from(opts.container.querySelectorAll(opts.sources));
    }
    function syncAttachments() {
        const next = new Set(resolveSources());
        // Detach removed
        for (const el of attached) {
            if (!next.has(el)) {
                session.detach(el);
                attached.delete(el);
            }
        }
        // Attach new
        for (const el of next) {
            if (!attached.has(el)) {
                session.attach(el);
                attached.add(el);
            }
        }
    }
    syncAttachments();
    return {
        refresh: syncAttachments,
        destroy() {
            stopScrollLoop();
            for (const el of attached)
                session.detach(el);
            attached.clear();
            session.destroy();
        },
    };
}
//# sourceMappingURL=grid-drag.js.map