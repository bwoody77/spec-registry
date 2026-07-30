// Tabs — a bar-only tab strip. Renders the tab buttons and emits "change"
// with the clicked tab's id. The consumer owns the content (e.g. match on
// the active id), so each tab can have its own data source and side effects.
//
//   Tabs(tabs: myTabs, activeTab: active, variant: 'pill', overflow: 'wrap') {
//     on change(id): setActive(id)
//   }
//
// tabs:     array of { id: string, label: string, icon?: string }
// variant:  'pill' (filled chip, carded strip) | 'underline' (2px indicator)
// overflow: 'wrap' (grid auto-fill) | 'scroll' (single row, auto-scroll)
//           | 'grow' (equal-width columns filling the row)
// Index of the tab carrying `id`, or 0 when it isn't in the list (an activeTab
// pointing at a removed tab must not strand the arrow keys).
fn _tabIndexOfId(items: array, id: string) -> number {
  for item, i in items {
    if item.id == id { return i }
  }
  return 0
}

// Wrap around both ends — ArrowRight on the last tab lands on the first, which
// is what the ARIA tabs pattern specifies.
fn _tabWrap(index: number, delta: number, len: number) -> number {
  if len <= 0 { return 0 }
  return ((index + delta) % len + len) % len
}

component Tabs(tabs: array, activeTab: string = "", variant: string = "pill", overflow: string = "wrap") {
  @state {
    // Which tab currently holds DOM focus. Empty until the user actually moves
    // focus into the strip — otherwise `focus:` would steal focus on mount.
    focusedId: ''
  }

  @computed {
    // Overflow is expressed entirely through the grid column template.
    gridColumns: overflow == 'grow'
                   ? ('repeat(' + (tabs.length + '') + ', 1fr)')
                   : (overflow == 'scroll'
                       ? ('repeat(' + (tabs.length + '') + ', max-content)')
                       : 'repeat(auto-fill, minmax(110px, max-content))')
    scrollMode:  overflow == 'scroll' ? 'auto' : 'visible'
    // Strip chrome differs by variant.
    stripBg:        variant == 'pill' ? semantic.surface : 'transparent'
    stripBorder:    variant == 'pill' ? borders.default : '1px solid transparent'
    stripBorderBot: variant == 'pill' ? borders.default : ('1px solid ' + semantic.border)
    stripRadius:    variant == 'pill' ? 12px : 0px
    stripPad:       variant == 'pill' ? 6px : 0px

    // Roving tabindex: exactly ONE tab is in the page tab order, so Tab moves
    // past the whole strip to the panel instead of stepping through every tab.
    // That stop is the focused tab once the user has arrowed into the strip,
    // and the selected one otherwise.
    tabStopId: focusedId != '' ? focusedId : activeTab
    tabCount:  tabs.length
  }

  @actions {
    // MANUAL activation: the arrows move FOCUS only; Enter/Space (native button
    // behaviour) selects. The ARIA practices allow either, and prefer automatic
    // selection only when panels appear without noticeable latency — Vector's
    // tabs each own their own @source and fetch on mount, so arrowing across a
    // five-tab strip under automatic activation would fire five loads. Focus
    // moves, selection waits for a deliberate keypress.
    moveFocus(delta) {
      if tabCount > 0 {
        // Read the raw `focusedId` state, NOT the tabStopId @computed derived
        // from it: two arrow presses in quick succession would both see the
        // pre-first-press computed and the second press would go nowhere.
        let currentId = focusedId != '' ? focusedId : activeTab
        let from = _tabIndexOfId(tabs, currentId)
        focusedId = tabs[_tabWrap(from, delta, tabCount)].id
      }
    }
    focusEdge(last) {
      if tabCount > 0 {
        focusedId = last ? tabs[tabCount - 1].id : tabs[0].id
      }
    }
    // Picking a tab makes it the tab stop again, so a later Tab-away/Tab-back
    // returns to the tab the user actually chose.
    pickTab(id) {
      focusedId = id
      emit("change", id)
    }
  }

  block {
    // role=tablist pairs with role=tab on each item, so assistive tech
    // announces "tab 2 of 5" instead of reading five unrelated buttons.
    role: "tablist"
    // Keydown is bound on the STRIP, not each tab — the event bubbles from
    // whichever tab has focus, so one handler covers them all. `match event.key`
    // also makes the compiler preventDefault the matched keys, which stops
    // ArrowLeft/Right and Home/End from scrolling the page underneath.
    on key-down(event): match event.key {
      "ArrowRight" -> moveFocus(1),
      "ArrowLeft"  -> moveFocus(-1),
      "Home"       -> focusEdge(false),
      "End"        -> focusEdge(true),
      _ -> {}
    }
    layout: grid, columns: gridColumns, gap: 4px, align: center
    overflow: scrollMode
    background: stripBg
    border: stripBorder
    border-bottom: stripBorderBot
    border-radius: stripRadius
    padding: stripPad

    each tabs as tab (tab.id) {
      TabsItem(
        tab: tab
        active: tab.id == activeTab
        variant: variant
        tabStop: tab.id == tabStopId
        focused: tab.id == focusedId
      ) {
        on change(id): pickTab(id)
      }
    }
  }
}

