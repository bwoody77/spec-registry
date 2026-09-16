/**
 * PanZoom's one platform read. Everything else in the component is Spec, so
 * it ports; whether the user asked for less motion is an OS setting only the
 * host can see.
 */
export function pzPrefersReducedMotion() {
    try {
        return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    catch {
        return false;
    }
}
//# sourceMappingURL=pan-zoom.js.map