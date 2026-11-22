#!/usr/bin/env node

// make_social_card.js adds a social media card (Open Graph / Twitter Card) to a
// Wasm build, so that a link to the published site unfurls with a screenshot of
// the plug-in and a short description.
//
// It does two things to the dist folder produced by makedist-wasm.sh (or the
// CMake <project>-wasm-dist target):
//
// 1. Writes social-card.png (1200x630). By default the plug-in is loaded in
//    headless Chromium via Playwright, its UI is screenshotted and composed
//    with the title/description. Alternatively a ready-made image can be
//    supplied in config/TemplateProject-web.json.
// 2. Injects the <meta> tags into index.html (safe to run repeatedly).
//
// Usage:
//   node make_social_card.js [dist-dir] [--url <site-url>] [--no-screenshot]
//
// dist-dir defaults to ../build-web-wasm
//
// The site URL is needed because card images must be absolute URLs. It is
// taken from, in order: --url, "url" in the config json, $SITE_URL, or the
// default GitHub Pages address derived from $GITHUB_REPOSITORY in CI.
//
// Playwright is only needed for the automatic screenshot:
//   npm install --no-save --no-package-lock playwright
//   npx playwright install --with-deps chromium

'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const crypto = require('crypto');

const PROJECT_NAME = 'TemplateProject';
const PROJECT_ROOT = path.resolve(__dirname, '..');
const CONFIG_JSON = path.join(PROJECT_ROOT, 'config', `${PROJECT_NAME}-web.json`);

const CARD_FILE = 'social-card.png';
const CARD_WIDTH = 1200;
const CARD_HEIGHT = 630;
const BEGIN_MARKER = '<!-- social-card:begin -->';
const END_MARKER = '<!-- social-card:end -->';

//------------------------------------------------------------------------------

function parseArgs(argv) {
  const args = { distDir: path.join(PROJECT_ROOT, 'build-web-wasm'), url: '', screenshot: true };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--url') args.url = argv[++i] || '';
    else if (arg === '--no-screenshot') args.screenshot = false;
    else if (arg === '-h' || arg === '--help') {
      console.log('Usage: node make_social_card.js [dist-dir] [--url <site-url>] [--no-screenshot]');
      process.exit(0);
    } else if (arg.startsWith('-')) {
      throw new Error(`Unknown option ${arg}`);
    } else args.distDir = path.resolve(arg);
  }
  return args;
}

// Read a #define from config.h, e.g. PLUG_NAME "Foo" or PLUG_WIDTH 1024
function readDefine(name, fallback) {
  try {
    const src = fs.readFileSync(path.join(PROJECT_ROOT, 'config.h'), 'utf8');
    const match = src.match(new RegExp(`^\\s*#define\\s+${name}\\s+(?:"([^"]*)"|(\\S+))`, 'm'));
    if (match) return match[1] !== undefined ? match[1] : match[2];
  } catch (err) { /* fall through */ }
  return fallback;
}

function readConfig() {
  let json = {};
  if (fs.existsSync(CONFIG_JSON)) {
    json = JSON.parse(fs.readFileSync(CONFIG_JSON, 'utf8'));
  }
  const name = readDefine('PLUG_NAME', PROJECT_NAME);
  return {
    title: json.title || name,
    description: json.description || `${name} audio plug-in, running in your browser.`,
    author: json.author !== undefined ? json.author : readDefine('PLUG_MFR', ''),
    url: json.url || '',
    image: json.image || '',
    twitterSite: json.twitterSite || '',
    background: json.background || '#16181d',
    foreground: json.foreground || '#ffffff',
    screenshotDelayMs: Number.isFinite(json.screenshotDelayMs) ? json.screenshotDelayMs : 1000,
    width: parseInt(readDefine('PLUG_WIDTH', '1024'), 10) || 1024,
    height: parseInt(readDefine('PLUG_HEIGHT', '768'), 10) || 768,
    hasUI: readDefine('PLUG_HAS_UI', '1') === '1',
  };
}

// https://<owner>.github.io/<repo>/ (or the root for a <owner>.github.io repo)
function gitHubPagesUrl() {
  const repository = process.env.GITHUB_REPOSITORY;
  if (!repository || !repository.includes('/')) return '';
  const [owner, repo] = repository.split('/');
  const host = `${owner.toLowerCase()}.github.io`;
  return repo.toLowerCase() === host ? `https://${host}/` : `https://${host}/${repo}/`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

//------------------------------------------------------------------------------
// Static file server with the headers needed for SharedArrayBuffer

const MIME_TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.wasm': 'application/wasm',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml',
};

