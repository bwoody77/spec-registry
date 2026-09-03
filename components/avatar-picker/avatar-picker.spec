@extern { pickImageFile, cropAvatarToDataUrl, imageAspect, downscaleToDataUrl } from "@spec/components/avatar-picker.js"

// AvatarPicker — pick a photo, frame it in a circle, save the crop.
//
// ── PAN (fixed 2026-08-25) ──────────────────────────────────────────────────
// The preview lays the image out the way the cropper reasons about it: SHORT
// side pinned to `previewSide * zoom`, long side following the natural aspect
// ratio, centred in the circle and clipped by it. The overflow IS the pan
// range, which is why a landscape photo can be panned at zoom 1 — it already
// overflows.
//
// It used to bound pan at `130 * (zoom - 1)` and draw the preview with
// `object-fit: cover`. Both were wrong, and together they made pan a no-op at
// every zoom level: the bound is zero at zoom 1 regardless of the picture, and
// `cover` clips the overflow BEFORE any transform runs, so translating the
// element slid a pre-cropped square over black rather than revealing more
// image. A 1200x400 photo showed only its middle third and neither end could
// be reached. Geometry now lives in avatar-picker-math.ts, shared with
// cropAvatarToDataUrl and unit-tested for agreement.
//
// ── WHY THE ZOOM SLIDER HAS NO `on change` ──────────────────────────────────
// It used to read `on change(v): onZoom(v)`. On a raw `slider()` the handler
// argument is the DOM EVENT, not the value (ai-reference "Two-Way Binding"),
// so that assigned an Event object to `zoom`. The damage was silent and
// three-deep: every `zoom > 1` test went false, so the pan bounds collapsed to
// zero; `scale(<object>)` is an invalid CSS declaration the browser DROPS, so
// the preview kept its last good transform and looked fine; and
// cropAvatarToDataUrl's `Number(zoom) || 1` turned the Event into 1, so the
// SAVED avatar quietly ignored the zoom the user had chosen. `slider(zoom)`
// already writes the value itself; `on input(event)` only has to re-clamp the
// pan and coerce the string to a number.

