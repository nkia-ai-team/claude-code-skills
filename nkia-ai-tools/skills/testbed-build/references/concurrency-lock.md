# Concurrency Lock

같은 target_host + cluster_name 에 두 사용자가 동시에 testbed-build 를 돌리면 K3s/k3d
cluster / namespace / Ansible race 가 발생한다. flock 으로 가드한다.

## Lock 파일 위치

```
~/.testbed-build/.locks/<target_host>_<cluster_name>.lock
```

`<target_host>` = interview.target.host 의 IP 또는 hostname.
`<cluster_name>` = testbed 이름. 파일명 안전성을 위해 `/`, 공백, `:` 는 `_` 로 치환한다.
예: `203.0.113.109_plopvape-shop.lock`.

## Acquire

Phase 5 (interview 끝 + architecture 승인 후) 에서:

```bash
LOCK_DIR="$HOME/.testbed-build/.locks"
mkdir -p "$LOCK_DIR"
SAFE_TARGET=$(printf '%s' "$TARGET_HOST" | tr '/: ' '___')
SAFE_CLUSTER=$(printf '%s' "$CLUSTER_NAME" | tr '/: ' '___')
LOCK_FILE="$LOCK_DIR/${SAFE_TARGET}_${SAFE_CLUSTER}.lock"

# flock fd 9 사용 (관습)
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  # 누가 점유 중인지 안내
  HOLDER=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
  cat <<EOF
=== Lock 충돌 ===

타겟 $TARGET_HOST / cluster $CLUSTER_NAME 에 이미 진행 중인 run 이 있습니다.
Lock holder: $HOLDER

조치:
  1. 다른 사용자/세션이 진행 중이면 기다리세요
  2. 비정상 종료된 lock 이면 수동 정리:
     rm "$LOCK_FILE"
  3. 다른 target 으로 진행하려면 인터뷰 다시 시작

EOF
  exit 1
fi

# 본인 정보 lock 파일에 기록 (디버깅 + 다음 사용자 안내)
echo "run_id=$RUN_ID pid=$$ user=$(whoami) host=$(hostname) started=$(date -Iseconds)" > "$LOCK_FILE"

# manifest 갱신
update_manifest_phase "lock_acquired" "completed"
```

## Release

`cleanup` 또는 fatal exit:

```bash
release_lock() {
  flock -u 9 2>/dev/null
  exec 9>&-
  rm -f "$LOCK_FILE"
}

trap release_lock EXIT
```

스크립트 내부에서 명시적으로 호출:
```bash
# cleanup 정상 완료 시
release_lock
```

비정상 종료 (Ctrl+C / SIGKILL) 시 trap 으로 자동 release. 단 SIGKILL 은 못 잡음 → lock 파일 잔존 가능성. 사용자가 "비정상 종료된 lock" 임을 안내받고 수동 정리 가능 (위 사용자 prompt 의 조치 2).

## 만료 처리 (선택)

old lock 자동 reclaim:
- lock 파일의 mtime 이 30분 전 + lock 파일에 기록된 pid 가 살아있지 않으면
- 자동 reclaim + 안내 ("이전 run 이 비정상 종료되었습니다. lock reclaim.")

```bash
if [ -f "$LOCK_FILE" ] && ! flock -n 9 9>"$LOCK_FILE"; then
  # 점유 중. mtime + pid 검사
  HOLDER_PID=$(grep -oP 'pid=\K\d+' "$LOCK_FILE" 2>/dev/null)
  LOCK_AGE_MIN=$(( ( $(date +%s) - $(stat -c %Y "$LOCK_FILE") ) / 60 ))
  if [ "$LOCK_AGE_MIN" -gt 30 ] && [ -n "$HOLDER_PID" ] && ! kill -0 "$HOLDER_PID" 2>/dev/null; then
    echo "이전 lock 만료 (${LOCK_AGE_MIN}분 전, holder pid=$HOLDER_PID 사라짐). reclaim."
    rm -f "$LOCK_FILE"
    exec 9>"$LOCK_FILE"
    flock -n 9
  fi
fi
```

## 단일 사용자 / 단일 머신 가정 — 한계

본 lock 은 같은 controller 머신 안의 다중 호출만 가드. 다른 머신에서 같은 target 을 동시에 건드리면 못 막음. 그 케이스는 ansible 자체의 K8s/Polestar10 idempotency 에 의존.

## Lock 위치 변경 (선택)

별도 컨트롤러를 여러 사람이 돌릴 때 — target 호스트의 `/var/run/testbed-build/<target>.lock` 으로 SSH 통해 acquire 하는 방안. 본 세션 구현 안 함.
