fn wrapIndex(index: number, delta: number, len: number) -> number {
  if len <= 0 { return 0 }
  return ((index + delta) % len + len) % len
}

// `ariaLabel` is normally supplied by the compiler from the visible label
// rendered beside the control (ast-to-ir inferAccessibleNames), not by hand.
component MultiSelect(options: array = [], values: array = [], placeholder: string = "Select...", searchable: boolean = true, disabled: boolean = false, label: string = "", display: string = "chips", showCheckbox: boolean = true, mode: string = "dropdown", maxChips: number = 3, ariaLabel: string = "") {
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
    // Chips are capped by COUNT, not by rendered rows: the approved design
    // capped at two rendered rows, which needs post-layout measurement.
    // Spec has no such primitive; a CSS max-height would slice chips
    // mid-glyph and make the overflow count uncomputable, and an @extern
    // measurement is web-only and stubs-only on iOS. A count cap is
    // deterministic and portable. The remainder rolls into one counter
    // chip that opens the panel, where every selection stays removable.
    // Clamp negative maxChips to 0 chips: `slice`'s 2nd arg treats a
    // negative number as an offset from the END of the array, not as a
    // cap, so an un-clamped negative maxChips would silently render most
    // of the chips instead of none. A negative cap means "no chips".
    visibleChips: selectedOptions.slice(0, maxChips < 0 ? 0 : maxChips)
    hiddenChipCount: selectedOptions.length - visibleChips.length
    hasHiddenChips: hiddenChipCount > 0
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
    // The text-summary block below grows (grow: true) when display=='text'
    // and something is selected. The chips-display block, the text-summary
    // block, and the placeholder are independent siblings in the control
    // row, each individually visibility-gated — there is no shared
    // toggle-area wrapper. All three claim grow:true, but their visibility
    // is mutually exclusive (chips when display=='chips' and something is
    // selected; text-summary when display=='text' and something is
    // selected; placeholder when nothing is selected), so exactly one
    // grows at a time and the caret's fixed 16px width is never squeezed —
    // it stays pinned to the far right.
    showTextSummary: hasSelections && display == "text"
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
      // Single click handler lives HERE and bubbles to every inner block
      // (placeholder, caret, text-summary) — none of them may add their own
      // on-click, or a click on them fires toggleOpen() twice and cancels
      // out. The one documented exception is the chip x, which calls
      // stopPropagation() so removing a tag doesn't also toggle the panel.
      block {
        layout: horizontal, gap: spacing.1, wrap, align: center
        // Select's own lesson (select.spec:84): padding declared BESIDE
        // `min-height` is ADDED to it (content-box), which rendered this
        // control ~56px next to Select's 40 in every app that used both.
        // The height-bearing box budgets for its padding instead.
        padding: spacing.2
        min-height: 24px
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
        // Was the bare literal, which announced every multi-select as
        // "Multi-select" and overrode the visible label beside it.
        aria-label: ariaLabel != "" ? ariaLabel : (label != "" ? label : "Multi-select")
        on click: toggleOpen()
        on hover { background: disabled ? token.select-bg : semantic.surface-raised }
        on focus: { focused = true }
        on blur: { focused = false }
        // ESCAPE IS HANDLED OUTSIDE THE `match`, ON PURPOSE — see the same
        // note on Select, which had this bug first.
        //
        // `on key-down` + a top-level `match event.key` makes the compiler
        // auto-add preventDefault for every key in the ARM LIST, whatever the
        // arm body does (ast-to-ir.ts's preventDefaultKeys, which spares only
        // Tab). With "Escape" as an arm this trigger cancelled Escape even
        // when no dropdown was open and closeDropdown() was a no-op.
        //
        // That makes the control a black hole for Escape: a dialog, drawer or
        // inline editor around it cannot tell "the MultiSelect consumed it"
        // from "the MultiSelect ignored it", since defaultPrevented is true
        // either way — so the container can never be dismissed while focus
        // sits here. Cancel it when we actually closed something; otherwise
        // let it through untouched.
        //
        // Keep it OUT of the match. Re-adding an "Escape" arm — even one
        // guarded by `open` — restores the unconditional cancel, because the
        // compiler reads the arm list, not the arm bodies.
        on key-down(event): {
          if event.key == 'Escape' {
            if open {
              event.preventDefault()
              closeDropdown()
            }
            return
          }
          match event.key {
            "ArrowDown" -> open ? moveHighlight(1) : openDropdown(),
            "ArrowUp" -> open ? moveHighlight(-1) : openDropdown(),
            "Enter" -> open ? toggleHighlighted() : toggleOpen(),
            " " -> open ? toggleHighlighted() : toggleOpen(),
            "Tab" -> closeDropdown(),
            "Backspace" -> query == "" && hasSelections ? removeLastTag() : {},
            _ -> {}
          }
        }

        // Chips display — outside the toggle-click zone
        block {
          layout: horizontal, gap: spacing.1, align: center, wrap
          grow: true
          visibility: hasSelections && display == "chips"

          each visibleChips as opt {
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
                on click(event): { event.stopPropagation() removeTag(opt.value) }
                text("\u00D7") { style: type.label-sm, color: semantic.text-tertiary }
              }
            }
          }

          // "+N more" counter for chips beyond maxChips. No on-click here:
          // this block sits inside the control row, so a click already
          // bubbles up to the row's toggleOpen() handler. Adding a
          // second handler here would fire toggleOpen() twice in one tick
          // and net to no state change \u2014 the exact defect Task 9 fixed for
          // the caret and placeholder. cursor stays 'pointer' so it still
          // reads as clickable.
          block {
            visibility: hasHiddenChips
            layout: horizontal, align: center
            padding-left: spacing.2
            padding-right: spacing.2
            background: token.select-optionSelected
            border-radius: radius.sm
            border: borders.default
            cursor: "pointer"

            text("+" + hiddenChipCount + " more") {
              style: type.label-sm
              color: semantic.interactive
            }
          }
        }

        // Text display — single-line summary that truncates with ellipsis when
        // the joined labels overflow the trigger width. `grow: true` claims
        // available space; `overflow: hidden` clips; `truncate: 1` adds the
        // ellipsis. Users see the summary; for full context they reopen the
        // panel (where individual options are still removable).
        block {
          visibility: showTextSummary
          grow: true
          overflow: hidden
          // Clickable. Without this only the caret opened the panel, and the
          // caret is ~12px at the far right: once a selection widened the label
          // ("Tier: All" -> "Student Member (59)"), a click at the visible
          // centre of the control landed here and did nothing, which reads as
          // "the dropdown won't reopen". The chip-bubbling concern that kept
          // on-click off the control row does not apply — chips live in their
          // own block gated on display == "chips", and this one only renders in
          // text mode. No handler here anymore: the row-level on-click (above)
          // bubbles to this block, so adding one here would double-fire.
          text(displayText) {
            style: type.body-md
            color: semantic.text-primary
            truncate: 1
          }
        }

        // Placeholder — only when nothing is selected. No on-click: the
        // row-level handler bubbles down to here.
        block {
          visibility: hasSelections == false
          grow: true
          layout: horizontal, align: center
          text(placeholder) { style: type.body-md, color: semantic.text-tertiary }
        }

        // Caret — fixed width, never shrinks, always last. Previously this sat
        // inside a grow:true box (flex: 1 1 0%, min-width: 0), so a few chips
        // squeezed it to zero and there was nothing left to click. No
        // on-click here either: the row-level handler bubbles down.
        block {
          width: 16px
          layout: horizontal, justify: center, align: center
          // Icon, not the "\u25BE" text glyph \u2014 see the note on Select's caret.
          Icon(name: 'chevron-down', size: 16, color: semantic.text-tertiary)
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
                // role="option" comes from the compiler; which rows are
                // selected only this component knows.
                aria-selected: safeSelected.includes(option.value)
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
            aria-selected: safeSelected.includes(option.value)
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
