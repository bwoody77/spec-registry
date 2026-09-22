@extern { _registerChart } from "@spec/components/chart-utils.js"

fn _defaultColor(i: number) -> string {
  let colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16']
  return colors[i % length(colors)]
}

fn resolveSeries(type: string, series: list, yKey: string, color: string, colors: list) -> list {
  if type == 'pie' || type == 'donut' { return [] }
  if series != null && length(series) > 0 {
    return series |> map((s, i) => {
      return {
        key: s.key,
        label: s.label ?? s.key,
        color: s.color ?? (colors?.[i] ?? _defaultColor(i)),
        dashed: s.dashed ?? false
      }
    })
  }
  let k = yKey ?? 'y'
  return [{ key: k, label: k, color: color ?? _defaultColor(0), dashed: false }]
}

// The legend's color for slice i, and it MUST agree with the arc.
//
// This is the Spec-side twin of sliceColor() in chart-utils.ts; the precedence
// is stated there at length (colorKey, then a series color, then the
// positional palette, then the default — each falling through on a blank
// rather than painting a transparent wedge). A pie resolves no series, so the
// series step is the one rung this copy leaves out.
//
// It is a copy because a `fn` here cannot call the extern, and the two are
// held together by chart-slice-color.test.ts, which asserts this file's chain
// matches the TS one.
fn _sliceColor(d: object, i: number, colors: list, colorKey: string) -> string {
  if colorKey != null && colorKey != '' {
    let fromDatum = d[colorKey]
    if fromDatum != null && toString(fromDatum) != '' { return toString(fromDatum) }
  }
  return colors?.[i] ?? _defaultColor(i)
}

fn resolveSegmentMeta(data: list, colors: list, labelKey: string, colorKey: string) -> list {
  return data |> map((d, i) => {
    return {
      label: toString(d[labelKey] ?? i),
      color: _sliceColor(d, i, colors, colorKey)
    }
  })
}

component Chart(
  type: string = "line",
  data: array = [],
  series: array = [],
  xKey: string = "x",
  yKey: string = "y",
  labelKey: string = "label",
  valueKey: string = "value",
  color: string = "",
  colors: array = [],
  height: string = "300px",
  title: text = "",
  showLegend: boolean = true,
  showGrid: boolean = true,
  showValues: boolean = false,
  yMin: number = null,
  yMax: number = null,
  connectNulls: boolean = false,
  colorKey: string = "",
  formatX: string = "",
  formatY: string = ""
) {
  @computed {
    isEmpty: data == null || data.length == 0
    isPie: type == "pie" || type == "donut"
    resolvedSeries: resolveSeries(type, series, yKey, color, colors)
    legendItems: isPie ? resolveSegmentMeta(data, colors, labelKey, colorKey) : resolvedSeries
    showLegendBar: showLegend && (isPie || resolvedSeries.length > 1)
  }

  block {
    layout: vertical, gap: spacing.2
    width: "100%"
    height: height

    // Title
    block {
      visibility: title != ""
      layout: horizontal, justify: center
      padding-bottom: spacing.1
      text(title) { style: type.label-md, color: semantic.text-primary }
    }

    // SVG canvas via mount factory
    block {
      grow: true
      visibility: isEmpty == false
      mount("ChartSVG") {
        type: type
        data: data
        series: resolvedSeries
        xKey: xKey
        labelKey: labelKey
        valueKey: valueKey
        showGrid: showGrid
        showValues: showValues
        yMin: yMin
        yMax: yMax
        connectNulls: connectNulls
        colorKey: colorKey
        // `colors` was NOT passed here, and that alone made the prop inert for
        // pie and donut however the renderer behaved: it had no way to see the
        // palette. Cartesian charts still fold `colors` into resolvedSeries
        // above and ignore this.
        colors: colors
        formatX: formatX
        formatY: formatY
      }
    }

    // Empty state
    block {
      visibility: isEmpty
      grow: true
      layout: horizontal, justify: center, align: center
      text("No data") { style: type.body-md, color: semantic.text-tertiary }
    }

    // Legend
    block {
      visibility: showLegendBar
      layout: horizontal, justify: center, gap: spacing.3
      each legendItems as item {
        block {
          layout: horizontal, align: center, gap: spacing.1
          block {
            width: "10px"
            height: "10px"
            border-radius: radius.sm
            background: item.color
          }
          text(item.label) { style: type.caption, color: semantic.text-secondary }
        }
      }
    }
  }
}
