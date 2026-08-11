/**
 * Jump-to-first-error for the form standard.
 *
 * FormErrorSummary sits next to the submit button. On a long form the failing
 * field is often far above the fold, so the summary offers a link that calls
 * this with validation.firstField.
 *
 * Fields opt in by rendering `data-field="<name>"` on their wrapper — FormField
 * does this automatically from its `field` prop. A name is unique per form, not
 * per document, so when several wrappers carry it the first VISIBLE one wins.
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
    // A field NAME is unique within a form, not within a document. The same name
    // can legitimately appear several times on one page — and worse, a modal
    // mounted unconditionally at app level and merely HIDDEN by CSS puts its
    // fields in the DOM of every page, ahead of the page's own content.
    //
    // `querySelector` took the first match in document order regardless, and the
    // control walk below then skipped its (hidden) controls and returned having
    // done nothing: the link looked dead. That shipped — in Vector, an
    // app-level `feedback-modal` hidden by AppModal put a data-field="title"
    // before every page's own, and two correctly wired forms silently lost their
    // jump link to it.
    //
    // So consider every match and take the first VISIBLE one. When none is
    // visible, fall back to the first match, which is exactly what this used to
    // do — a wrapper the caller is about to reveal still gets the scroll, and
    // nothing gets focused, because focusing an invisible control is a silent
    // no-op that only makes the jump LOOK like it worked.
    //
    // Note this needs no special case for a modal built as a `visibility:` block
    // around a component instance: that compiles to a LAZY MOUNT, so its wrapper
    // is genuinely ABSENT rather than hidden, and never matches at all.
    const wrappers = document.querySelectorAll('[data-field="' + fieldName + '"]');
    if (wrappers.length === 0)
        return;
    let wrap = wrappers[0];
    for (const candidate of wrappers) {
        if (!isHidden(candidate)) {
            wrap = candidate;
            break;
        }
    }
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
/**
 * True when the element or any ancestor is display:none / visibility:hidden.
 *
 * This is the definition of "visible" both call sites use — the wrapper choice
 * above and the control walk. It deliberately answers only "is this rendered at
 * all", not "is this in the viewport" or "is this covered": jumping to a field
 * scrolled off-screen is the whole point of the feature.
 *
 * `offsetParent` is NOT usable for it. It needs a layout engine, and under
 * happy-dom it returns undefined for every element, visible or not — so
 * `offsetParent === null` would never fire and the guard would be dead code no
 * test could catch. Walking ancestors with getComputedStyle works in both a
 * real browser and happy-dom (verified against this repo's happy-dom 20.7.0).
 *
 * When there is no style engine at all this reports everything visible, so the
 * wrapper choice collapses to "first match" — the behaviour that predates it.
 */
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