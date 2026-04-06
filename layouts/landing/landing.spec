// Landing — Hero + sections marketing landing page
//
// A full-viewport scrollable page with a hero section at the top,
// a slot for arbitrary content sections, and a footer. Each section is
// full-width with centered, max-width content. Responsive by default.
// Works with every theme via semantic design tokens.
//
// Example usage:
//
//   Landing(heroTitle: 'Ship faster with Spec', heroSubtitle: 'A declarative UI language that compiles to minimal JS.') {
//     slot("hero-actions") {
//       Button(label: 'Get Started', variant: 'primary')
//       Button(label: 'Learn More', variant: 'secondary')
//     }
//
//     // Default slot — page sections
//     LandingSection(title: 'Features') {
//       block {
//         layout: grid, columns: responsive("1fr", md: "1fr 1fr 1fr"), gap: spacing.5
//         Card() { text('Fast') }
//         Card() { text('Small') }
//         Card() { text('Typed') }
//       }
//     }
//
//     slot("footer") {
//       text('© 2026 Acme Inc.') { color: semantic.text-tertiary }
//     }
//   }

component Landing(
  heroTitle: string = "",
  heroSubtitle: string = "",
  maxWidth: string = "1200px"
) {
  block {
    width: 100%
    min-height: 100vh
    background: semantic.background
    overflow: auto
    layout: vertical
    padding-top: env(safe-area-inset-top)

    // Navigation bar (optional)
    block {
      visibility: hasSlot("nav")
      width: 100%
      padding-y: spacing.3
      padding-x: responsive(spacing.4, md: spacing.6)
      background: semantic.surface
      border-bottom: borders.default
      layout: horizontal, align: center, justify: between

      block {
        width: 100%
        max-width: maxWidth
        layout: horizontal, align: center, justify: between
        @slot("nav")
      }
    }

    // Hero section
    block {
      width: 100%
      padding-y: responsive(spacing.8, md: spacing.10)
      padding-x: responsive(spacing.4, md: spacing.6)
      background: semantic.surface
      layout: vertical, align: center

      block {
        width: 100%
        max-width: maxWidth
        layout: vertical, gap: spacing.5, align: center

        block {
          visibility: heroTitle != ""
          layout: vertical, gap: spacing.3, align: center
          max-width: 800px

          text(heroTitle) {
            style: type.heading-xl
            color: semantic.text-primary
            letter-spacing: "-0.03em"
          }

          block {
            visibility: heroSubtitle != ""
            text(heroSubtitle) {
              style: type.body-lg
              color: semantic.text-secondary
            }
          }
        }

        // Hero actions slot (CTA buttons)
        block {
          visibility: hasSlot("hero-actions")
          layout: responsive(vertical, md: horizontal), gap: spacing.3, align: center
          @slot("hero-actions")
        }

        // Hero media slot (screenshot, illustration, video)
        block {
          visibility: hasSlot("hero-media")
          width: 100%
          layout: horizontal, justify: center
          @slot("hero-media")
        }
      }
    }

    // Content sections (default slot)
    block {
      width: 100%
      grow: true
      layout: vertical
      @children
    }

    // Footer
    block {
      visibility: hasSlot("footer")
      width: 100%
      padding-y: spacing.5
      padding-x: responsive(spacing.4, md: spacing.6)
      background: semantic.surface
      border-top: borders.default
      layout: horizontal, justify: center

      block {
        width: 100%
        max-width: maxWidth
        layout: responsive(vertical, md: horizontal), gap: spacing.4, justify: between, align: center
        @slot("footer")
      }
    }
  }
}

// LandingSection — A full-width band with centered, max-width content.
// Use inside the Landing default slot.
//
// Example:
//   LandingSection(title: 'Features', subtitle: 'Everything you need.') {
//     block { layout: grid, columns: "1fr 1fr 1fr", gap: spacing.4
//       Card() { text('Fast') }
//     }
//   }

component LandingSection(
  title: string = "",
  subtitle: string = "",
  maxWidth: string = "1200px",
  background: string = ""
) {
  block {
    width: 100%
    padding-y: responsive(spacing.7, md: spacing.9)
    padding-x: responsive(spacing.4, md: spacing.6)
    background: background != "" ? background : "transparent"
    layout: vertical, align: center

    block {
      width: 100%
      max-width: maxWidth
      layout: vertical, gap: spacing.5

      // Section heading
      block {
        visibility: title != ""
        layout: vertical, gap: spacing.2, align: center

        text(title) {
          style: type.heading-lg
          color: semantic.text-primary
          letter-spacing: "-0.02em"
        }

        block {
          visibility: subtitle != ""
          max-width: 640px
          text(subtitle) {
            style: type.body-lg
            color: semantic.text-secondary
          }
        }
      }

      // Section content
      @children
    }
  }
}
