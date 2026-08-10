/**
 * The visual artifacts of a column drag: the lifted column ghost and the
 * drop-slot placeholder.
 *
 * This module owns CONSTRUCTION only — it builds two detached (well, one
 * body-appended) DOM elements and hands them back. It knows nothing about
 * pointer sessions, geometry snapshots or gap math; `data-grid-column-drag.ts`
 * owns all of that and positions what is built here. Nothing in this file
 * queries the grid's DOM contract either: the caller passes the column's body
 * cells in, so the `[data-grid-*]` selectors stay in one place.
 *
 * ───────────────────────────────────────────────────────────────────────
 * Why the ghost is the FULL column width
 * ───────────────────────────────────────────────────────────────────────
 * The ghost is a faithful clone of the grabbed column — a shaded header strip
 * plus one padded, separated row per body cell — rendered at the column's
 * exact measured width. That width is not cosmetic. The header cell's own
 * content is a flex row (label + sort/filter icon); clone it into anything
 * narrower and the flex row wraps, dropping the icon onto a second line below
 * the label. The drag image then no longer looks like the column the user
 * grabbed. Keep the width exact.
 */
// ─── Tunables ─────────────────────────────────────────────────────────────────
const SLOT_BG = 'rgba(22,132,255,0.07)'; // placeholder fill
const SLOT_BORDER = '2px dashed rgba(22,132,255,0.45)';
// ─── Whole-column ghost ─────────────────────────────────────────────────────────
/**
 * Build the drag image for a grabbed column.
 *
 * @param srcEl     the grabbed header cell — cloned, and its width sets the ghost's
 * @param bodyCells that column's body cells; hidden ones are skipped here
 */
export function buildColumnGhost(srcEl, bodyCells) {
    const W = Math.round(srcEl.getBoundingClientRect().width);
    const container = document.createElement('div');
    container.setAttribute('data-col-ghost', '');
    Object.assign(container.style, {
        position: 'fixed',
        width: W + 'px',
        background: '#ffffff',
        border: '1px solid rgba(22,132,255,0.45)',
        borderRadius: '8px',
        overflow: 'hidden',
        boxShadow: '0 14px 32px rgba(14,22,38,0.20), 0 3px 10px rgba(14,22,38,0.12)',
        opacity: '0.98',
        pointerEvents: 'none',
        zIndex: '9999',
        margin: '0',
        transform: 'none',
    });
    // Header strip — mirror the grid header (shaded, label + icon inline).
    const hStrip = document.createElement('div');
    Object.assign(hStrip.style, {
        background: '#f1f5f9',
        borderBottom: '1px solid #e6ebf2',
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        boxSizing: 'border-box',
        width: '100%',
    });
    const hClone = srcEl.cloneNode(true);
    hClone.style.transform = '';
    hClone.style.opacity = '';
    hClone.style.width = '100%';
    hStrip.appendChild(hClone);
    container.appendChild(hStrip);
    // One row per visible body cell of this column.
    for (const cell of bodyCells.filter((el) => el.offsetParent !== null)) {
        const row = document.createElement('div');
        Object.assign(row.style, {
            borderBottom: '1px solid #eef2f7',
            padding: '8px 12px',
            display: 'flex',
            alignItems: 'center',
            boxSizing: 'border-box',
            width: '100%',
            minHeight: Math.round(cell.getBoundingClientRect().height) + 16 + 'px',
        });
        const c = cell.cloneNode(true);
        c.style.transform = '';
        c.style.opacity = '';
        c.style.width = '100%';
        row.appendChild(c);
        container.appendChild(row);
    }
    return container;
}
// ─── Drop-slot placeholder ───────────────────────────────────────────────────────
/**
 * A fixed, column-width shaded box that marks the empty space ready to accept
 * the column. Glides between gap positions. Appended to document.body and
 * returned hidden (`opacity: 0`) — the wire positions it and reveals it.
 */
export function makeSlot() {
    const el = document.createElement('div');
    el.setAttribute('data-col-drop-slot', '');
    Object.assign(el.style, {
        position: 'fixed',
        background: SLOT_BG,
        border: SLOT_BORDER,
        borderRadius: '6px',
        boxSizing: 'border-box',
        zIndex: '9998',
        pointerEvents: 'none',
        opacity: '0',
        transition: 'opacity 120ms ease, left 150ms cubic-bezier(0.2, 0, 0, 1)',
    });
    document.body.appendChild(el);
    return el;
}
//# sourceMappingURL=column-ghost.js.map