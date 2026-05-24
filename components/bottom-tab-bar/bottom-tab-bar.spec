component BottomTabBar(
  tabs: array = [],
  activeTab: string = "",
  showLabels: boolean = true
) {
  @actions {
    selectTab(tabId) {
      emit("tabChange", tabId)
    }
  }

  block {
    z-index: 900
    background: semantic.surface
    border-top: borders.default
    padding-bottom: env(safe-area-inset-bottom)
    user-select: "none"

    layout: horizontal, align: center, justify: center

    each tabs as tab {
      block {
        grow: true
        padding-top: spacing.2
        padding-bottom: spacing.1
        cursor: "pointer"
        layout: vertical, align: center, gap: 2px
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
