// Font package: Roboto
//
// Google's neo-grotesque sans-serif. Default typeface for
// Material Design / MUI theme.
//
// Usage:
//   @import "font-roboto/font.spec"

@fonts {
  "Roboto": 400 "./woff2/roboto-regular.woff2", 500 "./woff2/roboto-medium.woff2", 700 "./woff2/roboto-bold.woff2"
}

@visual-system {
  font.body: "'Roboto', 'Helvetica Neue', -apple-system, sans-serif"
  font.heading: "'Roboto', 'Helvetica Neue', -apple-system, sans-serif"

  type-scale: 1.25-ratio, base 14px
}
