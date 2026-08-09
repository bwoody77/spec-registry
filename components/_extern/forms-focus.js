/**
 * Jump-to-first-error for the form standard.
 *
 * FormErrorSummary sits next to the submit button. On a long form the failing
 * field is often far above the fold, so the summary offers a link that calls
 * this with validation.firstField.
 *
 * Fields opt in by rendering `data-field="<name>"` on their wrapper — FormField
 * does this automatically from its `field` prop.
 *
 * Not idempotent: fires on every click. Reduced-motion aware. Best-effort on
 * older engines.
 */
export function focusFormField(fieldName) {
    if (typeof document === 'undefined')
        return;
    if (!fieldName)
        return;
    // CSS.escape is not universally available in the engines Spec targets, and
    // the field names are author-controlled identifiers — so restrict the input
    // rather than escape it.
    if (!/^[A-Za-z0-9_-]+$/.test(fieldName))
        return;
    const wrap = document.querySelector('[data-field="' + fieldName + '"]');
    if (!wrap)
        return;
    const reduce = typeof window !== 'undefined' &&
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    try {
        wrap.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    }
    catch {
        /* older engines: best-effort, no-op */
    }
    // Move focus to the control itself, so keyboard and screen-reader users land
    // ON the thing that needs fixing rather than merely near it.
    //
    // Hidden controls are skipped defensively: focusing something invisible is a
    // silent no-op that makes the jump look broken, whatever put it there. (An
    // earlier draft claimed this was load-bearing because FormField's built-in
    // TextInput persisted as display:none when a control was slotted — that is
    // FALSE. A `visibility:` block containing a component instance compiles to a
    // lazy mount, ast-to-ir.ts:3738 → ir-to-js.ts:2352-2387, so the input is
    // never mounted. The guard is still correct; it is just not why.)
    //
    // `offsetParent` is NOT usable for this: it needs a layout engine, and in
    // happy-dom it returns undefined for every element, visible or not — so
    // `offsetParent === null` never fires and the guard would be dead code that
    // no test could catch. Walking ancestors with getComputedStyle works in both
    // a real browser and happy-dom (verified against this repo's happy-dom 20.7.0).
    const candidates = wrap.querySelectorAll('input, textarea, select, [tabindex]');
    for (const control of candidates) {
        if (isHidden(control))
            continue;
        try {
            control.focus({ preventScroll: true });
        }
        catch {
            try {
                control.focus();
            }
            catch {
                /* no-op */
            }
        }
        return;
    }
}
/** True when the element or any ancestor is display:none / visibility:hidden. */
function isHidden(el) {
    if (typeof getComputedStyle !== 'function')
        return false; // no style engine: assume visible
    let node = el;
    while (node) {
        const style = getComputedStyle(node);
        if (style.display === 'none' || style.visibility === 'hidden')
            return true;
        node = node.parentElement;
    }
    return false;
}
//# sourceMappingURL=forms-focus.js.map