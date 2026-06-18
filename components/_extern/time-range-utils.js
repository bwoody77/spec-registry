// Pure time/date helpers for TimeRangePicker and DateTimeRangePicker.
// No DOM, no Spec — unit-tested in isolation. Values are 24h "HH:MM";
// dates are "YYYY-MM-DD". `format` ('12'|'24') affects labels only.
function pad2(n) {
    return String(n).padStart(2, '0');
}
function toMinutes(hhmm) {
    if (!hhmm || !hhmm.includes(':'))
        return 0; // guard: empty/malformed → 00:00, never NaN
    const [h, m] = hhmm.split(':').map(Number);
    return h * 60 + m;
}
function fromMinutes(min) {
    return `${pad2(Math.floor(min / 60))}:${pad2(min % 60)}`;
}
function label12(hhmm) {
    const [h, m] = hhmm.split(':').map(Number);
    const period = h >= 12 ? 'PM' : 'AM';
    const display = h === 0 ? 12 : h > 12 ? h - 12 : h;
    return `${display}:${pad2(m)} ${period}`;
}
function labelFor(hhmm, format) {
    return format === '12' ? label12(hhmm) : hhmm;
}
/** All time-of-day options between minHour:00 and maxHour:00 inclusive,
 *  on a stepMinutes grid. */
export function timeOptions(minHour, maxHour, stepMinutes, format) {
    const out = [];
    for (let t = minHour * 60; t <= maxHour * 60; t += stepMinutes) {
        const value = fromMinutes(t);
        out.push({ value, label: labelFor(value, format) });
    }
    return out;
}
/** Start options trimmed so the latest start still leaves room for at least
 *  one valid end (start + gap <= maxHour:00). */
export function timeRangeStartOptions(minHour, maxHour, stepMinutes, gapMinutes, format) {
    const latestStart = maxHour * 60 - gapMinutes;
    return timeOptions(minHour, maxHour, stepMinutes, format).filter(o => toMinutes(o.value) <= latestStart);
}
/** End options that are all >= start + gap. */
export function timeRangeEndOptions(startValue, minHour, maxHour, stepMinutes, gapMinutes, format) {
    const min = toMinutes(startValue) + gapMinutes;
    return timeOptions(minHour, maxHour, stepMinutes, format).filter(o => toMinutes(o.value) >= min);
}
/** Return endValue if still >= start + gap, else the first valid end. */
export function clampEnd(startValue, endValue, gapMinutes) {
    const min = toMinutes(startValue) + gapMinutes;
    if (endValue !== '' && toMinutes(endValue) >= min)
        return endValue;
    return fromMinutes(min);
}
function dateToNum(ymd) {
    if (ymd === '')
        return -Infinity;
    return Number(ymd.replace(/-/g, ''));
}
function addOneDay(ymd) {
    const [y, m, d] = ymd.split('-').map(Number);
    const dt = new Date(Date.UTC(y, m - 1, d + 1));
    return `${dt.getUTCFullYear()}-${pad2(dt.getUTCMonth() + 1)}-${pad2(dt.getUTCDate())}`;
}
/** Clamp end date+time so the end is >= start + gap. End date before start
 *  date snaps to start date. When dates are equal, push end time to
 *  >= start + gap; if that exceeds maxHour:00, roll to the next day at
 *  minHour:00. A missing start date means nothing to clamp against. */
export function clampEndDateTime(startDate, startTime, endDate, endTime, gapMinutes, minHour, maxHour, stepMinutes) {
    if (startDate === '')
        return { endDate, endTime };
    let d = endDate;
    if (dateToNum(d) < dateToNum(startDate))
        d = startDate;
    if (d === startDate) {
        const minEnd = toMinutes(startTime) + gapMinutes;
        if (minEnd > maxHour * 60) {
            return { endDate: addOneDay(startDate), endTime: fromMinutes(minHour * 60) };
        }
        if (endTime === '' || toMinutes(endTime) < minEnd) {
            return { endDate: d, endTime: fromMinutes(minEnd) };
        }
    }
    return { endDate: d, endTime: endTime === '' ? fromMinutes(minHour * 60) : endTime };
}
//# sourceMappingURL=time-range-utils.js.map