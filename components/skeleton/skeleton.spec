// Skeleton — wave-shimmer loading placeholders.
// Primitives compose into content-shaped skeletons; `Skeleton` keeps its old
// signature for back-compat (now wave instead of pulse).

// One shimmering bar. The base block is the gray fill; the inner absolutely-
// positioned block is a moving light gradient (native `wave` keyframe).
component SkeletonLine(width: string = "100%", height: string = "12px") {
  block {
    width: width
    height: height
    border-radius: radius.sm
    background: token.skeleton-bg
    overflow: hidden
    position: "relative"

    block {
      position: "absolute"
      top: 0px
      left: 0px
      bottom: 0px
      width: 100%
      background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent)"
      animation: "wave"
    }
  }
}

component SkeletonBlock(width: string = "100%", height: string = "80px", radius: string = "10px") {
  block {
    width: width
    height: height
    border-radius: radius
    background: token.skeleton-bg
    overflow: hidden
    position: "relative"

    block {
      position: "absolute"
      top: 0px
      left: 0px
      bottom: 0px
      width: 100%
      background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent)"
      animation: "wave"
    }
  }
}

component SkeletonCircle(size: string = "40px") {
  block {
    width: size
    height: size
    border-radius: 9999px
    background: token.skeleton-bg
    overflow: hidden
    position: "relative"

    block {
      position: "absolute"
      top: 0px
      left: 0px
      bottom: 0px
      width: 100%
      background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent)"
      animation: "wave"
    }
  }
}

component SkeletonRow() {
  block {
    layout: horizontal, gap: 12px, align: center
    width: 100%

    SkeletonCircle(size: "38px")

    block {
      grow: true
      layout: vertical, gap: 7px
      SkeletonLine(width: "55%", height: "12px")
      SkeletonLine(width: "35%", height: "10px")
    }

    SkeletonBlock(width: "64px", height: "24px", radius: "6px")
  }
}

component SkeletonCard() {
  block {
    layout: vertical, gap: 10px
    padding: 16px
    border-radius: radius.md
    background: semantic.surface

    SkeletonLine(width: "45%", height: "14px")
    SkeletonLine(width: "80%", height: "10px")
    SkeletonLine(width: "70%", height: "10px")
  }
}

// Back-compat: original fixed shape (rectangle + avatar row), now wave.
component Skeleton(width: string = "100%", height: string = "") {
  block {
    width: width
    height: height
    layout: vertical, gap: spacing.3
    overflow: hidden

    SkeletonBlock(width: "100%", height: "80px", radius: "10px")
    SkeletonRow()
  }
}
