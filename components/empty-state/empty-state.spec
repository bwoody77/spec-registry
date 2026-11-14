// `size` sizes the message to where the empty state sits (Vector I-5657):
// "md" (default) is a page or list's own empty state, heading-sm; "sm" sits
// inside a titled card and must not outrank that card's title, so its message
// is heading-xs. Icon, description, padding and layout are the same at both.
component EmptyState(message: text, description: text = "", size: string = "md") {
  @computed {
    messageStyle: size == "sm" ? type.heading-xs : type.heading-sm
  }

  block {
    layout: vertical, gap: spacing.2, align: center
    padding: spacing.6
    role: "status"

    Icon(name: "inbox", size: icon.xxl, color: semantic.text-tertiary)

    text(message) {
      style: messageStyle
      color: semantic.text-primary
    }

    text(description) {
      visibility: description != ""
      style: type.body-md
      color: semantic.text-secondary
    }
  }
}
