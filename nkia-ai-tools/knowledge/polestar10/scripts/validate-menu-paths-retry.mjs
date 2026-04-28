// Round 2: retry NONE entries from round 1 with prefix/suffix variants.
//   - k8s/* manuals: prepend "쿠버네티스 "
//   - any feature with multiple tokens: try first 2 tokens, then first token only
//   - strip trailing common nouns (목록/현황/관리/설정/상세/등록/편집/뷰어)
//
// Inputs (env): see validate-menu-paths.mjs.
// NO clicks beyond the search input. NO navigation away from the dashboard.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const REPO = process.env.POLESTAR_REPO ?? path.resolve(new URL('.', import.meta.url).pathname, '../../../..');
const MANUALS = path.join(REPO, 'nkia-ai-tools/knowledge/polestar10/manuals');
const OUT_DIR = process.env.POLESTAR_OUT ?? '/tmp/polestar10-validation';
const OUT_JSONL = path.join(OUT_DIR, 'dumps', 'validation-retry.jsonl');
const ROUND1_JSONL = path.join(OUT_DIR, 'dumps', 'validation-results-v2.jsonl');

const BASE = process.env.POLESTAR_BASE ?? (() => { throw new Error('POLESTAR_BASE env required'); })();
const USER = process.env.POLESTAR_USER ?? (() => { throw new Error('POLESTAR_USER env required'); })();
const PASS = process.env.POLESTAR_PASS ?? (() => { throw new Error('POLESTAR_PASS env required'); })();

fs.mkdirSync(path.dirname(OUT_JSONL), { recursive: true });

function parseFrontmatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  if (!m) return null;
  const fm = {};
  for (const line of m[1].split('\n')) {
    const km = line.match(/^([a-z_]+):\s*(.*)$/);
    if (!km) continue;
    let val = km[2].trim();
    if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
    if (val === 'true') val = true;
    else if (val === 'false') val = false;
    fm[km[1]] = val;
  }
  return fm;
}

// load NONE list from prior run
const prior = fs.readFileSync(ROUND1_JSONL, 'utf-8')
  .trim().split('\n').map((l) => JSON.parse(l));
const targets = prior.filter((r) => !r.chosen);

function buildExtraQueries(rec) {
  const f = rec.feature;
  if (typeof f !== 'string' || !f) return [];
  const q = [];
  // strip html
  const clean = f.replace(/<[^>]+>/g, '').trim();
  if (rec.category === 'k8s') {
    // try with "쿠버네티스" prefix
    q.push(`쿠버네티스 ${clean}`);
    // also try just first non-trivial token
    const tokens = clean.split(/\s+/);
    if (tokens.length > 1) q.push(`쿠버네티스 ${tokens[0]}`);
  }
  if (clean.includes(' ')) {
    // try first two tokens
    const t = clean.split(/\s+/);
    if (t.length > 2) q.push(t.slice(0, 2).join(' '));
    // try first token only
    q.push(t[0]);
  }
  // strip trailing common nouns ("목록", "현황", "관리", "설정") and try
  const stripped = clean.replace(/\s*(목록|현황|관리|설정|상세|등록|편집|뷰어)\s*$/, '');
  if (stripped && stripped !== clean) q.push(stripped);
  return Array.from(new Set(q));
}

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1920, height: 1080 } });
const page = await ctx.newPage();

await page.goto(BASE, { waitUntil: 'load' });
await page.waitForSelector('#loginId');
const ok = page.getByRole('button', { name: '확인' });
if (await ok.count()) await ok.first().click().catch(() => {});
await page.waitForTimeout(200);
await page.fill('#loginId', USER);
await page.fill('#password', PASS);
await page.getByRole('button', { name: '로그인' }).click();
await page.waitForURL((u) => !u.toString().endsWith('/login'), { timeout: 20000 });
for (let i = 0; i < 30; i++) {
  await page.waitForTimeout(500);
  const has = await page.evaluate(() => !!document.querySelector('input[placeholder*="장비"]'));
  if (has) break;
}
console.log('LOGGED IN');

const search = page.locator('input[placeholder*="장비, IP, 메뉴"]').first();

async function searchOne(query) {
  await search.click();
  await page.keyboard.press('Control+a').catch(() => {});
  await page.keyboard.press('Delete').catch(() => {});
  await page.waitForTimeout(120);
  await search.fill(query);
  await page.waitForTimeout(1500);
  return await page.evaluate(() => {
    const drop = document.querySelector('.portal-auto-complete-dropdown');
    if (!drop) return { state: 'no-dropdown', items: [] };
    const result = drop.querySelector('.auto-complete-result');
    if (result) {
      const countEl = result.querySelector('.result-header-section .count');
      const count = countEl ? parseInt(countEl.textContent.trim(), 10) : null;
      const items = [];
      for (const c of result.querySelectorAll('.result-content')) {
        const cat = c.querySelector('.category')?.innerText?.trim() || '';
        const kw = c.querySelector('.keyword')?.innerText?.trim() || '';
        items.push({ category: cat, keyword: kw });
      }
      return { state: 'ok', count, items };
    }
    if (drop.querySelector('.auto-complete-no-result')) return { state: 'empty', items: [] };
    return { state: 'unknown', items: [] };
  });
}

fs.writeFileSync(OUT_JSONL, '');
let idx = 0, exact = 0, partial = 0, none = 0;
const t0 = Date.now();
for (const rec of targets) {
  idx++;
  const queries = buildExtraQueries(rec);
  const attempts = [];
  let chosen = null;
  for (const q of queries) {
    if (!q) continue;
    const r = await searchOne(q);
    attempts.push({ q, ...r });
    if (r.state === 'ok' && r.items.length) {
      const target = rec.feature;
      const exactItem = r.items.find((it) => it.keyword === target || it.keyword === q);
      chosen = { query: q, result: r, exactMatch: exactItem };
      break;
    }
  }
  if (chosen) { if (chosen.exactMatch) exact++; else partial++; } else none++;
  fs.appendFileSync(OUT_JSONL, JSON.stringify({
    path: rec.path, role: rec.role, category: rec.category, slug: rec.slug,
    feature: rec.feature, queries_tried: attempts, chosen,
  }) + '\n');
  if (idx % 10 === 0 || idx === targets.length) {
    console.log(`[${idx}/${targets.length}] ${((Date.now() - t0) / 1000).toFixed(0)}s | exact=${exact} partial=${partial} none=${none}`);
  }
}
await browser.close();
console.log('DONE');
