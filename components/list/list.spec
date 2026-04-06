component List(items: array = [], selection: string = "none", selected: array = [], searchable: boolean = false, searchPlaceholder: string = "Search...", height: string = "") {
  @state {
    selectedIds: selected
    searchQuery: ""
  }

  @computed {
    filteredItems: searchQuery != "" ? items.filter(item => item.label.toLowerCase().includes(searchQuery.toLowerCase())) : items
    hasItems: filteredItems.length > 0
  }

  @actions {
    setSearch(v) {
      searchQuery = v
      emit("search", v)
    }
    handleSelect(id) {
      if selection == "single" {
        selectedIds = [id]
        emit("selection-change", selectedIds)
      } else {
        if selection == "multi" {
          if selectedIds.includes(id) {
            selectedIds = selectedIds.filter(sid => sid != id)
          } else {
            selectedIds = selectedIds + [id]
          }
          emit("selection-change", selectedIds)
        }
      }
    }
  }

  block {
    layout: vertical

    // Search input
    block {
      visibility: searchable
      padding: spacing.2
      border-bottom: borders.default

      TextInput(placeholder: searchPlaceholder, value: searchQuery) {
        on change(v): setSearch(v)
      }
    }

    // List items
    block {
      layout: vertical
      overflow: "auto"

      each filteredItems as item {
        block {
          layout: horizontal, align: center
          padding: spacing.2
          cursor: item.disabled == true ? "default" : "pointer"
          opacity: item.disabled == true ? 0.5 : 1
          background: selectedIds.includes(item.id) ? semantic.surface-raised : "transparent"
          on hover { background: semantic.surface-raised }
          on click: handleSelect(item.id)

          text(item.label) {
            style: type.body-md
            color: selectedIds.includes(item.id) ? semantic.interactive : semantic.text-primary
          }
        }
      }
    }

    // Empty state
    block {
      visibility: hasItems == false
      padding: spacing.3
      layout: horizontal, justify: center
      text("No items") { style: type.body-md, color: semantic.text-tertiary }
    }
  }
}
