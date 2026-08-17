fn wrapIndex(index: number, delta: number, len: number) -> number {
  if len <= 0 { return 0 }
  return ((index + delta) % len + len) % len
}

// `ariaLabel` is normally supplied by the compiler, not by hand: a control
// rendered under its own `text('ROLE')` gets that label synthesized in as this
// prop (ast-to-ir inferAccessibleNames). Pass it explicitly only when the
// visible label is somewhere the compiler can't see, or when the control needs
// a longer name than the one on screen.
component Select(options: array = [], value: string = "", placeholder: string = "Select...", searchable: boolean = false, disabled: boolean = false, label: string = "", clearable: boolean = false, clearLabel: string = "Clear selection", error: boolean = false, errorMessage: string = "", ariaLabel: string = "", autoFocus: boolean = false) {
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
    // Option groups. An option may carry `group: string`; a non-interactive
    // header row renders above the FIRST option of each contiguous run of the
    // same group (DataGridNative's `_gFirst` idiom — callers pass options already
    // ordered by group). This list is 1:1 with filteredOptions — same length,
    // same order — so highlightIndex, scroll-to and selectHighlighted never
    // learn that headers exist. Group-less options mark no firsts and render
    // no headers, keeping every existing caller untouched.
    groupedOptions: filteredOptions |> map((o, i) => {
      _opt: o,
      _gFirst: o.group != null && o.group != '' && (i == 0 || filteredOptions[i - 1].group != o.group)
    })
    // Index of the currently-selected option (0 when none) so opening the
    // dropdown highlights it — the `scroll-to: idx == highlightIndex` binding
    // below then scrolls the selected value into view instead of the top.
    selectedIndex: selectedOption != null ? safeOptions.findIndex(o => o.value == value) : 0
  }

  @actions {
    toggleOpen() {
      if disabled == false {
        open = open == false
        query = ""
        highlightIndex = selectedIndex
      }
    }
    openDropdown() {
      if disabled == false && open == false {
        open = true
        query = ""
        highlightIndex = selectedIndex
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
    //
    // THE PADDING INVARIANT — the same one DataGrid documents for column
    // widths. Spec blocks are content-box and Spec has no `box-sizing`, so
    // padding declared BESIDE `min-height` is added to it rather than absorbed:
    // this trigger asked for 40px and rendered 58 (40 + 2×spacing.2 + 2×border)
    // in every app that used it. So the height-bearing box carries no padding;
    // an inner block holds the padding and the content.
    block {
      layout: horizontal
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
      // autoFocus — opt-in, so every existing caller is untouched. A caller
      // that reveals a Select (a disclosure, an inline editor) otherwise has
      // no way to move focus into it: a raw element can be driven with
      // `focus:`, but a component is a black box unless it offers the door.
      // Leaving focus behind means the user tabs forward blind to find the
      // control the disclosure exists to expose.
      focus: autoFocus
      // Was the bare literal "Select", which announced every select in every
      // app as "Select" and, worse, OVERRODE the visible label sitting beside
      // it. Prefer the name the compiler inferred from that visible label,
      // then this component's own rendered `label`, and only fall back to the
      // generic word when there is genuinely nothing to say.
      aria-label: ariaLabel != "" ? ariaLabel : (label != "" ? label : "Select")
      on hover { background: disabled ? token.select-bg : semantic.surface-raised }
      on click: toggleOpen()
      on focus: { focused = true }
      on blur: { focused = false }
      // ESCAPE IS HANDLED OUTSIDE THE `match`, ON PURPOSE.
      //
      // `on key-down` + `match event.key` makes the compiler auto-add
      // preventDefault() for EVERY matched key (ast-to-ir.ts's
      // preventDefaultKeys, which spares only Tab). With "Escape" as an arm,
      // this trigger cancelled Escape whether or not there was a dropdown to
      // close — and closeDropdown() is a no-op when it is already closed.
      //
      // That made the Select a black hole for Escape: an ancestor that closes
      // on Escape (a drawer, a dialog, an inline editor strip) could not tell
      // "the Select consumed it" from "the Select ignored it", because
      // defaultPrevented was true either way. Consumers were left choosing
      // between a dropdown that cannot be dismissed and a container that
      // cannot be. The contract is now the honest one: cancel Escape when we
      // actually closed something, otherwise let it through untouched.
      //
      // Keep it OUT of the match. Adding an "Escape" arm back — even one
      // guarded by `open` — restores the unconditional preventDefault,
      // because the compiler reads the arm LIST, not the arm bodies.
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
          "Enter" -> open ? selectHighlighted() : toggleOpen(),
          " " -> open ? selectHighlighted() : toggleOpen(),
          "Tab" -> closeDropdown(),
          _ -> {}
        }
      }

      block {
        grow: true
        layout: horizontal, justify: between, align: center
        padding: spacing.2
        text(displayText) {
          style: type.body-md
          color: selectedOption != null ? semantic.text-primary : semantic.text-tertiary
        }
        // Caret. An Icon, not the "\u25BE" text glyph it used to be: that glyph
        // is font-dependent (it renders at a different weight and baseline
        // across platforms) and it left the registry disagreeing with itself,
        // since column-chooser and Vector's hand-rolled dropdown triggers all
        // draw `chevron-down`. Every combobox in the registry now uses this
        // exact mark at this exact size.
        Icon(name: 'chevron-down', size: 16, color: semantic.text-tertiary)
      }
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

          each groupedOptions as g, idx {
            // Group header — present in every iteration, shown only on the
            // first option of a run (`visibility:` compiles to display:none,
            // so hidden headers cost nothing visible). The explicit `role:`
            // opts this row out of markListboxOptions' automatic
            // `role="option"` stamp — the developer took responsibility.
            block {
              visibility: g._gFirst
              role: "presentation"
              padding: spacing.2
              cursor: "default"
              text(g._gFirst ? g._opt.group : "") {
                style: type.label-sm
                color: semantic.text-tertiary
                weight: 700
                letter-spacing: '0.06em'
              }
            }
            block {
              padding: spacing.2
              border-radius: radius.sm
              cursor: "pointer"
              background: match idx == highlightIndex {
                true -> token.select-optionHover,
                _ -> match g._opt.value == value {
                  true -> token.select-optionSelected,
                  _ -> "transparent"
                }
              }
              scroll-to: idx == highlightIndex
              // `role="option"` is stamped by the compiler (every listbox row
              // is an option — ast-to-ir markListboxOptions). Selection is NOT
              // inferable: only this component knows which row is current, so
              // it says so here.
              aria-selected: g._opt.value == value
              on hover { background: token.select-optionHover }
              on click: selectOption(g._opt.value)

              text(g._opt.label) {
                style: type.body-md
                color: g._opt.value == value ? semantic.interactive : semantic.text-primary
                weight: g._opt.value == value ? 500 : 400
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
