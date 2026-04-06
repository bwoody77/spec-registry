component TimePicker(value: string = "12:00", format: string = "24", minuteStep: number = 1, label: string = "", disabled: boolean = false) {
  @state {
    hours: 12
    minutes: 0
    ampm: "AM"
  }

  @computed {
    displayHours: format == "12" ? (hours == 0 ? 12 : (hours > 12 ? hours - 12 : hours)) : hours
    formattedH: displayHours < 10 ? "0{displayHours}" : "{displayHours}"
    formattedM: minutes < 10 ? "0{minutes}" : "{minutes}"
    timeString: format == "12" ? "{formattedH}:{formattedM} {ampm}" : "{formattedH}:{formattedM}"
  }

  @actions {
    incHour() {
      hours = format == "24" ? ((hours + 1) % 24) : ((hours + 1) % 12)
      emit("change", timeString)
    }
    decHour() {
      hours = format == "24" ? ((hours + 23) % 24) : ((hours + 11) % 12)
      emit("change", timeString)
    }
    incMinute() {
      minutes = (minutes + minuteStep) % 60
      emit("change", timeString)
    }
    decMinute() {
      minutes = (minutes - minuteStep + 60) % 60
      emit("change", timeString)
    }
    toggleAmPm() {
      ampm = ampm == "AM" ? "PM" : "AM"
      emit("change", timeString)
    }
  }

  block {
    layout: vertical, gap: spacing.2
    role: "group"
    aria-label: "Time picker"

    // Label
    block {
      visibility: label != ""
      text(label) { style: type.label-sm, color: semantic.text-secondary }
    }

    block {
      layout: horizontal, gap: spacing.2, align: center

      // Hours column
      block {
        layout: vertical, align: center, gap: spacing.1
        text("Hr") { style: type.caption, color: semantic.text-tertiary }
        block {
          layout: horizontal, gap: spacing.1, align: center
          block {
            padding: spacing.1
            border-radius: radius.sm
            cursor: disabled ? "default" : "pointer"
            opacity: disabled ? 0.4 : 1
            on hover { background: disabled ? "transparent" : semantic.surface-raised }
            on click: { if disabled == false { decHour() } }
            text("\u25BC") { style: type.caption, color: semantic.text-secondary }
          }
          block {
            padding: spacing.2
            min-width: 40px
            background: semantic.surface-raised
            border: borders.default
            border-radius: radius.md
            layout: horizontal, align: center, justify: center
            text(formattedH) { style: type.body-md, color: semantic.text-primary }
          }
          block {
            padding: spacing.1
            border-radius: radius.sm
            cursor: disabled ? "default" : "pointer"
            opacity: disabled ? 0.4 : 1
            on hover { background: disabled ? "transparent" : semantic.surface-raised }
            on click: { if disabled == false { incHour() } }
            text("\u25B2") { style: type.caption, color: semantic.text-secondary }
          }
        }
      }

      text(":") { style: type.heading-sm, color: semantic.text-primary }

      // Minutes column
      block {
        layout: vertical, align: center, gap: spacing.1
        text("Min") { style: type.caption, color: semantic.text-tertiary }
        block {
          layout: horizontal, gap: spacing.1, align: center
          block {
            padding: spacing.1
            border-radius: radius.sm
            cursor: disabled ? "default" : "pointer"
            opacity: disabled ? 0.4 : 1
            on hover { background: disabled ? "transparent" : semantic.surface-raised }
            on click: { if disabled == false { decMinute() } }
            text("\u25BC") { style: type.caption, color: semantic.text-secondary }
          }
          block {
            padding: spacing.2
            min-width: 40px
            background: semantic.surface-raised
            border: borders.default
            border-radius: radius.md
            layout: horizontal, align: center, justify: center
            text(formattedM) { style: type.body-md, color: semantic.text-primary }
          }
          block {
            padding: spacing.1
            border-radius: radius.sm
            cursor: disabled ? "default" : "pointer"
            opacity: disabled ? 0.4 : 1
            on hover { background: disabled ? "transparent" : semantic.surface-raised }
            on click: { if disabled == false { incMinute() } }
            text("\u25B2") { style: type.caption, color: semantic.text-secondary }
          }
        }
      }

      // AM/PM toggle column
      block {
        visibility: format == "12"
        layout: vertical, align: center, gap: spacing.1

        // Spacer label to align with Hr/Min labels
        text(" ") { style: type.caption, color: "transparent" }

        block {
          padding: spacing.2
          min-width: 48px
          min-height: 36px
          background: semantic.surface-raised
          border: borders.default
          border-radius: radius.md
          cursor: disabled ? "default" : "pointer"
          opacity: disabled ? 0.4 : 1
          layout: horizontal, align: center, justify: center
          on hover { background: disabled ? semantic.surface-raised : semantic.interactive }
          on click: { if disabled == false { toggleAmPm() } }
          text(ampm) { style: type.label-sm, color: semantic.text-primary }
        }
      }
    }
  }
}
