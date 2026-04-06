// Skeleton — loading placeholder with pulse animation
component Skeleton(width: string = "100%", height: string = "") {
  block {
    width: width
    height: height
    layout: vertical, gap: spacing.3
    overflow: hidden

    // Rectangle placeholder
    block {
      height: 80px
      background: token.skeleton-bg
      border-radius: radius.md
      opacity: 0.7
      animation: "pulse"
    }

    // Circle + text lines row
    block {
      layout: horizontal, gap: spacing.3, align: center

      // Circle
      block {
        width: 48px
        height: 48px
        border-radius: 9999px
        background: token.skeleton-bg
        opacity: 0.7
        animation: "pulse"
      }

      // Text lines
      block {
        grow: true
        layout: vertical, gap: spacing.2

        block {
          height: 14px
          background: token.skeleton-bg
          border-radius: radius.sm
          opacity: 0.7
          animation: "pulse"
        }
        block {
          height: 14px
          width: 70%
          background: token.skeleton-bg
          border-radius: radius.sm
          opacity: 0.7
          animation: "pulse"
        }
      }
    }
  }
}
