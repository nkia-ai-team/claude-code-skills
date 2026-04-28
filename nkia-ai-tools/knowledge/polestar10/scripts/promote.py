#!/usr/bin/env python3
"""promote.py — promote one category from _staging/ into manuals/<type>/<cat>/.

Reads _classification.md, finds every row with the requested category, and for
each row:
  - moves _staging/<type>/<orig_stem>.md → manuals/<type>/<cat>/<slug>.md
  - moves _staging/<type>/images/<orig_stem>/ →
    manuals/<type>/<cat>/images/<slug>/
  - rewrites inline image references to './images/<slug>/...'
  - prepends a 6-key frontmatter block (menu_path, feature, admin_required,
    original_title, category, menu_path_verified)

Also (re)generates:
  - manuals/<type>/<cat>/00-toc-<cat>.md  (per-category TOC)
  - manuals/<type>/00-toc.md              (master TOC, category link upserted)

Appends per-category draft entries to REVIEW_NEEDED.md so the human reviewer
has the full menu_path draft list when toggling menu_path_verified.

Usage:
  scripts/promote.py <category>

The script is idempotent per (type, cat): rerunning it after edits will
overwrite the promoted md files from staging and regenerate the TOCs.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import sys
from collections import defaultdict

KB = pathlib.Path(__file__).resolve().parent.parent
STAGING = KB / "_staging"
MANUALS = KB / "manuals"
CLASSIFY = KB / "_classification.md"
REVIEW_NEEDED = KB / "REVIEW_NEEDED.md"

ROW_RE = re.compile(r"^\|\s*(?P<orig>[^|]+?)\s*\|\s*(?P<slug>[^|]+?)\s*\|\s*(?P<cat>[^|]+?)\s*\|\s*(?P<type>admin|user)\s*\|\s*$")
H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")
FRONTMATTER_START = "---"


def read_rows(cat_filter: str) -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for line in CLASSIFY.read_text(encoding="utf-8").splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        orig = m.group("orig")
        slug = m.group("slug")
        cat = m.group("cat")
        type_ = m.group("type")
        if cat != cat_filter:
            continue
        if orig in ("original_filename", "orig"):
            continue
        out.append((orig, slug, cat, type_))
    return out


def derive_menu_path(body: str, fallback: str) -> str:
    for line in body.splitlines():
        m = H1_RE.match(line)
        if m:
            title = m.group(1).strip()
            if title:
                return title
    return fallback


def derive_feature(body: str) -> str:
    # first non-empty, non-heading, non-image, non-comment paragraph after the
    # first H1 (or from the top if no H1).
    lines = body.splitlines()
    i = 0
    for idx, line in enumerate(lines):
        if H1_RE.match(line):
            i = idx + 1
            break
    while i < len(lines):
        s = lines[i].strip()
        i += 1
        if not s:
            continue
        if s.startswith("#"):
            continue
        if s.startswith("<!--"):
            continue
        if s.startswith("!["):
            continue
        if s.startswith("|") or s.startswith("---"):
            continue
        # collapse whitespace, trim length
        s = re.sub(r"\s+", " ", s)
        return s[:200]
    return "(본문 요약 미생성 — 사람 확인 필요)"


def strip_frontmatter(body: str) -> str:
    lines = body.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_START:
        return body
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_START:
            end = i
            break
    if end is None:
        return body
    return "\n".join(lines[end + 1 :])


def rewrite_image_refs(body: str, orig_stem: str, type_: str, slug: str) -> str:
    """Rewrite every image path that points into the staging tree so it reads
    './images/<slug>/...' relative to the final .md location.

    pandoc --extract-media produces URLs of the form
        <extract-dir>/media/<filename>
    where <extract-dir> was '_staging/<type>/images/<orig_stem>'. In the md
    text the URL may be:
      1) absolute: /home/.../_staging/<type>/images/<orig_stem>/media/...
      2) relative: _staging/<type>/images/<orig_stem>/media/...
      3) bare:     images/<orig_stem>/media/...
    and any of () [] in the URL get backslash-escaped by pandoc (markdown URL
    escape rules), so we must match both the escaped and unescaped forms.
    """
    escaped_stem = (
        orig_stem
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )
    variants = {orig_stem, escaped_stem}
    replacement = f"./images/{slug}/"
    for stem in variants:
        patterns = [
            re.compile(re.escape(str(STAGING / type_ / "images") + "/" + stem) + r"/"),
            re.compile(r"(?<![\w/])" + re.escape(f"_staging/{type_}/images/{stem}") + r"/"),
            re.compile(r"(?<![\w/])" + re.escape(f"images/{stem}") + r"/"),
        ]
        for pat in patterns:
            body = pat.sub(replacement, body)
    return body


def yaml_escape(v: str) -> str:
    # use double-quoted yaml; escape backslashes and double-quotes
    return v.replace("\\", "\\\\").replace('"', '\\"')


def promote(cat: str) -> None:
    rows = read_rows(cat)
    if not rows:
        print(f"no rows for category={cat}; nothing to do.")
        return

    drafts_by_type: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for orig, slug, _cat, type_ in rows:
        stem = orig[: -len(".docx")] if orig.endswith(".docx") else orig
        src_md = STAGING / type_ / f"{stem}.md"
        src_img_dir = STAGING / type_ / "images" / stem
        dst_dir = MANUALS / type_ / cat
        dst_img_dir = dst_dir / "images" / slug
        dst_md = dst_dir / f"{slug}.md"
        dst_dir.mkdir(parents=True, exist_ok=True)
        (dst_dir / "images").mkdir(parents=True, exist_ok=True)

        if not src_md.is_file():
            print(f"WARN: missing staging md {src_md}", file=sys.stderr)
            continue

        body = src_md.read_text(encoding="utf-8", errors="replace")
        body = strip_frontmatter(body)

        menu_path = derive_menu_path(body, fallback=stem)
        feature = derive_feature(body)

        if src_img_dir.is_dir():
            if dst_img_dir.exists():
                shutil.rmtree(dst_img_dir)
            shutil.copytree(src_img_dir, dst_img_dir)

        body = rewrite_image_refs(body, stem, type_, slug)

        admin_required = "true" if type_ == "admin" else "false"
        fm = [
            "---",
            f'menu_path: "{yaml_escape(menu_path)}"',
            f'feature: "{yaml_escape(feature)}"',
            f"admin_required: {admin_required}",
            f'original_title: "{yaml_escape(stem)}"',
            f"category: {cat}",
            "menu_path_verified: false",
            "---",
            "",
        ]
        dst_md.write_text("\n".join(fm) + body.lstrip("\n") + "\n", encoding="utf-8")
        drafts_by_type[type_].append((slug, menu_path, dst_md.relative_to(KB).as_posix()))

    # ---- per-category + master TOCs ----
    for type_ in ("admin", "user"):
        dir_ = MANUALS / type_ / cat
        if not dir_.is_dir():
            continue
        md_files = sorted(p for p in dir_.glob("*.md") if p.name != f"00-toc-{cat}.md")
        if not md_files:
            continue
        toc = dir_ / f"00-toc-{cat}.md"
        header = [
            f"# {cat} ({type_}) TOC",
            "",
            "| menu_path | feature | file | admin |",
            "|---|---|---|---|",
        ]
        body_lines: list[str] = []
        for p in md_files:
            mp = ""
            fe = ""
            ar = ""
            for ln in p.read_text(encoding="utf-8").splitlines()[:10]:
                if ln.startswith('menu_path: "'):
                    mp = ln[len('menu_path: "') : -1]
                elif ln.startswith('feature: "'):
                    fe = ln[len('feature: "') : -1]
                elif ln.startswith("admin_required:"):
                    ar = ln.split(":", 1)[1].strip()
            body_lines.append(
                f"| {mp.replace('|', chr(92)+'|')} | {fe.replace('|', chr(92)+'|')} | {p.name} | {ar} |"
            )
        toc.write_text("\n".join(header + body_lines) + "\n", encoding="utf-8")

        master = MANUALS / type_ / "00-toc.md"
        section_header = f"## {cat}"
        link_line = f"- [{cat}]({cat}/00-toc-{cat}.md)"
        existing = master.read_text(encoding="utf-8") if master.is_file() else f"# {type_} manuals master index\n"
        if section_header not in existing:
            if not existing.endswith("\n"):
                existing += "\n"
            existing += f"\n{section_header}\n{link_line}\n"
        elif link_line not in existing:
            existing += f"{link_line}\n"
        master.write_text(existing, encoding="utf-8")

    # ---- REVIEW_NEEDED.md append ----
    if REVIEW_NEEDED.is_file():
        text = REVIEW_NEEDED.read_text(encoding="utf-8")
    else:
        text = "# polestar10 지식베이스 — 사람 검토 필요 항목\n\n"

    section_tag = f"### {cat}"
    if section_tag not in text:
        lines = [f"\n{section_tag}", ""]
        for type_ in ("admin", "user"):
            drafts = drafts_by_type.get(type_, [])
            if not drafts:
                continue
            lines.append(f"**{type_}** ({len(drafts)} file(s)):")
            lines.append("")
            lines.append("| slug | menu_path (초안) | 경로 |")
            lines.append("|---|---|---|")
            for slug, mp, path in drafts:
                mp_safe = mp.replace("|", "\\|")
                lines.append(f"| {slug} | {mp_safe} | {path} |")
            lines.append("")
        lines.append("> 위 `menu_path` 는 pandoc 이 추출한 md 본문 H1 제목을 그대로 초안으로 옮긴 것입니다.")
        lines.append("> 사람이 polestar10 웹에서 대조 후 frontmatter 의 `menu_path_verified` 를 `true` 로 토글.")
        text = text.rstrip() + "\n" + "\n".join(lines) + "\n"
        REVIEW_NEEDED.write_text(text, encoding="utf-8")

    total = sum(len(v) for v in drafts_by_type.values())
    print(f"promoted {total} file(s) into category='{cat}'.")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: promote.py <category>", file=sys.stderr)
        sys.exit(2)
    promote(sys.argv[1])


if __name__ == "__main__":
    main()
