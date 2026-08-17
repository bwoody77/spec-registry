// Autocomplete — typing-driven combobox.
//
// A TextInput that opens an inline dropdown beneath itself filtered by
// what the user types. Use this instead of `Select(searchable: true)`
// when the option list is long enough that "click → popup → click search →
// type" is too many steps. The user just clicks the field and starts
// typing; matches appear as they go.
//
// Two activation modes (toggled by `openOnFocus`):
//
//   • openOnFocus: false (default) — dropdown opens only after the user
//     starts typing. Best for very long lists where popping a giant
//     menu on every focus would be noisy. Pairs naturally with server-
//     side filtering (caller recomputes `options` from a debounced
//     query against the bound `value`).
//
//   • openOnFocus: true — clicking/focusing the field opens the dropdown
//     immediately with all options visible; typing then narrows the
//     list. This is the "dropdown that also accepts typing" UX — the
//     right choice for short bounded lists (aircraft, instructors,
//     time slots) where users often want to browse without typing.
//     This mode also paints Select's chevron-down caret INSIDE the field
//     at its right edge, so the field advertises the menu it drops;
//     clicking the caret focuses the input and opens it.
//     Typing-driven mode (the default) deliberately has no caret — there
//     is no menu to promise until the user has typed.
//
// Two value modes (toggled by `freeText`):
//
//   • Strict (default) — value MUST come from the options list. The input
//     shows the matching option's `label` when not being edited; on blur
//     the typed text reverts to the selected label. Internal filter trims
//     `options` against the typed query.
//
//   • freeText: true — value is whatever the user types. Suggestions are
//     hints — typing "06A2" (not in the list) is preserved and emitted
//     as-is. The caller is responsible for filtering / scoring `options`
//     externally (typically by recomputing them from the bound `value`
//     signal); the component does NO internal filter in this mode, and
//     no client-side revert on blur. Use this for ICAO/airport pickers,
//     tag inputs, or any field where a free string is sometimes valid.
//
// Props
//   options:      [{ label, value }] — list of suggestions.
//   value:        string             — currently-selected `value`. In
//                                       strict mode, the input shows the
//                                       matching option's `label` while
//                                       idle; in freeText mode the input
//                                       just shows `value` directly.
//   placeholder:  string             — empty-state placeholder.
//   error:        boolean            — destructive-tinted border.
//   freeText:     boolean            — see modes above. Default false.
//
// Events
//   change(v):    in strict mode, fires with the picked option's `value`
//                 (or `''` on Clear). In freeText mode, fires on every
//                 keystroke with the typed text, AND on pick with the
//                 selected option's value.
//
// Keyboard
//   ArrowDown / ArrowUp — move highlight (wraps).
//   Enter               — commits when the user has arrow-keyed a highlight,
//                         when the typed text exactly matches an option label,
//                         or (strict mode) when typing has narrowed the list to
//                         a single option. Otherwise it just closes: Enter on an
//                         untouched field must never commit whichever option
//                         happens to sit at the default highlight position.
//   Escape              — close dropdown without picking.
//   Tab                 — in strict mode, commits the typed text when it
//                         exactly matches an option label (case-insensitive);
//                         otherwise reverts to the selected label so the
//                         field never displays an uncommitted value. In
//                         freeText mode it just closes the dropdown.
//
// Floating dropdown — the suggestion panel is anchored to the input row via
// `anchor: 'bottom'`, which positionDropdown renders position:fixed with
// viewport-relative coords. It therefore floats OVER the page (no sibling
// push-down) and escapes any overflow:hidden|auto ancestor (scrollable cards,
// data grids, modal bodies) — same pattern as Select / MultiSelect.
// positionDropdown only restyles the panel in place (no reparenting), so it
// stays a child of this component's wrapper.
//
// Outside-click dismissal — the panel carries `role="listbox"` and
// `data-autocomplete-popup` so a host application can wire its own
// outside-click → Escape dispatch (see e.g. the popup.js helper used by golf /
// vector). Such helpers must detect visibility via offsetHeight rather than
// offsetParent: a position:fixed element reports offsetParent === null even
// when fully visible. Spec's `overlay()` would auto-dismiss but tends to
// collapse the surrounding layout when nested in a vertical stack; the
// anchored-panel approach here is more predictable.
//
// Styling — uses semantic + token color names so it adapts to themes.
// Override `font` and `border` tokens via the host's @theme to reskin.

