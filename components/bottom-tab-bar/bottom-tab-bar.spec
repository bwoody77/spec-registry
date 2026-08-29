component BottomTabBar(
  tabs: array = [],
  activeTab: string = "",
  showLabels: boolean = true,
  ariaLabel: string = "",
  // The id of ONE tab to render as a raised circular disc standing proud of the
  // bar, instead of a flat icon. "" (the default) is every bar that shipped
  // before this prop existed, byte for byte.
  //
  // It names a TAB ID rather than an index, on purpose. A bar's tab set is
  // usually role- or config-driven, so the middle slot is not a stable place;
  // binding the treatment to the id means the disc follows its button when the
  // set is reordered, instead of promoting whatever happens to land in the
  // centre.
  //
  // An id not present in `tabs` is a no-op, so a caller may pass one
  // unconditionally for a bar that only sometimes contains that tab.
  raisedTabId: string = ""
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

        // ── Icon, in one of two forms ────────────────────────────────────
        //
        // The raised test is repeated at each site rather than hoisted, because
        // `@computed` cannot see `tab` — it is the `each` binding. It is still
        // REACTIVE: the expression NAMES the `raisedTabId` signal, and
        // collectSignalDeps walks binaries, so a subscription is emitted. Same
        // shape as the `activeTab == tab.id` comparisons this component already
        // uses for colour and for aria-current.
        //
        // Two sibling blocks rather than one Icon with conditional sizing: the
        // raised form needs a WRAPPER (the disc), and `visibility:` is silently
        // ignored on a bare component call — so the Icon sits inside a block
        // either way.

        // Raised: a 56px disc pulled up out of the bar, ringed in the bar's own
        // surface colour so it reads as sitting ON the bar rather than in it.
        // The bar declares no `overflow`, so the overhang is not clipped.
        //
        // Every token here is a platform one. `semantic.surface-sunken` would
        // have been the natural inactive fill and is deliberately NOT used — it
        // is not guaranteed to exist on every platform (see data-grid-spec's
        // `groupBackground` note), and a registry component may not assume it.
        block {
          visibility: raisedTabId != "" && raisedTabId == tab.id
          width: 56px
          height: 56px
          margin-top: -26px
          border-radius: 999px
          background: activeTab == tab.id ? semantic.accent : semantic.surface-hover
          border: "3px solid " + semantic.surface
          shadow: activeTab == tab.id ? elevation.floating : elevation.raised
          layout: horizontal, justify: center, align: center
          Icon(name: tab.icon, size: "26px", color: activeTab == tab.id ? semantic.on-interactive : semantic.text-tertiary)
        }

        // Flat: every other tab, and every tab on a bar that passes no
        // raisedTabId. Byte-identical to what this component rendered before.
        block {
          visibility: !(raisedTabId != "" && raisedTabId == tab.id)
          Icon(name: tab.icon, size: "22px", color: activeTab == tab.id ? semantic.accent : semantic.text-tertiary)
        }

        // Label
        text(tab.label) {
          visibility: showLabels == true
          style: type.caption
          color: activeTab == tab.id ? semantic.accent : semantic.text-tertiary
        }

        // Active indicator. Suppressed on the raised tab: the disc's own fill
        // already carries the active state, and a 2px bar pinned to `top: 0`
        // would cut across the middle of a disc that overhangs that very edge.
        block {
          visibility: activeTab == tab.id && !(raisedTabId != "" && raisedTabId == tab.id)
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
