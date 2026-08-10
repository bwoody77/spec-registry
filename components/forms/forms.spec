@extern { focusFormField } from "@spec/components/forms-focus.js"

// forms — the shared form standard: one validation engine, one field, one
// summary panel. Consumed by every Spec app, so it carries no app concepts.
//
// The rule this package exists to enforce: a form that cannot be submitted must
// say WHY, the moment the user tries. A disabled submit button with no
// explanation is not validation — it is a dead end. Nothing here takes a
// `disabled` prop driven by validity.

// Portable validation engine. Pure Spec — compiles to JS, Swift and Kotlin.
// Each check: { field: string, label: string, valid: boolean, message: string }.
// Returns { isValid, items, errors, firstField } where `errors` is keyed by
// field name and holds only the FAILING fields, and `firstField` names the
// first failing field in declaration order ('' when valid) so the summary can
// offer a jump-to-field link.
fn validateFields(checks: list) -> map {
  let failed = checks |> filter(c => !c.valid)
  return {
    isValid:    length(failed) == 0,
    items:      failed |> map(c => c.label),
    errors:     failed |> map(c => [c.field, c.message]) |> fromEntries,
    firstField: length(failed) > 0 ? failed[0].field : ''
  }
}

// FormField — a labelled control that knows its own error state.
//
// Two ways to drive the red state; pick one per field:
//
//   Derived (preferred). Pass the validation map, this field's key, and the
//   form's showErrors flag — the field works the rest out:
//
//     FormField(label: 'Name', value: name, validation: validation,
//               field: 'name', showErrors: showErrors) { on input(x): setName(x) }
//
//   Explicit. Pass error / errorMessage yourself. Kept so existing call sites
//   that already compute two ternaries per field keep working unchanged.
//
// Enter fires `submit` from the built-in single-line input only. In a textarea
// Enter is a newline; a slotted control owns its own Enter, because the
// registry DatePicker binds it to commit a date segment and Autocomplete to
// pick the highlighted option — taking those over breaks them silently.
//
// The wrapper always renders `data-field` when `field` is set. That is how
// FormErrorSummary's jump link finds it (forms-focus.js).
//
// Re-toning the label: use `labelTone: 'secondary' | 'primary'`, NOT
// `labelColor: semantic.text-secondary`. A token passed in through `labelColor`
// arrives already resolved and stops tracking the theme — see the note on
// `effLabelColor` below.
component FormField(
  label:        string  = '',
  value:        string  = '',
  placeholder:  string  = '',
  inputType:    string  = 'text',
  validation:   map     = null,
  field:        string  = '',
  showErrors:   boolean = false,
  error:        boolean = false,
  errorMessage: string  = '',
  labelWeight:  number  = 700,
  labelSpacing: string  = '0.06em',
  labelTone:    "tertiary" | "secondary" | "primary" = 'tertiary',
  labelColor:   string  = '',
  labelStyle:   string  = '',
  fieldGap:     string  = '6px'
) {
  @computed {
    // Only take over the error state when a validation map AND a field key are
    // supplied; otherwise the explicit error/errorMessage props win untouched.
    derives:    validation != null && field != ''
    failing:    derives && validation.errors != null && validation.errors[field] != null
    effError:   derives ? (showErrors && failing) : error
    effMsg:     derives ? ((showErrors && failing) ? validation.errors[field] : '') : errorMessage
    isTextarea: inputType == 'textarea'
    // `labelTone` — NOT `labelColor` — is how a caller re-tones the label.
    //
    // A theme token has to be resolved INSIDE the component to stay live. Write
    // `labelColor: semantic.text-secondary` at a call site and the *caller*
    // compiles it to a one-shot `_tok("text-secondary")()`, so what arrives here
    // is the string "#3d4a5f" — a colour frozen at mount. Nothing this component
    // does can thaw it: the freeze happened before the prop was passed. Switch
    // the app to a dark theme and every such label keeps the light-theme colour
    // while its plain-`text()` neighbours move. (Confirmed in a browser
    // 2026-08-10, four labels stuck at rgb(61,74,95) on a dark canvas.)
    //
    // Naming the tone instead keeps the token reference in this file, where the
    // computed below subscribes to it — the emitted computed carries `_ts`/`_tv`
    // in its dependency list, so a theme change re-runs it.
    //
    // `labelColor` still wins when set, and is the escape hatch for a colour
    // that is not a token at all (a brand hex, a computed rgba). Passing a
    // token through it is the one thing it cannot do.
    effLabelColor: labelColor != '' ? labelColor
                 : (labelTone == 'secondary' ? semantic.text-secondary
                 : (labelTone == 'primary'   ? semantic.text-primary
                 : semantic.text-tertiary))
    effLabelStyle: labelStyle != '' ? labelStyle : type.label-xs
  }

  @actions {
    onKey(e) {
      if e.key == 'Enter' && !isTextarea { emit("submit") }
    }
  }

  block {
    layout: vertical, gap: fieldGap
    data-field: field

    block {
      visibility: label != ''
      text(label) {
        color: effLabelColor
        weight: labelWeight
        style: effLabelStyle
        letter-spacing: labelSpacing
      }
    }

    // A `visibility:`-gated block that contains a component instance (here,
    // TextInput — a SurfaceRef) compiles to a LAZY MOUNT, not a display:none
    // toggle on a persisted node: ast-to-ir.ts's `hasVisibility && hasSurfaceRef`
    // branch (ast-to-ir.ts:3738) routes it through lazyMount (ir-to-js.ts:2352-
    // 2387), which keeps the children unmounted while the condition is false.
    // So the built-in input is not merely hidden when a control is slotted —
    // it is never mounted at all. (A visibility-gated block with no component
    // instance inside it, e.g. the plain `text()` blocks elsewhere in this
    // file, *does* get the display:none treatment; only the SurfaceRef case
    // takes the lazy-mount path.)
    block {
      visibility: !hasSlot("control")
      TextInput(value: value, placeholder: placeholder, type: inputType,
                error: effError, errorMessage: effMsg) {
        on change(x): emit("input", x)
        on keydown(e): onKey(e)
      }
    }

    // `@slot` emits its `[data-slot]` container unconditionally — an empty
    // `display:block` div is still a flex item, so on a field using the
    // built-in input it cost a full `fieldGap` (6px) of dead space under
    // every field. Gating the container on the slot being filled makes the
    // wrapper `display:none`, which is not a flex item and generates no gap.
    //
    // The gate is safe here for the reason the comment above explains in
    // reverse: this block holds a `@slot`, not a SurfaceRef, so it takes the
    // display:none path rather than the lazy-mount one — the slotted control
    // is mounted exactly as before when the slot IS filled.
    block {
      visibility: hasSlot("control")
      @slot("control")
    }

    // The built-in TextInput renders its own caption. A slotted control cannot
    // — slot content is evaluated in the CALLER's scope, so this component's
    // computed error state is not reachable from inside it. The caller passes
    // its own `error:` to its own control; the message is rendered here.
    block {
      visibility: hasSlot("control") && effMsg != ''
      text(effMsg) {
        style: type.caption
        color: semantic.destructive
      }
    }
  }
}

