// Font package: Orbitron
//
// Geometric display typeface with a sci-fi, space-age aesthetic.
// Best suited for headings and display text. Used as a companion
// to Rajdhani in the cyberpunk theme.
//
// Usage:
//   @import "font-orbitron/font.spec"

@fonts {
  "Orbitron": 400 "./woff2/orbitron-regular.woff2", 500 "./woff2/orbitron-medium.woff2", 600 "./woff2/orbitron-semibold.woff2", 700 "./woff2/orbitron-bold.woff2"
}

@visual-system {
  font.heading: "'Orbitron', 'Rajdhani', 'Consolas', sans-serif"

  // Larger ratio suits display/heading-only usage
  type-scale: 1.333-ratio, base 14px
}
