// ColumnChooser — show, hide, reorder and search a grid's columns.
//
// DataGridSpec embeds it behind `configurableColumns: true`, so a consumer
// gets the whole feature from one prop. It also stands alone, which is what
// lets a page put the trigger in a toolbar it already owns rather than accept
// a second button in the grid's own chrome.
//
// ── A group is a UNIT ───────────────────────────────────────────────────────
// A grouped run gets its OWN row — grip, up/down, eye — and drags, steps and
// hides as a block, exactly like a column. Its members sit indented beneath it
// and reorder within it. Group contiguity is therefore an invariant of the
// model rather than a wall: the only refusal left is dragging a single member
// out of its group.
//
// ── Every decision arrives precomputed ──────────────────────────────────────
// This file is markup. Which control is enabled, which row starts a run, what
// survives the search, whether an eye may be clicked — all of it is decided by
// `chooserRows` in column-chooser-math.ts, where it has a unit-test suite. A
// `.spec` cannot be unit-tested, so a rule written here would be a rule nobody
// can check.
//
// Props:
//   columns        — [{ key, label, group?, hideable?, movable? }]
//   hiddenColumns  — keys currently hidden. Caller-owned and persisted.
//   columnOrder    — key order. [] = the columns' declared order.
//   searchThreshold— the search box appears at >= this many columns
//   label          — the trigger button's label
//
// Emits: columnVisibilityChange(hiddenKeys), columnOrderChange(allKeys)
//        Both carry the FULL list, never a delta. `Reset` emits both with [],
//        which is already the documented "nothing saved" value for each.

@extern { genChooserId, chooserRows, moveKeyBy, moveGroupBy, groupKeys, wireChooserDrag } from "@spec/components/column-chooser-drag.js"

// One row of the panel. Renders from `row` alone — it makes no decisions, so
// there is nothing here that a test could disagree with.
component ColumnChooserRow(row: object) {
  @computed {
    isGroup: row.kind == 'group'
    // Indented members carry a left rail so a run reads as one thing before
    // anything is dragged, rather than only when a drag is refused.
    railColor: row.indent ? semantic.border-strong : 'transparent'
    nameColor: row.hidden ? semantic.text-tertiary : semantic.text-primary
    groupCount: toString(row.count) + ' cols'
  }

  block {
    layout: horizontal, align: center, gap: 6px
    padding-x: 6px padding-y: 5px
    border-radius: 6px
    margin-left: row.indent ? 10px : 0px
    border-left: '2px solid ' + railColor
    on hover { background: semantic.surface-hover }

    // Grip — the drag handle the wire attaches to. A locked column gets a lock
    // glyph instead: no grab cursor on something that will not move.
    block {
      visibility: !row.locked
      // NULL, not '' — a binding removes an attribute only when the value is
      // null; '' SETS it. Written that way every column's grip also matched
      // [data-colchooser-group-grip], so the wire's source selector picked up
      // both and only a falsy-string accident kept getSrcId returning the
      // right one.
      data-colchooser-grip: isGroup ? null : row.key
      data-colchooser-group-grip: isGroup ? row.key : null
      cursor: 'grab'
      width: 20px
      layout: horizontal, align: center, justify: center
      Icon(name: 'grip-vertical', size: 15, color: semantic.text-tertiary)
    }
    block {
      visibility: row.locked
      width: 20px
      layout: horizontal, align: center, justify: center
      Icon(name: 'lock', size: 13, color: semantic.text-tertiary)
    }

    // Name. A group's reads as a label; a column's as text.
    block {
      visibility: !isGroup
      grow: true
      text(row.label) { style: type.body-sm, color: nameColor }
    }
    block {
      visibility: isGroup
      grow: true
      text(row.label) {
        style: type.label-sm
        weight: 700
        color: semantic.text-secondary
        letter-spacing: '0.07em'
        text-transform: 'uppercase'
      }
    }

    // A group says how many columns travel with it; a locked column says why
    // it cannot move.
    block {
      visibility: isGroup
      text(groupCount) { style: type.caption, color: semantic.text-tertiary }
    }
    block {
      visibility: row.locked
      text('pinned') { style: type.caption, color: semantic.text-tertiary }
    }

    // Up / down. The keyboard path — a drag is unreachable without a pointer,
    // so these are not a convenience.
    button {
      visibility: !row.locked
      disabled: !row.canUp
      aria-label: 'Move ' + row.label + ' up'
      background: 'transparent'
      border: 'none'
      border-radius: 4px
      padding: 3px
      cursor: 'pointer'
      opacity: row.canUp ? 1.0 : 0.3
      layout: horizontal, align: center, justify: center
      on click: emit("move", 0 - 1)
      Icon(name: 'chevron-up', size: 15, color: semantic.text-secondary)
    }
    button {
      visibility: !row.locked
      disabled: !row.canDown
      aria-label: 'Move ' + row.label + ' down'
      background: 'transparent'
      border: 'none'
      border-radius: 4px
      padding: 3px
      cursor: 'pointer'
      opacity: row.canDown ? 1.0 : 0.3
      layout: horizontal, align: center, justify: center
      on click: emit("move", 1)
      Icon(name: 'chevron-down', size: 15, color: semantic.text-secondary)
    }

    // The eye. Disabled on the last visible column — a grid with no columns
    // has no header and no way back.
    button {
      visibility: !row.locked
      disabled: !row.canHide
      aria-label: (row.hidden ? 'Show ' : 'Hide ') + row.label
      background: 'transparent'
      border: 'none'
      border-radius: 4px
      padding: 3px
      cursor: 'pointer'
      opacity: row.canHide ? 1.0 : 0.3
      layout: horizontal, align: center, justify: center
      on click: emit("toggle")
      Icon(name: row.hidden ? 'eye-off' : 'eye', size: 15, color: semantic.text-secondary)
    }
  }
}