// FormErrorSummary — the "fix these to continue" panel, plus a link that jumps
// to and focuses the first failing field.
//
// Place it next to the submit button; on a long form place a second one at the
// top of the form as well.
//
//   FormErrorSummary(visible: showErrors && !validation.isValid,
//                    items: validation.items, firstField: validation.firstField)
//
// The jump link is a real `button` so it is keyboard reachable — a div here
// would strand exactly the users who most need it. It hides itself when
// `firstField` is empty, which is what lets a caller adopt the panel first and
// the jump affordance later.
//
// A summary with nothing to report takes NO space in its parent's layout — it
// can sit directly in a `layout: horizontal, gap: …` button row without
// budgeting for it. See the note on the root `visibility:` below.
component FormErrorSummary(
  visible:    boolean = false,
  title:      string  = 'Fix these to continue:',
  items:      array   = [],
  firstField: string  = '',
  jumpLabel:  string  = 'Go to first problem'
) {
  // Top-level `visibility:` binds the COMPONENT ROOT's display, not a child's.
  // Every component is emitted inside a `_root` div, and that div is a flex
  // item of whatever laid the component out. With the gate only on the inner
  // block, the root stayed `display:block` at width 0 — so a form with nothing
  // wrong still paid a full `gap` after the last button (measured: 12px in cf's
  // submit row, 2026-08-10). display:none on the root removes it from the
  // parent's flex layout entirely.
  //
  // The inner gate is kept as well: it costs nothing, and it keeps the
  // `role="alert"` panel aria-hidden on its own terms rather than only by
  // inheritance from an ancestor.
  visibility: visible && items.length > 0

  block {
    visibility: visible && items.length > 0
    padding: 10px 12px
    background: semantic.destructive-bg
    border: borders.danger
    border-radius: 8px
    layout: vertical, gap: 4px
    role: 'alert'

    text(title) { color: semantic.destructive-hover, weight: 700, style: type.body-sm }
    each items as it, i {
      text('• ' + it) { color: semantic.destructive-hover, weight: 500, style: type.body-sm }
    }

    button {
      visibility: firstField != ''
      background: 'transparent'
      border: 'none'
      padding: 0
      margin-top: 2px
      cursor: 'pointer'
      layout: horizontal, gap: 4px, align: center
      on click: focusFormField(firstField)

      text(jumpLabel) {
        color: semantic.destructive-hover
        weight: 700
        style: type.body-sm
        text-decoration: 'underline'
      }
    }
  }
}
