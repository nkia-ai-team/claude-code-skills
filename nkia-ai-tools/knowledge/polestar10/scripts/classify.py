#!/usr/bin/env python3
"""classify.py — populate _classification.md.

Rules (locked; no interactive questions):
  1. Walk _staging/admin/*.md and _staging/user/*.md.
  2. For each file, pick a category by walking the RULE_TABLE top-to-bottom
     and taking the first whose any keyword matches either the original Korean
     filename stem OR the first ~4KB of the converted markdown body.
  3. If nothing matches, category = "etc".
  4. Slug = "<cat>-NNN" where NNN is a 3-digit ordinal per (type, category).
     (We deliberately do NOT try to romanize Korean — the ralph rules ban
     human judgment calls, and an ordinal slug is deterministic and reviewable.)

Writes:
  _classification.md — table with header rewritten:
      | original_filename | slug | category | type |
"""

from __future__ import annotations

import pathlib
import re
from collections import defaultdict

KB = pathlib.Path(__file__).resolve().parent.parent
STAGING = KB / "_staging"
CLASSIFY = KB / "_classification.md"

# Ordered by priority (first match wins).
RULE_TABLE: list[tuple[str, list[str]]] = [
    ("alert", ["알람", "이벤트", "수신자", "alert"]),
    ("perf", ["성능", "차트", "토폴로지", "이상", "감지"]),
    ("account", ["계정", "사용자", "권한", "2차인증", "담당자", "부서", "조직"]),
    ("network", ["NMS", "네트워크", "장비", "인터페이스", "라인"]),
    ("db", ["DPM", "MySQL", "CUBRID", "DB", "스키마", "인스턴스"]),
    ("k8s", [
        "쿠버네티스", "K8s", "k8s", "클러스터", "네임스페이스",
        "PV", "PVC", "StorageClass", "Pod", "디플로이먼트",
        "스테이트풀셋", "리플리카셋", "컨테이너", "컨피그맵", "인그레스",
    ]),
    ("system", ["라이선스", "업무시간", "휴일", "보고서", "룰체인", "시스템", "설정"]),
    ("agent-install", [
        "APM", "WPM", "KCM", "SMS", "Agent", "에이전트",
        "설치", "삭제", "패치", "AccessPoint", "AP", "기동", "중지",
        "사전설치", "사전환경", "서문", "부록", "POLESTAR10",
    ]),
]


def classify_one(stem: str, body_head: str) -> str:
    # Filename-first: polestar10 docs have descriptive Korean stems, so a
    # filename match is higher-signal than a body match. Only fall back to
    # body content when the filename has zero category-keyword matches.
    stem_low = stem.lower()
    for cat, kws in RULE_TABLE:
        for kw in kws:
            if kw.lower() in stem_low:
                return cat
    body_low = body_head.lower()
    for cat, kws in RULE_TABLE:
        for kw in kws:
            if kw.lower() in body_low:
                return cat
    return "etc"


def main() -> None:
    rows: list[tuple[str, str, str, str]] = []
    ordinals: dict[tuple[str, str], int] = defaultdict(int)

    for type_name in ("admin", "user"):
        d = STAGING / type_name
        if not d.is_dir():
            continue
        for md in sorted(d.glob("*.md")):
            stem = md.stem
            try:
                head = md.read_text(encoding="utf-8", errors="ignore")[:4096]
            except Exception:
                head = ""
            cat = classify_one(stem, head)
            ordinals[(type_name, cat)] += 1
            slug = f"{cat}-{ordinals[(type_name, cat)]:03d}"
            rows.append((stem + ".docx", slug, cat, type_name))

    lines = [
        "# polestar10 docx 분류표",
        "",
        "Story 2 에서 자동 채워짐. 분류는 scripts/classify.py 의 RULE_TABLE 규칙을 사용.",
        "",
        "| original_filename | slug | category | type |",
        "|---|---|---|---|",
    ]
    for orig, slug, cat, type_name in rows:
        safe_orig = orig.replace("|", "\\|")
        lines.append(f"| {safe_orig} | {slug} | {cat} | {type_name} |")

    CLASSIFY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # quick summary to stdout
    counter: dict[tuple[str, str], int] = defaultdict(int)
    for _, _, cat, type_name in rows:
        counter[(type_name, cat)] += 1
    print(f"classified {len(rows)} file(s).")
    for (type_name, cat), n in sorted(counter.items()):
        print(f"  {type_name:5s} {cat:15s} {n}")


if __name__ == "__main__":
    main()
