/**
 * avatar-picker-math.ts — the crop geometry, kept pure so the preview and the
 * cropper can be proved to describe the same square.
 *
 * ── THE MODEL ───────────────────────────────────────────────────────────────
 * The circle is `side` CSS px. The image is laid out so its SHORT side is
 * `side * zoom`, with the long side following the natural aspect ratio; it is
 * centred in the circle and clipped by it. The overflow — half of it on each
 * side, per axis — IS the pan range, which is why an image that is not square
 * can be panned at zoom 1: it already overflows.
 *
 * That is deliberately the same reasoning cropAvatarToDataUrl applies to
 * SOURCE pixels (crop side = min(w,h)/zoom, slack = (dimension - cropSide)/2),
 * just expressed in display px. The two are related by a single scale factor,
 * so an offset in [-1, 1] means the same thing to both — see cropWindow and
 * the agreement tests.
 *
 * ── WHAT THIS REPLACES ──────────────────────────────────────────────────────
 * The pan bound used to be `130 * (zoom - 1)`: a constant, blind to the aspect
 * ratio, and exactly ZERO at zoom 1. Combined with an `object-fit: cover`
 * preview — which clips the overflow BEFORE any transform, so translating the
 * element only slid a pre-cropped square over black — panning did nothing a
 * user could see at any zoom level. Reported by Bryan, Vector 2026-08-25:
 * "we give them a way to zoom the image in and out but they can't pan it."
 */
/** Finite and positive, or the fallback. Guards NaN/0/Infinity at the door. */
function positive(v, fallback) {
    return Number.isFinite(v) && v > 0 ? v : fallback;
}
/**
 * Lay the image out inside the circle.
 *
 * `aspect` is naturalWidth / naturalHeight. It is 0 or NaN until an image
 * decodes, and a NaN that reaches a CSS declaration is silently DROPPED by the
 * browser — the failure mode that hid the original zoom corruption — so a
 * nonsense aspect is treated as square rather than propagated.
 */
export function previewFit(aspect, zoom, side) {
    const a = positive(aspect, 1);
    // Below 1 the image would no longer cover the circle and the user would be
    // framing background, so 1 is the floor rather than a clamp on input error.
    const z = Math.max(1, positive(zoom, 1));
    const s = positive(side, 260);
    const shortSide = s * z;
    const width = a >= 1 ? shortSide * a : shortSide;
    const height = a >= 1 ? shortSide : shortSide / a;
    return {
        width,
        height,
        panMaxX: Math.max(0, (width - s) / 2),
        panMaxY: Math.max(0, (height - s) / 2),
    };
}
/**
 * Hold a pan offset inside +/- max. Never returns NaN, and never returns -0:
 * a negative zero stringifies into CSS as `-0px`, and `Object.is(-0, 0)` is
 * false, so it turns equality checks and snapshots into a coin flip for no
 * benefit whatsoever.
 */
export function clampPan(v, max) {
    const m = Number.isFinite(max) && max > 0 ? max : 0;
    if (!Number.isFinite(v))
        return 0;
    const c = v < -m ? -m : v > m ? m : v;
    return c === 0 ? 0 : c;
}
/**
 * Turn a pan offset in CSS px into the [-1, 1] offset cropAvatarToDataUrl
 * takes.
 *
 * SIGN-FLIPPED, and that is not a quirk: dragging the picture to the RIGHT
 * brings its LEFT side into view, so the crop centre moves LEFT.
 */
export function cropOffset(pan, panMax) {
    if (!Number.isFinite(panMax) || panMax <= 0)
        return 0;
    if (!Number.isFinite(pan))
        return 0;
    const o = -pan / panMax;
    const c = o < -1 ? -1 : o > 1 ? 1 : o;
    return c === 0 ? 0 : c; // see clampPan on -0
}
/**
 * The square of SOURCE pixels a given zoom/offset pair selects — the same
 * arithmetic cropAvatarToDataUrl performs, factored out so it can be tested
 * against previewFit without a canvas.
 *
 * cropAvatarToDataUrl calls this; the tests call it too, which is what makes
 * "the preview and the cropper agree" a checkable claim rather than a comment.
 */
export function cropWindow(w, h, zoom, offsetX, offsetY) {
    const z = Math.max(1, positive(zoom, 1));
    const ox = clampPan(offsetX, 1);
    const oy = clampPan(offsetY, 1);
    const side = Math.min(w, h) / z;
    const half = side / 2;
    const slackX = (w - side) / 2;
    const slackY = (h - side) / 2;
    const cx = clampTo(w / 2 + ox * slackX, half, w - half);
    const cy = clampTo(h / 2 + oy * slackY, half, h - half);
    return { sx: cx - half, sy: cy - half, side };
}
function clampTo(v, lo, hi) {
    return v < lo ? lo : v > hi ? hi : v;
}
//# sourceMappingURL=avatar-picker-math.js.map