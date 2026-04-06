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
            background: match true {
              i < activeStep -> "#22c55e",
              i == activeStep -> semantic.interactive,
              _ -> semantic.surface-raised
            }
            border: match true {
              i <= activeStep -> "2px solid transparent",
              _ -> borders.default
            }

            text(match true {
              i < activeStep -> "\u2713",
              _ -> "{i + 1}"
            }) {
              style: type.label-sm
              color: match true {
                i <= activeStep -> "#ffffff",
                _ -> semantic.text-secondary
              }
            }
          }

          // Label
          text(step.label) {
            style: type.label-sm
            color: match true {
              i == activeStep -> semantic.text-primary,
              i < activeStep -> "#22c55e",
              _ -> semantic.text-tertiary
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
          background: i < activeStep ? "#22c55e" : semantic.border
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
            background: match true {
              i < activeStep -> "#22c55e",
              i == activeStep -> semantic.interactive,
              _ -> semantic.surface-raised
            }
            border: match true {
              i <= activeStep -> "2px solid transparent",
              _ -> borders.default
            }
            on click: { if allowBack && i < activeStep { emit("change", i) } }

            text(match true {
              i < activeStep -> "\u2713",
              _ -> "{i + 1}"
            }) {
              style: type.label-sm
              color: match true {
                i <= activeStep -> "#ffffff",
                _ -> semantic.text-secondary
              }
            }
          }

          // Vertical connector
          block {
            visibility: i < stepCount - 1
            width: 2px
            grow: true
            min-height: 24px
            background: i < activeStep ? "#22c55e" : semantic.border
          }
        }

        // Label + description
        block {
          layout: vertical, gap: spacing.1
          padding: spacing.2

          text(step.label) {
            style: type.body-md
            color: match true {
              i == activeStep -> semantic.text-primary,
              i < activeStep -> "#22c55e",
              _ -> semantic.text-tertiary
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