// One tab button. Styling that depends on `active` (which changes at runtime)
// lives in @computed so it re-evaluates reactively — inline ternaries on a
// changing prop get stuck stale (see pilot-detail.spec PilotTab note).
//
// Renders a real <button role="tab"> carrying aria-selected. It was a
// `block { on click }` — a <div> — until 0.4.0: not focusable, not
// keyboard-activatable, and announced as nothing, so a tab strip built on this
// component could not be operated without a mouse. The button primitive needs
// its browser chrome zeroed (border/background/padding) to keep the previous
// visual output byte-for-byte; the compiler already emits
// `style.fontFamily = 'inherit'` for buttons, so typography is unaffected.
component TabsItem(tab: object, active: boolean = false, variant: string = "pill",
                   tabStop: boolean = true, focused: boolean = false) {
  @computed {
    padY:        variant == 'pill' ? 9px : 10px
    padX:        variant == 'pill' ? 12px : 16px
    itemRadius:  variant == 'pill' ? 8px : 0px
    // pill: filled chip when active. underline: no chip.
    itemBg:      (variant == 'pill' && active) ? semantic.interactive-bg : 'transparent'
    itemBorder:  (variant == 'pill' && active) ? '1px solid #bfdbfe' : '1px solid transparent'
    // underline: 2px indicator on the bottom. pill: keep bottom consistent
    // with the other three sides so the chip border is uniform.
    itemBorderBot: variant == 'underline'
                     ? (active ? ('2px solid ' + semantic.interactive) : '2px solid transparent')
                     : ((variant == 'pill' && active) ? '1px solid #bfdbfe' : '1px solid transparent')
    hoverBg:     active ? (variant == 'pill' ? semantic.interactive-bg : 'transparent') : semantic.surface-hover
    fg:          active ? semantic.interactive-hover : semantic.text-secondary
    iconFg:      active ? semantic.interactive-hover : semantic.text-tertiary
    labelWeight: active ? 700 : 600
    // Conditional attribute values must be named computeds, not inline
    // ternaries at the property.
    tabStopOrder: tabStop ? '0' : '-1'
  }

  button {
    role: "tab"
    // Pass the boolean, not a 'true'/'false' string — a binding only removes an
    // attribute when the value is null, so false correctly sets "false"
    // (ai-reference §31b). Reactive, so it re-announces on every switch.
    aria-selected: active
    // Roving tabindex — only the strip's single tab stop is reachable by Tab;
    // the rest are reached with the arrow keys.
    tabindex: tabStopOrder
    // Moves DOM focus here when the arrows select this tab. `focus:` fires on
    // the false→true transition, so it never grabs focus on mount (focusedId
    // starts empty and no tab is `focused`).
    focus: focused
    layout: horizontal, gap: 8px, align: center, justify: center
    cursor: 'pointer'
    // The button's own chrome, zeroed so the styling below is the only thing
    // that paints. width:100% keeps a grid item filling its column exactly as
    // the div did (a button does not stretch on its own).
    width: 100%
    padding-y: padY
    padding-x: padX
    border-radius: itemRadius
    background: itemBg
    border: itemBorder
    border-bottom: itemBorderBot
    on click: emit("change", tab.id)
    on hover {
      background: hoverBg
    }

    // Icon is optional — wrapped so a missing icon claims no space.
    block {
      visibility: tab.icon != null
      Icon(name: tab.icon, size: 14, color: iconFg)
    }
    text(tab.label) {
      style: type.body-sm
      weight: labelWeight
      color: fg
    }
  }
}
