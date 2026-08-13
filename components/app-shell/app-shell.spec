

component AppShell(
  breakpoint: string = "md",
  mobileNav: string = "bottom-bar"
) {
  @state {
    isMobile: true
  }

  @actions {
    setMobile(val) {
      isMobile = val
    }
  }

  block {
    width: 100%
    // `dvh`, not `vh`. On iOS Safari `100vh` is the LARGE viewport — the height
    // with the URL bar collapsed — so while chrome is showing, a 100vh shell
    // overflows below the visible area. For an app shell that means the bottom
    // navigation, being the last child of the column, sits off-screen: the
    // "scroll twice before you can reach the tab bar" symptom. `dvh` tracks the
    // currently-visible viewport, so the shell is exactly as tall as what the
    // user can see and the bottom bar stays glued to the visible edge.
    //
    // Deliberately `dvh` and not `svh`: svh never resizes (no reflow as chrome
    // retracts) but leaves a band of background below the shell once the URL
    // bar hides. A shell should fill the screen; the reflow is the cost.
    height: 100dvh
    overflow: "hidden"
    layout: vertical
    scroll-boundary: "contain"

    // Main column (responsive() triggers breakpoint creation for isMobile detection)
    block {
      grow: true
      layout: vertical
      overflow: "hidden"
      min-width: responsive(0px, sm: 0px)

      // Header (desktop only — mobile uses bottom bar)
      block {
        visibility: isMobile == false
        @slot("header")
      }

      // Content — scroll container for page content
      scrollView {
        grow: true
        scroll-boundary: "contain"
        @children
      }
    }

    // Bottom bar (mobile only)
    block {
      visibility: isMobile == true && mobileNav == "bottom-bar"
      @slot("bottom-bar")
    }
  }
}
