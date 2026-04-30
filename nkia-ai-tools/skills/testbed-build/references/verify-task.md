# Verify Task — testbed-verifier 에 넘기는 spec

testbed-build Phase 11 closed-loop 의 단발 호출 task.

## Agent 호출 prompt 템플릿

오케스트레이터가 다음 string 을 substitution 하여 testbed-verifier agent 에 prompt:

```
task: scenario-verification

context:
  testbed_name: {{TESTBED_NAME}}
  scenario_runner_base: {{SCENARIO_RUNNER_BASE}}     # http://192.168.200.109:8091
  polestar10_base: {{POLESTAR10_BASE_URL}}
  polestar10_cookie_jar: {{COOKIE_JAR}}              # ~/.polestar10/cookie.jar 또는 동등 경로
  scenarios_to_verify: {{SCENARIO_IDS}}              # ["01", "02", "03", "04"] 또는 "all"
  attempt_n: {{ATTEMPT_N}}                            # 1, 2, 3
  previous_verdict: {{PREVIOUS_VERDICT_JSON}}        # attempt 1 일 땐 null

요구:
  - 각 시나리오 1회 실행 (rca-scenario-runner POST /api/scenarios/<id>/run)
  - 실행 중 + 종료 후 90초 buffer Polestar10 알람 history 조회
  - expected_alarms vs 실제 발화 매칭 (이름 fuzzy + 자원 + severity LEVEL2+ + time window)
  - cleanup 호출 (POST /api/scenarios/<id>/cleanup)
  - 단발 verdict JSON 반환 (overall + scenarios[] + recommendations[])

  재시도 루프 X. 단 1 round.

  attempt_n > 1 이면 previous_verdict 의 missed/spurious 보고 매칭 룰 살짝 보강 가능
  (예: 이전에 missed 였던 알람은 이번에는 매칭 우선순위 높임).
```

## 입력 예시

```yaml
task: scenario-verification
context:
  testbed_name: plopvape-shop
  scenario_runner_base: http://192.168.200.109:8091
  polestar10_base: https://192.168.230.96
  polestar10_cookie_jar: /home/sjbang/.polestar10/cookie.jar
  scenarios_to_verify: ["01", "02", "03", "04"]
  attempt_n: 2
  previous_verdict:
    overall: PARTIAL
    scenarios:
      - id: "02"
        verdict: PARTIAL
        missed: ["DPM Lock 수 급증 (≥40 Lock)"]
```

## 출력 (testbed-verifier 가 반환)

```json
{
  "overall": "PASS",
  "duration_sec": 1240,
  "scenarios": [
    {
      "id": "01",
      "verdict": "PASS",
      "expected": ["DPM lock wait", "..."],
      "fired": [
        {"name": "DPM Lock Wait Time 초과", "resource": "postgres@rca-testbed-v2", "severity": "LEVEL3", "fired_at": "..."}
      ],
      "missed": [],
      "spurious": []
    },
    ...
  ],
  "recommendations": []
}
```

## 오케스트레이터 retry 루프

[SKILL.md Phase 11 의 의사코드 그대로]:

```bash
ATTEMPT=1
MAX_ATTEMPTS=3
PREVIOUS_VERDICT="null"

while [ "$ATTEMPT" -le "$MAX_ATTEMPTS" ]; do
  echo "[verify] attempt $ATTEMPT/$MAX_ATTEMPTS"

  TASK_PROMPT=$(render_template verify-task.md \
    TESTBED_NAME="$TESTBED_NAME" \
    SCENARIO_RUNNER_BASE="$RUNNER_URL" \
    POLESTAR10_BASE_URL="$POLESTAR10_BASE_URL" \
    COOKIE_JAR="$JAR" \
    SCENARIO_IDS='["01","02","03","04"]' \
    ATTEMPT_N="$ATTEMPT" \
    PREVIOUS_VERDICT_JSON="$PREVIOUS_VERDICT")

  VERDICT=$(claude_invoke_agent "testbed-verifier" "$TASK_PROMPT")

  echo "$VERDICT" >> "$HOME/.testbed-build/runs/$RUN_ID/verify.log"
  OVERALL=$(jq -r '.overall' <<< "$VERDICT")

  case "$OVERALL" in
    PASS)
      echo "[verify] PASS @ attempt $ATTEMPT"
      break
      ;;
    PARTIAL|FAIL)
      if [ "$ATTEMPT" -eq "$MAX_ATTEMPTS" ]; then
        echo "[verify] max attempts. 결과: $OVERALL"
        break
      fi
      # tune-alarms 재호출 (recommendations 기반)
      RECS=$(jq -c '.recommendations' <<< "$VERDICT")
      echo "[verify] FAIL/PARTIAL → testbed-tune-alarms retune"
      claude_invoke_skill "testbed-tune-alarms" \
        --target_scope "$TESTBED_NAME" \
        --mode apply \
        --recommendations "$RECS"
      PREVIOUS_VERDICT="$VERDICT"
      ATTEMPT=$((ATTEMPT+1))
      ;;
    *)
      echo "[verify] 예외 verdict: $OVERALL. 재시도 X. 사용자 prompt."
      break
      ;;
  esac
done

# 최종 verdict 를 manifest 에 기록
update_manifest "verify_attempts" "$ATTEMPT"
update_manifest "phases.verify" "completed"   # 또는 failed
```

## attempt 사이 sleep

연속 시나리오 실행 사이 Polestar10 backend 의 알람 history 정리 시간 확보 — 60초 sleep 권고:

```bash
if [ "$ATTEMPT" -gt 1 ]; then
  sleep 60   # 이전 attempt 의 알람 매칭 윈도우 종료
fi
```

## verify.log 누적 형식

각 attempt + retune 후 append. state-schema.md 의 verify.log 예시 그대로.

## verifier agent 가 ask-polestar10 호출하는 케이스

verifier 가 내부에서 Polestar10 알람 history API 5xx 만나면:
- agent 자체 도구 (Read, Grep, Glob, Bash) 만 가지므로 직접 ask-polestar10 호출 X
- agent 가 verdict 에 `error: "polestar10 alarm-history API 5xx. 호출자가 ask-polestar10 권고."` 담아서 반환
- 오케스트레이터가 verdict 보고 ask-polestar10 dispatch

## 사용자 force-pass

3회 모두 실패 + 사용자가 "수동 분석 후 force-pass":

```
=== Verify max attempts 도달 ===
attempt 3 verdict: PARTIAL
missed alarms: ...

옵션:
  1) finalize 진행 (PARTIAL 결과로 보고서)
  2) 수동 분석 권고 (run 보존, 종료)
  3) 강제 PASS 마킹 (테스트만 — production 권장 X)

선택 [1]:
```
