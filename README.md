# Spec Registry

The official curated package registry for the [Spec language](https://github.com/bwoody77/spec).

## Philosophy

Every package in this registry works with every other package. One date picker. One data grid. One theme system. If it's here, it's maintained, tested, and compatible with the current compiler.

We don't have 2 million packages. We have the right ones.

## Categories

| Category | Description | Count |
|----------|-------------|-------|
| **components** | Core UI building blocks | 55 |
| **themes** | Visual theme presets | 30 |
| **icons** | Icon set wrappers | 2 |
| **layouts** | Page-level layout patterns | _coming soon_ |
| **fonts** | Bundled fonts with type scale tokens | 14 |
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
spec add button          # adds button + writes ^X.Y.Z range to spec.packages.json
spec install             # installs everything listed; resolves ranges, writes spec.lock.json
spec install --frozen    # validates lockfile is in sync with manifest (CI-friendly)
```

`spec.packages.json` accepts caret (`^0.2.0`), tilde (`~0.2.0`), and exact (`0.2.0`) ranges. `spec.lock.json` records the exact installed version for each entry — commit both files.

## Fonts

Font packages bundle woff2 files and declare them via `@fonts` blocks. The compiler emits `FontFace` API calls (pure JS, zero CSS). Fonts are registered lazily — the browser only downloads a font when an element actually uses it.

```spec
// Import a font package to register its font faces
@import "@spec/font-inter"

// Assign the font in your visual system
@visual-system {
  font.body: "'Inter', -apple-system, sans-serif"
}
```

Available font packages: `inter`, `jetbrains-mono`, `dm-sans`, `playfair`, `geist`, `fira-code`, `roboto`, `nunito`, `rajdhani`, `orbitron`, `noto-sans`, `source-sans`, `merriweather-sans`, `source-code-pro`.

Themes that use web fonts already import the corresponding font package — no manual font setup needed when using a theme.

## How packages get here

This is the published registry. **Authoring happens in the spec monorepo, not here.** Direct edits to files in this repo will be reverted — they'd put the registry out of sync with the spec source.

The actual workflow:

1. Edit a component's `.spec` source in `spec/packages/components/spec/<name>.spec` (and the co-located `<name>.toml` if you need to manage metadata).
2. From the spec monorepo root, run:
   ```bash
   spec publish <name> --bump patch|minor|major
   ```
3. `spec publish` copies the source `.spec` + `.toml` into this registry's `components/<name>/` directory, bumps the version per `--bump`, and creates a `feat(<name>): publish X.Y.Z` (or `fix(...)` for patch) commit here.
4. Consumers (Vector, etc.) pick up the new version via `spec install`.

Use `spec publish --all --bump <level>` to publish every component that has drifted, or `--dry-run` to preview without writing.

A pre-commit hook in the spec monorepo refuses commits where a staged `.spec` file differs from the registry copy. The intended workflow is: edit → `spec publish` → commit. Bypass with `git commit --no-verify` for WIP.

## Contributing components

To propose a new component, open a PR against the **spec monorepo** (`bwoody77/spec`) adding it under `packages/components/spec/`. The CI/maintainer flow will then `spec publish` it into this registry as a single curated release.

We intentionally keep one package per purpose. If a better date picker exists, it replaces the current one — it doesn't sit alongside it.

## License

MIT
