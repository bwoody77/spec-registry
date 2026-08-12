component BottomTabBar(
  tabs: array = [],
  activeTab: string = "",
  showLabels: boolean = true,
  ariaLabel: string = ""
) {
  @actions {
    selectTab(tabId) {
      emit("tabChange", tabId)
    }
  }

  // A navigation landmark, NOT a tablist. `tablist`/`tab` describes tabs that
  // swap panels inside one view; this bar changes the route, so a tab role
  // would assert a controls-relationship that does not exist. The state that
  // fits a set of destinations is aria-current="page".
  block {
    z-index: 900
    background: semantic.surface
    border-top: borders.default
    padding-bottom: env(safe-area-inset-bottom)
    user-select: "none"
    role: "navigation"
    aria-label: ariaLabel != "" ? ariaLabel : "Primary"

    layout: horizontal, align: center, justify: center

    each tabs as tab {
      // `button`, not `block`. As a div each tab did get the compiler's
      // clickable shim (tabindex="0" plus an Enter/Space handler), so the bar
      // was operable by keyboard — but it announced as a focusable group with
      // a caption rather than as a control, and nothing carried the
      // current-page state. Vector's 2026-08-11 mobile QA pass hit this on
      // every role (vector#608).
      //
      // The two zeroed paddings keep the geometry identical to the div this
      // replaced. The compiler's own button reset already neutralises border,
      // background, colour and font — but NOT the user agent's horizontal
      // padding, and this bar sizes its tabs purely by `grow`.
      button {
        grow: true
        padding-top: spacing.2
        padding-bottom: spacing.1
        padding-left: 0px
        padding-right: 0px
        cursor: "pointer"
        layout: vertical, align: center, gap: 2px
        aria-current: activeTab == tab.id ? "page" : null
        // With showLabels: false the caption below is display:none, which takes
        // it out of the accessible name and leaves an icon-only button with no
        // name at all. Naming the button directly covers that arm; when the
        // caption IS visible this repeats it verbatim, which is harmless.
        aria-label: tab.label
        on click: selectTab(tab.id)
        on hover {
          background: semantic.surface-raised
        }

        // Icon
        Icon(name: tab.icon, size: "22px", color: activeTab == tab.id ? semantic.accent : semantic.text-tertiary)

        // Label
        text(tab.label) {
          visibility: showLabels == true
          style: type.caption
          color: activeTab == tab.id ? semantic.accent : semantic.text-tertiary
        }

        // Active indicator
        block {
          visibility: activeTab == tab.id
          width: 24px
          height: 2px
          border-radius: 1px
          background: semantic.accent
          position: "absolute"
          top: 0px
          left: 50%
          transform: "translateX(-50%)"
        }
      }
    }
  }
}
