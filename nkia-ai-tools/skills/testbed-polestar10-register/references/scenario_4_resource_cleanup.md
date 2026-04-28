# Scenario 4 — 자원 삭제 + agent 재출현 가드

> "plopvape-db 삭제해줘"
> "테스트베드 정리 — 등록한 자원 다 빼"

자원 삭제는 type 별 **method/URL/body 가 모두 다름**. 추가로 두 가지 사후 효과를 챙겨야 함:
1. **agent 모델은 재출현** (SMS/APM/KCM — 에이전트 살아있으면 다음 heartbeat 에 standby 에 다시 등장)
2. **DPM 만 알람 cascade 가 다름** (unregister 해도 알람 즉시 안 사라짐 → orphan)

---

## Trigger 키워드

`삭제`, `지워`, `제거`, `정리`, `cleanup`, `delete`, `빼`

---

## Pre-conditions

- Bootstrap 완료

---

## Type 별 삭제 패턴

상세 표는 [recipes/delete-target.md](../../../knowledge/polestar10/api/recipes/delete-target.md) 의 풀 표 참조. 시나리오 dispatch 핵심:

| Type | URL | Method | identifier 형식 / body | 재출현? | 알람 동작 |
|---|---|---|---|---|---|
| Web URL | `/api/weburl/delete` | POST | `{parameter:["weburl_<id>"]}` | 안 함 | 즉시 같이 사라짐 |
| 서버 (SMS) | `/api/sms/hosts/delete` | POST | `{parameter:["MA_<host>_<ts>"]}` | ⚠️ 함 | 즉시 같이 사라짐 |
| **DPM** | **`/api/dpm/unregister/<id>`** | **GET** | (none, path 에 ID) | 안 함 (polling) | ⚠️ **orphan + auto-reattach by resourceId** |
| **APM** | `/api/apm/unregisterservice` | POST | `[{serviceId, category:"APM"\|"WPM"}]` | ⚠️ 함 | 추정: orphan + reattach (DPM 패턴 동일 가능) |
| **KCM** | `/api/kcm/standby-clusters/unregister` | POST | `{clusterId}` (단일 객체) | ⚠️ 함 | 추정: orphan + reattach |
| **NMS** | `/api/nms/v1/deleteResource/<id>` | POST | (none, path 에 ID) | 안 함 (polling) | 추정: orphan |
| SLO | `/api/cm/slo/delete` | POST | `{parameter:[<id>]}` | 안 함 | 즉시 같이 사라짐 |

> **DPM cascade rule**:
> - unregister 후 알람 정의는 **즉시 삭제 안 됨** — orphan 으로 남음
> - 같은 `resourceId` 로 재등록 → 알람 자동 reattach (의도적 패턴)
> - 다른 `resourceId` 로 등록 → alarm 영구 orphan (수동 정리 필요)

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
   각 자원이 어떤 type 인지 모르면 type 별 list 를 순회해 매칭:
     - Web URL: weburl/list-filter 의 resourceName → id (weburl_<...>)
     - 서버: sms/hosts-filter 의 hostname → resourceId (MA_<host>_<ts>)
     - DPM: dpm/<dbtype>/list 의 hostName/dbName → resourceId (numeric)
            ⚠️ dbtype 별 endpoint 분리 — 처음엔 type 모르므로 dbtypes 순회 또는
               cm/portal/configuration/list 로 통합 식별 후 dbtype 결정
     - APM: apm list 의 serviceName / category → serviceId (= serviceName)
     - KCM: kcm list 의 clusterName → clusterId (cluster-<uuid>)
     - NMS: nms/v1/list 의 systemName/ipAddress → resourceId (24-hex)
     - SLO: cm/slo/list-filter 의 name → id (registered:true 와 false 양쪽)
   매칭 실패: 후보 dropdown 표시 → 사용자 선택

3. 삭제 전 카운트
   - /api/cm/portal/configuration/count   (전체)
   - 각 type 의 /count                     (개별: weburl/count, dpm/<type>/list totalElements 등)
   ※ 비교용 baseline. 삭제 후 검증에 사용.

4. 사용자 확인
   삭제 대상 표 (이름 / type / 식별자) + 영향도:
     - **알람 정의 동반 삭제 vs orphan** (위 표 참조 — DPM 만 orphan)
     - 메트릭 시계열은 retention 기간만 보존
     - **agent-based (SMS/APM/KCM) 는 영구 제거 아님** — 다음 heartbeat 에 재출현 → step 6 가드 필요
     - **polling 기반 (DPM/NMS) 는 재출현 없음** — 가드 skip
   "확인 (y/N):"