component AvatarPicker(
  currentAvatarUrl: string = "",
  // The stored ORIGINAL, when the caller keeps one. Given this, "Adjust
  // photo" can re-open the cropper on the full picture instead of forcing a
  // re-upload — the second half of the 2026-08-25 report. Callers that do not
  // keep an original simply omit it and the button does not appear.
  sourceUrl: string = "",
  // Crop to restore when re-opening a stored photo, so "Adjust" starts where
  // the user left off rather than snapping back to centre.
  initialZoom: number = 1,
  initialOffsetX: number = 0,
  initialOffsetY: number = 0,
  initials: string = "",
  fallbackColor: string = "#7585a0",
  buttonLabel: string = "",
  removable: boolean = true,
  cropSize: number = 256,
  size: number = 64,
  // Longest edge of the original handed back on `change`. 1024 is comfortably
  // more than re-cropping can ever show (cropSize x maxZoom = 768px) and about
  // 100 KB, against 3-5 MB for the raw phone photo.
  sourceMaxDim: number = 1024,
  // Show the photo and nothing else: no Change/Adjust/Remove, and the chip is
  // inert. For a profile page whose viewer may not edit this person's photo,
  // so the SAME component renders both the editor and the read-only chip —
  // callers used to keep a second, hand-rolled avatar for this case, and the
  // two drifted (Vector's desktop profile shipped without the cropper for a
  // week while the phone had it). 0.6.0.
  readOnly: boolean = false
) {
  @state {
    cropOpen: false
    imageSrc: ""
    // The original for THIS session's pick, kept so Save can hand it back and
    // so Adjust works before the caller has stored anything.
    pickedSrc: ""
    srcAspect: 1
    zoom: 1
    // Pan offset of the preview image in CSS px. dragBase{X,Y} hold the
    // committed offset at drag-start so each drag is additive.
    panTx: 0
    panTy: 0
    dragBaseX: 0
    dragBaseY: 0
    cropError: ""
    busy: false
  }

  @computed {
    hasAvatar: currentAvatarUrl != ""
    // Something to re-frame: either this session's pick or a stored original.
    adjustSrc: pickedSrc != "" ? pickedSrc : sourceUrl
    canAdjust: adjustSrc != "" && !busy && !readOnly
    // What the chip button announces. Read-only it is a picture, not an
    // affordance, so it must not promise an adjustment that cannot happen.
    chipLabel: readOnly ? "Profile photo" : "Adjust your photo"
    pickLabel: buttonLabel != "" ? buttonLabel : (hasAvatar ? "Change photo" : "Add photo")
    avatarPx: size + "px"

    // ── Preview geometry (mirrors avatar-picker-math.ts previewFit) ─────────
    previewSide: 260
    zoomSafe: zoom > 1 ? zoom : 1
    aspectSafe: srcAspect > 0 ? srcAspect : 1
    shortPx: 260 * zoomSafe
    dispW: aspectSafe >= 1 ? shortPx * aspectSafe : shortPx
    dispH: aspectSafe >= 1 ? shortPx : shortPx / aspectSafe
    panMaxX: (dispW - 260) / 2 > 0 ? (dispW - 260) / 2 : 0
    panMaxY: (dispH - 260) / 2 > 0 ? (dispH - 260) / 2 : 0
    dispWPx: dispW + "px"
    dispHPx: dispH + "px"
    // Centre the oversized image on the circle, then apply the pan. The -50%
    // pair resolves against the IMAGE's own box, which is what centres it.
    previewTransform: "translate(-50%, -50%) translate(" + panTx + "px, " + panTy + "px)"

    // Offsets in [-1, 1] for cropAvatarToDataUrl. SIGN-FLIPPED: dragging the
    // picture right brings its LEFT side into view, so the crop centre moves
    // left.
    cropOffsetX: panMaxX > 0 ? (0 - panTx) / panMaxX : 0
    cropOffsetY: panMaxY > 0 ? (0 - panTy) / panMaxY : 0
  }

  @actions {
    // Restore a saved crop onto the current preview geometry. Offsets are
    // stored normalised, so they survive a different zoom or a re-measure.
    //
    // BOTH axes get their real bound. An earlier version zeroed the "short"
    // axis by aspect ratio (usableY = 0 for a landscape image), which is only
    // right at zoom 1 — as soon as zoom > 1 the image overflows the circle on
    // BOTH axes, exactly as panMaxX/panMaxY say. The effect was that
    // re-opening Adjust on a zoomed photo silently dropped one axis of the
    // user's framing, and pressing Save then wrote that loss back.
    applyInitialCrop() {
      zoom = initialZoom > 1 ? initialZoom : 1
      let a = srcAspect > 0 ? srcAspect : 1
      let sp = 260 * zoom
      let w = a >= 1 ? sp * a : sp
      let h = a >= 1 ? sp : sp / a
      let cx = (w - 260) / 2 > 0 ? (w - 260) / 2 : 0
      let cy = (h - 260) / 2 > 0 ? (h - 260) / 2 : 0
      panTx = 0 - initialOffsetX * cx
      panTy = 0 - initialOffsetY * cy
      dragBaseX = panTx
      dragBaseY = panTy
    }

    resetCrop() {
      cropError = ""
      zoom = 1
      panTx = 0
      panTy = 0
      dragBaseX = 0
      dragBaseY = 0
    }

    pickPhoto() {
      busy = true
      let src = await pickImageFile()
      if src == "" {
        busy = false
        return
      }
      // Shrink FIRST, then frame the shrunk copy — so what the user sees in
      // the preview is exactly the pixels a later re-crop will have.
      let small = await downscaleToDataUrl(src, sourceMaxDim, 0.85)
      let a = await imageAspect(small)
      busy = false
      srcAspect = a > 0 ? a : 1
      pickedSrc = small
      imageSrc = small
      resetCrop()
      cropOpen = true
    }

    // Re-open the cropper on the image we already have — no re-upload.
    adjustPhoto() {
      if adjustSrc == "" { return }
      cropError = ""
      busy = true
      let a = await imageAspect(adjustSrc)
      busy = false
      srcAspect = a > 0 ? a : 1
      imageSrc = adjustSrc
      applyInitialCrop()
      cropOpen = true
    }

    cancelCrop() {
      cropOpen = false
      imageSrc = ""
      resetCrop()
    }

    // cropAvatarToDataUrl RESOLVES "" on failure rather than rejecting, and
    // that is deliberate: Spec actions have no try/catch, so a rejection would
    // abort this action before `busy = false` — leaving the dialog open with
    // Save permanently inert and nothing said to the user. (The failures are
    // real: a decode error, no canvas, and — in production, where the stored
    // original is served from R2 — a tainted-canvas SecurityError when the
    // bucket sends no CORS header.) Same rule as Vector's Safe api variants.
    applyCrop() {
      cropError = ""
      busy = true
      let dataUrl = await cropAvatarToDataUrl(imageSrc, zoom, cropOffsetX, cropOffsetY, cropSize)
      busy = false
      if dataUrl == "" {
        cropError = "Couldn't process that photo. Try uploading it again."
        return
      }
      cropOpen = false
      // `source` is "" when re-framing a photo the caller already stored —
      // that is the signal to keep the stored original rather than re-upload
      // an identical copy of it.
      emit("change", {
        dataUrl: dataUrl,
        source: pickedSrc,
        zoom: zoom,
        offsetX: cropOffsetX,
        offsetY: cropOffsetY
      })
      imageSrc = ""
    }

    removePhoto() {
      pickedSrc = ""
      emit("remove")
    }

    onZoom(v) {
      // `v` comes off the DOM as a string; `* 1` is exact Number().
      let z = v * 1
      zoom = z > 1 ? z : 1
      // Re-clamp: slack shrinks as zoom drops, and a stale pan would push the
      // crop outside the picture.
      let a = srcAspect > 0 ? srcAspect : 1
      let w = a >= 1 ? 260 * zoom * a : 260 * zoom
      let h = a >= 1 ? 260 * zoom : 260 * zoom / a
      let cx = (w - 260) / 2 > 0 ? (w - 260) / 2 : 0
      let cy = (h - 260) / 2 > 0 ? (h - 260) / 2 : 0
      panTx = match panTx > cx { true -> cx, _ -> (match panTx < (0 - cx) { true -> (0 - cx), _ -> panTx }) }
      panTy = match panTy > cy { true -> cy, _ -> (match panTy < (0 - cy) { true -> (0 - cy), _ -> panTy }) }
      dragBaseX = panTx
      dragBaseY = panTy
    }

    onPan(delta) {
      let nx = dragBaseX + delta.x
      let ny = dragBaseY + delta.y
      panTx = match nx > panMaxX { true -> panMaxX, _ -> (match nx < (0 - panMaxX) { true -> (0 - panMaxX), _ -> nx }) }
      panTy = match ny > panMaxY { true -> panMaxY, _ -> (match ny < (0 - panMaxY) { true -> (0 - panMaxY), _ -> ny }) }
    }

    onPanEnd(delta) {
      dragBaseX = panTx
      dragBaseY = panTy
    }
  }

  block {
    layout: horizontal, gap: spacing.3, align: center

    // The photo itself is the most obvious thing to tap when you want to
    // re-frame it, so it opens Adjust when there is something to adjust.
    // A real <button>, not a div with an onclick: a div cannot be tabbed to and
    // does not answer Enter/Space, and pairing one with an aria-label is the
    // worst of both — it ANNOUNCES as interactive and then cannot be reached.
    // `disabled` carries the not-yet-adjustable state to assistive tech
    // instead of only to the cursor.
    button {
      width: avatarPx
      height: avatarPx
      border-radius: 999px
      overflow: hidden
      border: 'none'
      padding: 0px
      background: fallbackColor
      layout: horizontal, justify: center, align: center
      cursor: canAdjust ? "pointer" : "default"
      disabled: !canAdjust
      aria-label: chipLabel
      on click: { if canAdjust { adjustPhoto() } }

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

    // The action column. Absent entirely in read-only mode — a viewer who may
    // not change this photo gets the picture and no buttons, not disabled ones.
    block {
      visibility: !readOnly
      layout: vertical, gap: spacing.2

      button {
        cursor: "pointer"
        padding-y: 6px
        padding-x: 12px
        border-radius: 8px
        border: 'none'
        background: semantic.interactive
        layout: horizontal, justify: center
        on click: pickPhoto()

        text(pickLabel) {
          color: semantic.on-interactive
          weight: 600
          style: type.label-sm
        }
      }

      // Only offered when there is an image to re-frame. Before this existed
      // the ONLY route back into the cropper was uploading the photo again.
      button {
        visibility: adjustSrc != ""
        cursor: "pointer"
        padding-y: 6px
        padding-x: 12px
        border-radius: 8px
        border: borders.default
        background: 'transparent'
        layout: horizontal, justify: center
        on click: adjustPhoto()

        text("Adjust") {
          color: semantic.text-secondary
          weight: 600
          style: type.label-sm
        }
      }

      button {
        visibility: removable && hasAvatar
        cursor: "pointer"
        padding-y: 6px
        padding-x: 12px
        border-radius: 8px
        border: borders.default
        background: 'transparent'
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
        layout: vertical, gap: 2px

        text("Adjust your photo") {
          style: type.heading-sm
          color: semantic.text-primary
        }
        text("Drag to move it, and use the slider to zoom.") {
          style: type.label-sm
          color: semantic.text-tertiary
        }
      }

      block {
        padding-y: 20px
        padding-x: 20px
        layout: vertical, gap: 16px, align: center

        // Draggable preview. The image is ABSOLUTE rather than a flex child:
        // a flex item shrinks to fit by default, which would undo the very
        // overflow that makes panning possible.
        block {
          width: 260px
          height: 260px
          border-radius: 999px
          overflow: hidden
          background: "#000"
          position: "relative"
          cursor: "grab"
          user-select: "none"
          on drag(delta): onPan(delta)
          on drag-end(delta): onPanEnd(delta)

          block {
            position: "absolute"
            top: 50%
            left: 50%
            width: dispWPx
            height: dispHPx
            transform: previewTransform

            image(imageSrc) {
              width: 100%
              height: 100%
            }
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
            aria-label: "Zoom"
            on input(event): onZoom(event.target.value)
          }
        }
      }

      block {
        visibility: cropError != ""
        padding-x: 20px
        padding-bottom: 4px
        text(cropError) {
          color: semantic.destructive
          weight: 600
          style: type.label-sm
        }
      }

      block {
        padding-y: 12px
        padding-x: 16px
        border-top: borders.default
        layout: horizontal, gap: spacing.2, justify: end

        button {
          cursor: "pointer"
          padding-y: 8px
          padding-x: 14px
          border-radius: 8px
          border: borders.default
          background: 'transparent'
          on click: cancelCrop()

          text("Cancel") {
            color: semantic.text-secondary
            weight: 600
            style: type.label-sm
          }
        }

        button {
          cursor: "pointer"
          padding-y: 8px
          padding-x: 14px
          border-radius: 8px
          border: 'none'
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
