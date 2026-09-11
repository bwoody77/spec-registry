/**
 * date-range-utils — pure date math for the DateRangePicker component.
 *
 * ISO 'YYYY-MM-DD' strings in and out, integer epoch-day math in UTC so no
 * timezone can move a date. `month` is 0-based (0 = January), the same
 * convention date-utils.ts and DatePicker's viewMonth use. Weeks start on
 * Sunday, as DatePicker's grid does.
 *
 * Three rules carry the weight, and each has a test:
 *
 *   • A range includes BOTH ends. A 14-day period that starts Sep 13 ends
 *     Sep 26 — start + 13. Start + 14 is day one of the next period.
 *   • Picking is click-click on one calendar: the first click is the start,
 *     the second (on or after it) the end; a click BEFORE the start restarts
 *     there; the same day twice is a one-day range.
 *   • A suggested end (from `periodDays`, or the band the start falls in) is
 *     TENTATIVE: shown, but confirmed only by a second click or Apply.
 */
const DAY_MS = 86400000;
const MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
const WEEKDAYS_LONG = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
/** Epoch day for a REAL calendar date, or null ('2026-02-30' → null). */
export function rangeToDay(iso) {
    if (typeof iso !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(iso))
        return null;
    const y = Number(iso.slice(0, 4));
    const m = Number(iso.slice(5, 7));
    const d = Number(iso.slice(8, 10));
    const t = Date.UTC(y, m - 1, d);
    const back = new Date(t);
    if (back.getUTCFullYear() !== y || back.getUTCMonth() !== m - 1 || back.getUTCDate() !== d)
        return null;
    return Math.round(t / DAY_MS);
}
export function rangeFromDay(z) {
    return new Date(z * DAY_MS).toISOString().slice(0, 10);
}
function dow(z) {
    return new Date(z * DAY_MS).getUTCDay();
}
function daysIn(year, month) {
    return new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
}
export function rangeAddDays(iso, n) {
    const z = rangeToDay(iso);
    return z === null ? '' : rangeFromDay(z + n);
}
/** Days in a range, BOTH ends counted; 0 when either end is missing or it runs backwards. */
export function rangeDays(start, end) {
    const a = rangeToDay(start);
    const b = rangeToDay(end);
    if (a === null || b === null || b < a)
        return 0;
    return b - a + 1;
}
/** 'Aug 30 – Sep 12, 2026' · 'Sep 13 – 26, 2026' · 'Dec 27, 2026 – Jan 9, 2027' · 'Sep 13, 2026'. */
export function rangeLabel(start, end) {
    const a = rangeToDay(start);
    const b = rangeToDay(end);
    if (a === null || b === null)
        return '';
    const da = new Date(a * DAY_MS);
    const db = new Date(b * DAY_MS);
    const ma = MONTHS_SHORT[da.getUTCMonth()];
    const mb = MONTHS_SHORT[db.getUTCMonth()];
    const ya = da.getUTCFullYear();
    const yb = db.getUTCFullYear();
    if (a === b)
        return `${ma} ${da.getUTCDate()}, ${ya}`;
    if (ya !== yb)
        return `${ma} ${da.getUTCDate()}, ${ya} – ${mb} ${db.getUTCDate()}, ${yb}`;
    if (da.getUTCMonth() === db.getUTCMonth())
        return `${ma} ${da.getUTCDate()} – ${db.getUTCDate()}, ${ya}`;
    return `${ma} ${da.getUTCDate()} – ${mb} ${db.getUTCDate()}, ${yb}`;
}
/** 'Sunday, September 13, 2026'. */
export function rangeLongDate(iso) {
    const z = rangeToDay(iso);
    if (z === null)
        return '';
    const d = new Date(z * DAY_MS);
    return `${WEEKDAYS_LONG[d.getUTCDay()]}, ${MONTHS_LONG[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}
export function rangeMonthTitle(year, month) {
    const v = rangeShiftView(year, month, 0);
    return `${MONTHS_LONG[v.month]} ${v.year}`;
}
function bandIndexOf(z, bands) {
    if (!Array.isArray(bands))
        return -1;
    for (let i = 0; i < bands.length; i++) {
        const s = rangeToDay(bands[i]?.start);
        const e = rangeToDay(bands[i]?.end);
        if (s !== null && e !== null && s <= z && z <= e)
            return i;
    }
    return -1;
}
/**
 * The end to fill in once a start is picked: a whole `periodDays` after it
 * (start + periodDays − 1, since both ends count), else the end of the band the
 * start falls in, else '' — no suggestion.
 */
export function rangeSuggestEnd(start, periodDays, bands) {
    const z = rangeToDay(start);
    if (z === null)
        return '';
    if (Number.isFinite(periodDays) && periodDays > 0)
        return rangeFromDay(z + Math.floor(periodDays) - 1);
    const i = bandIndexOf(z, bands);
    if (i < 0)
        return '';
    return bands[i].end;
}
/** One click on `day`. Returns the next selection state. */
export function rangePick(start, end, picking, day, periodDays, bands) {
    const zd = rangeToDay(day);
    if (zd === null)
        return { start, end, picking, suggested: false };
    const zs = rangeToDay(start);
    if (picking && zs !== null && zd >= zs) {
        return { start, end: day, picking: false, suggested: false };
    }
    const suggestedEnd = rangeSuggestEnd(day, periodDays, bands);
    return { start: day, end: suggestedEnd, picking: true, suggested: suggestedEnd !== '' };
}
/**
 * The cells of one month, Sunday-first, padded with blanks to whole weeks.
 *
 * While `picking` with a `hover` on or after the start, the hover previews the
 * end; otherwise the start..end on record is drawn, tentative when `suggested`.
 */
export function rangeMonthCells(year, month, start, end, hover, picking, suggested, bands, today) {
    const v = rangeShiftView(year, month, 0);
    const first = Math.round(Date.UTC(v.year, v.month, 1) / DAY_MS);
    const count = daysIn(v.year, v.month);
    const zs = rangeToDay(start);
    const ze = rangeToDay(end);
    const zh = rangeToDay(hover);
    const zt = rangeToDay(today);
    let lo = null;
    let hi = null;
    let tentative = false;
    if (picking && zs !== null && zh !== null && zh >= zs) {
        lo = zs;
        hi = zh;
        tentative = true;
    }
    else if (zs !== null && ze !== null && ze >= zs) {
        lo = zs;
        hi = ze;
        tentative = suggested;
    }
    else if (zs !== null) {
        lo = zs;
        hi = zs;
    }
    const blank = () => ({
        iso: '', day: 0, blank: true, inRange: false, isStart: false, isEnd: false,
        tentative: false, today: false, bandParity: -1, bandStart: false, bandEnd: false, label: '',
    });
    const cells = [];
    for (let i = 0; i < dow(first); i++)
        cells.push(blank());
    for (let d = 1; d <= count; d++) {
        const z = first + d - 1;
        const iso = rangeFromDay(z);
        const inRange = lo !== null && hi !== null && z >= lo && z <= hi;
        const isStart = lo !== null && z === lo;
        const isEnd = hi !== null && z === hi && inRange;
        const bi = bandIndexOf(z, bands);
        const band = bi >= 0 ? bands[bi] : null;
        let label = rangeLongDate(iso);
        if (z === zt)
            label += ', today';
        // A start still waiting for its end is drawn as a one-day span, but it is
        // not a one-day RANGE yet — announce it as the start.
        const awaitingEnd = picking && ze === null;
        if (isStart && isEnd && !awaitingEnd)
            label += ', selected';
        else if (isStart)
            label += ', start';
        else if (isEnd)
            label += tentative ? ', suggested end' : ', end';
        else if (inRange)
            label += ', in range';
        cells.push({
            iso, day: d, blank: false, inRange, isStart, isEnd,
            tentative: inRange && tentative,
            today: z === zt,
            bandParity: bi < 0 ? -1 : bi % 2,
            bandStart: band !== null && band.start === iso,
            bandEnd: band !== null && band.end === iso,
            label,
        });
    }
    while (cells.length % 7 !== 0)
        cells.push(blank());
    return cells;
}
/** Normalized {year, month} after moving `n` months. */
export function rangeShiftView(year, month, n) {
    const total = year * 12 + month + n;
    const y = Math.floor(total / 12);
    return { year: y, month: total - y * 12 };
}
/**
 * Which month opens on the LEFT. A range's start month — unless the whole
 * range (or, with none, today) sits in one month, in which case that month goes
 * on the RIGHT: reports look back, so the month before is the useful neighbour.
 */
export function rangeViewFor(start, end, today) {
    const zs = rangeToDay(start);
    const ze = rangeToDay(end);
    const anchor = zs ?? rangeToDay(today) ?? 0;
    const a = new Date(anchor * DAY_MS);
    const b = new Date((ze ?? anchor) * DAY_MS);
    const sameMonth = a.getUTCFullYear() === b.getUTCFullYear() && a.getUTCMonth() === b.getUTCMonth();
    return rangeShiftView(a.getUTCFullYear(), a.getUTCMonth(), sameMonth ? -1 : 0);
}
/** Is `iso` in one of the `months` months shown from {year, month}? */
export function rangeInView(iso, year, month, months) {
    const z = rangeToDay(iso);
    if (z === null)
        return false;
    const v = rangeShiftView(year, month, 0);
    const lo = Math.round(Date.UTC(v.year, v.month, 1) / DAY_MS);
    const end = rangeShiftView(v.year, v.month, Math.max(1, months));
    const hi = Math.round(Date.UTC(end.year, end.month, 1) / DAY_MS) - 1;
    return z >= lo && z <= hi;
}
/**
 * Keyboard focus movement in the grid, per the APG date-picker grid: arrows
 * by day / week, Home / End to the week's ends, PageUp / PageDown by month with
 * the day clamped to the target month. Any other key returns the date unchanged.
 */
export function rangeMoveFocus(iso, key) {
    const z = rangeToDay(iso);
    if (z === null)
        return iso;
    switch (key) {
        case 'ArrowLeft': return rangeFromDay(z - 1);
        case 'ArrowRight': return rangeFromDay(z + 1);
        case 'ArrowUp': return rangeFromDay(z - 7);
        case 'ArrowDown': return rangeFromDay(z + 7);
        case 'Home': return rangeFromDay(z - dow(z));
        case 'End': return rangeFromDay(z + (6 - dow(z)));
        case 'PageUp':
        case 'PageDown': {
            const d = new Date(z * DAY_MS);
            const v = rangeShiftView(d.getUTCFullYear(), d.getUTCMonth(), key === 'PageUp' ? -1 : 1);
            const day = Math.min(d.getUTCDate(), daysIn(v.year, v.month));
            return rangeFromDay(Math.round(Date.UTC(v.year, v.month, day) / DAY_MS));
        }
        default: return iso;
    }
}
/** What a screen reader hears after each step — and what the footer says. */
export function rangePrompt(start, end, picking, suggested) {
    if (rangeToDay(start) === null)
        return 'Pick a start date.';
    if (picking && suggested && rangeToDay(end) !== null) {
        return `Start ${rangeLongDate(start)}. End suggested: ${rangeLongDate(end)}. Pick another day to change it, or Apply.`;
    }
    if (picking)
        return `Start ${rangeLongDate(start)}. Now pick the end date.`;
    const n = rangeDays(start, end);
    if (n === 0)
        return 'Pick an end date.';
    return `${rangeLabel(start, end)} — ${n} ${n === 1 ? 'day' : 'days'}.`;
}
/** Do two ranges name exactly the same days? */
export function rangeSame(aStart, aEnd, bStart, bEnd) {
    return rangeToDay(aStart) !== null && aStart === bStart && aEnd === bEnd;
}
//# sourceMappingURL=date-range-utils.js.map