5. 삭제 호출 — 위 표의 type 별 method/URL/body 그대로
   recipes/delete-target.md (Web URL/서버) 또는 dpm-lifecycle.md "삭제" /
   nms-lifecycle.md "삭제" / add-target.md "Unregister" (KCM/APM)

   ⚠️ DPM 은 GET method — 다른 type 과 헷갈리지 말 것
   ⚠️ APM unregister 는 service 단위 — 그 service 의 모든 agent 가 함께 제거됨

6. agent 재출현 가드 (SMS/APM/KCM 만 해당)
   ⚠️ SMS 에이전트 / APM 에이전트 / KCM 클러스터-에이전트가 살아있으면
       다음 heartbeat 사이클 (5~10분) 안에 standby 재출현.
       에이전트가 살아있으면 5~10분 후 자동 재진입.
   사용자에게 안내:
     a. 일시적 정리 (다시 등록할 거면) → 가드 불필요, 그대로 종료
     b. 영구 제거 (재출현 막아야 함) → 다음 중 선택:
        - 에이전트 docker stop / systemctl stop  (사용자 측 작업)
        - 관리 정책에서 자동 등록 끄기 (관찰된 동작 — TBD endpoint 확정 필요)
   본 스킬은 가드 자동화는 하지 않음 (에이전트 라이프사이클 = 별도 sub-skill 영역).
   대신 5~10분 후 자동 재확인 prompt:
     "에이전트 stop 하셨나요? (y) → 5분 후 standby 재출현 여부 자동 체크"
     "건너뜀 (N) → 사용자가 직접 모니터링"

   DPM/NMS 는 polling 모델 — 본 가드 skip + "polling 모델이라 재출현 걱정 없음" 한 줄 안내

7. 사후 검증
   - 삭제 직후: type 별 list-filter 또는 count 로 감소 확인
   - 5~10분 후 (agent 가드 활성 시):
       SMS: /api/sms/standby-hosts/count?status=READY
       APM: /api/apm/standby-agent/count
       KCM: /api/kcm/standby-clusters/count (or filter-step1 totalElements)
     0 이면 영구 제거 OK. 아니면 "재출현 — 에이전트 stop 안 됐을 가능성" 안내

8. (DPM 영구 제거 시 선택) Orphan 알람 정리
   DPM 만 해당. 영구 제거 사용자가 원하면:
     a. /api/alarm/alarm-definitions list 에서 해당 resourceId 의 알람 ID 수집
     b. /api/alarm/alarm-definition/delete 로 일괄 정리
   (재등록 시 알람 보존이 필요하면 step 8 skip — 같은 resourceId 로 register 하면 자동 reattach)

9. 보고
   - 삭제된 자원 / 실패한 자원 / 영향받은 알람 정의 수
   - agent 가드 모니터링 결과 (활성 시)
   - DPM orphan 알람 정리 여부
```

---

## 식별자 형식 type 별 비교

```
Web URL : weburl_<24-hex-mongo-id>     ← prefix 있음
서버    : MA_<hostname>_<timestamp>     ← prefix 없음, agent ID 그대로
DPM     : <numeric>                     ← polestar10 자동 부여 (예: "954854831")
APM     : serviceName + category        ← serviceId = serviceName 그대로
KCM     : cluster-<uuid>                ← cluster- prefix
NMS     : <24-hex-mongo-id>             ← prefix 없음
SLO     : <24-hex-mongo-id>             ← prefix 없음
```

> 일반 prefix rule 없음. 반드시 list 응답 그대로 복사. 추측 금지.
> 상세 표는 [delete-target.md](../../../knowledge/polestar10/api/recipes/delete-target.md) 참조.

---

## 멱등성

이미 삭제된 식별자로 두 번째 호출:
- 응답 `success:true, data:"ok"` 또는 errorCode 없는 빈 결과
- count 가 변하지 않음 → 멱등 안전
- 실수로 중복 호출해도 OK

DPM 의 unregister 도 멱등 — 같은 resourceId 두 번째 GET 호출 시 `success:true, data:"<id>"` 그대로 응답.

---

## 다중 삭제 batch 크기

- 한 번에 너무 많은 식별자 (>500개) 는 timeout 위험
- 권장 batch: 100개 이하
- 더 많으면 chunk 로 분할 호출
- DPM/NMS 는 path-based — 단일 호출 / 자원이라 항상 하나씩 (병렬 호출 가능하지만 권장 5개 동시)

---

## 부분 실패 처리

```json
{"success":true,"data":{"failedCount":2,"successCount":3,"failedList":[...]}}
```

failedList 의 식별자만 모아 사용자에게 prompt:
- 재시도 (보통 transient)
- skip (이미 삭제된 상태)
- UI fallback

APM 의 경우 응답이 `{"data":{"failedList":[...]}}` 형태 — failedList 가 비어있으면 전체 성공.
KCM 은 `{"registrationSucceedClusters":[...], "registrationFailedClusters":[...]}` — 두 배열 비교로 판단.
