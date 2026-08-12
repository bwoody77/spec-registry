/**
 * Derived row grouping for DataGridSpec.
 *
 * ── Why this is a pure function and not a second render path ────────────────
 * DataGridSpec already renders `_kind: 'group'` rows: the caret, the collapse,
 * the group background and the toggle are all shipped code. `DataTable`'s
 * model differs only in WHERE the group headers come from — it derives them
 * from a field instead of making the caller inject them.
 *
 * So the derived model needs no rendering at all. It needs a function that
 * produces the shape the grid already draws, and the grid keeps ONE render
 * path. Two paths would eventually disagree; this cannot.
 *
 * ── Contiguity is the model ─────────────────────────────────────────────────
 * A value that reappears after a gap starts a NEW run rather than rejoining
 * the earlier one. Merging them would mean silently reordering the caller's
 * rows — the same rule `gridSegmentsOf` follows for header groups, for the
 * same reason.
 */
/** A group value as a comparable key. Null and missing collapse to ''. */
function keyOf(value) {
    if (value === null || value === undefined)
        return '';
    return String(value);
}
/**
 * The count to show on a group header: the caller's, else the rows present.
 *
 * Both sides are coerced to strings before comparison. Vector's helper
 * compares raw keys, so a NUMERIC-keyed counts map (`{ 2024: 900 }`) missed
 * and fell back to counting the loaded rows — silently, and precisely when it
 * matters most: on a paginated grid the rows present are a fraction of the
 * group, so the fallback is not just different, it is wrong.
 */
export function groupCountFor(counts, rows, value, groupBy) {
    if (!groupBy)
        return 0;
    const k = keyOf(value);
    if (counts && typeof counts === 'object') {
        for (const name of Object.keys(counts)) {
            if (keyOf(name) !== k)
                continue;
            const n = Number(counts[name]);
            if (Number.isFinite(n))
                return n;
        }
    }
    let n = 0;
    for (const row of rows)
        if (keyOf(row[groupBy]) === k)
            n += 1;
    return n;
}
/**
 * `rows` with a group header inserted before each contiguous run of `groupBy`.
 *
 * Returns fresh objects; the caller's rows are never mutated. Each member row
 * is tagged with `_group` so the grid's existing collapse can hide it, and
 * each header carries `_groupValue` (raw, for the toggle event) alongside
 * `_groupLabel` (display, with a dash for an absent value).
 */
export function gridDeriveGroupRows(rows, groupBy, counts) {
    if (!groupBy || !Array.isArray(rows) || rows.length === 0)
        return rows;
    // A caller already using the STRUCTURAL model must not get derived headers
    // interleaved with its own. Refusing beats producing two kinds of group row
    // in one list, which no collapse rule could then describe.
    if (rows.some((r) => r && r._kind !== undefined))
        return rows;
    const out = [];
    let prev = null;
    for (const row of rows) {
        const value = row[groupBy];
        const k = keyOf(value);
        if (prev === null || k !== prev) {
            out.push({
                _kind: 'group',
                _group: k,
                _groupValue: value === undefined ? null : value,
                _groupLabel: k === '' ? '—' : k,
                _groupCount: groupCountFor(counts, rows, value, groupBy),
            });
            prev = k;
        }
        out.push({ ...row, _group: k });
    }
    return out;
}
//# sourceMappingURL=grid-group-derive.js.map