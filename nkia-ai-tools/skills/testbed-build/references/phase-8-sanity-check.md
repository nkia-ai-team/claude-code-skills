# Phase 8 — APM standby agent heartbeat sanity check

ansible exit 0 라도 deployment manifest 의 OTLP env 누락 / OTel javaagent attach 실패 / collector NodePort 미도달 등으로 standby 미감지 가능. **Phase 9 (Polestar10 등록) 진입 전 필수 검증**.

이 체크가 round-7 의 'manifest OTLP env 누락 → fire 0건' silent failure 패턴 차단.

## 절차

```bash
EXPECTED=${SERVICE_COUNT}   # interview.app.testbed_services 의 개수
TESTBED=${APP_SUBDIR}

for i in 1 2 3 4 5; do
  CNT=$(curl -k -sS --cookie "$JAR" -X POST -H 'Content-Type: application/json' \
    -d '{"pageNumber":1,"pagePerSize":100,"gridFilters":[],"sortFieldSets":[],"tagFilters":[],"arguments":{}}' \
    "$POLESTAR10_BASE_URL/api/apm/standby-agents-filter-step1" | \
    jq --arg n "$TESTBED" '[.data.content[]
      | select((.hostName // "" | tostring | contains($n))
            or (.agentName // "" | tostring | startswith($n + "-")))
      | select(.agentType == "opentelemetry" and .availabilityStatus == "UP")] | length')

  if [ "$CNT" -ge "$EXPECTED" ]; then
    echo "[sanity] APM standby agents=$CNT (>=$EXPECTED) OK"
    break
  fi

  echo "[sanity] APM standby attempt $i/5 — $CNT / $EXPECTED. 1분 후 재시도"

  if [ $i -eq 5 ]; then
    echo "FATAL: APM standby heartbeat 5분 후 미도달."
    echo "원인 후보:"
    echo "  - testbed-services manifest 의 OTLP env 누락"
    echo "    (JAVA_TOOL_OPTIONS / OTEL_EXPORTER_OTLP_ENDPOINT / OTEL_RESOURCE_ATTRIBUTES)"
    echo "  - OTel collector port (default 6565) 도달 불가"
    echo "  - lucida.organizationId / lucida.groupId attribute 미설정"
    echo "사용자 안내 후 manifest patch / kubectl set env 권고."
    exit 1
  fi

  sleep 60
done
```

## 통과 기준

`$CNT >= $EXPECTED` (UP 상태인 OTel APM agent 수가 testbed_services 개수 이상).

## 실패 시 사용자 안내

5회 (5분) 후 미도달 → 사용자에게 원인 후보 표시 + manifest 점검 권고. Phase 9 진입 X.

흔한 원인:
1. **OTLP env 누락** — testbed-services 매니페스트의 `OTEL_EXPORTER_OTLP_ENDPOINT` placeholder (`${OTLP_ENDPOINT}`) 가 envsubst 안 됨 → 사용자가 kubectl describe pod 에서 env 확인
2. **collector port 도달 불가** — `nc -zv <collector_host> 6565` 실패 → bootstrap.yaml 의 polestar10.collector_host 가 사내 NAT/방화벽 outbound 차단되는 public IP 인지 확인
3. **organization_id 미설정** — OTEL_RESOURCE_ATTRIBUTES 의 `lucida.organizationId=` 빈값 → bootstrap.yaml 의 polestar10.organization_id 비어있는지 확인

## 회복 가능 / blocking 분기

- **회복 가능**: kubectl set env 으로 즉시 fix 가능 → 사용자 prompt + 1회 재시도
- **blocking**: collector_host 변경 필요 → bootstrap.yaml 수정 + ansible 재실행 권고 (Phase 8 부터 resume)
