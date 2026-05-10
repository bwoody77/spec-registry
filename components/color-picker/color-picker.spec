// ColorPicker — single-swatch trigger that opens the browser's native
// color chooser. Renders a chip showing the current color + hex value
// + a palette icon. Click anywhere on the chip to open the OS color
// picker (full HSV, eyedropper where available, hex input).
//
// Implementation note: a transparent native `<input type="color">` is
// overlaid on top of the styled chip via opacity:0 + position:absolute.
// This is the standard web pattern (used by MUI, Mantine, etc) — the
// browser's built-in picker is the right tool when the user needs to
// choose ANY color rather than from a small preset list.
//
// Props:
//   • value  — current color hex (e.g. "#1684ff"). Re-syncs if changed
//              by the parent (via @watch).
//   • name   — optional `name` attribute on the underlying input. Useful
//              for screen readers and form submission.
//
// Events:
//   • change(hex)  — fired whenever the user picks a new color
component ColorPicker(value: string = "#1684ff", name: string = "color") {
  @state {
    // Mirror of the `value` prop so the textInput two-way binding has a
    // writable target. @watch keeps this in sync when the parent
    // updates `value` (e.g. on form reset).
    localColor: value
  }

  @watch {
    value: { syncFromProp() }
  }

  @actions {
    syncFromProp() {
      if value != localColor {
        localColor = value
      }
    }
    pick(c) {
      localColor = c
      emit("change", c)
    }
  }

  block {
    position: 'relative'
    width: 160px
    height: 38px

    // Visible chip — purely decorative. Clicks fall through to the
    // transparent native input below.
    block {
      padding-y: 6px
      padding-x: 10px
      border-radius: 8px
      border: token.input-border
      background: token.input-bg
      width: 160px
      layout: horizontal, gap: 8px, align: center

      block {
        width: 24px
        height: 24px
        border-radius: 6px
        background: localColor
        border: token.border-default
      }

      text(localColor) {
        color: semantic.text-secondary
        weight: 600
        style: type.label-sm
        grow: true
      }
      Icon(name: 'palette', size: 14, color: semantic.text-tertiary)
    }

    // Native HTML color picker, overlaid full-bleed and transparent.
    // The browser opens its OS picker on click. Two-way binding means
    // the value flows back into localColor as the user picks.
    block {
      position: 'absolute'
      top: 0px
      left: 0px
      width: 160px
      height: 38px
      cursor: 'pointer'
      textInput(localColor) {
        type: 'color'
        name: name
        width: 100%
        height: 100%
        opacity: 0
        cursor: 'pointer'
        on input: pick(localColor)
      }
    }
  }
}
