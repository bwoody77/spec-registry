component Slider(min: number = 0, max: number = 100, step: number = 1, value: number = 50, label: string = "", disabled: boolean = false) {
  @state {
    currentValue: 50
  }

  @computed {
    displayValue: currentValue
  }

  @actions {
    updateValue(v) {
      currentValue = v
      emit("change", v)
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

    // Slider track
    slider(currentValue) {
      min: min
      max: max
      step: step
      disabled: disabled
      on change(v): updateValue(v)
    }
  }
}
