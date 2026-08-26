// Stepper — a multi-step progress indicator for sequential workflows.
//
// ── A step's own status (0.3.0) ─────────────────────────────────────────────
//
// Until 0.3.0 a step's mark had exactly one source: its index. Every step left
// of `activeStep` got a green ✓, every step right of it got its number. That
// models a strictly linear wizard, where the only way past a step is to finish
// it — and it is a lie for every wizard with a SKIPPABLE step, because moving
// past a step is not the same claim as completing it.
//
// The case that forced this: a six-step deal-origination wizard, three steps
// optional. Its shell computed a real per-step status, handed it to Stepper,
// and Stepper dropped it on the floor — so a step the user deliberately skipped
// showed a green tick meaning "done" while the review panel two inches below
// listed the same step in amber as "Not set" and named it as the reason the
// deal could not be created. One screen, two contradictory claims about the
// same step.
//
// So a step may now carry `status`:
//
//     steps: [
//       {id: 'terms',      label: 'Terms',      status: 'complete'},
//       {id: 'collateral', label: 'Collateral', status: 'skipped'},
//       {id: 'covenants',  label: 'Covenants',  status: 'incomplete'},
//       {id: 'review',     label: 'Review'}
//     ]
//
// ── Why a FIELD, and not a parallel `statuses` array prop ───────────────────
//
// A `statuses: array = []` prop was the obvious alternative and is worse in
// three concrete ways:
//
//   1. It is a second list to keep aligned with the first. Sort `steps`, filter
//      a step out for a deal type that does not need it, or splice one in, and
//      every status silently re-points at the wrong step. Nothing throws; the
//      screen is just wrong, which is the exact failure mode this change exists
//      to remove.
//   2. It is all-or-nothing. A caller who knows one step's status has to invent
//      a value for the rest. As a field, annotation is per step: an absent
//      `status` keeps that step on the positional rule, so a partly-annotated
//      Stepper is well defined.
//   3. `steps` already carries per-step data — `id`, `label`, `description`,
//      `optional`. A status IS per-step data, and it belongs where the rest of
//      it lives.
//
// The cost is real and worth naming: a field is invisible to the compiler's
// component-prop schema, so a typo (`state:` for `status:`) is not warned
// about, where an unknown PROP would be. `description` and `optional` already
// live with that trade, and being able to annotate one step out of six is worth
// more here than the typo check.
//
// ── The vocabulary, and what activeStep still owns ──────────────────────────
//
//   "complete"   — finished.               ✓ on green.
//   "skipped"    — deliberately passed over, and that is allowed.
//                                          – on gray.
//   "incomplete" — passed over, still needed.
//                                          ! on amber.
//   absent, "", or any word not in that list
//                — fall back to the positional rule, byte for byte.
//
// `activeStep` still owns "you are here": the step the user is standing on
// renders as the current step whatever its status says. Letting a status
// repaint the current step would re-create the contradiction above, one step to
// the left.
//
// Marks, not just colors. Each state has its own glyph, so the four are told
// apart with the color channel switched off — and the indicator carries
// `role: "img"` with an `aria-label` naming the step's position and state in
// words ("Step 2 of 4, skipped"), because a ✓ character and a hue are all a
// screen reader ever got from this component before. That name is built for a
// Stepper with no statuses too; it says "completed" / "current step" /
// "not started" from the positional rule.

// The state one step is in. Kept as one function because five style properties
// and the accessible name all have to agree about it; two of them disagreeing
// is the whole bug.
fn _stepState(step: map, i: number, activeStep: number) -> string {
  if i == activeStep { return "current" }
  let declared = step.status
  if declared == "complete"   { return "complete" }
  if declared == "skipped"    { return "skipped" }
  if declared == "incomplete" { return "incomplete" }
  if i < activeStep { return "complete" }
  return "upcoming"
}

// Whether the connector LEAVING step i should read as progress. Not derivable
// from _stepState: the current step reports "current", and a current step that
// is also finished should still lead on in green.
fn _stepDone(step: map, i: number, activeStep: number) -> boolean {
  let declared = step.status
  if declared == "complete"   { return true }
  if declared == "skipped"    { return false }
  if declared == "incomplete" { return false }
  return i < activeStep
}

fn _stepMark(step: map, i: number, activeStep: number) -> string {
  let state = _stepState(step, i, activeStep)
  if state == "complete"   { return "✓" }
  if state == "skipped"    { return "–" }
  if state == "incomplete" { return "!" }
  return toString(i + 1)
}

// The accessible name of the indicator. Position AND state, in words — the
// half of this change that survives a user who cannot see the green.
fn _stepName(step: map, i: number, count: number, activeStep: number) -> string {
  let state = _stepState(step, i, activeStep)
  let word = "not started"
  if state == "current"    { word = "current step" }
  if state == "complete"   { word = "completed" }
  if state == "skipped"    { word = "skipped" }
  if state == "incomplete" { word = "incomplete" }
  return "Step " + toString(i + 1) + " of " + toString(count) + ", " + word
}

