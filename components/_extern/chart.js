/**
 * Chart — SVG-only renderer. Title, legend, empty state, and container
 * sizing are handled declaratively by chart.spec. This file exports only
 * `mountChartSVG`, which fills its container with an auto-resizing SVG.
 */
import { createHandle } from './types.js';
import { DEFAULT_COLORS } from './chart-utils.js';
// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const PAD = { top: 20, right: 20, bottom: 44, left: 52 };
// ---------------------------------------------------------------------------
// SVG helpers
// ---------------------------------------------------------------------------
function svgEl(tag) {
    return document.createElementNS('http://www.w3.org/2000/svg', tag);
}
function svgAttr(el, attrs) {
    for (const [k, v] of Object.entries(attrs))
        el.setAttribute(k, String(v));
}
function formatNum(v) {
    if (Math.abs(v) >= 1_000_000)
        return (v / 1_000_000).toFixed(1) + 'M';
    if (Math.abs(v) >= 1_000)
        return (v / 1_000).toFixed(1) + 'K';
    if (Number.isInteger(v))
        return String(v);
    return v.toFixed(1);
}
/**
 * Apply a printf-style format specifier to a number.
 * Supports the common subset: %d, %i, %f, %.Nf, %s, and %% literal.
 * Returns the original value stringified if the spec doesn't match.
 */
function applyFormatSpec(spec, v) {
    if (!spec)
        return String(v ?? '');
    const m = spec.match(/%(?:\.(\d+))?([dif])/);
    if (m) {
        const precision = m[1] ? parseInt(m[1], 10) : 0;
        const num = Number(v);
        if (isNaN(num))
            return String(v ?? '');
        const formatted = m[2] === 'f' ? num.toFixed(precision) : Math.round(num).toString();
        return spec.replace(/%(?:\.(\d+))?[dif]/, formatted).replace(/%%/g, '%');
    }
    if (spec.includes('%s')) {
        return spec.replace('%s', String(v ?? '')).replace(/%%/g, '%');
    }
    return String(v ?? '');
}
/**
 * Resolve a formatX/formatY value (function or string spec) into a
 * concrete formatter function.
 */
