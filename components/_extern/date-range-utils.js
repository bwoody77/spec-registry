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
export function drpToDay(iso) {
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
export function drpFromDay(z) {
    return new Date(z * DAY_MS).toISOString().slice(0, 10);
}
function dow(z) {
    return new Date(z * DAY_MS).getUTCDay();
}
function daysIn(year, month) {
    return new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
}
export function drpAddDays(iso, n) {
    const z = drpToDay(iso);
    return z === null ? '' : drpFromDay(z + n);
}
/** Days in a range, BOTH ends counted; 0 when either end is missing or it runs backwards. */
export function drpDays(start, end) {
    const a = drpToDay(start);
    const b = drpToDay(end);
    if (a === null || b === null || b < a)
        return 0;
    return b - a + 1;
}
/** 'Aug 30 – Sep 12, 2026' · 'Sep 13 – 26, 2026' · 'Dec 27, 2026 – Jan 9, 2027' · 'Sep 13, 2026'. */
export function drpLabel(start, end) {
    const a = drpToDay(start);
    const b = drpToDay(end);
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
export function drpLongDate(iso) {
    const z = drpToDay(iso);
    if (z === null)
        return '';
    const d = new Date(z * DAY_MS);
    return `${WEEKDAYS_LONG[d.getUTCDay()]}, ${MONTHS_LONG[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}
export function drpMonthTitle(year, month) {
    const v = drpShiftView(year, month, 0);
    return `${MONTHS_LONG[v.month]} ${v.year}`;
}
function bandIndexOf(z, bands) {
    if (!Array.isArray(bands))
        return -1;
    for (let i = 0; i < bands.length; i++) {
        const s = drpToDay(bands[i]?.start);
        const e = drpToDay(bands[i]?.end);
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
export function drpSuggestEnd(start, periodDays, bands) {
    const z = drpToDay(start);
    if (z === null)
        return '';
    if (Number.isFinite(periodDays) && periodDays > 0)
        return drpFromDay(z + Math.floor(periodDays) - 1);
    const i = bandIndexOf(z, bands);
    if (i < 0)
        return '';
    return bands[i].end;
}
/** One click on `day`. Returns the next selection state. */
export function drpPick(start, end, picking, day, periodDays, bands) {
    const zd = drpToDay(day);
    if (zd === null)
        return { start, end, picking, suggested: false };
    const zs = drpToDay(start);
    if (picking && zs !== null && zd >= zs) {
        return { start, end: day, picking: false, suggested: false };
    }
    const suggestedEnd = drpSuggestEnd(day, periodDays, bands);
    return { start: day, end: suggestedEnd, picking: true, suggested: suggestedEnd !== '' };
}
/**
 * The cells of one month, Sunday-first, padded with blanks to whole weeks.
 *
 * While `picking` with a `hover` on or after the start, the hover previews the
 * end; otherwise the start..end on record is drawn, tentative when `suggested`.
 */
export function drpMonthCells(year, month, start, end, hover, picking, suggested, bands, today) {
    const v = drpShiftView(year, month, 0);
    const first = Math.round(Date.UTC(v.year, v.month, 1) / DAY_MS);
    const count = daysIn(v.year, v.month);
    const zs = drpToDay(start);
    const ze = drpToDay(end);
    const zh = drpToDay(hover);
    const zt = drpToDay(today);
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
    const blank = (i) => ({
        key: `blank-${i}`,
        iso: '', day: 0, blank: true, inRange: false, isStart: false, isEnd: false,
        tentative: false, today: false, bandParity: -1, bandStart: false, bandEnd: false, label: '',
    });
    const cells = [];
    for (let i = 0; i < dow(first); i++)
        cells.push(blank(cells.length));
    for (let d = 1; d <= count; d++) {
        const z = first + d - 1;
        const iso = drpFromDay(z);
        const inRange = lo !== null && hi !== null && z >= lo && z <= hi;
        const isStart = lo !== null && z === lo;
        const isEnd = hi !== null && z === hi && inRange;
        const bi = bandIndexOf(z, bands);
        const band = bi >= 0 ? bands[bi] : null;
        let label = drpLongDate(iso);
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
            key: iso,
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
        cells.push(blank(cells.length));
    return cells;
}
/** A month's cells, carrying only what does NOT change while a range is picked. */
export function drpMonthGrid(year, month, bands, today) {
    return drpMonthCells(year, month, '', '', '', false, false, bands, today).map((c) => ({
        key: c.key, iso: c.iso, day: c.day, blank: c.blank, today: c.today,
        bandParity: c.bandParity, bandStart: c.bandStart, bandEnd: c.bandEnd,
    }));
}
/** What to draw for the current selection — the rules drpMonthCells applies, once. */
export function drpSpan(start, end, hover, picking, suggested) {
    const zs = drpToDay(start);
    const ze = drpToDay(end);
    const zh = drpToDay(hover);
    const awaitingEnd = picking && ze === null;
    if (picking && zs !== null && zh !== null && zh >= zs)
        return { lo: start, hi: hover, tentative: true, awaitingEnd };
    if (zs !== null && ze !== null && ze >= zs)
        return { lo: start, hi: end, tentative: suggested, awaitingEnd };
    if (zs !== null)
        return { lo: start, hi: start, tentative: false, awaitingEnd };
    return { lo: '', hi: '', tentative: false, awaitingEnd: false };
}
/** Is a cell's ISO date inside the span? False for a blank cell or an empty span. */
export function drpIn(iso, span) {
    if (!iso || !span || !span.lo)
        return false;
    return iso >= span.lo && iso <= span.hi;
}
/** A cell's whole accessible name, exactly as drpMonthCells builds it. */
export function drpCellLabel(iso, span, today) {
    if (!iso)
        return '';
    let label = drpLongDate(iso);
    if (iso === today)
        label += ', today';
    const inRange = drpIn(iso, span);
    const isStart = inRange && iso === span.lo;
    const isEnd = inRange && iso === span.hi;
    if (isStart && isEnd && !span.awaitingEnd)
        label += ', selected';
    else if (isStart)
        label += ', start';
    else if (isEnd)
        label += span.tentative ? ', suggested end' : ', end';
    else if (inRange)
        label += ', in range';
    return label;
}
/** Normalized {year, month} after moving `n` months. */
export function drpShiftView(year, month, n) {
    const total = year * 12 + month + n;
    const y = Math.floor(total / 12);
    return { year: y, month: total - y * 12 };
}
/**
 * Which month opens on the LEFT of `months` visible months (1 on a phone).
 *
 *   • One month: the start's month (today's with no start). 0.1.2 used the
 *     two-month rule here too, so a phone showed an empty July for an August
 *     range — the range off screen and focus on a day that was not there.
 *   • Two months, a range spanning months: the start's month.
 *   • Two months, a range inside one month (or no range): that month on the
 *     left and the next on the right — unless it is TODAY's month, which goes
 *     on the right so last month shows beside it (reports look back).
 */
export function drpViewFor(start, end, today, months = 2) {
    const zs = drpToDay(start);
    const ze = drpToDay(end);
    const zt = drpToDay(today);
    const anchor = zs ?? zt ?? 0;
    const a = new Date(anchor * DAY_MS);
    if (months <= 1)
        return drpShiftView(a.getUTCFullYear(), a.getUTCMonth(), 0);
    const b = new Date((ze ?? anchor) * DAY_MS);
    const sameMonth = a.getUTCFullYear() === b.getUTCFullYear() && a.getUTCMonth() === b.getUTCMonth();
    if (!sameMonth)
        return drpShiftView(a.getUTCFullYear(), a.getUTCMonth(), 0);
    const t = new Date((zt ?? anchor) * DAY_MS);
    const todaysMonth = t.getUTCFullYear() === a.getUTCFullYear() && t.getUTCMonth() === a.getUTCMonth();
    return drpShiftView(a.getUTCFullYear(), a.getUTCMonth(), todaysMonth ? -1 : 0);
}
/** Is `iso` in one of the `months` months shown from {year, month}? */
export function drpInView(iso, year, month, months) {
    const z = drpToDay(iso);
    if (z === null)
        return false;
    const v = drpShiftView(year, month, 0);
    const lo = Math.round(Date.UTC(v.year, v.month, 1) / DAY_MS);
    const end = drpShiftView(v.year, v.month, Math.max(1, months));
    const hi = Math.round(Date.UTC(end.year, end.month, 1) / DAY_MS) - 1;
    return z >= lo && z <= hi;
}
/**
 * Keyboard focus movement in the grid, per the APG date-picker grid: arrows
 * by day / week, Home / End to the week's ends, PageUp / PageDown by month with
 * the day clamped to the target month. Any other key returns the date unchanged.
 */
export function drpMoveFocus(iso, key) {
    const z = drpToDay(iso);
    if (z === null)
        return iso;
    switch (key) {
        case 'ArrowLeft': return drpFromDay(z - 1);
        case 'ArrowRight': return drpFromDay(z + 1);
        case 'ArrowUp': return drpFromDay(z - 7);
        case 'ArrowDown': return drpFromDay(z + 7);
        case 'Home': return drpFromDay(z - dow(z));
        case 'End': return drpFromDay(z + (6 - dow(z)));
        case 'PageUp':
        case 'PageDown': {
            const d = new Date(z * DAY_MS);
            const v = drpShiftView(d.getUTCFullYear(), d.getUTCMonth(), key === 'PageUp' ? -1 : 1);
            const day = Math.min(d.getUTCDate(), daysIn(v.year, v.month));
            return drpFromDay(Math.round(Date.UTC(v.year, v.month, day) / DAY_MS));
        }
        default: return iso;
    }
}
/** What a screen reader hears after each step — and what the footer says. */
export function drpPrompt(start, end, picking, suggested) {
    if (drpToDay(start) === null)
        return 'Pick a start date.';
    if (picking && suggested && drpToDay(end) !== null) {
        return `Start ${drpLongDate(start)}. End suggested: ${drpLongDate(end)}. Pick another day to change it, or Apply.`;
    }
    if (picking)
        return `Start ${drpLongDate(start)}. Now pick the end date.`;
    const n = drpDays(start, end);
    if (n === 0)
        return 'Pick an end date.';
    return `${drpLabel(start, end)} — ${n} ${n === 1 ? 'day' : 'days'}.`;
}
/** Do two ranges name exactly the same days? */
export function drpSame(aStart, aEnd, bStart, bEnd) {
    return drpToDay(aStart) !== null && aStart === bStart && aEnd === bEnd;
}
//# sourceMappingURL=date-range-utils.js.map