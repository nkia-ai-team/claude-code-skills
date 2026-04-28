// Apply validation results to manual frontmatter:
//  - merge round-1 + round-2 JSONL
//  - for EXACT matches: set menu_path_verified: true and add menu_path_full
//  - for everything else: leave as-is
//  - emit a summary report (categories matched/unmatched)
//
// Inputs (env): POLESTAR_REPO (default: repo root inferred from script location),
//               POLESTAR_OUT  (default: /tmp/polestar10-validation).
// Pass --dry-run to skip writes.
import fs from 'node:fs';
import path from 'node:path';

const REPO = process.env.POLESTAR_REPO ?? path.resolve(new URL('.', import.meta.url).pathname, '../../../..');
const OUT_DIR = process.env.POLESTAR_OUT ?? '/tmp/polestar10-validation';
const R1 = path.join(OUT_DIR, 'dumps', 'validation-results-v2.jsonl');
const R2 = path.join(OUT_DIR, 'dumps', 'validation-retry.jsonl');
const REPORT = path.join(OUT_DIR, 'dumps', 'apply-report.json');
const DRY_RUN = process.argv.includes('--dry-run');

function loadJsonl(p) {
  if (!fs.existsSync(p)) return [];
  return fs.readFileSync(p, 'utf-8').trim().split('\n').filter(Boolean).map((l) => JSON.parse(l));
}

const r1 = loadJsonl(R1);
const r2 = loadJsonl(R2);
const r2byPath = new Map(r2.map((r) => [r.path, r]));

function classify(rec) {
  if (rec.chosen?.exactMatch) {
    const fullPath = rec.chosen.exactMatch.category.replace(/>\s*/g, ' > ').replace(/\s+/g, ' ').trim();
    return { status: 'exact', fullPath, keyword: rec.chosen.exactMatch.keyword };
  }
  if (rec.chosen) {
    const items = rec.chosen.result.items.slice(0, 5).map((it) => ({
      keyword: it.keyword,
      category: it.category.replace(/>\s*/g, ' > ').replace(/\s+/g, ' ').trim(),
    }));
    return { status: 'partial', candidates: items, query: rec.chosen.query };
  }
  return { status: 'none' };
}

const decisions = [];
for (const rec of r1) {
  let final = classify(rec);
  // upgrade with round-2 if round-1 was none/partial
  if (final.status !== 'exact' && r2byPath.has(rec.path)) {
    const upgrade = classify(r2byPath.get(rec.path));
    if (upgrade.status === 'exact') final = upgrade;
    else if (final.status === 'none' && upgrade.status === 'partial') final = upgrade;
  }
  decisions.push({ path: rec.path, role: rec.role, category: rec.category, slug: rec.slug,
    feature: rec.feature, menu_path: rec.menu_path, admin_required: rec.admin_required, final });
}

// summary
const summary = { total: decisions.length, exact: 0, partial: 0, none: 0,
  byCategory: {}, byRole: { user: { matched: 0, total: 0 }, admin: { matched: 0, total: 0 } } };
for (const d of decisions) {
  summary[d.final.status]++;
  summary.byRole[d.role].total++;
  if (d.final.status === 'exact') summary.byRole[d.role].matched++;
  const k = `${d.role}/${d.category}`;
  if (!summary.byCategory[k]) summary.byCategory[k] = { total: 0, exact: 0, partial: 0, none: 0 };
  summary.byCategory[k].total++;
  summary.byCategory[k][d.final.status]++;
}

console.log('===== SUMMARY =====');
console.log(`total=${summary.total} exact=${summary.exact} partial=${summary.partial} none=${summary.none}`);
console.log('byRole:', JSON.stringify(summary.byRole));
console.log('byCategory:');
for (const [k, v] of Object.entries(summary.byCategory)) {
  console.log(`  ${k.padEnd(28)} exact=${v.exact}  partial=${v.partial}  none=${v.none}  total=${v.total}`);
}

fs.writeFileSync(REPORT, JSON.stringify({ summary, decisions }, null, 2));
console.log(`\nReport written: ${REPORT}`);

if (DRY_RUN) {
  console.log('\n[dry-run] no files modified');
  process.exit(0);
}

// ---- apply to frontmatter ----
let changed = 0;
for (const d of decisions) {
  if (d.final.status !== 'exact') continue;
  const file = path.join(REPO, d.path);
  const text = fs.readFileSync(file, 'utf-8');
  const m = text.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) continue;
  const body = text.slice(m[0].length);
  const lines = m[1].split('\n');
  let touched = false;
  let hasFull = false;
  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i];
    if (/^menu_path_verified:\s*/.test(ln)) {
      if (ln.trim() !== 'menu_path_verified: true') {
        lines[i] = 'menu_path_verified: true';
        touched = true;
      }
    } else if (/^menu_path_full:\s*/.test(ln)) {
      hasFull = true;
      const want = `menu_path_full: "${d.final.fullPath}"`;
      if (ln.trim() !== want) { lines[i] = want; touched = true; }
    }
  }
  if (!hasFull) {
    lines.push(`menu_path_full: "${d.final.fullPath}"`);
    touched = true;
  }
  if (touched) {
    const out = `---\n${lines.join('\n')}\n---\n${body}`;
    fs.writeFileSync(file, out);
    changed++;
  }
}
console.log(`\n[apply] frontmatter updated: ${changed} files`);
