// Font package: Rajdhani
//
// Angular sans-serif with Devanagari roots and a futuristic,
// tech-forward personality. Used by the cyberpunk theme.
//
// Usage:
//   @import "font-rajdhani/font.spec"

@fonts {
  "Rajdhani": 400 "./woff2/rajdhani-regular.woff2", 500 "./woff2/rajdhani-medium.woff2", 600 "./woff2/rajdhani-semibold.woff2", 700 "./woff2/rajdhani-bold.woff2"
}

@visual-system {
  font.body: "'Rajdhani', 'Orbitron', 'Consolas', sans-serif"
  font.heading: "'Rajdhani', 'Orbitron', 'Consolas', sans-serif"

  type-scale: 1.25-ratio, base 15px
}
