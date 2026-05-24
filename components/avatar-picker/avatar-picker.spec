@extern { pickImageFile, cropAvatarToDataUrl } from "@spec/components/avatar-picker.js"

component AvatarPicker(currentAvatarUrl: string = "", initials: string = "", fallbackColor: string = "#7585a0", buttonLabel: string = "", removable: boolean = true, cropSize: number = 256, size: number = 64) {
  @state {
    cropOpen: false
    imageSrc: ""
    zoom: 1
    // Pan offset of the preview image in CSS pixels. dragBase{X,Y} hold the
    // committed offset at drag-start so each drag is additive.
    panTx: 0
    panTy: 0
    dragBaseX: 0
    dragBaseY: 0
    busy: false
  }

  @computed {
    hasAvatar: currentAvatarUrl != ""
    pickLabel: buttonLabel != "" ? buttonLabel : (hasAvatar ? "Change photo" : "Add photo")
    avatarPx: size + "px"
    // Half the preview side (260 / 2). Pan is bounded by this × (zoom-1) so
    // the cropped circle always stays filled with image pixels.
    panMaxAbs: zoom > 1 ? 130 * (zoom - 1) : 0
    panMaxNeg: zoom > 1 ? -130 * (zoom - 1) : 0
    // CSS transform applied to the preview image. Order matters: translate
    // first (post-scale frame), then scale.
    zoomTransform: "translate(" + panTx + "px," + panTy + "px) scale(" + zoom + ")"
    // Offsets in [-1, 1] expected by cropAvatarToDataUrl. Dragging the
    // image right (panTx>0) shifts the visible portion left, so the crop
    // centre moves left — sign-flipped.
    cropOffsetX: panMaxAbs > 0 ? (0 - panTx) / panMaxAbs : 0
    cropOffsetY: panMaxAbs > 0 ? (0 - panTy) / panMaxAbs : 0
  }

  @actions {
    pickPhoto() {
      busy = true
      let src = await pickImageFile()
      busy = false
      if src != "" {
        imageSrc = src
        zoom = 1
        panTx = 0
        panTy = 0
        dragBaseX = 0
        dragBaseY = 0
        cropOpen = true
      }
    }

    cancelCrop() {
      cropOpen = false
      imageSrc = ""
      zoom = 1
      panTx = 0
      panTy = 0
      dragBaseX = 0
      dragBaseY = 0
    }

    applyCrop() {
      busy = true
      let dataUrl = await cropAvatarToDataUrl(imageSrc, zoom, cropOffsetX, cropOffsetY, cropSize)
      busy = false
      cropOpen = false
      imageSrc = ""
      zoom = 1
      panTx = 0
      panTy = 0
      dragBaseX = 0
      dragBaseY = 0
      emit("change", dataUrl)
    }

    removePhoto() {
      emit("remove")
    }

    onZoom(v) {
      zoom = v
      // Re-clamp pan when zoom changes — slack shrinks at lower zoom.
      let cap = v > 1 ? 130 * (v - 1) : 0
      panTx = match panTx > cap { true -> cap, _ -> (match panTx < (0 - cap) { true -> (0 - cap), _ -> panTx }) }
      panTy = match panTy > cap { true -> cap, _ -> (match panTy < (0 - cap) { true -> (0 - cap), _ -> panTy }) }
      dragBaseX = panTx
      dragBaseY = panTy
    }

    onPan(delta) {
      let nx = dragBaseX + delta.x
      let ny = dragBaseY + delta.y
      panTx = match nx > panMaxAbs { true -> panMaxAbs, _ -> (match nx < panMaxNeg { true -> panMaxNeg, _ -> nx }) }
      panTy = match ny > panMaxAbs { true -> panMaxAbs, _ -> (match ny < panMaxNeg { true -> panMaxNeg, _ -> ny }) }
    }

    onPanEnd(delta) {
      dragBaseX = panTx
      dragBaseY = panTy
    }
  }

  block {
    layout: horizontal, gap: spacing.3, align: center

    block {
      width: avatarPx
      height: avatarPx
      border-radius: 999px
      overflow: hidden
      background: fallbackColor
      layout: horizontal, justify: center, align: center

      block {
        visibility: hasAvatar
        width: 100%
        height: 100%
        image(currentAvatarUrl) {
          width: 100%
          height: 100%
          object-fit: "cover"
        }
      }

      block {
        visibility: !hasAvatar
        layout: horizontal, justify: center, align: center
        text(initials) {
          color: "#ffffff"
          weight: 700
          style: type.body-md
        }
      }
    }

    block {
      layout: vertical, gap: spacing.2

      block {
        cursor: "pointer"
        padding-y: 6px
        padding-x: 12px
        border-radius: 8px
        background: semantic.interactive
        layout: horizontal, justify: center
        on click: pickPhoto()

        text(pickLabel) {
          color: semantic.on-interactive
          weight: 600
          style: type.label-sm
        }
      }

      block {
        visibility: removable && hasAvatar
        cursor: "pointer"
        padding-y: 6px
        padding-x: 12px
        border-radius: 8px
        border: borders.default
        layout: horizontal, justify: center
        on click: removePhoto()

        text("Remove") {
          color: semantic.text-secondary
          weight: 600
          style: type.label-sm
        }
      }
    }
  }

  block {
    visibility: cropOpen

    block {
      position: "fixed"
      top: 0px
      left: 0px
      right: 0px
      bottom: 0px
      z-index: 1100
      background: "rgba(15, 23, 42, 0.5)"
      on click: cancelCrop()
    }

    block {
      position: "fixed"
      top: 50%
      left: 50%
      transform: "translate(-50%, -50%)"
      z-index: 1101
      width: 360px
      max-width: 95vw
      background: semantic.surface
      border-radius: 14px
      shadow: elevation.floating
      layout: vertical

      block {
        padding-y: 16px
        padding-x: 16px
        border-bottom: borders.default

        text("Adjust your photo") {
          style: type.heading-sm
          color: semantic.text-primary
        }
      }

      block {
        padding-y: 20px
        padding-x: 20px
        layout: vertical, gap: 16px, align: center

        // Draggable preview — drag to pan, slider to zoom.
        block {
          width: 260px
          height: 260px
          border-radius: 999px
          overflow: hidden
          background: "#000"
          cursor: "grab"
          user-select: "none"
          on drag(delta): onPan(delta)
          on drag-end(delta): onPanEnd(delta)

          image(imageSrc) {
            width: 100%
            height: 100%
            object-fit: "cover"
            transform: zoomTransform
          }
        }

        block {
          width: 100%
          layout: horizontal, gap: 10px, align: center

          text("Zoom") {
            style: type.label-sm
            color: semantic.text-secondary
          }

          slider(zoom) {
            min: 1
            max: 3
            step: 0.05
            grow: true
            on change(v): onZoom(v)
          }
        }
      }

      block {
        padding-y: 12px
        padding-x: 16px
        border-top: borders.default
        layout: horizontal, gap: spacing.2, justify: end

        block {
          cursor: "pointer"
          padding-y: 8px
          padding-x: 14px
          border-radius: 8px
          border: borders.default
          on click: cancelCrop()

          text("Cancel") {
            color: semantic.text-secondary
            weight: 600
            style: type.label-sm
          }
        }

        block {
          cursor: "pointer"
          padding-y: 8px
          padding-x: 14px
          border-radius: 8px
          background: semantic.interactive
          on click: applyCrop()

          text("Save") {
            color: semantic.on-interactive
            weight: 600
            style: type.label-sm
          }
        }
      }
    }
  }
}
