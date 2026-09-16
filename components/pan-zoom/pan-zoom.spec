@extern { pzPrefersReducedMotion } from "@spec/components/pan-zoom.js"

// PanZoom — look closely at an image: wheel, pinch, drag, double-tap.
//
// THE MODEL, shared by every fn below and by AvatarPicker: the image is drawn at
// its FIT size times `s`, centered in a vw x vh viewport, then translated by
// (tx, ty). `s = 1` is fit. All values are CSS px, and x/y focal points are
// relative to the viewport's top-left.
//
// The geometry is fn, not @extern, so it ports; AvatarPicker calls pzZoomAt
// (registered in SPEC_FN_SOURCES) for its own circle rather than mounting this
// component, because its crop and save are its own.

fn pzFitSize(vw: number, vh: number, natW: number, natH: number, allowUpscale: boolean) -> map {
  if vw <= 0 || vh <= 0 || natW <= 0 || natH <= 0 {
    return { w: 0, h: 0 }
  }
  let k = min(vw / natW, vh / natH)
  // A small scan stays at its own pixels unless the caller wants it filled —
  // blurring one up is what "the image is very fuzzy" was.
  let k2 = allowUpscale ? k : min(k, 1)
  return { w: natW * k2, h: natH * k2 }
}

fn pzMaxScale(fitW: number, natW: number, maxActual: number) -> number {
  if fitW <= 0 || natW <= 0 {
    return 1
  }
  // Never less than 2x fit, so a small image can still be enlarged.
  return max(maxActual * natW / fitW, 2)
}

fn pzClampPan(s: number, tx: number, ty: number, fitW: number, fitH: number, vw: number, vh: number) -> map {
  let slackX = max((fitW * s - vw) / 2, 0)
  let slackY = max((fitH * s - vh) / 2, 0)
  let cx = min(max(tx, 0 - slackX), slackX)
  let cy = min(max(ty, 0 - slackY), slackY)
  return { tx: cx, ty: cy }
}

fn pzZoomAt(s: number, tx: number, ty: number, factor: number, x: number, y: number, vw: number, vh: number, fitW: number, fitH: number, maxS: number) -> map {
  let cur = s > 0 ? s : 1
  let ns = min(max(cur * factor, 1), max(maxS, 1))
  // Focal point relative to the viewport center, which is the transform origin.
  let fx = x - vw / 2
  let fy = y - vh / 2
  // The image-local point under the focus, (f - t) / s, must stay under it.
  let ntx = fx - (fx - tx) * ns / cur
  let nty = fy - (fy - ty) * ns / cur
  let p = pzClampPan(ns, ntx, nty, fitW, fitH, vw, vh)
  return { s: ns, tx: p.tx, ty: p.ty }
}

fn pzStep(s: number, dir: number, maxS: number) -> number {
  let top = max(maxS, 1)
  let n = dir > 0 ? s * 1.5 : s / 1.5
  if n < 1.02 {
    return 1
  }
  if n > top * 0.98 {
    return top
  }
  return n
}

fn pzPercent(s: number, fitW: number, natW: number) -> number {
  if natW <= 0 {
    return 0
  }
  return round(100 * s * fitW / natW)
}

fn pzActualScale(fitW: number, natW: number, maxS: number) -> number {
  if fitW <= 0 || natW <= 0 {
    return 1
  }
  return min(max(natW / fitW, 1), max(maxS, 1))
}

fn pzCommandName(cmd: string) -> string {
  return regexReplace(cmd, "#.*", "")
}

