component Timeline(items: array) {
  block {
    layout: vertical
    role: "list"

    each items as item, index {
      block {
        layout: horizontal
        role: "listitem"

        // Track: dot + connector line
        block {
          layout: vertical, align: center
          width: 24px
          min-width: 24px

          // Status dot
          block {
            width: 12px
            height: 12px
            min-width: 12px
            min-height: 12px
            border-radius: 9999px
            background: match item.status {
              "completed" -> "#22c55e", "active" -> "#3b82f6",
              "error" -> "#ef4444", _ -> "#9ca3af"
            }
          }
          // Connector line
          block {
            visibility: index != items.length - 1
            width: 2px
            min-width: 2px
            grow: true
            min-height: 24px
            background: match item.status {
              "completed" -> "#22c55e", "active" -> "#3b82f6",
              "error" -> "#ef4444", _ -> "#d1d5db"
            }
          }
        }

        // Content
        block {
          layout: vertical, gap: 2px
          padding: spacing.2
          grow: true

          block {
            visibility: item.date != ""
            text(item.date) {
              style: type.caption
              color: semantic.text-tertiary
            }
          }
          text(item.title) { style: type.body-md, color: semantic.text-primary }
          block {
            visibility: item.description != ""
            text(item.description) {
              style: type.body-md
              color: semantic.text-secondary
            }
          }
        }
      }
    }
  }
}
