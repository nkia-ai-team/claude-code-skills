#!/usr/bin/env python3
"""
polestar-eval-test 결과 자동 report.md 생성기.

사용법:
    python scripts/gen_report.py <run-id>
    python scripts/gen_report.py 2026-05-22-022924-104-all

입력 (runs/<run-id>/ 디렉토리):
    - memory-snapshot.json
    - queries-<category>.json (Challenger 산출)
    - <NNN>-<category>-<qid>.json (Runner checkpoint)
    - <NNN>-<category>-<qid>.png (screenshot)
    - verifier-<category>.json (Verifier 산출)

출력:
    - runs/<run-id>/report.md (strict template, 모든 query 마다 screenshot embed)
    - stderr 에 validation 결과 (missing screenshot / missing checkpoint)

검증 룰 (validation):
    - 모든 done query 는 PNG 존재해야 함 (없으면 WARN)
    - verifier 점수가 있는 query 는 axes 7개 필수
    - report 의 per-query block 은 다음 5요소 필수: Query / Screenshot / Answer / Axes table / Verdict
"""
import json
import sys
import os
import glob
from pathlib import Path


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt_axes(axes: dict) -> str:
    """7축 점수 표 markdown."""
    keys = ["correctness", "completeness", "format", "backend", "visual", "memory", "latency"]
    labels = {
        "correctness": "정확성",
        "completeness": "완성도",
        "format": "형식",
        "backend": "백엔드",
        "visual": "화면",
        "memory": "메모리",
        "latency": "응답시간",
    }
    rows = ["| 축 | 점수 | 비고 |", "|---|---|---|"]
    for k in keys:
        if k not in axes:
            rows.append(f"| {labels[k]} | -/- | (미평가) |")
            continue
        a = axes[k]
        rows.append(f"| {labels[k]} | {a.get('score','?')}/{a.get('max','?')} | {a.get('note','')} |")
    return "\n".join(rows)


def truncate(text: str, limit: int = 600) -> str:
    if not text:
        return ""
    text = text.replace("\r", "")
    if len(text) > limit:
        return text[:limit].rstrip() + " ..."
    return text


