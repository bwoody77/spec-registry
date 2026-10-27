// `align` picks the tile's cross-axis alignment: "start" left-aligns label,
// value, trend and help text (a dense KPI row, e.g. Vector's W&B verdict);
// anything else, the default included, centers it.
//
// It is a match between fixed keywords, not `align: align`. The web and
// Android bind an `align:` expression, but the iOS emitter gives a VStack
// whose alignment is bound `.leading`, so a bound prop would have left-aligned
// every default Stat in an iOS app. The default arm is the 0.4.0 tile: its
// children sit straight in the centered column (the match host is
// `display: contents`). The start arm wraps them in a full-width column of its
// own aligned to the start edge. The arms repeat the children: change both;
// stat-align.test.ts compares them. (An earlier `align` prop, written before
// the compiler bound expressions, never took effect and was removed.)
component Stat(label: text, value: string, trend: string = "", trendValue: string = "", helpText: text = "", align: string = "center") {
  block {
    layout: vertical, align: center

    match align {
      "start" -> {
        block {
          width: 100%
          layout: vertical, align: start

          text(label) { style: type.label-md, color: semantic.text-secondary, text-transform: "uppercase", letter-spacing: "0.05em" }
          text(value) { style: type.label-lg, weight: 700, color: semantic.text-primary }

          block {
            visibility: trend != ""
            layout: horizontal, gap: 4px, align: center
            text(match trend { "up" -> "↑", "down" -> "↓", _ -> "→" }) {
              style: type.label-sm
              color: match trend { "up" -> "#22c55e", "down" -> "#ef4444", _ -> semantic.text-tertiary }
            }
            text(trendValue) {
              visibility: trendValue != ""
              style: type.label-sm
              color: match trend { "up" -> "#22c55e", "down" -> "#ef4444", _ -> semantic.text-tertiary }
            }
          }

          text(helpText) { visibility: helpText != "", style: type.label-sm, color: semantic.text-tertiary }
        }
      }
      _ -> {
        text(label) { style: type.label-md, color: semantic.text-secondary, text-transform: "uppercase", letter-spacing: "0.05em" }
        text(value) { style: type.label-lg, weight: 700, color: semantic.text-primary }

        block {
          visibility: trend != ""
          layout: horizontal, gap: 4px, align: center
          text(match trend { "up" -> "↑", "down" -> "↓", _ -> "→" }) {
            style: type.label-sm
            color: match trend { "up" -> "#22c55e", "down" -> "#ef4444", _ -> semantic.text-tertiary }
          }
          text(trendValue) {
            visibility: trendValue != ""
            style: type.label-sm
            color: match trend { "up" -> "#22c55e", "down" -> "#ef4444", _ -> semantic.text-tertiary }
          }
        }

        text(helpText) { visibility: helpText != "", style: type.label-sm, color: semantic.text-tertiary }
      }
    }
  }
}
