/**
 * Pure utility functions for keyboard navigation.
 * Used via @extern from Select, MultiSelect, DatePicker, DataGrid .spec components.
 */
/** Clamp a value between min and max (inclusive). */
export function clamp(value, min, max) {
    return value < min ? min : value > max ? max : value;
}
/** Circular index navigation: wraps around when delta moves past boundaries. */
export function wrapIndex(index, delta, length) {
    if (length <= 0)
        return 0;
    return ((index + delta) % length + length) % length;
}
/** 2D grid navigation: returns new index after moving in a direction within a grid. */
export function gridNavigate(index, cols, total, direction) {
    if (total <= 0)
        return 0;
    const row = Math.floor(index / cols);
    const col = index % cols;
    switch (direction) {
        case 'left':
            return index > 0 ? index - 1 : index;
        case 'right':
            return index < total - 1 ? index + 1 : index;
        case 'up':
            return row > 0 ? index - cols : index;
        case 'down':
            return index + cols < total ? index + cols : index;
        default:
            return index;
    }
}
//# sourceMappingURL=nav-utils.js.map