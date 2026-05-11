# Sub-agent verdict JSON 표준

testbed-build orchestrator 와 모든 sub-agent (testbed-engineer / testbed-deployer /
testbed-tuner / testbed-verifier) 사이의 통신 계약. `phase` 값은
[phase-contract.md](phase-contract.md) 의 canonical `phase_id` 를 사용한다.

## 디자인 원칙

1. **raw 데이터 격리** — verdict JSON 의 어느 필드에도 raw 로그 / raw 시계열 / API 응답 본문 dump X
2. **summary first** — 80자 이내 한 줄 요약 필수 (LLM 이 next phase 결정 시 핵심 신호)
3. **structured outputs** — phase 별 후속 phase 가 사용할 구조화 데이터만 (예: scenario_hints / policy_yaml / resource_ids)
4. **errors[] 표준 5필드** — role/task / fatal_msg / cause / fix / severity
5. **next_action 명시** — orchestrator 가 분기 판단할 때 사용

## 표준 스키마

```json
{
  "phase": "<phase_id from phase-contract.md>",
  "verdict": "ok|warn|fail|skipped",
  "summary": "<한 줄, 80자 이내>",
  "outputs": { /* phase-specific 구조 */ },
  "errors": [
    {
      "role": "<ansible role / API endpoint / 등>",
      "task": "<task 또는 단계 이름>",
      "fatal_msg": "<5~10줄 인용>",
      "cause": "<한 줄, 80자 이내>",
      "fix": "<bash 명령 / 매뉴얼 링크 / 사용자 결정>",
      "severity": "blocking|recoverable",
      "pattern_matched": "<known 패턴 키 또는 'unknown'>"
    }
  ],
  "next_action": "proceed|warn|retry|user-decision|dispatch_<sub-skill>"
}
```

## verdict 값 의미

| verdict | next_action default | orchestrator 동작 |
|---|---|---|
| `ok` | `proceed` | manifest phase=completed → 다음 phase |
| `warn` | `proceed` | manifest phase=completed_with_warnings → 다음 phase + 보고서 표시 |
| `fail` (severity=recoverable) | `retry` | 사용자 prompt: "fix 적용 후 재시도?" → max 2 |
| `fail` (severity=blocking) | `user-decision` | 사용자 결정 필수, manifest phase=failed |
| `skipped` | `proceed` 또는 `user-decision` | 사전 조건 미충족 (조건부 phase 의 정상 동작) |

## phase 별 outputs 스키마

### `services_author` — testbed-engineer

```json
{
  "phase": "services_author",
  "outputs": {
    "testbed_name": "core-banking",
    "subdir_created": "<paths.testbed_services_repo>/core-banking",
    "services_created": ["account", "transfer", "ledger", "audit"],
    "files_count": 47,
    "build_passed": true,
    "build_warnings": 0,
    "branch": "feat/core-banking-scaffold",
    "pr_url": "https://github.com/nkia-ai-team/testbed-services/pull/12",
    "scenario_hints": {
      "lock_table": "accounts",
      "lock_endpoint": "/api/accounts/{id}",
      "external_endpoint": "/api/transfer",
      "external_container": "external-pg-mock",
      "primary_load_endpoint": "/api/transfer"
    }
  }
}
```

`scenario_hints` 는 `generate_scenarios` 가 변수 매핑에 사용.

### `ansible_deploy` — testbed-deployer

```json
{
  "phase": "ansible_deploy",
  "outputs": {
    "ansible_rc": 0,
    "play_recap": {"ok": 42, "changed": 15, "unreachable": 0, "failed": 0, "skipped": 3},
    "duration_sec": 873,
    "log_path": "/tmp/testbed-build/<run_id>/deploy.log"
  }
}
```

raw 로그는 `outputs.log_path` 에만 보존 (parent verdict 에 인용 X).

### `tune_alarms` — testbed-tuner

```json
{
  "phase": "tune_alarms",
  "outputs": {
    "policy_yaml": "<full yaml string>",
    "summary_table": [
      {"domain": "apm", "resource": "order", "metric": "AvgResponseTime",
       "current": "LEVEL3=5s", "recommended": "LEVEL3=3s", "reason": "p99=1.4s, 결제 SLA"}
    ],
    "stats_by_resource": {
      "order": {"AvgResponseTime": {"p50": 320, "p95": 820, "p99": 1400}}
    },
    "metrics_collected": 18,
    "policies_recommended": 4
  }
}
```

raw 시계열 (수천 datapoint) 은 agent 안에서만 머물고 verdict 에 X.

### `verify` — testbed-verifier

