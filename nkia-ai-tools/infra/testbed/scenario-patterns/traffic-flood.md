# Pattern: Traffic Flood

## Summary
점진적으로 동시 요청을 폭증시켜 (5 → 50 → 200 → 500 concurrent) 진입 서비스의 thread pool 포화 + DB connection/lock 경합 → cascade 5xx.

## 트리거 메커니즘
- 단일 진입 endpoint 에 4 단계 점진적 부하 (각 단계 N 초)
- thread pool 사이즈 (default 200) 초과 시 새 요청은 큐 대기 또는 reject
- DB connection pool (default ~50) 초과 시 connection acquire timeout
- 하위 서비스 호출 cascade → 다중 서비스 동시 5xx

## propagation (root → user-visible)
1. 1단계 (5 concurrent): 평소 부하, 정상 응답
2. 2단계 (50): thread pool 부분 활용, 응답시간 약간 증가
3. 3단계 (200): thread pool 포화 시작, queue 대기 발생
4. 4단계 (500): thread pool 완전 포화 → 503/connection refused
5. DB connection 고갈 → 트랜잭션 acquire timeout
6. 게이트웨이 5xx 폭증, 사용자 체감 가용성 급락

## 적합한 도메인
- 모든 웹 서비스 (가장 일반적인 부하 패턴)
- 핫이벤트 시즌 (블랙프라이데이, 신상품 런칭) 의 운영 환경 시뮬레이션
- thread pool / connection pool 튜닝 검증

## bash 스크립트 골격
```bash
#!/bin/bash
# scenario-XX-traffic-flood.sh
set -euo pipefail
trap cleanup EXIT

NAMESPACE="${NAMESPACE:-rca-testbed}"
SERVICE_API="${SERVICE_API:-http://127.0.0.1:30080}"
LOAD_ENDPOINT="${LOAD_ENDPOINT:-/api/<entry-endpoint>}"
LOAD_PAYLOAD='{"...": "..."}'

# 4단계 부하: (concurrency, duration_sec)
STAGES=(5:30 50:30 200:60 500:60)

cleanup() {
  echo "[INFO] cleanup: drain load + restart entry services"
  pkill -P $$ || true
  # 일부 서비스가 hung-up 상태일 수 있음 — rolling restart
  kubectl -n "$NAMESPACE" rollout restart deployment 2>/dev/null || true
  echo "[OK] cleanup complete"
}

if [ "${1:-}" = "cleanup" ]; then
  cleanup
  exit 0
fi

echo "[INFO] starting $0"

for stage in "${STAGES[@]}"; do
  IFS=: read -r CONC DUR <<< "$stage"
  echo "[INFO] stage: $CONC concurrent x ${DUR}s"
  END=$(( $(date +%s) + DUR ))
  while [ "$(date +%s)" -lt "$END" ]; do
    for i in $(seq 1 "$CONC"); do
      (curl -sS -m 30 -X POST -H 'Content-Type: application/json' \
        -d "$LOAD_PAYLOAD" "${SERVICE_API}${LOAD_ENDPOINT}" >/dev/null 2>&1) &
    done
    sleep 1
  done
  wait
done

echo "[OK] done"
```

## expected_alarms (기본값)
- `APM 평균응답시간 초과` (모든 호출되는 서비스)
- `APM 서비스 에러율 급증` (특히 진입 서비스)
- `DPM DB 연결 수 폭증`
- `DPM DB Lock 수 급증`
- `DPM 트랜잭션 시간 초과`
- (선택) `SMS process CPU%` 또는 `KCM Pod CPU` (peak 단계에서)

## cleanup 안전성 + 부작용
- 안전: `pkill -P $$` 로 자식 프로세스 정리 + (선택) 모든 deployment rolling restart
- **부작용 1**: rolling restart 로 WPM 에이전트가 재등록됨. 기존 에이전트는 disabled 상태. 카운트가 시나리오 실행마다 증가.
- **부작용 2**: disabled 에이전트 삭제 시 그 에이전트가 수집한 WPM 데이터 함께 삭제됨 (장기 dogfooding 시 주의)
- **부작용 3**: 일부 in-flight 트랜잭션은 실패 응답으로 종료 (의도된 동작)
- 주의: SIGKILL 시 trap 미동작 → 자식 프로세스 잔존 가능. 수동 `pkill -f curl` 정리.

## 치환 슬롯
- `STAGES` — 단계별 (concurrency, duration). 환경에 맞게 조정
- `LOAD_ENDPOINT` — 진입 endpoint (가장 비용 높은 transaction 경로 권장)
- 부하 도구 옵션: `curl` 대신 `hey` / `wrk` / `vegeta` (정밀 RPS 제어 시)
