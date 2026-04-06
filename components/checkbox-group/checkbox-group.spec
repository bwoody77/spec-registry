// CheckboxGroup — multi-select group using individual Checkbox components
component CheckboxGroup(legend: string, options: array, values: array = [], disabled: boolean = false) {
  @state {
    selected: values
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
