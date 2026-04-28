#!/usr/bin/env bash
# slugify-and-promote.sh
#
# Promote _staging/ md files for a single category into manuals/<type>/<cat>/.
# Reads the classification table from _classification.md to learn which files
# belong to which category, generates a romanized ASCII slug for each file,
# rewrites inline image paths to ./images/<slug>/..., and moves images into
# manuals/<type>/<cat>/images/<slug>/.
#
# Writes a frontmatter block with 6 mandatory keys:
#   menu_path, feature, admin_required, original_title, category, menu_path_verified
#
# Usage:
#   scripts/slugify-and-promote.sh <category>
#
# Requirements: bash, awk, sed, coreutils.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STAGING="$KB_DIR/_staging"
MANUALS="$KB_DIR/manuals"
CLASSIFY="$KB_DIR/_classification.md"

CAT="${1:-}"
if [[ -z "$CAT" ]]; then
  printf 'usage: %s <category>\n' "$0" >&2
  exit 2
fi

if [[ ! -f "$CLASSIFY" ]]; then
  printf 'missing %s\n' "$CLASSIFY" >&2
  exit 1
fi

# extract rows of the classification table matching this category
# expected format: | original_filename | slug | category | type |
mapfile -t ROWS < <(awk -F '|' -v cat="$CAT" '
  /^\|/ {
    # skip header separator lines
    gsub(/^ +| +$/, "", $2); gsub(/^ +| +$/, "", $3); gsub(/^ +| +$/, "", $4); gsub(/^ +| +$/, "", $5)
    if ($4 == cat && ($5 == "admin" || $5 == "user")) {
      print $2 "\t" $3 "\t" $4 "\t" $5
    }
  }
' "$CLASSIFY")

if [[ ${#ROWS[@]} -eq 0 ]]; then
  printf 'no rows for category=%s in %s (nothing to do)\n' "$CAT" "$CLASSIFY" >&2
  exit 0
fi

mkdir -p "$MANUALS/admin/$CAT/images" "$MANUALS/user/$CAT/images"

escape_sed() { printf '%s' "$1" | sed -e 's/[\/&]/\\&/g'; }

count_rows=0
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r orig slug cat_val type <<<"$row"
  [[ -z "$orig" || -z "$slug" || -z "$type" ]] && continue

  stem="${orig%.docx}"
  src_md="$STAGING/$type/$stem.md"
  src_img="$STAGING/$type/images/$stem"
  dst_dir="$MANUALS/$type/$CAT"
  dst_md="$dst_dir/$slug.md"
  dst_img="$dst_dir/images/$slug"

  if [[ ! -f "$src_md" ]]; then
    printf 'SKIP\tno staging md for %s (looked for %s)\n' "$orig" "$src_md" >&2
    continue
  fi

  mkdir -p "$dst_img"

  # derive menu_path from first ATX heading; feature from first non-empty paragraph
  menu_path="$(awk '
    /^# / { sub(/^# +/, ""); print; exit }
  ' "$src_md")"
  if [[ -z "$menu_path" ]]; then
    menu_path="$stem"
  fi

  feature="$(awk '
    BEGIN { found_heading = 0 }
    /^# / { found_heading = 1; next }
    found_heading && NF {
      # skip html comments, image-only lines
      if ($0 ~ /^<!--/) next
      if ($0 ~ /^!\[/) next
      print; exit
    }
  ' "$src_md")"
  if [[ -z "$feature" ]]; then
    feature="(본문 요약 미생성 — 사람 확인 필요)"
  fi
  # trim to 200 chars
  feature="${feature:0:200}"
  # escape yaml-unfriendly chars
  feature_yaml="${feature//\"/\\\"}"
  menu_path_yaml="${menu_path//\"/\\\"}"

  if [[ "$type" == "admin" ]]; then admin_required="true"; else admin_required="false"; fi

  # relocate images: copy tree
  if [[ -d "$src_img" ]]; then
    cp -r "$src_img"/. "$dst_img"/ 2>/dev/null || true
  fi

  # rewrite body: strip any pre-existing frontmatter from pandoc (rare) and
  # rewrite image paths from the _staging path into ./images/<slug>/...
  tmp_body="$(mktemp)"
  awk '
    BEGIN { skip=0 }
    NR==1 && $0=="---" { skip=1; next }
    skip==1 && $0=="---" { skip=0; next }
    skip==1 { next }
    { print }
  ' "$src_md" >"$tmp_body"

  # Replace absolute-like _staging image paths with relative ./images/<slug>/
  esc_src_img="$(escape_sed "$src_img")"
  esc_slug="$(escape_sed "$slug")"
  sed -i "s#${esc_src_img}/#./images/${esc_slug}/#g" "$tmp_body"
  # Also handle pandoc's relative '_staging/<type>/images/<stem>/...' form
  esc_rel_img="$(escape_sed "_staging/$type/images/$stem")"
  sed -i "s#${esc_rel_img}/#./images/${esc_slug}/#g" "$tmp_body"
  # And the form 'images/<stem>/...'
  esc_img_stem="$(escape_sed "images/$stem")"
  sed -i "s#(${esc_img_stem}/#(./images/${esc_slug}/#g" "$tmp_body"

  {
    printf -- '---\n'
    printf 'menu_path: "%s"\n' "$menu_path_yaml"
    printf 'feature: "%s"\n' "$feature_yaml"
    printf 'admin_required: %s\n' "$admin_required"
    printf 'original_title: "%s"\n' "$stem"
    printf 'category: %s\n' "$CAT"
    printf 'menu_path_verified: false\n'
    printf -- '---\n\n'
    cat "$tmp_body"
  } >"$dst_md"
  rm -f "$tmp_body"

  count_rows=$((count_rows + 1))
done

# ---- per-category TOC ----
for t in admin user; do
  dir="$MANUALS/$t/$CAT"
  [[ -d "$dir" ]] || continue
  # skip if no md files except TOC
  shopt -s nullglob
  files=("$dir"/*.md)
  shopt -u nullglob
  # filter out the TOC itself
  filtered=()
  for f in "${files[@]}"; do
    case "$(basename "$f")" in
      00-toc-*.md) continue ;;
      *) filtered+=("$f") ;;
    esac
  done
  [[ ${#filtered[@]} -eq 0 ]] && continue
  toc="$dir/00-toc-$CAT.md"
  {
    printf '# %s (%s) TOC\n\n' "$CAT" "$t"
    printf '| menu_path | feature | file | admin |\n'
    printf '|---|---|---|---|\n'
    for f in "${filtered[@]}"; do
      name="$(basename "$f")"
      mp="$(awk '/^menu_path:/ {sub(/^menu_path: *"?/,""); sub(/"? *$/,""); print; exit}' "$f")"
      fe="$(awk '/^feature:/ {sub(/^feature: *"?/,""); sub(/"? *$/,""); print; exit}' "$f")"
      ar="$(awk '/^admin_required:/ {print $2; exit}' "$f")"
      # escape pipes
      mp="${mp//|/\\|}"
      fe="${fe//|/\\|}"
      printf '| %s | %s | %s | %s |\n' "${mp:-?}" "${fe:-?}" "$name" "${ar:-?}"
    done
  } >"$toc"

  # ---- master TOC: ensure a section for this category ----
  master="$MANUALS/$t/00-toc.md"
  section_header="## $CAT"
  link_line="- [$CAT]($CAT/00-toc-$CAT.md)"
  if [[ ! -f "$master" ]]; then
    printf '# %s manuals master index\n\n' "$t" >"$master"
  fi
  if ! grep -qF "$section_header" "$master"; then
    printf '\n%s\n%s\n' "$section_header" "$link_line" >>"$master"
  elif ! grep -qF "$link_line" "$master"; then
    # header exists but link missing — append
    printf '%s\n' "$link_line" >>"$master"
  fi
done

printf 'promoted %s file(s) into category "%s".\n' "$count_rows" "$CAT"
