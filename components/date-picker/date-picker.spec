@extern { calendarGrid, todayStr, parseDateInput, daysInMonth, todayParts, formatDateOutput, formatSegments, formatSeparator, toISODate } from "@spec/components/date-utils.js"

component DatePicker(value: string = "", label: string = "", placeholder: string = "",
                     disabled: boolean = false, format: string = "MM/DD/YYYY",
                     error: boolean = false, errorMessage: string = "") {
  @state {
    open: false
    viewYear: 2026
    viewMonth: 2
    focusedDay: 1
    focused: false
    focusTrigger: false
    activeSegment: -1
    segMonth: 1
    segDay: 1
    segYear: 2026
    editing: false
    // True once the user actually changes a segment in the current edit session.
    // Until then an empty field keeps showing the MM/DD/YYYY mask instead of the
    // today-prefill in segMonth/Day/Year, so a field the user merely focused (but
    // never edited) reads as empty — not a misleading "today" that was never
    // committed to `value`.
    dirty: false
    digitBuffer: ""
    popupView: 0
    yearGridStart: 2020
  }

  @computed {
    valueISO: value != "" ? toISODate(value, format) : ""
    displayValue: value != "" ? value : ""
    placeholderText: placeholder != "" ? placeholder : format
    daysInCurrentMonth: daysInMonth(viewYear, viewMonth)
    monthNames: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    calendarCells: calendarGrid(viewYear, viewMonth)
    segments: formatSegments(format)
    sep: formatSeparator(format)
    parts: value != "" ? parseDateInput(value, format) : null
    showMask: value == "" && (editing == false || dirty == false)
    dMonth: editing == true ? segMonth : (parts != null ? parts.month + 1 : 1)
    dDay: editing == true ? segDay : (parts != null ? parts.day : 1)
    dYear: editing == true ? segYear : (parts != null ? parts.year : 2026)
    mStr: dMonth < 10 ? "0" + dMonth : dMonth + ""
    dStr: dDay < 10 ? "0" + dDay : dDay + ""
    yStr: dYear + ""
    monthShort: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    gridIndices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    yearRangeLabel: yearGridStart + " – " + (yearGridStart + 11)
    seg0Label: showMask == true ? (segments[0] == 'month' ? "MM" : segments[0] == 'day' ? "DD" : "YYYY") : (segments[0] == 'month' ? mStr : segments[0] == 'day' ? dStr : yStr)
    seg1Label: showMask == true ? (segments[1] == 'month' ? "MM" : segments[1] == 'day' ? "DD" : "YYYY") : (segments[1] == 'month' ? mStr : segments[1] == 'day' ? dStr : yStr)
    seg2Label: showMask == true ? (segments[2] == 'month' ? "MM" : segments[2] == 'day' ? "DD" : "YYYY") : (segments[2] == 'month' ? mStr : segments[2] == 'day' ? dStr : yStr)
  }

  @watch {
    // Close the calendar once a pick has flowed back through `value`. selectDay
    // intentionally does NOT close (see closeAfterPick) — closing in the same
    // action as emit() drops the picked date. This fires on the resulting value
    // change instead. Does not fire on mount, so it won't fight an open popup.
    value: { closeAfterPick() }
  }

  @actions {
    toggle() {
      if disabled == false {
        open = open == false
        if open == true {
          activeSegment = -1
          popupView = 0
          editing = false
          if value != "" {
            let parsed = parseDateInput(value, format)
            if parsed != null {
              viewYear = parsed.year
              viewMonth = parsed.month
              focusedDay = parsed.day
            }
          } else {
            let today = todayParts()
            viewYear = today.year
            viewMonth = today.month
            focusedDay = today.day
          }
        }
      }
    }
    close() {
      open = false
      popupView = 0
      focusTrigger = focusTrigger == false
    }
    prevMonth() {
      if viewMonth == 0 {
        viewMonth = 11
        viewYear = viewYear - 1
      } else {
        viewMonth = viewMonth - 1
      }
    }
    nextMonth() {
      if viewMonth == 11 {
        viewMonth = 0
        viewYear = viewYear + 1
      } else {
        viewMonth = viewMonth + 1
      }
    }
    openMonthView() { popupView = 1 }
    openYearView() {
      yearGridStart = viewYear - 6
      popupView = 2
    }
    pickMonth(m) {
      viewMonth = m
      popupView = 0
    }
    pickYear(y) {
      viewYear = y
      popupView = 0
    }
    prevDecade() { yearGridStart = yearGridStart - 12 }
    nextDecade() { yearGridStart = yearGridStart + 12 }
    selectDay(day) {
      emit("change", formatDateOutput(viewYear, viewMonth, day, format))
    }
    selectToday() {
      let today = todayParts()
      viewYear = today.year
      viewMonth = today.month
      selectDay(today.day)
    }

    // Keyboard navigation
    moveFocusLeft() {
      if focusedDay > 1 { focusedDay = focusedDay - 1 }
    }
    moveFocusRight() {
      if focusedDay < daysInCurrentMonth { focusedDay = focusedDay + 1 }
    }
    moveFocusUp() {
      if focusedDay > 7 { focusedDay = focusedDay - 7 }
    }
    moveFocusDown() {
      if focusedDay + 7 <= daysInCurrentMonth { focusedDay = focusedDay + 7 }
    }
    selectFocused() { selectDay(focusedDay) }
    focusPrevMonth() {
      prevMonth()
      let maxDay = daysInMonth(viewYear, viewMonth)
      if focusedDay > maxDay { focusedDay = maxDay }
    }
    focusNextMonth() {
      nextMonth()
      let maxDay = daysInMonth(viewYear, viewMonth)
      if focusedDay > maxDay { focusedDay = maxDay }
    }
    focusFirst() { focusedDay = 1 }
    focusLast() { focusedDay = daysInCurrentMonth }

    // Segment navigation
    activateSegments() {
      if value != "" {
        let parsed = parseDateInput(value, format)
        if parsed != null {
          segYear = parsed.year
          segMonth = parsed.month + 1
          segDay = parsed.day
        }
      } else {
        let today = todayParts()
        segYear = today.year
        segMonth = today.month + 1
        segDay = today.day
      }
      if activeSegment < 0 { activeSegment = 0 }
      editing = true
      // Armed but not yet edited: keep the mask showing for an empty field.
      dirty = false
      digitBuffer = ""
    }
    // Push the current segment buffer to `value` immediately, so a typed or
    // arrowed date is committed as the user edits — not only on blur. Without
    // this, submitting a form while a date field is still focused reads the old
    // (often empty) value even though the field visibly shows a date.
    emitBuffer() {
      dirty = true
      let safeYear = segYear < 1900 ? 1900 : (segYear > 2200 ? 2200 : segYear)
      emit("change", formatDateOutput(safeYear, segMonth - 1, segDay, format))
    }
    // Click a specific segment to edit it. Without this, focusing the field
    // always parks editing on segment 0; for a YYYY-MM-DD format that's the
    // YEAR, so digits the user intends for the month/day land in the year
    // (typing "07" "10" produced year 0710). Clicking a segment moves the
    // active cursor there. `on focus` runs first and arms editing; this then
    // re-targets the clicked segment.
    focusSegment(idx) {
      if disabled == false {
        if editing == false { activateSegments() }
        activeSegment = idx
        digitBuffer = ""
      }
    }
    prevSegment() {
      digitBuffer = ""
      if activeSegment > 0 { activeSegment = activeSegment - 1 }
    }
    nextSegment() {
      digitBuffer = ""
      if activeSegment < 2 { activeSegment = activeSegment + 1 }
    }
    incrementSegment() {
      let segType = segments[activeSegment]
      if segType == 'month' {
        segMonth = segMonth < 12 ? segMonth + 1 : 1
      }
      if segType == 'day' {
        let maxD = daysInMonth(segYear, segMonth - 1)
        segDay = segDay < maxD ? segDay + 1 : 1
      }
      if segType == 'year' {
        segYear = segYear + 1
      }
      emitBuffer()
    }
    decrementSegment() {
      let segType = segments[activeSegment]
      if segType == 'month' {
        segMonth = segMonth > 1 ? segMonth - 1 : 12
      }
      if segType == 'day' {
        let maxD = daysInMonth(segYear, segMonth - 1)
        segDay = segDay > 1 ? segDay - 1 : maxD
      }
      if segType == 'year' {
        segYear = segYear > 1 ? segYear - 1 : 1
      }
      emitBuffer()
    }
    handleDigit(key) {
      if key >= "0" && key <= "9" {
        digitBuffer = digitBuffer + key
        let segType = segments[activeSegment]
        if segType == 'month' {
          let n = parseInt(digitBuffer)
          let advance = (digitBuffer.length == 1 && n >= 2) || digitBuffer.length >= 2
          if advance == true {
            segMonth = n >= 1 && n <= 12 ? n : segMonth
            digitBuffer = ""
            if activeSegment < 2 { activeSegment = activeSegment + 1 }
            emitBuffer()
          }
        }
        if segType == 'day' {
          let maxD = daysInMonth(segYear, segMonth - 1)
          let n = parseInt(digitBuffer)
          let advance = (digitBuffer.length == 1 && n >= 4) || digitBuffer.length >= 2
          if advance == true {
            segDay = n >= 1 && n <= maxD ? n : segDay
            digitBuffer = ""
            if activeSegment < 2 { activeSegment = activeSegment + 1 }
            emitBuffer()
          }
        }
        if segType == 'year' {
          if digitBuffer.length >= 4 {
            let v = parseInt(digitBuffer)
            segYear = v >= 1900 && v <= 2200 ? v : segYear
            digitBuffer = ""
            if activeSegment < 2 { activeSegment = activeSegment + 1 }
            emitBuffer()
          }
        }
      }
    }
    commitSegments() {
      // Never emit an out-of-range year (defends against a corrupt incoming
      // `value` parsed back into segYear). Clamp into the supported window
      // rather than emitting e.g. 0710 downstream.
      let safeYear = segYear < 1900 ? 1900 : (segYear > 2200 ? 2200 : segYear)
      emit("change", formatDateOutput(safeYear, segMonth - 1, segDay, format))
      activeSegment = -1
      editing = false
      dirty = false
      digitBuffer = ""
    }
    cancelSegments() {
      activeSegment = -1
      editing = false
      dirty = false
      digitBuffer = ""
    }
    // Close the calendar overlay AFTER a pick has flowed back through `value`.
    // This must NOT happen inside selectDay: setting open=false in the same
    // action as emit() unmounts the overlay (which hosts the clicked day cell)
    // before the deferred "change" event propagates, so the picked date is
    // dropped and the field never updates. Closing on the value change instead
    // fires once the parent has applied the new value.
    closeAfterPick() {
      if open == true {
        open = false
        focusTrigger = focusTrigger == false
      }
    }
  }

  block {
    layout: vertical, gap: spacing.1
    // Establish a positioning context so the calendar overlay (which uses
    // position:absolute; inset:0 internally) anchors to THIS DatePicker
    // rather than walking up to the nearest positioned ancestor (which is
    // typically the modal — yielding a popup that's centered in the modal
    // instead of pinned to the trigger).
    position: relative

    // Label
    block {
      visibility: label != ""
      text(label) { style: type.label-sm, color: semantic.text-secondary }
    }

    // Trigger — styled to match TextInput.spec
    block {
      role: "combobox"
      layout: horizontal, align: center, gap: 0px
      min-height: 36px
      background: token.input-bg
      border: match error {
        true -> token.input-borderWidth + " solid " + semantic.destructive,
        _ -> match focused {
          true -> token.input-borderWidth + " solid " + semantic.interactive,
          _ -> token.input-borderWidth + " solid " + token.input-border
        }
      }
      shadow: match focused {
        true -> "0 0 0 3px " + token.input-focusRing,
        _ -> token.input-shadow
      }
      border-radius: token.input-radius
      transition: transition.focus
      opacity: disabled ? 0.5 : 1
      overflow: hidden

      // Date input area
      block {
        grow: true
        padding: spacing.2
        cursor: "text"
        tabindex: "0"
        aria-label: "Date picker"
        focus: focusTrigger
        on focus: {
          focused = true
          if editing == false { activateSegments() }
        }
        on blur: {
          focused = false
          if editing == true { commitSegments() }
        }
        on key-down(event): {
          if activeSegment >= 0 {
            match event.key {
              "ArrowLeft" -> prevSegment(),
              "ArrowRight" -> nextSegment(),
              "ArrowUp" -> incrementSegment(),
              "ArrowDown" -> decrementSegment(),
              "Enter" -> commitSegments(),
              "Escape" -> cancelSegments(),
              // Tab: commit the typed value so it isn't lost, then allow the
              // browser's native Tab to move focus. Because this match arm is
              // inside an `if` block the compiler does NOT auto-preventDefault
              // for any key in this handler — Tab therefore falls through to
              // the browser naturally. The real fix for the tab-trap was
              // adding tabindex:"-1" to each segment block so Tab no longer
              // cycles through seg0→seg1→seg2 inside the picker.
              "Tab" -> commitSegments(),
              _ -> handleDigit(event.key)
            }
          } else {
            match event.key {
              "Escape" -> close(),
              "ArrowUp" -> activateSegments(),
              "ArrowDown" -> activateSegments(),
              _ -> {}
            }
          }
        }

        // Segmented date display (when editing segments)
        block {
          layout: horizontal, align: center, gap: 0px

          // Segment 0 — tabindex:"-1" removes it from the tab order so Tab
          // moves focus OUT of the picker rather than cycling through segments.
          // Click-to-focus still works; the parent block (tabindex:"0") is the
          // sole tab stop for the whole date-input area.
          block {
            padding-x: 2px
            cursor: "text"
            tabindex: "-1"
            background: activeSegment == 0 ? semantic.interactive : "transparent"
            border-radius: radius.sm
            on click: focusSegment(0)
            text(seg0Label) {
              style: type.body-md
              color: activeSegment == 0 ? semantic.surface : (showMask == true ? semantic.text-tertiary : semantic.text-primary)
            }
          }
          text(sep) { style: type.body-md, color: semantic.text-tertiary }
          // Segment 1
          block {
            padding-x: 2px
            cursor: "text"
            tabindex: "-1"
            background: activeSegment == 1 ? semantic.interactive : "transparent"
            border-radius: radius.sm
            on click: focusSegment(1)
            text(seg1Label) {
              style: type.body-md
              color: activeSegment == 1 ? semantic.surface : (showMask == true ? semantic.text-tertiary : semantic.text-primary)
            }
          }
          text(sep) { style: type.body-md, color: semantic.text-tertiary }
          // Segment 2
          block {
            padding-x: 2px
            cursor: "text"
            tabindex: "-1"
            background: activeSegment == 2 ? semantic.interactive : "transparent"
            border-radius: radius.sm
            on click: focusSegment(2)
            text(seg2Label) {
              style: type.body-md
              color: activeSegment == 2 ? semantic.surface : (showMask == true ? semantic.text-tertiary : semantic.text-primary)
            }
          }
        }
      }

      // Divider + calendar button
      block {
        width: 36px
        min-height: 36px
        layout: horizontal, justify: center, align: center
        border-left: match focused {
          true -> "1px solid " + semantic.interactive,
          _ -> "1px solid " + token.input-border
        }
        cursor: disabled ? "default" : "pointer"
        on hover { background: disabled ? "transparent" : semantic.surface-raised }
        on click: toggle()
        text("\uD83D\uDCC5") { style: type.body-md, color: semantic.text-tertiary }
      }
    }

    // Calendar popup
    overlay(visible: open, anchor: "parent", backdrop: "transparent", dismissOnTapOutside: true) {
      on dismiss: close()

      block {
        // Pin the calendar to the bottom-left of the trigger and let it
        // extend rightward + downward to its natural 280px. `position:
        // absolute` removes the popup from the overlay's flex centering
        // (which would otherwise shrink it to the trigger's column width
        // and clip the left edge when the trigger is near the modal's
        // left margin).
        position: absolute
        top: 100%
        left: 0
        // Margin shorthand applies to all sides; on a position:absolute
        // element only top/left meaningfully shift placement, giving us
        // a small gap below the trigger. The spec parser doesn't expose
        // a margin-top: shortcut.
        margin: spacing.1
        width: 280px
        min-width: 280px
        background: semantic.surface
        border: borders.default
        border-radius: radius.md
        shadow: elevation.floating
        layout: vertical

        block {
          visibility: popupView == 0
          layout: vertical

        // Month navigation
        block {
          layout: horizontal, justify: between, align: center
          padding: spacing.2
          border-bottom: borders.default

          block {
            cursor: "pointer"
            padding: spacing.2
            on click: prevMonth()
            text("\u25C0") { style: type.body-md, color: semantic.interactive }
          }
          block {
            layout: horizontal, align: center, gap: spacing.1
            block {
              cursor: "pointer"
              padding-x: spacing.1
              border-radius: radius.sm
              on hover { background: semantic.surface-raised }
              on click: openMonthView()
              text(monthNames[viewMonth]) { style: type.body-md, weight: 600, color: semantic.text-primary }
            }
            block {
              cursor: "pointer"
              padding-x: spacing.1
              border-radius: radius.sm
              on hover { background: semantic.surface-raised }
              on click: openYearView()
              text(viewYear + "") { style: type.body-md, weight: 600, color: semantic.text-primary }
            }
          }
          block {
            cursor: "pointer"
            padding: spacing.2
            on click: nextMonth()
            text("\u25B6") { style: type.body-md, color: semantic.interactive }
          }
        }

        // Day-of-week headers
        block {
          layout: grid, columns: "repeat(7, 1fr)"
          padding: spacing.1

          text('Su') { style: type.caption, color: semantic.text-tertiary }
          text('Mo') { style: type.caption, color: semantic.text-tertiary }
          text('Tu') { style: type.caption, color: semantic.text-tertiary }
          text('We') { style: type.caption, color: semantic.text-tertiary }
          text('Th') { style: type.caption, color: semantic.text-tertiary }
          text('Fr') { style: type.caption, color: semantic.text-tertiary }
          text('Sa') { style: type.caption, color: semantic.text-tertiary }
        }

        // Calendar grid
        block {
          layout: grid, columns: "repeat(7, 1fr)", gap: spacing.1
          padding: spacing.1

          on key-down(event): {
            match event.key {
              "ArrowLeft" -> moveFocusLeft(),
              "ArrowRight" -> moveFocusRight(),
              "ArrowUp" -> moveFocusUp(),
              "ArrowDown" -> moveFocusDown(),
              "Enter" -> selectFocused(),
              " " -> selectFocused(),
              "Escape" -> close(),
              "PageUp" -> focusPrevMonth(),
              "PageDown" -> focusNextMonth(),
              "Home" -> focusFirst(),
              "End" -> focusLast(),
              _ -> {}
            }
          }

          each calendarCells as cell {
            block {
              padding: spacing.1
              min-height: 32px
              layout: horizontal, justify: center, align: center
              border-radius: radius.sm
              cursor: cell.isCurrentMonth ? "pointer" : "default"
              border: cell.day == focusedDay && cell.isCurrentMonth ? "2px solid " + semantic.interactive : "2px solid transparent"
              background: match cell.dateStr == valueISO {
                true -> semantic.interactive,
                _ -> cell.day == focusedDay && cell.isCurrentMonth ? semantic.surface-raised : "transparent"
              }
              tabindex: "-1"
              focus: cell.day == focusedDay && cell.isCurrentMonth && open
              on hover { background: cell.isCurrentMonth ? semantic.surface-raised : "transparent" }
              on click: cell.isCurrentMonth ? selectDay(cell.day) : {}

              text(cell.day + "") {
                style: type.body-sm
                color: match cell.dateStr == valueISO {
                  true -> semantic.surface,
                  _ -> cell.isCurrentMonth ? semantic.text-primary : semantic.text-tertiary
                }
              }
            }
          }
        }

        // Today button
        block {
          padding: spacing.2
          border-top: borders.default
          layout: horizontal, justify: center
          block {
            cursor: "pointer"
            padding: spacing.1
            on click: selectToday()
            text('Today') { style: type.label-sm, color: semantic.interactive }
          }
        }
        }

        block {
          visibility: popupView == 1
          layout: vertical
          block {
            layout: horizontal, justify: center, align: center
            padding: spacing.2
            border-bottom: borders.default
            text('Select month') { style: type.label-sm, color: semantic.text-secondary }
          }
          block {
            layout: grid, columns: "repeat(3, 1fr)", gap: spacing.1
            padding: spacing.2
            each monthShort as name, idx {
              block {
                padding: spacing.2
                layout: horizontal, justify: center, align: center
                border-radius: radius.sm
                cursor: "pointer"
                background: idx == viewMonth ? semantic.interactive : "transparent"
                on hover { background: idx == viewMonth ? semantic.interactive : semantic.surface-raised }
                on click: pickMonth(idx)
                text(name) {
                  style: type.body-sm
                  color: idx == viewMonth ? semantic.surface : semantic.text-primary
                }
              }
            }
          }
        }

        block {
          visibility: popupView == 2
          layout: vertical
          block {
            layout: horizontal, justify: between, align: center
            padding: spacing.2
            border-bottom: borders.default
            block {
              cursor: "pointer"
              padding: spacing.2
              on click: prevDecade()
              text("◀") { style: type.body-md, color: semantic.interactive }
            }
            text(yearRangeLabel) { style: type.body-md, weight: 600, color: semantic.text-primary }
            block {
              cursor: "pointer"
              padding: spacing.2
              on click: nextDecade()
              text("▶") { style: type.body-md, color: semantic.interactive }
            }
          }
          block {
            layout: grid, columns: "repeat(3, 1fr)", gap: spacing.1
            padding: spacing.2
            each gridIndices as idx {
              block {
                padding: spacing.2
                layout: horizontal, justify: center, align: center
                border-radius: radius.sm
                cursor: "pointer"
                background: (yearGridStart + idx) == viewYear ? semantic.interactive : "transparent"
                on hover { background: (yearGridStart + idx) == viewYear ? semantic.interactive : semantic.surface-raised }
                on click: pickYear(yearGridStart + idx)
                text((yearGridStart + idx) + "") {
                  style: type.body-sm
                  color: (yearGridStart + idx) == viewYear ? semantic.surface : semantic.text-primary
                }
              }
            }
          }
        }
      }
    }

    // Error caption
    block {
      visibility: error == true
      text(errorMessage) { style: type.caption, color: semantic.destructive }
    }
  }
}
