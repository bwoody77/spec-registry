#!/usr/bin/env bash
# download-fonts.sh — Fetch woff2 font files for all font packages
#
# Sources:
#   Inter, DM Sans, Playfair Display, JetBrains Mono, Fira Code,
#   Roboto, Nunito, Rajdhani, Orbitron, Noto Sans, Source Sans 3,
#   Merriweather Sans, Source Code Pro — Google Fonts
#   Geist, Geist Mono — Vercel (github.com/vercel/geist-font)
#
# Usage:
#   cd spec-registry/fonts && bash download-fonts.sh
#
# Requires: curl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

download() {
  local url="$1" dest="$2"
  if [[ -f "$dest" ]]; then
    echo "  skip  $(basename "$dest") (exists)"
    return
  fi
  echo "  fetch $(basename "$dest")"
  curl -sL -o "$dest" "$url"
}

# Google Fonts serves woff2 when the user-agent indicates support.
# We use the CSS2 API to extract direct woff2 URLs.
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

fetch_google_font() {
  local family="$1" dest_dir="$2" prefix="$3"
  shift 3
  local weights=("$@")

  echo ""
  echo "=== $family ==="

  # Request CSS from Google Fonts API with woff2 user-agent
  local css
  css=$(curl -sL -H "User-Agent: $UA" \
    "https://fonts.googleapis.com/css2?family=${family// /+}:wght@$(IFS=\;; echo "${weights[*]}")&display=swap")

  for w in "${weights[@]}"; do
    local url
    url=$(echo "$css" | grep -A5 "font-weight: $w;" | grep -oP 'url\(\K[^)]+' | head -1)
    if [[ -z "$url" ]]; then
      echo "  WARN  no woff2 URL for weight $w"
      continue
    fi

    local weight_name
    case $w in
      400) weight_name="regular" ;;
      500) weight_name="medium" ;;
      600) weight_name="semibold" ;;
      700) weight_name="bold" ;;
      *) weight_name="w${w}" ;;
    esac

    download "$url" "$dest_dir/${prefix}-${weight_name}.woff2"
  done
}

# --- Inter ---
fetch_google_font "Inter" "$SCRIPT_DIR/inter/woff2" "inter" 400 500 600 700

# --- JetBrains Mono ---
fetch_google_font "JetBrains Mono" "$SCRIPT_DIR/jetbrains-mono/woff2" "jetbrains-mono" 400 500 700

# --- DM Sans ---
fetch_google_font "DM Sans" "$SCRIPT_DIR/dm-sans/woff2" "dm-sans" 400 500 600 700

# --- Playfair Display ---
fetch_google_font "Playfair Display" "$SCRIPT_DIR/playfair/woff2" "playfair-display" 400 500 600 700

# Playfair Display Italic
echo ""
echo "=== Playfair Display (italic) ==="
ITALIC_CSS=$(curl -sL -H "User-Agent: $UA" \
  "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,400&display=swap")
ITALIC_URL=$(echo "$ITALIC_CSS" | grep -oP 'url\(\K[^)]+' | head -1)
if [[ -n "$ITALIC_URL" ]]; then
  download "$ITALIC_URL" "$SCRIPT_DIR/playfair/woff2/playfair-display-italic.woff2"
fi

# --- Fira Code ---
fetch_google_font "Fira Code" "$SCRIPT_DIR/fira-code/woff2" "fira-code" 400 500 600 700

# --- Roboto ---
fetch_google_font "Roboto" "$SCRIPT_DIR/roboto/woff2" "roboto" 400 500 700

# --- Nunito ---
fetch_google_font "Nunito" "$SCRIPT_DIR/nunito/woff2" "nunito" 400 500 600 700

# --- Rajdhani ---
fetch_google_font "Rajdhani" "$SCRIPT_DIR/rajdhani/woff2" "rajdhani" 400 500 600 700

# --- Orbitron ---
fetch_google_font "Orbitron" "$SCRIPT_DIR/orbitron/woff2" "orbitron" 400 500 600 700

# --- Noto Sans ---
fetch_google_font "Noto Sans" "$SCRIPT_DIR/noto-sans/woff2" "noto-sans" 400 500 600 700

# --- Source Sans 3 ---
fetch_google_font "Source Sans 3" "$SCRIPT_DIR/source-sans/woff2" "source-sans-3" 400 600 700

# --- Merriweather Sans ---
fetch_google_font "Merriweather Sans" "$SCRIPT_DIR/merriweather-sans/woff2" "merriweather-sans" 400 500 700

# --- Source Code Pro ---
fetch_google_font "Source Code Pro" "$SCRIPT_DIR/source-code-pro/woff2" "source-code-pro" 400 500 700

# --- Geist (from Vercel GitHub releases) ---
echo ""
echo "=== Geist Sans ==="
GEIST_BASE="https://raw.githubusercontent.com/vercel/geist-font/main/packages/next/dist/fonts/geist-sans"
for pair in "400:regular" "500:medium" "600:semibold" "700:bold"; do
  w="${pair%%:*}" name="${pair##*:}"
  download "${GEIST_BASE}/Geist-${name^}.woff2" "$SCRIPT_DIR/geist/woff2/geist-${name}.woff2" 2>/dev/null || \
  download "${GEIST_BASE}/geist-${name}.woff2" "$SCRIPT_DIR/geist/woff2/geist-${name}.woff2" 2>/dev/null || \
  echo "  WARN  Geist Sans ${name} — check URL manually"
done

echo ""
echo "=== Geist Mono ==="
GEIST_MONO_BASE="https://raw.githubusercontent.com/vercel/geist-font/main/packages/next/dist/fonts/geist-mono"
for pair in "400:regular" "500:medium" "700:bold"; do
  w="${pair%%:*}" name="${pair##*:}"
  download "${GEIST_MONO_BASE}/GeistMono-${name^}.woff2" "$SCRIPT_DIR/geist/woff2/geist-mono-${name}.woff2" 2>/dev/null || \
  download "${GEIST_MONO_BASE}/geist-mono-${name}.woff2" "$SCRIPT_DIR/geist/woff2/geist-mono-${name}.woff2" 2>/dev/null || \
  echo "  WARN  Geist Mono ${name} — check URL manually"
done

echo ""
echo "Done. Verify woff2 files:"
find "$SCRIPT_DIR" -name "*.woff2" -exec ls -lh {} \;
