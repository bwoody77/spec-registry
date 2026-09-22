/**
 * chart-utils.ts — Helper functions for chart.spec via @extern.
 *
 * Imported by the compiled chart.spec as ES imports. Also self-registers the
 * ChartSVG mount factory so that mount("ChartSVG") works in chart.spec without
 * requiring a separate import of @spec/components/index.js.
 */
import { registerMount } from '@spec/runtime';
import { mountChartSVG } from './chart.js';
// Register on first import so mount("ChartSVG") resolves at runtime.
registerMount('ChartSVG', mountChartSVG);
/** Dummy export so @extern { _registerChart } keeps the import for the side effect. */
export function _registerChart() { }
export const DEFAULT_COLORS = [
    '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16',
];
/**
 * The color one pie/donut slice is painted — the SINGLE answer, used by both
 * the arc and the legend entry.
 *
 * ── Why this is a shared function rather than two expressions ─────────────
 * It was two, and they disagreed. `renderPie` read `props.series?.[i]?.color
 * ?? DEFAULT_COLORS[i]`, and resolveSeries() returns [] for pie/donut, so the
 * arc ALWAYS took the default palette. `resolveSegmentMeta` built the legend
 * from `colors?.[i] ?? DEFAULT_COLORS[i]`. Pass `colors` and the key was
 * painted in the caller's colors while the chart kept the library's — a
 * legend that confidently names the wrong wedge, which is worse than no
 * legend at all.
 *
 * Two callers cannot drift if there is one function, so there is one.
 *
 * ── Precedence, most specific first ───────────────────────────────────────
 *   1. `colorKey` — a color carried by the datum itself. Most specific: it
 *      varies per row, and it is what bar charts already honor
 *      (chart.ts, per-bar fill), so pie follows a precedent rather than
 *      inventing a rule.
 *   2. `series[i].color` — an explicit series color. A pie normally resolves
 *      no series at all; this is here so a caller that passes one anyway is
 *      not ignored.
 *   3. `colors[i]` — the positional palette.
 *   4. `DEFAULT_COLORS[i % len]` — wraps, so more slices than colors still
 *      paint.
 *
 * Every step falls THROUGH on a blank answer rather than returning it. An
 * empty fill renders a transparent wedge, which reads as a gap in the ring —
 * a missing slice rather than a wrongly-colored one, and far harder to spot.
 */
export function sliceColor(props, datum, i) {
    const key = props.colorKey;
    if (key) {
        const fromDatum = datum?.[key];
        if (fromDatum != null && String(fromDatum) !== '')
            return String(fromDatum);
    }
    const fromSeries = props.series?.[i]?.color;
    if (fromSeries)
        return fromSeries;
    const fromColors = props.colors?.[i];
    if (fromColors)
        return fromColors;
    return DEFAULT_COLORS[i % DEFAULT_COLORS.length];
}
/**
 * Normalise the series definition for cartesian charts.
 * Returns [] for pie/donut (no Cartesian series needed).
 */
export function resolveSeries(type, series, yKey, color, colors) {
    if (type === 'pie' || type === 'donut')
        return [];
    if (series && series.length > 0) {
        return series.map((s, i) => ({
            key: s.key,
            label: s.label ?? s.key,
            color: s.color ?? (colors?.[i] ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length]),
            dashed: s.dashed ?? false,
        }));
    }
    return [{ key: yKey || 'y', label: yKey || 'y', color: color || DEFAULT_COLORS[0], dashed: false }];
}
/**
 * Build legend items for pie/donut charts from the raw data array.
 */
export function resolveSegmentMeta(data, colors, labelKey, colorKey) {
    // sliceColor(), not a second copy of the fallback chain: the legend and the
    // arc it names must agree by construction. `colorKey` is optional so every
    // existing caller keeps compiling, and defaults to the behavior they had.
    return data.map((d, i) => ({
        label: String(d[labelKey] ?? i),
        color: sliceColor({ colors, colorKey }, d, i),
    }));
}
//# sourceMappingURL=chart-utils.js.map