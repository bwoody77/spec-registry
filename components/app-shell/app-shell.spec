component AppShell(
  breakpoint: string = "md",
  mobileNav: string = "bottom-bar"
) {
  @state {
    isMobile: true
  }

  block {
    width: 100%
    height: 100vh
    overflow: "hidden"
    layout: vertical
    scroll-boundary: "contain"

    // Desktop layout (sidebar + content)
    block {
      visibility: isMobile == false
      grow: true
      layout: horizontal
      overflow: "hidden"

      // Sidebar
      block {
        width: responsive(0px, md: 280px)
        height: 100%
        overflow: "auto"
        border-right: borders.default
        background: semantic.surface
        @slot("sidebar")
      }

      // Main content area
      block {
        grow: true
        layout: vertical
        overflow: "hidden"

        // Header
        block {
          @slot("header")
        }

        // Content
        block {
          grow: true
          overflow: "auto"
          @children
        }
      }
    }

    // Mobile layout (content + bottom bar)
    block {
      visibility: isMobile == true
      grow: true
      layout: vertical
      overflow: "hidden"

      // Mobile header
      block {
        @slot("header")
      }

      // Content
      block {
        grow: true
        overflow: "auto"
        scroll-boundary: "contain"
        padding-bottom: env(safe-area-inset-bottom)
        @children
      }

      // Bottom bar slot
      block {
        visibility: mobileNav == "bottom-bar"
        @slot("bottom-bar")
      }
    }
  }
}
