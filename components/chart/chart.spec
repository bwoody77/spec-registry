@extern { resolveSeries, resolveSegmentMeta } from "@spec/components/chart-utils.js"

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
  title: string = "",
  showLegend: boolean = true,
  showGrid: boolean = true,
  showValues: boolean = false
) {
  @computed {
    isEmpty: data == null || data.length == 0
    isPie: type == "pie" || type == "donut"
    resolvedSeries: resolveSeries(type, series, yKey, color, colors)
    legendItems: isPie ? resolveSegmentMeta(data, colors, labelKey) : resolvedSeries
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