component ColumnChooser(
  columns: array,
  hiddenColumns: array = [],
  columnOrder: array = [],
  searchThreshold: number = 8,
  label: string = 'Columns',
) {
  @state {
    // Per-instance id, so two choosers on one page never share a drag session.
    // Generated once at mount — @state initialisers do not re-run.
    _id: genChooserId()
    _query: ''
    _order: columnOrder
    _hidden: hiddenColumns
    // Returns a teardown fn. Declared after _id (it reads it) and after the
    // actions it calls back into. EVERY argument arrives at the extern as a
    // SIGNAL, not a value — a @state initialiser's references compile that way
    // — so the wire resolves each per use.
    _dragTeardown: wireChooserDrag(_id, onDragReorder, colsOf, orderOf)
  }

  @watch {
    // A caller that persists and feeds the value back re-seeds here. Without
    // this the seed happens once at mount and never again, which is the
    // seed-once staleness class that shipped a sort indicator naming the wrong
    // column in cf.
    columnOrder: {
      _order = columnOrder
    }
    hiddenColumns: {
      _hidden = hiddenColumns
    }
  }

  @computed {
    // Declared before `rows`, which reads it.
    effectiveOrder: length(_order) > 0 ? _order : (columns |> map(c => c.key))
    rows: chooserRows(columns, effectiveOrder, _hidden, _query)
    // Vector's rule: a handful of columns is faster to scan than to search.
    showSearch: length(columns) >= searchThreshold
    anyHidden: length(_hidden) > 0
    hiddenCount: toString(length(_hidden))
    noMatches: length(rows) == 0
    bulkLabel: anyHidden ? 'Show all' : 'Hide all'
    emptyLine: 'No columns match “' + _query + '”'
  }

  @actions {
    // Read back by the drag wire, which needs both to decide whether a drop is
    // legal. Passed as function references, resolved per use.
    colsOf() { return columns }
    orderOf() { return effectiveOrder }

    setQuery(v) { _query = v }

    // Local state first, then the emit. Making the panel wait for a round-trip
    // to agree with a gesture the user already completed is how a control comes
    // to feel like it snapped back.
    emitOrder(next) {
      _order = next
      emit("columnOrderChange", next)
    }
    emitHidden(next) {
      _hidden = next
      emit("columnVisibilityChange", next)
    }
    onDragReorder(next) { emitOrder(next) }

    moveRow(row, dir) {
      let next = row.kind == 'group'
        ? moveGroupBy(effectiveOrder, columns, row.key, dir)
        : moveKeyBy(effectiveOrder, columns, row.key, dir)
      if next != null { emitOrder(next) }
    }

    // A group's eye moves every member at once — parity with the single
    // control cf-market's own chooser already gives the Quality set.
    toggleRow(row) {
      let keys = row.kind == 'group' ? groupKeys(effectiveOrder, columns, row.key) : [row.key]
      let next = row.hidden
        ? (_hidden |> filter(k => !(keys |> includes(k))))
        : (_hidden |> concat(keys |> filter(k => !(_hidden |> includes(k)))))
      emitHidden(next)
    }

    // Reset is expressible in the contract that already exists: [] means "the
    // declared order" and "nothing hidden". No third event.
    resetAll() {
      emitOrder([])
      emitHidden([])
    }
    bulkToggle() {
      if anyHidden {
        emitHidden([])
      } else {
        emitHidden(columns |> filter(c => c.hideable != false) |> map(c => c.key))
      }
    }
  }

  block {
    inline: true

    Popover(placement: "bottom") {
      slot("trigger") {
        // The block exists for `data-colchooser-trigger`: a stable hook for
        // tests and automation, scoped to this instance. Matching the button by
        // its label instead breaks the moment a consumer renames it.
        block {
          data-colchooser-trigger: _id
          Button(label: label, iconLeft: 'columns-3', variant: 'secondary', size: 'sm')
        }
      }
      slot("content") {
        // The panel. `data-colchooser-id` scopes every query the drag wire
        // makes to THIS instance.
        block {
          data-colchooser-id: _id
          layout: vertical
          width: 268px

          // Search. Present only above the threshold; below it the list is
          // shorter than the query would be.
          block {
            visibility: showSearch
            data-colchooser-search: _id
            layout: horizontal, align: center, gap: 6px
            padding-x: 4px padding-y: 6px
            border-bottom: '1px solid ' + semantic.border
            Icon(name: 'search', size: 14, color: semantic.text-tertiary)
            textInput(_query) {
              border: 'none'
              background: 'transparent'
              width: 100%
              placeholder: 'Search columns…'
              aria-label: 'Search columns'
              on input(ev): setQuery(ev.target.value)
            }
          }

          // The list. `data-colchooser-list` is what the wire polls for — the
          // panel is mounted by the Popover only while it is open, so the wire
          // cannot find it at mount and watches for it instead.
          block {
            data-colchooser-list: _id
            overflow: 'auto'
            max-height: 320px
            padding-y: 4px

            each rows as r (r.id) {
              block {
                // NULL, not '' — a binding removes an attribute only when the
                // value is null (ai-reference §31b). An empty string SETS it,
                // so every group row would also match [data-colchooser-key]
                // and the wire would treat it as a column.
                data-colchooser-key: r.kind == 'col' ? r.key : null
                data-colchooser-group: r.kind == 'group' ? r.key : null
                ColumnChooserRow(row: r) {
                  on move(d): moveRow(r, d)
                  on toggle: toggleRow(r)
                }
              }
            }

            // An empty panel reads as broken; this says which query emptied it.
            block {
              visibility: noMatches
              padding-x: 10px padding-y: 14px
              text(emptyLine) {
                style: type.body-sm
                color: semantic.text-tertiary
                text-align: 'center'
              }
            }
          }

          block {
            border-top: '1px solid ' + semantic.border
            padding-x: 6px padding-y: 6px
            layout: horizontal, align: center
            Button(label: 'Reset', iconLeft: 'rotate-ccw', variant: 'ghost', size: 'sm') {
              on click: resetAll()
            }
            block { grow: true }
            Button(label: bulkLabel, variant: 'ghost', size: 'sm') {
              on click: bulkToggle()
            }
          }
        }
      }
    }
  }
}
