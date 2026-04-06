component Carousel(
  items: array = [],
  autoPlay: boolean = false,
  interval: number = 5000,
  showDots: boolean = true
) {
  @state {
    currentIndex: 0
  }

  @actions {
    goTo(index) {
      currentIndex = index
      emit("slideChange", index)
    }
    next() {
      currentIndex = match currentIndex >= items.length - 1 {
        true -> 0,
        _ -> currentIndex + 1
      }
      emit("slideChange", currentIndex)
    }
    prev() {
      currentIndex = match currentIndex <= 0 {
        true -> items.length - 1,
        _ -> currentIndex - 1
      }
      emit("slideChange", currentIndex)
    }
  }

  block {
    position: "relative"
    overflow: "hidden"
    user-select: "none"

    // Slides container
    block {
      layout: horizontal
      width: 100%
      overflow: "auto"
      scroll-snap: "x"
      scroll-boundary: "contain"

      on swipe-left: next()
      on swipe-right: prev()

      each items as item, index {
        block {
          min-width: 100%
          width: 100%
          snap-align: "center"
          @slot("slide", item)
        }
      }
    }

    // Navigation dots
    block {
      visibility: showDots == true && items.length > 1
      position: "absolute"
      bottom: 12px
      left: 0px
      right: 0px
      layout: horizontal, align: center, justify: center, gap: 6px

      each items as item, index {
        block {
          width: match currentIndex == index {
            true -> 20px,
            _ -> 8px
          }
          height: 8px
          border-radius: 4px
          background: match currentIndex == index {
            true -> semantic.accent,
            _ -> "rgba(255, 255, 255, 0.5)"
          }
          cursor: "pointer"
          transition: "width 200ms ease, background 200ms ease"
          on click: goTo(index)
        }
      }
    }
  }
}
