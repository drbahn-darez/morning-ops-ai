#!/usr/bin/env node
// Headless Instagram carousel renderer: spec JSON -> PNG slides + contact sheet.
//
//   node tools/carousel/render.mjs <spec.json> [outDir]
//
// Spec:
// {
//   "id": "ega-2026-10-07-sauna-myth",
//   "brand": "ega" | "adro",
//   "size": "4:5" (default, API carousel) | "3:4" (app-only hero carousel with music) | "1:1" | "9:16" (Reels cover_url),
//   "handle": "@brand",                     // optional, overrides theme
//   "format": "jpg" (default; the Instagram API accepts JPEG only) | "png",
//   "slides": [
//     { "layout": "cover",   "eyebrow": "Contrast Therapy", "title": "...", "sub": "...", "image": "assets/x.webp" },
//     { "layout": "text",    "eyebrow": "...", "title": "...", "body": "..." },
//     { "layout": "list",    "title": "...", "items": ["...", "..."] },
//     { "layout": "stat",    "stat": "15", "unit": "%", "title": "...", "source": "..." },
//     { "layout": "compare", "title": "...", "left": {"label": "Myth", "text": "..."}, "right": {"label": "Fact", "text": "..."} },
//     { "layout": "quote",   "quote": "...", "by": "..." },
//     { "layout": "cta",     "title": "...", "action": "..." }
//   ]
// }
// Any slide may add "disclaimer": "..." (small print kept above the bottom bar) and "image".

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { execSync, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { pathToFileURL } from 'node:url';
import { THEMES, SIZES } from './themes.mjs';

function loadPlaywright() {
  const require = createRequire(import.meta.url);
  try {
    return require('playwright');
  } catch {
    const root = execSync('npm root -g').toString().trim();
    return require(path.join(root, 'playwright'));
  }
}

// Google Fonts are fetched once with curl and cached on disk. Chromium asks for many
// unicode-range subsets in parallel, which some egress proxies drop; curl + cache is
// reliable and makes repeat renders fast.
const FONT_CACHE = process.env.CAROUSEL_FONT_CACHE || path.join(os.homedir(), '.cache', 'insta-carousel-fonts');
const run = promisify(execFile);
let inflight = Promise.resolve();

async function cachedFetch(url, userAgent) {
  const key = crypto.createHash('sha1').update(`${userAgent}|${url}`).digest('hex');
  const file = path.join(FONT_CACHE, key);
  if (!fs.existsSync(file)) {
    fs.mkdirSync(FONT_CACHE, { recursive: true });
    // Serialize downloads: one connection at a time through any proxy.
    const job = inflight.then(() =>
      run('curl', ['-sSfL', '--retry', '3', '-A', userAgent, '-o', `${file}.part`, url]).then(() =>
        fs.renameSync(`${file}.part`, file),
      ),
    );
    inflight = job.catch(() => {});
    await job;
  }
  return fs.readFileSync(file);
}

async function routeFonts(context) {
  await context.route(/^https:\/\/fonts\.(googleapis|gstatic)\.com\//, async (route) => {
    const req = route.request();
    const url = req.url();
    try {
      const body = await cachedFetch(url, req.headers()['user-agent'] || 'Mozilla/5.0');
      const css = url.includes('fonts.googleapis.com');
      await route.fulfill({
        status: 200,
        body,
        headers: { 'content-type': css ? 'text/css; charset=utf-8' : 'font/woff2', 'access-control-allow-origin': '*' },
      });
    } catch {
      await route.abort();
    }
  });
}

const esc = (s = '') =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
// Allow **bold** and line breaks in copy.
const rich = (s = '') => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');

function imageUrl(src, specDir) {
  if (!src) return null;
  if (/^https?:|^data:|^file:/.test(src)) return src;
  return pathToFileURL(path.resolve(specDir, src)).href;
}

function slideBody(s, i, total) {
  switch (s.layout) {
    case 'cover':
      return `
        <div class="cover">
          <h1 class="fit">${rich(s.title)}</h1>
          ${s.sub ? `<p class="sub">${rich(s.sub)}</p>` : ''}
        </div>
`;
    case 'text':
      return `
        <h2 class="fit">${rich(s.title)}</h2>
        ${s.body ? `<p class="body">${rich(s.body)}</p>` : ''}`;
    case 'list':
      return `
        <h2>${rich(s.title)}</h2>
        <ol class="list">${(s.items || []).slice(0, 6).map((it, n) => `<li><span class="n">${String(n + 1).padStart(2, '0')}</span><span>${rich(it)}</span></li>`).join('')}</ol>`;
    case 'stat':
      return `
        <div class="stat"><span class="num">${esc(s.stat)}</span><span class="unit">${esc(s.unit || '')}</span></div>
        <h2>${rich(s.title)}</h2>
        ${s.body ? `<p class="body">${rich(s.body)}</p>` : ''}
        ${s.source ? `<p class="source">Source: ${esc(s.source)}</p>` : ''}`;
    case 'compare':
      return `
        <h2>${rich(s.title)}</h2>
        <div class="compare">
          <div class="col left"><div class="tag">${esc(s.left?.label || 'Before')}</div><p>${rich(s.left?.text)}</p></div>
          <div class="col right"><div class="tag">${esc(s.right?.label || 'After')}</div><p>${rich(s.right?.text)}</p></div>
        </div>`;
    case 'quote':
      return `
        <blockquote class="fit">“${rich(s.quote)}”</blockquote>
        ${s.by ? `<p class="by">— ${esc(s.by)}</p>` : ''}`;
    case 'cta':
      return `
        <div class="cta">
          <h2 class="fit">${rich(s.title)}</h2>
          ${s.action ? `<p class="action">${rich(s.action)}</p>` : ''}
        </div>`;
    default:
      throw new Error(`slide ${i + 1}: unknown layout "${s.layout}"`);
  }
}

