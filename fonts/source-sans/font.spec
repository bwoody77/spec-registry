// Font package: Source Sans 3
//
// Adobe's open-source humanist sans-serif. Successor to Source
// Sans Pro. Used by the solarized theme.
//
// Usage:
//   @import "font-source-sans/font.spec"

@fonts {
  "Source Sans 3": 400 "./woff2/source-sans-3-regular.woff2", 600 "./woff2/source-sans-3-semibold.woff2", 700 "./woff2/source-sans-3-bold.woff2"
}

@visual-system {
  font.body: "'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', -apple-system, sans-serif"
  font.heading: "'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', -apple-system, sans-serif"

  type-scale: 1.25-ratio, base 15px
}
