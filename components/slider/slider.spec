component Slider(min: number = 0, max: number = 100, step: number = 1, value: number = 50, label: string = "", disabled: boolean = false) {
  @state {
    currentValue: 50
  }

  // Controlled: track the `value` prop (seed on mount via `!`, follow external
  // updates). Before this watch the prop was IGNORED — currentValue was born
  // 50 and only ever moved by dragging, so a host that set or later changed
  // `value` saw a thumb stuck wherever it was (found by Vector's W&B fuel
  // slider, 2026-08-28). Same idiom as CheckboxGroup's `values!:` watch.
  @watch {
    value!: { currentValue = value }
  }

  @computed {
    displayValue: currentValue
  }

  @actions {
    updateValue(v) {
      // Coerce: the DOM range input reports strings.
      currentValue = v * 1
      emit("change", v * 1)
    }
  }

  block {
    layout: vertical, gap: spacing.2

    // Label + value display
    block {
      visibility: label != ""
      layout: horizontal, justify: between, align: center
      text(label) { style: type.label-sm, color: semantic.text-secondary }
      text("{displayValue}") { style: type.label-sm, color: semantic.text-primary }
    }

    // Value display when no label
    block {
      visibility: label == ""
      layout: horizontal, justify: end
      text("{displayValue}") { style: type.label-sm, color: semantic.text-primary }
    }

    // Slider track. `on input(event)` with an explicit `event.target.value`
    // read — a bare `on change(v)` hands the DOM EVENT, not the value (the
    // avatar-picker zoom bug, 2026-08-25; see ai-reference "Two-Way Binding").
    slider(currentValue) {
      min: min
      max: max
      step: step
      disabled: disabled
      on input(event): updateValue(event.target.value)
    }
  }
}
