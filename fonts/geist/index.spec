// Font package: Geist
//
// Vercel's modern typeface family. Includes Geist Sans for body
// and heading text plus Geist Mono for code. Designed for
// clarity at small sizes with a neutral, contemporary feel.
//
// Usage:
//   @import "@spec/font-geist"
//
// Then add to your @visual-system:
//   font.body: "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
//   font.heading: "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
//   font.mono: "'Geist Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace"

@fonts {
  "Geist": 400 "./woff2/geist-regular.woff2", 500 "./woff2/geist-medium.woff2", 600 "./woff2/geist-semibold.woff2", 700 "./woff2/geist-bold.woff2"
  "Geist Mono": 400 "./woff2/geist-mono-regular.woff2", 500 "./woff2/geist-mono-medium.woff2", 700 "./woff2/geist-mono-bold.woff2"
}
