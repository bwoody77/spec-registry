fn wrapIndex(index: number, delta: number, len: number) -> number {
  if len <= 0 { return 0 }
  return ((index + delta) % len + len) % len
}

component MultiSelect(options: array = [], values: array = [], placeholder: string = "Select...", searchable: boolean = true, disabled: boolean = false, label: string = "", display: string = "chips", showCheckbox: boolean = true, mode: string = "dropdown") {
  @state {
    open: false
    query: ""
    selected: values
    highlightIndex: 0
    focused: false
  }

  // Sync internal `selected` state when the parent passes a new `values` prop
  // (e.g. when a Clear button resets `filterAircraftIds = []`). Without
  // this, the chips on screen remain stale even though the data is correct.
  @watch {
    values: {
      selected = values
    }
  }

  @computed {
    safeOptions: options != null ? options : []
    safeSelected: selected != null ? selected : []
    filteredOptions: searchable && query != "" ? safeOptions.filter(o => o.label.toLowerCase().includes(query.toLowerCase())) : safeOptions
    selectedOptions: safeOptions.filter(o => safeSelected.includes(o.value))
    hasSelections: safeSelected.length > 0
    hasOptions: filteredOptions.length > 0
    displayPlaceholder: hasSelections == false ? placeholder : ""
    // Summary text used in display='text' mode. Falls back to `label` when the
    // option doesn't define a `shortLabel` (e.g. callers building options from
    // simple {value,label} pairs). Aircraft pickers, for example, set shortLabel
    // to just the tail so the trigger row stays readable when many are picked.
    displayText: selectedOptions.map(o => (o.shortLabel != null ? o.shortLabel : o.label)).join(", ")
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
      // Bulk actions are intentional terminals — once the user picks "every"
      // or "none", they're done with the dropdown. Closing automatically
      // saves a click and matches MVP behavior of macOS / Windows pickers.
      open = false
      query = ""
    }
    clearAll() {
      selected = []
      emit("change", selected)
      open = false
      query = ""
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

    // Label
    block {
      visibility: label != ""
      text(label) { style: type.label-sm, color: semantic.text-secondary }
    }

    // ── DROPDOWN MODE ──────────────────────────────────────────────────
    block {
      visibility: isDropdownMode
      layout: vertical, gap: spacing.1

      // Control row — chips/text + placeholder + caret
      // NOTE: no on-click here — toggleOpen lives on the inner toggle block
      // so that chip x clicks don't bubble into toggleOpen.
      block {
        layout: horizontal, gap: spacing.1
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

        // Text display — single-line summary that truncates with ellipsis when
        // the joined labels overflow the trigger width. `grow: true` claims
        // available space; `overflow: hidden` clips; `truncate: 1` adds the
        // ellipsis. Users see the summary; for full context they reopen the
        // panel (where individual options are still removable).
        block {
          visibility: hasSelections && display == "text"
          grow: true
          overflow: hidden
          text(displayText) {
            style: type.body-md
            color: semantic.text-primary
            truncate: 1
          }
        }

        // Toggle area — clicking here opens/closes dropdown
        // NOTE: only grows when it's the sole flexible sibling in the row.
        // When display=='text' AND there are selections, the text-summary
        // block above (also grow:true) is visible too — two grow:true
        // siblings split the row and shove this area (and its caret)
        // inward, reading as a "box within the box" with the caret off-
        // center. Growing only when the text block is absent keeps the
        // caret pinned to the far right in every mode.
        block {
          grow: (hasSelections && display == "text") ? false : true
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

      // Dropdown panel — fixed-position below the trigger via anchor:'bottom'.
      // positionDropdown sets position:fixed, escaping any overflow:hidden ancestor.
      // popup.js dispatches Escape to the combobox trigger to close it on outside clicks.
      block {
        visibility: open
        anchor: 'bottom'
        padding: spacing.1
        max-height: 280px
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

      // Backdrop — catches clicks outside the dropdown so the panel closes
      // without needing a global document handler. Without this, a previously
      // opened dropdown stays open in the background and the user's next
      // click on the SAME trigger toggles it closed (requiring a second
      // click to reopen) — the recurring "sometimes 2 clicks to open" bug.
      // z-index sits below the panel (200) so the panel still wins clicks.
      // Placed AFTER the panel block so the panel's `anchor: 'bottom'`
      // resolves to its actual previous sibling (the trigger row), not the
      // backdrop.
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
