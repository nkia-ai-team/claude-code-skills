#!/usr/bin/env python3
"""build-validation.py — populate VALIDATION.md with automatic checks.

Section 1 (auto-verified by ralph):
  1.1  per-(type,cat) md count vs _classification.md expectation
  1.2  per-md frontmatter schema check (6 required keys)
  1.3  per-agent install-spec.yaml schema check

Section 2 (human work after ralph):
  2.1  table of 20 representative questions (answer cells left as _미작성_)
  2.2  pointer to REVIEW_NEEDED.md for menu_path verification
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
from collections import defaultdict

KB = pathlib.Path(__file__).resolve().parent.parent
MANUALS = KB / "manuals"
AGENTS = KB / "agents"
CLASSIFY = KB / "_classification.md"
OUT = KB / "VALIDATION.md"

ROW_RE = re.compile(r"^\|\s*(?P<orig>[^|]+?)\s*\|\s*(?P<slug>[^|]+?)\s*\|\s*(?P<cat>[^|]+?)\s*\|\s*(?P<type>admin|user)\s*\|\s*$")
FRONT_KEYS = ["menu_path", "feature", "admin_required", "original_title", "category", "menu_path_verified"]
METHOD_ENUM = {"native", "qemu-emulation", "cross-build"}

QUESTIONS = [
    "개별 알람 정책은 어떻게 추가해?",
    "공통 알람 정책과 개별 알람 정책의 차이는?",
    "서비스 그룹 생성 절차?",
    "담당자 권한 부여 메뉴?",
    "NMS에서 네트워크 장비 등록?",
    "DPM에서 MySQL 인스턴스 등록?",
    "APM Java Agent 설치 순서?",
    "WPM Agent 설치 시 사전 조건?",
    "KCM Agent를 ARM 서버에 설치하려면?",
    "SMS Agent가 ARM에서도 동작하나?",
    "알람 수신자 그룹 설정?",
    "성능 이상 감지 정책 생성?",
    "토폴로지 맵 뷰어 접근?",
    "보고서 템플릿 관리?",
    "라이선스 관리 메뉴?",
    "사용자 2차 인증 설정?",
    "업무시간/휴일 설정은 어디서?",
    "로그 감시 정책 등록?",
    "프로세스 감시 설정?",
    "파일 감시 설정?",
]


def read_classification() -> dict[tuple[str, str], int]:
    expected: dict[tuple[str, str], int] = defaultdict(int)
    for line in CLASSIFY.read_text(encoding="utf-8").splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        expected[(m.group("type"), m.group("cat"))] += 1
    return expected


def count_actual() -> dict[tuple[str, str], int]:
    actual: dict[tuple[str, str], int] = defaultdict(int)
    for type_dir in MANUALS.iterdir():
        if not type_dir.is_dir():
            continue
        for cat_dir in type_dir.iterdir():
            if not cat_dir.is_dir():
                continue
            n = sum(
                1
                for f in cat_dir.glob("*.md")
                if f.name != f"00-toc-{cat_dir.name}.md"
            )
            if n:
                actual[(type_dir.name, cat_dir.name)] = n
    return actual


def frontmatter_ok(md: pathlib.Path) -> bool:
    head = md.read_text(encoding="utf-8", errors="ignore").splitlines()[:10]
    seen = {k: False for k in FRONT_KEYS}
    for line in head:
        for k in FRONT_KEYS:
            if line.startswith(k + ":"):
                seen[k] = True
    return all(seen.values())


def yq_get(path: pathlib.Path, expr: str) -> str:
    r = subprocess.run(
        ["yq", "e", expr, str(path)], capture_output=True, text=True, check=False
    )
    return r.stdout.strip()


def check_agent(agent: str) -> tuple[bool, bool, bool]:
    """Return (yq_parses, has_5_keys, arch_methods_valid)."""
    spec = AGENTS / agent / "install-spec.yaml"
    if not spec.is_file():
        return (False, False, False)
    parse_ok = yq_get(spec, "type") in {"!!map", "!!seq", "map"}
    keys = {s.strip() for s in yq_get(spec, "keys | .[]").splitlines() if s.strip()}
    required = {"agent", "versions", "arch_support", "detection_command", "prerequisites"}
    keys_ok = required.issubset(keys)
    amd = yq_get(spec, ".arch_support.amd64.method")
    arm = yq_get(spec, ".arch_support.arm64.method")
    methods_ok = amd in METHOD_ENUM and arm in METHOD_ENUM
    return (parse_ok, keys_ok, methods_ok)


def main() -> None:
    expected = read_classification()
    actual = count_actual()

    lines: list[str] = []
    lines.append("# polestar10 지식베이스 검증")
    lines.append("")
    lines.append("## 1. 자동 검증 (ralph 완료)")
    lines.append("")
    lines.append("### 1.1 파일 수 집계")
    lines.append("")
    lines.append("| type | category | md 개수 | 분류표 기대값 | 일치 |")
    lines.append("|---|---|---|---|---|")
    all_keys = sorted(set(expected) | set(actual))
    count_mismatches = 0
    for key in all_keys:
        t, c = key
        exp = expected.get(key, 0)
        act = actual.get(key, 0)
        match = "✓" if exp == act else "✗"
        if exp != act:
            count_mismatches += 1
        lines.append(f"| {t} | {c} | {act} | {exp} | {match} |")
    lines.append("")
    lines.append(f"불일치 행 수: **{count_mismatches}**")
    lines.append("")

    lines.append("### 1.2 frontmatter 스키마")
    lines.append("")
    lines.append("| 파일 | 6개 필수 키 전부 존재 |")
    lines.append("|---|---|")
    total_md = 0
    fm_pass = 0
    fm_fail_files: list[str] = []
    for type_dir in sorted(p for p in MANUALS.iterdir() if p.is_dir()):
        for cat_dir in sorted(p for p in type_dir.iterdir() if p.is_dir()):
            for md in sorted(cat_dir.glob("*.md")):
                if md.name == f"00-toc-{cat_dir.name}.md":
                    continue
                total_md += 1
                if frontmatter_ok(md):
                    fm_pass += 1
                else:
                    fm_fail_files.append(md.relative_to(KB).as_posix())
    if total_md == fm_pass:
        lines.append(f"| (전체 {total_md} 개) | ✓ |")
    else:
        for f in fm_fail_files:
            lines.append(f"| {f} | ✗ |")
        lines.append(f"| (pass {fm_pass}/{total_md}) | — |")
    lines.append("")
    lines.append(f"frontmatter 통과: **{fm_pass} / {total_md}**")
    lines.append("")

    lines.append("### 1.3 에이전트 install-spec 스키마")
    lines.append("")
    lines.append("| agent | yq 파싱 | 필수 키 5개 | amd64/arm64 method 유효 |")
    lines.append("|---|---|---|---|")
    all_agents_ok = True
    for agent in ("wpm", "apm", "kcm", "sms"):
        parse_ok, keys_ok, methods_ok = check_agent(agent)
        row_ok = parse_ok and keys_ok and methods_ok
        if not row_ok:
            all_agents_ok = False
        p = "✓" if parse_ok else "✗"
        k = "✓" if keys_ok else "✗"
        m = "✓" if methods_ok else "✗"
        lines.append(f"| {agent} | {p} | {k} | {m} |")
    lines.append("")

    lines.append("## 2. 사람 확인 필요 (ralph 범위 밖)")
    lines.append("")
    lines.append("> polestar10 웹 화면 대조 필요. ralph 종료 후 별도 세션에서 사용자가 채움.")
    lines.append("")
    lines.append("### 2.1 대표 질문 세트 (20개)")
    lines.append("")
    lines.append("| # | 질문 | expert 답변(초안) | 실제 웹 확인 | 비고 |")
    lines.append("|---|---|---|---|---|")
    for i, q in enumerate(QUESTIONS, start=1):
        lines.append(f"| {i} | {q} | _미작성_ | _미확인_ |  |")
    lines.append("")
    lines.append("### 2.2 menu_path 배치 검수")
    lines.append("")
    lines.append("> 카테고리별 `menu_path_verified: false` 인 항목 사람이 웹에서 대조 후 `true` 로 토글.")
    lines.append("> 상세 목록은 `REVIEW_NEEDED.md` 참조.")
    lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # summary to stdout + non-zero exit on auto-check failure
    print(f"total md={total_md}, frontmatter pass={fm_pass}")
    print(f"classification mismatches={count_mismatches}")
    print(f"agents all_ok={all_agents_ok}")
    if count_mismatches or fm_pass != total_md or not all_agents_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
