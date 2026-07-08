// LoadingBlock — centered spinner + label for a loading section/panel.
// Drop-in for the "this region is fetching" case. tone 'on-dark' for dark panes.
component LoadingBlock(
  label:     string = "Loading…",
  tone:      string = "default",
  size:      string = "md",
  minHeight: string = "160px"
) {
  @computed {
    labelColor: match tone {
      "on-dark" -> "#aeb9cc",
      _ -> semantic.text-tertiary
    }
  }

  block {
    width: 100%
    min-height: minHeight
    layout: vertical, gap: 10px, justify: center, align: center

    Spinner(size: size, tone: tone)

    block {
      visibility: label != ""
      text(label) {
        style: type.body-sm
        weight: 500
        color: labelColor
      }
    }
  }
}
