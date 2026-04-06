// Font package: DM Sans
//
// Clean geometric sans-serif with a friendly, modern feel.
// Low contrast strokes and open apertures give it excellent
// readability at any size.
//
// Usage:
//   @import "font-dm-sans/font.spec"
//
// Provides font.body and font.heading overrides. Pair with
// font-face.css for self-hosted woff2.

@fonts {
  "DM Sans": 400 "./woff2/dm-sans-regular.woff2", 500 "./woff2/dm-sans-medium.woff2", 600 "./woff2/dm-sans-semibold.woff2", 700 "./woff2/dm-sans-bold.woff2"
}

@visual-system {
  font.body: "'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
  font.heading: "'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"

  // Type scale tuned for DM Sans metrics — slightly larger base
  // to compensate for the font's compact x-height
  type-scale: 1.25-ratio, base 15px
}
