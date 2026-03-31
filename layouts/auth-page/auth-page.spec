// AuthPage — Login / signup / forgot-password page layout
//
// A full-viewport centered card on a tinted background. Provides slots for
// a logo/brand header, the form body, and a footer row (links, legal text).
// Works with every theme via semantic design tokens.
//
// Example usage:
//
//   AuthPage(title: 'Sign In') {
//     slot("logo") {
//       Icon(name: 'lock', size: 32, color: semantic.interactive)
//     }
//
//     // Default slot — the form
//     block {
//       layout: vertical, gap: spacing.3
//       TextInput(email) { placeholder: 'Email', type: 'email' }
//       TextInput(password) { placeholder: 'Password', type: 'password' }
//       Button(label: 'Sign In', variant: 'primary')
//     }
//
//     slot("footer") {
//       link('/forgot') { text('Forgot password?') }
//       text('·') { color: semantic.text-tertiary }
//       link('/signup') { text('Create account') }
//     }
//   }

component AuthPage(
  title: string = "",
  subtitle: string = "",
  maxWidth: string = "420px"
) {
  block {
    width: 100%
    min-height: 100vh
    background: semantic.background
    layout: vertical, align: center, justify: center
    padding: spacing.5
    padding-top: env(safe-area-inset-top)
    padding-bottom: env(safe-area-inset-bottom)

    // Card container
    block {
      width: 100%
      max-width: maxWidth
      background: semantic.surface
      border: borders.default
      border-radius: radius.lg
      shadow: elevation.layered
      padding: responsive(spacing.5, md: spacing.7)
      layout: vertical, gap: spacing.5, align: center

      // Logo slot
      block {
        visibility: hasSlot("logo")
        layout: horizontal, justify: center
        @slot("logo")
      }

      // Title
      block {
        visibility: title != ""
        layout: vertical, gap: spacing.1, align: center

        text(title) {
          style: type.heading-lg
          color: semantic.text-primary
          letter-spacing: "-0.02em"
        }

        block {
          visibility: subtitle != ""
          text(subtitle) {
            style: type.body-md
            color: semantic.text-secondary
          }
        }
      }

      // Form content (default slot)
      block {
        width: 100%
        layout: vertical, gap: spacing.4
        @children
      }

      // Footer slot (links, legal, etc.)
      block {
        visibility: hasSlot("footer")
        width: 100%
        padding-top: spacing.3
        border-top: borders.default
        layout: horizontal, gap: spacing.2, justify: center, align: center

        @slot("footer")
      }
    }
  }
}
