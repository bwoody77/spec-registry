/**
 * Pure utility functions for the DatePicker component.
 * Used via @extern from date-picker.spec.
 */
/**
 * Build a 6×7 calendar grid for the given year/month.
 * Returns 42 CalendarDay objects (6 rows × 7 columns).
 */
export function calendarGrid(year, month) {
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    const firstDay = new Date(year, month, 1);
    const startDow = firstDay.getDay(); // 0=Sun
    const daysInCurrent = daysInMonth(year, month);
    // Previous month days
    const prevMonth = month === 0 ? 11 : month - 1;
    const prevYear = month === 0 ? year - 1 : year;
    const daysInPrev = daysInMonth(prevYear, prevMonth);
    const result = [];
    // Fill leading days from previous month
    for (let i = startDow - 1; i >= 0; i--) {
        const d = daysInPrev - i;
        result.push({
            day: d,
            dateStr: formatDateStr(prevYear, prevMonth, d),
            isCurrentMonth: false,
            isToday: false,
            blank: false,
        });
    }
    // Current month days
    for (let d = 1; d <= daysInCurrent; d++) {
        const ds = formatDateStr(year, month, d);
        result.push({
            day: d,
            dateStr: ds,
            isCurrentMonth: true,
            isToday: ds === todayStr,
            blank: false,
        });
    }
    // Fill trailing days from next month
    const nextMonth = month === 11 ? 0 : month + 1;
    const nextYear = month === 11 ? year + 1 : year;
    let d = 1;
    while (result.length < 42) {
        result.push({
            day: d,
            dateStr: formatDateStr(nextYear, nextMonth, d),
            isCurrentMonth: false,
            isToday: false,
            blank: false,
        });
        d++;
    }
    return result;
}
/** Format a date string for display. */
export function formatDate(dateStr, locale) {
    if (!dateStr)
        return '';
    const parts = parseDateParts(dateStr);
    if (!parts)
        return dateStr;
    const d = new Date(parts.year, parts.month, parts.day);
    try {
        return d.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' });
    }
    catch {
        return dateStr;
    }
}
/** Check if two date strings represent the same date. */
export function isSameDate(a, b) {
    return a === b;
}
/** Add days/months/years to a date string. */
export function dateAdd(dateStr, unit, amount) {
    const parts = parseDateParts(dateStr);
    if (!parts)
        return dateStr;
    const d = new Date(parts.year, parts.month, parts.day);
    if (unit === 'day')
        d.setDate(d.getDate() + amount);
    else if (unit === 'month')
        d.setMonth(d.getMonth() + amount);
    else if (unit === 'year')
        d.setFullYear(d.getFullYear() + amount);
    return formatDateStr(d.getFullYear(), d.getMonth(), d.getDate());
}
/** Get number of days in a month. */
export function daysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
}
/** Parse "YYYY-MM-DD" into parts. */
export function parseDateParts(dateStr) {
    if (!dateStr)
        return null;
    const m = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m)
        return null;
    return { year: parseInt(m[1], 10), month: parseInt(m[2], 10) - 1, day: parseInt(m[3], 10) };
}
/** Get today as "YYYY-MM-DD". */
export function todayStr() {
    const d = new Date();
    return formatDateStr(d.getFullYear(), d.getMonth(), d.getDate());
}
/** Get month name for display. */
export function monthName(year, month, locale) {
    const d = new Date(year, month, 1);
    try {
        return d.toLocaleDateString(locale, { year: 'numeric', month: 'long' });
    }
    catch {
        return `${year}-${String(month + 1).padStart(2, '0')}`;
    }
}
/** Check if a date string is within min/max bounds. */
export function isDateInRange(dateStr, min, max) {
    if (!dateStr)
        return false;
    if (min && dateStr < min)
        return false;
    if (max && dateStr > max)
        return false;
    return true;
}
/** Weekday header labels. */
export function weekdayHeaders(locale) {
    // Sun-Sat short names
    const headers = [];
    for (let i = 0; i < 7; i++) {
        const d = new Date(2024, 0, i); // Jan 2024 starts on Monday, but we need Sun=0
        // Jan 7, 2024 is a Sunday
        const d2 = new Date(2024, 0, 7 + i);
        try {
            headers.push(d2.toLocaleDateString(locale, { weekday: 'short' }).slice(0, 2));
        }
        catch {
            headers.push(['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'][i]);
        }
    }
    return headers;
}
/** Get today's date as {year, month, day} (month is 0-indexed). */
export function todayParts() {
    const d = new Date();
    return { year: d.getFullYear(), month: d.getMonth(), day: d.getDate() };
}
/**
 * Format a date into a given format string (e.g. "MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY").
 * Month is 0-indexed (0=January).
 */
export function formatDateOutput(year, month, day, format) {
    const yyyy = String(year).padStart(4, '0');
    const mm = String(month + 1).padStart(2, '0');
    const dd = String(day).padStart(2, '0');
    return format.replace(/YYYY/g, yyyy).replace(/MM/g, mm).replace(/DD/g, dd);
}
/**
 * Parse a date string according to a format string.
 * Returns { year, month (0-indexed), day } or null if parsing fails.
 */
export function parseDateInput(str, format) {
    if (!str || !format)
        return null;
    const yIdx = format.indexOf('YYYY');
    const mIdx = format.indexOf('MM');
    const dIdx = format.indexOf('DD');
    if (yIdx < 0 || mIdx < 0 || dIdx < 0)
        return null;
    const yStr = str.substring(yIdx, yIdx + 4);
    const mStr = str.substring(mIdx, mIdx + 2);
    const dStr = str.substring(dIdx, dIdx + 2);
    const y = parseInt(yStr, 10);
    const m = parseInt(mStr, 10);
    const d = parseInt(dStr, 10);
    if (isNaN(y) || isNaN(m) || isNaN(d))
        return null;
    if (m < 1 || m > 12 || d < 1 || d > 31)
        return null;
    return { year: y, month: m - 1, day: d };
}
/**
 * Get the segment order for a format string.
 * Returns an array of 3 segment types: 'month', 'day', 'year'.
 */
export function formatSegments(format) {
    const positions = [
        { type: 'year', idx: format.indexOf('YYYY') },
        { type: 'month', idx: format.indexOf('MM') },
        { type: 'day', idx: format.indexOf('DD') },
    ];
    positions.sort((a, b) => a.idx - b.idx);
    return positions.map(p => p.type);
}
/**
 * Get the separator character from a format string.
 */
export function formatSeparator(format) {
    const m = format.match(/[^A-Z]/);
    return m ? m[0] : '/';
}
/**
 * Convert a date string from any format to ISO "YYYY-MM-DD".
 */
export function toISODate(str, format) {
    const parts = parseDateInput(str, format);
    if (!parts)
        return '';
    return `${parts.year}-${String(parts.month + 1).padStart(2, '0')}-${String(parts.day).padStart(2, '0')}`;
}
// Internal helper
function formatDateStr(year, month, day) {
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}
//# sourceMappingURL=date-utils.js.map