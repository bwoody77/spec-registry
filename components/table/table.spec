component Table(columns: array, rows: array, striped: boolean = false) {
  block {
    overflow: "auto"
    border: borders.default
    border-radius: 8px

    // Header
    block {
      layout: horizontal
      background: semantic.surface-raised
      border-bottom: borders.default

      each columns as col {
        block {
          padding: spacing.3
          grow: true
          min-width: 120px
          text(col.header) {
            style: type.label-sm
            weight: 600
            color: semantic.text-secondary
            text-transform: "uppercase"
            letter-spacing: "0.05em"
          }
        }
      }
    }

    // Body rows
    each rows as row, rowIndex {
      block {
        layout: horizontal
        border-bottom: borders.default
        background: match striped {
          true -> match rowIndex % 2 {
            0 -> "transparent",
            _ -> semantic.surface-raised
          },
          _ -> "transparent"
        }
        on hover { background: semantic.surface-raised }

        each columns as col {
          block {
            padding: spacing.3
            grow: true
            min-width: 120px
            @slot("cell", col, row)
            text(row[col.key]) {
              style: type.body-md
              color: semantic.text-primary
            }
          }
        }
      }
    }
  }
}
