/**
 * Pure rules behind ColumnChooser.
 *
 * No DOM, no @spec imports. The component suite runs in happy-dom, which
 * computes no geometry, so anything left in a DOM wire is effectively
 * untested — and a `.spec` cannot be unit-tested at all. Every decision the
 * panel makes therefore lives here.
 *
 * ── A group is a UNIT ───────────────────────────────────────────────────────
 * The first design enforced group contiguity by REFUSING moves, which left the
 * group itself immovable: columns could be shuffled around Quality but Quality
 * could never move. Driving the mockup made that obvious within a minute.
 *
 * So a group is one thing in the list — it drags, steps and hides as a block,
 * and its members reorder within it. Contiguity is then an INVARIANT of the
 * model rather than a wall the user keeps hitting, and the only refusal left is
 * taking a single member out of its group.
 */
/** Unique per chooser INSTANCE, so two on one page never share a drag session. */
export function genChooserId() {
    return 'colch-' + Math.random().toString(36).slice(2, 9).padEnd(7, '0');
}
function groupOf(columns, key) {
    const col = columns.find((c) => c.key === key);
    return col && col.group ? col.group : '';
}
/** Every non-empty group occupies one contiguous run of `order`. */
export function groupsIntact(order, columns) {
    const firstAt = new Map();
    for (let i = 0; i < order.length; i++) {
        const g = groupOf(columns, order[i]);
        if (g === '')
            continue;
        const start = firstAt.get(g);
        if (start === undefined) {
            firstAt.set(g, i);
            continue;
        }
        for (let j = start; j < i; j++) {
            if (groupOf(columns, order[j]) !== g)
                return false;
        }
    }
    return true;
}
/**
 * The order reconciled against the columns: unknown keys dropped, columns the
 * order does not mention appended in declared order, repeats removed.
 *
 * This is the SAME contract DataGridSpec's `gridApplyColumnOrder` applies, and
 * the two must agree. They did not: the panel rendered by walking `order`, so
 * a column a partial saved order failed to mention was not listed AT ALL —
 * while the grid still rendered it, because the grid appends what the order
 * omits. The column became unhideable and unmovable with no way back.
 *
 * A partial order is not an edge case. The grid is fed only the VISIBLE
 * columns, so a header drag emits only those keys, and that narrower list is
 * exactly what a consumer persists and feeds back.
 */
export function reconcileOrder(columns, order) {
    const seen = new Set();
    const out = [];
    for (const k of order) {
        if (seen.has(k))
            continue;
        if (!columns.some((c) => c.key === k))
            continue;
        seen.add(k);
        out.push(k);
    }
    for (const c of columns) {
        if (seen.has(c.key))
            continue;
        seen.add(c.key);
        out.push(c.key);
    }
    return out;
}
/**
 * Every column pinned by `movable: false` still sits where it did.
 *
 * `movable: false` stopping only the LOCKED column from moving is not enough:
 * DataGridSpec's `pinFirst` pins by POSITION, so a neighbour moved above the
 * locked first column freezes the neighbour and silently un-pins the locked
 * one — while the panel goes on drawing it with a lock and a `pinned` tag.
 * A locked column holds its INDEX against everything, not just itself.
 */
function lockedHeld(order, next, columns) {
    for (const c of columns) {
        if (c.movable !== false)
            continue;
        if (order.indexOf(c.key) !== next.indexOf(c.key))
            return false;
    }
    return true;
}
/** `key` lifted out of `order` and re-inserted at packed index `at`. */
export function orderWith(order, key, at) {
    const packed = order.filter((k) => k !== key);
    const idx = Math.max(0, Math.min(at, packed.length));
    return packed.slice(0, idx).concat([key], packed.slice(idx));
}
function changed(a, b) {
    if (a.length !== b.length)
        return true;
    for (let i = 0; i < a.length; i++)
        if (a[i] !== b[i])
            return true;
    return false;
}
/**
 * May `key` be dropped at packed gap `at`? A no-op drop back into the same slot
 * is refused too — the caller must not emit a change event for it.
 */
export function dropAllowed(order, columns, key, at) {
    if (!order.includes(key))
        return false;
    const col = columns.find((c) => c.key === key);
    if (col && col.movable === false)
        return false;
    const next = orderWith(order, key, at);
    return changed(order, next) && groupsIntact(next, columns) && lockedHeld(order, next, columns);
}
/**
 * Move `key` one step in `dir`, sliding on to the next index that keeps every
 * run intact. An ungrouped column therefore steps over a whole group in one
 * press; a member at its group's edge has no legal target and this returns
 * null, so the caller renders its button disabled.
 */
