component Tooltip(text: string = "", placement: string = "top") {
  @state {
    visible: false
  }

  @actions {
    showTip() { delay("show", 300) { visible = true } }
    hideTip() {
      clearDelay("show")
      visible = false
    }
  }

  block {
    position: "relative"
    on mouse-enter: showTip()
    on mouse-leave: hideTip()
    on focus: showTip()
    on blur: hideTip()

    @children

    // Tooltip bubble — top
    block {
      visibility: visible == true && placement == "top"
      position: "absolute"
      z-index: 1000
      bottom: 100%
      left: 50%
      transform: "translateX(-50%)"
      margin: 8px
      padding: spacing.2
      background: "#1e293b"
      border-radius: 6px
      shadow: elevation.floating

      text(text) {
        style: type.label-sm
        color: "#f1f5f9"
      }
    }

    // Tooltip bubble — bottom
    block {
      visibility: visible == true && placement == "bottom"
      position: "absolute"
      z-index: 1000
      top: 100%
      left: 50%
      transform: "translateX(-50%)"
      margin: 8px
      padding: spacing.2
      background: "#1e293b"
      border-radius: 6px
      shadow: elevation.floating

      text(text) {
        style: type.label-sm
        color: "#f1f5f9"
      }
    }

    // Tooltip bubble — left
    block {
      visibility: visible == true && placement == "left"
      position: "absolute"
      z-index: 1000
      right: 100%
      top: 50%
      transform: "translateY(-50%)"
      margin: 8px
      padding: spacing.2
      background: "#1e293b"
      border-radius: 6px
      shadow: elevation.floating

      text(text) {
        style: type.label-sm
        color: "#f1f5f9"
      }
    }

    // Tooltip bubble — right
    block {
      visibility: visible == true && placement == "right"
      position: "absolute"
      z-index: 1000
      left: 100%
      top: 50%
      transform: "translateY(-50%)"
      margin: 8px
      padding: spacing.2
      background: "#1e293b"
      border-radius: 6px
      shadow: elevation.floating

      text(text) {
        style: type.label-sm
        color: "#f1f5f9"
      }
    }
  }
}
