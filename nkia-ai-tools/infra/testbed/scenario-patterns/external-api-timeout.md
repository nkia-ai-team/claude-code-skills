# Pattern: External API Timeout

## Summary
외부 의존성 (PG/3rd-party API/external mock) 가 무응답 (TCP 연결은 되지만 HTTP 응답 없음) 일 때 호출 측 read-timeout 누적 → 상위 서비스 thread starvation.

## 트리거 메커니즘
- 외부 의존성 컨테이너를 `docker stop` 또는 `iptables` 로 응답 차단
- 호출 측은 connection 자체는 성공하지만 read 단계에서 N 초 대기
- 호출이 누적되며 thread pool 고갈 → cascade timeout

## propagation (root → user-visible)
1. 외부 mock 컨테이너 정지 또는 blackhole
2. 호출 서비스의 HTTP 클라이언트가 connection 후 read 대기 (10s 등 default timeout)
3. 동시 요청들이 모두 동일 대기 → thread pool 포화
4. 상위 호출 서비스도 하위 응답 대기 → cascading timeout
5. 게이트웨이 5xx 또는 timeout

## 적합한 도메인
- 결제 (외부 PG), 인증 (외부 OAuth), 메시징 (외부 SMS gateway), 지도 (외부 geocoding) 등 **외부 의존성을 가진 도메인**
- mock 컨테이너로 외부를 모사하는 테스트베드 환경

## bash 스크립트 골격
```bash
#!/bin/bash
# scenario-XX-<external>-timeout.sh
set -euo pipefail
trap cleanup EXIT

EXTERNAL_CONTAINER="${EXTERNAL_CONTAINER:-pg-mock}"   # 인스턴스 시 치환
LOAD_ENDPOINT="${LOAD_ENDPOINT:-/api/<endpoint>}"
SERVICE_API="${SERVICE_API:-http://127.0.0.1:30080}"
LOAD_DURATION_SEC="${LOAD_DURATION_SEC:-180}"
LOAD_CONCURRENCY="${LOAD_CONCURRENCY:-20}"
LOAD_PAYLOAD='{"...": "..."}'                           # 인스턴스 시 치환

cleanup() {
  echo "[INFO] cleanup: restart external dep + drain load"
  docker start "$EXTERNAL_CONTAINER" 2>/dev/null || true
  pkill -P $$ || true
  echo "[OK] cleanup complete"
}

if [ "${1:-}" = "cleanup" ]; then
  cleanup
  exit 0
fi

echo "[INFO] starting $0"

# 1. 외부 의존성 정지
echo "[INFO] stopping external dep: $EXTERNAL_CONTAINER"
docker stop "$EXTERNAL_CONTAINER"

sleep 2

# 2. 호출 부하
echo "[INFO] firing $LOAD_CONCURRENCY concurrent requests for ${LOAD_DURATION_SEC}s"
END=$(( $(date +%s) + LOAD_DURATION_SEC ))
while [ "$(date +%s)" -lt "$END" ]; do
  for i in $(seq 1 "$LOAD_CONCURRENCY"); do
    (curl -sS -m 30 -X POST -H 'Content-Type: application/json' \
      -d "$LOAD_PAYLOAD" "${SERVICE_API}${LOAD_ENDPOINT}" >/dev/null) &
  done
  sleep 5
done
wait

echo "[OK] done"
```

## expected_alarms (기본값)
- `APM <외부 호출 서비스> 평균응답시간 초과` (외부 read-timeout 대기)
- `APM <상위 서비스> 평균응답시간 초과` (캐스케이드)
- `APM <상위 서비스> 에러율 급증`
- `DPM 트랜잭션 시간 초과` (외부 호출이 트랜잭션 안에 묶여있는 경우)
- `DPM Lock 수 급증` (장시간 트랜잭션 누적)

## cleanup 안전성 + 부작용
- 안전: `docker start` 로 외부 mock 재기동 → 정상 응답 복구
- 부작용: 부하 동안 들어온 요청 중 일부는 실패 응답으로 사용자에게 반환됨 (의도된 동작)
- 주의: SIGKILL 시 trap 미동작 → 외부 mock 이 정지된 채 남음. 수동 `docker start` 필요.

## 치환 슬롯
- `EXTERNAL_CONTAINER` — 외부 의존성 mock 컨테이너 이름
- `LOAD_ENDPOINT` — 외부를 호출하는 API
- `LOAD_DURATION_SEC` — 부하 지속 시간
- 차단 방식 옵션: `docker stop` 대신 `iptables -A INPUT -p tcp --dport <port> -j DROP` (TCP blackhole, RST 도 안 보냄)
