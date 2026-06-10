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
// Outside-click dismissal — the dropdown carries `role="listbox"` so a
// host application can wire up its own outside-click → Escape dispatch
// (see e.g. the popup.js helper used by golf / vector). Spec's
// `overlay()` would handle this automatically but tends to collapse the
// surrounding layout when nested inside a vertical stack with siblings;
// the inline-block approach here is more predictable.
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
    }
    clearSelection() {
      emit("change", "")
      query = ""
      typing = false
      open = false
      highlightIndex = 0
    }
    moveDown() {
      if matchLen > 0 {
        highlightIndex = _wrapIndex(safeIndex, 1, matchLen)
        if !open { open = true }
      }
    }
    moveUp() {
      if matchLen > 0 {
        highlightIndex = _wrapIndex(safeIndex, -1, matchLen)
        if !open { open = true }
      }
    }
    selectHighlighted() {
      if open && matchLen > 0 && safeIndex < matchLen {
        pickOption(filteredOptions[safeIndex])
      }
    }
    closeDropdown() {
      open = false
      typing = false
      highlightIndex = 0
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
    // bubbling up from the wrapped textInput primitive.
    block {
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

    // Inline dropdown — push siblings down. The host application is
    // expected to lay this component out in a column-flex container that
    // tolerates inline expansion. Use `Select` instead if you need a
    // floating popup.
    block {
      visibility: open && matchLen > 0
      role: "listbox"
      data-autocomplete-popup: "true"
      background: token.select-bg
      border: token.input-borderWidth + " solid " + semantic.border
      border-radius: token.select-radius
      max-height: 240px
      overflow: auto
      shadow: "0 8px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)"
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
      visibility: open && typing && query != "" && matchLen == 0
      data-autocomplete-popup: "true"
      padding: spacing.2
      background: token.select-bg
      border: token.input-borderWidth + " solid " + semantic.border
      border-radius: token.select-radius
      shadow: "0 8px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)"
      text("No matches for {query}") { style: type.body-md, color: semantic.text-tertiary }
    }
  }
}
