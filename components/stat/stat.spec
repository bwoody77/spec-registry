component Stat(label: string, value: string, trend: string = "", trendValue: string = "", helpText: string = "") {
  block {
    layout: vertical, align: center

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
