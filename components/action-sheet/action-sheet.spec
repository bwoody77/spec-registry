component ActionSheet(
  open: boolean = false,
  title: string = "",
  actions: array = []
) {
  @state {
    showing: false
  }

  @actions {
    doOpen() {
      showing = true
      lockScroll()
    }
    doClose() {
      showing = false
      unlockScroll()
      emit("close")
    }
    selectAction(actionId) {
      emit("select", actionId)
      doClose()
    }
  }

  @watch {
    open: {
      match open {
        true -> doOpen(),
        _ -> doClose()
      }
    }
  }

  overlay(visible: showing, anchor: "screen", align: "bottom", backdrop: "scrim") {
    on dismiss: doClose()

    block {
      padding-bottom: "env(safe-area-inset-bottom)"
      padding: spacing.2
      layout: vertical, gap: 8px

      // Actions container
      block {
        background: semantic.surface
        border-radius: 14px
        overflow: "hidden"
        layout: vertical

        // Title
        text(title) {
          visibility: title != ""
          style: type.caption
          color: semantic.text-tertiary
          padding: spacing.3
          text-transform: "uppercase"
          letter-spacing: "0.05em"
        }

        each actions as action {
          block {
            padding: spacing.3
            cursor: "pointer"
            layout: horizontal, align: center, justify: center
            border-top: borders.default
            on click: selectAction(action.id)
            on hover {
              background: semantic.surface-raised
            }

            text(action.label) {
              style: type.body
              color: match action.destructive {
                true -> "rgb(239, 68, 68)",
                _ -> semantic.accent
              }
              weight: 500
            }
          }
        }
      }

      // Cancel button
      block {
        background: semantic.surface
        border-radius: 14px
        padding: spacing.3
        cursor: "pointer"
        layout: horizontal, align: center, justify: center
        on click: doClose()
        on hover {
          background: semantic.surface-raised
        }

        text("Cancel") {
          style: type.body
          color: semantic.accent
          weight: 600
        }
      }
    }
  }
}
