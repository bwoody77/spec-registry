// Alert — a status notice.
//
// 0.3.0 REPLACES the 0.2.0 API. This component is a promotion of a real
// application's `InlineAlert`, which was itself built to absorb 181 open-coded
// copies of the same shape across 75 files — the single largest duplication
// class in that codebase, and one no declaration-level audit could see, because
// markup that was never declared is not a duplicate declaration.
//
// What changed from 0.2.0, and why:
//
//   severity: 'error'  ->  tone: 'destructive'   name the ROLE, not the mood;
//                                                matches semantic.destructive-*
//   token.alert-*      ->  semantic.* / borders.*  the platform's own ladders,
//                                                which every other component
//                                                here already uses. The old
//                                                alert-* set was a private
//                                                fourth palette that themes had
//                                                to style separately.
//   role="alert"       ->  (none)                see the a11y note below.
//   +title +icon +compact +flush +gutter +@children +colour overrides
//
// 0.2.0 consumers pin ^0.2.0 and are unaffected until they widen the range.
//
// ── Why no `role` ────────────────────────────────────────────────────────────
// 0.2.0 set role="alert" unconditionally. role="alert" is an ASSERTIVE live
// region: a screen reader interrupts whatever it is saying, every time the node
// is re-rendered. On a notice that is simply PRESENT on the page — "3 things to
// finish", a form's static hint — that is not an announcement, it is a barrage.
//
// A conditional role is not expressible: the compiler takes a literal for
// `role`, so `role: assertive ? "alert" : ""` does not compile. Given the
// choice, the static case is overwhelmingly the common one, so it wins. A
// caller that genuinely needs an assertive announcement — a submit failure the
// user must hear — should wrap this in its own role="alert" region, or use a
// dedicated error-summary component.
//
// ── The shrink trap this component used to hit ───────────────────────────────
// A tinted box with a border-radius is a flex item in most layouts, and the
// compiler auto-injects an overflow for the radius. Until spec e6bb0af that
// overflow was `hidden`, which zeroes a flex item's automatic minimum size —
// so the box could be crushed below its own text and then clip it, silently.
// It is `clip` now (no scroll container, minimum size survives). Nothing here
// works around it; the note exists so the next person to see a short banner
// looks at the compiler rule rather than at this file.

component Alert(
  // 'info' | 'success' | 'warning' | 'destructive'
  tone:    string  = 'info',
  message: string  = '',
  // Optional bolded first line above the message.
  title:   string  = '',
  // Overrides the per-tone default glyph. 'none' hides the icon entirely;
  // '' means "use the tone's default", which is what the default value does.
  icon:    string  = '',
  // Tighter padding for a notice inside a dense panel or dialog.
  compact: boolean = false,
  // Full-bleed page banner instead of an inset rounded notice: square corners
  // and a single bottom rule, so it sits flush against the header above it.
  //
  // A variant rather than a second component because everything that varies by
  // tone — the four background/border/text/icon ladders — is identical; copying
  // those to get a square-cornered box is the duplication this exists to stop.
  flush:   boolean = false,
  // Horizontal padding. Only meaningful with `flush`, where it must line up
  // with the page's own gutter — '' keeps the standard inset padding.
  gutter:  string  = '',
  // Escape hatch for an APPLICATION-SPECIFIC tone the platform has no role for
  // — a maintenance purple, a brand violet. Pass all four together; each falls
  // back to the resolved tone when empty, so passing none changes nothing.
  //
  // This exists so an app does not fork the component to add one colour. It is
  // deliberately raw values rather than a fifth tone name: the platform has no
  // opinion about what "maintenance" means, and inventing a token for it here
  // would put one app's domain into everyone's design system.
  bg:       string = '',
  border:   string = '',
  fg:       string = '',
  iconTint: string = ''
) {
  @computed {
    isSuccess: tone == 'success'
    isWarning: tone == 'warning'
    isDanger:  tone == 'destructive'

    toneBg:     isDanger  ? semantic.destructive-bg
              : isWarning ? semantic.warning-bg
              : isSuccess ? semantic.success-bg
              : semantic.interactive-bg
    toneBorder: isDanger  ? borders.destructive
              : isWarning ? borders.warning
              : isSuccess ? borders.success
              : borders.interactive
    toneFg:     isDanger  ? semantic.destructive
              : isWarning ? semantic.warning-text
              : isSuccess ? semantic.success-text
              : semantic.interactive-text
    toneIcon:   isDanger  ? semantic.destructive
              : isWarning ? semantic.warning
              : isSuccess ? semantic.success
              : semantic.interactive

    alertBg:     bg       != '' ? bg       : toneBg
    alertBorder: border   != '' ? border   : toneBorder
    alertFg:     fg       != '' ? fg       : toneFg
    iconColor:   iconTint != '' ? iconTint : toneIcon

    defaultIcon: isDanger  ? 'alert-triangle'
               : isWarning ? 'alert-triangle'
               : isSuccess ? 'circle-check'
               : 'info'
    iconName:    icon != '' ? icon : defaultIcon
    showIcon:    iconName != 'none'

    padY:       compact ? 8px : 12px
    hasTitle:   title != ''
    hasMessage: message != ''

    // Conditional style values must be named computeds, never inline. The
    // PROPERTY to set cannot itself be conditional, so BOTH border keys are
    // always emitted and `flush` decides what each holds.
    //
    // `border-bottom` carries the tone in BOTH modes, and that is not
    // redundancy — it is why this works. The compiler emits `border` before
    // `border-bottom`, so whatever the second key holds wins for the bottom
    // edge. Setting it to 'none' when not flush would quietly strip the bottom
    // rule off every ordinary inset alert.
    alertRadius:     flush ? '0px' : '8px'
    alertBoxBorder:  flush ? 'none' : alertBorder
    alertEdgeBorder: alertBorder
    // A string on both branches — `gutter` is a string prop and the compact
    // padding is a size literal; mixing the two in one ternary invites trouble.
    alertPadX:       gutter != '' ? gutter : (compact ? '10px' : '12px')
  }

  block {
    padding-y: padY
    padding-x: alertPadX
    border-radius: alertRadius
    background: alertBg
    border: alertBoxBorder
    border-bottom: alertEdgeBorder
    layout: horizontal, gap: 8px, align: start

    block {
      visibility: showIcon
      Icon(name: iconName, size: 14, color: iconColor)
    }

    block {
      grow: true
      layout: vertical, gap: 2px, align: start

      block {
        visibility: hasTitle
        text(title) { color: alertFg, weight: 600, style: type.body-md }
      }
      block {
        visibility: hasMessage
        text(message) { color: alertFg, weight: 500, style: type.body-md }
      }
      // Renders after the message, inside the box, for a trailing action link
      // ("View aircraft status ›") or a short list of rows.
      @children
    }
  }
}