function serve(rootDir) {
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    let filePath = path.join(rootDir, path.normalize(urlPath));
    if (!filePath.startsWith(rootDir)) { res.writeHead(403).end(); return; }
    if (urlPath.endsWith('/')) filePath = path.join(filePath, 'index.html');
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404).end(); return; }
      res.writeHead(200, {
        'Content-Type': MIME_TYPES[path.extname(filePath)] || 'application/octet-stream',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Resource-Policy': 'same-origin',
      });
      res.end(data);
    });
  });
  return new Promise((resolve, reject) => {
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

//------------------------------------------------------------------------------
// Screenshot + card rendering

// Load the built plug-in and return a PNG buffer of its UI
async function screenshotPlugin(browser, distDir, config) {
  const server = await serve(distDir);
  const context = await browser.newContext({
    viewport: { width: config.width + 80, height: config.height + 240 },
    deviceScaleFactor: 2,
  });
  try {
    const page = await context.newPage();
    page.on('pageerror', (err) => console.warn(`  page error: ${err.message}`));
    await page.goto(`http://127.0.0.1:${server.address().port}/index.html`);

    const tag = `iplug-${PROJECT_NAME.toLowerCase()}`;
    // The page stretches the plug-in to fill the window: pin it to its default size instead
    await page.addStyleTag({
      content: `${tag} { width: ${config.width}px !important; height: ${config.height}px !important; }`,
    });
    await page.waitForFunction((t) => document.querySelector(t)?._uiReady === true, tag, { timeout: 60000 });
    // Let the UI draw a few frames (raise screenshotDelayMs for UIs that animate in)
    await page.waitForTimeout(config.screenshotDelayMs);

    return await page.locator(`${tag} canvas`).screenshot({ type: 'png' });
  } finally {
    await context.close();
    server.close();
  }
}

function cardHtml(config, siteUrl, screenshot) {
  // Wide UIs sit under the text, everything else sits next to it
  const stacked = screenshot && config.width / config.height > 2.2;
  const host = siteUrl ? siteUrl.replace(/^https?:\/\//, '').replace(/\/$/, '') : '';
  const shot = screenshot
    ? `<div class="shot"><img src="data:image/png;base64,${screenshot.toString('base64')}"></div>`
    : '';

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: ${CARD_WIDTH}px; height: ${CARD_HEIGHT}px; }
  body {
    display: flex;
    flex-direction: ${stacked ? 'column' : 'row'};
    align-items: ${stacked ? 'stretch' : 'center'};
    gap: ${stacked ? 36 : 56}px;
    padding: 60px;
    background: ${config.background};
    color: ${config.foreground};
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    overflow: hidden;
  }
  .text {
    flex: ${screenshot ? (stacked ? '0 0 auto' : '0 0 400px') : '1'};
    display: flex;
    flex-direction: column;
    gap: ${stacked ? 10 : 18}px;
    min-width: 0;
  }
  h1 { font-size: ${screenshot ? (stacked ? 52 : 56) : 96}px; line-height: 1.05; font-weight: 700; }
  .author { font-size: ${screenshot ? 24 : 34}px; opacity: 0.6; }
  .description { font-size: ${screenshot ? 28 : 42}px; line-height: 1.3; opacity: 0.85; }
  .host { font-size: ${screenshot ? 20 : 28}px; opacity: 0.5; margin-top: ${stacked ? 0 : 12}px; }
  .shot { flex: 1; min-width: 0; min-height: 0; display: flex; align-items: center; justify-content: center; ${stacked ? '' : 'height: 100%;'} }
  .shot img {
    max-width: 100%;
    max-height: 100%;
    border-radius: 10px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.08);
  }
</style>
</head>
<body>
  <div class="text">
    <h1>${escapeHtml(config.title)}</h1>
    ${config.author ? `<div class="author">${escapeHtml(config.author)}</div>` : ''}
    <div class="description">${escapeHtml(config.description)}</div>
    ${host && !stacked ? `<div class="host">${escapeHtml(host)}</div>` : ''}
  </div>
  ${shot}
  <script>
    // Shrink the title until its longest word fits the column
    const h1 = document.querySelector('h1');
    for (let size = parseFloat(getComputedStyle(h1).fontSize); h1.scrollWidth > h1.clientWidth && size > 24; size -= 2) {
      h1.style.fontSize = size + 'px';
    }
  </script>
</body>
</html>`;
}

async function renderCard(distDir, config, siteUrl, wantScreenshot) {
  let playwright;
  try {
    playwright = require('playwright');
  } catch (err) {
    console.warn('WARNING: Playwright is not installed, so no card image was generated.');
    console.warn('  npm install --no-save --no-package-lock playwright && npx playwright install --with-deps chromium');
    console.warn(`  (or set "image" in config/${PROJECT_NAME}-web.json to use a ready-made image)`);
    return false;
  }

  // WebGL needs a software GL fallback on machines without a GPU (e.g. CI runners)
  const browser = await playwright.chromium.launch({
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  try {
    let screenshot = null;
    if (wantScreenshot && config.hasUI) {
      try {
        console.log('Taking screenshot of plug-in UI...');
        screenshot = await screenshotPlugin(browser, distDir, config);
      } catch (err) {
        console.warn(`WARNING: could not screenshot the plug-in UI (${err.message.split('\n')[0]}), making a text-only card.`);
      }
    }

    const context = await browser.newContext({
      viewport: { width: CARD_WIDTH, height: CARD_HEIGHT },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    await page.setContent(cardHtml(config, siteUrl, screenshot), { waitUntil: 'load' });
    await page.screenshot({ path: path.join(distDir, CARD_FILE), type: 'png' });
    return true;
  } finally {
    await browser.close();
  }
}

//------------------------------------------------------------------------------
// index.html meta tags

function metaTags(config, siteUrl, imageFile, imageSize) {
  const tags = [];
  const meta = (attr, key, value) => tags.push(`<meta ${attr}="${key}" content="${escapeHtml(value)}">`);

  meta('name', 'description', config.description);
  meta('property', 'og:type', 'website');
  meta('property', 'og:title', config.title);
  meta('property', 'og:description', config.description);
  if (siteUrl) meta('property', 'og:url', siteUrl);

  if (imageFile) {
    // The hash makes sites that cache cards by URL pick up a new screenshot
    const hash = crypto.createHash('sha1').update(fs.readFileSync(imageFile)).digest('hex').slice(0, 8);
    const imageUrl = `${siteUrl}${path.basename(imageFile)}?v=${hash}`;
    const alt = `Screenshot of ${config.title}`;
    meta('property', 'og:image', imageUrl);
    if (imageSize) {
      meta('property', 'og:image:width', imageSize.width);
      meta('property', 'og:image:height', imageSize.height);
    }
    meta('property', 'og:image:alt', alt);
    meta('name', 'twitter:card', 'summary_large_image');
    meta('name', 'twitter:image', imageUrl);
    meta('name', 'twitter:image:alt', alt);
  } else {
    meta('name', 'twitter:card', 'summary');
  }

  meta('name', 'twitter:title', config.title);
  meta('name', 'twitter:description', config.description);
  if (config.twitterSite) meta('name', 'twitter:site', config.twitterSite);

  return tags;
}

function injectMetaTags(indexPath, tags) {
  let html = fs.readFileSync(indexPath, 'utf8');
  const block = [BEGIN_MARKER, ...tags, END_MARKER].map((line) => `  ${line}`).join('\n');

  const begin = html.indexOf(BEGIN_MARKER);
  const end = html.indexOf(END_MARKER);
  if (begin !== -1 && end !== -1) {
    const lineStart = html.lastIndexOf('\n', begin) + 1;
    html = html.slice(0, lineStart) + block + html.slice(end + END_MARKER.length);
  } else if (html.includes('</title>')) {
    html = html.replace('</title>', () => `</title>\n${block}`);
  } else if (html.includes('</head>')) {
    html = html.replace('</head>', () => `${block}\n</head>`);
  } else {
    throw new Error(`${indexPath} has no <head> to add the meta tags to`);
  }
  fs.writeFileSync(indexPath, html);
}

// Width/height from a PNG header, or null for anything else
function pngSize(file) {
  const header = fs.readFileSync(file).subarray(0, 24);
  if (header.length < 24 || header.toString('latin1', 1, 4) !== 'PNG') return null;
  return { width: header.readUInt32BE(16), height: header.readUInt32BE(20) };
}

//------------------------------------------------------------------------------

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const config = readConfig();
  const indexPath = path.join(args.distDir, 'index.html');

  if (!fs.existsSync(indexPath)) {
    throw new Error(`${indexPath} not found - build the Wasm distribution first (makedist-wasm.sh)`);
  }

  let siteUrl = args.url || config.url || process.env.SITE_URL || gitHubPagesUrl();
  if (siteUrl && !siteUrl.endsWith('/')) siteUrl += '/';
  if (!siteUrl) {
    console.warn('WARNING: site URL unknown, so the card image URL will be relative and most sites will ignore it.');
    console.warn(`  Pass --url https://example.com/${PROJECT_NAME}/ or set "url" in config/${PROJECT_NAME}-web.json`);
  }

  let imageFile = null;
  if (config.image) {
    // Ready-made image: copy it into the dist folder as is
    const src = path.resolve(PROJECT_ROOT, config.image);
    imageFile = path.join(args.distDir, `social-card${path.extname(src).toLowerCase()}`);
    fs.copyFileSync(src, imageFile);
    console.log(`Using ${path.relative(PROJECT_ROOT, src)} as the card image`);
  } else if (await renderCard(args.distDir, config, siteUrl, args.screenshot)) {
    imageFile = path.join(args.distDir, CARD_FILE);
  }

  injectMetaTags(indexPath, metaTags(config, siteUrl, imageFile, imageFile && pngSize(imageFile)));

  console.log(`Social card added to ${path.relative(process.cwd(), indexPath) || indexPath}`);
  console.log(`  title:       ${config.title}`);
  console.log(`  description: ${config.description}`);
  console.log(`  url:         ${siteUrl || '(unknown)'}`);
  console.log(`  image:       ${imageFile ? path.basename(imageFile) : '(none)'}`);
}

main().catch((err) => {
  console.error(`ERROR: ${err.message}`);
  process.exit(1);
});
