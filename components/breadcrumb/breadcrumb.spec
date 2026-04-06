component Breadcrumb(items: array, separator: string = "/", maxVisible: number = 0) {
  @state { expanded: false }
  @watch {
    maxVisible: { expanded = false }
  }
  @actions {
    expand() { expanded = true }
  }

  block {
    layout: horizontal, gap: 4px, align: center
    role: "navigation"
    aria-label: "Breadcrumb"

    each items as item, index {
      // Separator — shown before visible items and before the ellipsis
      block {
        visibility: index > 0 && (expanded || maxVisible == 0 || items.length <= maxVisible || index == 1 || index >= items.length - maxVisible + 1)
        text(separator) {
          style: type.body-md
          color: semantic.text-tertiary
        }
      }
      // Ellipsis expander — only at index 1 when collapsed
      block {
        visibility: !expanded && maxVisible > 0 && items.length > maxVisible && index == 1
        cursor: "pointer"
        on click: expand()
        on hover { opacity: 0.8 }
        text("\u2026") {
          style: type.body-md
          color: semantic.interactive
        }
      }
      // Non-last items: clickable link
      block {
        visibility: index != items.length - 1 && (expanded || maxVisible == 0 || items.length <= maxVisible || index == 0 || index >= items.length - maxVisible + 1)
        cursor: "pointer"
        on click: emit("select", item)
        on hover { opacity: 0.8 }
        text(item.label) {
          style: type.body-md
          color: semantic.interactive
          text-decoration: "underline"
        }
      }
      // Last item: plain text (current page)
      block {
        visibility: index == items.length - 1
        text(item.label) {
          style: type.body-md
          color: semantic.text-primary
        }
      }
    }
  }
}
