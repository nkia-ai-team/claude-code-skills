# Pattern: DB CPU Throttle

## Summary
DB 컨테이너의 CPU limit 을 극단적으로 낮춰 (예: 500m → 10m) 모든 쿼리가 throttling 으로 지연됨 → 전 서비스 응답시간 급증.

## 트리거 메커니즘
- K8s `kubectl patch` 로 postgres pod (또는 다른 DB pod) 의 `resources.limits.cpu` 를 극저값으로 변경
- pod 재기동 후 모든 쿼리가 CPU throttling 받음 (마이크로초 단위 작업도 수십~수백 ms)
- 전 서비스가 DB 응답 대기 → 평균 응답시간 N배 증가

## propagation (root → user-visible)
1. DB pod CPU limit 축소 적용 (rolling restart)
2. 모든 SQL 쿼리가 throttling → 평소 ms 단위가 수 초 단위로
3. 전 서비스의 DB 호출 지연 → APM 평균 응답시간 폭증
4. 일부 트랜잭션은 timeout → 5xx
5. 사용자 체감 응답시간 N배 증가

## 적합한 도메인
- DB 의존도 높은 모든 웹 서비스 (대부분의 트랜잭션 서비스)
- K3s/K8s 환경 (CPU limit patch 가능해야 함)
- metrics-server 가 깔린 클러스터 (KCM pod CPU throttling 알람 측정 위해)

## bash 스크립트 골격
```bash
#!/bin/bash
# scenario-XX-db-cpu-throttle.sh
set -euo pipefail
trap cleanup EXIT

NAMESPACE="${NAMESPACE:-rca-testbed}"
DB_DEPLOYMENT="${DB_DEPLOYMENT:-postgres}"
DB_CONTAINER="${DB_CONTAINER:-postgres}"
NORMAL_CPU="${NORMAL_CPU:-500m}"
THROTTLED_CPU="${THROTTLED_CPU:-10m}"
SERVICE_API="${SERVICE_API:-http://127.0.0.1:30080}"
LOAD_ENDPOINT="${LOAD_ENDPOINT:-/api/<endpoint>}"
LOAD_DURATION_SEC="${LOAD_DURATION_SEC:-150}"
LOAD_CONCURRENCY="${LOAD_CONCURRENCY:-15}"

cleanup() {
  echo "[INFO] cleanup: restore DB CPU limit + drain load"
  kubectl -n "$NAMESPACE" patch deployment "$DB_DEPLOYMENT" --type='json' \
    -p="[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/limits/cpu\",\"value\":\"$NORMAL_CPU\"}]" || true
  kubectl -n "$NAMESPACE" rollout status deployment "$DB_DEPLOYMENT" --timeout=60s || true
  pkill -P $$ || true
  echo "[OK] cleanup complete"
}

if [ "${1:-}" = "cleanup" ]; then
  cleanup
  exit 0
fi

echo "[INFO] starting $0"

# 1. CPU limit 축소
echo "[INFO] patching $DB_DEPLOYMENT cpu limit -> $THROTTLED_CPU"
kubectl -n "$NAMESPACE" patch deployment "$DB_DEPLOYMENT" --type='json' \
  -p="[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/limits/cpu\",\"value\":\"$THROTTLED_CPU\"}]"
kubectl -n "$NAMESPACE" rollout status deployment "$DB_DEPLOYMENT" --timeout=60s

# 2. 부하
echo "[INFO] firing concurrent load for ${LOAD_DURATION_SEC}s"
END=$(( $(date +%s) + LOAD_DURATION_SEC ))
while [ "$(date +%s)" -lt "$END" ]; do
  for i in $(seq 1 "$LOAD_CONCURRENCY"); do
    (curl -sS -m 30 "${SERVICE_API}${LOAD_ENDPOINT}" >/dev/null) &
  done
  sleep 3
done
wait

echo "[OK] done"
```

## expected_alarms (기본값)
- `APM 평균응답시간 초과` (전 서비스, DB 의존 모든 endpoint)
- `APM 서비스 에러율 급증` (timeout 누적)
- `KCM postgres Pod CPU throttling` (metrics-server 설치 시)
- `DPM 트랜잭션 시간 초과`

## cleanup 안전성 + 부작용
- 안전: 원래 CPU limit 으로 복원 + rolling restart 로 적용
- **부작용 1**: postgres pod 재기동 시 KCM 의 pod-단위 알람 정책이 disable 될 수 있음 (콘솔에서 수동 재활성화)
- **부작용 2**: 클러스터에 metrics-server 미설치 시 KCM Pod CPU 알람은 발화하지 않음 (시나리오 자체 실행은 영향 X)
- 주의: 재기동 동안 DB 일시 단절 → in-flight 트랜잭션 일부 실패. 결과적으로 connection pool 재초기화.

## 치환 슬롯
- `DB_DEPLOYMENT` / `DB_CONTAINER` — postgres / mysql / mariadb / oracle (Tibero/CUBRID 는 별도 patch 경로)
- `THROTTLED_CPU` — 더 낮을수록 강한 throttle (10m = 1% CPU). 너무 낮으면 readiness probe 자체 실패로 빠르게 unhealthy
- `NORMAL_CPU` — cleanup 시 복구 값. 환경에 맞춤
