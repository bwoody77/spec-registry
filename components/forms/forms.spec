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
        color: semantic.text-tertiary
        weight: labelWeight
        style: type.label-xs
        letter-spacing: labelSpacing
      }
    }

    TextInput(value: value, placeholder: placeholder, type: inputType,
              error: effError, errorMessage: effMsg) {
      on change(x): emit("input", x)
      on keydown(e): onKey(e)
    }
  }
}