component Stepper(steps: array = [], activeStep: number = 0, orientation: string = "horizontal", allowBack: boolean = true) {
  @computed {
    stepCount: steps.length
  }

  // Horizontal orientation
  block {
    visibility: orientation == "horizontal"
    layout: horizontal, align: center
    role: "group"
    aria-label: "Progress steps"

    each steps as step, i {
      block {
        layout: horizontal, align: center
        grow: true

        // Step indicator + label
        block {
          layout: vertical, align: center, gap: spacing.1
          cursor: allowBack && i < activeStep ? "pointer" : "default"
          on click: { if allowBack && i < activeStep { emit("change", i) } }

          // Circle indicator
          block {
            width: 32px
            height: 32px
            min-width: 32px
            border-radius: 9999px
            layout: horizontal, align: center, justify: center
            // role + aria-label: the glyph inside is a picture of the step's
            // state, and a bare <div> may not be named. aria-current is the
            // standard "this is the step you are on" for a process.
            role: "img"
            aria-label: _stepName(step, i, stepCount, activeStep)
            aria-current: i == activeStep ? "step" : "false"
            background: match _stepState(step, i, activeStep) {
              "current"    -> semantic.interactive,
              "complete"   -> "#22c55e",
              "skipped"    -> semantic.border,
              "incomplete" -> semantic.warning,
              _            -> semantic.surface-raised
            }
            border: match _stepState(step, i, activeStep) {
              "upcoming" -> borders.default,
              _          -> "2px solid transparent"
            }

            text(_stepMark(step, i, activeStep)) {
              style: type.label-sm
              color: match _stepState(step, i, activeStep) {
                "upcoming"   -> semantic.text-secondary,
                // Dark ink on the gray and the amber: white would clear no
                // contrast bar on either.
                "skipped"    -> semantic.text-secondary,
                "incomplete" -> semantic.text-primary,
                _            -> "#ffffff"
              }
            }
          }

          // Label
          text(step.label) {
            style: type.label-sm
            color: match _stepState(step, i, activeStep) {
              "current"    -> semantic.text-primary,
              "complete"   -> "#22c55e",
              "incomplete" -> semantic.warning-text,
              _            -> semantic.text-tertiary
            }
          }
        }

        // Connector line
        block {
          visibility: i < stepCount - 1
          grow: true
          height: 2px
          min-height: 2px
          margin: spacing.2
          background: _stepDone(step, i, activeStep) ? "#22c55e" : semantic.border
        }
      }
    }
  }

  // Vertical orientation
  block {
    visibility: orientation == "vertical"
    layout: vertical
    role: "group"
    aria-label: "Progress steps"

    each steps as step, i {
      block {
        layout: horizontal, gap: spacing.3

        // Track column: indicator + connector
        block {
          layout: vertical, align: center
          width: 32px
          min-width: 32px

          // Circle indicator
          block {
            width: 32px
            height: 32px
            min-width: 32px
            border-radius: 9999px
            layout: horizontal, align: center, justify: center
            cursor: allowBack && i < activeStep ? "pointer" : "default"
            role: "img"
            aria-label: _stepName(step, i, stepCount, activeStep)
            aria-current: i == activeStep ? "step" : "false"
            background: match _stepState(step, i, activeStep) {
              "current"    -> semantic.interactive,
              "complete"   -> "#22c55e",
              "skipped"    -> semantic.border,
              "incomplete" -> semantic.warning,
              _            -> semantic.surface-raised
            }
            border: match _stepState(step, i, activeStep) {
              "upcoming" -> borders.default,
              _          -> "2px solid transparent"
            }
            on click: { if allowBack && i < activeStep { emit("change", i) } }

            text(_stepMark(step, i, activeStep)) {
              style: type.label-sm
              color: match _stepState(step, i, activeStep) {
                "upcoming"   -> semantic.text-secondary,
                "skipped"    -> semantic.text-secondary,
                "incomplete" -> semantic.text-primary,
                _            -> "#ffffff"
              }
            }
          }

          // Vertical connector
          block {
            visibility: i < stepCount - 1
            width: 2px
            grow: true
            min-height: 24px
            background: _stepDone(step, i, activeStep) ? "#22c55e" : semantic.border
          }
        }

        // Label + description
        block {
          layout: vertical, gap: spacing.1
          padding: spacing.2

          text(step.label) {
            style: type.body-md
            color: match _stepState(step, i, activeStep) {
              "current"    -> semantic.text-primary,
              "complete"   -> "#22c55e",
              "incomplete" -> semantic.warning-text,
              _            -> semantic.text-tertiary
            }
          }

          block {
            visibility: step.description != null
            text(step.description) {
              style: type.caption
              color: semantic.text-tertiary
            }
          }
        }
      }
    }
  }
}
