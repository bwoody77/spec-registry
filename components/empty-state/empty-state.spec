component EmptyState(message: string, description: string = "") {
  block {
    layout: vertical, gap: spacing.2, align: center
    padding: spacing.6
    role: "status"

    Icon(name: "inbox", size: icon.xxl, color: semantic.text-tertiary)

    text(message) {
      style: type.heading-sm
      color: semantic.text-primary
    }

    text(description) {
      visibility: description != ""
      style: type.body-md
      color: semantic.text-secondary
    }
  }
}
