// SegmentedControl — a small set of mutually exclusive choices, shown all at
// once, where a Select would hide all but one.
//
// Promoted from Vector, which had the ITEM (`ViewToggleButton`) as a component
// and hand-rolled the GROUP — the padded, bordered, rounded track — at every
// call site: schedule's Day/Week/Month, schedule's Normal/Compact, squawks'
// Board/Matrix, fleet's Table/Timeline. Four copies of the same eight lines,
// already drifting in radius and min-width. The group is the part worth owning.
//
// WHEN TO USE THIS RATHER THAN A SELECT: two to five options, all worth seeing,
// where the choice reframes what is on screen rather than filling in a value. A
// Select is right when the list is long, or when the options are data. This is
// right when they are VIEWS.
//
// AND RATHER THAN A TOGGLE: a Toggle is on/off, and it only reads clearly when
// its label states the ON condition. Two NAMED alternatives — "Hide" versus
// "Ghost", "Board" versus "Matrix" — are not on/off, and forcing them into a
// switch makes the reader work out which end is which every time.
//
// ACCESSIBILITY, which is the part Vector's version deferred. Its own comment
// said "active state is visual only (no aria-pressed yet; add when we have a
// use case that needs it)" — so a screen-reader user heard four buttons and
// could not tell which was in effect. Here the track is a `role="group"` with
// an accessible name and each item carries `aria-pressed`, so the state is
// announced rather than merely coloured.
//
// Hover uses opacity rather than `on hover { background: … }`: setting a
// shorthand inside a hover block clobbers the longhand beneath it, which is the
// white-on-white bug chip.spec documents.

component SegmentedControl(
  options: array = [],
  value: string = "",
  ariaLabel: string = "",
  disabled: boolean = false,
  size: string = "md"
) {
  @computed {
    padY: size == "sm" ? 4 : 6
    padX: size == "sm" ? 10 : 14
  }

  block {
    role: "group"
    aria-label: ariaLabel
    padding: 4px
    border-radius: 8px
    background: semantic.surface-hover
    border: borders.default
    layout: horizontal, gap: 0px

    each options as opt (opt.value) {
      SegmentedControlItem(
        label: opt.label,
        active: opt.value == value,
        disabled: disabled,
        padY: padY,
        padX: padX
      ) {
        on click: emit("change", opt.value)
      }
    }
  }
}

// One segment. A real <button>, so the group is reachable and operable from the
// keyboard — a clickable div would put the whole control out of reach.
component SegmentedControlItem(
  label: string,
  active: boolean = false,
  disabled: boolean = false,
  padY: number = 6,
  padX: number = 14
) {
  // Every active-conditional style is hoisted into @computed rather than
  // written as an inline ternary on a prop — inline ternaries on props do not
  // re-evaluate reliably, which Vector's original notes as bug #0d.
  @computed {
    bg:          active ? semantic.surface : 'transparent'
    fg:          active ? semantic.text-primary : semantic.text-tertiary
    labelWeight: active ? 600 : 500
    chipShadow:  active ? '0 1px 2px rgba(14,22,38,0.06), 0 0 0 1px rgba(14,22,38,0.06)' : 'none'
    itemCursor:  disabled ? 'default' : 'pointer'
    itemOpacity: disabled ? 0.5 : 1
  }

  button {
    disabled: disabled
    padding-y: padY
    padding-x: padX
    border-radius: 6px
    background: bg
    shadow: chipShadow
    border: 'none'
    // The half Vector's version deferred: the pressed state is announced, not
    // only coloured.
    aria-pressed: active
    aria-disabled: disabled
    cursor: itemCursor
    opacity: itemOpacity
    layout: horizontal, align: center, justify: center
    on click(event): emit("click", event)
    on hover { opacity: 0.8 }

    text(label) {
      color: fg
      weight: labelWeight
      style: type.body-sm
      white-space: 'nowrap'
    }
  }
}
