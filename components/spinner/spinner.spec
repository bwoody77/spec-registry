// Spinner — classic ring loading indicator (native `spin` keyframe).
// tone: 'default' (brand arc on faint track) | 'on-dark' (light arc for dark
//       panes) | 'muted' (gray). color/trackColor override the tone.
// size: 'sm' | 'md' | 'lg'.
component Spinner(
  size:       string = "md",
  tone:       string = "default",
  color:      string = "",
  trackColor: string = "",
  label:      string = ""
) {
  @computed {
    px: match size {
      "sm" -> 18,
      "lg" -> 40,
      _ -> 26
    }
    bw: match size {
      "sm" -> 2,
      "lg" -> 4,
      _ -> 3
    }
    arcColor: color != "" ? color : match tone {
      "on-dark" -> "#7fb0ff",
      "muted" -> "#94a3b8",
      _ -> "#1684ff"
    }
    trackCol: trackColor != "" ? trackColor : match tone {
      "on-dark" -> "rgba(255,255,255,0.16)",
      "muted" -> "rgba(148,163,184,0.22)",
      _ -> "rgba(22,132,255,0.18)"
    }
    ringBorder: "{bw}px solid {trackCol}"
    arcBorder: "{bw}px solid {arcColor}"
    ringPx: "{px}px"
  }

  block {
    layout: horizontal, gap: 9px, align: center
    role: "status"

    block {
      width: ringPx
      height: ringPx
      border: ringBorder
      border-top: arcBorder
      border-radius: 9999px
      animation: "spin"
    }

    block {
      visibility: label != ""
      text(label) {
        style: type.label-sm
        weight: 600
        color: arcColor
      }
    }
  }
}
