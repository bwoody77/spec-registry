// Font package: Fira Code
//
// Monospace font with programming ligatures. Popular choice for
// code-centric themes (dracula, geek, monokai, retro).
//
// Usage:
//   @import "font-fira-code/font.spec"
//
// Overrides font.mono. Pair with font-face.css for self-hosted woff2.

@fonts {
  "Fira Code": 400 "./woff2/fira-code-regular.woff2", 500 "./woff2/fira-code-medium.woff2", 600 "./woff2/fira-code-semibold.woff2", 700 "./woff2/fira-code-bold.woff2"
}

@visual-system {
  font.mono: "'Fira Code', 'Cascadia Code', 'Consolas', monospace"

  type-scale: 1.25-ratio, base 14px
}
