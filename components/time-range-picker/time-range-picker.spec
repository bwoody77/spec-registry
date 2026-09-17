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

// ═══════════════════════════════════════════════════════════════════════════
// Time option lists and clamps behind TimeRangePicker, as portable fns.
//
// Values are 24h "HH:MM"; dates are "YYYY-MM-DD". `format` ('12' | '24')
// affects labels only, and a 12h label's AM/PM marker is calendarMeridiem(),
// so a locale build reads in its own language. Dates compare as YYYYMMDD
// integers and roll over by integer epoch-day math, with no Date, so no
// timezone can move one. Tested in time-range-picker-fns.test.ts.
//
// Shapes:
//   option  { value, label }
//   end     { endDate, endTime }
// ═══════════════════════════════════════════════════════════════════════════

fn trpPad2(n: number) -> string {
  return padStart("{n}", 2, '0')
}

// Empty or malformed → 00:00, never NaN.
fn trpToMinutes(hhmm: any) -> number {
  if typeOf(hhmm) != 'string' || includes(hhmm, ':') == false { return 0 }
  let parts = split(hhmm, ':')
  return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10)
}

fn trpFromMinutes(min: number) -> string {
  return trpPad2(floor(min / 60)) + ':' + trpPad2(min % 60)
}

// Hour 24 is END-OF-DAY midnight, not a 25th hour: fold it onto 0 before the
// AM/PM split. Without the fold `h >= 12` picks PM and `h > 12` maps 24 onto
// 12, so a range ending at midnight renders "12:00 PM" — noon. On a 0..24 grid
// that puts two options labelled "12:00 PM" in one dropdown with nothing to
// tell them apart, and picking the wrong one silently records the wrong time.
fn trpLabel12(hhmm: string) -> string {
  let parts = split(hhmm, ':')
  let h = parseInt(parts[0], 10)
  let m = parseInt(parts[1], 10)
  let h24 = h == 24 ? 0 : h
  let period = h24 >= 12 ? calendarMeridiem('pm') : calendarMeridiem('am')
  let display = h24 == 0 ? 12 : (h24 > 12 ? h24 - 12 : h24)
  return "{display}:" + trpPad2(m) + " {period}"
}

fn trpLabelFor(hhmm: string, format: string) -> string {
  return format == '12' ? trpLabel12(hhmm) : hhmm
}

// All time-of-day options between minHour:00 and maxHour:00 inclusive, on a
// stepMinutes grid.
fn timeOptions(minHour: number, maxHour: number, stepMinutes: number, format: string) -> list {
  let out = []
  if stepMinutes <= 0 { return out }
  let first = minHour * 60
  let count = floor((maxHour * 60 - first) / stepMinutes) + 1
  // maxHour before minHour. JavaScript's range() would answer [], but Swift's
  // `0..<count` traps on a negative count.
  if count <= 0 { return out }
  for i in range(0, count) {
    let value = trpFromMinutes(first + i * stepMinutes)
    push(out, { value: value, label: trpLabelFor(value, format) })
  }
  return out
}

// Start options trimmed so the latest start still leaves room for at least one
// valid end (start + gap <= maxHour:00).
fn timeRangeStartOptions(minHour: number, maxHour: number, stepMinutes: number, gapMinutes: number, format: string) -> list {
  let latestStart = maxHour * 60 - gapMinutes
  return filter(timeOptions(minHour, maxHour, stepMinutes, format), o => trpToMinutes(o.value) <= latestStart)
}

// End options that are all >= start + gap.
fn timeRangeEndOptions(startValue: string, minHour: number, maxHour: number, stepMinutes: number, gapMinutes: number, format: string) -> list {
  let least = trpToMinutes(startValue) + gapMinutes
  return filter(timeOptions(minHour, maxHour, stepMinutes, format), o => trpToMinutes(o.value) >= least)
}

// endValue if still >= start + gap, else the first valid end.
fn clampEnd(startValue: string, endValue: string, gapMinutes: number) -> string {
  let least = trpToMinutes(startValue) + gapMinutes
  if endValue != '' && trpToMinutes(endValue) >= least { return endValue }
  return trpFromMinutes(least)
}

// Epoch day for a civil date (m is 1-based) — Hinnant's days_from_civil.
// (A copy of DateRangePicker's drpCivilToDay: a registry component is one file.)
fn trpCivilToDay(y: number, m: number, d: number) -> number {
  let yy = m <= 2 ? y - 1 : y
  let era = floor(yy / 400)
  let yoe = yy - era * 400
  let mp = m > 2 ? m - 3 : m + 9
  let doy = floor((153 * mp + 2) / 5) + d - 1
  let doe = yoe * 365 + floor(yoe / 4) - floor(yoe / 100) + doy
  return era * 146097 + doe - 719468
}

// Civil date { y, m (1-based), d } for an epoch day — Hinnant's civil_from_days.
fn trpDayToCivil(z: number) -> map {
  let zz = z + 719468
  let era = floor(zz / 146097)
  let doe = zz - era * 146097
  let yoe = floor((doe - floor(doe / 1460) + floor(doe / 36524) - floor(doe / 146096)) / 365)
  let doy = doe - (365 * yoe + floor(yoe / 4) - floor(yoe / 100))
  let mp = floor((5 * doy + 2) / 153)
  let d = doy - floor((153 * mp + 2) / 5) + 1
  let m = mp < 10 ? mp + 3 : mp - 9
  let y = yoe + era * 400 + (m <= 2 ? 1 : 0)
  return { y: y, m: m, d: d }
}

// "YYYY-MM-DD" as the integer YYYYMMDD; '' sorts before every date.
fn trpDateToNum(ymd: string) -> number {
  if ymd == '' { return -1 }
  return parseInt(regexReplace(ymd, '-', ''), 10)
}

fn trpAddOneDay(ymd: string) -> string {
  let parts = split(ymd, '-')
  let c = trpDayToCivil(trpCivilToDay(parseInt(parts[0], 10), parseInt(parts[1], 10), parseInt(parts[2], 10)) + 1)
  return "{c.y}-" + trpPad2(c.m) + '-' + trpPad2(c.d)
}

// Clamp end date+time so the end is >= start + gap. An end date before the
// start date snaps to the start date. When the dates are equal, push the end
// time to >= start + gap; if that exceeds maxHour:00, roll to the next day at
// minHour:00. A missing start date means nothing to clamp against.
fn clampEndDateTime(startDate: string, startTime: string, endDate: string, endTime: string, gapMinutes: number, minHour: number, maxHour: number, stepMinutes: number) -> map {
  if startDate == '' { return { endDate: endDate, endTime: endTime } }
  let d = endDate
  if trpDateToNum(d) < trpDateToNum(startDate) { d = startDate }
  if d == startDate {
    let minEnd = trpToMinutes(startTime) + gapMinutes
    if minEnd > maxHour * 60 {
      return { endDate: trpAddOneDay(startDate), endTime: trpFromMinutes(minHour * 60) }
    }
    if endTime == '' || trpToMinutes(endTime) < minEnd {
      return { endDate: d, endTime: trpFromMinutes(minEnd) }
    }
  }
  return { endDate: d, endTime: endTime == '' ? trpFromMinutes(minHour * 60) : endTime }
}
