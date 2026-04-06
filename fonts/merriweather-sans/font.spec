// Font package: Merriweather Sans
//
// Warm, readable sans-serif with a slightly condensed feel.
// Companion to the Merriweather serif. Used by the earth theme.
//
// Usage:
//   @import "font-merriweather-sans/font.spec"

@fonts {
  "Merriweather Sans": 400 "./woff2/merriweather-sans-regular.woff2", 500 "./woff2/merriweather-sans-medium.woff2", 700 "./woff2/merriweather-sans-bold.woff2"
}

@visual-system {
  font.body: "'Merriweather Sans', 'Georgia', -apple-system, sans-serif"
  font.heading: "'Merriweather Sans', 'Georgia', -apple-system, sans-serif"

  type-scale: 1.25-ratio, base 14px
}
