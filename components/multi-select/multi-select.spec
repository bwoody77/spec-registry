@extern { wrapIndex } from "@spec/components/nav-utils.js"

component MultiSelect(options: array = [], values: array = [], placeholder: string = "Select...", searchable: boolean = true, disabled: boolean = false, label: string = "", display: string = "chips", showCheckbox: boolean = true, mode: string = "dropdown") {
  @state {
    open: false
    query: ""
    selected: values
    highlightIndex: 0
    focused: false
  }

  @computed {
    safeOptions: options != null ? options : []
    safeSelected: selected != null ? selected : []
    filteredOptions: searchable && query != "" ? safeOptions.filter(o => o.label.toLowerCase().includes(query.toLowerCase())) : safeOptions
    selectedOptions: safeOptions.filter(o => safeSelected.includes(o.value))
    hasSelections: safeSelected.length > 0
    hasOptions: filteredOptions.length > 0
    displayPlaceholder: hasSelections == false ? placeholder : ""
    displayText: selectedOptions.map(o => o.label).join(", ")
    isDropdownMode: mode == "dropdown"
    showList: isDropdownMode == false || open == true
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
    setQuery(v) {
      query = v
      highlightIndex = 0
      if open == false {
        open = true
      }
    }
    toggleOption(val) {
      if selected.includes(val) {
        selected = selected.filter(v => v != val)
      } else {
        selected = selected.concat([val])
      }
      emit("change", selected)
    }
    removeTag(val) {
      selected = selected.filter(v => v != val)
      emit("change", selected)
    }
    selectAll() {
      selected = filteredOptions.filter(o => o.disabled != true).map(o => o.value)
      emit("change", selected)
    }
    clearAll() {
      selected = []
      emit("change", selected)
    }
    moveHighlight(delta) {
      if filteredOptions.length > 0 {
        highlightIndex = wrapIndex(highlightIndex, delta, filteredOptions.length)
      }
    }
    toggleHighlighted() {
      if filteredOptions.length > 0 && highlightIndex < filteredOptions.length {
        toggleOption(filteredOptions[highlightIndex].value)
      }
    }
    removeLastTag() {
      if safeSelected.length > 0 {
        selected = selected.slice(0, selected.length - 1)
        emit("change", selected)
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

    // ── DROPDOWN MODE ──────────────────────────────────────────────────
    block {
      visibility: isDropdownMode
      layout: vertical, gap: spacing.1
      position: "relative"

      // Control row — chips/text + placeholder + caret
      // NOTE: no on-click here — toggleOpen lives on the inner toggle block
      // so that chip × clicks don't bubble into toggleOpen.
      block {
        layout: horizontal, gap: spacing.1, align: center
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
        aria-label: "Multi-select"
        on hover { background: disabled ? token.select-bg : semantic.surface-raised }
        on focus: { focused = true }
        on blur: { focused = false }
        on key-down(event): {
          match event.key {
            "ArrowDown" -> open ? moveHighlight(1) : openDropdown(),
            "ArrowUp" -> open ? moveHighlight(-1) : openDropdown(),
            "Enter" -> open ? toggleHighlighted() : toggleOpen(),
            "Escape" -> closeDropdown(),
            " " -> open ? toggleHighlighted() : toggleOpen(),
            "Tab" -> closeDropdown(),
            "Backspace" -> query == "" && hasSelections ? removeLastTag() : {},
            _ -> {}
          }
        }

        // Chips display — outside the toggle-click zone
        block {
          layout: horizontal, gap: spacing.1, align: center
          visibility: hasSelections && display == "chips"

          each selectedOptions as opt {
            block {
              layout: horizontal, gap: spacing.1, align: center
              padding-left: spacing.2
              padding-right: spacing.1
              background: semantic.surface-raised
              border-radius: radius.sm
              border: borders.default

              text(opt.label) { style: type.label-sm, color: semantic.text-primary }

              block {
                cursor: "pointer"
                on click: removeTag(opt.value)
                text("\u00D7") { style: type.label-sm, color: semantic.text-tertiary }
              }
            }
          }
        }

        // Text display — wrapped in block for visibility (text() ignores visibility:)
        block {
          visibility: hasSelections && display == "text"
          text(displayText) { style: type.body-md, color: semantic.text-primary }
        }

        // Toggle area — clicking here opens/closes dropdown
        block {
          grow: true
          layout: horizontal, align: center, justify: between
          on click: toggleOpen()

          // Placeholder
          block {
            visibility: hasSelections == false
            text(placeholder) { style: type.body-md, color: semantic.text-tertiary }
          }

          text("\u25BE") { style: type.caption, color: semantic.text-tertiary }
        }
      }

      // Backdrop
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
        max-height: 280px
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

        // Action buttons
        block {
          layout: horizontal, gap: spacing.2, justify: end
          padding: spacing.2
          border-bottom: borders.default

          block {
            cursor: "pointer"
            on click: selectAll()
            text('Select all') { style: type.label-sm, color: semantic.interactive }
          }
          block {
            cursor: "pointer"
            on click: clearAll()
            text('Clear all') { style: type.label-sm, color: semantic.interactive }
          }
        }

        // Options list (dropdown)
        block {
          visibility: hasOptions
          layout: vertical

          each filteredOptions as option, idx {
            block {
              layout: horizontal, gap: spacing.2, align: center
              padding: spacing.2
              border-radius: radius.sm
              cursor: option.disabled == true ? "default" : "pointer"
              opacity: option.disabled == true ? 0.5 : 1
              background: match idx == highlightIndex {
                true -> token.select-optionHover,
                _ -> match safeSelected.includes(option.value) {
                  true -> token.select-optionSelected,
                  _ -> "transparent"
                }
              }
              scroll-to: idx == highlightIndex
              on hover { background: option.disabled == true ? "transparent" : token.select-optionHover }
              on click: toggleOption(option.value)

              // Checkbox / checkmark indicator
              text(match showCheckbox {
                true -> safeSelected.includes(option.value) ? "\u2611" : "\u2610",
                _ -> safeSelected.includes(option.value) ? "\u2713" : ""
              }) {
                style: type.label-sm
                color: semantic.interactive
                width: 16px
              }

              text(option.label) {
                style: type.body-md
                color: safeSelected.includes(option.value) ? semantic.interactive : semantic.text-primary
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

    // ── LIST MODE ──────────────────────────────────────────────────────
    block {
      visibility: isDropdownMode == false
      layout: vertical, gap: spacing.1

      // Selected count header
      block {
        visibility: hasSelections
        padding: spacing.2
        text(safeSelected.length + " selected") { style: type.label-sm, color: semantic.text-secondary }
      }

      // Search input
      block {
        visibility: searchable
        padding: spacing.2
        border-bottom: borders.default
        TextInput(placeholder: "Search...", value: query) {
          on change(v): setQuery(v)
        }
      }

      // Action buttons
      block {
        layout: horizontal, gap: spacing.2, justify: end
        padding: spacing.2
        border-bottom: borders.default

        block {
          cursor: "pointer"
          on click: selectAll()
          text('Select all') { style: type.label-sm, color: semantic.interactive }
        }
        block {
          cursor: "pointer"
          on click: clearAll()
          text('Clear all') { style: type.label-sm, color: semantic.interactive }
        }
      }

      // Options list (list mode)
      block {
        visibility: hasOptions
        layout: vertical
        max-height: 280px
        overflow: auto
        border: token.input-borderWidth + " solid " + semantic.border
        border-radius: token.select-radius
        background: token.select-bg
        tabindex: "0"
        role: "listbox"
        on focus: { focused = true }
        on blur: { focused = false }
        on key-down(event): {
          match event.key {
            "ArrowDown" -> moveHighlight(1),
            "ArrowUp" -> moveHighlight(-1),
            "Enter" -> toggleHighlighted(),
            " " -> toggleHighlighted(),
            _ -> {}
          }
        }

        each filteredOptions as option, idx {
          block {
            layout: horizontal, gap: spacing.2, align: center
            padding: spacing.2
            border-radius: radius.sm
            cursor: option.disabled == true ? "default" : "pointer"
            opacity: option.disabled == true ? 0.5 : 1
            background: match idx == highlightIndex {
              true -> token.select-optionHover,
              _ -> match safeSelected.includes(option.value) {
                true -> token.select-optionSelected,
                _ -> "transparent"
              }
            }
            scroll-to: idx == highlightIndex
            on hover { background: option.disabled == true ? "transparent" : token.select-optionHover }
            on click: toggleOption(option.value)

            // Checkbox / checkmark indicator
            text(match showCheckbox {
              true -> safeSelected.includes(option.value) ? "\u2611" : "\u2610",
              _ -> safeSelected.includes(option.value) ? "\u2713" : ""
            }) {
              style: type.label-sm
              color: semantic.interactive
              width: 16px
            }

            text(option.label) {
              style: type.body-md
              color: safeSelected.includes(option.value) ? semantic.interactive : semantic.text-primary
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
