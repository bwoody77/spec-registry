// Font package: Source Code Pro
//
// Adobe's open-source monospace typeface. Clean and highly
// readable at small sizes. Used as a fallback in the monokai theme.
//
// Usage:
//   @import "font-source-code-pro/font.spec"

@fonts {
  "Source Code Pro": 400 "./woff2/source-code-pro-regular.woff2", 500 "./woff2/source-code-pro-medium.woff2", 700 "./woff2/source-code-pro-bold.woff2"
}

@visual-system {
  font.mono: "'Source Code Pro', 'Fira Code', 'Consolas', monospace"

  type-scale: 1.25-ratio, base 14px
}
