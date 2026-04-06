// Font package: Inter
//
// Clean, versatile sans-serif optimized for screen readability.
// Default sans-serif for the Spec ecosystem.
//
// Usage:
//   @import "font-inter/font.spec"
//
// Provides font.body and font.heading overrides. Pair with
// font-face.css for self-hosted woff2 (no CDN dependency).

@fonts {
  "Inter": 400 "./woff2/inter-regular.woff2", 500 "./woff2/inter-medium.woff2", 600 "./woff2/inter-semibold.woff2", 700 "./woff2/inter-bold.woff2"
}

@visual-system {
  font.body: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
  font.heading: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

  // Type scale tuned for Inter's x-height and metrics
  type-scale: 1.25-ratio, base 14px
}
