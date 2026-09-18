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
//
// ── WHEEL AND PINCH (0.8.0) ─────────────────────────────────────────────────
// Scrolling or pinching over the circle zooms toward the cursor or the
// fingers, through pzZoomAt from pan-zoom.spec, so the crop editor and the
// PanZoom viewer share one piece of geometry.

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
  // Whose photo this is, for the chip's accessible name when the viewer is
  // NOT the person pictured ("Edit Avery Pilot's photo"). Empty means the
  // viewer's own photo, and the chip says "your". 0.7.1.
  subjectName: string = "",
  fallbackColor: string = "#7585a0",
  // Retired in 0.7.0: the chip replaced the button this labeled. Kept so
  // existing call sites still compile; it has no effect.
  buttonLabel: string = "",
  // Offer Delete photo in the editor when a photo exists.
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
    // 0.7.0: while true, the editor's footer is swapped for a one-line
    // confirm. Delete also discards the stored original, so it asks once.
    confirmDelete: false
    // False when the editor opened on a photo with no stored original. The
    // dialog still offers Replace and Delete, but the only picture to re-crop
    // is the already-cropped JPEG, so pan, zoom and Save are off.
    framing: true
    imageSrc: ""
    // The original for THIS session's pick, kept so Save can hand it back and
    // so Adjust works before the caller has stored anything.
    pickedSrc: ""
    // The pick that was last SAVED. Cancel restores pickedSrc to this, so a
    // Replace the user backed out of cannot become the next edit's picture,
    // or be uploaded as the original by the next Save. 0.7.1.
    committedPick: ""
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
    // What the chip announces (0.7.0). The chip is the whole editable surface
    // now, so its name says what tapping it does. Read-only it is a picture,
    // not an affordance, and must not promise anything.
    chipLabel: readOnly ? t("Profile photo")
      : (hasAvatar
        ? (subjectName != "" ? t("Edit {subjectName}'s photo") : t("Edit your photo"))
        : (subjectName != "" ? t("Add a photo of {subjectName}") : t("Add a photo")))
    chipDisabled: readOnly || busy
    dialogHint: framing ? t("Drag to move it. Scroll, pinch or use the slider to zoom.") : t("Replace it to reframe.")
    closeLabel: framing ? t("Cancel") : t("Close")
    previewCursor: framing ? "grab" : "default"
    canDelete: removable && hasAvatar
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

  // The host may load the original AFTER the user tapped the chip: Vector's
  // ProfileAvatar fetches it asynchronously. An editor that opened with
  // framing off for want of it switches framing on when it lands, rather than
  // go on saying the photo predates reframing. 0.7.1.
  @watch {
    sourceUrl: {
      onSourceArrived()
    }
  }

  @actions {
    onSourceArrived() {
      if !cropOpen { return }
      if framing { return }
      if confirmDelete { return }
      if adjustSrc == "" { return }
      openEditor()
    }

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
      framing = true
      confirmDelete = false
      cropOpen = true
    }

    // The chip's one gesture (0.7.0): no photo, pick one; a photo, edit it.
    onChipTap() {
      if readOnly { return }
      if hasAvatar {
        openEditor()
        return
      }
      pickPhoto()
    }

    // Open the editor on the photo we already have, with no re-upload. With a
    // stored original (or this session's pick) the framing is live. Without
    // one the editor still opens, so Replace and Delete stay reachable, and it
    // shows the stored crop with framing off.
    openEditor() {
      cropError = ""
      confirmDelete = false
      if adjustSrc == "" {
        srcAspect = 1
        imageSrc = currentAvatarUrl
        framing = false
        resetCrop()
        cropOpen = true
        return
      }
      busy = true
      let a = await imageAspect(adjustSrc)
      busy = false
      srcAspect = a > 0 ? a : 1
      imageSrc = adjustSrc
      framing = true
      applyInitialCrop()
      cropOpen = true
    }

    cancelCrop() {
      cropOpen = false
      confirmDelete = false
      pickedSrc = committedPick
      imageSrc = ""
      resetCrop()
    }

    askDelete() { confirmDelete = true }
    keepPhoto() { confirmDelete = false }

    // cropAvatarToDataUrl RESOLVES "" on failure rather than rejecting, and
    // that is deliberate: Spec actions have no try/catch, so a rejection would
    // abort this action before `busy = false` — leaving the dialog open with
    // Save permanently inert and nothing said to the user. (The failures are
    // real: a decode error, no canvas, and — in production, where the stored
    // original is served from R2 — a tainted-canvas SecurityError when the
    // bucket sends no CORS header.) Same rule as Vector's Safe api variants.
    applyCrop() {
      if !framing { return }
      cropError = ""
      busy = true
      let dataUrl = await cropAvatarToDataUrl(imageSrc, zoom, cropOffsetX, cropOffsetY, cropSize)
      busy = false
      if dataUrl == "" {
        cropError = t("Couldn't process that photo. Try uploading it again.")
        return
      }
      cropOpen = false
      committedPick = pickedSrc
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

    // Confirmed from the editor's footer. Closes the editor, since there is
    // nothing left in it to frame.
    removePhoto() {
      confirmDelete = false
      cropOpen = false
      imageSrc = ""
      pickedSrc = ""
      committedPick = ""
      resetCrop()
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
      if !framing { return }
      let nx = dragBaseX + delta.x
      let ny = dragBaseY + delta.y
      panTx = match nx > panMaxX { true -> panMaxX, _ -> (match nx < (0 - panMaxX) { true -> (0 - panMaxX), _ -> nx }) }
      panTy = match ny > panMaxY { true -> panMaxY, _ -> (match ny < (0 - panMaxY) { true -> (0 - panMaxY), _ -> ny }) }
    }

    onPanEnd(delta) {
      dragBaseX = panTx
      dragBaseY = panTy
    }

    // 0.8.0: wheel and pinch. Same model as PanZoom — a 260px viewport, the
    // cover-fit size at zoom 1 (the dispW/dispH above at zoomSafe 1), pan
    // measured from the center — so the shared pzZoomAt does the focal-point
    // math and the clamp is the panMaxX/panMaxY bound the slider and drag
    // already obey. The slider is bound to `zoom`, so it follows.
    //
    // The drag base is re-synced because `on drag` resumes after a pinch with
    // its travel restarting at zero: a stale base would jump the picture back.
    onPinch(g) {
      if !framing { return }
      let a = srcAspect > 0 ? srcAspect : 1
      let fw = a >= 1 ? 260 * a : 260
      let fh = a >= 1 ? 260 : 260 / a
      let v = pzZoomAt(zoom, panTx + g.panX, panTy + g.panY, g.factor, g.x, g.y, 260, 260, fw, fh, 3)
      zoom = v.s
      panTx = v.tx
      panTy = v.ty
      dragBaseX = v.tx
      dragBaseY = v.ty
    }
  }

  block {
    layout: horizontal, gap: spacing.3, align: center
    // The frame the badge is placed against. Sized to the chip, because the
    // chip clips its own contents (overflow: hidden) and would cut the badge
    // off if the badge sat inside it.
    position: "relative"
    width: avatarPx
    height: avatarPx

    // The photo IS the control (0.7.0). With no photo, tapping it picks one.
    // With a photo, tapping it opens the editor, which holds framing, Replace
    // and Delete. There is no button column beside it any more. One gesture on
    // every surface, phone and desktop alike.
    // A real <button>, not a div with an onclick: a div cannot be tabbed to and
    // does not answer Enter/Space, and pairing one with an aria-label is the
    // worst of both. It ANNOUNCES as interactive and then cannot be reached.
    // `disabled` carries read-only (and busy) to assistive tech instead of
    // only to the cursor.
    button {
      width: avatarPx
      height: avatarPx
      border-radius: 999px
      overflow: hidden
      position: "relative"
      border: 'none'
      padding: 0px
      background: fallbackColor
      layout: horizontal, justify: center, align: center
      cursor: readOnly ? "default" : "pointer"
      disabled: chipDisabled
      aria-label: chipLabel
      on click: onChipTap()

      // The monogram sits BEHIND the photo, always. Until the image paints
      // (a stored avatar on a slow connection, R2 in production) the disc
      // shows the initials rather than a blank coloured circle — the symptom
      // Vector's #423 was filed for, and which its hand-rolled chips fixed
      // with a spinner layer that this component did not carry (0.6.1). A
      // saved crop is an opaque JPEG, so once it lands the monogram is gone.
      block {
        position: "absolute"
        top: 0px
        left: 0px
        right: 0px
        bottom: 0px
        layout: horizontal, justify: center, align: center
        text(initials) {
          color: "#ffffff"
          weight: 700
          style: type.body-md
        }
      }

      block {
        visibility: hasAvatar
        position: "relative"
        width: 100%
        height: 100%
        image(currentAvatarUrl) {
          width: 100%
          height: 100%
          object-fit: "cover"
        }
      }
    }

    // 0.7.0 retired the action column (Add/Change photo, Adjust, Remove) that
    // sat here. Everything it did is reached by tapping the chip.

    // The badge says "this picture is a control", which a bare circle does
    // not. "+" with no photo, a camera with one. Absent when read-only, where
    // the chip is only a picture. `pointer-events: none` so a tap on the badge
    // lands on the chip underneath. Two literal icons rather than a computed
    // name: a host's icon build can only include names it can see.
    block {
      data-avatar-badge: '1'
      visibility: !readOnly
      position: "absolute"
      right: 0px
      bottom: 0px
      width: 22px
      height: 22px
      border-radius: 999px
      background: semantic.interactive
      border: '2px solid ' + semantic.surface
      pointer-events: "none"
      layout: horizontal, justify: center, align: center

      block {
        visibility: !hasAvatar
        layout: horizontal, justify: center, align: center
        Icon(name: "plus", size: 12, color: semantic.on-interactive)
      }
      block {
        visibility: hasAvatar
        layout: horizontal, justify: center, align: center
        Icon(name: "camera", size: 12, color: semantic.on-interactive)
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

        text("Edit your photo") {
          style: type.heading-sm
          color: semantic.text-primary
        }
        text(dialogHint) {
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
          cursor: previewCursor
          user-select: "none"
          data-avatar-preview: "true"
          on drag(delta): onPan(delta)
          on drag-end(delta): onPanEnd(delta)
          on zoom(g): onPinch(g)

          // The picture must not receive the press. An <img> is draggable by
          // default, so a mouse-down that lands on it starts a native HTML5
          // image drag — the not-allowed cursor, a ghost of the photo — and
          // the browser fires pointercancel on the container, which ends the
          // pan before it moved a pixel. Touch never saw it: the touch path
          // preventDefaults on move and no native drag begins. Found on the
          // desktop profile 2026-09-05: zoom worked, pan did nothing (0.6.2).
          block {
            position: "absolute"
            top: 50%
            left: 50%
            width: dispWPx
            height: dispHPx
            transform: previewTransform
            pointer-events: "none"

            image(imageSrc) {
              width: 100%
              height: 100%
            }
          }
        }

        // A photo saved without its original can be replaced or deleted, but
        // not re-framed. Say so rather than leave a slider that does nothing.
        block {
          visibility: !framing
          width: 100%
          padding-y: 8px
          padding-x: 10px
          border-radius: 8px
          background: semantic.surface-sunken
          layout: horizontal, justify: center
          text("This photo was saved before reframing was available.") {
            style: type.label-sm
            color: semantic.text-secondary
            text-align: center
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
            disabled: !framing
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

      // Footer (0.7.0). Two rows so four buttons fit a 360px dialog: what to
      // do with the photo (Replace, Delete) above how to leave (Cancel, Save).
      block {
        visibility: !confirmDelete
        padding-y: 12px
        padding-x: 16px
        border-top: borders.default
        layout: vertical, gap: spacing.2

        block {
          layout: horizontal, gap: spacing.2, align: center

          button {
            cursor: "pointer"
            padding-y: 8px
            padding-x: 14px
            border-radius: 8px
            border: borders.default
            background: 'transparent'
            disabled: busy
            on click: pickPhoto()

            text("Replace photo") {
              color: semantic.text-secondary
              weight: 600
              style: type.label-sm
            }
          }

          // Offers the delete; the confirm below does it (solid red there).
          button {
            visibility: canDelete
            cursor: "pointer"
            padding-y: 8px
            padding-x: 14px
            border-radius: 8px
            border: '1px solid ' + semantic.destructive
            background: 'transparent'
            on click: askDelete()

            text("Delete photo") {
              color: semantic.destructive
              weight: 600
              style: type.label-sm
            }
          }
        }

        block {
          layout: horizontal, gap: spacing.2, justify: end

          button {
            cursor: "pointer"
            padding-y: 8px
            padding-x: 14px
            border-radius: 8px
            border: borders.default
            background: 'transparent'
            on click: cancelCrop()

            text(closeLabel) {
              color: semantic.text-secondary
              weight: 600
              style: type.label-sm
            }
          }

          button {
            visibility: framing
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

      // The delete confirm replaces the footer in place, so the question sits
      // where the button was pressed.
      block {
        visibility: confirmDelete
        padding-y: 12px
        padding-x: 16px
        border-top: borders.default
        layout: vertical, gap: spacing.2

        block {
          layout: vertical, gap: 2px
          text("Delete this photo?") {
            color: semantic.text-primary
            weight: 600
            style: type.label-sm
          }
          text("Your initials will show instead.") {
            color: semantic.text-tertiary
            style: type.label-sm
          }
        }

        block {
          layout: horizontal, gap: spacing.2, justify: end

          button {
            cursor: "pointer"
            padding-y: 8px
            padding-x: 14px
            border-radius: 8px
            border: borders.default
            background: 'transparent'
            on click: keepPhoto()

            text("Keep photo") {
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
            background: semantic.destructive
            on click: removePhoto()

            text("Delete") {
              color: semantic.on-interactive
              weight: 600
              style: type.label-sm
            }
          }
        }
      }
    }
  }
}
