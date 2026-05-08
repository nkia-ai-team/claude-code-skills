# Phase Checkpoint + Resume

## manifest.yaml 운용

매 phase 진입/완료 시 `runs/<RUN_ID>/manifest.yaml` 갱신. resume 시 이 파일이 SOT.
phase id / 상태 enum 은 [phase-contract.md](phase-contract.md) 를 따른다.

### Phase 상태

- `pending` — 아직 시작 X (default)
- `in_progress` — 시작했으나 미완 (cancel/실패 시 잔존)
- `completed` — 정상 완료
- `completed_with_warnings` — 경고는 있으나 다음 phase 진행 가능
- `skipped` — 조건부 phase 의 정상 skip
- `failed` — phase 안에서 fatal error. resume 시 재시도 또는 사용자 개입 필요
- `finalized_partial` — verify PASS 전 보고서 작성 선택

### 갱신 시점

```
phase X 진입 → manifest.current_phase = X + manifest.phases.X.status = "in_progress" + last_updated_at = now → 저장
phase X 끝 (성공) → manifest.phases.X.status = "completed" + completed_at = now → 저장
phase X 끝 (skip) → manifest.phases.X.status = "skipped" + completed_at = now → 저장
phase X 끝 (실패) → manifest.phases.X.status = "failed" + last_error = "<msg>" → 저장
```

원자적 저장: `mv manifest.yaml.tmp manifest.yaml` 패턴 (부분 쓰기 방지).

## Resume 진입 흐름

```bash
# testbed-build 진입 시
RUNS_DIR="$HOME/.testbed-build/runs"
INCOMPLETE=()
for run in "$RUNS_DIR"/*/; do
  rid=$(basename "$run")
  manifest="$run/manifest.yaml"
  [ -f "$manifest" ] || continue
  finalize=$(yq '.phases.finalize.status // .phases.finalize' "$manifest")
  if [ "$finalize" != "completed" ] && [ "$finalize" != "finalized_partial" ]; then
    INCOMPLETE+=("$rid")
  fi
done

if [ ${#INCOMPLETE[@]} -eq 0 ]; then
  RUN_ID=$(date +%Y%m%d-%H%M%S)
  init_new_manifest
else
  prompt_user_for_resume "${INCOMPLETE[@]}"
fi
```

### 사용자 prompt

```
=== 미완 run 발견 ===

1) 2026-04-30-153022 (plopvape-shop, target=203.0.113.109)
   - 시작: 2026-04-30 15:30:22
   - 마지막 갱신: 2026-04-30 15:48:11
   - 미완 phase: ansible_deploy (in_progress)
   - last_error: <none>

2) 2026-04-29-180012 (core-banking, target=...)
   - ...

선택:
  [1-N] 해당 run resume
  [n]   새 run 시작 (기존 미완은 보존)
  [d-N] 미완 run 삭제 + 새 run 시작
  [q]   종료
```

## Resume 룰 — phase 별

### `bootstrap`, `interview`
- completed 면 skip
- in_progress 또는 failed 면 처음부터 (인터뷰 답 다시 받음. 단 슬롯 캐시는 살아있음)

### `precheck`
- completed 면 skip
- 그 외 → 다시 실행 (네트워크 transient 일 수 있음)

### `architecture` + `user_approval`
- completed 면 skip (architecture.md 도 보존)
- in_progress 면 architecture.md 다시 작성 + 사용자에게 다시 prompt
- 사용자 승인 후만 next phase

### `existing_testbed_detect`
- completed 또는 skipped 면 skip
- failed 면 다시 감지

### `lock_acquired`
- 늘 다시 시도 (resume 시점에 lock 풀려있을 수 있음)
- 이미 다른 run 이 lock 점유 중이면 fail

### `services_author`
- completed 또는 skipped 면 skip
- in_progress 또는 failed 면 testbed-services 디렉토리/branch 상태를 확인한 뒤 같은 task 로 재호출

### `inventory_generated`
- completed 면 skip (inventory.yml 보존)
- 그 외 다시 작성 (멱등)

### `ansible_deploy`
- **항상 ansible-playbook 다시 호출** (Ansible 자체 idempotent. 이미 깔린 부분은 changed=0)
- 단 deploy.log 는 새 파일 (timestamp suffix) 또는 append

### `sanity_check`
- completed 면 skip
- 그 외 다시 실행. 실패 시 `ansible_deploy` 부터 resume 권고

### `polestar10_register`
- completed 면 skip
- in_progress / failed 면 다시 (testbed-polestar10-register 가 이미 등록된 자원은 errorCode 기반으로 skip)

### `generate_scenarios`
- completed 면 skip
- 다시 호출 시 service-spec.yaml 의 기존 entry 와 새 entry 충돌 검사. id 중복이면 사용자 prompt.

### `tune_alarms`
- completed 면 skip
- 다시 호출 시 polestar10 의 기존 정책 보고 변경 사항 prompt

### `verify`
- completed (PASS) 면 skip
- in_progress 면 verify.log 의 attempt 누적 그대로 + 다음 attempt 부터 재개
- failed (max_attempts 도달) 면 사용자 prompt: "수동 검토 후 force-pass? 또는 다시 시도?"

### `finalize`
- 늘 다시 (보고서 다시 작성, 멱등)

## 자동 cleanup 룰

`cleanup` 진입 시:
- finalize=completed → safe 정리 (run dir 삭제, report 영구 보존)
- finalize=finalized_partial → safe 정리 전 사용자 확인. 기본은 run dir 보존
- finalize=failed → 보존
- 사용자 cancel (모든 phase 가 in_progress 또는 pending) → 보존 + 안내

## 부분 실패 케이스 시나리오

### Case 1: ansible-playbook 도중 SSH 끊김
- phases.ansible_deploy.status = in_progress
- last_error = "ansible: timeout / SSH connection lost"
- resume → 사용자에게 "ansible 재실행? deploy.log 확인 권고" → yes 시 다시 site.yml 호출

### Case 2: polestar10_register 중 Polestar10 5xx
- phases.polestar10_register.status = failed
- last_error = "polestar10 API 5xx for /api/sms/standby-hosts/register"
- resume → ask-polestar10 호출 안내 + 재시도 prompt

### Case 3: verify max_attempts 도달
- phases.verify.status = failed
- verify_attempts = [{n:1, PARTIAL}, {n:2, PARTIAL}, {n:3, PARTIAL}]
- resume → "max attempts. 시나리오 부하 강화 또는 임계치 수동 조정 권고. force-finalize? [y/N]"

## manifest 손상 감지

manifest.yaml 이 corrupt (yaml parse error) 또는 일부 필드 누락:
- 백업 (`manifest.yaml.corrupt`) + 빈 manifest 새로 작성
- 사용자에게 "manifest 손상. 새 run 으로 시작 권고" 안내
