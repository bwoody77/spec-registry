@extern { timeRangeStartOptions, timeRangeEndOptions, clampEnd } from "@spec/components/time-range-utils.js"

// Paired start/end time selects. The end list is always >= start + gapMinutes;
// changing the start recomputes the end options and, if the current end would
// become invalid, auto-advances it. Emits a single change with the clamped
// { start, end } pair so consumers never re-implement the rule. Values are
// 24h "HH:MM"; `format` controls only the visible labels.
component TimeRangePicker(startValue: string = "09:00", endValue: string = "10:00", minHour: number = 6, maxHour: number = 22, stepMinutes: number = 30, gapMinutes: number = 30, format: string = "24", startLabel: string = "", endLabel: string = "", disabled: boolean = false) {
  @computed {
    startOpts: timeRangeStartOptions(minHour, maxHour, stepMinutes, gapMinutes, format)
    endOpts: timeRangeEndOptions(startValue, minHour, maxHour, stepMinutes, gapMinutes, format)
  }

  @actions {
    onStart(v) {
      emit("change", { start: v, end: clampEnd(v, endValue, gapMinutes) })
    }
    onEnd(v) {
      emit("change", { start: startValue, end: v })
    }
  }

  block {
    layout: horizontal, gap: spacing.2, align: center
    role: "group"
    aria-label: "Time range"

    block {
      grow: true
      Select(options: startOpts, value: startValue, disabled: disabled, label: startLabel) {
        on change(v): onStart(v)
      }
    }
    text("to") { style: type.label-sm, color: semantic.text-tertiary }
    block {
      grow: true
      Select(options: endOpts, value: endValue, disabled: disabled, label: endLabel) {
        on change(v): onEnd(v)
      }
    }
  }
}
