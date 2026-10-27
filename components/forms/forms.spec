@extern { focusFormField, pulseFormField } from "@spec/components/forms-focus.js"

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
// Re-toning the label: use `labelTone: 'secondary' | 'primary'`. `labelColor`
// is for a color that is not a theme token — see the note on `effLabelColor`
// below.
//
// Naming: this component renders the visible label ITSELF and mounts TextInput
// in a different block, so `label` alone named nothing — see `effAriaLabel`.
// Pass `ariaLabel` only when the accessible name must differ from the visible
// one, or when there is no visible label at all.
component FormField(
  label:        text  = '',
  ariaLabel:    text  = '',
  value:        string  = '',
  placeholder:  text  = '',
  inputType:    string  = 'text',
  // Forwarded to the built-in TextInput's `autocomplete` (0.14.0+): the
  // browser's fill hint. Empty omits the attribute. A password field that is
  // not the viewer's own sign-in says 'new-password': on a page with no
  // <form> Chrome otherwise reads it as a login and fills the saved email
  // into the text field before it, and 'off' does not stop that (Vector
  // #2757, an S3 key ID).
  autocomplete: string  = '',
  validation:   map     = null,
  field:        string  = '',
  showErrors:   boolean = false,
  error:        boolean = false,
  errorMessage: text  = '',
  // Forwarded verbatim to the built-in TextInput; its value space is
  // TextInput's ("default" | "warning" | "danger" | "highlight").
  //
  // This is how a caller marks a field as WANTED without marking it WRONG.
  // `error:` means "you broke a rule the submit enforces"; `tone: 'warning'`
  // means "something still wants this" — a blank field nobody has asked for
  // yet is not a mistake, and painting it in the error colour tells the user
  // they made one.
  //
  // Forwarded rather than reconciled here on purpose: TextInput already
  // resolves `match error { true -> destructive, _ -> match tone { ... } }`,
  // so a field that is both a gap and a failed validation reads as the
  // failure with no precedence logic in this component to drift out of sync.
  //
  // Defaults to 'default', so every existing call site is untouched.
  tone:         string  = 'default',
  labelWeight:  number  = 700,
  labelSpacing: string  = '0.06em',
  labelTone:    "tertiary" | "secondary" | "primary" = 'tertiary',
  labelColor:   string  = '',
  labelStyle:   string  = '',
  // PAINT ONLY — the visible label's `text-transform`.
  //
  // The accessible name is deliberately NOT transformed. `effAriaLabel` falls
  // back to `label`, so an app wanting uppercase labels without this prop had
  // to pass 'PHONE' as the label itself — which is the name a screen reader
  // then announces. Casing is a visual decision and must not leave the paint
  // layer.
  //
  // Defaults to 'none', so every existing call site is untouched.
  labelTransform: "none" | "uppercase" = 'none',
  fieldGap:     string  = '6px'
) {
  @state {
    // The words a slotted control's caption says. The props reach it through
    // followCaption(), not directly: see "Saying it again" below. Seeded from
    // effMsg once, so a field mounted with an error already set shows it.
    capWords: effMsg
    // True for 100ms after the caption went empty: the page may not have drawn
    // the empty caption yet, so words arriving now wait until it has.
    capHeld: false
  }

  @computed {
    // Only take over the error state when a validation map AND a field key are
    // supplied; otherwise the explicit error/errorMessage props win untouched.
    derives:    validation != null && field != ''
    failing:    derives && validation.errors != null && validation.errors[field] != null
    effError:   derives ? (showErrors && failing) : error
    effMsg:     derives ? ((showErrors && failing) ? validation.errors[field] : '') : errorMessage
    isTextarea: inputType == 'textarea'
    // The accessible name for the built-in input.
    //
    // This component renders the visible label in its OWN block and mounts
    // TextInput in another, which defeats both of the routes that would
    // otherwise name the input:
    //
    //   - the compiler's inferAccessibleNames only reaches a control whose
    //     label is the immediately-preceding rendering SIBLING of the mount;
    //   - TextInput's own `label:` prop does name the input — but it also
    //     RENDERS the label (text-input.spec `block { visibility: label != "" }`),
    //     so forwarding `label` down that channel would print every field's
    //     label twice. That is why the migration dropped it, and why the name
    //     has to travel on `ariaLabel`, which names without rendering.
    //
    // Chain: explicit ariaLabel, then the visible label, then '' — which hands
    // the decision back to TextInput's own fallback (placeholder, else no
    // attribute at all). Never emit a name this component invented: '' is
    // passed through, and TextInput turns a fully-empty chain into `null` so
    // the attribute is REMOVED rather than set to an empty (real, and
    // silencing) accessible name.
    //
    // `ariaLabel` wins over `label` deliberately: the case it exists for is a
    // terse visible label that needs a fuller spoken one ('Unit price' →
    // 'Unit price in USD per metric tonne'). Because declaring `ariaLabel`
    // also opts this component into inferAccessibleNames, a caller's preceding
    // heading could otherwise out-rank the field's own label — the compiler
    // now declines to infer for a call that passes its own `label:`
    // (ast-to-ir inferAccessibleNames), which keeps that ordering safe.
    effAriaLabel: ariaLabel != '' ? ariaLabel : label
    // `labelTone` is how a caller re-tones the label: it names the tone, and
    // the token lookup below stays in this file, where the computed subscribes
    // to it (the emitted computed carries `_ts`/`_tv` in its dependency list),
    // so a theme change re-runs it.
    //
    // `labelColor` wins when set, and is the escape hatch for a color that is
    // not a token at all (a brand hex, a computed rgba). A token passed through
    // it follows the theme too: since Vector #2620 the caller forwards a
    // token-only argument live (`_tok("text-secondary")`) rather than as a
    // value resolved at mount. Prefer `labelTone` for a token anyway, so the
    // set of tones a label can take stays in one place.
    effLabelColor: labelColor != '' ? labelColor
                 : (labelTone == 'secondary' ? semantic.text-secondary
                 : (labelTone == 'primary'   ? semantic.text-primary
                 : semantic.text-tertiary))
    // The default comes from the `field-labelStyle` COMPONENT TOKEN, so an app
    // sets its field-label size once — `@visual-system { field.labelStyle:
    // 'body-md' }`, or per theme `@theme dense { field-labelStyle: 'label-xs' }`
    // — instead of passing `labelStyle:` at every call site. The token's value
    // space is the prop's: a type-scale level name, never a CSS length. The
    // explicit prop still wins, so a single odd field stays a one-line override.
    //
    // The token ships as 'label-sm', which is what this line hardcoded before —
    // adopting it changes nothing until an app overrides it.
    //
    // label-sm, not label-xs. `label-xs` is floor-clamped at 10px, so an
    // unstyled field label rendered at or below the CAPTION tier — a field's
    // name no larger than its own footnote. Two signals, not one opinion:
    // Vector's LabeledField (the ~95 call sites this component replaces)
    // hardcodes label-sm, so an `label-xs` default would silently shrink every
    // label 11.2px → 10px on a pure rename; and cf overrides `labelStyle` at
    // every labelled call site rather than accept the default. A default every
    // adopter overrides is the wrong default.
    effLabelStyle: labelStyle != '' ? labelStyle : token.field-labelStyle
    // A style value that varies is a NAMED computed, never an inline
    // expression on the property. Normalised to an explicit 'none' rather than
    // passed through, so the emitted declaration is always a valid
    // text-transform even if the union ever grows a value CSS does not know.
    effLabelTransform: labelTransform == 'uppercase' ? 'uppercase' : 'none'

    // ── A slotted control's error, said as well as painted (Vector #1136) ───
    //
    // The built-in TextInput draws and speaks its own error (text-input 0.12).
    // A slotted control cannot get this component's error state (slot content
    // is evaluated in the CALLER's scope), so the caption under it is drawn
    // here, and it is TextInput's line: a role=alert region that is always in
    // the field, empty until there is a message, and out of the flow while
    // empty, so a field with no error takes exactly the room it took before
    // (the column's `gap` does not apply to an absolute child).
    //
    // It used to be a block gated by `visibility: effMsg != ''`, which compiles
    // to display:none. A live region that enters the accessibility tree
    // together with its words is never announced, so a Select, a date picker
    // or a money field in a slot failed in silence, even the first time.
    //
    // ── Saying it again ──────────────────────────────────────────────────────
    //
    // A live region speaks when its text CHANGES, so the same message set
    // twice is heard once. The host's half is to empty the message (or turn
    // showErrors off) as each attempt starts and then refill it. A check that
    // fails without a request does both in ONE action, and Spec writes the DOM
    // once per frame, so the caption would go from the words to the same words.
    // So it shows `capWords`, not `capText`: words that arrive within 100ms of
    // the caption going empty wait out those 100ms with it empty (TextInput
    // 0.12.1 and Vector's kit ErrorLine do the same). Meanwhile `capStandIn`
    // paints them where the caption stands, aria-hidden, so the field neither
    // blinks nor moves. A first message, or a different one, shows at once,
    // and a clear empties the caption at once.
    //
    // The words are effMsg, as the caption always drew them: on the explicit
    // path a slotted field shows `errorMessage` whatever `error` says, because
    // the caller paints its own control red.
    capText: effMsg
    capShown: capWords != ''
    capPosition: capShown ? 'static' : 'absolute'
    capStandIn: capHeld ? capText : ''
    capStandInShown: capStandIn != ''
  }

  @watch {
    // Every prop effMsg reads, not effMsg itself: a watch on one prop reads a
    // sibling's old value when the caller changes both, so each runs the same
    // follow and the last one sees them all (TextInput's shape).
    //
    // Immediate (`!`), so the caption also follows at construction (0.9.3).
    // The @state seed already shows a message set at mount, so this changes
    // nothing on screen; it says what is true: FormField latches nothing and
    // needs no false → true edge, so a field built under a `visibility:` gate
    // with `showErrors: true` is fine. A non-immediate watch on a prop is how
    // an overlay that DOES latch (Modal's `open`) looks, and Vector's
    // check-lazy-gated-overlays reads it that way.
    errorMessage!: { followCaption() }
    validation!: { followCaption() }
    showErrors!: { followCaption() }
    field!: { followCaption() }
  }

  @actions {
    onKey(e) {
      if e.key == 'Enter' && !isTextarea { emit("submit") }
    }
    followCaption() {
      let words = effMsg
      if words == '' {
        if capWords != '' {
          capWords = ''
          capHeld = true
          delay("capRefill", 100) {
            capHeld = false
            capWords = effMsg
          }
        }
        return
      }
      if !capHeld {
        capWords = words
      }
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
        text-transform: effLabelTransform
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
      // `ariaLabel:`, never `label:` — see the note on effAriaLabel. `label:`
      // would render a second visible copy of every field's label.
      TextInput(value: value, placeholder: placeholder, type: inputType,
                autocomplete: autocomplete,
                ariaLabel: effAriaLabel, tone: tone,
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
    //
    // A `match`, not `visibility: hasSlot("control") && effMsg != ''`. With no
    // component inside it, that block compiled to display:none on a node that
    // was always mounted, so a field using the built-in input carried a second,
    // hidden copy of every error beside TextInput's own — found twice by a
    // strict text locator, an `includeHidden` query or a screen reader (Vector
    // #879, the class of #796). `hasSlot` is answered once at mount, so the arm
    // never taken costs a comment node.
    //
    // Inside the slotted arm the caption is a live region that is always here
    // (see capText above), never a `visibility:` gate. `data-error-line` names
    // it by the field's key, the hook Vector's e2e helper finds a line by.
    match hasSlot("control") {
      true -> {
        block {
          role: 'alert'
          aria-live: 'assertive'
          data-error-line: field
          position: capPosition
          text(capWords) {
            style: type.caption
            color: semantic.destructive
          }
        }
        // The same words while the caption waits out its empty moment (see
        // "Saying it again"), painted in its place so the field neither blinks
        // nor moves. aria-hidden and outside the region: the caption is what
        // speaks, once the wait is over. Empty and display:none otherwise, so
        // a field holds no hidden copy of its message.
        block {
          visibility: capStandInShown
          aria-hidden: 'true'
          text(capStandIn) {
            style: type.caption
            color: semantic.destructive
          }
        }
      },
      _ -> {}
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
  title:      text  = 'Fix these to continue:',
  items:      array   = [],
  firstField: string  = '',
  jumpLabel:  text    = 'Go to first problem'
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

    // body-md, not body-sm. This panel is the message that tells someone the
    // form will not submit; at body-sm it rendered SMALLER than every control
    // around it (measured in Vector at its 1.125 scale on 2026-08-10: 12.6px
    // against 15.75px controls, only 1.35px above a per-field caption). The
    // weights carry the emphasis — the size should not also whisper.
    text(title) { color: semantic.destructive-hover, weight: 700, style: type.body-md }
    each items as it, i {
      text('• ' + it) { color: semantic.destructive-hover, weight: 500, style: type.body-md }
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
        style: type.body-md
        text-decoration: 'underline'
      }
    }
  }
}