def main():
    if len(sys.argv) < 2:
        print("Usage: gen_report.py <run-id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]
    base = Path(__file__).resolve().parent.parent
    run_dir = base / "runs" / run_id
    if not run_dir.is_dir():
        print(f"ERROR: run dir not found: {run_dir}", file=sys.stderr)
        sys.exit(2)

    memo_path = run_dir / "memory-snapshot.json"
    memo = load_json(memo_path) if memo_path.exists() else {"enabled": None, "count": 0, "items": []}

    checkpoint_files = sorted(
        f for f in run_dir.iterdir()
        if f.is_file() and f.suffix == ".json"
        and f.name[:3].isdigit() and "-" in f.name
    )

    if not checkpoint_files:
        print(f"WARN: no checkpoint JSON files in {run_dir}", file=sys.stderr)

    verifier_by_qid = {}
    for vf in run_dir.glob("verifier-*.json"):
        try:
            vdata = load_json(vf)
        except Exception as e:
            print(f"WARN: verifier load failed {vf}: {e}", file=sys.stderr)
            continue
        per_query = vdata.get("per_query", [])
        for pq in per_query:
            verifier_by_qid[pq["id"]] = pq

    cat_summary = {}
    queries_in_order = []
    issues = []

    for cf in checkpoint_files:
        try:
            qdata = load_json(cf)
        except Exception as e:
            print(f"WARN: checkpoint load failed {cf}: {e}", file=sys.stderr)
            continue
        qid = qdata.get("id", cf.stem)
        cat = qdata.get("category", "?")
        png_path = cf.with_suffix(".png")
        if not png_path.exists():
            issues.append(f"missing screenshot for {qid}: expected {png_path.name}")

        qdata["_idx"] = cf.stem.split("-")[0]
        qdata["_png"] = png_path.name if png_path.exists() else None
        qdata["_verifier"] = verifier_by_qid.get(qid, None)

        queries_in_order.append(qdata)
        cat_summary.setdefault(cat, []).append(qdata)

    cat_stats = {}
    grand = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "scores": []}
    for cat, items in cat_summary.items():
        stats = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "scores": []}
        for q in items:
            v = q.get("_verifier")
            if v:
                verdict = v.get("verdict", "?")
                if verdict in stats:
                    stats[verdict] += 1
                    grand[verdict] += 1
                if "score" in v:
                    stats["scores"].append(v["score"])
                    grand["scores"].append(v["score"])
        stats["avg"] = round(sum(stats["scores"]) / len(stats["scores"]), 1) if stats["scores"] else None
        cat_stats[cat] = stats
    grand["avg"] = round(sum(grand["scores"]) / len(grand["scores"]), 1) if grand["scores"] else None

    parts = []
    parts.append(f"# Polestar AI 평가 — run `{run_id}`\n")
    parts.append(f"- 총 query: {len(queries_in_order)}\n")
    parts.append(f"- 카테고리: {', '.join(sorted(cat_summary.keys()))}\n")
    parts.append("")

    parts.append("## 요약\n")
    parts.append("| 카테고리 | PASS | PARTIAL | FAIL | 평균 |")
    parts.append("|---|---|---|---|---|")
    for cat in sorted(cat_stats.keys()):
        s = cat_stats[cat]
        avg = s["avg"] if s["avg"] is not None else "-"
        parts.append(f"| {cat} | {s['PASS']} | {s['PARTIAL']} | {s['FAIL']} | {avg} |")
    g_avg = grand["avg"] if grand["avg"] is not None else "-"
    parts.append(f"| **합계** | **{grand['PASS']}** | **{grand['PARTIAL']}** | **{grand['FAIL']}** | **{g_avg}** |")
    parts.append("")

    parts.append("## 메모리 사전 점검\n")
    parts.append(f"- enabled: {memo.get('enabled')}")
    parts.append(f"- count: {memo.get('count', 0)}")
    parts.append("- items:")
    for it in memo.get("items", []):
        parts.append(f"  - {it.get('content', '')}  *(source: {it.get('source','?')})*")
    parts.append("")

    parts.append("---\n")
    parts.append("# 시나리오 별 상세 (evidence)\n")

    for cat in sorted(cat_summary.keys()):
        parts.append(f"## {cat}\n")
        for q in cat_summary[cat]:
            qid = q.get("id", "?")
            idx = q.get("_idx", "?")
            png = q.get("_png")
            verifier = q.get("_verifier")
            verdict = verifier["verdict"] if verifier else "(미평가)"
            score = verifier["score"] if verifier else "?"
            difficulty = ""
            for tag in ["easy", "medium", "hard"]:
                if tag in qid or f"-{tag[0]}" in qid:
                    difficulty = tag
                    break
            parts.append(f"### #{idx} {qid} ({difficulty}) — **{verdict}** ({score}/100)\n")

            query_text = q.get("query")
            if not query_text and "turns" in q:
                query_text = " → ".join(t.get("query", "") for t in q["turns"])
            parts.append(f"**Query**: `{query_text or '(unknown)'}`\n")

            if png:
                parts.append(f"![{qid}](./{png})\n")
            else:
                parts.append(f"⚠ screenshot 누락 ({qid})\n")

            answer = q.get("final_answer") or q.get("narrative_answer") or ""
            if answer:
                parts.append(f"**Answer**: {truncate(answer, 600)}\n")

            tp = q.get("tool_params")
            ut = q.get("ui_total")
            uti = q.get("ui_title")
            elapsed = q.get("elapsed_ms")
            meta_bits = []
            if tp:
                meta_bits.append(f"`tool_params`: `{json.dumps(tp, ensure_ascii=False)[:200]}`")
            if uti:
                meta_bits.append(f"`ui_title`: {uti}")
            if ut is not None:
                meta_bits.append(f"`ui_total`: {ut}")
            if elapsed is not None:
                meta_bits.append(f"`elapsed`: {round(elapsed/1000,1)}s")
            if meta_bits:
                parts.append(" · ".join(meta_bits) + "\n")

            if verifier:
                parts.append(fmt_axes(verifier.get("axes", {})) + "\n")
                vissues = verifier.get("issues", [])
                if vissues:
                    parts.append("**Issues**:")
                    for iss in vissues:
                        parts.append(f"- {iss}")
                    parts.append("")

            log_path = q.get("log_path")
            if log_path and (run_dir / log_path).exists() and (run_dir / log_path).stat().st_size > 0:
                with open(run_dir / log_path, encoding="utf-8", errors="replace") as f:
                    log_excerpt = f.read()[:1500]
                if log_excerpt.strip():
                    parts.append("**Backend log 발췌**:")
                    parts.append("```")
                    parts.append(log_excerpt)
                    parts.append("```\n")

            notes = q.get("notes", "")
            if notes:
                parts.append(f"**Notes**: {notes}\n")

            parts.append("---\n")

    parts.append("## 발견된 issue (Verifier 통합)\n")
    findings = []
    for vf in run_dir.glob("verifier-*.json"):
        try:
            vdata = load_json(vf)
            for kf in vdata.get("summary", {}).get("key_findings", []):
                findings.append(f"- [{vdata.get('category','?')}] {kf}")
        except Exception:
            pass
    if findings:
        parts.extend(findings)
    else:
        parts.append("- (verifier-*.json 의 key_findings 없음)")
    parts.append("")

    if issues:
        parts.append("\n## ⚠ Validation 경고\n")
        for w in issues:
            parts.append(f"- {w}")
        parts.append("")
        for w in issues:
            print(f"WARN: {w}", file=sys.stderr)

    parts.append("\n## 디렉토리\n")
    parts.append("```")
    parts.append(f"runs/{run_id}/")
    for f in sorted(run_dir.iterdir()):
        parts.append(f"├── {f.name}")
    parts.append("```")

    out = run_dir / "report.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"OK: wrote {out}")
    print(f"  queries: {len(queries_in_order)} | PASS {grand['PASS']} / PARTIAL {grand['PARTIAL']} / FAIL {grand['FAIL']} | avg {g_avg}")
    if issues:
        print(f"  warnings: {len(issues)}")


if __name__ == "__main__":
    main()
