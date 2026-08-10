// ModalSelect — a controlled overlay picker: pick one row (or several) from a
// set too rich for a dropdown.
//
// Wraps Modal, so scroll lock, focus trap, Escape/backdrop dismiss and a
// labelled role="dialog" are inherited rather than rebuilt. Renders its own
// rows rather than reusing Table: Table has no row click, no selection and no
// disabled state, and teaching it those to serve one caller is the wrong trade.
// The columns[] contract is Table's, so the two read alike.
//
// PURE. It emits and the caller acts — there is no action prop, no endpoint
// prop, no busy/error props. That is what keeps it usable for pick-a-user,
// pick-a-counterparty or pick-a-document-template, none of which share any one
// caller's semantics.
//
// Props:
//   open      — controlled visibility
//   title     — dialog heading, and the default accessible name
//   width     — dialog width (Modal caps it at 95vw)
//   columns   — [{ key, header, width? }], same contract as Table's columns[]
//               for parity — but `width` is CURRENTLY IGNORED, same as
//               Table's own. Every cell hardcodes `grow: true; min-width:
//               80px` regardless of `width`, so do not design against it
//               yet. Per-column `min-width: col.width` compiles and
//               evaluates correctly in this `each columns as col` loop —
//               the loop is not what stands in the way — but wiring it up
//               across both the header and body cell loops, and deciding
//               the `max-width` counterpart, has not been done.
//   rows      — [{ value, ...cellValues }]; value is the emitted identity and
//               the row's React-style key. A row with `disabled: true` is
//               rendered aria-disabled, taken out of the tab order, ignored
//               on click (see pickRow() below), shown with a muted cursor
//               and cell text colour, and removed from hit-testing
//               (pointer-events: none); its hover highlight is suppressed
//               by a conditional `on hover` — see the row button below.
//   loading   — shows content-shaped skeleton rows in place of the table
//   emptyMessage — shown when rows is empty and loading is false; distinct
//               from the "no matches for your search" state below — different
//               cause, different fix, so they never share a string
//   searchable — shows a search field (first child of the dialog) that
//               filters rows against every column's value, case-insensitively.
//               Hidden when there is nothing to search (rows is empty, or the
//               caller opts out) — a filter over an empty set is a dead
//               control.
//   multi      — false: a row click picks and closes immediately (unchanged).
//               true: a row click toggles membership in `selected` instead —
//               aria-pressed reflects it, a disabled row still cannot be
//               toggled — and a footer (last child of the dialog) shows the
//               running count plus Cancel/confirm. Confirm emits select()
//               with the whole array, then close(); it is a no-op with
//               nothing selected. The selection resets to empty every time
//               the dialog opens (see @watch below), so a reopened picker
//               never carries a stale selection over.
//   confirmLabel — the multi-select footer's confirm button label prefix;
//               the button itself always also shows the live count
//               ("Add 2"), so the caller only supplies the verb.
//
// The table, loading, empty and no-match blocks are mutually exclusive — see
// the @computed isEmpty/hasRows/noMatch latch below, which gates on HAVING
// TRIED (!loading), never on emptiness alone. Truth table over
// {loading, rows.length, visibleRows.length}:
//
//   loading  rows.length  visibleRows.length | table  loading  empty  noMatch
//   true     *            *                  | no     YES      no     no
//   false    0            0                  | no     no       YES    no
//   false    >0           0                  | no     no       no     YES
//   false    >0           >0                 | YES    no       no     no
//
// `loading` is checked first in every computed (`!loading && …`), so it alone
// decides the loading row. Among the three `!loading` rows, `rows.length ==
// 0` and `rows.length > 0` partition the remaining space, and within
// `rows.length > 0`, `visibleRows.length == 0` / `> 0` partition again — so
// exactly one of {loading, isEmpty, noMatch, hasRows} is true in every
// reachable state.
//
// Emits: close(), select(value) — in single mode (the default), clicking a
// row emits select(value) (one value) and is immediately followed by
// close(). In multi mode, select(value) instead carries the whole selected
// array, emitted (with close()) only from the footer's confirm button — row
// clicks toggle silently and emit nothing.
//
// Slots:
//   cell(col, row) — rendered ABOVE the default `text(row[col.key])` in
//   every cell, not instead of it — same idiom as table.spec:44-50, which
//   also renders both. Lets a caller add a badge or icon in one column
//   without losing the default text.
component ModalSelect(
  open: boolean = false,
  title: string = "Select",
  width: string = "640px",
  columns: array = [],
  rows: array = [],
  loading: boolean = false,
  emptyMessage: string = "Nothing to choose from",
  searchable: boolean = true,
  multi: boolean = false,
  confirmLabel: string = "Add"
) {
  @state {
    query: ""
    selected: []
  }

  @computed {
    q: query |> toLowerCase()

    // One searchable haystack per row, built from every column value — a
    // search that only reads the first column silently ignores the others.
    // There is no `join` in the stdlib (ai-reference.md:948-957); `reduce` is
    // the documented way to fold columns into one string.
    prepared: rows |> map(r => {
      return {
        row: r,
        hay: columns |> reduce((acc, c) => acc + " " + toString(r[c.key]), "") |> toLowerCase()
      }
    })

    matched:     q == "" ? prepared : (prepared |> filter(p => p.hay |> includes(q)))
    visibleRows: matched |> map(p => p.row)

    // Latch on HAVING TRIED, never on emptiness alone — the four states must
    // be mutually exclusive or two render at once (see the truth table above).
    isEmpty:    !loading && rows.length == 0
    hasRows:    !loading && rows.length > 0 && visibleRows.length > 0
    noMatch:    !loading && rows.length > 0 && visibleRows.length == 0
    showSearch: searchable && !loading && rows.length > 0

    noMatchText: "No matches for “" + query + "”"

    // Multi-select footer state — see the `multi` prop doc above.
    // `hasSelection`/`confirmText`/`countText` each read `selected.length`
    // inline: there is only one thing to keep in sync, so a separate
    // `selectedCount` computed would be one more name for the same value.
    hasSelection: selected.length > 0
    confirmText:  confirmLabel + " " + toString(selected.length)
    countText:    toString(selected.length) + " selected"
  }

  @actions {
    pick(v) {
      emit("select", v)
      emit("close")
    }

    // Row-level entry point: honours row.disabled before delegating to
    // pick() (single mode) or toggle() (multi mode). Kept separate from
    // pick() so a caller driving selection some other way (e.g. a future
    // keyboard-only path) still has the value-only action available.
    pickRow(r) {
      if r.disabled == true { return }
      match multi {
        true -> toggle(r.value),
        _    -> pick(r.value)
      }
    }

    // Flips one value in the selection set. `selected` never holds
    // duplicates: a value already in the set is removed, otherwise it is
    // appended. Assigns the RESULT of the match (same shape as
    // accordion.spec's toggle()), not an assignment inside each arm — an
    // arm body of `{ selected = ... }` parses as an OBJECT LITERAL in this
    // expression position (the compiler expects `identifier: value` and
    // errors on the bare `=`), not as a statement block.
    toggle(v) {
      selected = match selected |> includes(v) {
        true -> selected |> filter(x => x != v),
        _    -> selected.concat([v])
      }
    }

    // Multi-select's confirm action — the array analogue of pick(). A no-op
    // with nothing selected, so the confirm button emits nothing when
    // pressed on an empty selection (it is also disabled then, via
    // hasSelection, but this guards the action itself, not just the UI).
    confirmSelection() {
      if selected.length == 0 { return }
      emit("select", selected)
      emit("close")
    }
  }

  @watch {
    // Reset the selection AND the search query every time the dialog opens,
    // so a reopened picker never carries stale state from a previous
    // open/close cycle. `query` is assigned by nothing but the search
    // field's `on change` (below) — without this it survives close->reopen
    // and a reopened picker redisplays a filtered subset, or lands directly
    // on "No matches for ..." if `rows` changed between opens. Same
    // object-literal-vs-block trap as toggle() above — assign the match's
    // result rather than assigning inside an arm.
    open: {
      selected = match open {
        true -> [],
        _ -> selected
      }
      query = match open {
        true -> "",
        _ -> query
      }
    }
  }

  Modal(open: open, title: title, width: width, chrome: true) {
    on close: emit("close")

    block {
      data-modal-select: "dialog"
      layout: vertical, gap: spacing.3

      // Search — filters visibleRows against every column. Hidden when
      // there is nothing to search (see showSearch above).
      block {
        visibility: showSearch
        data-modal-select: "search"

        TextInput(placeholder: "Search", value: query) {
          on change(v): { query = v }
        }
      }

      // Rows table. Header + one button per row; the button is real so Tab
      // and Enter work without any key handling of our own.
      block {
        visibility: hasRows
        data-modal-select: "table"
        border: borders.default
        border-radius: 10px
        overflow: hidden
        layout: vertical

        // Header
        block {
          layout: horizontal
          background: semantic.surface-raised
          border-bottom: borders.default

          each columns as col {
            block {
              padding: spacing.2
              grow: true
              min-width: 80px
              text(col.header) {
                style: type.label-sm
                weight: 600
                color: semantic.text-secondary
                text-transform: "uppercase"
                letter-spacing: "0.05em"
                text-align: "start"
              }
            }
          }
        }

        // Scrollable rows wrapper — the motivating case is "a tenant with
        // thirty templates" (roughly 1200px of rows against Modal's ~900px
        // max-height cap). Without this, Modal's own body scroller
        // (overflow: auto inside max-height: 90vh — modal.spec:86-87) is the
        // ONLY scroll container, and the search field / footer are its
        // siblings — so a long row list pushes search off the top and the
        // multi footer off the bottom. Same idiom as command-palette.spec's
        // results list (overflow: auto; max-height: 360px). The HEADER
        // stays outside this wrapper, above it, so it never scrolls away
        // from the rows it labels. The outer table block's own `overflow:
        // hidden` (above) is doing border-radius clipping, not scrolling —
        // left alone.
        block {
          overflow: auto
          max-height: 360px

          // aria-pressed is a plain generic aria-* passthrough (same route,
          // same codegen, as aria-disabled two lines below), so it always
          // renders — `="false"` on a non-toggle row in single mode is not
          // omitted, matching the aria-disabled="false" this component
          // already ships on every enabled row (pinned by
          // modal-select.test.ts's "marks a disabled row aria-disabled"
          // test). `aria-pressed` is a supported ARIA 1.2 attribute on
          // role=button regardless of toggle state, so this is not an axe
          // violation.
          each visibleRows as row (row.value) {
            button {
              data-modal-select-row: row.value
              layout: horizontal, align: center
              width: 100%
              padding: "0"
              border: "none"
              background: "transparent"
              // A per-item conditional style expression referencing the
              // loop variable — compiles to a per-row dynamic assignment,
              // re-evaluated at each row's own instantiation, same as
              // `aria-disabled`/`tabindex` below and the cell text
              // `color:` below.
              cursor: row.disabled == true ? "default" : "pointer"
              // A disabled row takes no pointer input at all — belt-and-
              // braces alongside pickRow()'s own `if r.disabled == true {
              // return }` guard, which still governs keyboard/programmatic
              // activation, and alongside the conditional hover below. This
              // is no longer load-bearing for the hover highlight, which the
              // override now suppresses on its own; it stays because a
              // disabled control should not respond to a click or a drag
              // either.
              pointer-events: row.disabled == true ? "none" : "auto"
              border-bottom: borders.subtle
              aria-disabled: row.disabled == true
              aria-pressed: multi && (selected |> includes(row.value))
              tabindex: row.disabled == true ? "-1" : "0"
              on click: pickRow(row)
              // Conditional on the row, the same way `cursor:` above is. A
              // disabled row keeps its resting background on hover, so it
              // never offers the affordance of a row you can pick.
              //
              // This used to be unconditional and lean on `pointer-events:`
              // to suppress the highlight, because a loop variable in an
              // `on hover { … }` override collapsed to the same empty string
              // for every row — `resolveOverrideBinding` had no branch for
              // one. Fixed 2026-08-10; the override says what it means now,
              // and unlike hit-testing it is assertable in happy-dom.
              on hover {
                background: row.disabled == true ? "transparent" : semantic.surface-raised
              }

              // Selection indicator — sighted feedback for multi mode, to
              // match aria-pressed (which serves screen readers alone; the
              // hover highlight is identical whether a row is selected or
              // not, so without this a sighted user sees nothing change on
              // click). Reuses the exact predicate already on aria-pressed
              // above, proven reactive post-mount by the "toggles back
              // off" test. Sits before the per-column `each`, not inside
              // it, so it never multiplies per column or disturbs column
              // alignment — same idiom as checkbox.spec:62-65's check
              // glyph (a visibility-gated block holding the glyph, nested
              // inside an always-present container).
              block {
                width: 20px
                min-width: 20px
                layout: horizontal, align: center, justify: center
                block {
                  visibility: multi && (selected |> includes(row.value))
                  data-modal-select-check: row.value
                  // Decorative glyph in its OWN inner block, not on the
                  // visibility-gated block above: `visibility:` on the
                  // outer block already drives its own `aria-hidden`
                  // reactively (bindVisibility sets it whenever the block
                  // is hidden, clears it whenever shown — see
                  // runtime/bindings.ts), so a `aria-hidden: true` placed
                  // on that SAME element would be overwritten back to
                  // absent the moment the row becomes selected — exactly
                  // when the glyph is showing and needs to stay hidden
                  // from assistive tech. This inner block carries no
                  // `visibility:` of its own, so nothing ever touches its
                  // `aria-hidden` but this static value. `aria-pressed` on
                  // the row button already states selection, so the glyph
                  // joining the row's accessible name would be redundant,
                  // not additive — same generic aria-* passthrough as
                  // `aria-pressed`/`aria-disabled` above.
                  block {
                    aria-hidden: true
                    text("✓") {
                      style: type.body-md
                      color: semantic.interactive
                      weight: 600
                    }
                  }
                }
              }

              each columns as col {
                block {
                  padding: spacing.2
                  grow: true
                  min-width: 80px
                  @slot("cell", col, row)
                  text(toString(row[col.key])) {
                    style: type.body-md
                    // Same idiom as `cursor:` above — a plain style
                    // binding referencing the loop variable, not inside
                    // `on hover`, so it correctly lowers to a per-row
                    // `inline` binding.
                    color: row.disabled == true ? semantic.text-tertiary : semantic.text-primary
                    text-align: "start"
                  }
                }
              }
            }
          }
        }
      }

      // Loading — content-shaped skeletons, not a spinner.
      block {
        visibility: loading
        data-modal-select: "loading"
        layout: vertical, gap: spacing.2
        padding: spacing.3

        SkeletonLine(width: "60%", height: "12px")
        SkeletonLine(width: "45%", height: "12px")
        SkeletonLine(width: "70%", height: "12px")
        SkeletonLine(width: "40%", height: "12px")
      }

      // Empty — nothing to choose from at all. Distinct from "your search
      // matched nothing" (Task 4): different cause, different fix.
      block {
        visibility: isEmpty
        data-modal-select: "empty"
        padding: spacing.5
        layout: vertical, align: center

        EmptyState(message: emptyMessage)
      }

      // No match — distinct from `empty`. "There is nothing" and "your query
      // matched nothing" have different fixes, so they never share a string.
      block {
        visibility: noMatch
        data-modal-select: "no-match"
        padding: spacing.5
        layout: vertical, align: center

        EmptyState(message: noMatchText, description: "Try a shorter search, or clear it to see everything.")
      }

      // Multi-select footer — count + confirm/cancel. Last child of the
      // dialog block so it reads as the closing action bar, below whichever
      // of the four state blocks above is currently showing.
      block {
        visibility: multi
        data-modal-select: "footer"
        layout: horizontal, justify: between, align: center
        padding: spacing.3
        border-top: borders.default

        text(countText) { style: type.body-sm, color: semantic.text-secondary }

        block {
          layout: horizontal, gap: spacing.2, align: center

          Button(label: "Cancel", variant: "ghost", size: "sm") {
            on click: emit("close")
          }
          Button(label: confirmText, variant: "primary", size: "sm", disabled: !hasSelection) {
            on click: confirmSelection()
          }
        }
      }
    }
  }
}
