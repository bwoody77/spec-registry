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
//
// `fontSize` (Vector #4819): the text at a fixed size ('11px'), for an app
// whose type scale is FIXED (Vector's shop phone app: an 11.5px label-sm badge
// sat beside 11px captions). '' (the default) draws type.label-sm as before. A
// size keeps label-sm's weight and line height and replaces only its size; on
// iOS it lowers to `.font(.system(size:))`, which Dynamic Type leaves alone.
// Two arms of a `match`, because a `font-size:` bound to '' clears the
// level's size. The arm never changes at a call site, so one arm mounts.
component Badge(text: text, variant: string = "neutral", shape: string = "pill", fontSize: string = "") {
  @computed {
    badgeArm: fontSize != "" ? "fixed" : "level"
    badgeColor: match variant {
      "info" -> token.badge-info-color,
      "success" -> token.badge-success-color,
      "warning" -> token.badge-warning-color,
      "error" -> token.badge-error-color,
      "neutral" -> token.badge-neutral-color,
      _ -> token.badge-neutral-color
    }
  }
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

    match badgeArm {
      "fixed" -> {
        // `weight` is label-sm's own 500, written out for iOS: there an
        // authored size lowers to `.system(size:)`, which carries only an
        // authored weight, not the level's.
        text(text) {
          style: type.label-sm
          font-size: fontSize
          weight: 500
          color: badgeColor
        }
      },
      _ -> {
        text(text) {
          style: type.label-sm
          color: badgeColor
        }
      }
    }
  }
}
