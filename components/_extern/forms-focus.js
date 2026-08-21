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
const PULSE_PEAK = '#fde047'; // bright amber peak
const PULSE_MS = 2000; // two flashes over ~2s
/**
 * The first VISIBLE `[data-field=<name>]` wrapper, else the first match, else
 * null.
 *
 * Shared by focusFormField and pulseFormField so the wrapper-selection rule
 * below has exactly one definition. It was inlined in focusFormField when the
 * pulse was added; two copies of a rule whose whole purpose is to dodge a
 * subtle shipped bug is how one of them silently regresses.
 */
function resolveFieldWrapper(fieldName, requireVisible = false) {
    if (typeof document === 'undefined')
        return null;
    if (!fieldName)
        return null;
    // CSS.escape is not universally available in the engines Spec targets, and
    // the field names are author-controlled identifiers — so restrict the input
    // rather than escape it.
    if (!/^[A-Za-z0-9_-]+$/.test(fieldName))
        return null;
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
        return null;
    let wrap = requireVisible ? null : wrappers[0];
    for (const candidate of wrappers) {
        if (!isHidden(candidate)) {
            wrap = candidate;
            break;
        }
    }
    return wrap;
}
// ── Waiting for the field to exist AND be visible ───────────────────────────
//
// Both helpers below are usually called from a click, when the DOM has long
// settled. But the other real caller is an ARRIVAL effect: a page that has just
// revealed a form and wants to point at a field in it. On that path the wrapper
// is in the DOM and still `display:none`, because Spec's `visibility:` hides
// rather than unmounts — so a naive call focuses nothing (focus on a hidden
// control is a silent no-op) and animates a wrapper the user cannot see.
//
// That combination is worse than doing nothing, because it REPORTS success: the
// animation runs, an Element.prototype.animate spy sees it, and the only thing
// missing is the part a person would have noticed. Vector hit exactly this — a
// pulse that fired on every arrival and was never once visible.
//
// So retry briefly rather than acting on a hidden node. The shape is
// deliberately the same as Vector's reconciliation-scroll.js, which treats
// hidden as not-yet-available for the same reason. A caller whose field is
// genuinely absent (filtered out, never rendered) simply gets nothing after
// ~1s, which is what it used to get immediately.
const READY_RETRY_MS = 50;
const READY_MAX_TRIES = 20; // ~1s
function whenFieldReady(fieldName, act) {
    let tries = 0;
    const tick = () => {
        const wrap = resolveFieldWrapper(fieldName, true);
        if (wrap) {
            act(wrap);
            return;
        }
        // Nothing by that name at all, ever: give up immediately rather than
        // holding a timer open for a typo.
        if (resolveFieldWrapper(fieldName, false) === null)
            return;
        if (tries++ < READY_MAX_TRIES) {
            setTimeout(tick, READY_RETRY_MS);
        }
    };
    tick();
}
/** True when the user has asked for reduced motion. */
function prefersReducedMotion() {
    try {
        return (typeof window !== 'undefined' &&
            typeof window.matchMedia === 'function' &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches === true);
    }
    catch {
        return false;
    }
}
export function focusFormField(fieldName) {
    whenFieldReady(fieldName, (wrap) => focusResolvedField(wrap));
}
function focusResolvedField(wrap) {
    const reduce = prefersReducedMotion();
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
/**
 * Double-pulse a field's background to say "this is the one".
 *
 * Companion to focusFormField, which scrolls and focuses. They are separate
 * because they answer different questions: focus says WHERE to type, the pulse
 * says WHICH of several fields brought you here. A caller wanting both calls
 * both — and a caller pulsing several fields focuses only the first.
 *
 * Deliberately NOT the whole of the message. This does nothing under reduced
 * motion and is gone in two seconds regardless, while a form is worked in for
 * minutes. Callers pair it with a persistent state — FormField's
 * `tone: "warning"` — which is what carries the meaning after the animation
 * ends and what says anything at all to a user who asked for no motion.
 *
 * Fades back to the element's OWN resting background rather than to a literal,
 * so it never leaves a field a colour the rest of the form is not.
 *
 * Not idempotent: fires on every call.
 */
export function pulseFormField(fieldName) {
    // Checked BEFORE waiting: under reduced motion there is nothing to wait for.
    if (prefersReducedMotion())
        return;
    whenFieldReady(fieldName, (wrap) => pulseResolvedField(wrap));
}
function pulseResolvedField(wrap) {
    if (typeof wrap.animate !== 'function')
        return;
    let rest = 'transparent';
    try {
        if (typeof getComputedStyle === 'function') {
            const bg = getComputedStyle(wrap).backgroundColor;
            if (bg)
                rest = bg;
        }
    }
    catch {
        /* no style engine: transparent is a safe resting value */
    }
    try {
        wrap.animate([
            { backgroundColor: rest, offset: 0 },
            { backgroundColor: PULSE_PEAK, offset: 0.18 },
            { backgroundColor: rest, offset: 0.45 },
            { backgroundColor: PULSE_PEAK, offset: 0.63 },
            { backgroundColor: rest, offset: 1 },
        ], { duration: PULSE_MS, easing: 'ease-in-out', fill: 'none' });
    }
    catch {
        /* WAAPI refused: the caller's persistent tone still marks the field */
    }
}
//# sourceMappingURL=forms-focus.js.map