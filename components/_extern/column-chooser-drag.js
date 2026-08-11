/**
 * ColumnChooser list drag — grip-drag a row, or a whole group, to reorder.
 *
 * Rides `drag-core/grid-drag.js`, whose hit-test walks up from
 * `elementsFromPoint` to the nearest row, so the ghost sitting under the cursor
 * never blocks the target beneath it.
 *
 * ── The drop affordance ─────────────────────────────────────────────────────
 * The drop target is a REAL SLOT the height of whatever is being carried — one
 * row for a column, the whole block for a group. The rows being dragged leave
 * the flow for the duration, so the list closes up behind them and the slot is
 * the only space in it.
 *
 * An insertion LINE was the first attempt and it is wrong: it sits underneath
 * the ghost the user is dragging, so the one thing they need to see is the one
 * thing covered up. (The mockup still draws a line; the component must not.)
 *
 * ── A group is a unit ───────────────────────────────────────────────────────
 * Dragging a group's row moves every member together. Dragging a single member
 * is confined to its own group — the drop simply never opens outside it, so an
 * illegal drop is unreachable rather than rejected after the fact.
 *
 * ── Why every parameter may be a function ───────────────────────────────────
 * The `.spec` calls this from a `@state` initialiser, and the compiler passes a
 * `@state` initialiser's references as SIGNALS. A value captured here would be
 * both wrong (a function is always truthy) and stale forever, which is exactly
 * how `reorderableColumns: false` once shipped doing nothing. Everything is
 * resolved per use.
 */
import { mountGridDrag } from './drag-core/grid-drag.js';
import { dropAllowed, groupDropAllowed, orderWith, orderWithGroup, groupKeys, } from './column-chooser-math.js';
/** Rows a drop can land against. Group rows are targets too — a column may be
 *  dropped above or below a whole group. */
const ROW = '[data-colchooser-key], [data-colchooser-group]';
const GRIP = '[data-colchooser-grip], [data-colchooser-group-grip]';
const SLOT = '[data-colchooser-slot]';
/**
 * What the hit-test may land on: a row, OR THE SLOT ITSELF.
 *
 * The slot has to be hittable, and this is not a nicety — it is what makes the
 * drop work at all. `onPointerUp` RE-RUNS the hit-test at the release point
 * (drag-core/pointer.ts:187) instead of committing the target the placeholder
 * is showing, and the slot is a real in-flow element, so opening it DISPLACES
 * the rows under the cursor by its own height. The pointer therefore ends up
 * over the slot; with the slot invisible to hit-testing that resolved to null
 * and drag-core cancelled the drag it was about to commit — mid-drag the
 * placeholder tracked perfectly and the drop silently did nothing.
 *
 * Landing on the slot means "the gap you are already showing me", which is
 * also exactly what the user means by releasing there.
 */
