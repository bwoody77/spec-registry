/**
 * avatar-picker.ts — Helper functions for avatar-picker.spec via @extern.
 *
 * pickImageFile() opens a transient <input type="file"> and resolves with a
 * data URL (or empty string if the user cancelled). cropAvatarToDataUrl()
 * takes the source data URL plus zoom/offset parameters and returns a
 * square JPEG data URL ready to POST to the server.
 *
 * The cropper uses center-anchored zoom plus optional offset in [-1, 1]
 * along each axis, where +/-1 means the crop centre is pinned to the
 * far edge of the image (clamped to keep the crop in-bounds). The geometry
 * itself lives in avatar-picker-math.ts, which the PREVIEW also uses — that
 * shared module is what makes "what you framed is what you saved" a tested
 * claim instead of two implementations that happen to look similar.
 *
 * imageAspect() and downscaleToDataUrl() serve the two 2026-08-25 fixes:
 * the preview needs the natural aspect ratio to size itself (without it the
 * pan range cannot be known), and re-opening the cropper later needs an
 * ORIGINAL to re-crop, which has to be shrunk before it is worth storing.
 */
import { cropWindow, needsReencode, dataUrlBytes } from './avatar-picker-math.js';
export function pickImageFile() {
    return new Promise((resolve) => {
        if (typeof document === 'undefined') {
            resolve('');
            return;
        }
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.style.position = 'fixed';
        input.style.left = '-9999px';
        let resolved = false;
        const cleanup = () => {
            try {
                document.body.removeChild(input);
            }
            catch { /* noop */ }
        };
        input.addEventListener('change', () => {
            const file = input.files && input.files[0];
            if (!file) {
                resolved = true;
                cleanup();
                resolve('');
                return;
            }
            const reader = new FileReader();
            reader.onload = () => {
                resolved = true;
                cleanup();
                resolve(String(reader.result || ''));
            };
            reader.onerror = () => {
                resolved = true;
                cleanup();
                resolve('');
            };
            reader.readAsDataURL(file);
        });
        const onFocus = () => {
            window.removeEventListener('focus', onFocus);
            setTimeout(() => {
                if (!resolved) {
                    cleanup();
                    resolve('');
                }
            }, 300);
        };
        window.addEventListener('focus', onFocus);
        document.body.appendChild(input);
        input.click();
    });
}
/**
 * Crop to a square data URL, or RESOLVE `''` if that is not possible.
 *
 * It resolves rather than rejects on purpose. Spec actions have no try/catch,
 * so a rejection aborts the calling action mid-way — leaving `busy` stuck true
 * and the dialog open with no explanation. Every failure here is one a user can
 * actually hit: an undecodable file, a browser with no canvas, and — in
 * production, where the stored original is served from R2 — a tainted-canvas
 * SecurityError when the bucket sends no `Access-Control-Allow-Origin`.
 */
export function cropAvatarToDataUrl(srcDataUrl, zoom, offsetX, offsetY, size) {
    return new Promise((resolve) => {
        if (!srcDataUrl || typeof Image === 'undefined') {
            resolve('');
            return;
        }
        const out = Math.max(16, Math.floor(size || 256));
        const z = Math.max(1, Number(zoom) || 1);
        // cropWindow clamps these into [-1, 1] itself, so there is exactly one
        // place that decides what an out-of-range offset means.
        const ox = Number(offsetX) || 0;
        const oy = Number(offsetY) || 0;
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            // Shared with the preview — see avatar-picker-math.ts.
            const { sx, sy, side } = cropWindow(img.naturalWidth, img.naturalHeight, z, ox, oy);
            const canvas = document.createElement('canvas');
            canvas.width = out;
            canvas.height = out;
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                resolve('');
                return;
            }
            ctx.imageSmoothingQuality = 'high';
            ctx.drawImage(img, sx, sy, side, side, 0, 0, out, out);
            try {
                resolve(canvas.toDataURL('image/jpeg', 0.9));
            }
            catch {
                // Tainted canvas — a cross-origin source without CORS headers.
                resolve('');
            }
        };
        img.onerror = () => resolve('');
        img.src = srcDataUrl;
    });
}
/**
 * Natural width / height of an image, or 0 if it cannot be read.
 *
 * The preview cannot size itself without this: the pan range IS the amount by
 * which the image overflows the circle, which is a function of the aspect
 * ratio. Resolves rather than rejects on failure so a broken URL degrades to a
 * square preview (no pan) instead of leaving the cropper stuck.
 *
 * Deliberately does NOT set `crossOrigin`. Reading naturalWidth/Height never
 * taints anything, so requiring CORS here would buy nothing and cost the whole
 * preview geometry: in production the stored original comes from R2, and if the
 * bucket sends no `Access-Control-Allow-Origin` an anonymous request simply
 * fails — the aspect would come back 0, the preview would fall back to square,
 * and a landscape photo would be framed wrongly before the user touched it.
 * (cropAvatarToDataUrl still needs CORS, because it reads pixels back out; it
 * reports that failure instead of hiding it.)
 */
