# Pattern: DB Lock Contention

## Summary
한 트랜잭션이 row/table lock 을 장시간 점유한 상태에서 동시 요청이 몰리면 lock wait 누적 → 상위 서비스 타임아웃 캐스케이드.

## 트리거 메커니즘
- 백그라운드 세션이 `BEGIN; SELECT ... FOR UPDATE;` 후 commit 지연 (sleep)
- 동시에 N 개 클라이언트가 같은 row/table 을 갱신하는 요청을 발사
- DB lock wait 가 누적되며 connection 고갈 + 응답 지연

## propagation (root → user-visible)
1. background tx 가 lock 획득 후 점유
2. 들어오는 요청들이 같은 row 에 lock 대기
3. 요청 처리 thread 가 DB wait 에 묶임 → thread pool 고갈
4. 상위 서비스 호출이 timeout / 5xx
5. 게이트웨이 레벨에서 502/504 사용자 가시

## 적합한 도메인
- 트랜잭션 일관성 중요한 도메인: e-commerce 주문/재고, banking 계좌이체, 예약 시스템
- 핫 row 가 명확한 시스템 (재고 수량, 잔액, 좌석 등)

## bash 스크립트 골격
```bash
#!/bin/bash
# scenario-XX-<lock-target>-lock.sh
set -euo pipefail
trap cleanup EXIT

NAMESPACE="${NAMESPACE:-rca-testbed}"
DB_POD=$(kubectl -n "$NAMESPACE" get pod -l app=postgres -o jsonpath='{.items[0].metadata.name}')
SERVICE_API="${SERVICE_API:-http://127.0.0.1:30080}"
LOCK_TABLE="${LOCK_TABLE:-<table_name>}"      # 인스턴스 시 치환
LOCK_KEY="${LOCK_KEY:-<row_key>}"             # 인스턴스 시 치환
LOAD_ENDPOINT="${LOAD_ENDPOINT:-/api/<endpoint>}"
LOAD_PAYLOAD='{"...": "..."}'                  # 인스턴스 시 치환
HOLD_SECS="${HOLD_SECS:-180}"
LOAD_CONCURRENCY="${LOAD_CONCURRENCY:-30}"

cleanup() {
  echo "[INFO] cleanup: kill background lock holder + drain load"
  kubectl -n "$NAMESPACE" exec "$DB_POD" -- \
    psql -U postgres -d shop -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle in transaction' AND query LIKE '%FOR UPDATE%';" || true
  pkill -P $$ || true
  echo "[OK] cleanup complete"
}

if [ "${1:-}" = "cleanup" ]; then
  cleanup
  exit 0
fi

echo "[INFO] starting $0"

# 1. 백그라운드 lock 획득
kubectl -n "$NAMESPACE" exec -i "$DB_POD" -- \
  psql -U postgres -d shop <<EOF &
BEGIN;
SELECT * FROM ${LOCK_TABLE} WHERE id = '${LOCK_KEY}' FOR UPDATE;
SELECT pg_sleep(${HOLD_SECS});
COMMIT;
EOF
LOCK_PID=$!

sleep 3
echo "[INFO] background lock acquired (pid=$LOCK_PID), starting concurrent load"

# 2. 동시 부하
for i in $(seq 1 "$LOAD_CONCURRENCY"); do
  (curl -sS -X POST -H 'Content-Type: application/json' \
    -d "$LOAD_PAYLOAD" "${SERVICE_API}${LOAD_ENDPOINT}" >/dev/null) &
done

wait $LOCK_PID
echo "[OK] done"
```

## expected_alarms (기본값)
- `DPM lock wait` (DB lock wait time 또는 lock count 임계 초과)
- `APM <대상-서비스> 평균응답시간 초과` (lock 대기 → 처리 지연)
- `APM 서비스 에러율 급증` (5xx 누적)
- `SMS postgres process CPU%` (백그라운드 lock 세션 CPU)

## cleanup 안전성 + 부작용
- 안전: `pg_terminate_backend` 으로 idle-in-transaction 세션 강제 종료. row 자체는 변경 X.
- 부작용: 강제 종료된 트랜잭션이 rollback 되며 일시적 connection churn. 핵심 비즈니스 데이터는 영향 X.
- 주의: cleanup 안 거치면 DB 가 lock wait 풀릴 때까지 (sleep) 응답 지연 잔존. SIGKILL 시 trap 미동작 → 수동 정리 필요.

## 치환 슬롯
- `LOCK_TABLE` / `LOCK_KEY` — 도메인별 핫 row (inventory.id / accounts.id / seats.id)
- `LOAD_ENDPOINT` — 그 row 를 갱신하는 API
- `HOLD_SECS` — lock 점유 기간 (시나리오 재생산 시간)
- `LOAD_CONCURRENCY` — 동시 요청 수
