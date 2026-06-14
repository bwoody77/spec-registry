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
//   Enter               — pick highlighted option (if any).
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
// data grids, modal bodies) — same pattern as Select / MultiSelect. A
// fullscreen backdrop sibling (placed AFTER the panel so the panel's
// `anchor:'bottom'` still resolves to the input row, its previous sibling)
// handles outside-click dismissal. The input row is elevated above the
// backdrop while open so the user can keep clicking into the field to edit.
//
// (popup.js's outside-click helper relies on offsetParent, which is null for
// position:fixed elements, so it no longer governs this dropdown — the
// backdrop does. The `data-autocomplete-popup` / `role="listbox"` attributes
// are retained for back-compat and a11y.)
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
  disabled: boolean = false,
  freeText: boolean = false,
  openOnFocus: boolean = false
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
    matchLen:       filteredOptions.length
    safeIndex:      matchLen > 0 && highlightIndex < matchLen ? highlightIndex : 0
    // The floating panel is shown when there are matches to list OR a typed
    // query yielded none (so the "no matches" hint can render). Both the
    // options list and the empty hint live inside this single anchored panel.
    showEmptyHint:  open && typing && query != "" && matchLen == 0
    showPanel:      open && (matchLen > 0 || showEmptyHint)
    // Lift the input row above the outside-click backdrop (190) while open so
    // the field stays clickable; drop back to 1 when closed so it never sits
    // over unrelated page chrome.
    inputZ:         open ? 201 : 1
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
    // Enter handling. We only commit an option when the user has either
    // (a) actively highlighted it with the arrow keys, or (b) typed a query
    // that EXACTLY matches an option's label. Pressing Enter on an empty /
    // partial field where option 0 just happens to sit at the default
    // highlight position must NOT silently pick it — in freeText mode we
    // keep the typed value and just close the dropdown; in strict mode we
    // close without committing a wrong selection.
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
      // No user-chosen highlight and no exact-match query: don't snap to the
      // default option. freeText keeps the typed value; both modes close.
      closeDropdown()
    }
    closeDropdown() {
      open = false
      typing = false
      highlightIndex = 0
      userHighlighted = false
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
    // floating panel positions against (its immediate next sibling). Elevated
    // above the outside-click backdrop while open so the field stays clickable.
    block {
      position: 'relative'
      z-index: inputZ
      layout: horizontal, gap: spacing.1, align: center
      on key-down(event): match event.key {
        "ArrowDown" -> moveDown(),
        "ArrowUp"   -> moveUp(),
        "Enter"     -> selectHighlighted(),
        "Escape"    -> closeDropdown(),
        "Tab"       -> handleTabAway(),
        _ -> {}
      }

      block {
        grow: true
        TextInput(value: inputValue, placeholder: placeholder, error: error, disabled: disabled) {
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

    // Outside-click backdrop — fullscreen fixed sibling BELOW the panel in
    // z-order (190 < 200) and placed AFTER it so the panel's `anchor:'bottom'`
    // resolves to the input row (its previous sibling), not the backdrop.
    // Closes the dropdown on any click outside the (elevated) input + panel.
    block {
      visibility: open
      position: 'fixed'
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 190
      on click: closeDropdown()
    }
  }
}
