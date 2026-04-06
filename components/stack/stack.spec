component Stack(direction: string = "vertical", gap: string = "0", align: string = "stretch", wrap: boolean = false) {
  // Vertical layout
  block {
    visibility: direction == "vertical"
    layout: vertical
    @children
  }

  // Horizontal layout
  block {
    visibility: direction == "horizontal"
    layout: horizontal
    @children
  }
}
