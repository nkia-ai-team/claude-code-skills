# Phase 12 — Closed-loop verify retry 루프

orchestrator-side 재시도 로직. testbed-verifier agent 는 단발 verdict 만 리턴 — 재시도 결정은 orchestrator 가 owns.

## 입력
- testbed_name (= app_subdir)
- 첫 attempt 의 시나리오 범위: `all` (전체)
- 재시도시 PASS 가 아닌 시나리오만 재실행 (PASS skip 으로 시간 절약)
- max_attempts=3

## 루프

```bash
ATTEMPT=1
MAX_ATTEMPTS=3
SCENARIOS_TO_VERIFY="all"

while [ "$ATTEMPT" -le "$MAX_ATTEMPTS" ]; do
  echo "[verify] attempt $ATTEMPT/$MAX_ATTEMPTS — scenarios=$SCENARIOS_TO_VERIFY"

  # Agent: testbed-verifier dispatch (verify-task.md 의 task spec)
  VERDICT=$(call testbed-verifier with task scenarios=$SCENARIOS_TO_VERIFY)

  OVERALL=$(jq -r '.outputs.overall' <<< "$VERDICT")
  if [ "$OVERALL" = "PASS" ]; then
    echo "[verify] PASS — finalize 진행"
    break
  fi
  if [ "$ATTEMPT" -eq "$MAX_ATTEMPTS" ]; then
    echo "[verify] max attempts 도달. PARTIAL/FAIL 결과로 finalize 진행."
    break
  fi

  # PARTIAL/FAIL → tune-alarms 재호출 (recommendations 기반)
  echo "[verify] FAIL/PARTIAL. testbed-tune-alarms 재호출"
  RECOMMENDATIONS=$(jq -r '.outputs.recommendations[]?' <<< "$VERDICT")
  call testbed-tune-alarms with $RECOMMENDATIONS

  # 다음 attempt 는 PASS 가 아닌 시나리오만 재실행 (시간 절약)
  SCENARIOS_TO_VERIFY=$(echo "$VERDICT" | jq -r '
    [ .outputs.scenarios[] | select(.verdict != "PASS") | .id ] | join(",")
  ')
  [ -z "$SCENARIOS_TO_VERIFY" ] && SCENARIOS_TO_VERIFY="all"   # safety fallback

  ATTEMPT=$((ATTEMPT+1))
done
```

각 attempt 의 verdict + 재튜닝 내역 → `runs/<RUN_ID>/verify.log` append.

## ⚠️ PASS skip 안전장치

한 시나리오의 cleanup 이 다른 시나리오에 부작용 (예: K3s pod 재기동으로 다른 시나리오의 메트릭 기준 변동) 이 있으면 skip 시 false-negative 가능.

다음 라운드에 의심 발생 시 `SCENARIOS_TO_VERIFY="all"` 강제 (전체 재실행) — 환경 변수 또는 인터뷰 옵션으로 노출.

## verdict 처리 매트릭스

| verdict | next_action | orchestrator 동작 |
|---|---|---|
| `PASS` (overall) | `proceed` | finalize 진행 |
| `PARTIAL` | `tune_and_retry` | tune-alarms recommendations 적용 → 다음 attempt |
| `FAIL` | `tune_and_retry` 또는 `user-decision` | recoverable 면 자동 retry, blocking 이면 사용자 prompt |
| `ERROR` (시나리오 자체 실패) | `user-decision` | rca-scenario-runner 도달성 점검 안내 |

## 재시도 한계 도달 후

3 attempts 가 모두 PASS 미달 → finalize 단계로 진입. report.md 에 "verify 미통과 — last verdict" 명시.

사용자에게 매뉴얼 점검 안내:
- expected_alarms 가 정확한지 (시나리오 yaml 의 expected_alarms vs 실제 발화 알람)
- 알람 정책의 임계치가 시나리오 강도와 매칭되는지
- 시나리오 trigger 자체가 작동하는지 (rca-scenario-runner 의 /api/scenarios/<id>/run 응답 확인)
