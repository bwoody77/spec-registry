/**
 * drag-core/pointer — `createDragSession` backed by Pointer Events.
 *
 * Use this mode when:
 *   - You don't need to drag content out of the browser window.
 *   - You want a single code path for mouse + touch + pen.
 *   - You want full control over the ghost element (no native drag image).
 *
 * If you DO need cross-window or desktop drag-out (e.g. drag a list item
 * into Slack as a URL), import from `./html5` instead.
 *
 * The exported `createDragSession` has the same signature as the one in
 * `./html5`, so callers can swap modes by changing the import path.
 *
 * Bundle: importing from this module pulls in `shared.ts` + this file
 * (~130 lines together). The HTML5 path is NOT included.
 */
import { DRAG_MOUSE_MOVE_START, DRAG_TOUCH_HOLD_MS, DRAG_TOUCH_MOVE_CANCEL, installEscListener, isInHandle, makeGhost, targetsEqual, } from './shared.js';
/**
 * Create a Pointer Events-based drag session.
 *
 * Lifecycle:
 *   1. Caller calls `attach(srcEl)` for each draggable element.
 *   2. On pointerdown (mouse) or after touchHoldMs (touch), drag begins:
 *      `onStart` fires, the ghost element appears, the cursor becomes 'grabbing'.
 *   3. On every pointermove, `hitTest(x, y)` runs. If the target changed,
 *      `onTargetChange(new, prev)` fires.
 *   4. On pointerup, if a target is present, `onDrop(srcId, target)` fires.
 *      Otherwise `onCancel(srcId)` fires.
 *   5. `onEnd(srcId)` always fires last (after drop OR cancel).
 *   6. ESC during drag cancels (calls `onCancel` then `onEnd`).
 *   7. Caller calls `destroy()` to tear everything down on unmount.
 */