export function moveKeyBy(order, columns, key, dir) {
    const from = order.indexOf(key);
    if (from === -1)
        return null;
    const packedLen = order.length - 1;
    for (let at = from + dir; at >= 0 && at <= packedLen; at += dir) {
        if (dropAllowed(order, columns, key, at))
            return orderWith(order, key, at);
    }
    return null;
}
/**
 * The members of `group`, in current order.
 *
 * The empty group is NOT a group: ungrouped columns share the label `''` and
 * moving "all of them" is never what anyone means.
 */
export function groupKeys(order, columns, group) {
    if (group === '')
        return [];
    return order.filter((k) => groupOf(columns, k) === group);
}
/** The whole run of `group` lifted out and re-inserted at packed index `at`. */
export function orderWithGroup(order, columns, group, at) {
    const members = groupKeys(order, columns, group);
    const packed = order.filter((k) => !members.includes(k));
    const idx = Math.max(0, Math.min(at, packed.length));
    return packed.slice(0, idx).concat(members, packed.slice(idx));
}
export function groupDropAllowed(order, columns, group, at) {
    if (groupKeys(order, columns, group).length === 0)
        return false;
    const next = orderWithGroup(order, columns, group, at);
    return changed(order, next) && groupsIntact(next, columns) && lockedHeld(order, next, columns);
}
/** The up/down control for a whole group. moveKeyBy's rule, one level up. */
export function moveGroupBy(order, columns, group, dir) {
    const members = groupKeys(order, columns, group);
    if (members.length === 0)
        return null;
    const packedLen = order.length - members.length;
    const from = order.indexOf(members[0]);
    for (let at = from + dir; at >= 0 && at <= packedLen; at += dir) {
        if (groupDropAllowed(order, columns, group, at)) {
            return orderWithGroup(order, columns, group, at);
        }
    }
    return null;
}
/**
 * The rows the panel renders, with every decision already made.
 *
 * This exists so the `.spec` is markup. The panel's hard parts are DECISIONS —
 * is this control enabled, is this row the first of its run, does it survive
 * the search, may this eye be clicked — and computed in the `.spec` they would
 * be untestable and would push the file past 300 lines.
 *
 * Run edges are computed over the MATCHING rows, not the whole list. Taken
 * from the unfiltered neighbours, a search that excluded a group's first
 * member took the group's row down with it and left the survivors indented
 * under nothing. Found by driving the mockup on 2026-08-11.
 */
export function chooserRows(columns, order, hidden, query) {
    const q = (query || '').trim().toLowerCase();
    const labelOf = (k) => {
        const c = columns.find((x) => x.key === k);
        if (!c)
            return k;
        return c.label || c.header || k;
    };
    const isHidden = (k) => hidden.includes(k);
    // Reconciled, not raw: an unknown key is dropped and a column the order does
    // not mention is appended, exactly as the grid does. Walking `order` alone
    // made a partial saved order hide columns from the panel entirely.
    const full = reconcileOrder(columns, order);
    const shownCount = full.filter((k) => !isHidden(k)).length;
    const visible = full.filter((k) => q === '' || labelOf(k).toLowerCase().includes(q));
    const rows = [];
    visible.forEach((k, i) => {
        const col = columns.find((c) => c.key === k);
        const g = col.group || '';
        const prevG = i > 0 ? groupOf(columns, visible[i - 1]) : '';
        const nextG = i < visible.length - 1 ? groupOf(columns, visible[i + 1]) : '';
        const first = g !== '' && g !== prevG;
        const last = g !== '' && g !== nextG;
        if (first) {
            const members = groupKeys(full, columns, g);
            rows.push({
                kind: 'group',
                id: 'group:' + g,
                key: g,
                label: g,
                group: g,
                count: members.length,
                // A group reads as hidden only when nothing of it is left on screen;
                // the eye then SHOWS the whole run rather than re-hiding part of it.
                hidden: members.every(isHidden),
                locked: false,
                indent: false,
                groupFirst: false,
                groupLast: false,
                canUp: moveGroupBy(full, columns, g, -1) !== null,
                canDown: moveGroupBy(full, columns, g, 1) !== null,
                canHide: true,
            });
        }
        const locked = col.movable === false && col.hideable === false;
        rows.push({
            kind: 'col',
            id: 'col:' + k,
            key: k,
            label: labelOf(k),
            group: g,
            count: 0,
            hidden: isHidden(k),
            locked,
            indent: g !== '',
            groupFirst: first,
            groupLast: last,
            canUp: !locked && col.movable !== false && moveKeyBy(full, columns, k, -1) !== null,
            canDown: !locked && col.movable !== false && moveKeyBy(full, columns, k, 1) !== null,
            // The last visible column cannot be hidden: a grid with no columns has no
            // header and no way back. Showing a hidden one is always allowed.
            canHide: col.hideable !== false && (isHidden(k) || shownCount > 1),
        });
    });
    return rows;
}
//# sourceMappingURL=column-chooser-math.js.map