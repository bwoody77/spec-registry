component TreeNode(node: object, level: number = 1, expandedIds: array = [], selectedIds: array = [], selectionMode: string = "none", expandMode: string = "icon") {
  @computed {
    isExpanded: expandedIds.includes(node.id)
    isSelected: selectedIds.includes(node.id)
    hasChildren: node.children != null && node.children.length > 0
    toggleIcon: isExpanded ? "▾" : "▸"
  }

  @actions {
    handleToggle() {
      if expandMode == "icon" {
        emit("toggle", node.id)
      }
    }
    handleSelect() {
      if node.disabled != true && selectionMode != "none" {
        emit("select", node.id)
      }
    }
    handleRowClick() {
      if expandMode == "row" {
        if hasChildren {
          emit("toggle", node.id)
        } else {
          handleSelect()
        }
      } else {
        handleSelect()
      }
    }
  }

  block {
    layout: vertical

    // Node row
    block {
      layout: horizontal, align: center
      padding-top: spacing.1
      padding-bottom: spacing.1
      cursor: node.disabled == true ? "default" : "pointer"
      opacity: node.disabled == true ? 0.5 : 1
      on hover { background: node.disabled == true ? "transparent" : semantic.surface-raised }
      on click: handleRowClick()
      role: "treeitem"

      // Expand/collapse toggle
      block {
        visibility: hasChildren
        width: 20px
        min-width: 20px
        cursor: "pointer"
        on click: handleToggle()

        text(toggleIcon) { style: type.body-md, color: semantic.text-secondary }
      }
      block {
        visibility: hasChildren == false
        width: 20px
        min-width: 20px
      }

      // Icon (if node has an icon field)
      block {
        visibility: node.icon != null
        layout: horizontal, align: center, justify: center
        width: 20px
        min-width: 20px

        Icon(name: node.icon != null ? node.icon : "", size: 16, color: semantic.text-secondary)
      }

      // Label
      text(node.label) {
        style: type.body-md
        color: isSelected ? semantic.interactive : semantic.text-primary
        weight: isSelected ? 600 : 400
        padding-left: spacing.1
      }
    }

    // Children (recursive) — indentation via padding-left
    block {
      visibility: isExpanded && hasChildren
      layout: vertical
      padding-left: 20px

      each node.children as child {
        TreeNode(node: child, level: level + 1, expandedIds: expandedIds, selectedIds: selectedIds, selectionMode: selectionMode, expandMode: expandMode) {
          on toggle(id): emit("toggle", id)
          on select(id): emit("select", id)
        }
      }
    }
  }
}

component Tree(nodes: array, selection: string = "none", selected: array = [], expanded: array = [], expandMode: string = "icon") {
  @state {
    expandedIds: expanded @persist
    selectedIds: selected @persist
  }

  @actions {
    handleToggle(id) {
      if expandedIds.includes(id) {
        expandedIds = expandedIds.filter(eid => eid != id)
        emit("collapse", id)
      } else {
        expandedIds = expandedIds + [id]
        emit("expand", id)
      }
    }
    handleSelect(id) {
      if selection == "single" {
        selectedIds = [id]
      } else {
        if selection == "multi" {
          if selectedIds.includes(id) {
            selectedIds = selectedIds.filter(sid => sid != id)
          } else {
            selectedIds = selectedIds + [id]
          }
        }
      }
      emit("select", id)
      emit("selection-change", selectedIds)
    }
  }

  block {
    layout: vertical
    tabindex: "0"
    role: "tree"
    aria-label: "Tree navigation"

    each nodes as node {
      TreeNode(node: node, level: 1, expandedIds: expandedIds, selectedIds: selectedIds, selectionMode: selection, expandMode: expandMode) {
        on toggle(id): handleToggle(id)
        on select(id): handleSelect(id)
      }
    }
  }
}
