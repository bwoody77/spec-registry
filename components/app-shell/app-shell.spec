

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
    height: 100vh
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
