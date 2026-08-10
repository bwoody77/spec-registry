/**
 * Pure math behind DataGridSpec's column drag-to-reorder.
 *
 * No DOM, no @spec imports — every decision that can be made from numbers
 * lives here so it can be unit-tested. The component suite runs in happy-dom,
 * which computes no geometry at all, so anything left in the DOM wire is
 * effectively untested. Keep that boundary.
 *
 * Ported from Vector's data-table-header-drag-helpers.js, with the segment
 * splice added: DataGridSpec constrains a drag to its column's segment but
 * emits the FULL key order, so the two have to be reconciled.
 */
/** Unique per grid INSTANCE, so two grids on one page never share a session. */
export function genGridId() {
    return 'grid-' + Math.random().toString(36).slice(2, 9).padEnd(7, '0');
}
/**
 * How far into a column the cursor must travel before that column counts as
 * passed. The threshold follows the drag DIRECTION — entering from the left
 * when dragging right, from the right when dragging left — which gives a 60%
 * dead band in each column's middle and stops the drop slot flickering.
 */
const ENTER_FRAC = 0.2;
/**
 * Cursor X → packed gap index: how many non-source columns sit to its left.
 * `cols` is a drag-start snapshot of ORIGINAL geometry, so the answer stays
 * stable while the live columns shift around the cursor.
 */
export function gapFromX(cols, srcIdx, clientX, dir) {
    const frac = dir > 0 ? ENTER_FRAC : 1 - ENTER_FRAC;
    let g = 0;
    for (let i = 0; i < cols.length; i++) {
        if (i === srcIdx)
            continue;
        const c = cols[i];
        if (c.left + c.width * frac < clientX)
            g++;
    }
    return g;
}
/**
 * Drag `fromKey` out of `keys` and re-insert it at packed gap index `g`.
 * Returns null when nothing actually moved — the caller must not emit a
 * change event for a drop back into the same slot.
 */
export function orderFromGapIndex(keys, fromKey, g) {
    if (!keys.includes(fromKey))
        return null;
    const packed = keys.filter((k) => k !== fromKey);
    const at = Math.max(0, Math.min(g, packed.length));
    const result = [...packed.slice(0, at), fromKey, ...packed.slice(at)];
    for (let i = 0; i < result.length; i++) {
        if (result[i] !== keys[i])
            return result;
    }
    return null;
}
/**
 * Write a segment's new internal order back into the full key list, at the
 * slots that segment already occupies. Columns outside the segment never move
 * — which is what makes a strict-segment drag expressible as a full-order
 * event: the grid emits every key, and only the segment's slots differ.
 */
export function applySegmentOrder(fullKeys, segmentKeys, newSegmentKeys) {
    const inSegment = new Set(segmentKeys);
    let i = 0;
    return fullKeys.map((k) => (inSegment.has(k) ? newSegmentKeys[i++] ?? k : k));
}
//# sourceMappingURL=column-reorder-math.js.map