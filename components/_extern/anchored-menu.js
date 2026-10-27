/**
 * Keyboard dismissal for an anchored menu: a trigger, a panel shown under it
 * with `anchor:`, and a fixed backdrop that closes it on an outside click.
 * Popover is the shape; consuming apps copy it (Vector's FilterChipMenu, its
 * schedule Views menu and PresetMenu), so the two rules live here once.
 *
 * WHY. The backdrop is the only outside-close, and a backdrop only hears the
 * mouse. A keyboard user who Tabbed past an open menu left it open, its
 * backdrop over the whole page, so their next click did nothing but close it.
 * And Escape closed the menu with focus still on an item that had just been
 * hidden, which drops focus to <body>: a screen-reader user lost their place.
 *
 * Both take the event from a handler on the menu's ROOT block (the element
 * holding trigger, panel and backdrop), and read `currentTarget`
 * synchronously: the browser clears it once dispatch ends.
 *
 * DOM-only on purpose. iOS and Android have no Tab order to leave and no
 * focus to lose; there these are stand-ins that answer null, which the
 * components read as "stay open" and "nothing to focus".
 */
/**
 * Did focus leave the menu? For the root's `on focus-out(event)`.
 *
 * True only when focus moved to a REAL element outside the root. A move
 * between the trigger and an item, or onto the backdrop (tabindex -1, so a
 * click on it focuses it before its click closes the menu), stays inside.
 * No `relatedTarget` is not a departure: a click on a non-focusable part of
 * the panel blurs to <body>, and switching windows blurs too and hands focus
 * back on return. Closing on either would close a menu the user is in.
 */
export function menuFocusLeft(event) {
    if (!event)
        return false;
    const root = event.currentTarget;
    const next = event.relatedTarget;
    if (!root || !next || typeof root.contains !== 'function')
        return false;
    return !root.contains(next);
}
/** What a keyboard can land on. Disabled and tabindex -1 are left out. */
const FOCUSABLE = [
    'button:not([disabled])',
    'a[href]',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
].join(', ');
/**
 * Put focus back on the menu's trigger. For the root's Escape handler.
 *
 * The trigger is the root's FIRST `[data-menu-trigger]`: a menu nested in the
 * panel has its own, but the panel comes after the trigger, so document order
 * finds this menu's. Focus goes to the first focusable thing inside it (the
 * caller's button), else to the marked element itself when it can take focus.
 * Inside first: Popover's trigger wrapper has a click handler, so the compiler
 * makes it a tab stop of its own, and focusing it would land on an unnamed
 * div around the button rather than on the button.
 */
export function menuFocusTrigger(event) {
    if (!event)
        return;
    const root = event.currentTarget;
    if (!root || typeof root.querySelector !== 'function')
        return;
    const trigger = root.querySelector('[data-menu-trigger]');
    if (!trigger)
        return;
    const target = trigger.querySelector(FOCUSABLE) ?? (trigger.matches(FOCUSABLE) ? trigger : null);
    target?.focus({ preventScroll: true });
}
//# sourceMappingURL=anchored-menu.js.map