fn _wrapIndex(index: number, delta: number, len: number) -> number {
  if len <= 0 { return 0 }
  return ((index + delta) % len + len) % len
}

component Autocomplete(
  options: array = [],
  value: string = "",
  placeholder: string = "Type to search…",
  error: boolean = false,
  errorMessage: string = "",
  disabled: boolean = false,
  freeText: boolean = false,
  openOnFocus: boolean = false,
  // Supplied by the compiler from the adjacent visible label; forwarded
  // to the wrapped TextInput, which is the element that needs the name.
  ariaLabel: string = ""
) {
  @state {
    query: ""
    open: false
    typing: false
    highlightIndex: 0
    // True only once the user has actively moved the highlight with the
    // arrow keys. Distinguishes "option 0 is highlighted because it's the
    // default resting position" from "the user chose this option". Enter
    // must NOT silently commit the default-position option (that booked
    // phantom 6:00 AM flights — the first time-slot option — when a user
    // pressed Enter on an empty/partial field). Reset on focus / fresh
    // input so a stale highlight can't leak across edits.
    userHighlighted: false
  }

  @computed {
    safeOptions:    options != null ? options : []
    selectedOption: safeOptions |> find(o => o.value == value)
    selectedLabel:  selectedOption != null ? selectedOption.label : ""

    // In strict mode the input shows the option label while idle; in
    // freeText mode it shows the raw `value` (typed by the user) since
    // there's no canonical label to revert to. While typing, both modes
    // show the in-progress `query` string.
    inputValue:     typing ? query : (freeText ? value : selectedLabel)

    qLower:         query.toLowerCase()

    // Strict mode: filter client-side so the dropdown narrows as the user
    // types. freeText mode: the CALLER controls `options` (typically by
    // recomputing matches from the bound `value` signal with its own
    // scoring), so don't filter again — we'd just chew the caller's
    // pre-ranked list.
    filteredOptions: freeText
                      ? safeOptions
                      : (typing && query != "" ? (safeOptions |> filter(o => o.label.toLowerCase().includes(qLower))) : safeOptions)

    // freeText has no "selected option" concept — the value IS the typed
    // string. We still hide the Clear pill while the dropdown is open in
    // freeText, since there's no resting "selected" state to clear FROM.
    hasSelection:   freeText ? (value != "" && !typing) : (selectedOption != null && !typing)

    // Dropdown caret, handed to the wrapped TextInput so it paints INSIDE the
    // field's border — the same mark, size and tone Select uses, so a browse-
    // style Autocomplete reads as a sibling of the Selects beside it rather
    // than as a plain text field that mysteriously drops a menu. It used to be
    // a "▾" text glyph in a block of its own OUTSIDE the input, which is what
    // made it look bolted on next to the field instead of part of it.
    //
    // Only in openOnFocus mode. Without it there IS no menu to promise until
    // the user has typed something, and a permanent caret on a typing-driven
    // search field would advertise a dropdown that clicking cannot produce.
    // "" is the TextInput's "no trailing icon" value.
    //
    // It needs no click handler of its own any more: TextInput's field
    // container is a <label> wrapping the input, so a click on the caret is
    // delegated to the input, which fires the focus event this component
    // already listens to. That is strictly better than the old block's
    // `on click: handleFocus()` — the caret press now really does put the
    // caret in the field, instead of opening a menu the user then had to
    // click again to type into.
    caretIcon:      openOnFocus && !disabled ? "chevron-down" : ""

    matchLen:       filteredOptions.length
    safeIndex:      matchLen > 0 && highlightIndex < matchLen ? highlightIndex : 0
    // The floating panel is shown when there are matches to list OR a typed
    // query yielded none (so the "no matches" hint can render). Both the
    // options list and the empty hint live inside this single anchored panel.
    showEmptyHint:  open && typing && query != "" && matchLen == 0
    showPanel:      open && (matchLen > 0 || showEmptyHint)
  }

  @actions {
    handleFocus() {
      if disabled { return }
      if openOnFocus {
        open = true
        // Stay in "not typing" mode so the input shows the selected label
        // (strict) or the raw value (freeText) until the user actually
        // types. filteredOptions reduces to safeOptions when query == "",
        // so all options are visible on focus.
        typing = false
        query = ""
        highlightIndex = 0
        userHighlighted = false
      }
    }
    handleInput(v) {
      if disabled { return }
      query = v
      typing = true
      // openOnFocus: stay open while the field has focus; v != "" still
      // toggles open for the non-focus path.
      open = openOnFocus || v != ""
      highlightIndex = 0
      userHighlighted = false
      // freeText: propagate every keystroke so the caller's signal tracks
      // what the user is typing (and can refresh `options` from it).
      // Strict: stay silent until pickOption / clearSelection.
      if freeText { emit("change", v) }
    }
    pickOption(opt) {
      emit("change", opt.value)
      query = ""
      typing = false
      open = false
      highlightIndex = 0
      userHighlighted = false
    }
    clearSelection() {
      emit("change", "")
      query = ""
      typing = false
      open = false
      highlightIndex = 0
      userHighlighted = false
    }
    moveDown() {
      if matchLen > 0 {
        highlightIndex = _wrapIndex(safeIndex, 1, matchLen)
        userHighlighted = true
        if !open { open = true }
      }
    }
    moveUp() {
      if matchLen > 0 {
        highlightIndex = _wrapIndex(safeIndex, -1, matchLen)
        userHighlighted = true
        if !open { open = true }
      }
    }
    // Enter handling. We commit an option when the user has (a) actively
    // highlighted it with the arrow keys, (b) typed a query that EXACTLY
    // matches an option's label, or (c) typed a query that narrowed the list
    // to a SINGLE option. Pressing Enter on an empty / partial field where
    // option 0 just happens to sit at the default highlight position must NOT
    // silently pick it — in freeText mode we keep the typed value and just
    // close the dropdown; in strict mode we close without committing a wrong
    // selection.
    selectHighlighted() {
      if open && userHighlighted && matchLen > 0 && safeIndex < matchLen {
        pickOption(filteredOptions[safeIndex])
        return
      }
      let q = query.trim().toLowerCase()
      let exactHit = q != "" ? (safeOptions |> find(o => o.label.toLowerCase() == q)) : null
      if exactHit != null {
        pickOption(exactHit)
        return
      }
      // Sole surviving match — standard combobox behaviour, and not the
      // ambiguity the default-highlight guard exists for: the user's own
      // typing is what singled this option out, so Enter commits it rather
      // than forcing a reach for the mouse. STRICT MODE ONLY: freeText does
      // no internal filtering (the caller owns `options`), so one option
      // there is a suggestion, not a match, and must never overwrite the
      // typed value.
      if !freeText && open && typing && q != "" && matchLen == 1 {
        pickOption(filteredOptions[0])
        return
      }
      // No user-chosen highlight, no exact match, no sole match: don't snap to
      // the default option. freeText keeps the typed value; both modes close.
      closeDropdown()
    }
    closeDropdown() {
      open = false
      typing = false
      highlightIndex = 0
      userHighlighted = false
    }
    // escapeKey — close the suggestion list AND say so.
    //
    // The registry's Escape contract is "cancel it exactly when you consumed
    // it". This component had the under-capturing half of that wrong: it
    // closed the list on Escape but never called preventDefault, so a dialog
    // or drawer around it also closed. One keystroke, two levels destroyed.
    //
    // The cancel has to be written by hand here. The compiler's automatic
    // preventDefault only applies to a `match event.key` that is a top-level
    // STATEMENT of the handler (ast-to-ir.ts checks Array.isArray on the
    // handler action); this handler's action is a bare `match` expression, so
    // no key gets one. That is deliberate and worth preserving — wrapping the
    // match in a block would silently start cancelling Enter too, and Enter
    // with nothing highlighted must stay available to submit the surrounding
    // form.
    escapeKey(event) {
      if !open {
        return
      }
      event.preventDefault()
      closeDropdown()
    }
    // Tab-away while typing. Strict mode previously left the typed text
    // VISIBLE while the bound value silently kept its old selection — the
    // field lied (forms then submitted the stale value). Tab is handled in
    // key-down (it fires before blur, so this can't race the dropdown's
    // click-to-pick the way an on-blur handler would). Note: NOT
    // preventDefault'd — focus still moves to the next field.
    handleTabAway() {
      if !typing { return }
      if freeText {
        closeDropdown()
      } else {
        let q = query.trim().toLowerCase()
        let exactHit = safeOptions |> find(o => o.label.toLowerCase() == q)
        if exactHit != null {
          pickOption(exactHit)
        } else {
          closeDropdown()
        }
      }
    }
  }

  block {
    layout: vertical, gap: spacing.1
    opacity: match disabled { true -> 0.5, _ -> 1 }

    // Input row — listens for arrow / Enter / Escape via key-down
    // bubbling up from the wrapped textInput primitive. Also the anchor the
    // floating panel positions against (its immediate next sibling).
    block {
      layout: horizontal, gap: spacing.1, align: center
      on key-down(event): match event.key {
        "ArrowDown" -> moveDown(),
        "ArrowUp"   -> moveUp(),
        "Enter"     -> selectHighlighted(),
        "Escape"    -> escapeKey(event),
        "Tab"       -> handleTabAway(),
        _ -> {}
      }

      block {
        grow: true
        TextInput(value: inputValue, placeholder: placeholder, error: error, errorMessage: errorMessage, disabled: disabled, ariaLabel: ariaLabel, trailingIcon: caretIcon) {
          on change(v): handleInput(v)
          on focus: handleFocus()
        }
      }

      // Inline "Clear" pill — only visible when something's selected and
      // the field isn't being edited. Tapping it clears the selection.
      block {
        visibility: hasSelection && !disabled
        padding-y: spacing.1
        padding-x: spacing.2
        border-radius: radius.sm
        background: token.select-bg
        border: borders.default
        cursor: "pointer"
        on click: clearSelection()
        on hover { background: semantic.surface-raised }
        text("Clear") { style: type.label-sm, color: semantic.text-secondary, weight: 600 }
      }

      // The dropdown caret used to be a third block here, outside the field.
      // It now rides on the TextInput as `trailingIcon: caretIcon` (see the
      // caretIcon computed) so it paints inside the field's border, which is
      // where Select has always drawn it.
    }

    // Floating suggestion panel — anchored to the input row above, rendered
    // position:fixed by positionDropdown so it floats over the page instead of
    // pushing siblings down, and escapes overflow:hidden|auto ancestors. Holds
    // both the options list and the empty-state hint.
    block {
      visibility: showPanel
      anchor: 'bottom'
      z-index: 200
      role: "listbox"
      data-autocomplete-popup: "true"
      background: token.select-bg
      border: token.input-borderWidth + " solid " + semantic.border
      border-radius: token.select-radius
      max-height: 240px
      overflow: auto
      shadow: "0 8px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)"
      layout: vertical

      // Options list
      block {
        visibility: matchLen > 0
        layout: vertical

        each filteredOptions as opt, idx {
          block {
            padding: spacing.2
            cursor: "pointer"
            background: match idx == safeIndex {
              true -> token.select-optionHover,
              _ -> "transparent"
            }
            scroll-to: idx == safeIndex
            // role="option" is the compiler's; which row is current is ours.
            aria-selected: idx == safeIndex
            on click: pickOption(opt)
            on hover { background: token.select-optionHover }
            text(opt.label) {
              style: type.body-md
              color: idx == safeIndex ? semantic.interactive : semantic.text-primary
              weight: idx == safeIndex ? 700 : 500
            }
          }
        }
      }

      // Empty-state hint while typing
      block {
        visibility: showEmptyHint
        padding: spacing.2
        text("No matches for {query}") { style: type.body-md, color: semantic.text-tertiary }
      }
    }
  }
}