function resolveFormatter(f, fallback) {
    if (typeof f === 'function')
        return f;
    if (typeof f === 'string' && f.length > 0) {
        return (v) => applyFormatSpec(f, v);
    }
    return fallback;
}
// ---------------------------------------------------------------------------
// Chart rendering
// ---------------------------------------------------------------------------
function renderChart(svg, props, W, H) {
    while (svg.firstChild)
        svg.removeChild(svg.firstChild);
    const data = props.data ?? [];
    if (data.length === 0)
        return;
    const type = props.type;
    if (type === 'pie' || type === 'donut') {
        renderPie(svg, props, data, W, H, type === 'donut');
    }
    else {
        renderCartesian(svg, props, data, W, H);
    }
}
// ---------------------------------------------------------------------------
// Cartesian charts (line, bar, area)
// ---------------------------------------------------------------------------
function renderCartesian(svg, props, data, W, H) {
    const xKey = props.xKey ?? 'x';
    const type = props.type;
    const showGrid = props.showGrid !== false;
    const fmtY = resolveFormatter(props.formatY, (v) => formatNum(Number(v)));
    const fmtX = resolveFormatter(props.formatX, (v) => String(v ?? ''));
    const connectNulls = props.connectNulls === true;
    const seriesList = props.series && props.series.length > 0
        ? props.series
        : [{ key: 'y', label: 'y', color: DEFAULT_COLORS[0] }];
    // Compute Y scale — support custom yMin/yMax for charts that shouldn't start at 0
    const allRawY = seriesList.flatMap(s => data.map(d => {
        const raw = d[s.key];
        return raw === null || raw === undefined ? null : Number(raw);
    }));
    const allY = allRawY.filter((v) => v !== null && !isNaN(v));
    const dataMin = allY.length > 0 ? Math.min(...allY) : 0;
    const dataMax = allY.length > 0 ? Math.max(...allY) : 0;
    const yMin = props.yMin != null ? props.yMin : Math.min(dataMin, 0);
    const yMax = props.yMax != null ? props.yMax : Math.max(dataMax, 0);
    const yRange = (yMax - yMin) || 1;
    const pad = PAD;
    const cW = W - pad.left - pad.right;
    const cH = H - pad.top - pad.bottom;
    const xScale = (i) => pad.left + (data.length <= 1 ? cW / 2 : (i / (data.length - 1)) * cW);
    const barW = data.length > 0 ? (cW / data.length) * 0.65 : 20;
    const barX = (i) => pad.left + (i / data.length) * cW + ((cW / data.length) - barW) / 2;
    const yScale = (v) => pad.top + cH - ((v - yMin) / yRange) * cH;
    // Grid lines + Y labels
    const gridCount = 4;
    for (let i = 0; i <= gridCount; i++) {
        const v = yMin + (yRange * i) / gridCount;
        const y = yScale(v);
        if (showGrid) {
            const line = svgEl('line');
            svgAttr(line, { x1: pad.left, x2: pad.left + cW, y1: y, y2: y, stroke: '#f3f4f6', 'stroke-width': 1 });
            svg.appendChild(line);
        }
        const label = svgEl('text');
        svgAttr(label, { x: pad.left - 6, y: y + 4, 'text-anchor': 'end', fill: '#6b7280', 'font-size': 11 });
        label.textContent = fmtY(v, i);
        svg.appendChild(label);
    }
    // X-axis baseline
    const baseline = svgEl('line');
    svgAttr(baseline, { x1: pad.left, x2: pad.left + cW, y1: pad.top + cH, y2: pad.top + cH, stroke: '#e5e7eb', 'stroke-width': 1 });
    svg.appendChild(baseline);
    // X-axis labels — skip to avoid crowding
    const maxLabels = Math.floor(cW / 55);
    const step = Math.max(1, Math.ceil(data.length / maxLabels));
    data.forEach((d, i) => {
        if (i % step !== 0 && i !== data.length - 1)
            return;
        const x = type === 'bar' ? barX(i) + barW / 2 : xScale(i);
        const label = svgEl('text');
        svgAttr(label, { x, y: pad.top + cH + 16, 'text-anchor': 'middle', fill: '#6b7280', 'font-size': 11 });
        label.textContent = fmtX(d[xKey], i);
        svg.appendChild(label);
    });
    // Draw series
    for (const [si, s] of seriesList.entries()) {
        // Typed value array with null support for connectNulls handling
        const vals = data.map(d => {
            const raw = d[s.key];
            if (raw === null || raw === undefined)
                return null;
            const n = Number(raw);
            return isNaN(n) ? null : n;
        });
        if (type === 'bar') {
            vals.forEach((v, i) => {
                if (v === null)
                    return;
                const x = barX(i) + (si * barW) / seriesList.length;
                const w = barW / seriesList.length - 1;
                const barTop = yScale(v);
                const barBottom = yScale(0);
                const bH = Math.abs(barBottom - barTop);
                const bY = Math.min(barTop, barBottom);
                // Per-bar color from colorKey, fallback to series color
                const barFill = props.colorKey
                    ? String(data[i]?.[props.colorKey] ?? s.color)
                    : s.color;
                const rect = svgEl('rect');
                svgAttr(rect, {
                    x, y: bY, width: Math.max(w, 1), height: Math.max(bH, 1),
                    fill: barFill, rx: 2,
                });
                if (props.onPointClick) {
                    rect.style.cursor = 'pointer';
                    rect.addEventListener('click', () => props.onPointClick(i, s.key));
                }
                svg.appendChild(rect);
                if (props.showValues && bH > 16) {
                    const vl = svgEl('text');
                    svgAttr(vl, { x: x + w / 2, y: bY + 12, 'text-anchor': 'middle', fill: '#fff', 'font-size': 10 });
                    vl.textContent = fmtY(v, i);
                    svg.appendChild(vl);
                }
            });
        }
        else {
            // line / area — split into segments on null boundaries when connectNulls is false
            const segments = []; // [x, y, dataIdx]
            let current = [];
            vals.forEach((v, i) => {
                if (v === null) {
                    if (!connectNulls && current.length > 0) {
                        segments.push(current);
                        current = [];
                    }
                    return;
                }
                current.push([xScale(i), yScale(v), i]);
            });
            if (current.length > 0)
                segments.push(current);
            // Render each segment
            for (const seg of segments) {
                if (seg.length === 0)
                    continue;
                const ptStr = seg.map(([x, y]) => `${x},${y}`).join(' ');
                if (type === 'area') {
                    const bottom = yScale(Math.max(yMin, 0));
                    const areaStr = `${seg[0][0]},${bottom} ${ptStr} ${seg[seg.length - 1][0]},${bottom}`;
                    const area = svgEl('polygon');
                    svgAttr(area, { points: areaStr, fill: s.color + '28', stroke: 'none' });
                    svg.appendChild(area);
                }
                const line = svgEl('polyline');
                const lineAttrs = {
                    points: ptStr, fill: 'none', stroke: s.color,
                    'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round',
                };
                if (s.dashed)
                    lineAttrs['stroke-dasharray'] = '5,5';
                svgAttr(line, lineAttrs);
                svg.appendChild(line);
                // Dots
                seg.forEach(([x, y, i]) => {
                    const circle = svgEl('circle');
                    svgAttr(circle, { cx: x, cy: y, r: 3, fill: s.color, stroke: 'white', 'stroke-width': 1.5 });
                    if (props.onPointClick) {
                        circle.style.cursor = 'pointer';
                        circle.addEventListener('click', () => props.onPointClick(i, s.key));
                    }
                    svg.appendChild(circle);
                });
            }
        }
    }
}
// ---------------------------------------------------------------------------
// Pie / Donut (SVG arcs only — legend handled by chart.spec)
// ---------------------------------------------------------------------------
function renderPie(svg, props, data, W, H, isDonut) {
    const labelKey = props.labelKey ?? 'label';
    const valueKey = props.valueKey ?? 'value';
    const fmtY = resolveFormatter(props.formatY, (v) => formatNum(Number(v)));
    const values = data.map(d => Math.max(Number(d[valueKey]) || 0, 0));
    const total = values.reduce((a, b) => a + b, 0) || 1;
    const cx = W / 2;
    const cy = H / 2;
    const r = Math.min(W / 2, H / 2) * 0.78;
    const innerR = isDonut ? r * 0.5 : 0;
    let angle = -Math.PI / 2; // Start at top
    data.forEach((d, i) => {
        const v = values[i];
        const sweep = (v / total) * 2 * Math.PI;
        const color = props.series?.[i]?.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length];
        const midAngle = angle + sweep / 2;
        const x1 = cx + r * Math.cos(angle);
        const y1 = cy + r * Math.sin(angle);
        const x2 = cx + r * Math.cos(angle + sweep);
        const y2 = cy + r * Math.sin(angle + sweep);
        const largeArc = sweep > Math.PI ? 1 : 0;
        let pathD;
        if (isDonut) {
            const ix1 = cx + innerR * Math.cos(angle);
            const iy1 = cy + innerR * Math.sin(angle);
            const ix2 = cx + innerR * Math.cos(angle + sweep);
            const iy2 = cy + innerR * Math.sin(angle + sweep);
            pathD = `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} L ${ix2} ${iy2} A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix1} ${iy1} Z`;
        }
        else {
            pathD = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`;
        }
        const path = svgEl('path');
        svgAttr(path, { d: pathD, fill: color, stroke: 'white', 'stroke-width': 2 });
        if (props.onPointClick) {
            path.style.cursor = 'pointer';
            path.addEventListener('click', () => props.onPointClick(i, String(d[labelKey] ?? i)));
        }
        svg.appendChild(path);
        // Value label inside segment if large enough
        if (props.showValues && sweep > 0.4) {
            const labelR = isDonut ? (r + innerR) / 2 : r * 0.65;
            const lx = cx + labelR * Math.cos(midAngle);
            const ly = cy + labelR * Math.sin(midAngle);
            const vl = svgEl('text');
            svgAttr(vl, { x: lx, y: ly + 4, 'text-anchor': 'middle', fill: 'white', 'font-size': 11, 'font-weight': 600 });
            vl.textContent = fmtY(v, i);
            svg.appendChild(vl);
        }
        angle += sweep;
    });
    // Center label for donut
    if (isDonut) {
        const tl = svgEl('text');
        svgAttr(tl, { x: cx, y: cy + 5, 'text-anchor': 'middle', fill: '#374151', 'font-size': 14, 'font-weight': 700 });
        tl.textContent = fmtY(total, 0);
        svg.appendChild(tl);
        const sub = svgEl('text');
        svgAttr(sub, { x: cx, y: cy + 19, 'text-anchor': 'middle', fill: '#9ca3af', 'font-size': 10 });
        sub.textContent = 'total';
        svg.appendChild(sub);
    }
}
// ---------------------------------------------------------------------------
// Mount factory — registered as 'ChartSVG' in index.ts
// ---------------------------------------------------------------------------
/**
 * Mount a self-sizing SVG chart into `container`.
 *
 * This is the low-level renderer. The container's height is controlled by
 * the wrapping chart.spec block (`grow: true` inside a fixed-height parent).
 * Title, legend, and empty state are rendered as HTML by chart.spec.
 */
export function mountChartSVG(container, props) {
    let current = props;
    const svg = svgEl('svg');
    svg.style.cssText = 'width:100%;height:100%;overflow:visible;display:block;';
    container.appendChild(svg);
    let rafId = 0;
    function redraw() {
        rafId = 0;
        const W = container.clientWidth || 500;
        const H = container.clientHeight || 300;
        renderChart(svg, current, W, H);
    }
    const ro = new ResizeObserver(() => {
        if (rafId)
            cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(redraw);
    });
    ro.observe(container);
    requestAnimationFrame(redraw);
    return createHandle((next) => {
        current = { ...current, ...next };
        if (rafId)
            cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(redraw);
    }, () => {
        ro.disconnect();
        if (rafId)
            cancelAnimationFrame(rafId);
        svg.remove();
    });
}
//# sourceMappingURL=chart.js.map