function pageHtml(spec, s, i, total, specDir) {
  const t = THEMES[spec.brand];
  const { width, height } = SIZES[spec.size || '4:5'];
  const alt = t.alternate && i > 0 && i < total - 1 && i % 2 === 1;
  const bg = alt ? t.bgAlt : t.bg;
  const ink = alt ? t.inkAlt : t.ink;
  const muted = alt ? t.mutedAlt : t.muted;
  const accent = alt ? t.accentAlt : t.accent;
  const img = imageUrl(s.image, specDir);
  const handle = spec.handle ?? t.handle;
  const pad = 96;
  // Reels cover (9:16): keep text inside y 300-1240 so it survives the Reels UI and the 3:4 grid crop.
  const inset = spec.size === '9:16' ? `300px ${pad}px 680px` : `${pad}px ${pad}px ${pad + 24}px`;
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="${t.fonts}">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: ${width}px; height: ${height}px; }
  body { background: ${bg}; color: ${ink}; font-family: ${t.body}; overflow: hidden; position: relative;
         -webkit-font-smoothing: antialiased; word-break: keep-all; overflow-wrap: anywhere; }
  .bgimg { position: absolute; inset: 0; background: url("${img || ''}") center/cover no-repeat; }
  .scrim { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.25) 40%, ${bg}F2 78%, ${bg} 100%); }
  ${t.grid ? `.grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px); background-size: 90px 90px; }` : ''}
  .frame { position: absolute; inset: ${inset}; display: flex; flex-direction: column; }
  .top { display: flex; justify-content: space-between; align-items: baseline; color: ${muted};
         font-family: ${t.eyebrow}; font-style: ${t.eyebrowStyle}; letter-spacing: ${t.eyebrowTracking}; font-size: 34px; }
  .top .eyebrow { color: ${accent}; }
  .content { flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 36px; min-height: 0; }
  h1, h2, blockquote { font-family: ${t.headline}; font-weight: ${t.headlineWeight}; line-height: 1.22; letter-spacing: -0.02em; text-wrap: balance; }
  h1 { font-size: 92px; }
  h2 { font-size: 76px; }
  strong { color: ${accent}; font-weight: inherit; }
  .cover { margin-top: auto; display: flex; flex-direction: column; gap: 28px; }
  .content:has(.cover) { justify-content: flex-end; }
  .sub { font-size: 40px; line-height: 1.5; color: ${muted}; }
  .body { font-size: 42px; line-height: 1.6; color: ${muted}; }
  .list { list-style: none; display: flex; flex-direction: column; gap: 30px; }
  .list li { display: flex; gap: 28px; font-size: 44px; line-height: 1.45; align-items: baseline; }
  .list .n { font-family: ${t.eyebrow}; color: ${accent}; font-size: 34px; min-width: 56px; }
  .stat { display: flex; align-items: baseline; gap: 12px; color: ${accent}; font-family: ${t.headline}; font-weight: ${t.headlineWeight}; }
  .stat .num { font-size: 260px; line-height: 0.9; letter-spacing: -0.04em; }
  .stat .unit { font-size: 110px; }
  .source { font-size: 24px; color: ${muted}; }
  .compare { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
  .compare .col { border: 2px solid ${muted}; border-radius: 20px; padding: 36px; display: flex; flex-direction: column; gap: 20px; }
  .compare .right { border-color: ${accent}; }
  .compare .tag { font-family: ${t.eyebrow}; font-style: ${t.eyebrowStyle}; letter-spacing: ${t.eyebrowTracking}; color: ${accent}; font-size: 30px; }
  .compare p { font-size: 40px; line-height: 1.5; }
  blockquote { font-size: 70px; }
  .by { font-size: 32px; color: ${muted}; }
  .cta { display: flex; flex-direction: column; gap: 36px; }
  .action { display: inline-block; align-self: flex-start; font-size: 36px; padding: 22px 34px; border-radius: 999px;
            background: ${accent}; color: ${bg}; font-weight: 700; }
  .disclaimer { font-size: 24px; line-height: 1.45; color: ${muted}; margin-top: 18px; }
  .bottom { display: flex; justify-content: space-between; align-items: center; font-size: 26px; color: ${muted};
            border-top: 2px solid ${accent}; padding-top: 22px; margin-top: 28px; }
</style></head><body>
${img ? '<div class="bgimg"></div><div class="scrim"></div>' : ''}${t.grid ? '<div class="grid"></div>' : ''}
<div class="frame">
  <div class="top"><span class="eyebrow">${esc(s.eyebrow || '')}</span><span>${total > 1 ? `${String(i + 1).padStart(2, '0')} / ${String(total).padStart(2, '0')}` : ''}</span></div>
  <div class="content">${slideBody(s, i, total)}</div>
  ${s.disclaimer ? `<p class="disclaimer">${esc(s.disclaimer)}</p>` : ''}
  <div class="bottom"><span>${esc(handle)}</span><span>${i === 0 && total > 1 ? '넘겨서 보기 →' : esc(spec.footer || '')}</span></div>
</div>
<script>
  // Shrink headlines that overflow their box so long Korean titles never clip.
  document.fonts.ready.then(() => {
    const content = document.querySelector('.content');
    for (const el of document.querySelectorAll('.fit, h2')) {
      let size = parseFloat(getComputedStyle(el).fontSize);
      while (content.scrollHeight > content.clientHeight && size > 40) {
        size -= 4; el.style.fontSize = size + 'px';
      }
    }
    document.body.dataset.ready = '1';
  });
</script>
</body></html>`;
}

function sheetHtml(files, cols, w, h) {
  const tw = 360, th = Math.round((h / w) * tw);
  return `<!doctype html><html><body style="margin:0;background:#111;display:grid;grid-template-columns:repeat(${cols},${tw}px);gap:12px;padding:12px;width:max-content">
${files.map((f) => `<img src="${pathToFileURL(f).href}" style="width:${tw}px;height:${th}px;display:block">`).join('')}
</body></html>`;
}

export async function render(specPath, outDir) {
  const specDir = path.dirname(path.resolve(specPath));
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  if (!THEMES[spec.brand]) throw new Error(`unknown brand "${spec.brand}" (known: ${Object.keys(THEMES).join(', ')})`);
  if (!SIZES[spec.size || '4:5']) throw new Error(`unknown size "${spec.size}"`);
  const slides = spec.slides || [];
  if (slides.length < 1 || slides.length > 20) throw new Error('a carousel needs 1-20 slides');
  const { width, height } = SIZES[spec.size || '4:5'];
  const id = spec.id || path.basename(specPath, '.json');
  outDir = path.resolve(outDir || path.join('out', id));
  fs.mkdirSync(outDir, { recursive: true });

  const { chromium } = loadPlaywright();
  // Behind an egress proxy (cloud sessions) Chromium must be told about it to load web fonts.
  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  const browser = await chromium.launch(proxy ? { proxy: { server: proxy } } : {});
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, ignoreHTTPSErrors: !!proxy });
  await routeFonts(context);
  const page = await context.newPage();
  const files = [];
  try {
    for (let i = 0; i < slides.length; i++) {
      const htmlPath = path.join(outDir, `.slide-${i + 1}.html`);
      fs.writeFileSync(htmlPath, pageHtml(spec, slides[i], i, slides.length, specDir));
      await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'networkidle' });
      await page.waitForSelector('body[data-ready="1"]', { timeout: 15000 });
      const jpg = (spec.format || 'jpg') !== 'png';
      const file = path.join(outDir, `${id}_${String(i + 1).padStart(2, '0')}.${jpg ? 'jpg' : 'png'}`);
      await page.screenshot({ path: file, clip: { x: 0, y: 0, width, height }, ...(jpg ? { type: 'jpeg', quality: 92 } : {}) });
      if (!process.env.KEEP_HTML) fs.unlinkSync(htmlPath);
      files.push(file);
    }
    const cols = Math.min(files.length, 5);
    const sheetPath = path.join(outDir, '.sheet.html');
    fs.writeFileSync(sheetPath, sheetHtml(files, cols, width, height));
    await page.setViewportSize({ width: 2000, height: 2000 });
    await page.goto(pathToFileURL(sheetPath).href, { waitUntil: 'load' });
    const sheet = path.join(outDir, `${id}_sheet.png`);
    await page.locator('body').screenshot({ path: sheet });
    fs.unlinkSync(sheetPath);
    return { id, outDir, slides: files, sheet };
  } finally {
    await browser.close();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [specPath, outDir] = process.argv.slice(2);
  if (!specPath) {
    console.error('usage: node tools/carousel/render.mjs <spec.json> [outDir]');
    process.exit(2);
  }
  render(specPath, outDir)
    .then((r) => console.log(JSON.stringify(r, null, 1)))
    .catch((e) => {
      console.error(e.message);
      process.exit(1);
    });
}
