// `size` sizes the empty state to where it sits (Vector I-5657, I-5659):
// "sm" (default) is heading-xs over a 32px icon, the largest text an app page
// draws under its shell title, so a page or list's empty state never reads as a
// second page title; "md" is heading-sm over a 48px icon, for an empty state
// that IS the whole screen and wants to be large. Description, padding and
// layout are the same at both: the description is centered and capped near 60
// characters.
component EmptyState(message: text, description: text = "", size: string = "sm") {
  @computed {
    messageStyle: size == "md" ? type.heading-sm : type.heading-xs
    iconSize: size == "md" ? icon.xxl : icon.xl
  }

  block {
    layout: vertical, gap: spacing.2, align: center
    padding: spacing.6
    role: "status"

    Icon(name: "inbox", size: iconSize, color: semantic.text-tertiary)

    text(message) {
      style: messageStyle
      color: semantic.text-primary
    }

    // The description is centered under the message and stops near 60
    // characters (0.4.1, Vector I-5685). A one-line description centered only
    // because it shrank to fit; a longer one filled the card and its lines
    // started at the left edge, under a centered heading.
    block {
      visibility: description != ""
      layout: vertical
      max-width: '60ch'

      text(description) {
        style: type.body-md
        color: semantic.text-secondary
        text-align: 'center'
      }
    }
  }
}
