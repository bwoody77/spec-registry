// Badge — inline status badge
//
// shape — "pill" (default, unchanged) or "square", a small radius instead of a
// full one. Same prop name and the same two-value shape as Button's own
// `shape`, so the two components do not describe the same idea differently.
//
// A squared badge reads as a FIELD VALUE rather than as a status pill, which is
// what a table column of them wants: a grid of full-radius pills turns every
// cell into a button-shaped object and the eye stops being able to tell the one
// that is interactive from the ones that are not. cf's deals grid asked for it
// on its stage column, where the badge sits in a row beside plain-text cells.
//
// The radius comes from `token.badge-square-radius` rather than a literal, for
// the same reason the pill's comes from a token: an app that wants softer or
// sharper corners overrides a token instead of forking the component.
component Badge(text: string, variant: string = "neutral", shape: string = "pill") {
  block {
    inline: true
    layout: horizontal, gap: 4px, align: center
    padding-x: 10
    padding-y: 2
    border-radius: match shape {
      "square" -> token.badge-square-radius,
      _ -> token.badge-radius
    }
    overflow: hidden
    cursor: "default"
    background: match variant {
      "info" -> token.badge-info-bg,
      "success" -> token.badge-success-bg,
      "warning" -> token.badge-warning-bg,
      "error" -> token.badge-error-bg,
      "neutral" -> token.badge-neutral-bg,
      _ -> token.badge-neutral-bg
    }
    role: "status"

    text(text) {
      style: type.label-sm
      weight: 500
      color: match variant {
        "info" -> token.badge-info-color,
        "success" -> token.badge-success-color,
        "warning" -> token.badge-warning-color,
        "error" -> token.badge-error-color,
        "neutral" -> token.badge-neutral-color,
        _ -> token.badge-neutral-color
      }
    }
  }
}
