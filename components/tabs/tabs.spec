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
// 'wrap' gives every tab a 110px minimum so the wrapped rows line up as a
// grid. When a strip has MANY tabs of uneven length that floor stops paying
// for itself — see `PackedTabs` further down this file, which sizes each tab
// to its own label and separates them with a rule instead.
// countTone: how a tab's `count` badge is coloured.
//           'state'  (default) — tinted with the tab's own active/inactive
//                    state, so the count reads as part of that tab.
//           'strong' — one fixed solid fill in both states, from the
//                    `tab-countStrongBg` / `tab-countStrongColor` tokens. For a
//                    strip of QUEUES, where a busy tab must pull the eye
//                    whether or not it is the one you are standing on.
//           A tab with no `count` renders no badge under either tone, so a
//           caller showing outstanding work should pass `count: null` at zero
//           rather than 0 — an empty queue should not wear a badge.
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

// The strip's CELLS — one grid column each.
//
// A run of ADJACENT tabs carrying the same non-null `group` collapses into one
// cell, so they can share a single enclosure. Every other tab is a cell of one,
// which is what keeps `repeat(N, …)` correct for every existing caller: no
// `group` anywhere means cells.length == tabs.length, exactly as before.
//
// ADJACENCY, not a tag: two tabs sharing a group value with another tab between
// them stay separate. The enclosure describes a position in the strip, and
// pulling them together would silently reorder tabs the caller placed
// deliberately. So the run breaks the moment the value changes.
//
// Each cell is `{ key, grouped, tabs }`. `grouped` is false for a run of one —
// a box drawn around a single tab would be a lie about the hierarchy — and
// `key` is the first tab's id, which is unique across the strip.
//
// On the accumulator shape: the run is built in its OWN local and the finished
// cell is pushed whole, then `run` is REBOUND (`run = [item]`) rather than
// emptied in place. `push` into a receiver two or more levels inside a local —
// `out[i].tabs` — is mutated in place on JS but COPIED on Swift, losing the
// mutation (fn-reference §Array). Rebinding is well-defined on every target.
fn _tabCells(items: array) -> array {
  let out = []
  let run = []
  let runKey = null
  for item in items {
    let g = item.group ?? null
    if g != null && g == runKey && length(run) > 0 {
      push(run, item)
    } else {
      if length(run) > 0 {
        push(out, { key: run[0].id, grouped: length(run) > 1, tabs: run })
      }
      run = [item]
      runKey = g
    }
  }
  if length(run) > 0 {
    push(out, { key: run[0].id, grouped: length(run) > 1, tabs: run })
  }
  return out
}

