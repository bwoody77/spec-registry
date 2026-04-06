// Font package: Playfair Display
//
// Elegant serif typeface with high contrast and distinctive
// details. Best suited for headings and editorial layouts.
// Body text falls back to a system sans-serif for readability.
//
// Usage:
//   @import "font-playfair/font.spec"
//
// Sets font.heading to Playfair Display while keeping font.body
// as a readable sans-serif. Pair with font-face.css for
// self-hosted woff2.

@fonts {
  "Playfair Display": 400 "./woff2/playfair-display-regular.woff2", 500 "./woff2/playfair-display-medium.woff2", 600 "./woff2/playfair-display-semibold.woff2", 700 "./woff2/playfair-display-bold.woff2"
}

@visual-system {
  font.body: "'Georgia', 'Times New Roman', serif"
  font.heading: "'Playfair Display', 'Georgia', 'Times New Roman', serif"

  // Type scale tuned for Playfair — larger ratio for dramatic
  // heading hierarchy that suits editorial design
  type-scale: 1.333-ratio, base 16px
}
