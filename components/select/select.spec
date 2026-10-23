fn wrapIndex(index: number, delta: number, len: number) -> number {
  if len <= 0 { return 0 }
  return ((index + delta) % len + len) % len
}

// `ariaLabel` is normally supplied by the compiler, not by hand: a control
// rendered under its own `text('ROLE')` gets that label synthesized in as this
// prop (ast-to-ir inferAccessibleNames). Pass it explicitly only when the
// visible label is somewhere the compiler can't see, or when the control needs
// a longer name than the one on screen.
component Select(options: array = [], value: string = "", highlight: string = "", placeholder: text = "Select...", searchable: boolean = false, disabled: boolean = false, label: text = "", clearable: boolean = false, clearLabel: string = "Clear selection", error: boolean = false, errorMessage: text = "", ariaLabel: text = "", autoFocus: boolean = false, size: string = "md", appearance: text = "field") {
  @state {
    open: false
    query: ""
    highlightIndex: 0
    focused: false
    // The error line's id, which the trigger's aria-describedby names. Minted
    // per mount: a literal would repeat on every Select on the page.
    msgId: uniqueId('spec-field-msg')
    // The words the error line says, through followError() (TextInput's
    // "Saying it again", Vector #987).
    errWords: error == true ? errorMessage : ''
    // True for 100ms after the line went empty.
    errHeld: false
  }

  @computed {
    // ── The error, said as well as painted (Vector #989) ─────────────────────
    //
    // TextInput's pattern (Vector #874, #987), and its comments say why. The
    // line used to be gated by `visibility: error == true`, which is
    // display:none: a live region that enters the accessibility tree together
    // with its words is never announced, and the trigger said neither that it
    // was invalid nor what was wrong. Now the line is always here, holds the
    // words while `error` is on, and is out of the flow while it is empty, so
    // a Select with no error takes exactly the room it took before.
    errText: error == true ? errorMessage : ''
    errShown: errWords != ''
    errPosition: errShown ? 'static' : 'absolute'
    errStandIn: errHeld ? errText : ''
    errStandInShown: errStandIn != ''
    // null, not "false" or "": bindAttr removes the attribute, so a Select
    // with no error carries neither.
    invalidAttr: error == true ? 'true' : null
    describedBy: errShown ? msgId : null

    // ── size: "md" (default, unchanged) | "sm" ───────────────────────────────
    //
    // BOTH of these move together or neither does anything, which is the whole
    // reason they are named here instead of written inline at their two sites.
    // Per the padding invariant documented on the trigger below, the outer box
    // carries min-height and no padding while an inner box carries the padding
    // and the text. The rendered height is therefore
    // max(min-height, padding×2 + line) + 2×border, so at "md" the outer 40
    // beats the inner 8+20+8=36 and the control measures 42.
    //
    // Drop min-height alone and the inner 36 becomes the floor: the control
    // goes 42 → 38 and looks untouched. Drop the padding alone and the outer 40
    // still wins: nothing moves at all. An earlier attempt at this prop changed
    // one of them, measured no change, and was reverted as a no-op.
    //
    // "sm" is 4+20+4=28 under a 30 floor, so the control measures 32 — the
    // height a filter toolbar wants beside a 30px segmented control.
    //
    // ⚠ THE UNITS ARE LOAD-BEARING, and this prop shipped without them.
    //
    // A size property written as a LITERAL in markup is resolved by the
    // compiler and emitted with its unit; bound to a `@computed` the raw value
    // is emitted. This line used to read `min-height: 40px` in the markup below
    // and worked. Hoisting it into a computed NUMBER emitted `min-height: 40`,
    // which is not a length — so the browser dropped the declaration, the floor
    // stopped applying, and every Select in every consuming app went 42 → 38
    // and "sm" 32 → 30.
    //
    // That is the third face of the same no-op this comment already warned
    // about twice: not "changed one of the two" but "changed both, and one of
    // them stopped being valid CSS on the way". `select-trigger-padding.test.ts`
    // asserts the emitted value is `40px` and has been RED on main since — a
    // guard doing its job into a room with nobody in it.
    triggerMinHeight: size == "sm" ? '30px' : '40px'
    triggerPad: size == "sm" ? spacing.1 : spacing.2

    // ── appearance: "field" (default, unchanged) | "inline" (0.12.0) ─────────
    //
    // "inline" is the trailing value of a settings row, the shape iOS
    // Settings draws for a menu picker: no box, the picked value in the
    // interactive color at the row's end, an up-down caret beside it. The
    // row around it carries the label; the Select fills what is left of it,
    // so its open list is as wide as that space. On iOS it is the same Menu
    // Picker with a plain label (Vector #1293). An error still draws the
    // destructive border, since an inline field has no other place to say it.
    isInline: appearance == "inline"
    triggerBorder: error == true
      ? token.input-borderWidth + " solid " + semantic.destructive
      : (isInline ? "none" : (focused ? token.input-borderWidth + " solid " + token.input-focusBorder : token.input-borderWidth + " solid " + token.select-border))
    triggerBg: isInline ? "transparent" : token.select-bg
    triggerHoverBg: disabled || isInline ? triggerBg : semantic.surface-raised
    triggerJustify: isInline ? "end" : "between"
    triggerGap: isInline ? spacing.1 : '0px'
    caretName: isInline ? 'chevrons-up-down' : 'chevron-down'
    caretColor: isInline ? semantic.interactive : semantic.text-tertiary

    safeOptions: options != null ? options : []
    filteredOptions: searchable && query != "" ? safeOptions.filter(o => o.label.toLowerCase().includes(query.toLowerCase())) : safeOptions
    selectedOption: safeOptions.find(o => o.value == value)
    displayText: selectedOption != null ? selectedOption.label : placeholder
    displayColor: selectedOption != null ? (isInline ? semantic.interactive : semantic.text-primary) : semantic.text-tertiary
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
    // Where the list OPENS, which is not always where the selection is.
    //
    // `highlight` is for the two cases a selection cannot express: a field with
    // NO value that still knows roughly where the user is headed, and a value
    // that is not one of the options at all. Both are the same downstream
    // control — a half-hour time list, which opens on 12:00 AM when empty, and
    // whose 11:12 is in no half-hour grid. Naming a row to open on costs the
    // caller one prop and leaves every other caller exactly as it was.
    //
    // It outranks the selection deliberately: a caller that passes both is
    // saying "I know what is selected, open here anyway".
    highlightOption: highlight != "" ? safeOptions.find(o => o.value == highlight) : null
    openIndex: highlightOption != null
                 ? safeOptions.findIndex(o => o.value == highlight)
                 : selectedIndex
  }

  @watch {
    // Both props: a watch on one reads its sibling's old value when the
    // caller changes both.
    error: { followError() }
    errorMessage: { followError() }
  }

  @actions {
    // Words that arrive within 100ms of the line going empty wait out those
    // 100ms, so the empty line reaches the page before the same words come
    // back and a second failure is heard (TextInput's followError).
    followError() {
      let words = error == true ? errorMessage : ''
      if words == '' {
        if errWords != '' {
          errWords = ''
          errHeld = true
          delay("errRefill", 100) {
            errHeld = false
            errWords = error == true ? errorMessage : ''
          }
        }
        return
      }
      if !errHeld {
        errWords = words
      }
    }
    toggleOpen() {
      if disabled == false {
        open = open == false
        query = ""
        highlightIndex = openIndex
      }
    }
    openDropdown() {
      if disabled == false && open == false {
        open = true
        query = ""
        highlightIndex = openIndex
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
      min-height: triggerMinHeight
      background: triggerBg
      border: triggerBorder
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
      aria-invalid: invalidAttr
      aria-describedby: describedBy
      on hover { background: triggerHoverBg }
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
        layout: horizontal, justify: triggerJustify, align: center, gap: triggerGap
        padding: triggerPad
        text(displayText) {
          style: type.body-md
          color: displayColor
        }
        // Caret. An Icon, not the "\u25BE" text glyph it used to be: that glyph
        // is font-dependent (it renders at a different weight and baseline
        // across platforms) and it left the registry disagreeing with itself,
        // since column-chooser and Vector's hand-rolled dropdown triggers all
        // draw `chevron-down`. Every combobox in the registry now uses this
        // exact mark at this exact size.
        Icon(name: caretName, size: 16, color: caretColor)
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
              // An option may carry `sub: string` (0.12.0): a second line
              // under its label, as an iOS menu item's subtitle.
              block {
                visibility: g._opt.sub != null && g._opt.sub != ''
                text(g._opt.sub != null ? g._opt.sub : '') {
                  style: type.caption
                  color: semantic.text-tertiary
                }
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

    // Error message — a live region that is always here (see errText above).
    // role alert (assertive), as TextInput and Vector's kit ErrorLine.
    block {
      id: msgId
      role: 'alert'
      aria-live: 'assertive'
      position: errPosition
      text(errWords) {
        style: type.caption
        color: semantic.destructive
      }
    }

    // The same words while the line above waits out its empty moment,
    // painted in its place and aria-hidden (TextInput's stand-in).
    block {
      visibility: errStandInShown
      aria-hidden: 'true'
      text(errStandIn) {
        style: type.caption
        color: semantic.destructive
      }
    }
  }
}
