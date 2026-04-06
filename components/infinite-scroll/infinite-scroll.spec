component InfiniteScroll(
  loading: boolean = false,
  hasMore: boolean = true
) {
  @actions {
    triggerLoad() {
      match loading == false && hasMore == true {
        true -> emit("loadMore"),
        _ -> {}
      }
    }
  }

  block {
    layout: vertical

    // Content
    @children

    // Loading indicator
    block {
      visibility: loading == true
      padding: spacing.4
      layout: horizontal, align: center, justify: center

      block {
        width: 24px
        height: 24px
        border-radius: 12px
        border: "2px solid rgba(0,0,0,0.15)"
        animation: "spin"
        opacity: 0.6
      }
    }

    // Sentinel element — triggers load when visible
    block {
      visibility: hasMore == true && loading == false
      height: 1px
      on visible: triggerLoad()
    }
  }
}
