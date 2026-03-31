// Dashboard — Sidebar + header + content area layout
//
// Composes AppShell and Sidebar into a ready-to-use admin/dashboard shell.
// The sidebar collapses on mobile into a bottom bar or can be toggled.
// Header, sidebar, and content are all slotted for full customisation.
// Works with every theme via semantic design tokens.
//
// Example usage:
//
//   @state { view: 'home', sidebarCollapsed: false }
//
//   Dashboard(
//     brandName: 'My App',
//     navSections: [
//       {heading: 'Main', items: [
//         {id: 'home', label: 'Home', icon: 'home'},
//         {id: 'settings', label: 'Settings', icon: 'settings'}
//       ]}
//     ],
//     activeNav: view,
//     collapsed: sidebarCollapsed
//   ) {
//     slot("header-actions") {
//       Button(label: 'Profile', variant: 'ghost')
//     }
//
//     // Default slot — page content
//     text('Welcome to the dashboard')
//   }

component Dashboard(
  brandName: string = "",
  brandIcon: string = "home",
  navSections: array = [],
  activeNav: string = "",
  collapsed: boolean = false,
  sidebarWidth: string = "240px"
) {
  block {
    width: 100%
    height: 100vh
    overflow: hidden
    layout: vertical
    background: semantic.background

    // Header bar
    block {
      padding-y: responsive(6px, md: 10px)
      padding-x: responsive(12px, md: 20px)
      background: semantic.surface
      border-bottom: borders.default
      shadow: elevation.raised
      layout: horizontal, gap: spacing.4, align: center, justify: between

      // Left: brand
      block {
        layout: horizontal, gap: spacing.3, align: center

        block {
          width: 32px
          height: 32px
          border-radius: radius.md
          cursor: "pointer"
          layout: horizontal, align: center, justify: center
          on hover { background: semantic.surface-raised }
          on click: emit("toggle-sidebar")
          text("\u2630") { style: type.body-lg, color: semantic.text-secondary }
        }

        Icon(name: brandIcon, size: icon.lg, color: semantic.interactive)

        block {
          visibility: brandName != ""
          text(brandName) {
            style: type.heading-lg
            color: semantic.text-primary
            letter-spacing: "-0.02em"
          }
        }
      }

      // Right: header actions slot
      block {
        layout: horizontal, gap: spacing.2, align: center
        @slot("header-actions")
      }
    }

    // Breadcrumb bar (optional)
    block {
      visibility: hasSlot("breadcrumb")
      background: semantic.surface-raised
      border-bottom: borders.default
      padding-y: spacing.2
      padding-x: responsive(12px, md: 20px)
      @slot("breadcrumb")
    }

    // Body: sidebar + content
    block {
      grow: true
      layout: horizontal
      overflow: hidden

      // Sidebar
      Sidebar(
        sections: navSections,
        activeItem: activeNav,
        collapsed: collapsed,
        width: sidebarWidth
      ) {
        on select(id): emit("nav", id)
        on collapse(c): emit("collapse", c)
      }

      // Main content area
      block {
        grow: true
        padding: responsive(spacing.3, md: spacing.5)
        background: semantic.surface
        overflow: auto
        layout: vertical, gap: spacing.5
        @children
      }
    }
  }
}
