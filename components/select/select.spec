fn wrapIndex(index: number, delta: number, len: number) -> number {
  if len <= 0 { return 0 }
  return ((index + delta) % len + len) % len
}

component Select(options: array = [], value: string = "", placeholder: string = "Select...", searchable: boolean = false, disabled: boolean = false, label: string = "", clearable: boolean = false, clearLabel: string = "Clear selection", error: boolean = false, errorMessage: string = "") {
  @state {
    open: false
    query: ""
    highlightIndex: 0
    focused: false
  }

  @computed {
    safeOptions: options != null ? options : []
    filteredOptions: searchable && query != "" ? safeOptions.filter(o => o.label.toLowerCase().includes(query.toLowerCase())) : safeOptions
    selectedOption: safeOptions.find(o => o.value == value)
    displayText: selectedOption != null ? selectedOption.label : placeholder
    hasOptions: filteredOptions.length > 0
  }

  @actions {
    toggleOpen() {
      if disabled == false {
        open = open == false
        query = ""
        highlightIndex = 0
      }
    }
    openDropdown() {
      if disabled == false && open == false {
        open = true
        query = ""
        highlightIndex = 0
      }
    }
    closeDropdown() {
      open = false
      query = ""
    }
    selectOption(val) {
      emit("change", val)
      open = false
      query = ""
    }
    setQuery(v) {
      query = v
      highlightIndex = 0
    }
    moveHighlight(delta) {
      if filteredOptions.length > 0 {
        highlightIndex = wrapIndex(highlightIndex, delta, filteredOptions.length)
      }
    }
    selectHighlighted() {
      if filteredOptions.length > 0 && highlightIndex < filteredOptions.length {
        selectOption(filteredOptions[highlightIndex].value)
      }
    }
  }

  block {
    layout: vertical, gap: spacing.1

    // Label
    block {
      visibility: label != ""
      text(label) { style: type.label-sm, color: semantic.text-secondary }
    }

    // Trigger button
    block {
      layout: horizontal, justify: between, align: center
      padding: spacing.2
      min-height: 40px
      background: token.select-bg
      border: match error {
        true -> token.input-borderWidth + " solid " + semantic.destructive,
        _ -> match focused {
          true -> token.input-borderWidth + " solid " + token.input-focusBorder,
          _ -> token.input-borderWidth + " solid " + token.select-border
        }
      }
      shadow: match focused {
        true -> "0 0 0 3px " + token.input-focusRing,
        _ -> "none"
      }
      border-radius: token.select-radius
      cursor: disabled ? "not-allowed" : "pointer"
      opacity: disabled ? 0.5 : 1
      transition: transition.focus
      tabindex: "0"
      role: "combobox"
      aria-label: "Select"
      on hover { background: disabled ? token.select-bg : semantic.surface-raised }
      on click: toggleOpen()
      on focus: { focused = true }
      on blur: { focused = false }
      on key-down(event): {
        match event.key {
          "ArrowDown" -> open ? moveHighlight(1) : openDropdown(),
          "ArrowUp" -> open ? moveHighlight(-1) : openDropdown(),
          "Enter" -> open ? selectHighlighted() : toggleOpen(),
          "Escape" -> closeDropdown(),
          " " -> open ? selectHighlighted() : toggleOpen(),
          "Tab" -> closeDropdown(),
          _ -> {}
        }
      }

      text(displayText) {
        style: type.body-md
        color: selectedOption != null ? semantic.text-primary : semantic.text-tertiary
      }
      text("\u25BE") { style: type.caption, color: semantic.text-tertiary }
    }

    // Dropdown panel — fixed-position below the trigger via anchor:'bottom'.
    // positionDropdown sets position:fixed with viewport-relative coords, so
    // the panel escapes any overflow:hidden|auto ancestor (data grids,
    // scrollable cards, modal bodies that scroll). The previous
    // overlay(anchor:"parent") rendered this panel position:absolute and
    // flex-centered over the ~40px trigger, so a clipping ancestor cut off its
    // top half — see MultiSelect, which uses this same pattern.
    // popup.js dispatches Escape to the combobox trigger on outside click; the
    // sibling backdrop below catches the remaining clicks.
      block {
        visibility: open
        anchor: 'bottom'
        padding: spacing.1
        max-height: 240px
        overflow: auto
        background: token.select-bg
        border: token.input-borderWidth + " solid " + semantic.border
        border-radius: token.select-radius
        shadow: "0 4px 16px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04)"
        layout: vertical
        role: "listbox"
        z-index: 200

        // Search input
        block {
          visibility: searchable
          padding: spacing.2
          border-bottom: borders.default
          TextInput(placeholder: "Search...", value: query) {
            on change(v): setQuery(v)
          }
        }

        // Clear row — shown when `clearable` is set and the field has a
        // non-empty value. Clicking it emits change("") so the caller can
        // reset the field. Lives inside the dropdown so the trigger button's
        // layout doesn't shift when a value is picked. Bottom border acts
        // as the divider between Clear and the options list.
        block {
          visibility: clearable && value != ""
          padding: spacing.2
          border-radius: radius.sm
          border-bottom: borders.default
          cursor: "pointer"
          on hover { background: token.select-optionHover }
          on click: selectOption("")

          block {
            layout: horizontal, gap: spacing.1, align: center
            text("✕") { style: type.body-md, color: semantic.text-tertiary }
            text(clearLabel) { style: type.body-md, color: semantic.text-tertiary, weight: 500 }
          }
        }

        // Thin divider after the Clear row — bottom border on the Clear
        // block itself instead of a sibling div, since the Spec parser
        // doesn't accept margin-top/-bottom shortcuts (only `margin:`).

        // Options list
        block {
          visibility: hasOptions
          layout: vertical

          each filteredOptions as option, idx {
            block {
              padding: spacing.2
              border-radius: radius.sm
              cursor: "pointer"
              background: match idx == highlightIndex {
                true -> token.select-optionHover,
                _ -> match option.value == value {
                  true -> token.select-optionSelected,
                  _ -> "transparent"
                }
              }
              scroll-to: idx == highlightIndex
              on hover { background: token.select-optionHover }
              on click: selectOption(option.value)

              text(option.label) {
                style: type.body-md
                color: option.value == value ? semantic.interactive : semantic.text-primary
                weight: option.value == value ? 500 : 400
              }
            }
          }
        }

        // Empty state
        block {
          visibility: hasOptions == false
          padding: spacing.3
          layout: horizontal, justify: center
          text("No options") { style: type.body-md, color: semantic.text-tertiary }
        }
      }

      // Outside-click backdrop — a fixed-position fullscreen sibling sitting
      // BELOW the panel in z-order (190 < 200) so the panel still wins clicks.
      // Placed AFTER the panel so the panel's `anchor: 'bottom'` resolves to
      // the trigger (its previous sibling), not the backdrop. Without this a
      // previously opened dropdown stays open and the next click on the same
      // trigger just toggles it closed (the "two clicks to reopen" bug).
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

    // Error message
    block {
      visibility: error == true
      text(errorMessage) {
        style: type.caption
        color: semantic.destructive
      }
    }
  }
}