// size — "md" (default, unchanged) or "sm", which tightens the per-item padding.
//
// A tab strip that IS the page's navigation wants presence. A strip used as a
// SEGMENT CONTROL inside a toolbar is one control among several, and at the
// default padding it stands 39px tall beside 32px dropdowns — measured on cf's
// deals toolbar against its own mockup, which draws the segment at 28px. Same
// prop, same two values, as Select and Button.
component Tabs(tabs: array, activeTab: string = "", variant: string = "pill", overflow: string = "wrap",
               countTone: string = "state", size: string = "md") {
  @state {
    // Which tab currently holds DOM focus. Empty until the user actually moves
    // focus into the strip — otherwise `focus:` would steal focus on mount.
    focusedId: ''
  }

  @computed {
    // One column per CELL, not per tab — a grouped run occupies a single
    // column. With no `group` anywhere, cells.length == tabs.length and every
    // template below is byte-for-byte what it always was.
    cells: _tabCells(tabs)

    // Overflow is expressed entirely through the grid column template.
    gridColumns: overflow == 'grow'
                   ? ('repeat(' + (cells.length + '') + ', 1fr)')
                   : (overflow == 'scroll'
                       ? ('repeat(' + (cells.length + '') + ', max-content)')
                       : 'repeat(auto-fill, minmax(110px, max-content))')
    scrollMode:  overflow == 'scroll' ? 'auto' : 'visible'
    // Strip chrome differs by variant.
    stripBg:        variant == 'pill' ? semantic.surface : 'transparent'
    stripBorder:    variant == 'pill' ? borders.default : '1px solid transparent'
    stripBorderBot: variant == 'pill' ? borders.default : ('1px solid ' + semantic.border)
    stripRadius:    variant == 'pill' ? 12px : 0px
    stripPad:       variant == 'pill' ? 6px : 0px

    // The grouped cell's fill, which has to differ by variant because the PILL
    // variant already spends `semantic.interactive-bg` on its active chip
    // (itemBg in TabsItem). Tinting the enclosure the same colour would make
    // the active tab inside a group vanish into it — the one tab that must
    // stay legible. `surface-hover` is the recessed tone against a pill strip's
    // own `surface`, and leaves the active chip's interactive-bg distinct.
    //
    // Underline strips paint no tab background at all, so there is nothing to
    // collide with and the interactive tint reads as intended there.
    groupBg:     variant == 'pill' ? semantic.surface-hover : semantic.interactive-bg

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
    //
    // Grouping joins the same branch: an enclosure needs a wrapper to paint on,
    // so a strip with a real run takes the cell arm even with no slot supplied.
    // The condition is `cells.length != tabs.length`, which is true exactly when
    // some run has two or more tabs in it — so a caller whose `group` values
    // happen to form NO adjacent pair still renders through the original flat
    // path, wrapper-free and byte-identical to before.
    //
    // Both arms read `cells.length` rather than a `hasGroups` computed derived
    // from it: one extra level of cascade is one more position that can go stale
    // for a tick, and this comparison is a single integer test.
    unadornedTabs: (hasSlot("tabAdornment") || cells.length != tabs.length) ? [] : tabs
    cellList:      (hasSlot("tabAdornment") || cells.length != tabs.length) ? cells : []
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
    // The strip scrolls, and it does NOT draw a bar to do it.
    //
    // The active tab is marked with a 2px bottom border, and a phone draws its
    // overlay scrollbar inside this box — directly on top of that border. So on
    // a handset the one cue telling the reader which tab they are on was
    // covered by a bar they had no way to dismiss. Reported against Vector's
    // /my-profile credentials strip.
    //
    // Unconditional rather than gated on `overflow == 'scroll'`: the property
    // is inert on a box that does not scroll, and a conditional here would have
    // to be an expression, which `scrollbar:` deliberately does not take (part
    // of its output is a ::-webkit-scrollbar rule — see ai-reference §styles).
    //
    // The strip stays fully scrollable by wheel, touch and keyboard, and the
    // tablist's own ArrowLeft/ArrowRight handling above is unaffected — which
    // is what keeps hiding the bar a cosmetic change rather than a trap.
    scrollbar: none
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
        countTone: countTone
        size: size
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
    each cellList as cell (cell.key) {
      block {
        role: 'presentation'
        layout: horizontal, align: center, gap: 6px

        // The enclosure. Drawn on the CELL, so it spans the whole run and no
        // grid gap cuts through it — the reason grouping had to land here
        // rather than in a consumer: an app cannot style a cell it does not
        // emit, and two half-enclosures either side of the tablist's 4px gap
        // leave a transparent slit down the middle of the tint.
        //
        // A run of one paints nothing at all. `data-tab-group` is bound to null
        // there, and a binding REMOVES an attribute when its value is null
        // (ai-reference §31b), so a lone cell carries no marker and no styling
        // — which is what keeps an adorned-but-ungrouped strip looking exactly
        // as it did before this existed.
        //
        // Tokens, not literals: `semantic.interactive-bg` and
        // `borders.interactive` both exist in the compiler's own visual-system
        // defaults, so this renders in every app and adapts per theme. A NEW
        // token would have been the risk here — an unresolved one emits
        // nothing, with no error and no warning.
        data-tab-group: cell.grouped ? 'true' : null
        background:     cell.grouped ? groupBg : 'transparent'
        // `none`, not a transparent 1px: an ungrouped cell must not gain a
        // border box at all. A 1px transparent border would widen every tab in
        // every adorned strip by 2px — a silent layout change shipped to every
        // app on the registry for no visual gain.
        border:         cell.grouped ? borders.interactive : 'none'
        // Open at the bottom, so the enclosure reads as a tray opening out of
        // the strip rather than a closed box floating on it. A literal, not a
        // ternary: a REACTIVE border shorthand clobbers the longhand written
        // below it, and this has to survive that.
        border-bottom:  'none'
        border-radius:  cell.grouped ? '8px 8px 0 0' : 0px
        padding-x:      cell.grouped ? 4px : 0px
        // Sit the enclosure's open bottom edge ON the strip's own rule, so it
        // reads as a tray opening out of the strip rather than a floating box.
        margin-bottom:  cell.grouped ? -1px : 0px

        each cell.tabs as tab (tab.id) {
          TabsItem(
            tab: tab
            active: tab.id == activeTab
            variant: variant
            tabStop: tab.id == tabStopId
            focused: tab.id == focusedId
            countTone: countTone
            size: size
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
}

// PackedTabs — the same tab strip, sized to its labels.
//
//   PackedTabs(tabs: myTabs, activeTab: active) {
//     on change(id): setActive(id)
//   }
//
// `Tabs(overflow: 'wrap')` lays the strip out as a grid of
// `minmax(110px, max-content)` columns. Uniform columns are what make a
// wrapped strip read as a grid rather than a ragged run of chips, and the
// price is that EVERY tab pays the floor: measured on Vector's aircraft page
// at a 1224px strip, Oil needed 68px, W&B 81px, Rates 83px and Meters 92px,
// and all four were drawn 110px wide. Thirteen tabs then needed three lines
// with roughly 300px of the strip spent on nothing.
//
// PackedTabs is the other answer: each tab is exactly as wide as its own
// label, tabs are separated by a 1px rule instead of a 4px gap, and a tab that
// does not fit moves to the next line whole. Same page, same width: eleven
// tabs on the first line, two on the second, every label on one line, and the
// strip 96px tall against 117px.
//
// It is a SEPARATE component rather than another `overflow` mode because the
// two need different CSS display modes, and `layout:` is static in the
// compiler — `columns:` takes a binding, `display` does not (ir-to-js emits it
// from `layout.mode` as a literal). Free flow is flex-wrap and there is no
// grid template that reproduces it: `minmax(0, max-content)` gives natural
// widths but shrinks them to fit ONE row instead of wrapping, and every
// intrinsic minimum (`min-content`, bare `max-content`) is invalid under
// `auto-fill`. Both were measured in a browser before this component existed.
//
// Which to reach for: `Tabs` when the strip is short enough that uniform
// columns cost nothing, or when the tab labels are of similar length.
// PackedTabs when there are MANY tabs of uneven length — the case where the
// floor stops being alignment and starts being wasted row.
//
// Not supported here, deliberately: `overflow` (a packed strip always wraps —
// use Tabs for a scrolling or an equal-width strip), the `tabAdornment` slot
// and `group`. Those exist to structure a GRID of tabs; a packed strip has no
// columns for them to line up with. They can be added if a caller needs them.
component PackedTabs(tabs: array, activeTab: string = "", variant: string = "pill",
                     countTone: string = "state", size: string = "md") {
  @state {
    // Which tab currently holds DOM focus — empty until the user arrows into
    // the strip, so `focus:` never steals focus on mount. Same contract as Tabs.
    focusedId: ''
  }

  @computed {
    // Strip chrome, identical to Tabs so the two are interchangeable at a
    // glance: only what is INSIDE the strip differs.
    stripBg:        variant == 'pill' ? semantic.surface : 'transparent'
    stripBorder:    variant == 'pill' ? borders.default : '1px solid transparent'
    stripBorderBot: variant == 'pill' ? borders.default : ('1px solid ' + semantic.border)
    stripRadius:    variant == 'pill' ? 12px : 0px
    stripPad:       variant == 'pill' ? 6px : 0px

    // Roving tabindex — one tab in the page tab order, the rest on the arrows.
    tabStopId: focusedId != '' ? focusedId : activeTab
    tabCount:  tabs.length

    // The last tab wears no rule: a trailing divider at the end of the strip
    // draws a line against the strip's own padding and reads as an empty
    // fourteenth tab. A rule at a WRAP boundary is left in place on purpose —
    // it is the only thing marking where the row ended.
    lastId: tabCount > 0 ? tabs[tabCount - 1].id : ''
  }

  @actions {
    // MANUAL activation, exactly as in Tabs: the arrows move focus, Enter and
    // Space select. Vector's tabs each own a @source and fetch on mount, so
    // automatic activation would fire a load per tab arrowed past.
    moveFocus(delta) {
      if tabCount > 0 {
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
    pickTab(id) {
      focusedId = id
      emit("change", id)
    }
  }

  block {
    role: "tablist"
    on key-down(event): match event.key {
      "ArrowRight" -> moveFocus(1),
      "ArrowLeft"  -> moveFocus(-1),
      "Home"       -> focusEdge(false),
      "End"        -> focusEdge(true),
      _ -> {}
    }
    // The whole difference from Tabs is this line. `wrap` is the bare layout
    // flag (not `wrap: true`, which does not parse), and `gap: 0px` is what
    // lets the per-tab rule below be the separator — a gap plus a rule would
    // leave the line floating between two tabs instead of dividing them.
    layout: horizontal, gap: 0px, align: center, wrap
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
        countTone: countTone
        size: size
        fillColumn: false
        divider: tab.id != lastId
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
                   tabStop: boolean = true, focused: boolean = false,
                   countTone: string = "state", size: string = "md",
                   fillColumn: boolean = true, divider: boolean = false) {
  @computed {
    // The ONLY thing size changes. The radius, the borders and the count badge
    // are untouched, so a small strip is the same control drawn tighter rather
    // than a second design.
    padY:        size == 'sm' ? (variant == 'pill' ? 4px : 5px) : (variant == 'pill' ? 9px : 10px)
    padX:        size == 'sm' ? (variant == 'pill' ? 10px : 12px) : (variant == 'pill' ? 12px : 16px)
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
    // Count badge. toString guards a null (the badge is hidden then anyway, but
    // the computed still evaluates).
    countText: tab.count != null ? toString(tab.count) : ''
    // Two tones, because a count means two different things depending on the
    // strip:
    //
    //   'state'  (default) — tinted with the TAB's own state, so it reads as
    //            part of the tab. Right when the count is a property of the
    //            thing you are looking at ("Documents 12"): the number is
    //            context for the tab you are on, and the tabs you are not on
    //            should recede.
    //
    //   'strong' — one fixed solid fill in BOTH states. Right when the strip is
    //            a set of QUEUES and the count is the work outstanding: under
    //            'state' a busy queue you are not standing on renders in the
    //            quietest colour on the strip, which is backwards — the whole
    //            reason to show the number is that it should pull you to a tab
    //            you are NOT on.
    //
    // The strong fill is tokenised rather than hard-coded because it has to
    // carry contrast against BOTH the active pill and the bare strip, in every
    // theme an app ships — one literal cannot do that. Apps override
    // `tab.countStrongBg` / `tab.countStrongColor`; the defaults are neutral
    // slate so they sit correctly under any accent hue.
    countBg:   countTone == 'strong'
                 ? token.tab-countStrongBg
                 : (active ? semantic.interactive-bg : semantic.surface-hover)
    countFg:   countTone == 'strong'
                 ? token.tab-countStrongColor
                 : (active ? semantic.interactive-hover : semantic.text-tertiary)
    // Conditional attribute values must be named computeds, not inline
    // ternaries at the property.
    tabStopOrder: tabStop ? '0' : '-1'

    // `width: 100%` is what makes a tab fill its grid column — a <button> does
    // not stretch on its own. In a PACKED strip there is no column to fill:
    // the tab IS its label, and 100% would resolve against the flex container
    // and hand every tab the whole row. Defaults true, so Tabs is unchanged.
    itemWidth: fillColumn ? '100%' : 'auto'

    // The packed strip separates tabs with a rule instead of a gap. Written as
    // a full border shorthand rather than a colour, because `none` has to be
    // expressible: a transparent 1px would still widen every tab in every
    // existing strip by 1px, which is exactly the silent reflow the fillColumn
    // default above is avoiding. Declared AFTER `border` / `border-bottom`
    // below — a reactive border shorthand clobbers longhands written under it.
    itemBorderRight: divider ? ('1px solid ' + semantic.border) : 'none'
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
    // the div did (a button does not stretch on its own) — see itemWidth.
    width: itemWidth
    padding-y: padY
    padding-x: padX
    border-radius: itemRadius
    background: itemBg
    border: itemBorder
    border-bottom: itemBorderBot
    border-right: itemBorderRight
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
