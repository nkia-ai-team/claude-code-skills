#!/usr/bin/env python3
"""
memory-crud 카테고리의 baseline-aware auto cleanup.

사용:
    python3 scripts/memory_cleanup.py <run-id>

동작:
    1. runs/<run-id>/memory-snapshot-before.json 의 item ids 를 baseline 으로 로딩
    2. chrome MCP 가 아닌 host 에서 직접 chat-ap API 호출 — 단 cookie 가 필요해서
       이 script 는 [의도된 사용] 으로 run dir 안의 ai_session.json (선택) 또는
       Claude 가 chrome MCP 로 호출해야 함
    3. 현재 list 의 item ids 와 baseline diff 계산 → added_ids 모두 DELETE
    4. memoryEnabled 가 false 면 복원
    5. log runs/<run-id>/memory-crud-cleanup.json

★ 이 script 는 직접 fetch 못 함 (HttpOnly cookie). 실제 cleanup 은 Claude 가
chrome MCP evaluate_script 안에서 fetch 로 수행. 이 script 는 baseline diff 계산
+ cleanup plan 산출만 담당.
"""
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: memory_cleanup.py <run-id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]
    base = Path(__file__).resolve().parent.parent
    run_dir = base / "runs" / run_id
    if not run_dir.is_dir():
        print(f"ERROR: run dir not found: {run_dir}", file=sys.stderr)
        sys.exit(2)

    before_path = run_dir / "memory-snapshot-before.json"
    after_path = run_dir / "memory-snapshot-after.json"
    if not before_path.exists():
        print(f"ERROR: memory-snapshot-before.json not found in {run_dir}", file=sys.stderr)
        print("       memory-crud 카테고리는 시작 시 before snapshot 이 필수", file=sys.stderr)
        sys.exit(3)

    before = json.load(open(before_path))
    baseline_ids = {it["id"] for it in before.get("items", [])}
    baseline_enabled = before.get("enabled")

    cleanup_plan = {
        "baseline_ids": sorted(baseline_ids),
        "baseline_enabled": baseline_enabled,
        "added_ids_to_delete": [],
        "settings_to_restore": {},
        "note": "Claude 가 chrome MCP evaluate_script 로 이 plan 을 실행",
    }

    if after_path.exists():
        after = json.load(open(after_path))
        after_ids = {it["id"] for it in after.get("items", [])}
        cleanup_plan["added_ids_to_delete"] = sorted(after_ids - baseline_ids)
        if after.get("enabled") != baseline_enabled:
            cleanup_plan["settings_to_restore"]["memoryEnabled"] = baseline_enabled

    out = run_dir / "memory-crud-cleanup-plan.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cleanup_plan, f, ensure_ascii=False, indent=2)

    print(f"OK: cleanup plan {out}")
    print(f"  baseline: {len(baseline_ids)} item, enabled={baseline_enabled}")
    print(f"  to delete: {len(cleanup_plan['added_ids_to_delete'])} added item")
    if cleanup_plan["settings_to_restore"]:
        print(f"  to restore: {cleanup_plan['settings_to_restore']}")

    print("\n--- Claude 가 chrome MCP 에서 실행할 cleanup JS ---")
    js = "async () => {\n"
    js += "  const results = [];\n"
    for item_id in cleanup_plan["added_ids_to_delete"]:
        js += f'  results.push(await (await fetch("/api/chat-ap/memories/delete",{{method:"POST",credentials:"include",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{id:"{item_id}"}})}})).json());\n'
    if "memoryEnabled" in cleanup_plan["settings_to_restore"]:
        v = "true" if cleanup_plan["settings_to_restore"]["memoryEnabled"] else "false"
        js += f'  results.push(await (await fetch("/api/chat-ap/memories/setting/update",{{method:"POST",credentials:"include",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{memoryEnabled:{v}}})}})).json());\n'
    js += "  return results;\n"
    js += "}"
    print(js)


if __name__ == "__main__":
    main()
