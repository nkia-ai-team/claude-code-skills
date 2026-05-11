# `verify` — Closed-loop verify retry 루프

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
| `PARTIAL` | `dispatch_tune_and_retry` | tune-alarms recommendations 적용 → 다음 attempt |
| `FAIL` | `dispatch_tune_and_retry` 또는 `user-decision` | recoverable 면 자동 retry, blocking 이면 사용자 prompt |
| `ERROR` (시나리오 자체 실패) | `user-decision` | rca-scenario-runner 도달성 점검 안내 |

## WPM `served=0` 진단 가이드 (FAIL 시 1순위)

verify 가 PARTIAL/FAIL 이고 WPM 메트릭이 0 (혹은 `served=0`) 인 서비스가 있으면 **다음 순서를 strict 하게 따른다**. 1·2·3 단계 우회한 채 4 부터 의심하면 시간 허비.

1. **application HTTP status code 분포** (1순위 — 가장 흔한 원인)
   - 의심 서비스의 pod 에서 직접 prob:
     ```bash
     kubectl exec -n <ns> <pod> -- curl -s -o /dev/null -w '%{http_code}\n' \
       http://localhost:<port>/<endpoint> -X POST -d '<sample-body>' -H 'Content-Type: application/json'
     ```
   - `kubectl logs -n <ns> <pod> --tail=200 | grep -E ' 5[0-9]{2} | 4[0-9]{2} '`
   - 5xx (특히 503) 다수 → **application 도메인 정정이 먼저**. WPM 은 정상 처리된 요청을 봐야 카운트.
     (전형 케이스: capacity gating 으로 503 fast-fail — capacity-gated 도메인의 lifecycle terminal 합성 누락이 root cause)

2. **WPM agent boot/계측 정상 여부** (1 통과 시):
   - pod 의 stdout 에 `WPM Agent started` 류 boot 메시지
   - `kubectl logs <pod> | grep -i 'objType\|wpm\|scouter'` 로 Spring URL 감지 확인
   - WPM-SCOUTER thread 수 (`jstack` 또는 thread dump) — 정상은 SCOUTER1/2/3 + SCOUTER-TCP 의 4개

3. **P10 collector 측 로그** (2 통과 시 — 104 controller 서버에서):
   ```bash
   docker logs polestar-app-wpm-1 --since 10m | grep <serviceName>
   ```
   - `tcpConnected=false` / `lastTcpConnect=null` → TCP 31005 풀 비활성 (4 진입)
   - `udpActive=true` 인데 tcp 만 false → §1 `enabledAutoAddAgent` toggle 미적용 의심

4. **`enabledAutoAddAgent` 토글 확인** (3 까지 통과 시):
   - P10 UI > 전체구성 > WPM > 서비스 클릭 > 우측 드로어 > "에이전트 자동 추가" 토글
   - 또는 `recipes/wpm-enable-auto-add.md` 실행

**금지 패턴**: 1·2·3 단계 우회하고 "RestClient 미지원" / "@XxxMapping value 누락" / "WPM TCP collector 차단" 가설로 직진 — application 5xx 가 1순위.

reference: `knowledge/polestar10/agents/wpm/install-guide.md`.

---

## 재시도 한계 도달 후

3 attempts 가 모두 PASS 미달 → 사용자 결정 후 `finalize` 단계로 진입 가능.
이 경우 `finalize.status=finalized_partial` 로 기록하고 report.md 에
"verify 미통과 — last verdict" 를 명시한다. PASS 와 동일한 성공으로 취급하지 않는다.

사용자에게 매뉴얼 점검 안내:
- expected_alarms 가 정확한지 (시나리오 yaml 의 expected_alarms vs 실제 발화 알람)
- 알람 정책의 임계치가 시나리오 강도와 매칭되는지
- 시나리오 trigger 자체가 작동하는지 (rca-scenario-runner 의 /api/scenarios/<id>/run 응답 확인)
