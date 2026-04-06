// Accordion — collapsible sections with single or multi-expand mode
component Accordion(items: array, multiple: boolean = false) {
  @state {
    openIds: []
  }

  @actions {
    toggle(id) {
      openIds = match openIds.includes(id) {
        // Closing: always just remove the id
        true -> openIds.filter(x => x != id),
        // Opening: in single mode, replace; in multi mode, append
        _ -> match multiple {
          true -> openIds.concat([id]),
          _ -> [id]
        }
      }
      emit("change", openIds)
    }
  }

  block {
    layout: vertical
    border: borders.default
    border-radius: 8px
    overflow: "hidden"

    each items as item {
      block {
        layout: vertical

        // Header button
        block {
          layout: horizontal, gap: spacing.2, align: center
          padding: spacing.3
          cursor: "pointer"
          background: semantic.surface
          border-bottom: borders.default
          on click: toggle(item.id)
          on hover { background: semantic.surface-raised }

          text(item.title) {
            style: type.body-md
            weight: 500
            color: semantic.text-primary
            grow: true
          }
          text(match openIds.includes(item.id) { true -> "−", _ -> "+" }) {
            style: type.body-md
            color: semantic.text-tertiary
          }
        }

        // Content panel
        block {
          max-height: match openIds.includes(item.id) { true -> "500px", _ -> "0" }
          overflow: "hidden"
          transition: transition.expand

          block {
            padding: spacing.3
            text(item.content) {
              style: type.body-md
              color: semantic.text-secondary
            }
          }
        }
      }
    }
  }
}
