# Spec Registry

The official curated package registry for the [Spec language](https://github.com/bwoody77/spec).

## Philosophy

Every package in this registry works with every other package. One date picker. One data grid. One theme system. If it's here, it's maintained, tested, and compatible with the current compiler.

We don't have 2 million packages. We have the right ones.

## Categories

| Category | Description | Count |
|----------|-------------|-------|
| **components** | Core UI building blocks | 51 |
| **themes** | Visual theme presets | 30 |
| **icons** | Icon set wrappers | 2 |
| **layouts** | Page-level layout patterns | _coming soon_ |
| **fonts** | Bundled fonts with type scale tokens | _coming soon_ |
| **animations** | Animation and transition presets | _coming soon_ |
| **validators** | Input validation rules | _coming soon_ |
| **connectors** | Data source bindings | _coming soon_ |
| **i18n** | Internationalization bundles | _coming soon_ |
| **a11y** | Accessibility presets | _coming soon_ |
| **charts** | Data visualization types | _coming soon_ |
| **starters** | App scaffold templates | _coming soon_ |
| **integrations** | Third-party service wrappers | _coming soon_ |
| **dev-tools** | Debugging and inspection tools | _coming soon_ |

## Usage

```bash
spec add button          # there's only one — the good one
spec add theme-nord      # curated theme
spec browse components   # see everything
```

## Contributing

Packages are added via pull request. Before submitting:

1. Check that no existing package serves the same purpose
2. Include a `spec.toml` manifest
3. Include the `.spec` source file(s)
4. Ensure compatibility with the current Spec compiler

We intentionally keep one package per purpose. If a better date picker exists, it replaces the current one — it doesn't sit alongside it.

## License

MIT
