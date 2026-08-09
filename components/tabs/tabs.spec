// Tabs — a bar-only tab strip. Renders the tab buttons and emits "change"
// with the clicked tab's id. The consumer owns the content (e.g. match on
// the active id), so each tab can have its own data source and side effects.
//
//   Tabs(tabs: myTabs, activeTab: active, variant: 'pill', overflow: 'wrap') {
//     on change(id): setActive(id)
//   }
//
// tabs:     array of { id: string, label: string, icon?: string, count?: number }
// variant:  'pill' (filled chip, carded strip) | 'underline' (2px indicator)
// overflow: 'wrap' (grid auto-fill) | 'scroll' (single row, auto-scroll)
//           | 'grow' (equal-width columns filling the row)
//
// Optional slot `tabAdornment`, invoked once per tab with that tab, so a
// caller can render something (a chip naming what was drilled into, say)
// immediately after ONE tab instead of at the end of the strip:
//
//   Tabs(tabs: myTabs, activeTab: active) {
//     on change(id): setActive(id)
//     slot("tabAdornment") { |tab|
//       block { visibility: tab.id == 'documents' && openDoc != null
//         Badge(text: openDoc)
//       }
//     }
//   }
//
// Providing it wraps each tab in a presentational cell (see below). NOT
// providing it renders exactly what this component rendered without it.
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

    // The `tabAdornment` branch, expressed as two complementary lists rather
    // than two `visibility:` arms. `visibility:` emits `display: none`, it does
    // not omit the node — two arms would leave an un-adorned caller with a
    // wrapper element inside its `role=tablist` forever, and `Tabs` ships to
    // several apps. Exactly one of these lists is ever non-empty, so the
    // un-adorned caller runs the original loop below, byte-for-byte unchanged.
    // (An `each` still creates its own list container, so the unused loop costs
    // one EMPTY `display: contents` div: no box, no grid item, nothing painted.)
    unadornedTabs: hasSlot("tabAdornment") ? [] : tabs
    adornedTabs:   hasSlot("tabAdornment") ? tabs : []
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

    // No `tabAdornment` slot — EXACTLY what this component rendered before the
    // slot existed. TabsItem is the grid cell, one per column, and nothing
    // stands between it and the tablist that did not stand there before.
    // `tabs-adornment.test.ts` compares this against a frozen copy of the
    // pre-slot component and fails on any difference.
    each unadornedTabs as tab (tab.id) {
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

    // Adorned — one wrapper cell per tab, so the strip still has exactly one
    // grid item per column. Emitting the adornment as a SIBLING of TabsItem
    // would put 2N children into the N-column template and wrap them onto
    // implicit rows.
    //
    // role=presentation keeps the wrapper out of the accessibility tree, so
    // the tab buttons remain the tablist's semantic children even though this
    // arm nests them one element deeper than the un-adorned arm.
    each adornedTabs as tab (tab.id) {
      block {
        role: 'presentation'
        layout: horizontal, align: center, gap: 6px
        TabsItem(
          tab: tab
          active: tab.id == activeTab
          variant: variant
          tabStop: tab.id == tabStopId
          focused: tab.id == focusedId
        ) {
          on change(id): pickTab(id)
        }
        // Invoked once per tab, with that tab — a caller can render for one
        // tab only: `slot("tabAdornment") { |tab| … }`.
        @slot("tabAdornment", tab)
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
    // Count badge — tinted with the tab's own state so it reads as part of the
    // tab rather than a floating chip. toString guards a null (the badge is
    // hidden then anyway, but the computed still evaluates).
    countText: tab.count != null ? toString(tab.count) : ''
    countBg:   active ? semantic.interactive-bg : semantic.surface-hover
    countFg:   active ? semantic.interactive-hover : semantic.text-tertiary
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
    // Optional count badge ("Documents 12"). Absent unless a tab supplies
    // `count`, so every existing caller renders byte-for-byte as before.
    //
    // The height is FIXED rather than left to the badge's padding. A padded
    // badge is taller than the bare label, and this row is align:center, so a
    // strip mixing counted and uncounted tabs would centre their labels on two
    // different baselines — the counted ones sitting a few px higher. Pinning
    // the badge to the label's own line box keeps every label on one baseline
    // whether or not it has a count.
    //
    // The count is centred inside that fixed height with `layout: … align:
    // center`, NOT a line-height. `line-height` is not a Spec property — it
    // comes from the `style:` type token — so `line-height: 18px` here was a
    // parse error, which made resolveSpecComponents drop this whole file and
    // silently omit Tabs from every consumer's bundle.
    block {
      visibility: tab.count != null
      layout: horizontal, align: center, justify: center
      padding-x: 6px
      height: 18px
      border-radius: '9px'
      background: countBg
      text(countText) {
        style: type.label-xs
        weight: 700
        color: countFg
      }
    }
  }
}
