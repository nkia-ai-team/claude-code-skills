# 서버단(백엔드 only) TC 작성 가이드

화면 없이 API/DB/배치/MQ/메트릭/인프라 변경만 있는 이슈의 TC 작성법.
**4섹션 구조는 화면 TC 와 동일**. 절차와 예상결과의 도구만 다르다.

## 이슈 유형별 도구 매핑

| 이슈 유형 | 절차 도구 | 예상결과 단언 대상 |
|----------|---------|------------------|
| REST API 추가/변경 | `curl` + `jq` | HTTP status, response body 필드, 응답 시간 (`-w '%{time_total}'`) |
| DB 스키마/데이터 | `mongosh` / `psql` / `mysql` | row count, 컬럼 존재, 값, 인덱스 |
| 배치/스케줄 잡 | `kubectl exec` / 트리거 CLI | job status, 출력 파일, DB row 변화 |
| Kafka/MQ | `kafka-console-producer/consumer` | 메시지 수신, payload 일치 |
| LLM/AI 파이프라인 | API 호출 + 평가 스크립트 | 응답 형식, 키워드 포함, 정성 평가 |
| 알람/임계치 | 메트릭 주입 + polestar10 API | 알람 발화, 임계치 비교, 알람 history |
| 권한/인증 | curl 토큰 변경 | 200 vs 401/403 |
| 인프라/배포 | `docker logs`, `kubectl get`, `systemctl status` | 컨테이너 Running, 헬스체크 OK, 환경변수 적용 |
| 성능 | `ab` / `wrk` / `hey` | RPS, p95/p99 latency |

## 성능 측정 — 서버단도 필수

- API 응답 시간: `curl -w 'time_total: %{time_total}s\n'`
- DB 쿼리: `EXPLAIN ANALYZE` 또는 `\timing on`
- 배치 잡: `time kubectl exec ...` 또는 잡 시작/완료 timestamp
- 예상결과에 굵게 명시: `**API 응답 시간이 측정되어 결과에 기록된다.**`

## Negative 패턴 (서버단)

| 카테고리 | 예시 |
|---------|------|
| 잘못된 페이로드 | 필수 필드 누락 → 400 + 검증 메시지 JSON |
| 권한 없음 | 다른 role 토큰으로 호출 → 401/403 |
| 미존재 리소스 | 없는 ID 조회 → 404 |
| 동시성 | 같은 자원 동시 수정 → 409 Conflict |
| 비즈니스 룰 위반 | 잘못된 상태에서 전이 시도 → 500 또는 도메인 에러 코드 |

## 완성 예시 — API 이슈

```
## TC-RCA-001 - [RCA] 시나리오 트리거 API POST 정상 호출

사전조건
- rca-scenario-runner 서비스가 109 서버에서 Running 상태
- service-spec.yaml 에 시나리오 "high-cpu" 등록되어 있음

참고사항
- 엔드포인트: POST /api/scenarios/trigger
- 페이로드: { "scenario": "high-cpu", "duration_sec": 60 }
- 응답: 202 Accepted + { "runId": "uuid" }
- 비동기 실행. 결과는 GET /api/scenarios/{runId} 로 폴링

테스트절차
1. curl -X POST https://109:8443/api/scenarios/trigger -H "Content-Type: application/json" -d '{"scenario":"high-cpu","duration_sec":60}' -w '%{http_code} %{time_total}\n' 실행
2. 응답에서 runId 를 jq 로 추출한다.
3. 5초 후 GET /api/scenarios/{runId} 를 호출한다.
4. docker logs rca-scenario-runner | grep "scenario started" 확인

예상결과 (캡처포함)
- 1. HTTP status 202, response.body.runId 가 UUID v4 형식. **API 응답 시간이 측정되어 결과에 기록된다 (목표 < 500ms).**
- 2. runId 가 non-empty string 으로 추출된다.
- 3. response.body.status 가 "RUNNING" 또는 "COMPLETED".
- 4. 로그에 "scenario started runId=<id>" 라인이 1건 이상 출력된다.
```

## 완성 예시 — DB 마이그레이션 이슈

```
## TC-MIGRATION-001 - [auth] users 테이블에 last_login_at 컬럼 추가

사전조건
- 마이그레이션 0042_add_last_login.sql 이 main 에 머지됨
- staging DB 가 마이그레이션 적용된 상태

참고사항
- 컬럼명: last_login_at, 타입: timestamp with time zone, nullable
- 기존 row 는 NULL 로 백필
- 마이그레이션은 zero-downtime (NOT NULL 강제 X)

테스트절차
1. psql -c "\d users" 로 컬럼 존재 확인
2. psql -c "SELECT count(*) FROM users WHERE last_login_at IS NULL" 실행
3. INSERT 신규 user 1건 후 last_login_at 이 NULL 인지 확인
4. UPDATE last_login_at = now() 적용 후 SELECT 확인

예상결과 (캡처포함)
- 1. \d 출력에 "last_login_at | timestamp with time zone | nullable" 라인 포함
- 2. count(*) 가 기존 user 수와 동일 (전체 NULL 백필 확인)
- 3. 신규 INSERT row 의 last_login_at 이 NULL
- 4. UPDATE 후 SELECT 시 timestamp 값 반환, 약 현재 시각 ± 5초 이내
```

## 자동 수행 스크립트

Playwright 대신 **bash 스크립트** 로 절차 자동화:

```bash
#!/usr/bin/env bash
# scripts/generated/<LinearID>-backend.sh
set -e
OUT=scripts/runs/$LINEAR_ID-backend
mkdir -p "$OUT"

# Step 1
echo "== TC-RCA-001 절차 1: trigger API =="
RESP=$(curl -sk -X POST https://109:8443/api/scenarios/trigger \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"high-cpu","duration_sec":60}' \
  -w '\n__STATUS=%{http_code} __TIME=%{time_total}\n')
echo "$RESP" | tee "$OUT/01-trigger.txt"

# Step 2
RUN_ID=$(echo "$RESP" | head -n1 | jq -r '.runId')
echo "runId=$RUN_ID" | tee "$OUT/02-runid.txt"
[ -z "$RUN_ID" ] && { echo "[FAIL] runId 추출 실패"; exit 1; }

# Step 3
sleep 5
curl -sk "https://109:8443/api/scenarios/$RUN_ID" | tee "$OUT/03-status.json"

# Step 4
docker logs rca-scenario-runner 2>&1 | grep "scenario started" | tee "$OUT/04-log.txt"

echo "[PASS] all steps"
```

결과 파일 (txt/json) 을 PIMS 댓글 첨부로 등록.

## TC 산정 가이드 (서버단 이슈당 표준 TC 개수)

| 이슈 규모 | 표준 TC 개수 |
|---------|------------|
| 단일 API endpoint 추가 | 2~4 (정상 1~2 + 검증 에러 1 + 권한 1) |
| 다중 API endpoint (CRUD) | 5~8 (각 endpoint × 정상/에러) |
| DB 마이그레이션 | 2~3 (스키마 확인 + 백필 + 신규 INSERT) |
| 배치/스케줄 잡 | 3~5 (트리거 + 결과 + 재시도 + 로그) |
| LLM 파이프라인 변경 | 3~5 (대표 입력 3~5개 + 형식 검증) |
| 알람 임계치 변경 | 2~3 (트리거 + 발화 + 해제) |
| 인프라/배포 (헬스체크) | 1~2 (Running + 환경변수) |
| 리팩토링 (기능 무변경) | 0 (회귀 테스트로 충분, 별도 TC 불필요) |
