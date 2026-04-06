component FAB(
  icon: string = "plus",
  size: string = "md",
  label: string = ""
) {
  @computed {
    btnSize: match size {
      "sm" -> "40px",
      "lg" -> "64px",
      _ -> "56px"
    }
    iconSize: match size {
      "sm" -> "18px",
      "lg" -> "28px",
      _ -> "24px"
    }
  }

  block {
    position: "fixed"
    z-index: 800
    bottom: responsive(24px, md: 32px)
    right: 24px
    padding-bottom: env(safe-area-inset-bottom)

    block {
      width: label != "" ? "auto" : btnSize
      height: btnSize
      min-width: btnSize
      border-radius: label != "" ? "28px" : "50%"
      background: semantic.accent
      shadow: elevation.raised
      cursor: "pointer"
      layout: horizontal, align: center, justify: center, gap: 8px
      padding-x: label != "" ? spacing.4 : 0px
      transition: "transform 150ms ease, box-shadow 150ms ease"
      user-select: "none"

      on click: emit("click")
      on hover {
        transform: "scale(1.05)"
        shadow: elevation.floating
      }
      on active {
        transform: "scale(0.95)"
      }

      Icon(name: icon, size: iconSize, color: "white")

      text(label) {
        visibility: label != ""
        color: "white"
        style: type.label
        weight: 600
      }
    }
  }
}
