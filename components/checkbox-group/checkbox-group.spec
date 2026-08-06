// CheckboxGroup — multi-select group using individual Checkbox components
component CheckboxGroup(legend: string, options: array, values: array = [], disabled: boolean = false) {
  @state {
    selected: values
  }

  // A plain @state initializer only SNAPSHOTS the prop at construction. A host
  // that mounts this group before its data has arrived — or, in Spec, mounts it
  // hidden, since `visibility:` compiles to display:none rather than DOM
  // removal — and supplies `values` afterwards got a group that rendered every
  // box unchecked. Worse, the first toggle then built its emit off that stale
  // `[]`, so ticking one box silently discarded every previously-saved value.
  //
  // `values!` (immediate watch) seeds at construction AND re-fires on each prop
  // update, which is the documented fix for this "data already present at
  // mount" gap. See ai-reference.md, "Immediate watches (`name!:`)".
  @watch {
    values!: { selected = values }
  }

  @actions {
    toggle(val) {
      selected = selected.includes(val) ? selected.filter(v => v != val) : selected.concat([val])
      emit("change", selected)
    }
  }

  block {
    layout: vertical, gap: spacing.2

    text(legend) {
      style: type.label-md
      font-weight: 600
      color: semantic.text-primary
    }

    each options as opt {
      Checkbox(label: opt.label, checked: selected.includes(opt.value), disabled: disabled == true ? true : opt.disabled == true) {
        on change: toggle(opt.value)
      }
    }
  }
}