// ── PanZoom ──────────────────────────────────────────────────────────────
// Fills its parent (give the parent a definite size). The image never takes
// pointer events: an <img> under a pointer drag starts a native image drag and
// cancels the gesture (AvatarPicker 0.6.2).
component PanZoom(
  src: string = "",
  alt: string = "",
  // false: a small image opens at its own pixel size rather than blurred up.
  allowUpscale: boolean = false,
  // The zoom ceiling, in multiples of the image's ACTUAL pixels (and never
  // less than 2x fit).
  maxActual: number = 4,
  // Any change returns to fit. A viewer passes the document's URL, so a new
  // document or page always opens at fit.
  resetKey: any = "",
  // "<in|out|fit|actual>#<n>". ONE prop, not a command plus a counter: a watch
  // on one prop reads a sibling prop's OLD value when both change in the same
  // tick, so a separate counter could run the previous command.
  command: string = ""
) {
  @state {
    vw: 0
    vh: 0
    natW: 0
    natH: 0
    s: 1
    tx: 0
    ty: 0
    // Where the image sat when the current drag began. `on drag` reports the
    // travel since the drag (or its resume after a pinch) started, so the pan
    // is always base + travel.
    baseX: 0
    baseY: 0
    dragging: false
    animate: false
    reduceMotion: false
  }

  @computed {
    fit: pzFitSize(vw, vh, natW, natH, allowUpscale)
    dispWPx: (fit.w * s) + "px"
    dispHPx: (fit.h * s) + "px"
    imgTransform: "translate(-50%, -50%) translate(" + tx + "px, " + ty + "px)"
    pzCursor: dragging ? "grabbing" : (s > 1.001 ? "grab" : "default")
    pzTransition: animate && !reduceMotion ? "width 160ms ease-out, height 160ms ease-out, transform 160ms ease-out" : "none"
  }

  @watch {
    resetKey: {
      animate = false
      applyView({ s: 1, tx: 0, ty: 0 })
    }
    command: { runCommand(pzCommandName(command)) }
  }

  @actions {
    // A resize or rotate keeps the scale and re-clamps the pan.
    onResize(r) {
      vw = r.width
      vh = r.height
      let f = pzFitSize(r.width, r.height, natW, natH, allowUpscale)
      let p = pzClampPan(s, tx, ty, f.w, f.h, r.width, r.height)
      applyView({ s: s, tx: p.tx, ty: p.ty })
    }

    onLoaded(w, h) {
      let nw = w * 1
      let nh = h * 1
      // A decode failure can still fire `load` with no size; keep what we have.
      if nw <= 0 || nh <= 0 { return }
      natW = nw
      natH = nh
      reduceMotion = pzPrefersReducedMotion()
      animate = false
      emit("load", { naturalWidth: nw, naturalHeight: nh })
      applyView({ s: 1, tx: 0, ty: 0 })
    }

    // Every change of view goes through here, so the drag base and the host's
    // readout can never fall behind the picture. Re-basing matters after a
    // pinch in particular: the drag resumes from the finger left down with its
    // travel restarting at zero, so a stale base would jump the image back.
    applyView(v) {
      s = v.s
      tx = v.tx
      ty = v.ty
      baseX = v.tx
      baseY = v.ty
      // Before the image has a size there is no view to report: a resize or a
      // new resetKey would otherwise flash "0%" in the host's readout.
      if natW <= 0 { return }
      let f = pzFitSize(vw, vh, natW, natH, allowUpscale)
      let m = pzMaxScale(f.w, natW, maxActual)
      emit("change", {
        scale: v.s,
        percent: pzPercent(v.s, f.w, natW),
        atFit: v.s <= 1.001,
        atMax: v.s >= m - 0.001,
        atActual: abs(v.s - pzActualScale(f.w, natW, m)) < 0.001
      })
    }

    onZoom(g) {
      animate = false
      let f = pzFitSize(vw, vh, natW, natH, allowUpscale)
      let m = pzMaxScale(f.w, natW, maxActual)
      applyView(pzZoomAt(s, tx + g.panX, ty + g.panY, g.factor, g.x, g.y, vw, vh, f.w, f.h, m))
    }

    onDrag(d) {
      animate = false
      dragging = true
      let f = pzFitSize(vw, vh, natW, natH, allowUpscale)
      let p = pzClampPan(s, baseX + d.x, baseY + d.y, f.w, f.h, vw, vh)
      tx = p.tx
      ty = p.ty
    }

    onDragEnd(d) {
      dragging = false
      baseX = tx
      baseY = ty
    }

    onDoubleTap(p) {
      let f = pzFitSize(vw, vh, natW, natH, allowUpscale)
      let m = pzMaxScale(f.w, natW, maxActual)
      animate = true
      if s > 1.001 {
        applyView({ s: 1, tx: 0, ty: 0 })
        return
      }
      // 2.5x fit, which pzZoomAt caps at the ceiling.
      applyView(pzZoomAt(s, tx, ty, 2.5 / s, p.x, p.y, vw, vh, f.w, f.h, m))
    }

    // Before load, applyView keeps the view silent and onLoaded resets it.
    runCommand(c) {
      let f = pzFitSize(vw, vh, natW, natH, allowUpscale)
      let m = pzMaxScale(f.w, natW, maxActual)
      animate = true
      if c == "fit" {
        applyView({ s: 1, tx: 0, ty: 0 })
        return
      }
      let target = c == "in" ? pzStep(s, 1, m) : (c == "out" ? pzStep(s, -1, m) : (c == "actual" ? pzActualScale(f.w, natW, m) : s))
      applyView(pzZoomAt(s, tx, ty, target / s, vw / 2, vh / 2, vw, vh, f.w, f.h, m))
    }
  }

  block {
    data-pan-zoom: "true"
    width: 100%
    height: 100%
    position: "relative"
    overflow: hidden
    user-select: "none"
    cursor: pzCursor
    on resize(r): onResize(r)
    on zoom(g): onZoom(g)
    on drag(d): onDrag(d)
    on drag-end(d): onDragEnd(d)
    on double-tap(p): onDoubleTap(p)
    block {
      position: "absolute"
      top: 50%
      left: 50%
      width: dispWPx
      height: dispHPx
      transform: imgTransform
      transition: pzTransition
      pointer-events: "none"
      image(src) {
        alt: alt
        width: 100%
        height: 100%
        on load(e): onLoaded(e.target.naturalWidth, e.target.naturalHeight)
        on error: emit("error")
      }
    }
  }
}