const HIT = ROW + ', ' + SLOT;
/** A group source is prefixed, so one id space covers both kinds of drag. */
const GROUP_PREFIX = 'g:';
/** How often we look for a panel that the Popover mounts only while open. */
const POLL_MS = 80;
function makeSlot(height) {
    const el = document.createElement('div');
    el.setAttribute('data-colchooser-slot', 'true');
    // `pointer-events` is deliberately left at its default so the slot IS
    // hit-testable — see the note on HIT above. A `none` here reads as the
    // obvious choice for a placeholder and silently breaks every drop.
    el.style.cssText =
        'box-sizing:border-box;border:1px dashed currentColor;border-radius:6px;' +
            'opacity:0.55;margin:1px 4px;height:' + height + 'px;';
    return el;
}
export function wireChooserDrag(chooserId, onReorder, columns, order) {
    let handle = null;
    let listEl = null;
    let waitTimer = null;
    let destroyed = false;
    // Per-drag state. Reset by onDragEnd, which drag-core always fires.
    let movingKeys = [];
    let movingEls = [];
    let srcGroup = null;
    let srcKey = null;
    let slot = null;
    /** The gap the slot is currently showing. -1 = none open. */
    let curAt = -1;
    function resolveId() {
        return typeof chooserId === 'function' ? chooserId() : chooserId;
    }
    function resolveColumns() {
        const c = typeof columns === 'function' ? columns() : columns;
        return Array.isArray(c) ? c : [];
    }
    function resolveOrder() {
        const o = typeof order === 'function' ? order() : order;
        return Array.isArray(o) ? o : [];
    }
    function findList() {
        const id = resolveId();
        return id
            ? document.querySelector('[data-colchooser-list="' + id + '"]')
            : null;
    }
    /** Rows that can be landed on: everything except what is being carried. */
    function targetRows() {
        if (!listEl)
            return [];
        return Array.from(listEl.querySelectorAll(ROW)).filter((el) => movingEls.indexOf(el) === -1);
    }
    /** Undo the drag's DOM writes. Runs on drop, on cancel, and on teardown. */
    function clearDragVisuals() {
        for (const el of movingEls)
            el.style.display = '';
        movingEls = [];
        movingKeys = [];
        srcGroup = null;
        srcKey = null;
        curAt = -1;
        if (slot) {
            slot.remove();
            slot = null;
        }
    }
    function placeSlot(at) {
        if (!slot || !listEl)
            return;
        if (at === null) {
            slot.remove();
            return;
        }
        const rows = targetRows();
        if (rows.length === 0) {
            listEl.appendChild(slot);
            return;
        }
        if (at >= rows.length) {
            const last = rows[rows.length - 1];
            last.parentNode?.insertBefore(slot, last.nextSibling);
            return;
        }
        const target = rows[at];
        target.parentNode?.insertBefore(slot, target);
    }
    function mount(list) {
        listEl = list;
        // The wire's own attach signal.
        //
        // There has to be one, and it cannot be `cursor: grab` the way it is for
        // the grid's header drag: there the WIRE sets the cursor, here the `.spec`
        // sets it statically in markup. A test waiting on the cursor is therefore
        // waiting on something that is true before the wire exists — it passes
        // against a completely unattached wire, which is exactly how two drag
        // tests came to race the 80ms poll and fail only on a slower machine.
        list.setAttribute('data-colchooser-armed', 'true');
        handle = mountGridDrag({
            container: list,
            sources: GRIP,
            cellSelector: HIT,
            mouseMoveStart: 5,
            getSrcId: (el) => {
                const g = el.getAttribute('data-colchooser-group-grip');
                if (g)
                    return GROUP_PREFIX + g;
                return el.getAttribute('data-colchooser-grip');
            },
            // The ghost is the whole row, not the grip that started the drag.
            //
            // ⚠ A FUNCTION ghost gets NONE of drag-core's default styling.
            // `makeGhost` applies DEFAULT_GHOST_CSS only on the 'clone' path; for a
            // caller-supplied element it appends it as-is (shared.ts:194-197). So a
            // custom ghost must position and neutralise ITSELF, exactly as
            // column-ghost.ts does for the column drag.
            //
            // Both halves below were bugs, and they had the same symptom — the drop
            // slot never appeared at all:
            //
            //  · without `pointer-events: none` the ghost is hit-testable, so
            //    `elementsFromPoint` returns it and drag-core's `closest(cellSelector)`
            //    matches the ghost instead of the row underneath;
            //  · and because the clone still carried `data-colchooser-key`, that
            //    match looked like a perfectly valid row — one that is not in
            //    `targetRows()`, so every hit-test resolved to null and no drag could
            //    ever find a target.
            ghost: (srcEl) => {
                const row = srcEl.closest(ROW) ?? srcEl;
                const clone = row.cloneNode(true);
                // A ghost is a picture of a row, not a row. Strip every attribute the
                // hit-test or the wire's own queries key on.
                for (const el of [clone, ...Array.from(clone.querySelectorAll('*'))]) {
                    el.removeAttribute('data-colchooser-key');
                    el.removeAttribute('data-colchooser-group');
                    el.removeAttribute('data-colchooser-grip');
                    el.removeAttribute('data-colchooser-group-grip');
                }
                Object.assign(clone.style, {
                    position: 'fixed',
                    width: row.getBoundingClientRect().width + 'px',
                    pointerEvents: 'none',
                    zIndex: '9999',
                    margin: '0',
                    opacity: '0.95',
                    background: 'var(--spec-surface, #ffffff)',
                    boxShadow: '0 10px 26px rgba(14,22,38,0.18)',
                    borderRadius: '6px',
                });
                return clone;
            },
            onDragStart: (srcId, srcEl) => {
                const isGroup = srcId.startsWith(GROUP_PREFIX);
                srcGroup = isGroup ? srcId.slice(GROUP_PREFIX.length) : null;
                srcKey = isGroup ? null : srcId;
                const row = srcEl.closest(ROW);
                if (srcGroup) {
                    movingKeys = groupKeys(resolveOrder(), resolveColumns(), srcGroup);
                    // The group's own row travels with its members.
                    movingEls = [].concat(row ? [row] : [], movingKeys
                        .map((k) => list.querySelector('[data-colchooser-key="' + k + '"]'))
                        .filter((el) => el !== null));
                }
                else {
                    movingKeys = srcKey ? [srcKey] : [];
                    movingEls = row ? [row] : [];
                }
                // Measure BEFORE hiding: a display:none row has no height.
                const height = movingEls.reduce((sum, el) => sum + el.getBoundingClientRect().height, 0);
                for (const el of movingEls)
                    el.style.display = 'none';
                slot = makeSlot(height);
            },
            /**
             * The row under the pointer → a packed index among the remaining rows.
             * Returns null when the resulting order would be illegal, so no slot
             * opens there and the drop is simply unreachable.
             */
            cellToTarget: (cellEl, _x, y) => {
                // Released (or hovering) over the placeholder: commit the gap it is
                // already showing. Without this the slot's own displacement makes the
                // release point resolve to nothing and the drop is cancelled.
                if (cellEl.hasAttribute('data-colchooser-slot')) {
                    return curAt >= 0 ? { at: curAt } : null;
                }
                const rows = targetRows();
                const idx = rows.indexOf(cellEl);
                if (idx === -1)
                    return null;
                const box = cellEl.getBoundingClientRect();
                const at = y > box.top + box.height / 2 ? idx + 1 : idx;
                const ord = resolveOrder();
                const cols = resolveColumns();
                if (srcGroup) {
                    return groupDropAllowed(ord, cols, srcGroup, at) ? { at } : null;
                }
                if (srcKey) {
                    return dropAllowed(ord, cols, srcKey, at) ? { at } : null;
                }
                return null;
            },
            onTargetChange: (target) => {
                curAt = target ? target.at : -1;
                placeSlot(target ? target.at : null);
            },
            onDrop: (_srcId, target) => {
                const ord = resolveOrder();
                const cols = resolveColumns();
                const group = srcGroup;
                const key = srcKey;
                const at = target ? target.at : null;
                clearDragVisuals();
                if (at === null)
                    return;
                if (group)
                    onReorder(orderWithGroup(ord, cols, group, at));
                else if (key)
                    onReorder(orderWith(ord, key, at));
            },
            onCancel: () => clearDragVisuals(),
            onDragEnd: () => clearDragVisuals(),
        });
    }
    /**
     * The panel is mounted by a Popover only while it is open, so there is
     * nothing to attach to at mount and the container's identity changes every
     * time it reopens. Poll, and re-mount whenever a different list appears.
     */
    function tick() {
        waitTimer = null;
        if (destroyed)
            return;
        const found = findList();
        if (found !== listEl) {
            if (handle) {
                handle.destroy();
                handle = null;
            }
            clearDragVisuals();
            if (listEl)
                listEl.removeAttribute('data-colchooser-armed');
            listEl = null;
            if (found)
                mount(found);
        }
        else if (handle) {
            // The row set changes as columns are hidden, shown and reordered.
            handle.refresh();
        }
        waitTimer = setTimeout(tick, POLL_MS);
    }
    tick();
    return function teardown() {
        destroyed = true;
        if (waitTimer != null) {
            clearTimeout(waitTimer);
            waitTimer = null;
        }
        if (handle) {
            try {
                handle.destroy();
            }
            catch {
                /* noop */
            }
            handle = null;
        }
        clearDragVisuals();
        if (listEl)
            listEl.removeAttribute('data-colchooser-armed');
        listEl = null;
    };
}
// Re-exported so `column-chooser.spec` needs exactly ONE `@extern` line — and
// so the math module reaches the registry as a TRANSITIVE import, which is the
// case P0's graph walker exists for.
export { genChooserId, chooserRows, moveKeyBy, moveGroupBy, groupKeys, } from './column-chooser-math.js';
//# sourceMappingURL=column-chooser-drag.js.map