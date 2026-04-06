component Pagination(total: number, pageSize: number = 10, page: number = 1, maxButtons: number = 7) {
  @computed {
    totalPages: total > 0 ? (total % pageSize == 0 ? total / pageSize : (total - total % pageSize) / pageSize + 1) : 1
    currentPage: page < 1 ? 1 : (page > totalPages ? totalPages : page)
    startItem: (currentPage - 1) * pageSize + 1
    endItem: currentPage * pageSize > total ? total : currentPage * pageSize
    hasPrev: currentPage > 1
    hasNext: currentPage < totalPages
  }

  block {
    layout: horizontal, gap: spacing.2, align: center
    role: "navigation"
    aria-label: "Pagination"

    // Total display
    text("{startItem}-{endItem} of {total}") {
      style: type.body-sm
      color: semantic.text-secondary
    }

    block {
      layout: horizontal, gap: spacing.1

      // Previous button
      block {
        padding: spacing.2
        min-width: 32px
        min-height: 32px
        border-radius: radius.md
        cursor: hasPrev ? "pointer" : "default"
        opacity: hasPrev ? 1 : 0.4
        layout: horizontal, align: center, justify: center
        on hover { background: hasPrev ? semantic.surface-raised : "transparent" }
        on click: { if hasPrev { emit("change", currentPage - 1) } }
        text("\u2039") { style: type.body-md, color: semantic.text-primary }
      }

      // Page 1
      block {
        padding: spacing.2
        min-width: 32px
        min-height: 32px
        border-radius: radius.md
        cursor: "pointer"
        background: currentPage == 1 ? semantic.interactive : "transparent"
        layout: horizontal, align: center, justify: center
        on hover { background: currentPage == 1 ? semantic.interactive : semantic.surface-raised }
        on click: emit("change", 1)
        text("1") {
          style: type.body-md
          color: currentPage == 1 ? "#ffffff" : semantic.text-secondary
        }
      }

      // Left ellipsis
      block {
        visibility: currentPage > 3 && totalPages > maxButtons
        padding: spacing.2
        min-width: 32px
        layout: horizontal, align: center, justify: center
        text("\u2026") { style: type.body-md, color: semantic.text-tertiary }
      }

      // Page before current
      block {
        visibility: totalPages > 2 && currentPage - 1 > 1
        padding: spacing.2
        min-width: 32px
        min-height: 32px
        border-radius: radius.md
        cursor: "pointer"
        background: "transparent"
        layout: horizontal, align: center, justify: center
        on hover { background: semantic.surface-raised }
        on click: emit("change", currentPage - 1)
        text("{currentPage - 1}") { style: type.body-md, color: semantic.text-secondary }
      }

      // Current page (when not first or last)
      block {
        visibility: currentPage > 1 && currentPage < totalPages
        padding: spacing.2
        min-width: 32px
        min-height: 32px
        border-radius: radius.md
        background: semantic.interactive
        layout: horizontal, align: center, justify: center
        text("{currentPage}") { style: type.body-md, color: "#ffffff" }
      }

      // Page after current
      block {
        visibility: totalPages > 2 && currentPage + 1 < totalPages
        padding: spacing.2
        min-width: 32px
        min-height: 32px
        border-radius: radius.md
        cursor: "pointer"
        background: "transparent"
        layout: horizontal, align: center, justify: center
        on hover { background: semantic.surface-raised }
        on click: emit("change", currentPage + 1)
        text("{currentPage + 1}") { style: type.body-md, color: semantic.text-secondary }
      }

      // Right ellipsis
      block {
        visibility: currentPage < totalPages - 2 && totalPages > maxButtons
        padding: spacing.2
        min-width: 32px
        layout: horizontal, align: center, justify: center
        text("\u2026") { style: type.body-md, color: semantic.text-tertiary }
      }

      // Last page
      block {
        visibility: totalPages > 1
        padding: spacing.2
        min-width: 32px
        min-height: 32px
        border-radius: radius.md
        cursor: "pointer"
        background: currentPage == totalPages ? semantic.interactive : "transparent"
        layout: horizontal, align: center, justify: center
        on hover { background: currentPage == totalPages ? semantic.interactive : semantic.surface-raised }
        on click: emit("change", totalPages)
        text("{totalPages}") {
          style: type.body-md
          color: currentPage == totalPages ? "#ffffff" : semantic.text-secondary
        }
      }

      // Next button
      block {
        padding: spacing.2
        min-width: 32px
        min-height: 32px
        border-radius: radius.md
        cursor: hasNext ? "pointer" : "default"
        opacity: hasNext ? 1 : 0.4
        layout: horizontal, align: center, justify: center
        on hover { background: hasNext ? semantic.surface-raised : "transparent" }
        on click: { if hasNext { emit("change", currentPage + 1) } }
        text("\u203A") { style: type.body-md, color: semantic.text-primary }
      }
    }
  }
}
