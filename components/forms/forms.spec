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
