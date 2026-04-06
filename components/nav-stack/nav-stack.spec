component NavStack(
  showBackButton: boolean = true,
  title: string = ""
) {
  @state {
    canGoBack: false
  }

  @actions {
    goBack() {
      emit("back")
    }
  }

  block {
    width: 100%
    height: 100%
    layout: vertical
    overflow: "hidden"

    // Navigation header
    block {
      height: 56px
      padding-x: spacing.3
      padding-top: env(safe-area-inset-top)
      background: semantic.surface
      border-bottom: borders.default
      layout: horizontal, align: center, gap: 8px

      // Back button
      block {
        visibility: showBackButton == true && canGoBack == true
        width: 40px
        height: 40px
        border-radius: 20px
        cursor: "pointer"
        layout: horizontal, align: center, justify: center
        on click: goBack()
        on swipe-right: goBack()
        on hover {
          background: semantic.surface-raised
        }

        Icon(name: "arrow-left", size: "20px", color: semantic.text-primary)
      }

      // Title
      text(title) {
        visibility: title != ""
        grow: true
        style: type.heading-sm
        color: semantic.text-primary
        weight: 600
      }

      // Right actions slot
      block {
        layout: horizontal, align: center, gap: 4px
        @slot("actions")
      }
    }

    // Content
    block {
      grow: true
      overflow: "auto"
      scroll-boundary: "contain"
      @children
    }
  }
}
