// Image — lazy-loading image with skeleton placeholder and error fallback
component Image(
  src: string,
  alt: string,
  aspectRatio: string = "",
  lazy: boolean = false,
  fallbackSrc: string = ""
) {
  @state {
    loaded: false
    errored: false
  }

  @computed {
    displaySrc: errored ? (fallbackSrc != "" ? fallbackSrc : src) : src
    loadingAttr: lazy ? "lazy" : "eager"
  }

  @actions {
    handleLoad() { loaded = true }
    handleError() { errored = true
      loaded = true }
  }

  block {
    position: "relative"
    overflow: hidden
    width: 100%
    aspect-ratio: aspectRatio

    // Skeleton placeholder
    block {
      visibility: loaded == false
      position: "absolute"
      top: 0
      left: 0
      right: 0
      bottom: 0
      background: semantic.surface-raised
      animation: "pulse 1.5s ease-in-out infinite"
    }

    // Actual image
    image(displaySrc) {
      alt: alt
      loading: loadingAttr
      width: 100%
      height: 100%
      object-fit: "cover"
      opacity: match loaded { true -> 1, _ -> 0 }
      transition: "opacity 0.3s ease"
      on load: handleLoad()
      on error: handleError()
    }
  }
}
