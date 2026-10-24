component SidebarLayout(
  activeRoute: string = "",
  sections: array = [],
  items: array = [],
  breadcrumbSection: text = "",
  breadcrumbTitle: text = ""
) {
  @state {
    sidebarCollapsed: false
    commandPaletteOpen: false
  }

  layout: horizontal

  // Left sidebar
  Sidebar(sections: sections, collapsed: sidebarCollapsed, activeItem: activeRoute) {
    on select(id): { emit("navigate", id) }
    on collapse(v): { sidebarCollapsed = v }
  }

  // Content area
  block {
    grow: true
    layout: vertical

    // Header bar with breadcrumb + command palette trigger
    block {
      layout: horizontal, align: center, justify: between
      padding: spacing.3
      border-bottom: borders.default

      Breadcrumb(items: [
        {id: "home", label: t("Home")},
        {id: activeRoute, label: breadcrumbSection},
        {id: activeRoute, label: breadcrumbTitle}
      ])

      block {
        layout: horizontal, gap: spacing.2
        Button(label: "", variant: "ghost") {
          on click: { commandPaletteOpen = true }
          Icon(name: "search", size: icon.md)
        }
      }
    }

    // Main content
    block {
      grow: true
      overflow: auto
      padding: spacing.4
      @children
    }
  }

  // Command palette overlay
  CommandPalette(open: commandPaletteOpen, commands: items) {
    on select(id): {
      commandPaletteOpen = false
      emit("navigate", id)
    }
    on close: { commandPaletteOpen = false }
  }
}
