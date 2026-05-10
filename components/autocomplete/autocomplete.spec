// Autocomplete — typing-driven combobox.
//
// A TextInput that opens an inline dropdown beneath itself filtered by
// what the user types. Use this instead of `Select(searchable: true)`
// when the option list is long enough that "click → popup → click search →
// type" is too many steps. The user just clicks the field and starts
// typing; matches appear as they go.
//
// Props
//   options:      [{ label, value }] — full list of options.
//   value:        string             — currently-selected `value`. The
//                                       component shows the matching
//                                       option's `label` when the input
//                                       is not being edited.
//   placeholder:  string             — empty-state placeholder.
//   error:        boolean            — when true, the input renders with
//                                       a destructive-tinted border.
//
// Events
//   change(v):    fires with the picked option's `value`. Emits `''`
//                 when the user clicks the inline Clear pill.
//
// Keyboard
//   ArrowDown / ArrowUp — move highlight (wraps).
//   Enter               — pick highlighted option.
//   Escape              — close dropdown without picking.
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
  disabled: boolean = false
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
    inputValue:     typing ? query : selectedLabel
    qLower:         query.toLowerCase()
    filteredOptions: typing && query != "" ? (safeOptions |> filter(o => o.label.toLowerCase().includes(qLower))) : safeOptions
    hasSelection:   selectedOption != null && !typing
    matchLen:       filteredOptions.length
    safeIndex:      matchLen > 0 && highlightIndex < matchLen ? highlightIndex : 0
  }

  @actions {
    handleInput(v) {
      if disabled { return }
      query = v
      typing = true
      open = v != ""
      highlightIndex = 0
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
        _ -> {}
      }

      block {
        grow: true
        TextInput(value: inputValue, placeholder: placeholder, error: error, disabled: disabled) {
          on change(v): handleInput(v)
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
