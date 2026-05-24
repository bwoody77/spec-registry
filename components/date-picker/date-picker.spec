@extern { calendarGrid, todayStr, parseDateInput, daysInMonth, todayParts, formatDateOutput, formatSegments, formatSeparator, toISODate } from "@spec/components/date-utils.js"

component DatePicker(value: string = "", label: string = "", placeholder: string = "",
                     disabled: boolean = false, format: string = "MM/DD/YYYY") {
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
    digitBuffer: ""
  }

  @computed {
    valueISO: value != "" ? toISODate(value, format) : ""
    displayValue: value != "" ? value : ""
    placeholderText: placeholder != "" ? placeholder : format
    daysInCurrentMonth: daysInMonth(viewYear, viewMonth)
    monthNames: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    monthLabel: monthNames[viewMonth] + " " + viewYear
    calendarCells: calendarGrid(viewYear, viewMonth)
    segments: formatSegments(format)
    sep: formatSeparator(format)
    seg0Label: segments[0] == 'month' ? (segMonth < 10 ? "0" + segMonth : segMonth + "") : segments[0] == 'day' ? (segDay < 10 ? "0" + segDay : segDay + "") : segYear + ""
    seg1Label: segments[1] == 'month' ? (segMonth < 10 ? "0" + segMonth : segMonth + "") : segments[1] == 'day' ? (segDay < 10 ? "0" + segDay : segDay + "") : segYear + ""
    seg2Label: segments[2] == 'month' ? (segMonth < 10 ? "0" + segMonth : segMonth + "") : segments[2] == 'day' ? (segDay < 10 ? "0" + segDay : segDay + "") : segYear + ""
  }

  @actions {
    toggle() {
      if disabled == false {
        open = open == false
        if open == true {
          activeSegment = -1
          editing = false
          if value != "" {
            let parts = parseDateInput(value, format)
            if parts != null {
              viewYear = parts.year
              viewMonth = parts.month
              focusedDay = parts.day
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
    selectDay(day) {
      emit("change", formatDateOutput(viewYear, viewMonth, day, format))
      open = false
      focusTrigger = focusTrigger == false
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
        let parts = parseDateInput(value, format)
        if parts != null {
          segYear = parts.year
          segMonth = parts.month + 1
          segDay = parts.day
        }
      } else {
        let today = todayParts()
        segYear = today.year
        segMonth = today.month + 1
        segDay = today.day
      }
      activeSegment = 0
      editing = true
      digitBuffer = ""
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
    }
    handleDigit(key) {
      if key >= "0" && key <= "9" {
        digitBuffer = digitBuffer + key
        let segType = segments[activeSegment]
        if segType == 'month' {
          if digitBuffer.length >= 2 {
            let v = parseInt(digitBuffer)
            segMonth = v >= 1 && v <= 12 ? v : segMonth
            digitBuffer = ""
            if activeSegment < 2 { activeSegment = activeSegment + 1 }
          }
        }
        if segType == 'day' {
          if digitBuffer.length >= 2 {
            let maxD = daysInMonth(segYear, segMonth - 1)
            let v = parseInt(digitBuffer)
            segDay = v >= 1 && v <= maxD ? v : segDay
            digitBuffer = ""
            if activeSegment < 2 { activeSegment = activeSegment + 1 }
          }
        }
        if segType == 'year' {
          if digitBuffer.length >= 4 {
            let v = parseInt(digitBuffer)
            segYear = v > 0 ? v : segYear
            digitBuffer = ""
            if activeSegment < 2 { activeSegment = activeSegment + 1 }
          }
        }
      }
    }
    commitSegments() {
      emit("change", formatDateOutput(segYear, segMonth - 1, segDay, format))
      activeSegment = -1
      editing = false
      digitBuffer = ""
    }
    cancelSegments() {
      activeSegment = -1
      editing = false
      digitBuffer = ""
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
      border: match focused {
        true -> token.input-borderWidth + " solid " + semantic.interactive,
        _ -> token.input-borderWidth + " solid " + token.input-border
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
              "Tab" -> {},
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
          visibility: editing == true
          layout: horizontal, align: center, gap: 0px

          // Segment 0
          block {
            padding-x: 2px
            background: activeSegment == 0 ? semantic.interactive : "transparent"
            border-radius: radius.sm
            text(seg0Label) {
              style: type.body-md
              color: activeSegment == 0 ? semantic.surface : semantic.text-primary
            }
          }
          text(sep) { style: type.body-md, color: semantic.text-tertiary }
          // Segment 1
          block {
            padding-x: 2px
            background: activeSegment == 1 ? semantic.interactive : "transparent"
            border-radius: radius.sm
            text(seg1Label) {
              style: type.body-md
              color: activeSegment == 1 ? semantic.surface : semantic.text-primary
            }
          }
          text(sep) { style: type.body-md, color: semantic.text-tertiary }
          // Segment 2
          block {
            padding-x: 2px
            background: activeSegment == 2 ? semantic.interactive : "transparent"
            border-radius: radius.sm
            text(seg2Label) {
              style: type.body-md
              color: activeSegment == 2 ? semantic.surface : semantic.text-primary
            }
          }
        }

        // Plain display (when not editing segments)
        block {
          visibility: editing == false
          text(displayValue != "" ? displayValue : placeholderText) {
            style: type.body-md
            color: displayValue != "" ? semantic.text-primary : semantic.text-tertiary
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
          text(monthLabel) { style: type.body-md, weight: 600, color: semantic.text-primary }
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
    }
  }
}