```json
{
  "phase": "verify",
  "outputs": {
    "overall": "PASS|PARTIAL|FAIL|ERROR",
    "scenarios": [
      {"id": "01", "verdict": "PASS|PARTIAL|FAIL",
       "expected": ["DPM lock wait", ...],
       "fired": ["DPM lock wait", ...],
       "missed": [],
       "spurious": []}
    ],
    "recommendations": [
      "DPM lock wait LEVEL3 30 → 20 (현재 임계치 너무 높음)",
      "..."
    ]
  }
}
```

`recommendations[]` 는 orchestrator 가 testbed-tune-alarms 재호출 결정 시 사용.

## errors[] 구조 (4 sub-agent 공통)

각 fatal 마다 한 entry. 예시:

```json
{
  "role": "agent-kcm",
  "task": "Clone lucida-kcmagent",
  "fatal_msg": "fatal: [arm64-target]: FAILED! => {\"changed\": false, \"msg\": \"git clone failed: 401 Unauthorized\"}",
  "cause": "ARM KCM source-build 시 git clone 인증 실패 — kcm_source_repo 의 PAT 만료",
  "fix": "사용자에게 GitLab PAT 재발급 prompt + bootstrap.yaml 의 git.pat_file 갱신",
  "severity": "blocking",
  "pattern_matched": "kcm-source-auth-failed"
}
```

`fatal_msg` 는 5~10줄 한정. 그 이상은 outputs.log_path 로.

## raw 데이터 격리 룰 (4 agent 공통 강제)

### ❌ 절대 금지
- raw stdout / stderr 전체 dump
- raw 시계열 (timestamps[] / values[]) 배열 전체
- API 응답 본문 raw JSON
- 100자 넘는 단일 문자열 인용 (`fatal_msg` 5~10줄 예외)

### ✅ 권장
- 통계로 환원 (count / p50 / p95 / p99 / max)
- 분류로 환원 (failed=N, recovered=M)
- 경로로 보존 (`outputs.log_path`, `outputs.metrics_snapshot_path`)
- 5~10줄 인용으로 제한 (errors[].fatal_msg)

## next_action 매트릭스

| next_action | 의미 | orchestrator 분기 |
|---|---|---|
| `proceed` | 다음 phase 진행 | manifest 갱신 + 다음 phase dispatch |
| `warn` | 진행하되 보고서 명시 | manifest=completed_with_warnings + 다음 phase |
| `retry` | 같은 phase 재실행 | retry counter ++ 후 동일 dispatch (max 2) |
| `user-decision` | 사용자 결정 필수 | AskUserQuestion 카드 또는 자유 prompt |
| `dispatch_register_scenario_2` | 후속 sub-skill 호출 | testbed-polestar10-register 시나리오 2 dispatch |
| `dispatch_tune_and_retry` | tune-alarms → 다시 verify | recommendations 적용 → `verify` 재진입 |

## 멱등성 + 재시도 룰

- 모든 sub-agent 는 **단발 verdict** — 재시도 루프는 orchestrator owns
- 재시도 시 같은 입력으로 호출 OK (각 agent 가 자체 멱등성 보장)
- recoverable 는 자동 retry max 2회, blocking 은 자동 retry X (사용자 prompt)

## verdict 검증 체크리스트 (orchestrator 측)

dispatch 후 verdict 받자마자:

```bash
# 1. 필수 필드 존재 확인
jq -e '.phase, .verdict, .summary, .next_action' <<< "$VERDICT_JSON" >/dev/null \
  || { echo "FATAL: invalid verdict schema"; exit 1; }

# 2. verdict 값 enum 검증
VAL=$(jq -r '.verdict' <<< "$VERDICT_JSON")
[[ "$VAL" =~ ^(ok|warn|fail|skipped)$ ]] \
  || { echo "FATAL: invalid verdict value: $VAL"; exit 1; }

# 3. raw 데이터 누출 검사 (heuristic)
if jq -e '.outputs | tostring | length > 50000' <<< "$VERDICT_JSON" >/dev/null; then
  echo "WARN: outputs > 50KB. raw 데이터 누출 의심. log_path 사용 권고."
fi
```

## 디자인 근거

본 표준은 [Anthropic Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) + [Equipping agents for the real world](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) 의 orchestrator-worker 패턴 적용. 무거운 raw 데이터를 sub-agent fork context 에 격리하고 parent 는 verdict JSON 만 받아 next phase 결정.

sub-agent 격리로 각 phase 의 verdict 가 ~1KB 수준으로 일정 → orchestrator context 가 `verify` 까지 가도 여유.
