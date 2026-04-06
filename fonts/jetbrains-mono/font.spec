// Font package: JetBrains Mono
//
// Monospace font designed for developers. Increased letter height
// for better readability at small sizes, with coding ligatures.
//
// Usage:
//   @import "font-jetbrains-mono/font.spec"
//
// Overrides font.mono (code blocks, mono-* type scale tokens).
// Pair with font-face.css for self-hosted woff2.

@fonts {
  "JetBrains Mono": 400 "./woff2/jetbrains-mono-regular.woff2", 500 "./woff2/jetbrains-mono-medium.woff2", 700 "./woff2/jetbrains-mono-bold.woff2"
}

@visual-system {
  font.mono: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace"

  // Type scale tuned for JetBrains Mono metrics
  type-scale: 1.25-ratio, base 14px
}
