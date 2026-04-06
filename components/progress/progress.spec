// Progress — bar progress indicator with expression-based width
component Progress(value: number = 0, label: string = "") {
  block {
    height: 8px
    background: token.progress-trackBg
    border-radius: 4px
    overflow: hidden
    role: "progressbar"

    // Fill bar — width bound to value param
    block {
      height: 8px
      width: match value {
        0 -> "0%",
        _ -> "{value}%"
      }
      background: token.progress-fillBg
      border-radius: 4px
      transition: transition.fill
    }
  }
}
