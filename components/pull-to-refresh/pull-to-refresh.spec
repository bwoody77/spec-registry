component PullToRefresh(
  loading: boolean = false,
  threshold: number = 80
) {
  @state {
    pullDistance: 0
    pulling: false
  }

  @computed {
    indicatorOpacity: match pullDistance > 20 {
      true -> match pullDistance / threshold > 1 {
        true -> 1,
        _ -> pullDistance / threshold
      },
      _ -> 0
    }
    indicatorTransform: "translateY(" + match pullDistance > threshold {
      true -> threshold,
      _ -> pullDistance
    } + "px)"
  }

  @actions {
    handleDrag(delta) {
      match delta.y > 0 {
        true -> startPull(delta)
        _ -> noop()
      }
    }
    startPull(delta) {
      pulling = true
      pullDistance = delta.y * 0.5
    }
    noop() {}
    handleDragEnd(delta) {
      match pullDistance >= threshold {
        true -> emit("refresh")
        _ -> noop()
      }
      pullDistance = 0
      pulling = false
    }
  }

  block {
    position: "relative"
    overflow: "hidden"
    scroll-boundary: "contain"

    // Pull indicator
    block {
      visibility: pulling == true || loading == true
      position: "absolute"
      top: 0px
      left: 0px
      right: 0px
      height: 60px
      layout: horizontal, align: center, justify: center
      opacity: indicatorOpacity
      transform: indicatorTransform
      z-index: 1

      block {
        width: 24px
        height: 24px
        border-radius: 12px
        border: "2px solid rgba(0,0,0,0.1)"
        animation: loading ? "spin" : "none"
      }
    }

    // Content
    block {
      on drag(delta): handleDrag(delta)
      on drag-end(delta): handleDragEnd(delta)
      @children
    }
  }
}
