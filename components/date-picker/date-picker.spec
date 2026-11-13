@extern { calendarGrid, todayStr, parseDateInput, daysInMonth, todayParts, formatDateOutput, formatSegments, formatSeparator, toISODate, isoToOutput, segmentsTakeTyping } from "@spec/components/date-utils.js"

component DatePicker(value: string = "", label: text = "", placeholder: text = "",
                     disabled: boolean = false, format: string = "MM/DD/YYYY",
                     error: boolean = false, errorMessage: text = "",
                     // Same value space as TextInput's `tone`, and the same
                     // meaning: `error` says the submit rejected this field,
                     // `tone: "warning"` says something still wants a value
                     // here. A date the form has not been given yet is not a
                     // date entered wrongly.
                     //
                     // Defaults to "default", so every existing call site is
                     // untouched.
                     tone: string = "default",
                     // The date field's accessible name, when it is not `label`.
                     //
                     // The tab stop used to say "Date picker" whatever the
                     // field was, so every date in an app was announced alike
                     // and none by its label (Vector I-1264: Returned on, New
                     // expiration). Chain, FormField's effAriaLabel plus a last
                     // resort: `ariaLabel`, else `label`, else "Date picker".
                     //
                     // Declaring it also opts DatePicker into the compiler's
                     // inferred names (ast-to-ir inferAccessibleNames): a
                     // `text('Returned on')` rendered just before the call is
                     // passed in here, so pass it by hand only when the label
                     // is out of the compiler's sight (a FormField slot, a
                     // wrapper block) or the spoken name should differ.
                     ariaLabel: text = "",
                     // "md" (default, 38px) | "sm" (32px, beside a small
                     // Select or TextInput in a dense form row).
                     size: string = "md",
                     // "field" (default, unchanged) | "inline" (0.14.0): a date
                     // written on a printed form (Vector I-5148, the training
                     // record sheet). No box: the date reads as text in its
                     // cell, the calendar button shows only on hover or focus,
                     // and typing it works as in the field. A blank shows the
                     // placeholder; the form around it draws the blank's fill.
                     appearance: string = "field",
                     // The date's size and face in the "inline" look ('11.5px',
                     // 'mono'; '' is 13px in the inherited face). The field
                     // look keeps body-md and ignores both.
                     fontSize: string = "",
                     fontFamily: string = "",
                     // The date's color, for a surface that is not the
                     // theme's (paper stays ink on white in a dark theme). ''
                     // keeps the text color. The mask and placeholder keep
                     // their tertiary color.
                     valueColor: string = "",
                     // The date may be left empty (0.15.0, Vector I-5386). A
                     // clear button shows in the field while it holds a date,
                     // and Backspace/Delete erase a committed segment; leaving
                     // the field with the date erased sends ''. Off by
                     // default: a required date keeps what it holds, as before.
                     clearable: boolean = false) {
  @state {
    open: false
    viewYear: 2026
    viewMonth: 2
    focusedDay: 1
    focused: false
    // Focus is on the field or on one of its segments (focus-in / focus-out,
    // which bubble from a segment where focus / blur do not). See fieldFocusOut.
    focusWithin: false
    // The pointer is over the trigger: the "inline" look shows its calendar
    // button then, as it does on focus.
    hovered: false
    // "The field should take focus back." A REQUEST, not a toggle. It used to
    // be flipped (`focusTrigger = focusTrigger == false`) on every close, and
    // bindFocus fires on the false->true EDGE only — so focus came back on
    // alternate closes and landed on <body> the other half of the time. The
    // flag is cleared when the calendar opens, so every close is a fresh edge.
    refocusField: false
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
    // Has the user actually typed these segments this session, or are they
    // still the today-prefill from activateSegments? The day segment must not
    // be range-checked against a year/month the user hasn't entered yet: on
    // MM/DD/YYYY (the default) the year is typed LAST, so validating day 29
    // against the prefilled current year silently rejected every Feb-29 date
    // whenever today's year was not a leap year — the day kept its default and
    // 02/29/1968 committed as 1968-02-14. See reconcileDay.
    // …and the day needs the same flag, for the DISPLAY rather than for
    // validation: all three say "this segment holds something the user chose,
    // not the activateSegments prefill". See maskMonth/maskDay/maskYear.
    monthTyped: false
    dayTyped: false
    yearTyped: false
    digitBuffer: ""
    // Did the user ASK to edit the segments, or did focus arm them for free?
    // `on focus` calls activateSegments so a tabbed-into field is immediately
    // typeable — a convenience, not an edit. Escape must not treat it as
    // something to cancel, or every date field costs the dialog around it an
    // extra keystroke to dismiss. See escapeSegments.
    userArmed: false
    popupView: 0
    yearGridStart: 2020
    // The error line's id, which the date field's aria-describedby names.
    // Minted per mount: a literal would repeat on every DatePicker on a page.
    msgId: uniqueId('spec-field-msg')
    // The words the error line says, through followError() (TextInput's
    // "Saying it again", Vector #987).
    errWords: error == true ? errorMessage : ''
    // True for 100ms after the line went empty.
    errHeld: false
  }

  @computed {
    // ── The error, said as well as painted (Vector #989) ─────────────────────
    //
    // TextInput's pattern (Vector #874, #987), and its comments say why. The
    // caption used to be gated by `visibility: error == true`, which is
    // display:none: a live region that enters the accessibility tree together
    // with its words is never announced, and the field said neither that it
    // was invalid nor what was wrong. Now the line is always here, holds the
    // words while `error` is on, and is out of the flow while it is empty, so
    // a DatePicker with no error takes exactly the room it took before.
    errText: error == true ? errorMessage : ''
    errShown: errWords != ''
    errPosition: errShown ? 'static' : 'absolute'
    errStandIn: errHeld ? errText : ''
    errStandInShown: errStandIn != ''
    // null, not "false" or "": bindAttr removes the attribute, so a field with
    // no error carries neither.
    invalidAttr: error == true ? 'true' : null
    describedBy: errShown ? msgId : null
    // ── appearance: "inline" (0.14.0, Vector I-5148) ─────────────────────────
    // No border, fill or shadow at rest; the focus ring still says where the
    // keyboard is, and an error or tone still paints its fill and border,
    // since an inline date has no other place to say it. The calendar button
    // has no divider and shows on hover, on focus and while the calendar is
    // open (opacity, not visibility: it stays the same click target, and a
    // touch focuses the field first). The texts are a `match` of two arms
    // (textArm), as Select's fontSize is: a `font-size:` bound to '' clears
    // the level's size, so the field look keeps its own unbound texts.
    isInline: appearance == "inline"
    textArm: isInline ? "inline" : "field"
    inlineSize: fontSize != "" ? fontSize : '13px'
    inlineFace: fontFamily != "" ? fontFamily : 'inherit'
    inkColor: valueColor != "" ? valueColor : semantic.text-primary
    restBg: isInline ? "transparent" : token.input-bg
    restBorder: isInline
      ? token.input-borderWidth + " solid transparent"
      : (focused ? token.input-borderWidth + " solid " + semantic.interactive : token.input-borderWidth + " solid " + token.input-border)
    restShadow: isInline ? "none" : token.input-shadow
    calWidth: isInline ? '22px' : '36px'
    calDivider: isInline
      ? "none"
      : (focused ? "1px solid " + semantic.interactive : "1px solid " + token.input-border)
    calOpacity: isInline == false || focused || hovered || open ? 1 : 0
    // ── size (Vector I-5062) ─────────────────────────────────────────────────
    // "sm" matches Select's and TextInput's small field: a 30px floor on the
    // trigger, and 0 8px on the date area, so the
    // floor sets the height for any text line up to 30 and the field measures
    // what they do (30 + 2×border content-box, 30 under a global border-box).
    // It was 4px 8px on the reasoning "4 + 20 + 4 = 28 under the floor", but
    // the line is the app's body-md line, not 20: Vector's is 23.6, so the
    // date area was 31.6 and the field stood 33.6 beside a 30px TextInput
    // (Vector I-5080). "md" (the default) is the 36px floor and 8px padding
    // every caller had before. Both are STRING lengths: a computed number
    // emits `min-height: 30`, which the browser drops (TextInput's note).
    //
    // The calendar button must not carry the floor itself in "sm". It used
    // to repeat the trigger's 30px min-height so its divider ran the full
    // height, but it sits INSIDE the trigger's border: under a global
    // `box-sizing: border-box` (Vector) the trigger's 30 includes its 1px
    // border, the button's 30 does not fit in the 28 left, and the field
    // measured 32 beside a 30px TextInput. So "sm" stretches the row's
    // children instead (triggerAlign) and the button takes the row's height
    // whatever the box model; the date area centers its own text. "md" keeps
    // the centered row and the button's 36 floor, exactly as before.
    triggerMinHeight: isInline ? 'auto' : (size == "sm" ? '30px' : '36px')
    calMinHeight: size == "sm" || isInline ? 'auto' : '36px'
    triggerAlign: isInline ? 'center' : (size == "sm" ? 'stretch' : 'center')
    fieldPad: isInline ? '0px 2px' : (size == "sm" ? '0px 8px' : spacing.2)

    valueISO: value != "" ? toISODate(value, format) : ""
    displayValue: value != "" ? value : ""
    // The letters a date-entry mask shows, in the build's language (es: A for
    // año). Declared before the seg*Label masks that read them — computeds
    // evaluate in order.
    maskY: calendarMaskLetter('Y')
    maskM: calendarMaskLetter('M')
    maskD: calendarMaskLetter('D')
    daysInCurrentMonth: daysInMonth(viewYear, viewMonth)
    monthNames: calendarMonths('long')
    calendarCells: calendarGrid(viewYear, viewMonth)
    segments: formatSegments(format)
    sep: formatSeparator(format)
    parts: value != "" ? parseDateInput(value, format) : null
    // Masking is PER SEGMENT, because activateSegments prefills all three with
    // today at once. A single showMask flag meant entering the month un-masked
    // the day and year too, so the field read 03/20/2026 when the user had
    // typed "03" — today's date presented as their answer. Not editing: a
    // parseable value shows, anything else masks.
    maskMonth: editing == true ? monthTyped == false : parts == null
    maskDay:   editing == true ? dayTyped == false   : parts == null
    maskYear:  editing == true ? yearTyped == false  : parts == null
    mask0: segments[0] == 'month' ? maskMonth : (segments[0] == 'day' ? maskDay : maskYear)
    mask1: segments[1] == 'month' ? maskMonth : (segments[1] == 'day' ? maskDay : maskYear)
    mask2: segments[2] == 'month' ? maskMonth : (segments[2] == 'day' ? maskDay : maskYear)
    // A date needs all three parts. Until it has them there is nothing honest
    // to emit — see emitBuffer.
    segmentsComplete: monthTyped && dayTyped && yearTyped
    // An empty field nobody has typed into yet: the prefill is not a date,
    // so a click on any segment starts at the first (focusSegment).
    untouched: value == "" && !monthTyped && !dayTyped && !yearTyped && digitBuffer == ""
    dMonth: editing == true ? segMonth : (parts != null ? parts.month + 1 : 1)
    dDay: editing == true ? segDay : (parts != null ? parts.day : 1)
    dYear: editing == true ? segYear : (parts != null ? parts.year : 2026)
    mStr: dMonth < 10 ? "0" + dMonth : dMonth + ""
    dStr: dDay < 10 ? "0" + dDay : dDay + ""
    yStr: dYear + ""
    monthShort: calendarMonths('short')
    gridIndices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    yearRangeLabel: yearGridStart + " – " + (yearGridStart + 11)
    seg0Label: mask0 ? (segments[0] == 'month' ? maskM + maskM : segments[0] == 'day' ? maskD + maskD : maskY + maskY + maskY + maskY) : (segments[0] == 'month' ? mStr : segments[0] == 'day' ? dStr : yStr)
    seg1Label: mask1 ? (segments[1] == 'month' ? maskM + maskM : segments[1] == 'day' ? maskD + maskD : maskY + maskY + maskY + maskY) : (segments[1] == 'month' ? mStr : segments[1] == 'day' ? dStr : yStr)
    seg2Label: mask2 ? (segments[2] == 'month' ? maskM + maskM : segments[2] == 'day' ? maskD + maskD : maskY + maskY + maskY + maskY) : (segments[2] == 'month' ? mStr : segments[2] == 'day' ? dStr : yStr)
    // What a segment actually SHOWS. The committed value is only half of it:
    // a segment being typed into has to echo the digits already entered, or
    // the field looks inert until the segment happens to complete. On a
    // four-digit year that is three keystrokes of silence - type 2, 0, 2 and
    // the field still reads YYYY (or the old year); only the 6 changes
    // anything. digitBuffer holds those pending digits, so show them.
    seg0Text: activeSegment == 0 && digitBuffer != "" ? digitBuffer : seg0Label
    seg1Text: activeSegment == 1 && digitBuffer != "" ? digitBuffer : seg1Label
    seg2Text: activeSegment == 2 && digitBuffer != "" ? digitBuffer : seg2Label
    // An empty field the user is not typing into shows the caller's
    // placeholder in place of the three masks. The prop was declared and never
    // drawn, so every 'Pick a date…' a caller wrote was dead copy (Vector
    // bwoody77/vector#3435). Focus arms the segments (`editing`), which brings
    // the mask back for entry; no placeholder keeps the mask as before.
    showPlaceholder: placeholder != "" && value == "" && editing == false
    placeholderShown: showPlaceholder ? placeholder : ""
    // ── clearable (0.15.0, Vector I-5386) ────────────────────────────────────
    // The button shows while there is a date to clear; it is a real <button>,
    // so Tab reaches it and Enter or Space presses it.
    clearShown: clearable && disabled == false && value != ""
    // Every segment erased, nothing pending: Enter commits the clear.
    segmentsErased: !monthTyped && !dayTyped && !yearTyped && digitBuffer == ""
    // The user took something away this edit. An unparseable `value` arms
    // with its segments untyped too, which looks like an erased date; without
    // `dirty` a focus and a blur would send '' over it (0.15.1).
    userErased: clearable && value != "" && dirty
  }

  @watch {
    // Close the calendar once a pick has flowed back through `value`. selectDay
    // intentionally does NOT close (see closeAfterPick) — closing in the same
    // action as emit() drops the picked date. This fires on the resulting value
    // change instead. Does not fire on mount, so it won't fight an open popup.
    value: { valueChanged() }
    // Both props: a watch on one reads its sibling's old value when the
    // caller changes both.
    error: { followError() }
    errorMessage: { followError() }
  }

  @actions {
    // Words that arrive within 100ms of the line going empty wait out those
    // 100ms, so the empty line reaches the page before the same words come
    // back and a second failure is heard (TextInput's followError).
    followError() {
      let words = error == true ? errorMessage : ''
      if words == '' {
        if errWords != '' {
          errWords = ''
          errHeld = true
          delay("errRefill", 100) {
            errHeld = false
            errWords = error == true ? errorMessage : ''
          }
        }
        return
      }
      if !errHeld {
        errWords = words
      }
    }
    toggle() {
      if disabled == false {
        open = open == false
        if open == true {
          refocusField = false
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
      refocusField = true
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
      let out = formatDateOutput(viewYear, viewMonth, day, format)
      if out == value {
        // Same date re-selected: no value change, so @watch won't fire.
        // Close directly — safe because there is no emit() here.
        closeAfterPick()
        return
      }
      emit("change", out)
    }
    // Select any visible calendar cell by its true ISO dateStr. Leading/trailing
    // cells belong to the previous/next month, so we must emit from the cell's
    // own date — NOT from viewYear/viewMonth, which would wrongly snap e.g. a
    // clicked "July 1" (visible while viewing June) back to June 1.
    selectCell(iso) {
      let out = isoToOutput(iso, format)
      if out == value {
        // Same date re-selected: no value change, so @watch won't fire.
        // Close directly — safe because there is no emit() here.
        closeAfterPick()
        return
      }
      emit("change", out)
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
      // Reset first, so an unparseable incoming value leaves the field masked
      // rather than showing whatever the segments happened to hold.
      monthTyped = false
      dayTyped = false
      yearTyped = false
      if value != "" {
        let parsed = parseDateInput(value, format)
        if parsed != null {
          segYear = parsed.year
          segMonth = parsed.month + 1
          segDay = parsed.day
          // Parsed from a real value: all three are genuine, so they show
          // rather than mask, and the day can be range-checked straight away.
          monthTyped = true
          dayTyped = true
          yearTyped = true
        }
      } else {
        let today = todayParts()
        segYear = today.year
        segMonth = today.month + 1
        segDay = today.day
        // Prefill only — NOT the user's intent. Until they type these the day
        // is validated permissively (see applyBuffer), the segments show their
        // mask, and nothing is emitted.
      }
      if activeSegment < 0 { activeSegment = 0 }
      editing = true
      userArmed = true
      // Armed but not yet edited: keep the mask showing for an empty field.
      dirty = false
      digitBuffer = ""
    }
    // Push the current segment buffer to `value` immediately, so a typed or
    // arrowed date is committed as the user edits — not only on blur. Without
    // this, submitting a form while a date field is still focused reads the old
    // (often empty) value even though the field visibly shows a date.
    emitBuffer() {
      // Records that the user has edited — Escape reads this — whether or not
      // there is yet a date to emit.
      dirty = true
      // A partial entry is not a date. Emitting one meant the segments the
      // user had not reached were filled from the today-prefill and committed
      // as though chosen: type "03", tab away, and the form received
      // 03/20/2026. The field now shows 03/DD/YYYY and sends nothing until it
      // can send the whole thing.
      if segmentsComplete == false { return }
      let safeYear = segYear < 1900 ? 1900 : (segYear > 2200 ? 2200 : segYear)
      emit("change", formatDateOutput(safeYear, segMonth - 1, segDay, format))
    }
    // Arm the segments because focus arrived, not because the user asked. Same
    // setup, but Escape stays available to the dialog (see escapeSegments).
    armFromFocus() {
      if segmentsTakeTyping() == false { return }
      activateSegments()
      userArmed = false
    }
    // Click a specific segment to edit it. Without this, focusing the field
    // always parks editing on segment 0; for a YYYY-MM-DD format that's the
    // YEAR, so digits the user intends for the month/day land in the year
    // (typing "07" "10" produced year 0710). Clicking a segment moves the
    // active cursor there. `on focus` runs first and arms editing; this then
    // re-targets the clicked segment.
    //
    // Where no keyboard reaches the segments (Android: the field is a
    // focusable box, not a text field, so a tap raised none), a tap on the
    // date opens the calendar, as the button does and as iOS's native picker
    // does (Vector #2369). Arming there left a highlighted segment that
    // nothing could type into.
    focusSegment(idx) {
      if segmentsTakeTyping() == false {
        if open == false { toggle() }
        return
      }
      if disabled == false {
        if editing == false { activateSegments() }
        // Commit what was typed into the segment being LEFT. Clicking straight
        // from a half-typed month onto the day used to drop the month.
        flushSegment()
        // An empty field types from its first segment wherever it was clicked
        // (Vector #5035). A click lands on whatever segment is under the
        // pointer, and the digits of a whole date typed into the year were
        // refused there (1110 is no year), leaving the month and day blank:
        // Enter then had nothing to commit and the field read empty again.
        // Once a segment holds something the click means "edit this one".
        activeSegment = untouched ? 0 : idx
        digitBuffer = ""
      }
    }
    prevSegment() {
      flushSegment()
      if activeSegment > 0 { activeSegment = activeSegment - 1 }
    }
    nextSegment() {
      flushSegment()
      if activeSegment < 2 { activeSegment = activeSegment + 1 }
    }
    // Arrowing a segment is the user choosing that value, so it counts as
    // entered — otherwise the segment they just changed would keep its mask.
    markSegmentEntered() {
      let segType = segments[activeSegment]
      if segType == 'month' { monthTyped = true }
      if segType == 'day' { dayTyped = true }
      if segType == 'year' { yearTyped = true }
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
      markSegmentEntered()
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
      markSegmentEntered()
      emitBuffer()
    }
    // Trim the day once a newly-typed month/year makes it impossible (Feb 30,
    // or Feb 29 in a non-leap year). Runs AFTER the month/year segments are
    // set, so the day is judged against what the user actually entered rather
    // than against a prefill. Only ever shrinks the day, and the field shows
    // the trimmed value — it never silently keeps a stale default.
    reconcileDay() {
      let refYear = yearTyped ? segYear : 2000
      let mx = daysInMonth(refYear, segMonth - 1)
      if segDay > mx { segDay = mx }
    }
    // Write the pending digits into the active segment and clear the buffer.
    // Every route out of a segment funnels through here - auto-advance, a
    // separator key, an arrow, a click on a sibling segment, Tab, Enter, blur
    // - so a single typed digit ("1" for January, "5" for the 5th) is never
    // silently dropped just because the segment was left before it filled.
    //
    // Out-of-range digits leave the segment alone rather than writing nonsense;
    // the field keeps showing the previous value, which is what the user then
    // corrects.
    applyBuffer() {
      if activeSegment < 0 { return }
      if digitBuffer == "" { return }
      let n = parseInt(digitBuffer)
      let segType = segments[activeSegment]
      if segType == 'month' {
        if n >= 1 && n <= 12 {
          segMonth = n
          monthTyped = true
        }
      }
      if segType == 'day' {
        // Only range-check against segments the user has actually typed.
        // Month unknown (DD/MM/YYYY types day first) -> allow any real day.
        // Month known but year not (MM/DD/YYYY) -> use a LEAP reference year
        // so Feb 29 is accepted; reconcileDay trims it if the year they go on
        // to type isn't a leap year. Checking the day against the today-
        // prefilled year instead silently dropped Feb 29 and kept the default.
        let refYear = yearTyped ? segYear : 2000
        let maxD = monthTyped ? daysInMonth(refYear, segMonth - 1) : 31
        if n >= 1 && n <= maxD {
          segDay = n
          dayTyped = true
        }
      }
      if segType == 'year' {
        // Two digits is the familiar shorthand, and it only ever reaches here
        // when the user LEFT the segment early (auto-advance needs four), so
        // expanding it is the difference between "08/20/26" working and the
        // year being thrown away. Pivot at 68, the POSIX convention.
        let y = digitBuffer.length == 2 ? (n <= 68 ? 2000 + n : 1900 + n) : n
        if y >= 1900 && y <= 2200 {
          segYear = y
          yearTyped = true
        }
      }
      digitBuffer = ""
      reconcileDay()
    }
    // applyBuffer + emit, for the paths that leave a segment without also
    // committing the whole field. Silent when nothing was typed: a stray key
    // on an untouched field must not commit the today-prefill.
    flushSegment() {
      if digitBuffer != "" {
        applyBuffer()
        emitBuffer()
      }
    }
    // A separator key means "done with this segment". Without it the buffer
    // just kept accumulating - typing 1/5/2026 sent "1", ignored the "/", then
    // appended the "5" to make month 15, which is not a month, so the field
    // committed nothing at all. Any of / - . is accepted regardless of the
    // format's own separator; nobody looks before they type.
    //
    // An EMPTY buffer means there is nothing to finish, so the key does
    // nothing rather than skipping a segment. That case is the common one, not
    // an edge: a full-width segment auto-advances on its last digit, so in
    // "08/20/2026" every separator arrives just after the move it would
    // otherwise repeat — and a repeat lands the day's digits in the year.
    advanceSegment() {
      if digitBuffer == "" { return }
      flushSegment()
      if activeSegment < 2 { activeSegment = activeSegment + 1 }
    }
    // Backspace takes back the digit you just typed. Now that pending digits
    // are visible (see seg0Text), a mistype is something you can SEE, and the
    // only reasonable expectation is to be able to delete it. An already-empty
    // buffer steps back to the previous segment instead.
    //
    // On a `clearable` field, Backspace or Delete on a segment that holds
    // something (and nothing pending) erases that segment instead: it shows
    // its mask again, and the next Backspace steps back as above. Leaving the
    // field with the date erased sends the clear (commitSegments). A field
    // that does not opt in has no way to lose its date, as before.
    backspaceSegment() {
      if digitBuffer != "" {
        digitBuffer = digitBuffer.slice(0, digitBuffer.length - 1)
        return
      }
      if clearable == true {
        let segType = segments[activeSegment]
        let held = segType == 'month' ? monthTyped : (segType == 'day' ? dayTyped : yearTyped)
        if held {
          if segType == 'month' { monthTyped = false }
          if segType == 'day' { dayTyped = false }
          if segType == 'year' { yearTyped = false }
          dirty = true
          return
        }
      }
      if activeSegment > 0 { activeSegment = activeSegment - 1 }
    }
    handleDigit(key) {
      if key >= "0" && key <= "9" {
        digitBuffer = digitBuffer + key
        let segType = segments[activeSegment]
        let n = parseInt(digitBuffer)
        // Advance as soon as no further digit could change the answer: a
        // segment at full width, a month starting 2-9, or a day starting 4-9.
        let full = segType == 'year' ? digitBuffer.length >= 4 : digitBuffer.length >= 2
        let leadMonth = segType == 'month' && digitBuffer.length == 1 && n >= 2
        let leadDay = segType == 'day' && digitBuffer.length == 1 && n >= 4
        if full || leadMonth || leadDay {
          advanceSegment()
        }
      }
    }
    // Enter commits a date the field holds, and is the field's alone either
    // way (Vector #5035). Handled and then let go, it also reached every
    // ancestor's key handler: a dialog's default action, a workbench's keys,
    // which is how Enter in a date took a reviewer out of the review.
    //
    // A half-typed date is NOT thrown away here, as blur throws it away: the
    // user is still in the field, so the digits stay on screen and typing
    // goes on where it was. Discarding left an empty field reading MM/DD/YYYY
    // after Enter, which reads as the date having been cleared. Only a buffer
    // that is the date's LAST missing part is applied, so "11/10/26" + Enter
    // commits 2026 while "11/1" + Enter leaves the 1 open for the 0.
    enterSegments(event) {
      consumeKey(event)
      let segType = segments[activeSegment]
      let othersTyped = segType == 'month' ? (dayTyped && yearTyped) : (segType == 'day' ? (monthTyped && yearTyped) : (monthTyped && dayTyped))
      if digitBuffer != "" && othersTyped { applyBuffer() }
      if segmentsComplete == true {
        commitSegments()
        return
      }
      // A clearable date erased segment by segment: Enter means "that's it".
      if userErased && segmentsErased { commitSegments() }
    }
    commitSegments() {
      // Flush the half-typed segment first: blurring or tabbing out of a field
      // visibly showing "1" for the month has to commit January, not drop it.
      applyBuffer()
      // Same rule as emitBuffer: an incomplete entry is discarded rather than
      // completed from the prefill. Blur is where that mattered most — tabbing
      // out of a field showing "03" used to commit today's day and year.
      if segmentsComplete == true {
        // Never emit an out-of-range year (defends against a corrupt incoming
        // `value` parsed back into segYear). Clamp into the supported window
        // rather than emitting e.g. 0710 downstream.
        let safeYear = segYear < 1900 ? 1900 : (segYear > 2200 ? 2200 : segYear)
        emit("change", formatDateOutput(safeYear, segMonth - 1, segDay, format))
      } else {
        // A clearable field left with its date partly or wholly erased sends
        // the clear (0.15.0). Dropping the edit put the old date back on
        // screen, though the user had taken it away; the field and the value
        // now agree on empty. Without `clearable` a held date cannot be
        // erased, so this only ever drops a half-typed new one, as before.
        if userErased { emit("change", "") }
      }
      activeSegment = -1
      editing = false
      userArmed = false
      dirty = false
      monthTyped = false
      dayTyped = false
      yearTyped = false
      digitBuffer = ""
    }
    // escapeSegments / escapePopup — the two ways this picker consumes Escape,
    // each cancelling the key only when it actually did something. Anything
    // else has to travel on: the dialog around the picker is usually what the
    // user meant to dismiss, and a control that swallows Escape unconditionally
    // is a black hole no dialog can be closed from.
    //
    // preventDefault alone does NOT hold the key here. Modal installs its
    // dismiss listener on `document` and never consults defaultPrevented, so a
    // merely-prevented Escape still bubbles all the way out and closes the
    // dialog — which is how backing out of the year grid used to take the
    // whole modal with it. Stopping propagation is the part that does the work.
    consumeKey(event) {
      event.preventDefault()
      event.stopPropagation()
    }
    // Escape with the calendar open backs out ONE layer at a time: the
    // month/year chooser returns to the day grid, the day grid closes the
    // calendar, and only a closed calendar lets the key reach the dialog.
    escapePopup(event) {
      if popupView != 0 {
        popupView = 0
        consumeKey(event)
        return
      }
      if open == true {
        consumeKey(event)
        close()
      }
    }
    // Abandoning the segment edit. Consumes when there is an edit to abandon —
    // the user armed the segments deliberately, changed one, or has digits
    // pending. Segments armed by focus alone with nothing typed are NOT an
    // edit: closing the calendar hands focus back to the field, which re-arms
    // them, and consuming there left the Escape ladder unable to reach the
    // dialog at all.
    escapeSegments(event) {
      if userArmed == false && dirty == false && digitBuffer == "" {
        escapePopup(event)
        return
      }
      consumeKey(event)
      cancelSegments()
    }
    // The clear button (0.15.0). Drops any edit in progress, closes the
    // calendar, sends '' and hands focus back to the field: the button hides
    // once the date is gone, and focus must not fall to the page. The field's
    // blur cleared refocusField, so this is a fresh false->true edge.
    clearDate() {
      if disabled == true { return }
      cancelSegments()
      open = false
      popupView = 0
      emit("change", "")
      refocusField = true
    }
    // focus-out arrives before the focus-in of wherever focus goes next, so
    // the leave waits for that to run: inside the field it sets focusWithin
    // again and nothing happens. Outside, the edit is committed as a blur of
    // the field commits it (a half-typed date is discarded), and the
    // highlight goes.
    fieldFocusOut() {
      focusWithin = false
      delay("dpLeave", 0) {
        if focusWithin == false { leaveField() }
      }
    }
    leaveField() {
      if editing == true { commitSegments() }
      activeSegment = -1
    }
    cancelSegments() {
      activeSegment = -1
      editing = false
      userArmed = false
      dirty = false
      monthTyped = false
      dayTyped = false
      yearTyped = false
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
        refocusField = true
      }
    }
    valueChanged() {
      closeAfterPick()
      followValue()
    }
    // The host owns `value`, even while the field is being typed in (Vector
    // I-4379). The segments are this picker's copy of the date during an
    // edit, and blur commits them, so a host change they did not take used to
    // be undone: a form reset or a Clear button that left focus here kept
    // showing the old date, and blur sent it back, refilling the cleared
    // field. Not editing, nothing is held: the field reads `value` itself.
    //
    // The picker emits '' only from a clearable field's clear (clearDate,
    // or commitSegments), and both have left editing by the time it comes
    // back, so an empty value met here comes from the host. A date it
    // emitted itself comes back equal to the segments and
    // changes nothing (emit reaches the host synchronously, so no newer
    // keystroke can be waiting in digitBuffer behind it).
    followValue() {
      if editing == false { return }
      if value == "" {
        // As activateSegments leaves an empty field: today's prefill, masked,
        // nothing typed or pending, so blur has nothing to send. Typing
        // starts again at the first segment.
        let today = todayParts()
        segYear = today.year
        segMonth = today.month + 1
        segDay = today.day
        monthTyped = false
        dayTyped = false
        yearTyped = false
        digitBuffer = ""
        dirty = false
        activeSegment = 0
        return
      }
      let parsed = parseDateInput(value, format)
      if parsed == null { return }
      if segmentsComplete && parsed.year == segYear && parsed.month + 1 == segMonth && parsed.day == segDay { return }
      segYear = parsed.year
      segMonth = parsed.month + 1
      segDay = parsed.day
      monthTyped = true
      dayTyped = true
      yearTyped = true
      digitBuffer = ""
    }
  }

  block {
    layout: vertical, gap: spacing.1
    // `position: relative` kept for legacy reasons; no longer needed for
    // the calendar popup (which now uses anchor:'bottom' → position:fixed
    // via positionDropdown, escaping any overflow ancestors).
    position: relative

    // Escape fallback for focus sitting on a part of the picker with no handler
    // of its own — the calendar toggle button, or a chooser button the focus
    // binding could not reach because its view was still hidden when the write
    // was scheduled. Everything that DOES consume Escape stops propagation, so
    // this only ever runs when nothing else did.
    on key-down(event): {
      if event.key == "Escape" {
        escapePopup(event)
      }
    }

    // Label
    block {
      visibility: label != ""
      text(label) { style: type.label-sm-strong, color: semantic.text-secondary }
    }

    // Trigger — styled to match TextInput.spec
    // No role here: the combobox is the date field inside, the node that takes
    // focus and carries the name (Vector I-1142).
    block {
      layout: horizontal, align: triggerAlign, gap: 0px
      min-height: triggerMinHeight
      // Ordering mirrors TextInput.spec exactly: error first, then tone, then
      // focus, then rest. The two match blocks are separate code — this trigger
      // is hand-styled to match rather than reusing TextInput — so they can
      // drift, and date-picker-typing.test.ts asserts this precedence here for
      // that reason.
      // `error` outranks `tone` here for the same reason it does on the border
      // below, and it has to be said in BOTH places or the precedence is only
      // half true: a field that is a setup gap AND a failed validation would
      // otherwise paint a red border over an amber fill — two states at once,
      // which is exactly the mixed signal the two-state split exists to avoid.
      background: match error {
        true -> semantic.destructive-bg,
        _ -> match tone {
          "warning" -> semantic.warning-bg,
          "danger"  -> semantic.destructive-bg,
          _ -> restBg
        }
      }
      border: match error {
        true -> token.input-borderWidth + " solid " + semantic.destructive,
        _ -> match tone {
          "warning"   -> token.input-borderWidth + " solid " + semantic.warning,
          "danger"    -> token.input-borderWidth + " solid " + semantic.destructive,
          "highlight" -> token.input-borderWidth + " solid " + semantic.interactive,
          _ -> restBorder
        }
      }
      shadow: match focused {
        true -> "0 0 0 3px " + token.input-focusRing,
        _ -> restShadow
      }
      border-radius: token.input-radius
      transition: transition.focus
      opacity: disabled ? 0.5 : 1
      overflow: hidden
      on mouse-enter: { hovered = true }
      on mouse-leave: { hovered = false }

      // Date input area
      block {
        grow: true
        // A column that centers its line: in "sm" the row stretches this
        // box to the floor, and the date stays in the middle of it. In "md"
        // the box is its content's height, so nothing moves.
        layout: vertical, justify: center
        padding: fieldPad
        cursor: "text"
        tabindex: "0"
        // The combobox is the tab stop, not the trigger wrapper around it: the
        // node a screen reader lands on carries the role, the name and the
        // error together. On a role-less node Chrome read the field as
        // "generic", where aria-invalid is deprecated in ARIA 1.2 (Vector
        // I-1142). The compiler binds aria-expanded to `open` on any
        // role:"combobox" block, so the open state moved here with the role.
        role: "combobox"
        aria-label: ariaLabel != "" ? ariaLabel : (label != "" ? label : "Date picker")
        aria-invalid: invalidAttr
        aria-describedby: describedBy
        focus: refocusField
        on focus: {
          focused = true
          if editing == false { armFromFocus() }
        }
        on blur: {
          focused = false
          // The refocus request is met once focus has been here and gone, so
          // the next request (a close, a clear) is a fresh edge for bindFocus.
          refocusField = false
          if editing == true { commitSegments() }
          // Whatever `editing` says: no segment stays lit once focus is gone
          // (Vector I-5562).
          activeSegment = -1
        }
        // A click on a segment focuses the SEGMENT (tabindex "-1"), and `blur`
        // does not bubble, so focus leaving from there never reached the
        // handler above: the date stayed armed and its last typed segment
        // kept the blue highlight (Vector I-5562). focus-in / focus-out
        // bubble; leaveField runs once focus has settled outside the field,
        // so a move between two segments, or onto the field itself, is not
        // a leave.
        on focus-in: { focusWithin = true }
        on focus-out: fieldFocusOut()
        on key-down(event): {
          if activeSegment >= 0 {
            match event.key {
              "ArrowLeft" -> prevSegment(),
              "ArrowRight" -> nextSegment(),
              "ArrowUp" -> incrementSegment(),
              "ArrowDown" -> decrementSegment(),
              "Enter" -> enterSegments(event),
              // escapeSegments, not cancelSegments: abandoning a half-typed
              // date CONSUMES the key, so it must say so. Neither match here
              // is a top-level statement of the handler — they sit inside the
              // if/else — so the compiler adds no preventDefault for any key
              // in this handler (see the Tab note below, which depends on
              // that). The cancel therefore has to be written by hand.
              "Escape" -> escapeSegments(event),
              // A separator commits the segment and moves on, so a date can be
              // typed the way it is spoken: 1/5/2026, not 01/05/2026.
              "/" -> advanceSegment(),
              "-" -> advanceSegment(),
              "." -> advanceSegment(),
              "Backspace" -> backspaceSegment(),
              "Delete" -> backspaceSegment(),
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
              // Conditional, unlike the segment branch above: with no segments
              // active there may also be no calendar open, and close() on an
              // already-closed picker is a no-op. Cancelling Escape there
              // would make this control a black hole — the dialog around it
              // could never be dismissed while focus sat on the field.
              "Escape" -> escapePopup(event),
              // Nothing to commit (the segments disarm after a commit while
              // focus stays here), but the key is still the field's: a
              // second Enter must not reach the dialog either (#5035).
              "Enter" -> consumeKey(event),
              "ArrowUp" -> activateSegments(),
              "ArrowDown" -> activateSegments(),
              _ -> {}
            }
          }
        }

        // Two arms, one per look (textArm). The field arm is the markup every
        // caller had before; the inline arm is the same with its texts at
        // inlineSize / inlineFace / inkColor. textArm never changes at a call
        // site, so one arm mounts.
        match textArm {
          "inline" -> {
            // Segments with no padding of their own: the date reads as it
            // prints, 11/03/2026, not 11 / 03 / 2026.
            // Segmented date display (when editing segments, or when there is no
            // placeholder to show)
            block {
              visibility: !showPlaceholder
              layout: horizontal, align: center, gap: 0px

              // Segment 0 — tabindex:"-1" removes it from the tab order so Tab
              // moves focus OUT of the picker rather than cycling through segments.
              // Click-to-focus still works; the parent block (tabindex:"0") is the
              // sole tab stop for the whole date-input area.
              block {
                padding-x: 0px
                cursor: "text"
                tabindex: "-1"
                background: activeSegment == 0 ? semantic.interactive : "transparent"
                border-radius: radius.sm
                on click: focusSegment(0)
                // A key-down of its own, though empty, keeps the compiler from making
                // Enter/Space click this block (Vector #5035). A click on a segment
                // focuses the segment, so every key after it is pressed here: Enter
                // clicked the segment, re-ran focusSegment and sent the click up to
                // every ancestor's click handler. The key still bubbles to the field's
                // key-down, which handles it. Same on every segment below.
                on key-down: {}
                text(seg0Text) {
                  style: type.body-md
                  font-size: inlineSize
                  font-family: inlineFace
                  color: activeSegment == 0 ? semantic.surface : (mask0 ? semantic.text-tertiary : inkColor)
                }
              }
              text(sep) { style: type.body-md, font-size: inlineSize, font-family: inlineFace, color: semantic.text-tertiary }
              // Segment 1
              block {
                padding-x: 0px
                cursor: "text"
                tabindex: "-1"
                background: activeSegment == 1 ? semantic.interactive : "transparent"
                border-radius: radius.sm
                on click: focusSegment(1)
                on key-down: {}
                text(seg1Text) {
                  style: type.body-md
                  font-size: inlineSize
                  font-family: inlineFace
                  color: activeSegment == 1 ? semantic.surface : (mask1 ? semantic.text-tertiary : inkColor)
                }
              }
              text(sep) { style: type.body-md, font-size: inlineSize, font-family: inlineFace, color: semantic.text-tertiary }
              // Segment 2
              block {
                padding-x: 0px
                cursor: "text"
                tabindex: "-1"
                background: activeSegment == 2 ? semantic.interactive : "transparent"
                border-radius: radius.sm
                on click: focusSegment(2)
                on key-down: {}
                text(seg2Text) {
                  style: type.body-md
                  font-size: inlineSize
                  font-family: inlineFace
                  color: activeSegment == 2 ? semantic.surface : (mask2 ? semantic.text-tertiary : inkColor)
                }
              }
            }

            // The placeholder, while the field is empty and not being typed into.
            // A click on it does what a click on the first segment does: on web,
            // focus has already armed the segments; where no keyboard reaches them
            // (Android) focusSegment opens the calendar. truncate: 1 ends a long
            // placeholder in "…" in a narrow field rather than running it under
            // the calendar button. tabindex "-1", as on the segments: the field
            // around it stays the one tab stop (a clickable block with none gets
            // tabindex "0"). pointer-events "none" on the web (0.11.3, found by a
            // Vector e2e on the Access tab): a press focuses the focusable node
            // under it, which was this one, and it hides the moment focus arms the
            // segments, so the browser moved focus to the page and every digit
            // typed after a click on an empty field went nowhere. Now the press
            // lands on the combobox around it, whose `on focus` arms the segments
            // and keeps the keys. iOS and Android do not read pointer-events, so a
            // tap there still runs focusSegment (Android: the calendar). It sits
            // AFTER the segments so the first tabindex "-1" node in the field is
            // still segment 0. The words are '' while hidden: text locators match
            // hidden nodes, and a placeholder kept under a set date collided with
            // any label or option that reads the same.
            block {
              visibility: showPlaceholder
              padding-x: 0px
              cursor: "text"
              tabindex: "-1"
              pointer-events: "none"
              on click: focusSegment(0)
              on key-down: {}
              text(placeholderShown) {
                style: type.body-md
                font-size: inlineSize
                color: semantic.text-tertiary
                truncate: 1
              }
            }
          },
          _ -> {
            // Segmented date display (when editing segments, or when there is no
            // placeholder to show)
            block {
              visibility: !showPlaceholder
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
                on key-down: {}
                text(seg0Text) {
                  style: type.body-md
                  color: activeSegment == 0 ? semantic.surface : (mask0 ? semantic.text-tertiary : semantic.text-primary)
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
                on key-down: {}
                text(seg1Text) {
                  style: type.body-md
                  color: activeSegment == 1 ? semantic.surface : (mask1 ? semantic.text-tertiary : semantic.text-primary)
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
                on key-down: {}
                text(seg2Text) {
                  style: type.body-md
                  color: activeSegment == 2 ? semantic.surface : (mask2 ? semantic.text-tertiary : semantic.text-primary)
                }
              }
            }

            // The placeholder, while the field is empty and not being typed into.
            // A click on it does what a click on the first segment does: on web,
            // focus has already armed the segments; where no keyboard reaches them
            // (Android) focusSegment opens the calendar. truncate: 1 ends a long
            // placeholder in "…" in a narrow field rather than running it under
            // the calendar button. tabindex "-1", as on the segments: the field
            // around it stays the one tab stop (a clickable block with none gets
            // tabindex "0"). pointer-events "none" on the web (0.11.3, found by a
            // Vector e2e on the Access tab): a press focuses the focusable node
            // under it, which was this one, and it hides the moment focus arms the
            // segments, so the browser moved focus to the page and every digit
            // typed after a click on an empty field went nowhere. Now the press
            // lands on the combobox around it, whose `on focus` arms the segments
            // and keeps the keys. iOS and Android do not read pointer-events, so a
            // tap there still runs focusSegment (Android: the calendar). It sits
            // AFTER the segments so the first tabindex "-1" node in the field is
            // still segment 0. The words are '' while hidden: text locators match
            // hidden nodes, and a placeholder kept under a set date collided with
            // any label or option that reads the same.
            block {
              visibility: showPlaceholder
              padding-x: 2px
              cursor: "text"
              tabindex: "-1"
              pointer-events: "none"
              on click: focusSegment(0)
              on key-down: {}
              text(placeholderShown) {
                style: type.body-md
                color: semantic.text-tertiary
                truncate: 1
              }
            }
          }
        }
      }

      // Clear button (0.15.0, `clearable`): only while the field holds a
      // date. No divider: it belongs to the date, not to the calendar.
      button {
        visibility: clearShown
        border: "none"
        background: "transparent"
        aria-label: "Clear the date"
        width: isInline ? '22px' : '28px'
        min-height: calMinHeight
        // The "inline" look shows it when it shows the calendar button.
        opacity: calOpacity
        layout: horizontal, justify: center, align: center
        border-radius: radius.sm
        cursor: "pointer"
        on hover { background: semantic.surface-raised }
        on click: clearDate()
        text("\u00D7") { style: type.body-md, color: semantic.text-tertiary }
      }

      // Divider + calendar button
      button {
        border: "none"
        background: "transparent"
        aria-label: "Open the calendar"
        width: calWidth
        min-height: calMinHeight
        layout: horizontal, justify: center, align: center
        border-left: calDivider
        opacity: calOpacity
        transition: transition.focus
        cursor: disabled ? "default" : "pointer"
        on hover { background: disabled ? "transparent" : semantic.surface-raised }
        on click: toggle()
        text("\uD83D\uDCC5") { style: type.body-md, color: semantic.text-tertiary }
      }
    }

    // Calendar popup — anchor:'bottom' invokes positionDropdown (position:fixed,
    // viewport-clamped), so the calendar escapes any overflow-clipping ancestor.
    // The trigger block is the previous sibling; positionDropdown reads its rect
    // and positions the popup below it. z-index:1000 keeps the position:fixed
    // popup above Vector's sticky page chrome (sticky headers/overlays live at
    // 100-300) and above the transparent dismiss-backdrop (z-index:999), while
    // staying below top toasts (9999). Modal-embedded pickers are bounded by the
    // modal's own stacking context, so this only affects same-root sticky chrome.
    block {
      visibility: open
      anchor: 'bottom'
      z-index: 1000
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

          button {
            border: "none"
            background: "transparent"
            aria-label: "Previous month"
            cursor: "pointer"
            padding: spacing.2
            on click: prevMonth()
            text("\u25C0") { style: type.body-md, color: semantic.interactive }
          }
          block {
            layout: horizontal, align: center, gap: spacing.1
            button {
              border: "none"
              background: "transparent"
              aria-label: "Choose a month"
              cursor: "pointer"
              padding-x: spacing.1
              border-radius: radius.sm
              on hover { background: semantic.surface-raised }
              on click: openMonthView()
              text(monthNames[viewMonth]) { style: type.body-md-strong, color: semantic.text-primary }
            }
            button {
              border: "none"
              background: "transparent"
              aria-label: "Choose a year"
              cursor: "pointer"
              padding-x: spacing.1
              border-radius: radius.sm
              on hover { background: semantic.surface-raised }
              on click: openYearView()
              text(viewYear + "") { style: type.body-md-strong, color: semantic.text-primary }
            }
          }
          button {
            border: "none"
            background: "transparent"
            aria-label: "Next month"
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

          each calendarWeekdays('min') as w {
            text(w) { style: type.caption, color: semantic.text-tertiary }
          }
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
              "Escape" -> escapePopup(event),
              "PageUp" -> focusPrevMonth(),
              "PageDown" -> focusNextMonth(),
              "Home" -> focusFirst(),
              "End" -> focusLast(),
              _ -> {}
            }
          }

          each calendarCells as cell {
            button {
              border: "none"
              background: "transparent"
              aria-label: cell.dateStr
              padding: spacing.1
              min-height: 32px
              layout: horizontal, justify: center, align: center
              border-radius: radius.sm
              cursor: "pointer"
              border: cell.day == focusedDay && cell.isCurrentMonth ? "2px solid " + semantic.interactive : "2px solid transparent"
              background: match cell.dateStr == valueISO {
                true -> semantic.interactive,
                _ -> cell.day == focusedDay && cell.isCurrentMonth ? semantic.surface-raised : "transparent"
              }
              tabindex: "-1"
              focus: cell.day == focusedDay && cell.isCurrentMonth && open && popupView == 0
              on hover { background: cell.dateStr == valueISO ? semantic.interactive-hover : semantic.surface-raised }
              on click: selectCell(cell.dateStr)

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
          button {
            border: "none"
            background: "transparent"
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
            // Escape backs out to the day grid rather than closing anything.
            on key-down(event): {
              if event.key == "Escape" {
                escapePopup(event)
              }
            }
            each monthShort as name, idx {
              button {
                border: "none"
                background: "transparent"
                padding: spacing.2
                layout: horizontal, justify: center, align: center
                border-radius: radius.sm
                cursor: "pointer"
                background: idx == viewMonth ? semantic.interactive : "transparent"
                // Opening the chooser hides the button that opened it, which
                // drops focus to the body — and a key pressed on the body is
                // a key this component never sees. Pull focus onto the current
                // month so the grid above can hear Escape.
                focus: idx == viewMonth && popupView == 1 && open
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
            button {
              border: "none"
              background: "transparent"
              aria-label: "Earlier years"
              cursor: "pointer"
              padding: spacing.2
              on click: prevDecade()
              text("◀") { style: type.body-md, color: semantic.interactive }
            }
            text(yearRangeLabel) { style: type.body-md-strong, color: semantic.text-primary }
            button {
              border: "none"
              background: "transparent"
              aria-label: "Later years"
              cursor: "pointer"
              padding: spacing.2
              on click: nextDecade()
              text("▶") { style: type.body-md, color: semantic.interactive }
            }
          }
          block {
            layout: grid, columns: "repeat(3, 1fr)", gap: spacing.1
            padding: spacing.2
            // Escape backs out to the day grid rather than closing anything.
            on key-down(event): {
              if event.key == "Escape" {
                escapePopup(event)
              }
            }
            each gridIndices as idx {
              button {
                border: "none"
                background: "transparent"
                padding: spacing.2
                layout: horizontal, justify: center, align: center
                border-radius: radius.sm
                cursor: "pointer"
                background: (yearGridStart + idx) == viewYear ? semantic.interactive : "transparent"
                // See the month grid: without this, focus is on a hidden button
                // and Escape goes straight past the picker to the dialog.
                focus: (yearGridStart + idx) == viewYear && popupView == 2 && open
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

    // Transparent full-screen backdrop: intercepts click-outside to dismiss the
    // calendar. Sits below the popup in z-index (999 < 1000) so day-cell clicks
    // still reach the popup, but above sticky page chrome (100-300). ESC key is
    // handled by the trigger's on key-down.
    block {
      visibility: open
      position: fixed
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 999
      // Explicit tabindex suppresses the synthetic tabindex="0" the compiler
      // adds to every click-handling block. Without it this invisible
      // full-screen element is a tab stop sitting in front of the whole page,
      // and Enter on it "clicks" the backdrop. It stays a block (not a button)
      // because it is not a control — it exists to swallow an outside click.
      tabindex: "-1"
      on click: close()
    }

    // Error caption — a live region that is always here (see errText above).
    // role alert (assertive), as TextInput and Vector's kit ErrorLine.
    block {
      id: msgId
      role: 'alert'
      aria-live: 'assertive'
      position: errPosition
      text(errWords) { style: type.caption, color: semantic.destructive }
    }

    // The same words while the line above waits out its empty moment,
    // painted in its place and aria-hidden (TextInput's stand-in).
    block {
      visibility: errStandInShown
      aria-hidden: 'true'
      text(errStandIn) { style: type.caption, color: semantic.destructive }
    }
  }
}
