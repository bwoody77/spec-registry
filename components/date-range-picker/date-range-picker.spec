@extern { toISODate, isoToOutput, todayStr } from "@spec/components/date-utils.js"

// DateRangePicker — a start and an end picked on ONE calendar.
//
// Replaces the two-unrelated-DatePickers shape ("From" and "To", each with its
// own one-month calendar that knows nothing of the other). One field opens one
// popover: presets, two months side by side (one on a phone), typed Start /
// Through fields, Apply / Cancel.
//
//   start, end   ISO 'YYYY-MM-DD' in; `change` emits { start, end } in ISO.
//   format       how the typed fields read and parse ('MM/DD/YYYY' default).
//   presets      [{ label, start, end }] — a click applies immediately.
//   periodDays   > 0: a picked start SUGGESTS end = start + periodDays − 1
//                (both ends count, so 14 days from Sep 13 ends Sep 26).
//   bands        [{ start, end }] — drawn as an alternating ruler under the
//                weeks (pay periods, sprints). With periodDays 0, the band a
//                start falls in suggests its end.
//   today        ISO; defaults to the browser's local date. Pass the business's
//                own "today" when that can differ.
//
// Interaction (the drp* fns at the end of this file hold every rule, tested in
// date-range-picker-fns.test.ts):
//   • click a start → the end is suggested (dashed) or awaited; hovering
//     previews the end; the next click on or after the start sets it; a click
//     before the start restarts; the same day twice is a one-day range.
//   • the months never move between the two clicks (NN/g: a calendar that
//     jumps between picks causes misclicks).
//   • Apply validates on click and names what is missing — it is never a
//     silently disabled button.
//   • keyboard: arrows / Home / End / PageUp / PageDown move, Enter or Space
//     picks, Escape closes without changing anything.
//
// Closing after Apply waits for the new props to flow back (see closeAfterApply)
// for the reason DatePicker's closeAfterPick gives: closing in the same action
// as emit() hides the control that emitted before the parent has applied it.
component DateRangePicker(start: string = "", end: string = "",
                          format: string = "MM/DD/YYYY",
                          presets: list = [],
                          periodDays: number = 0,
                          bands: list = [],
                          bandsLabel: string = "",
                          today: string = "",
                          label: text = "",
                          placeholder: text = "Pick dates",
                          disabled: boolean = false,
                          error: boolean = false,
                          errorMessage: text = "") {
  @state {
    open: false
    viewYear: 2026
    viewMonth: 0
    // The range being edited. `start` / `end` stay untouched until Apply.
    draftStart: ""
    draftEnd: ""
    // Waiting for the end: a hover previews it, the next click sets it.
    picking: false
    // draftEnd was filled in, not picked — drawn dashed until confirmed.
    suggested: false
    // The user typed or picked an end in this session, so a typed start
    // keeps it (see typeStart).
    endTouched: false
    hover: ""
    focusIso: ""
    startText: ""
    endText: ""
    problem: ""
    pendingClose: false
    refocusTrigger: false
  }

  // Two months side by side when there is room; one on a phone.
  @viewport { wide: 720px }

  @computed {
    todayIso: today != "" ? today : todayStr()
    months: wide ? 2 : 1
    rightView: drpShiftView(viewYear, viewMonth, 1)
    // The day lists change only with the month, the bands and today — never
    // with a hover or a pick — so their buttons are never rebuilt under the
    // keyboard. The selection is `span`, and each cell compares itself to it.
    leftCells: drpMonthGrid(viewYear, viewMonth, bands, todayIso)
    rightCells: drpMonthGrid(rightView.year, rightView.month, bands, todayIso)
    span: drpSpan(draftStart, draftEnd, hover, picking, suggested)
    leftTitle: drpMonthTitle(viewYear, viewMonth)
    rightTitle: drpMonthTitle(rightView.year, rightView.month)
    hasValue: start != "" && end != ""
    triggerText: hasValue ? drpLabel(start, end) : placeholder
    valueDays: drpDays(start, end)
    triggerMeta: valueDays == 0 ? "" : plural(valueDays, one: "{valueDays} day", other: "{valueDays} days")
    triggerName: (label != "" ? label : t("Date range")) + ": " + triggerText
    prompt: drpPrompt(draftStart, draftEnd, picking, suggested)
    hasPresets: presets.length > 0
    showBandsKey: bands.length > 0 && bandsLabel != ""
    popWidth: wide ? (hasPresets ? "780px" : "600px") : "320px"
    weekdays: calendarWeekdays('min')
  }

  @watch {
    start: { closeAfterApply() }
    end: { closeAfterApply() }
  }

  @actions {
    openPicker() {
      if disabled { return }
      draftStart = start
      draftEnd = end
      picking = false
      suggested = false
      endTouched = false
      hover = ""
      problem = ""
      pendingClose = false
      let v = drpViewFor(start, end, todayIso, months)
      viewYear = v.year
      viewMonth = v.month
      focusIso = start != "" ? start : todayIso
      syncTexts()
      refocusTrigger = false
      open = true
    }
    toggle() {
      if open {
        cancel()
      } else {
        openPicker()
      }
    }
    cancel() {
      open = false
      hover = ""
      pendingClose = false
      refocusTrigger = true
    }
    syncTexts() {
      startText = draftStart != "" ? isoToOutput(draftStart, format) : ""
      endText = draftEnd != "" ? isoToOutput(draftEnd, format) : ""
    }
    // The pick is taken into a local before any field is written: each field
    // below feeds the computeds the next line would otherwise read.
    pickDay(iso) {
      if iso == "" { return }
      let r = drpPick(draftStart, draftEnd, picking, iso, periodDays, bands)
      draftStart = r.start
      draftEnd = r.end
      picking = r.picking
      suggested = r.suggested
      // A click that completes a range chose its end; one that starts a range
      // has not chosen one yet.
      endTouched = r.picking == false
      hover = ""
      focusIso = iso
      problem = ""
      syncTexts()
    }
    hoverDay(iso) {
      if picking { hover = iso }
    }
    clearHover() { hover = "" }
    shiftView(n) {
      let v = drpShiftView(viewYear, viewMonth, n)
      viewYear = v.year
      viewMonth = v.month
    }
    prevMonth() { shiftView(-1) }
    nextMonth() { shiftView(1) }
    moveFocus(key) {
      let from = focusIso != "" ? focusIso : todayIso
      let next = drpMoveFocus(from, key)
      if drpInView(next, viewYear, viewMonth, months) == false {
        // Epoch days, never the ISO strings — see drpIn.
        if drpToDay(next) < drpToDay(from) {
          shiftView(-1)
        } else {
          shiftView(1)
        }
      }
      focusIso = next
      if picking { hover = next }
    }
    // No Enter / Space arm in the grids' key handlers: each day is a real
    // button, and a focused button already turns Enter and Space into a click.
    // Handling them in the grid as well picked TWICE — a start, then the same
    // day again, which is a one-day range (date-range-picker.test.ts, keyboard).
    applyPreset(s, e) {
      draftStart = s
      draftEnd = e
      picking = false
      suggested = false
      apply()
    }
    // Validate on click and say what is missing, rather than a disabled Apply.
    apply() {
      if draftStart == "" {
        problem = t("Pick a start date.")
        return
      }
      if draftEnd == "" {
        problem = t("Pick an end date.")
        return
      }
      if drpToDay(draftEnd) < drpToDay(draftStart) {
        problem = t("The end is before the start.")
        return
      }
      problem = ""
      picking = false
      suggested = false
      if draftStart == start && draftEnd == end {
        // Nothing changed, so no prop will flow back to close on.
        cancel()
        return
      }
      pendingClose = true
      emit("change", { start: draftStart, end: draftEnd })
    }
    closeAfterApply() {
      if pendingClose {
        pendingClose = false
        open = false
        hover = ""
        refocusTrigger = true
      }
    }
    // A typed date counts once it is a whole, real date in `format`.
    typeStart(v) {
      startText = v
      if v.length != format.length { return }
      let iso = toISODate(v, format)
      if iso == "" { return }
      problem = ""
      // A typed start BEGINS a range, exactly as a clicked one does: the end is
      // suggested (or awaited) and stays tentative until Apply or a second
      // pick. The one end it keeps is one the user typed or picked in THIS
      // session that still follows the new start.
      //
      // 0.1.1 kept whatever end the draft held — which, on opening, is the
      // range already applied. Typing Mar 17 over an applied Aug 16 – 29
      // therefore kept Aug 29, Apply refused "The end is before the start",
      // and nothing reached the page (Vector e2e PPR3). It also left `picking`
      // false, so a suggestion read as a confirmed range (PPR2).
      if endTouched && draftEnd != "" && drpToDay(draftEnd) >= drpToDay(iso) {
        draftStart = iso
        picking = false
        suggested = false
      } else {
        let se = drpSuggestEnd(iso, periodDays, bands)
        draftStart = iso
        draftEnd = se
        suggested = se != ""
        picking = true
        endText = se != "" ? isoToOutput(se, format) : ""
      }
      let nv = drpViewFor(iso, draftEnd, todayIso, months)
      viewYear = nv.year
      viewMonth = nv.month
      focusIso = iso
    }
    typeEnd(v) {
      endText = v
      if v.length != format.length { return }
      let iso = toISODate(v, format)
      if iso == "" { return }
      draftEnd = iso
      suggested = false
      picking = false
      endTouched = true
      problem = ""
    }
    // Escape closes the popover and is CONSUMED — stopPropagation too, since a
    // Modal's dismiss listener ignores defaultPrevented (see DatePicker). With
    // the popover closed the key travels on to whatever holds this field.
    escapeKey(event) {
      if open {
        event.preventDefault()
        event.stopPropagation()
        cancel()
      }
    }
  }

  block {
    layout: vertical, gap: spacing.1
    position: relative

    on key-down(event): {
      if event.key == "Escape" {
        escapeKey(event)
      }
    }

    block {
      visibility: label != ""
      text(label) { style: type.label-sm, color: semantic.text-secondary }
    }

    // Trigger — styled to match DatePicker's field.
    button {
      aria-label: triggerName
      aria-haspopup: "dialog"
      aria-expanded: open
      layout: horizontal, align: center, gap: spacing.2
      min-height: 36px
      padding: spacing.2
      background: match error {
        true -> semantic.destructive-bg,
        _ -> token.input-bg
      }
      border: match error {
        true -> token.input-borderWidth + " solid " + semantic.destructive,
        _ -> token.input-borderWidth + " solid " + token.input-border
      }
      border-radius: token.input-radius
      cursor: disabled ? "default" : "pointer"
      opacity: disabled ? 0.5 : 1
      focus: refocusTrigger
      on click: toggle()
      text("📅") { style: type.body-md, color: semantic.text-tertiary }
      text(triggerText) {
        style: type.body-sm, weight: 600, text-align: start
        color: hasValue ? semantic.text-primary : semantic.text-tertiary
      }
      text(triggerMeta) {
        visibility: triggerMeta != ""
        style: type.caption, color: semantic.text-tertiary
      }
    }

    // Popover — anchor:'bottom' positions it (position: fixed, viewport-
    // clamped) under the trigger, its previous sibling; z-index as DatePicker.
    block {
      visibility: open
      anchor: 'bottom'
      z-index: 1000
      width: popWidth
      max-width: "calc(100vw - 32px)"
      background: semantic.surface
      border: borders.default
      border-radius: radius.md
      shadow: elevation.floating
      layout: horizontal
      role: "dialog"
      aria-label: "Choose a date range"

      // Presets — a rail on the left when there is room.
      block {
        visibility: wide && hasPresets
        width: 180px
        min-width: 180px
        layout: vertical, gap: spacing.1
        padding: spacing.2
        border-right: borders.default
        role: "group"
        aria-label: "Quick ranges"
        each presets as p {
          button {
            width: 100%
            border: "none"
            background: drpSame(draftStart, draftEnd, p.start, p.end) ? semantic.interactive-bg : "transparent"
            layout: vertical, gap: 2px
            padding: spacing.2
            border-radius: radius.sm
            cursor: "pointer"
            on hover { background: semantic.surface-raised }
            on click: applyPreset(p.start, p.end)
            text(p.label) { style: type.body-sm, weight: 600, color: semantic.text-primary, text-align: start }
            text(drpLabel(p.start, p.end)) { style: type.caption, color: semantic.text-tertiary, text-align: start }
          }
        }
      }

      block {
        grow: true
        min-width: 0
        layout: vertical

        // Presets — a chip row on a phone.
        block {
          visibility: wide == false && hasPresets
          layout: horizontal, gap: spacing.1, wrap
          padding: spacing.2
          border-bottom: borders.default
          role: "group"
          aria-label: "Quick ranges"
          each presets as p {
            button {
              border: borders.default
              background: drpSame(draftStart, draftEnd, p.start, p.end) ? semantic.interactive-bg : "transparent"
              padding: spacing.1
              border-radius: radius.sm
              cursor: "pointer"
              on click: applyPreset(p.start, p.end)
              text(p.label) { style: type.caption, weight: 600, color: semantic.text-primary }
            }
          }
        }

        // The months. Hovering previews an end only while picking one.
        block {
          layout: horizontal, gap: spacing.4, align: start
          padding: spacing.2
          on mouse-leave: clearHover()

          // ── Left month ──────────────────────────────────────────────────
          block {
            grow: true
            min-width: 0
            layout: vertical, gap: spacing.1

            block {
              layout: horizontal, justify: between, align: center
              button {
                border: "none"
                background: "transparent"
                aria-label: "Previous month"
                cursor: "pointer"
                padding: spacing.2
                on click: prevMonth()
                text("◀") { style: type.body-md, color: semantic.interactive }
              }
              text(leftTitle) { style: type.body-md, weight: 600, color: semantic.text-primary }
              button {
                visibility: wide == false
                border: "none"
                background: "transparent"
                aria-label: "Next month"
                cursor: "pointer"
                padding: spacing.2
                on click: nextMonth()
                text("▶") { style: type.body-md, color: semantic.interactive }
              }
              block {
                visibility: wide
                width: 32px
              }
            }

            block {
              layout: grid, columns: "repeat(7, 1fr)"
              each weekdays as w {
                text(w) { style: type.caption, color: semantic.text-tertiary, text-align: center }
              }
            }

            block {
              layout: grid, columns: "repeat(7, 1fr)"
              role: "group"
              aria-label: leftTitle
              on key-down(event): {
                match event.key {
                  "ArrowLeft" -> moveFocus("ArrowLeft"),
                  "ArrowRight" -> moveFocus("ArrowRight"),
                  "ArrowUp" -> moveFocus("ArrowUp"),
                  "ArrowDown" -> moveFocus("ArrowDown"),
                  "Home" -> moveFocus("Home"),
                  "End" -> moveFocus("End"),
                  "PageUp" -> moveFocus("PageUp"),
                  "PageDown" -> moveFocus("PageDown"),
                  _ -> {}
                }
              }
              // Keyed, so a day's button survives a hover or pick and keeps
              // keyboard focus; see RangeCell.key.
              each leftCells as cell (cell.key) {
                block {
                  layout: horizontal, justify: center, align: center
                  min-height: 38px
                  background: drpIn(cell.iso, span) && cell.iso != span.lo && cell.iso != span.hi ? semantic.interactive-bg : "transparent"
                  border-bottom: cell.bandParity == 0 ? "3px solid " + semantic.border-strong : (cell.bandParity == 1 ? "3px solid " + semantic.border : "3px solid transparent")
                  button {
                    visibility: cell.blank == false
                    width: 34px
                    min-height: 32px
                    border-radius: radius.sm
                    cursor: "pointer"
                    aria-label: drpCellLabel(cell.iso, span, todayIso)
                    border: cell.iso == span.hi && span.tentative && cell.iso != span.lo ? "2px dashed " + semantic.interactive : "2px solid transparent"
                    background: drpIn(cell.iso, span) && (cell.iso == span.lo || (cell.iso == span.hi && span.tentative == false)) ? semantic.interactive : "transparent"
                    tabindex: cell.iso == focusIso ? "0" : "-1"
                    focus: cell.iso == focusIso && open
                    on hover { background: drpIn(cell.iso, span) && (cell.iso == span.lo || (cell.iso == span.hi && span.tentative == false)) ? semantic.interactive-hover : semantic.surface-raised }
                    on mouse-enter: hoverDay(cell.iso)
                    on click: pickDay(cell.iso)
                    text(cell.day + "") {
                      style: type.body-sm
                      weight: cell.today ? 700 : 400
                      color: drpIn(cell.iso, span) && (cell.iso == span.lo || (cell.iso == span.hi && span.tentative == false)) ? semantic.surface : semantic.text-primary
                    }
                  }
                }
              }
            }
          }

          // ── Right month (wide only) ─────────────────────────────────────
          block {
            visibility: wide
            grow: true
            min-width: 0
            layout: vertical, gap: spacing.1

            block {
              layout: horizontal, justify: between, align: center
              block { width: 32px }
              text(rightTitle) { style: type.body-md, weight: 600, color: semantic.text-primary }
              button {
                border: "none"
                background: "transparent"
                aria-label: "Next month"
                cursor: "pointer"
                padding: spacing.2
                on click: nextMonth()
                text("▶") { style: type.body-md, color: semantic.interactive }
              }
            }

            block {
              layout: grid, columns: "repeat(7, 1fr)"
              each weekdays as w {
                text(w) { style: type.caption, color: semantic.text-tertiary, text-align: center }
              }
            }

            block {
              layout: grid, columns: "repeat(7, 1fr)"
              role: "group"
              aria-label: rightTitle
              on key-down(event): {
                match event.key {
                  "ArrowLeft" -> moveFocus("ArrowLeft"),
                  "ArrowRight" -> moveFocus("ArrowRight"),
                  "ArrowUp" -> moveFocus("ArrowUp"),
                  "ArrowDown" -> moveFocus("ArrowDown"),
                  "Home" -> moveFocus("Home"),
                  "End" -> moveFocus("End"),
                  "PageUp" -> moveFocus("PageUp"),
                  "PageDown" -> moveFocus("PageDown"),
                  _ -> {}
                }
              }
              each rightCells as cell (cell.key) {
                block {
                  layout: horizontal, justify: center, align: center
                  min-height: 38px
                  background: drpIn(cell.iso, span) && cell.iso != span.lo && cell.iso != span.hi ? semantic.interactive-bg : "transparent"
                  border-bottom: cell.bandParity == 0 ? "3px solid " + semantic.border-strong : (cell.bandParity == 1 ? "3px solid " + semantic.border : "3px solid transparent")
                  button {
                    visibility: cell.blank == false
                    width: 34px
                    min-height: 32px
                    border-radius: radius.sm
                    cursor: "pointer"
                    aria-label: drpCellLabel(cell.iso, span, todayIso)
                    border: cell.iso == span.hi && span.tentative && cell.iso != span.lo ? "2px dashed " + semantic.interactive : "2px solid transparent"
                    background: drpIn(cell.iso, span) && (cell.iso == span.lo || (cell.iso == span.hi && span.tentative == false)) ? semantic.interactive : "transparent"
                    tabindex: cell.iso == focusIso ? "0" : "-1"
                    focus: cell.iso == focusIso && open
                    on hover { background: drpIn(cell.iso, span) && (cell.iso == span.lo || (cell.iso == span.hi && span.tentative == false)) ? semantic.interactive-hover : semantic.surface-raised }
                    on mouse-enter: hoverDay(cell.iso)
                    on click: pickDay(cell.iso)
                    text(cell.day + "") {
                      style: type.body-sm
                      weight: cell.today ? 700 : 400
                      color: drpIn(cell.iso, span) && (cell.iso == span.lo || (cell.iso == span.hi && span.tentative == false)) ? semantic.surface : semantic.text-primary
                    }
                  }
                }
              }
            }
          }
        }

        // ── Footer ───────────────────────────────────────────────────────
        block {
          layout: vertical, gap: spacing.2
          padding: spacing.2
          border-top: borders.default

          block {
            visibility: showBandsKey
            layout: horizontal, gap: spacing.2, align: center
            block {
              width: 22px
              height: 3px
              background: semantic.border-strong
              border-radius: 2px
            }
            text(bandsLabel) { style: type.caption, color: semantic.text-tertiary }
          }

          // The same words a screen reader hears after each step.
          block {
            aria-live: "polite"
            text(prompt) { style: type.body-sm, color: semantic.text-secondary }
          }

          block {
            layout: horizontal, gap: spacing.2, align: end, wrap

            block {
              layout: vertical, gap: 2px
              text("Start") { style: type.caption, color: semantic.text-tertiary }
              block {
                width: 124px
                padding: spacing.1
                border: token.input-borderWidth + " solid " + token.input-border
                border-radius: token.input-radius
                background: token.input-bg
                textInput(startText) {
                  border: 'none'
                  background: 'transparent'
                  width: 100%
                  placeholder: format
                  aria-label: "Start date"
                  on input: typeStart(startText)
                }
              }
            }
            block {
              layout: vertical, gap: 2px
              text("Through") { style: type.caption, color: semantic.text-tertiary }
              block {
                width: 124px
                padding: spacing.1
                border: token.input-borderWidth + " solid " + token.input-border
                border-radius: token.input-radius
                background: token.input-bg
                textInput(endText) {
                  border: 'none'
                  background: 'transparent'
                  width: 100%
                  placeholder: format
                  aria-label: "End date"
                  on input: typeEnd(endText)
                }
              }
            }

            block { grow: true }

            button {
              border: borders.default
              background: "transparent"
              padding: spacing.2
              border-radius: radius.sm
              cursor: "pointer"
              on click: cancel()
              text("Cancel") { style: type.label-sm, color: semantic.text-primary }
            }
            button {
              border: "none"
              background: semantic.interactive
              padding: spacing.2
              border-radius: radius.sm
              cursor: "pointer"
              on hover { background: semantic.interactive-hover }
              on click: apply()
              text("Apply") { style: type.label-sm, weight: 600, color: semantic.surface }
            }
          }

          block {
            visibility: problem != ""
            role: "alert"
            text(problem) { style: type.caption, color: semantic.destructive }
          }
        }
      }
    }

    // Click-outside dismiss, below the popover (999 < 1000) — as DatePicker.
    // tabindex -1 keeps this invisible full-screen block out of the tab order.
    block {
      visibility: open
      position: fixed
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 999
      tabindex: "-1"
      on click: cancel()
    }

    block {
      visibility: error == true
      text(errorMessage) { style: type.caption, color: semantic.destructive }
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// drp* — the date math behind DateRangePicker, as portable fns.
//
// ISO 'YYYY-MM-DD' strings in and out, integer epoch-day math (whole days since
// 1970-01-01) with no Date, so no timezone can move a date and every target
// computes the same answer. `month` is 0-based (0 = January), the convention
// DatePicker's viewMonth uses. Weeks start on Sunday, as DatePicker's grid
// does. Names, word order and prose come from calendar*() / fillPattern() /
// t() / plural(), so a locale build reads in its own language.
//
// Three rules carry the weight, and each has a test
// (date-range-picker-fns.test.ts):
//
//   • A range includes BOTH ends. A 14-day period that starts Sep 13 ends
//     Sep 26 — start + 13. Start + 14 is day one of the next period.
//   • Picking is click-click on one calendar: the first click is the start,
//     the second (on or after it) the end; a click BEFORE the start restarts
//     there; the same day twice is a one-day range.
//   • A suggested end (from `periodDays`, or the band the start falls in) is
//     TENTATIVE: shown, but confirmed only by a second click or Apply.
//
// Shapes:
//   band   { start, end } — a marked span drawn as a ruler under the weeks.
//   cell   { key, iso, day, blank, inRange, isStart, isEnd, tentative, today,
//            bandParity, bandStart, bandEnd, label } — `key` is the ISO date
//            or 'blank-N', stable within one month, so the component's keyed
//            `each` keeps a day's button (and its keyboard focus) across a
//            re-render. `tentative` marks a suggested end or a hover preview;
//            `bandParity` is 0 / 1 alternating per band, -1 outside any band.
//   pick   { start, end, picking, suggested }
//   view   { year, month }
//   span   { lo, hi, tentative, awaitingEnd }
// ═══════════════════════════════════════════════════════════════════════════

// Epoch day for a civil date (m is 1-based) — Hinnant's days_from_civil.
fn drpCivilToDay(y: number, m: number, d: number) -> number {
  let yy = m <= 2 ? y - 1 : y
  let era = floor(yy / 400)
  let yoe = yy - era * 400
  let mp = m > 2 ? m - 3 : m + 9
  let doy = floor((153 * mp + 2) / 5) + d - 1
  let doe = yoe * 365 + floor(yoe / 4) - floor(yoe / 100) + doy
  return era * 146097 + doe - 719468
}

// Civil date { y, m (1-based), d } for an epoch day — Hinnant's civil_from_days.
fn drpDayToCivil(z: number) -> map {
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

// 0 = Sunday. Epoch day 0 (1970-01-01) was a Thursday.
fn drpDow(z: number) -> number {
  return (((z % 7) + 7) % 7 + 4) % 7
}

// month0 is 0-based, as everywhere in this component.
fn drpDaysIn(year: number, month0: number) -> number {
  let next = drpShiftView(year, month0, 1)
  return drpCivilToDay(next.year, next.month + 1, 1) - drpCivilToDay(year, month0 + 1, 1)
}

// Epoch day for a REAL calendar date, or null ('2026-02-30' → null).
fn drpToDay(iso: any) -> any {
  if typeOf(iso) != 'string' { return null }
  if regexTest(iso, '^\d{4}-\d{2}-\d{2}$') == false { return null }
  let y = parseInt(slice(iso, 0, 4), 10)
  let m = parseInt(slice(iso, 5, 7), 10)
  let d = parseInt(slice(iso, 8, 10), 10)
  if m < 1 || m > 12 || d < 1 { return null }
  if d > drpDaysIn(y, m - 1) { return null }
  return drpCivilToDay(y, m, d)
}

fn drpFromDay(z: number) -> string {
  let c = drpDayToCivil(z)
  return padStart("{c.y}", 4, '0') + '-' + padStart("{c.m}", 2, '0') + '-' + padStart("{c.d}", 2, '0')
}

fn drpAddDays(iso: any, n: number) -> string {
  let z = drpToDay(iso)
  if z == null { return '' }
  return drpFromDay(z + n)
}

// Days in a range, BOTH ends counted; 0 when either end is missing or it runs backwards.
fn drpDays(start: any, end: any) -> number {
  let a = drpToDay(start)
  let b = drpToDay(end)
  if a == null || b == null { return 0 }
  if b < a { return 0 }
  return b - a + 1
}

// 'Aug 30 – Sep 12, 2026' · 'Sep 13 – 26, 2026' · 'Dec 27, 2026 – Jan 9, 2027' · 'Sep 13, 2026'.
fn drpLabel(start: any, end: any) -> string {
  let a = drpToDay(start)
  let b = drpToDay(end)
  if a == null || b == null { return '' }
  let ca = drpDayToCivil(a)
  let cb = drpDayToCivil(b)
  let short = calendarMonths('short')
  let ma = short[ca.m - 1]
  let mb = short[cb.m - 1]
  if a == b {
    return fillPattern(calendarPattern('monthDayYear'), { mon: ma, d: ca.d, y: ca.y })
  }
  if ca.y != cb.y {
    return fillPattern(calendarPattern('monthDayYear'), { mon: ma, d: ca.d, y: ca.y }) + ' – ' + fillPattern(calendarPattern('monthDayYear'), { mon: mb, d: cb.d, y: cb.y })
  }
  if ca.m == cb.m {
    return fillPattern(calendarPattern('rangeSameMonth'), { mon: ma, d1: ca.d, d2: cb.d, y: ca.y })
  }
  return fillPattern(calendarPattern('rangeSameYear'), { mon1: ma, d1: ca.d, mon2: mb, d2: cb.d, y: cb.y })
}

// 'Sunday, September 13, 2026'.
fn drpLongDate(iso: any) -> string {
  let z = drpToDay(iso)
  if z == null { return '' }
  let c = drpDayToCivil(z)
  return fillPattern(calendarPattern('fullDate'), { weekday: calendarWeekdays('long')[drpDow(z)], month: calendarMonths('long')[c.m - 1], d: c.d, y: c.y })
}

fn drpMonthTitle(year: number, month: number) -> string {
  let v = drpShiftView(year, month, 0)
  return fillPattern(calendarPattern('monthYear'), { month: calendarMonths('long')[v.month], y: v.year })
}

// Index of the band holding epoch day z, or -1.
fn drpBandIndexOf(z: number, bands: any) -> number {
  if isList(bands) == false { return -1 }
  for b, i in bands {
    let s = drpToDay(b?.start)
    let e = drpToDay(b?.end)
    if s != null && e != null && s <= z && z <= e { return i }
  }
  return -1
}

// The end to fill in once a start is picked: a whole `periodDays` after it
// (start + periodDays − 1, since both ends count), else the end of the band the
// start falls in, else '' — no suggestion.
fn drpSuggestEnd(start: any, periodDays: any, bands: any) -> string {
  let z = drpToDay(start)
  if z == null { return '' }
  if typeOf(periodDays) == 'number' && periodDays > 0 {
    return drpFromDay(z + floor(periodDays) - 1)
  }
  let i = drpBandIndexOf(z, bands)
  if i < 0 { return '' }
  return bands[i].end
}

// One click on `day`. Returns the next selection state.
fn drpPick(start: any, end: any, picking: boolean, day: any, periodDays: any, bands: any) -> map {
  let zd = drpToDay(day)
  if zd == null {
    return { start: start, end: end, picking: picking, suggested: false }
  }
  let zs = drpToDay(start)
  if picking && zs != null && zd >= zs {
    return { start: start, end: day, picking: false, suggested: false }
  }
  let suggestedEnd = drpSuggestEnd(day, periodDays, bands)
  return { start: day, end: suggestedEnd, picking: true, suggested: suggestedEnd != '' }
}

// A padding cell outside the month.
fn drpBlankCell(i: number) -> map {
  return { key: "blank-{i}", iso: '', day: 0, blank: true, inRange: false, isStart: false, isEnd: false, tentative: false, today: false, bandParity: -1, bandStart: false, bandEnd: false, label: '' }
}

// The cells of one month, Sunday-first, padded with blanks to whole weeks.
//
// While `picking` with a `hover` on or after the start, the hover previews the
// end; otherwise the start..end on record is drawn, tentative when `suggested`.
fn drpMonthCells(year: number, month: number, start: any, end: any, hover: any, picking: boolean, suggested: boolean, bands: any, today: any) -> list {
  let v = drpShiftView(year, month, 0)
  let first = drpCivilToDay(v.year, v.month + 1, 1)
  let count = drpDaysIn(v.year, v.month)
  let zs = drpToDay(start)
  let ze = drpToDay(end)
  let zh = drpToDay(hover)
  let zt = drpToDay(today)

  let lo = null
  let hi = null
  let tentative = false
  if picking && zs != null && zh != null && zh >= zs {
    lo = zs
    hi = zh
    tentative = true
  } else if zs != null && ze != null && ze >= zs {
    lo = zs
    hi = ze
    tentative = suggested
  } else if zs != null {
    lo = zs
    hi = zs
  }

  let cells = []
  for i in range(0, drpDow(first)) {
    push(cells, drpBlankCell(length(cells)))
  }
  for d in range(1, count + 1) {
    let z = first + d - 1
    let iso = drpFromDay(z)
    let inRange = lo != null && hi != null && z >= lo && z <= hi
    let isStart = lo != null && z == lo
    let isEnd = hi != null && z == hi && inRange
    let bi = drpBandIndexOf(z, bands)
    let band = bi >= 0 ? bands[bi] : null
    let label = drpLongDate(iso)
    if z == zt {
      label = t("{label}, today")
    }
    // A start still waiting for its end is drawn as a one-day span, but it is
    // not a one-day RANGE yet — announce it as the start.
    let awaitingEnd = picking && ze == null
    if isStart && isEnd && !awaitingEnd {
      label = t("{label}, selected")
    } else if isStart {
      label = t("{label}, start")
    } else if isEnd {
      label = tentative ? t("{label}, suggested end") : t("{label}, end")
    } else if inRange {
      label = t("{label}, in range")
    }
    push(cells, { key: iso, iso: iso, day: d, blank: false, inRange: inRange, isStart: isStart, isEnd: isEnd, tentative: inRange && tentative, today: z == zt, bandParity: bi < 0 ? -1 : bi % 2, bandStart: band != null && band.start == iso, bandEnd: band != null && band.end == iso, label: label })
  }
  let trailing = (7 - length(cells) % 7) % 7
  for i in range(0, trailing) {
    push(cells, drpBlankCell(length(cells)))
  }
  return cells
}

// ── The same picture, split for rendering ─────────────────────────────────
//
// drpMonthCells answers everything about a cell at once, which makes the LIST
// change on every hover and pick — and a list that changes is re-rendered, so
// the day button holding keyboard focus was destroyed on each arrow key. The
// component therefore renders drpMonthGrid (which changes only with the month,
// the bands and today) and asks drpSpan / drpIn / drpCellLabel per cell. The
// parity test holds the split to drpMonthCells exactly.

// A month's cells, carrying only what does NOT change while a range is picked.
fn drpMonthGrid(year: number, month: number, bands: any, today: any) -> list {
  let out = []
  for c in drpMonthCells(year, month, '', '', '', false, false, bands, today) {
    push(out, { key: c.key, iso: c.iso, day: c.day, blank: c.blank, today: c.today, bandParity: c.bandParity, bandStart: c.bandStart, bandEnd: c.bandEnd })
  }
  return out
}

// What to draw for the current selection — the rules drpMonthCells applies, once.
// Each cell compares its own epoch day to lo / hi (drpIn).
fn drpSpan(start: any, end: any, hover: any, picking: boolean, suggested: boolean) -> map {
  let zs = drpToDay(start)
  let ze = drpToDay(end)
  let zh = drpToDay(hover)
  let awaitingEnd = picking && ze == null
  if picking && zs != null && zh != null && zh >= zs {
    return { lo: start, hi: hover, tentative: true, awaitingEnd: awaitingEnd }
  }
  if zs != null && ze != null && ze >= zs {
    return { lo: start, hi: end, tentative: suggested, awaitingEnd: awaitingEnd }
  }
  if zs != null {
    return { lo: start, hi: start, tentative: false, awaitingEnd: awaitingEnd }
  }
  return { lo: '', hi: '', tentative: false, awaitingEnd: false }
}

// Is a cell's ISO date inside the span? False for a blank cell or an empty span.
fn drpIn(iso: any, span: any) -> boolean {
  if typeOf(iso) != 'string' || iso == '' { return false }
  if typeOf(span) != 'map' { return false }
  if typeOf(span.lo) != 'string' || span.lo == '' { return false }
  // Epoch days, not the strings. ISO dates do sort as strings, but only in
  // JavaScript: the Swift emitter lowers `>=` to specNum on each side, and
  // specNum('2026-09-13') is NaN — so no day was ever in range on iOS.
  let z = drpToDay(iso)
  let lo = drpToDay(span.lo)
  let hi = drpToDay(span.hi)
  if z == null || lo == null || hi == null { return false }
  return z >= lo && z <= hi
}

// A cell's whole accessible name, exactly as drpMonthCells builds it.
fn drpCellLabel(iso: any, span: any, today: any) -> string {
  if typeOf(iso) != 'string' || iso == '' { return '' }
  let label = drpLongDate(iso)
  if iso == today {
    label = t("{label}, today")
  }
  let inRange = drpIn(iso, span)
  let isStart = inRange && iso == span.lo
  let isEnd = inRange && iso == span.hi
  if isStart && isEnd && !span.awaitingEnd {
    label = t("{label}, selected")
  } else if isStart {
    label = t("{label}, start")
  } else if isEnd {
    label = span.tentative ? t("{label}, suggested end") : t("{label}, end")
  } else if inRange {
    label = t("{label}, in range")
  }
  return label
}

// Normalized {year, month} after moving `n` months.
fn drpShiftView(year: number, month: number, n: number) -> map {
  let total = year * 12 + month + n
  let y = floor(total / 12)
  return { year: y, month: total - y * 12 }
}

// Which month opens on the LEFT of `months` visible months (1 on a phone, 2
// otherwise). `months` is REQUIRED: a fn has no default parameters, and while a
// 3-argument call happens to work in JavaScript (undefined <= 1 is false), the
// Swift build rejects it.
//
//   • One month: the start's month (today's with no start). 0.1.2 used the
//     two-month rule here too, so a phone showed an empty July for an August
//     range — the range off screen and focus on a day that was not there.
//   • Two months, a range spanning months: the start's month.
//   • Two months, a range inside one month (or no range): that month on the
//     left and the next on the right — unless it is TODAY's month, which goes
//     on the right so last month shows beside it (reports look back).
fn drpViewFor(start: any, end: any, today: any, months: any) -> map {
  let zs = drpToDay(start)
  let ze = drpToDay(end)
  let zt = drpToDay(today)
  let anchor = zs ?? zt ?? 0
  let a = drpDayToCivil(anchor)
  if months <= 1 {
    return drpShiftView(a.y, a.m - 1, 0)
  }
  let b = drpDayToCivil(ze ?? anchor)
  let sameMonth = a.y == b.y && a.m == b.m
  if !sameMonth {
    return drpShiftView(a.y, a.m - 1, 0)
  }
  let tc = drpDayToCivil(zt ?? anchor)
  let todaysMonth = tc.y == a.y && tc.m == a.m
  return drpShiftView(a.y, a.m - 1, todaysMonth ? -1 : 0)
}

// Is `iso` in one of the `months` months shown from {year, month}?
fn drpInView(iso: any, year: number, month: number, months: number) -> boolean {
  let z = drpToDay(iso)
  if z == null { return false }
  let v = drpShiftView(year, month, 0)
  let lo = drpCivilToDay(v.year, v.month + 1, 1)
  let after = drpShiftView(v.year, v.month, max(1, months))
  let hi = drpCivilToDay(after.year, after.month + 1, 1) - 1
  return z >= lo && z <= hi
}

// Keyboard focus movement in the grid, per the APG date-picker grid: arrows
// by day / week, Home / End to the week's ends, PageUp / PageDown by month with
// the day clamped to the target month. Any other key returns the date unchanged.
fn drpMoveFocus(iso: any, key: string) -> string {
  let z = drpToDay(iso)
  if z == null { return iso }
  if key == 'ArrowLeft' { return drpFromDay(z - 1) }
  if key == 'ArrowRight' { return drpFromDay(z + 1) }
  if key == 'ArrowUp' { return drpFromDay(z - 7) }
  if key == 'ArrowDown' { return drpFromDay(z + 7) }
  if key == 'Home' { return drpFromDay(z - drpDow(z)) }
  if key == 'End' { return drpFromDay(z + (6 - drpDow(z))) }
  if key == 'PageUp' || key == 'PageDown' {
    let c = drpDayToCivil(z)
    let v = drpShiftView(c.y, c.m - 1, key == 'PageUp' ? -1 : 1)
    let day = min(c.d, drpDaysIn(v.year, v.month))
    return drpFromDay(drpCivilToDay(v.year, v.month + 1, day))
  }
  return iso
}

// What a screen reader hears after each step — and what the footer says.
fn drpPrompt(start: any, end: any, picking: boolean, suggested: boolean) -> string {
  if drpToDay(start) == null {
    return t("Pick a start date.")
  }
  let startDate = drpLongDate(start)
  if picking && suggested && drpToDay(end) != null {
    let endDate = drpLongDate(end)
    return t("Start {startDate}. End suggested: {endDate}. Pick another day to change it, or Apply.")
  }
  if picking {
    return t("Start {startDate}. Now pick the end date.")
  }
  let n = drpDays(start, end)
  if n == 0 {
    return t("Pick an end date.")
  }
  let rangeLabel = drpLabel(start, end)
  return plural(n, one: "{rangeLabel} — {n} day.", other: "{rangeLabel} — {n} days.")
}

// Do two ranges name exactly the same days?
fn drpSame(aStart: any, aEnd: any, bStart: any, bEnd: any) -> boolean {
  return drpToDay(aStart) != null && aStart == bStart && aEnd == bEnd
}