export function createDragSession(opts) {
    const touchHoldMs = opts.touchHoldMs ?? DRAG_TOUCH_HOLD_MS;
    const touchMoveCancel = opts.touchMoveCancel ?? DRAG_TOUCH_MOVE_CANCEL;
    const mouseMoveStart = opts.mouseMoveStart ?? DRAG_MOUSE_MOVE_START;
    const cancelOnEsc = opts.cancelOnEsc !== false;
    // Active-drag state. Held in closure (not per-element) because at most one
    // drag is active at a time.
    let activeSrcEl = null;
    let activeSrcId = null;
    let ghost = null;
    let lastTarget = null;
    let escCleanup = null;
    let pendingPointerId = null;
    let pendingSrcEl = null;
    let pendingSrcId = null;
    let pendingStartX = 0;
    let pendingStartY = 0;
    let pendingTimer = null;
    let dragStarted = false;
    const attached = new WeakMap();
    function clearPending() {
        if (pendingTimer != null) {
            clearTimeout(pendingTimer);
            pendingTimer = null;
        }
        pendingPointerId = null;
        pendingSrcEl = null;
        pendingSrcId = null;
    }
    function endDrag(reason, target) {
        if (!dragStarted || !activeSrcId) {
            // Drag was pending but never started (e.g. quick tap). Clean up
            // pending state and exit silently.
            clearPending();
            return;
        }
        const srcId = activeSrcId;
        if (reason === 'drop' && target != null) {
            opts.onDrop(srcId, target);
        }
        else {
            opts.onCancel?.(srcId);
        }
        opts.onEnd?.(srcId);
        // Reset state
        ghost?.destroy();
        ghost = null;
        if (escCleanup) {
            escCleanup();
            escCleanup = null;
        }
        document.removeEventListener('pointermove', onPointerMove);
        document.removeEventListener('pointerup', onPointerUp);
        document.removeEventListener('pointercancel', onPointerCancel);
        activeSrcEl = null;
        activeSrcId = null;
        lastTarget = null;
        dragStarted = false;
        clearPending();
    }
    function startDrag(srcEl, srcId, clientX, clientY) {
        dragStarted = true;
        activeSrcEl = srcEl;
        activeSrcId = srcId;
        ghost = makeGhost(srcEl, clientX, clientY, opts.ghost ?? 'clone', opts.ghostStyle);
        opts.onStart?.(srcId, srcEl);
        // Initial hit-test so onTargetChange fires immediately if we begin
        // already over a valid target.
        const initial = opts.hitTest(clientX, clientY);
        if (initial != null) {
            opts.onTargetChange?.(initial, null);
            lastTarget = initial;
        }
        if (cancelOnEsc) {
            escCleanup = installEscListener(() => endDrag('cancel', null));
        }
    }
    function onPointerMove(e) {
        if (pendingPointerId != null && !dragStarted) {
            const dx = Math.abs(e.clientX - pendingStartX);
            const dy = Math.abs(e.clientY - pendingStartY);
            if (e.pointerType === 'touch') {
                // Touch hold-delay path: cancel if the user moved too far before
                // the timer fired (treated as scroll intent, not drag).
                if (dx + dy > touchMoveCancel) {
                    clearPending();
                    document.removeEventListener('pointermove', onPointerMove);
                    document.removeEventListener('pointerup', onPointerUp);
                    document.removeEventListener('pointercancel', onPointerCancel);
                }
            }
            else {
                // Mouse / pen: drag begins once movement exceeds the threshold.
                // Below the threshold, pointerup is treated as a click and the
                // source's own onclick handler runs (we never preventDefault'd).
                if (dx + dy >= mouseMoveStart && pendingSrcEl && pendingSrcId != null) {
                    // Steal the click — this prevents the source's click from firing
                    // when the user actually meant to drag.
                    startDrag(pendingSrcEl, pendingSrcId, e.clientX, e.clientY);
                }
            }
            return;
        }
        if (!dragStarted)
            return;
        // Active drag: move ghost, run hit-test, fire onTargetChange on diff.
        e.preventDefault();
        ghost?.moveTo(e.clientX, e.clientY);
        const next = opts.hitTest(e.clientX, e.clientY);
        if (!targetsEqual(next, lastTarget)) {
            opts.onTargetChange?.(next, lastTarget);
            lastTarget = next;
        }
    }
    function onPointerUp(e) {
        if (!dragStarted) {
            clearPending();
            document.removeEventListener('pointermove', onPointerMove);
            document.removeEventListener('pointerup', onPointerUp);
            document.removeEventListener('pointercancel', onPointerCancel);
            return;
        }
        const finalTarget = opts.hitTest(e.clientX, e.clientY);
        endDrag(finalTarget != null ? 'drop' : 'cancel', finalTarget);
    }
    function onPointerCancel() {
        if (dragStarted) {
            endDrag('cancel', null);
        }
        else {
            clearPending();
            document.removeEventListener('pointermove', onPointerMove);
            document.removeEventListener('pointerup', onPointerUp);
            document.removeEventListener('pointercancel', onPointerCancel);
        }
    }
    function onPointerDown(srcEl, e) {
        if (dragStarted || pendingPointerId != null)
            return;
        if (!isInHandle(srcEl, e.target, opts.handle))
            return;
        if (e.button !== 0 && e.pointerType === 'mouse')
            return; // primary button only
        const srcId = opts.getSrcId(srcEl);
        if (srcId == null)
            return;
        // Stop the pointerdown from bubbling to ancestor draggable elements.
        // Without this, a drag handle nested inside a larger draggable (e.g.
        // a resize-edge inside a move-draggable schedule block) would fire
        // BOTH sessions' pointerdown — both go pending and both start dragging
        // on the same pointermove. stopPropagation lets the inner element
        // claim the pointer exclusively.
        e.stopPropagation();
        pendingPointerId = e.pointerId;
        pendingSrcEl = srcEl;
        pendingSrcId = srcId;
        pendingStartX = e.clientX;
        pendingStartY = e.clientY;
        document.addEventListener('pointermove', onPointerMove, { passive: false });
        document.addEventListener('pointerup', onPointerUp);
        document.addEventListener('pointercancel', onPointerCancel);
        if (e.pointerType === 'touch') {
            // Touch: wait for hold-delay before starting drag. This lets quick
            // taps still register as taps (and lets vertical scroll begin if the
            // finger moves past the cancel threshold during the wait).
            pendingTimer = setTimeout(() => {
                pendingTimer = null;
                if (pendingPointerId == null)
                    return;
                startDrag(srcEl, srcId, pendingStartX, pendingStartY);
            }, touchHoldMs);
        }
        // Mouse / pen: don't startDrag yet — onPointerMove starts it once
        // movement exceeds mouseMoveStart. Until then, pointerup acts as a
        // click and the source's own click handler runs. mouseMoveStart=0
        // (set by caller) reverts to the old "drag immediately" behavior.
        else if (mouseMoveStart === 0) {
            e.preventDefault();
            startDrag(srcEl, srcId, e.clientX, e.clientY);
        }
    }
    function attach(srcEl) {
        if (attached.has(srcEl))
            return;
        const handler = (e) => onPointerDown(srcEl, e);
        srcEl.addEventListener('pointerdown', handler);
        // touch-action: none on the source disables native scrolling/zoom on
        // the draggable. This is what lets us preventDefault on pointermove
        // for touch drags. Saved via inline style so detach() can restore it.
        const prevTouchAction = srcEl.style.touchAction;
        srcEl.style.touchAction = 'none';
        attached.set(srcEl, () => {
            srcEl.removeEventListener('pointerdown', handler);
            srcEl.style.touchAction = prevTouchAction;
        });
    }
    function detach(srcEl) {
        const cleanup = attached.get(srcEl);
        if (cleanup) {
            cleanup();
            attached.delete(srcEl);
        }
    }
    function destroy() {
        if (dragStarted || pendingPointerId != null) {
            endDrag('cancel', null);
        }
        // attached is a WeakMap — we don't enumerate. Caller should detach()
        // each element it attached, OR rely on GC once the elements are removed
        // from the DOM. document-level listeners are already cleaned up above.
    }
    return { attach, detach, destroy };
}
//# sourceMappingURL=pointer.js.map