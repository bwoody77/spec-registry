/**
 * avatar-picker.js — Helper functions for avatar-picker.spec via @extern.
 *
 * pickImageFile() opens a transient <input type="file"> and resolves with a
 * data URL (or empty string if the user cancelled). cropAvatarToDataUrl()
 * takes the source data URL plus zoom/offset parameters and returns a
 * square JPEG data URL ready to POST to the server.
 *
 * The cropper uses center-anchored zoom plus optional offset in [-1, 1]
 * along each axis, where +/-1 means the crop centre is pinned to the
 * far edge of the image (clamped to keep the crop in-bounds).
 */

export function pickImageFile() {
  return new Promise((resolve) => {
    if (typeof document === 'undefined') { resolve(''); return; }
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.style.position = 'fixed';
    input.style.left = '-9999px';
    let resolved = false;
    const cleanup = () => {
      try { document.body.removeChild(input); } catch { /* noop */ }
    };
    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      if (!file) { resolved = true; cleanup(); resolve(''); return; }
      const reader = new FileReader();
      reader.onload = () => { resolved = true; cleanup(); resolve(String(reader.result || '')); };
      reader.onerror = () => { resolved = true; cleanup(); resolve(''); };
      reader.readAsDataURL(file);
    });
    // Fallback for cancelled file picker: focus returns to window without a
    // change event firing. Give the browser a tick, then clean up.
    const onFocus = () => {
      window.removeEventListener('focus', onFocus);
      setTimeout(() => {
        if (!resolved) { cleanup(); resolve(''); }
      }, 300);
    };
    window.addEventListener('focus', onFocus);
    document.body.appendChild(input);
    input.click();
  });
}

export function cropAvatarToDataUrl(srcDataUrl, zoom, offsetX, offsetY, size) {
  return new Promise((resolve, reject) => {
    if (!srcDataUrl) { reject(new Error('no image source')); return; }
    const out = Math.max(16, Math.floor(size || 256));
    const z = Math.max(1, Number(zoom) || 1);
    const ox = clamp(Number(offsetX) || 0, -1, 1);
    const oy = clamp(Number(offsetY) || 0, -1, 1);
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      const w = img.naturalWidth;
      const h = img.naturalHeight;
      const baseSide = Math.min(w, h);
      const cropSide = baseSide / z;
      const halfCrop = cropSide / 2;
      // Offset in pixels: half the slack on each axis after the crop is sized
      const slackX = (w - cropSide) / 2;
      const slackY = (h - cropSide) / 2;
      const cx = clamp(w / 2 + ox * slackX, halfCrop, w - halfCrop);
      const cy = clamp(h / 2 + oy * slackY, halfCrop, h - halfCrop);
      const sx = cx - halfCrop;
      const sy = cy - halfCrop;
      const canvas = document.createElement('canvas');
      canvas.width = out;
      canvas.height = out;
      const ctx = canvas.getContext('2d');
      if (!ctx) { reject(new Error('canvas unavailable')); return; }
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, sx, sy, cropSide, cropSide, 0, 0, out, out);
      try {
        resolve(canvas.toDataURL('image/jpeg', 0.9));
      } catch (err) {
        reject(err);
      }
    };
    img.onerror = () => reject(new Error('failed to load image'));
    img.src = srcDataUrl;
  });
}

function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
