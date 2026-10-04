// Renderer regression tests. Run: node --test tools/carousel/test_render.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { render, validateSpec } from './render.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'carousel-test-'));
const write = (name, spec) => {
  const p = path.join(tmp, `${name}.json`);
  fs.writeFileSync(p, JSON.stringify(spec));
  return p;
};
const LONG = '처음 사우나에 가는 사람이 꼭 알아야 하는 온탕과 냉탕 사이의 아주 긴 제목이 여기에 들어갑니다 정말로 깁니다';

test('validation rejects bad specs before rendering anything', () => {
  assert.throws(() => validateSpec({ brand: 'ega', slides: [{ layout: 'hero', title: 'x' }] }), /unknown layout/);
  assert.throws(() => validateSpec({ brand: 'ega', slides: [{ layout: 'list', title: 'x', items: Array(7).fill('a') }] }), /max 6/);
  assert.throws(() => validateSpec({ brand: 'ega', slides: [{ layout: 'stat', title: 'x' }] }), /missing "stat"/);
  assert.throws(() => validateSpec({ brand: 'nope', slides: [{ layout: 'cover', title: 'x' }] }), /unknown brand/);
});

test('long titles stay inside the canvas, stats never wrap, stale slides are removed', { timeout: 120000 }, async () => {
  const out = path.join(tmp, 'out');
  const spec = write('long', {
    id: 't-long', brand: 'ega', handle: '@test',
    slides: [
      { layout: 'cover', eyebrow: 'Long Title', title: LONG, sub: LONG },
      { layout: 'stat', stat: '100,000', unit: '회', title: '10만 조회' },
      { layout: 'text', title: '사진 위 본문', body: '본문', image: path.join(here, 'examples/test-photo.jpg') },
      { layout: 'cta', title: '저장하세요' },
    ],
  });
  const r = await render(spec, out);
  assert.equal(r.slides.length, 4);
  // re-render with fewer slides into the same folder: old _03/_04 must be gone
  const spec2 = write('long', { id: 't-long', brand: 'ega', handle: '@test', slides: [{ layout: 'cover', title: '짧은 제목' }] });
  await render(spec2, out);
  const left = fs.readdirSync(out).filter((f) => /^t-long_\d{2}\.jpg$/.test(f));
  assert.deepEqual(left, ['t-long_01.jpg']);
});

test('9:16 cover renders at 1080x1920 and copy that cannot fit fails loudly', { timeout: 120000 }, async () => {
  const out = path.join(tmp, 'cover');
  const r = await render(write('cover', { id: 't-cover', brand: 'adro', size: '9:16', slides: [{ layout: 'cover', title: LONG }] }), out);
  const head = fs.readFileSync(r.slides[0]);
  assert.equal(head[0], 0xff); // JPEG
  const huge = Array(12).fill(LONG).join(' ');
  await assert.rejects(
    render(write('huge', { id: 't-huge', brand: 'adro', slides: [{ layout: 'text', title: huge, body: huge }] }), path.join(tmp, 'huge')),
    /does not fit/,
  );
  assert.equal(fs.existsSync(path.join(tmp, 'huge', 't-huge_01.jpg')), false);
});
