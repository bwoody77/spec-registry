#!/usr/bin/env node
/**
 * download-fonts.mjs — Fetch woff2 font files for all font packages.
 * Node.js version (cross-platform, no grep -P dependency).
 *
 * Usage: node download-fonts.mjs
 */

import { writeFile, mkdir, stat } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36";

async function fileExists(path) {
  try { await stat(path); return true; } catch { return false; }
}

async function download(url, dest) {
  if (await fileExists(dest)) {
    console.log(`  skip  ${dest.split('/').pop()} (exists)`);
    return true;
  }
  console.log(`  fetch ${dest.split('/').pop()}`);
  try {
    const res = await fetch(url, { headers: { 'User-Agent': UA } });
    if (!res.ok) { console.log(`  WARN  HTTP ${res.status}`); return false; }
    const buf = Buffer.from(await res.arrayBuffer());
    await writeFile(dest, buf);
    return true;
  } catch (e) {
    console.log(`  WARN  ${e.message}`);
    return false;
  }
}

async function fetchGoogleFont(family, destDir, prefix, weights) {
  console.log(`\n=== ${family} ===`);
  await mkdir(destDir, { recursive: true });

  const weightStr = weights.join(';');
  const cssUrl = `https://fonts.googleapis.com/css2?family=${family.replace(/ /g, '+')}:wght@${weightStr}&display=swap`;
  const res = await fetch(cssUrl, { headers: { 'User-Agent': UA } });
  const css = await res.text();

  for (const w of weights) {
    // Find the @font-face block for this weight and extract the url
    const regex = new RegExp(`font-weight:\\s*${w};[\\s\\S]*?src:\\s*url\\(([^)]+)\\)`, 'g');
    let match = null;
    // Find last match (Google Fonts puts latin last)
    let m;
    while ((m = regex.exec(css)) !== null) { match = m; }

    if (!match) {
      console.log(`  WARN  no woff2 URL for weight ${w}`);
      continue;
    }

    const url = match[1];
    const weightName = { 400: 'regular', 500: 'medium', 600: 'semibold', 700: 'bold' }[w] || `w${w}`;
    await download(url, join(destDir, `${prefix}-${weightName}.woff2`));
  }
}

// All Google Fonts packages
const fonts = [
  { family: 'Inter', dir: 'inter', prefix: 'inter', weights: [400, 500, 600, 700] },
  { family: 'JetBrains Mono', dir: 'jetbrains-mono', prefix: 'jetbrains-mono', weights: [400, 500, 700] },
  { family: 'DM Sans', dir: 'dm-sans', prefix: 'dm-sans', weights: [400, 500, 600, 700] },
  { family: 'Playfair Display', dir: 'playfair', prefix: 'playfair-display', weights: [400, 500, 600, 700] },
  { family: 'Fira Code', dir: 'fira-code', prefix: 'fira-code', weights: [400, 500, 600, 700] },
  { family: 'Roboto', dir: 'roboto', prefix: 'roboto', weights: [400, 500, 700] },
  { family: 'Nunito', dir: 'nunito', prefix: 'nunito', weights: [400, 500, 600, 700] },
  { family: 'Rajdhani', dir: 'rajdhani', prefix: 'rajdhani', weights: [400, 500, 600, 700] },
  { family: 'Orbitron', dir: 'orbitron', prefix: 'orbitron', weights: [400, 500, 600, 700] },
  { family: 'Noto Sans', dir: 'noto-sans', prefix: 'noto-sans', weights: [400, 500, 600, 700] },
  { family: 'Source Sans 3', dir: 'source-sans', prefix: 'source-sans-3', weights: [400, 600, 700] },
  { family: 'Merriweather Sans', dir: 'merriweather-sans', prefix: 'merriweather-sans', weights: [400, 500, 700] },
  { family: 'Source Code Pro', dir: 'source-code-pro', prefix: 'source-code-pro', weights: [400, 500, 700] },
];

for (const f of fonts) {
  await fetchGoogleFont(f.family, join(__dirname, f.dir, 'woff2'), f.prefix, f.weights);
}

// Geist (from Vercel GitHub)
console.log('\n=== Geist Sans ===');
const geistDir = join(__dirname, 'geist', 'woff2');
await mkdir(geistDir, { recursive: true });
const geistBase = 'https://raw.githubusercontent.com/vercel/geist-font/main/packages/next/dist/fonts/geist-sans';
for (const [w, name] of [[400,'regular'],[500,'medium'],[600,'semibold'],[700,'bold']]) {
  const ok = await download(`${geistBase}/Geist-${name.charAt(0).toUpperCase()+name.slice(1)}.woff2`, join(geistDir, `geist-${name}.woff2`));
  if (!ok) await download(`${geistBase}/geist-${name}.woff2`, join(geistDir, `geist-${name}.woff2`));
}

console.log('\n=== Geist Mono ===');
const geistMonoBase = 'https://raw.githubusercontent.com/vercel/geist-font/main/packages/next/dist/fonts/geist-mono';
for (const [w, name] of [[400,'regular'],[500,'medium'],[700,'bold']]) {
  const ok = await download(`${geistMonoBase}/GeistMono-${name.charAt(0).toUpperCase()+name.slice(1)}.woff2`, join(geistDir, `geist-mono-${name}.woff2`));
  if (!ok) await download(`${geistMonoBase}/geist-mono-${name}.woff2`, join(geistDir, `geist-mono-${name}.woff2`));
}

console.log('\nDone.');
