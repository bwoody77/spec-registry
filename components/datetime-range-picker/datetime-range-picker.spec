@extern { timeOptions, clampEndDateTime } from "@spec/components/time-range-utils.js"

// Start date+time to end date+time, where the end may fall on a later day
// (e.g. Fri 5pm -> Tue 9am). The end is always clamped to >= start + gapMinutes:
// an earlier end date snaps to the start date, and on the same day the end time
// is pushed to >= start + gap (rolling to the next day if it would pass maxHour).
// Emits one change with the full { startDate, startTime, endDate, endTime }.
component DateTimeRangePicker(startDate: string = "", startTime: string = "09:00", endDate: string = "", endTime: string = "10:00", minHour: number = 6, maxHour: number = 22, stepMinutes: number = 30, gapMinutes: number = 30, format: string = "24", startLabel: string = "Start", endLabel: string = "End", disabled: boolean = false) {
  @computed {
    timeOpts: timeOptions(minHour, maxHour, stepMinutes, format)
  }

  @actions {
    setStartDate(v) {
      let c = clampEndDateTime(v, startTime, endDate, endTime, gapMinutes, minHour, maxHour, stepMinutes)
      emit("change", { startDate: v, startTime: startTime, endDate: c.endDate, endTime: c.endTime })
    }
    setStartTime(v) {
      let c = clampEndDateTime(startDate, v, endDate, endTime, gapMinutes, minHour, maxHour, stepMinutes)
      emit("change", { startDate: startDate, startTime: v, endDate: c.endDate, endTime: c.endTime })
    }
    setEndDate(v) {
      let c = clampEndDateTime(startDate, startTime, v, endTime, gapMinutes, minHour, maxHour, stepMinutes)
      emit("change", { startDate: startDate, startTime: startTime, endDate: c.endDate, endTime: c.endTime })
    }
    setEndTime(v) {
      let c = clampEndDateTime(startDate, startTime, endDate, v, gapMinutes, minHour, maxHour, stepMinutes)
      emit("change", { startDate: startDate, startTime: startTime, endDate: c.endDate, endTime: c.endTime })
    }
  }

  block {
    layout: vertical, gap: spacing.3
    role: "group"
    aria-label: "Date and time range"

    // Start row
    block {
      layout: vertical, gap: spacing.1
      block {
        visibility: startLabel != ""
        text(startLabel) { style: type.label-sm, color: semantic.text-secondary }
      }
      block {
        layout: horizontal, gap: spacing.2, align: center
        block {
          grow: true
          DatePicker(value: startDate, disabled: disabled) {
            on change(v): setStartDate(v)
          }
        }
        block {
          grow: true
          Select(options: timeOpts, value: startTime, disabled: disabled) {
            on change(v): setStartTime(v)
          }
        }
      }
    }

    text("to") { style: type.label-sm, color: semantic.text-tertiary }

    // End row
    block {
      layout: vertical, gap: spacing.1
      block {
        visibility: endLabel != ""
        text(endLabel) { style: type.label-sm, color: semantic.text-secondary }
      }
      block {
        layout: horizontal, gap: spacing.2, align: center
        block {
          grow: true
          DatePicker(value: endDate, disabled: disabled) {
            on change(v): setEndDate(v)
          }
        }
        block {
          grow: true
          Select(options: timeOpts, value: endTime, disabled: disabled) {
            on change(v): setEndTime(v)
          }
        }
      }
    }
  }
}
