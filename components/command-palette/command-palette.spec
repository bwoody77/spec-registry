component CommandPalette(commands: array = [], open: boolean = false, placeholder: string = "Type a command...", maxResults: number = 50) {
  @state {
    query: ""
    highlightIndex: 0
  }

  @computed {
    filtered: query != "" ? commands.filter(c => c.label.toLowerCase().includes(query.toLowerCase())) : commands
    results: filtered.length > maxResults ? filtered.slice(0, maxResults) : filtered
    hasResults: results.length > 0
  }

  @actions {
    setQuery(v) {
      query = v
      highlightIndex = 0
    }
    selectItem(id) {
      emit("select", id)
      query = ""
      highlightIndex = 0
    }
    dismiss() {
      emit("close")
      query = ""
      highlightIndex = 0
    }
  }

  // Modal backdrop
  block {
    visibility: open == true
    position: "fixed"
    top: 0px
    left: 0px
    right: 0px
    bottom: 0px
    z-index: 9000
    background: "rgba(0, 0, 0, 0.5)"
    layout: horizontal, align: center, justify: center
    on click: dismiss()

    // Dialog panel
    block {
      width: 560px
      max-width: 90vw
      max-height: 480px
      background: semantic.surface
      border: borders.default
      border-radius: 12px
      shadow: elevation.floating
      overflow: hidden
      layout: vertical
      on click: {}

      // Search input
      block {
        padding: spacing.3
        border-bottom: borders.default

        TextInput(placeholder: placeholder, value: query) {
          on change(v): setQuery(v)
        }
      }

      // Results list
      block {
        overflow: auto
        max-height: 360px
        layout: vertical

        block {
          visibility: hasResults
          layout: vertical

          each results as cmd, idx {
            block {
              layout: horizontal, justify: between, align: center
              padding: spacing.3
              cursor: "pointer"
              background: idx == highlightIndex ? semantic.surface-raised : "transparent"
              on hover { background: semantic.surface-raised }
              on click: selectItem(cmd.id)

              block {
                layout: vertical, gap: spacing.1
                text(cmd.label) { style: type.body-md, color: semantic.text-primary }
                block {
                  visibility: cmd.description != null
                  text(cmd.description) { style: type.caption, color: semantic.text-tertiary }
                }
              }

              // Shortcut badge
              block {
                visibility: cmd.shortcut != null
                padding: spacing.1
                background: semantic.surface-raised
                border: borders.default
                border-radius: radius.sm
                text(cmd.shortcut) { style: type.caption, color: semantic.text-secondary }
              }
            }
          }
        }

        // Empty state
        block {
          visibility: hasResults == false && query != ""
          padding: spacing.4
          layout: horizontal, justify: center
          text("No matching commands") { style: type.body-md, color: semantic.text-tertiary }
        }
      }
    }
  }
}
