// Round 1: search-based menu_path verification across all polestar10 manuals.
//
// Inputs (env): POLESTAR_BASE, POLESTAR_USER, POLESTAR_PASS,
//               POLESTAR_REPO (default: repo root inferred from script location),
//               POLESTAR_OUT  (default: /tmp/polestar10-validation).
// Output: <OUT>/dumps/validation-results-v2.jsonl
//
// NO clicks beyond the search input. NO navigation away from the dashboard.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const REPO = process.env.POLESTAR_REPO ?? path.resolve(new URL('.', import.meta.url).pathname, '../../../..');
const MANUALS = path.join(REPO, 'nkia-ai-tools/knowledge/polestar10/manuals');
const OUT_DIR = process.env.POLESTAR_OUT ?? '/tmp/polestar10-validation';
const OUT_JSONL = path.join(OUT_DIR, 'dumps', 'validation-results-v2.jsonl');

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
function listManuals(root) {
  const out = [];
  for (const role of ['user', 'admin']) {
    const roleDir = path.join(root, role);
    if (!fs.existsSync(roleDir)) continue;
    for (const cat of fs.readdirSync(roleDir)) {
      const catDir = path.join(roleDir, cat);
      if (!fs.statSync(catDir).isDirectory()) continue;
      for (const f of fs.readdirSync(catDir)) {
        if (!f.endsWith('.md') || f.startsWith('00-toc')) continue;
        const full = path.join(catDir, f);
        const fm = parseFrontmatter(fs.readFileSync(full, 'utf-8'));
        if (!fm) continue;
        out.push({ path: path.relative(REPO, full), role, category: cat, slug: f.replace(/\.md$/, ''), frontmatter: fm });
      }
    }
  }
  return out;
}
function buildQueries(fm) {
  const out = [];
  const f = fm.feature;
  if (typeof f === 'string' && f) {
    const noParen = f.replace(/\s*[（(].*$/, '').trim();
    const firstChunk = noParen.split(/\s*[–\-]\s+/)[0].trim();
    if (firstChunk) out.push(firstChunk);
    if (noParen && !out.includes(noParen)) out.push(noParen);
    if (!out.includes(f)) out.push(f);
  }
  if (fm.menu_path && !out.includes(fm.menu_path)) out.push(fm.menu_path);
  if (fm.original_title && !out.includes(fm.original_title)) out.push(fm.original_title);
  return out;
}

const manuals = listManuals(MANUALS);
console.log(`MANUALS: ${manuals.length}`);
fs.writeFileSync(OUT_JSONL, '');

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

let idx = 0, exact = 0, partial = 0, none = 0;
const t0 = Date.now();
for (const m of manuals) {
  idx++;
  const queries = buildQueries(m.frontmatter);
  let attempts = [];
  let chosen = null;
  for (const q of queries) {
    const r = await searchOne(q);
    attempts.push({ q, ...r });
    if (r.state === 'ok' && r.items.length) {
      const target = m.frontmatter.feature;
      const exactItem = r.items.find((it) => it.keyword === target || it.keyword === q);
      chosen = { query: q, result: r, exactMatch: exactItem };
      break;
    }
  }
  if (chosen) {
    if (chosen.exactMatch) exact++; else partial++;
  } else none++;
  fs.appendFileSync(OUT_JSONL, JSON.stringify({
    idx, path: m.path, role: m.role, category: m.category, slug: m.slug,
    feature: m.frontmatter.feature, menu_path: m.frontmatter.menu_path,
    admin_required: m.frontmatter.admin_required,
    queries_tried: attempts, chosen,
  }) + '\n');
  if (idx % 5 === 0 || idx === manuals.length) {
    const sec = ((Date.now() - t0) / 1000).toFixed(0);
    console.log(`[${idx}/${manuals.length}] ${sec}s | exact=${exact} partial=${partial} none=${none}`);
  }
}

await browser.close();
console.log('DONE');
