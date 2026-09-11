@extern { drpMonthCells, drpPick, drpViewFor, drpShiftView, drpMonthTitle, drpMoveFocus, drpInView, drpLabel, drpDays, drpPrompt, drpSame, drpSuggestEnd } from "@spec/components/date-range-utils.js"
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
// Interaction (date-range-utils.ts holds every rule, tested there):
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
                          label: string = "",
                          placeholder: string = "Pick dates",
                          disabled: boolean = false,
                          error: boolean = false,
                          errorMessage: string = "") {
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
    leftCells: drpMonthCells(viewYear, viewMonth, draftStart, draftEnd, hover, picking, suggested, bands, todayIso)
    rightCells: drpMonthCells(rightView.year, rightView.month, draftStart, draftEnd, hover, picking, suggested, bands, todayIso)
    leftTitle: drpMonthTitle(viewYear, viewMonth)
    rightTitle: drpMonthTitle(rightView.year, rightView.month)
    hasValue: start != "" && end != ""
    triggerText: hasValue ? drpLabel(start, end) : placeholder
    valueDays: drpDays(start, end)
    triggerMeta: valueDays == 0 ? "" : (valueDays == 1 ? "1 day" : valueDays + " days")
    triggerName: (label != "" ? label : "Date range") + ": " + triggerText
    prompt: drpPrompt(draftStart, draftEnd, picking, suggested)
    hasPresets: presets.length > 0
    showBandsKey: bands.length > 0 && bandsLabel != ""
    popWidth: wide ? (hasPresets ? "780px" : "600px") : "320px"
    weekdays: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
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
      hover = ""
      problem = ""
      pendingClose = false
      let v = drpViewFor(start, end, todayIso)
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
        if next < from {
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
        problem = "Pick a start date."
        return
      }
      if draftEnd == "" {
        problem = "Pick an end date."
        return
      }
      if draftEnd < draftStart {
        problem = "The end is before the start."
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
      draftStart = iso
      problem = ""
      if draftEnd == "" || suggested {
        let se = drpSuggestEnd(iso, periodDays, bands)
        if se != "" {
          draftEnd = se
          suggested = true
          endText = isoToOutput(se, format)
        }
      }
      let nv = drpViewFor(iso, draftEnd, todayIso)
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
              each leftCells as cell {
                block {
                  layout: horizontal, justify: center, align: center
                  min-height: 38px
                  background: cell.inRange && cell.isStart == false && cell.isEnd == false ? semantic.interactive-bg : "transparent"
                  border-bottom: cell.bandParity == 0 ? "3px solid " + semantic.border-strong : (cell.bandParity == 1 ? "3px solid " + semantic.border : "3px solid transparent")
                  button {
                    visibility: cell.blank == false
                    width: 34px
                    min-height: 32px
                    border-radius: radius.sm
                    cursor: "pointer"
                    aria-label: cell.label
                    border: cell.isEnd && cell.tentative && cell.isStart == false ? "2px dashed " + semantic.interactive : "2px solid transparent"
                    background: cell.isStart || (cell.isEnd && cell.tentative == false) ? semantic.interactive : "transparent"
                    tabindex: cell.iso == focusIso ? "0" : "-1"
                    focus: cell.iso == focusIso && open
                    on hover { background: cell.isStart || (cell.isEnd && cell.tentative == false) ? semantic.interactive-hover : semantic.surface-raised }
                    on mouse-enter: hoverDay(cell.iso)
                    on click: pickDay(cell.iso)
                    text(cell.day + "") {
                      style: type.body-sm
                      weight: cell.today ? 700 : 400
                      color: cell.isStart || (cell.isEnd && cell.tentative == false) ? semantic.surface : semantic.text-primary
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
              each rightCells as cell {
                block {
                  layout: horizontal, justify: center, align: center
                  min-height: 38px
                  background: cell.inRange && cell.isStart == false && cell.isEnd == false ? semantic.interactive-bg : "transparent"
                  border-bottom: cell.bandParity == 0 ? "3px solid " + semantic.border-strong : (cell.bandParity == 1 ? "3px solid " + semantic.border : "3px solid transparent")
                  button {
                    visibility: cell.blank == false
                    width: 34px
                    min-height: 32px
                    border-radius: radius.sm
                    cursor: "pointer"
                    aria-label: cell.label
                    border: cell.isEnd && cell.tentative && cell.isStart == false ? "2px dashed " + semantic.interactive : "2px solid transparent"
                    background: cell.isStart || (cell.isEnd && cell.tentative == false) ? semantic.interactive : "transparent"
                    tabindex: cell.iso == focusIso ? "0" : "-1"
                    focus: cell.iso == focusIso && open
                    on hover { background: cell.isStart || (cell.isEnd && cell.tentative == false) ? semantic.interactive-hover : semantic.surface-raised }
                    on mouse-enter: hoverDay(cell.iso)
                    on click: pickDay(cell.iso)
                    text(cell.day + "") {
                      style: type.body-sm
                      weight: cell.today ? 700 : 400
                      color: cell.isStart || (cell.isEnd && cell.tentative == false) ? semantic.surface : semantic.text-primary
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
