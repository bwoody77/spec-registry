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
component Tabs(tabs: array, activeTab: string = "", variant: string = "pill", overflow: string = "wrap") {
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
    stripBorderBot: variant == 'pill' ? borders.default : '1px solid #e6ebf2'
    stripRadius:    variant == 'pill' ? 12px : 0px
    stripPad:       variant == 'pill' ? 6px : 0px
  }

  block {
    layout: grid, columns: gridColumns, gap: 4px
    align: center
    overflow: scrollMode
    background: stripBg
    border: stripBorder
    border-bottom: stripBorderBot
    border-radius: stripRadius
    padding: stripPad

    each tabs as tab (tab.id) {
      TabsItem(tab: tab, active: tab.id == activeTab, variant: variant) {
        on change(id): emit("change", id)
      }
    }
  }
}

// One tab button. Styling that depends on `active` (which changes at runtime)
// lives in @computed so it re-evaluates reactively — inline ternaries on a
// changing prop get stuck stale (see pilot-detail.spec PilotTab note).
component TabsItem(tab: object, active: boolean = false, variant: string = "pill") {
  @computed {
    isPill:      variant == 'pill'
    padY:        variant == 'pill' ? 9px : 10px
    padX:        variant == 'pill' ? 12px : 16px
    itemRadius:  variant == 'pill' ? 8px : 0px
    // pill: filled chip when active. underline: no chip.
    itemBg:      (variant == 'pill' && active) ? semantic.interactive-bg : 'transparent'
    itemBorder:  (variant == 'pill' && active) ? '1px solid #bfdbfe' : '1px solid transparent'
    // underline: 2px indicator on the bottom. pill: keep bottom consistent
    // with the other three sides so the chip border is uniform.
    itemBorderBot: variant == 'underline'
                     ? (active ? '2px solid #0067e6' : '2px solid transparent')
                     : ((variant == 'pill' && active) ? '1px solid #bfdbfe' : '1px solid transparent')
    hoverBg:     active ? (variant == 'pill' ? semantic.interactive-bg : 'transparent') : semantic.surface-hover
    fg:          active ? semantic.interactive-hover : semantic.text-secondary
    iconFg:      active ? semantic.interactive-hover : semantic.text-tertiary
    labelWeight: active ? 700 : 600
  }

  block {
    layout: horizontal, gap: 8px, align: center, justify: center
    cursor: 'pointer'
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
