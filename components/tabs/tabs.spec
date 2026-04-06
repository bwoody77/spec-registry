component Tabs(tabs: array, activeTab: string = "") {
  block {
    layout: vertical

    // Tab bar
    block {
      layout: horizontal, gap: 0px

      each tabs as tab {
        block {
          padding: spacing.3
          cursor: "pointer"
          position: relative
          border-radius: "6px 6px 0 0"
          overflow: visible
          transition: transition.interactive-full
          border-top: match tab.id == activeTab {
            true -> borders.default,
            _ -> "1px solid transparent"
          }
          border-left: match tab.id == activeTab {
            true -> borders.default,
            _ -> "1px solid transparent"
          }
          border-right: match tab.id == activeTab {
            true -> borders.default,
            _ -> "1px solid transparent"
          }
          border-bottom: match tab.id == activeTab {
            true -> "1px solid transparent",
            _ -> borders.default
          }
          on click: emit("change", tab.id)
          on hover {
            background: match tab.id == activeTab {
              true -> "transparent",
              _ -> semantic.surface-hover
            }
          }

          text(tab.label) {
            style: type.label-md
            weight: 500
            color: match tab.id == activeTab {
              true -> semantic.interactive,
              _ -> semantic.text-secondary
            }
          }
        }
      }

      // Filler — extends the bottom border to full width
      block {
        grow: true
        border-bottom: borders.default
      }
    }

    // Content area
    block {
      padding: spacing.4
      @children
    }
  }
}
