// An `align: string = "center"` prop was REMOVED here — it never worked.
//
// It did `layout: vertical, align: align`, but `align:` is a layout sub-arg
// resolved at COMPILE time: the value must be one of the literal keywords
// (start | center | end | stretch | baseline), and a prop reference is not a
// literal. `ALIGN_MAP[align]` was therefore always undefined, so no alignItems
// was ever emitted and every Stat rendered with the flex default regardless of
// what the caller passed. Nothing broke by removing it: no call site in any
// consuming app passed it, precisely because it had no observable effect.
//
// The intent was real and is still wanted — the original comment noted that
// start-aligned is what a dense KPI row needs, and that apps hand-rolled their
// own tile rather than adopt this one (Vector's `OsMiniStat` is one such copy).
// Delivering it needs dynamic layout alignment in the compiler: `gap:` already
// accepts a binding via emitStyleBinding, but `align:` emits a static string,
// and a bound value would also need a runtime word->CSS mapping because the
// author writes Spec's `start` while CSS wants `flex-start`. Filed as its own
// piece of work; restore the prop once that lands.
//
// Until then this tile is centred, and that is now TRUE rather than merely
// documented.
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
