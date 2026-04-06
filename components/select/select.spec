@extern { wrapIndex } from "@spec/components/nav-utils.js"

component Select(options: array = [], value: string = "", placeholder: string = "Select...", searchable: boolean = false, disabled: boolean = false, label: string = "") {
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
    position: "relative"

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
      border: match focused {
        true -> token.input-borderWidth + " solid " + token.input-focusBorder,
        _ -> token.input-borderWidth + " solid " + token.select-border
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

    // Backdrop — catches outside clicks
    block {
      visibility: open == true
      position: "fixed"
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 999
      on click: closeDropdown()
    }

    // Dropdown panel
    block {
      visibility: open == true
      position: "absolute"
      top: 100%
      left: 0px
      right: 0px
      z-index: 1000
      margin: spacing.1
      padding: spacing.1
      max-height: 240px
      overflow: auto
      background: token.select-bg
      border: token.input-borderWidth + " solid " + semantic.border
      border-radius: token.select-radius
      shadow: "0 4px 16px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04)"
      layout: vertical
      role: "listbox"

      // Search input
      block {
        visibility: searchable
        padding: spacing.2
        border-bottom: borders.default
        TextInput(placeholder: "Search...", value: query) {
          on change(v): setQuery(v)
        }
      }

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
  }
}
