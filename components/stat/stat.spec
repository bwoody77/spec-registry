// `align` follows the same add-a-prop-with-a-safe-default shape as form-kit's
// `boxAlign`: the default reproduces the original centred tile exactly, so no
// existing caller can shift. Left-aligned is what a dense KPI row wants — the
// reason several apps hand-rolled their own tile rather than adopt this one.
component Stat(label: string, value: string, trend: string = "", trendValue: string = "", helpText: string = "", align: string = "center") {
  block {
    layout: vertical, align: align

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
