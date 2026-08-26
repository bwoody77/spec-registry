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
import { cropWindow } from './avatar-picker-math.js';
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
export function cropAvatarToDataUrl(srcDataUrl, zoom, offsetX, offsetY, size) {
    return new Promise((resolve, reject) => {
        if (!srcDataUrl) {
            reject(new Error('no image source'));
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
                reject(new Error('canvas unavailable'));
                return;
            }
            ctx.imageSmoothingQuality = 'high';
            ctx.drawImage(img, sx, sy, side, side, 0, 0, out, out);
            try {
                resolve(canvas.toDataURL('image/jpeg', 0.9));
            }
            catch (err) {
                reject(err);
            }
        };
        img.onerror = () => reject(new Error('failed to load image'));
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
 */
export function imageAspect(src) {
    return new Promise((resolve) => {
        if (!src || typeof Image === 'undefined') {
            resolve(0);
            return;
        }
        const img = new Image();
        img.crossOrigin = 'anonymous';
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
export function downscaleToDataUrl(srcDataUrl, maxDim, quality) {
    return new Promise((resolve) => {
        if (!srcDataUrl || typeof Image === 'undefined') {
            resolve(srcDataUrl);
            return;
        }
        const cap = Math.max(64, Math.floor(maxDim || 1024));
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
            const scale = Math.min(1, cap / Math.max(w, h));
            if (scale >= 1) {
                resolve(srcDataUrl);
                return;
            }
            const canvas = document.createElement('canvas');
            canvas.width = Math.max(1, Math.round(w * scale));
            canvas.height = Math.max(1, Math.round(h * scale));
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                resolve(srcDataUrl);
                return;
            }
            ctx.imageSmoothingQuality = 'high';
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            try {
                const out = canvas.toDataURL('image/jpeg', q);
                // A pathological re-encode that GREW the payload is never worth
                // taking — keep whichever is smaller.
                resolve(out.length < srcDataUrl.length ? out : srcDataUrl);
            }
            catch {
                resolve(srcDataUrl);
            }
        };
        img.onerror = () => resolve(srcDataUrl);
        img.src = srcDataUrl;
    });
}
//# sourceMappingURL=avatar-picker.js.map