/**
 * Shared component protocol types.
 */
/**
 * Create a callable ComponentHandle — the returned function acts as a
 * cleanup shortcut (calls destroy), while also exposing update/destroy.
 */
export function createHandle(update, destroy, getState, setState) {
    const handle = (() => { handle.destroy(); });
    handle.update = update;
    handle.destroy = destroy;
    if (getState)
        handle.getState = getState;
    if (setState)
        handle.setState = setState;
    return handle;
}
//# sourceMappingURL=types.js.map