#!/usr/bin/env bash
# convert-docx.sh
#
# Batch convert admin/ + user/ docx manuals to markdown under _staging/.
#
# Usage:
#   scripts/convert-docx.sh [ADMIN_DOCX_DIR] [USER_DOCX_DIR]
#
# Defaults:
#   ADMIN_DOCX_DIR = /home/sjbang/dev/admin/docx
#   USER_DOCX_DIR  = /home/sjbang/dev/user/docx
#
# Behavior:
# - For each *.docx (excluding Office lock files ~$*.docx), runs pandoc with
#   -f docx -t gfm --wrap=none --markdown-headings=atx --extract-media=<imgdir>.
# - Writes .md to _staging/<type>/<slug>.md and images to
#   _staging/<type>/images/<slug>/.
# - <slug> here is a simple hash-free slug derived from the file stem: lower-cased
#   transliteration is NOT performed (Korean filenames are kept); spaces and
#   problematic characters are replaced with '-'. Final slugification into the
#   final manuals/ tree is handled by slugify-and-promote.sh.
# - Appends success/failure lines to _staging/_conversion-report.txt.
#
# Requirements: pandoc (>= 2.9), bash.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STAGING="$KB_DIR/_staging"
REPORT="$STAGING/_conversion-report.txt"

ADMIN_SRC="${1:-/home/sjbang/dev/admin/docx}"
USER_SRC="${2:-/home/sjbang/dev/user/docx}"

mkdir -p "$STAGING/admin" "$STAGING/user"
: > "$REPORT"

# pandoc >= 2.11 uses --markdown-headings=atx; 2.9.x uses --atx-headers.
# Pick whichever this install supports so the script is portable.
if pandoc --help 2>&1 | grep -q -- '--markdown-headings='; then
  ATX_OPT=(--markdown-headings=atx)
elif pandoc --help 2>&1 | grep -q -- '--atx-headers'; then
  ATX_OPT=(--atx-headers)
else
  ATX_OPT=()
fi

slugify_stem() {
  local stem="$1"
  stem="${stem// /-}"
  stem="${stem//\//-}"
  stem="${stem//\\/-}"
  stem="${stem//:/-}"
  stem="${stem//\*/-}"
  stem="${stem//\?/-}"
  stem="${stem//\"/-}"
  stem="${stem//</-}"
  stem="${stem//>/-}"
  stem="${stem//\|/-}"
  printf '%s' "$stem"
}

convert_one() {
  local src="$1"
  local type="$2"
  local base stem slug out imgdir
  base="$(basename "$src")"

  if [[ "$base" == ~\$* ]]; then
    return 0
  fi

  stem="${base%.docx}"
  slug="$(slugify_stem "$stem")"
  out="$STAGING/$type/$slug.md"
  imgdir="$STAGING/$type/images/$slug"
  mkdir -p "$(dirname "$out")" "$imgdir"

  if pandoc -f docx -t gfm \
      --wrap=none \
      "${ATX_OPT[@]}" \
      --extract-media="$imgdir" \
      -o "$out" "$src" 2>>"$REPORT"; then
    printf 'OK\t%s\t%s\n' "$type" "$base" >>"$REPORT"
  else
    printf 'FAIL\t%s\t%s\n' "$type" "$base" >>"$REPORT"
  fi
}

convert_dir() {
  local dir="$1"
  local type="$2"
  if [[ ! -d "$dir" ]]; then
    printf 'MISSING\t%s\t%s\n' "$type" "$dir" >>"$REPORT"
    return 0
  fi
  local f
  while IFS= read -r -d '' f; do
    convert_one "$f" "$type"
  done < <(find "$dir" -maxdepth 1 -type f -name '*.docx' -print0)
}

convert_dir "$ADMIN_SRC" admin
convert_dir "$USER_SRC" user

ok_count=$(grep -c '^OK' "$REPORT" 2>/dev/null || echo 0)
fail_count=$(grep -c '^FAIL' "$REPORT" 2>/dev/null || echo 0)
printf '\nSUMMARY\tOK=%s\tFAIL=%s\n' "$ok_count" "$fail_count" >>"$REPORT"
printf 'convert-docx.sh done: OK=%s FAIL=%s\nReport: %s\n' "$ok_count" "$fail_count" "$REPORT"
