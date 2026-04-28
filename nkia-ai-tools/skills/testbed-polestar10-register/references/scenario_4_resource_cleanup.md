# Scenario 4 — 자원 삭제 + agent 재출현 가드

> "plopvape-db 삭제해줘"
> "테스트베드 정리 — 등록한 자원 다 빼"

자원 삭제는 type 별 식별자 형식이 다르고, **agent-based 자원은 에이전트가 살아있으면 다시 standby 에 등장** 한다.

---

## Trigger 키워드

`삭제`, `지워`, `제거`, `정리`, `cleanup`, `delete`, `빼`

---

## Pre-conditions

- Bootstrap 완료

---

## Dispatch flow

```
1. 삭제 대상 식별
   사용자 입력 형태:
     - 자원 이름 1개          → 단일 삭제
     - 서비스 그룹 이름        → 그 그룹의 모든 자원 (시나리오 1 의 역방향)
     - "테스트베드 전부"       → 인터뷰 후 서비스 그룹 또는 명시 목록 확인
     - 자원 이름 N개 (콤마/줄)  → 다중 삭제

2. type 분류 + 식별자 추출
   recipes/list-targets.md 의 type 별 list-filter 로 매칭:
     - 서버: hostname → resourceId (MA_<host>_<ts>)
     - Web URL: resourceName → id (weburl_<...>)
     - SLO: name → id (registered:true 와 false 양쪽 검색)
     - DB/APM/KCM/NMS: TBD type 별 list-filter
   매칭 실패: 후보 dropdown 표시 → 사용자 선택

3. 삭제 전 카운트
   /api/cm/portal/configuration/count   (전체)
   각 type 의 /api/<type>/count          (개별)
   ※ 비교용 baseline. 삭제 후 검증에 사용.

4. 사용자 확인
   삭제 대상 표 (이름 / type / 식별자) + 영향도:
     - 알람 정의도 함께 사라짐 (자원 종속)
     - 메트릭 시계열은 retention 기간만 보존
     - agent-based 는 영구 제거 아님 (5단계 안내)
   "확인 (y/N):"

5. 삭제 호출
   recipes/delete-target.md
     - 서버:    /api/sms/hosts/delete    body: {parameter:[<resourceId>...]}
     - Web URL: /api/weburl/delete       body: {parameter:["weburl_<id>"...]}
     - SLO:     /api/cm/slo/delete       body: {parameter:[<id>...]}
     - 그 외 TBD type: UI fallback

6. agent-based 재출현 가드 (서버/DB/APM/KCM/NMS 만)
   ⚠️ 알려진 동작: SMS 에이전트가 살아있으면 다음 heartbeat 사이클 (5~10분) 안에 standby 재출현.
                   NKIAAI-539 검증 세션에서 109 server 삭제 → 5분 후 standby 재진입 직접 관찰됨.

   사용자에게 안내:
     a. 일시적 정리 (다시 등록할 거면) → 가드 불필요, 그대로 종료
     b. 영구 제거 (재출현 막아야 함) → 다음 중 선택:
        - 에이전트 docker stop / systemctl stop  (사용자 측 작업)
        - 관리 정책에서 자동 등록 끄기 (관찰된 동작 — TBD endpoint 확정 필요)

   본 스킬은 가드 자동화는 하지 않음 (에이전트 라이프사이클 = 별도 sub-skill 영역).
   대신 5~10분 후 자동 재확인 prompt:

      "에이전트 stop 하셨나요? (y) → 5분 후 standby 재출현 여부 자동 체크"
      "건너뜀 (N) → 사용자가 직접 모니터링"

7. 사후 검증
   - 삭제 직후: type 별 list-filter 또는 count 로 감소 확인
   - 5~10분 후 (가드 활성 시): /api/sms/standby-hosts/count?status=READY 가 0 인지
                              아니면 "재출현 — 에이전트 stop 안 됐을 가능성"

8. 보고
   - 삭제된 자원 / 실패한 자원 / 영향받은 알람 정의 수
   - 재출현 모니터링 결과 (가드 활성 시)
```

---

## 식별자 형식 type 별 비교

```
Web URL : weburl_<24-hex-mongo-id>     ← prefix 있음
서버    : MA_<hostname>_<timestamp>     ← prefix 없음, agent ID 그대로
SLO     : <24-hex-mongo-id>             ← prefix 없음
DB/APM/KCM/NMS : TBD                    ← 캡처 후 확정
```

> 일반 prefix rule 없음. 반드시 list-filter 응답 그대로 복사. 추측 금지.
> 상세 표는 [delete-target.md](../../../knowledge/polestar10/api/recipes/delete-target.md) 참조.

---

## 멱등성

이미 삭제된 식별자로 두 번째 호출:
- 응답 `success:true, data:"ok"` 또는 errorCode 없는 빈 결과
- count 가 변하지 않음 → 멱등 안전
- 실수로 중복 호출해도 OK

---

## 다중 삭제 batch 크기

- 한 번에 너무 많은 식별자 (>500개) 는 timeout 위험
- 권장 batch: 100개 이하
- 더 많으면 chunk 로 분할 호출

---

## 부분 실패 처리

```json
{"success":true,"data":{"failedCount":2,"successCount":3,"failedList":[...]}}
```

failedList 의 식별자만 모아 다음 항목과 함께 사용자에게 prompt:
- 재시도 (보통 transient)
- skip (이미 삭제된 상태)
- UI fallback
