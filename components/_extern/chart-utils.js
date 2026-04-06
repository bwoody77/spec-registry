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
export const DEFAULT_COLORS = [
    '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16',
];
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
        }));
    }
    return [{ key: yKey || 'y', label: yKey || 'y', color: color || DEFAULT_COLORS[0] }];
}
/**
 * Build legend items for pie/donut charts from the raw data array.
 */
export function resolveSegmentMeta(data, colors, labelKey) {
    return data.map((d, i) => ({
        label: String(d[labelKey] ?? i),
        color: colors?.[i] ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length],
    }));
}
//# sourceMappingURL=chart-utils.js.map