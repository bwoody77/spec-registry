// SettingsPage — Settings page with sidebar navigation
//
// A two-column layout: a left nav listing settings sections and a right
// content area for the active section. On mobile the nav stacks above
// the content. Emits "select" when a nav item is clicked.
// Works with every theme via semantic design tokens.
//
// Example usage:
//
//   @state { section: 'profile' }
//
//   SettingsPage(
//     title: 'Settings',
//     sections: [
//       {id: 'profile', label: 'Profile', icon: 'user'},
//       {id: 'notifications', label: 'Notifications', icon: 'bell'},
//       {id: 'security', label: 'Security', icon: 'lock'},
//       {id: 'billing', label: 'Billing', icon: 'credit-card'}
//     ],
//     activeSection: section
//   ) {
//     on select(id): { section = id }
//
//     // Default slot — the active section content
//     match section {
//       'profile' -> { ProfileSettings() },
//       'notifications' -> { NotificationSettings() },
//       _ -> { text('Select a section') }
//     }
//   }

component SettingsPage(
  title: string = "Settings",
  sections: array = [],
  activeSection: string = "",
  navWidth: string = "240px"
) {
  block {
    width: 100%
    layout: vertical, gap: spacing.5

    // Page title
    block {
      visibility: title != ""
      layout: horizontal, gap: spacing.3, align: center
      Icon(name: "settings", size: icon.md, color: semantic.interactive)
      text(title) {
        style: type.heading-lg
        color: semantic.text-primary
        letter-spacing: "-0.02em"
      }
    }

    // Two-column body
    block {
      layout: responsive(vertical, md: horizontal), gap: spacing.5
      grow: true

      // Left nav
      block {
        width: responsive(100%, md: navWidth)
        min-width: responsive(0px, md: navWidth)
        background: semantic.surface-raised
        border: borders.default
        border-radius: radius.lg
        padding: spacing.2
        layout: vertical, gap: spacing.1

        each sections as sec {
          block {
            layout: horizontal, gap: spacing.3, align: center
            padding: spacing.3
            border-radius: radius.md
            cursor: "pointer"
            background: sec.id == activeSection ? semantic.surface : "transparent"
            shadow: sec.id == activeSection ? elevation.raised : elevation.flat
            on hover { background: semantic.surface-hover }
            on click: emit("select", sec.id)

            block {
              visibility: sec.icon != null
              width: 20px
              min-width: 20px
              layout: horizontal, align: center, justify: center
              Icon(name: sec.icon, size: 18, color: sec.id == activeSection ? semantic.interactive : semantic.text-secondary)
            }

            text(sec.label) {
              style: type.body-md
              color: sec.id == activeSection ? semantic.text-primary : semantic.text-secondary
            }
          }
        }
      }

      // Right content area
      block {
        grow: true
        layout: vertical, gap: spacing.5
        @children
      }
    }
  }
}
