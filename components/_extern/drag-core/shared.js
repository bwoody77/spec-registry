/**
 * drag-core/shared — bits used by both Pointer Events and HTML5 DnD modes.
 *
 * Public-API additions go in `pointer.ts` or `html5.ts`. This module is the
 * implementation primitives both of those build on, plus the public types
 * that describe the API surface (which is identical between the two modes).
 *
 * Nothing here is browser-coupled to a specific event model — it's just
 * touch-state plumbing, ghost-element rendering, ESC handling, and a few
 * constants. Mode-specific code (pointerdown vs dragstart) lives in the
 * sibling files and imports what it needs from here.
 */
// ─── Constants ──────────────────────────────────────────────────────────────
/**
 * Touch must be held for this long before drag begins. Lower values fight
 * with native scroll; higher values feel sluggish. 200ms is what sortable
 * and kanban have shipped with — kept here for API stability.
 */
export const DRAG_TOUCH_HOLD_MS = 200;
/**
 * Touch movement during the hold-delay that cancels the drag (instead a
 * scroll begins). 8px is wider than typical jitter, narrower than an
 * intentional drag.
 */
export const DRAG_TOUCH_MOVE_CANCEL = 8;
/**
 * Mouse/pen movement before drag begins. Below this, pointerup acts as a
 * click (source's own click handlers run). 5px is the conventional value
 * for distinguishing click from drag.
 */
export const DRAG_MOUSE_MOVE_START = 5;
// ─── Ghost element ──────────────────────────────────────────────────────────
const DEFAULT_GHOST_CSS = [
    'position:fixed',
    'opacity:0.85',
    'box-shadow:0 8px 24px rgba(0,0,0,0.15)',
    'pointer-events:none',
    'z-index:9999',
    'margin:0',
    'transform:scale(1.03)',
    'border-radius:8px',
    'transition:none',
].join(';');
export function createGhost(srcEl, pointerX, pointerY, styleOverride) {
    const rect = srcEl.getBoundingClientRect();
    const offsetX = pointerX - rect.left;
    const offsetY = pointerY - rect.top;
    const ghost = srcEl.cloneNode(true);
    ghost.style.cssText = `${DEFAULT_GHOST_CSS};left:${rect.left}px;top:${rect.top}px;width:${rect.width}px;`;
    if (styleOverride) {
        Object.assign(ghost.style, styleOverride);
    }
    document.body.appendChild(ghost);
    let destroyed = false;
    return {
        el: ghost,
        moveTo(clientX, clientY) {
            if (destroyed)
                return;
            ghost.style.left = `${clientX - offsetX}px`;
            ghost.style.top = `${clientY - offsetY}px`;
        },
        destroy() {
            if (destroyed)
                return;
            destroyed = true;
            ghost.remove();
        },
    };
}
/**
 * Build a ghost using the caller's chosen strategy. Returns null when
 * `ghost: 'none'` was selected — caller renders its own preview.
 */
export function makeGhost(srcEl, pointerX, pointerY, strategy, styleOverride) {
    if (strategy === 'none')
        return null;
    if (typeof strategy === 'function') {
        const el = strategy(srcEl);
        document.body.appendChild(el);
        const rect = srcEl.getBoundingClientRect();
        const offsetX = pointerX - rect.left;
        const offsetY = pointerY - rect.top;
        let destroyed = false;
        return {
            el,
            moveTo(clientX, clientY) {
                if (destroyed)
                    return;
                el.style.left = `${clientX - offsetX}px`;
                el.style.top = `${clientY - offsetY}px`;
            },
            destroy() {
                if (destroyed)
                    return;
                destroyed = true;
                el.remove();
            },
        };
    }
    // Default 'clone'
    return createGhost(srcEl, pointerX, pointerY, styleOverride);
}
// ─── ESC-cancel listener ────────────────────────────────────────────────────
/**
 * Install a one-shot keydown listener that fires `onEsc` when ESC is pressed.
 * Returns a cleanup function. Used by both modes during an active drag.
 */
export function installEscListener(onEsc) {
    const handler = (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            onEsc();
        }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
}
// ─── Handle-selector resolution ─────────────────────────────────────────────
/**
 * Returns true if `e.target` is inside `srcEl`'s drag handle. When no handle
 * selector is configured, every drag start on `srcEl` is allowed.
 *
 * Callers wire this into their pointerdown / dragstart / touchstart guard.
 */
export function isInHandle(srcEl, target, handle) {
    if (!handle)
        return true;
    const t = target;
    if (!t)
        return false;
    const matched = t.closest(handle);
    return matched != null && srcEl.contains(matched);
}
// ─── Target-change diff (drives onTargetChange) ─────────────────────────────
/**
 * Compare two targets for equality. Default uses JSON.stringify because
 * targets are typically small, plain-data descriptors. Callers with hot
 * paths can pass a custom comparator via the per-mode opts.
 */
export function targetsEqual(a, b) {
    if (a === b)
        return true;
    if (a == null || b == null)
        return false;
    return JSON.stringify(a) === JSON.stringify(b);
}
//# sourceMappingURL=shared.js.map