export function imageAspect(src) {
    return new Promise((resolve) => {
        if (!src || typeof Image === 'undefined') {
            resolve(0);
            return;
        }
        const img = new Image();
        img.onload = () => {
            const w = img.naturalWidth;
            const h = img.naturalHeight;
            resolve(w > 0 && h > 0 ? w / h : 0);
        };
        img.onerror = () => resolve(0);
        img.src = src;
    });
}
/**
 * Re-encode an image down to `maxDim` on its longest edge.
 *
 * This is what makes keeping the ORIGINAL affordable. Re-cropping only ever
 * feeds a `cropSize` square (256px by default) at up to 3x zoom, i.e. ~768px
 * of source, so anything past ~1024px cannot be seen in the result — while a
 * phone photo is 3-5 MB. Returns the input untouched when it is already small
 * enough, so a modest upload is not needlessly re-encoded (and never grows).
 */
export function downscaleToDataUrl(srcDataUrl, maxDim, quality, maxBytes = 1_200_000) {
    return new Promise((resolve) => {
        if (!srcDataUrl || typeof Image === 'undefined') {
            resolve(srcDataUrl);
            return;
        }
        const cap = Math.max(64, Math.floor(maxDim || 1024));
        const budget = Math.max(50_000, Math.floor(maxBytes || 1_200_000));
        const q = quality > 0 && quality <= 1 ? quality : 0.85;
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            const w = img.naturalWidth;
            const h = img.naturalHeight;
            if (!(w > 0 && h > 0)) {
                resolve(srcDataUrl);
                return;
            }
            if (!needsReencode(dataUrlBytes(srcDataUrl), Math.max(w, h), budget, cap)) {
                resolve(srcDataUrl);
                return;
            }
            const ctx2d = (cw, ch) => {
                const c = document.createElement('canvas');
                c.width = Math.max(1, Math.round(cw));
                c.height = Math.max(1, Math.round(ch));
                const g = c.getContext('2d');
                if (!g)
                    return null;
                g.imageSmoothingQuality = 'high';
                g.drawImage(img, 0, 0, c.width, c.height);
                return [c, g];
            };
            // Step the longest edge down until the DECODED payload fits the budget.
            // A single pass at `cap` is not enough on its own: a detailed photo can
            // still exceed the cap at 1024px, and the server rejects the entire
            // avatar update rather than just the original. 320px is the floor —
            // below that the stored original stops being able to feed a re-crop.
            let edge = Math.min(cap, Math.max(w, h));
            let best = srcDataUrl;
            for (let i = 0; i < 4; i += 1) {
                const scale = edge / Math.max(w, h);
                const made = ctx2d(w * scale, h * scale);
                if (!made)
                    break;
                let out = '';
                try {
                    out = made[0].toDataURL('image/jpeg', q);
                }
                catch {
                    break; // tainted canvas — keep the input
                }
                best = out;
                if (dataUrlBytes(out) <= budget)
                    break;
                if (edge <= 320)
                    break;
                edge = Math.max(320, Math.floor(edge * 0.75));
            }
            // A pathological re-encode that GREW the payload is never worth taking.
            resolve(dataUrlBytes(best) > 0 && dataUrlBytes(best) < dataUrlBytes(srcDataUrl)
                ? best : srcDataUrl);
        };
        img.onerror = () => resolve(srcDataUrl);
        img.src = srcDataUrl;
    });
}
//# sourceMappingURL=avatar-picker.js.map