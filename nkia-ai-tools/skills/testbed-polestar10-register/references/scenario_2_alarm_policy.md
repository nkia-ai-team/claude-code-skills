# Scenario 2 — 알람 정책 추가 (공통 / 개별)

polestar10 의 알람 정책은 두 종류 — 공통 정책(도메인별 임계치 템플릿) vs 개별 알람 정의(자원 1개 한정).
recipe 는 동일하게 `recipes/add-alert-policy.md` 를 사용하되 섹션이 다르다 (전반부=공통, 후반부=개별).

---

## Trigger 키워드 + 분기 판정

| 키워드 / 표현 | 분기 |
|---|---|
| `도메인`, `여러 자원`, `일괄 임계치`, `공통 정책`, `<vendor> 기본 정책` | Branch A — 공통 정책 |
| `<자원이름>에 알람`, `Lock 수`, `CPU 80%`, `이 서버`, `개별 알람`, `임계치` | Branch B — 개별 정의 |
| 위 둘 다 모호 | 사용자에게 분기 prompt |

분기 prompt 메시지 예:
```
알람 정책에는 두 가지 방식이 있습니다.
  1) 공통 정책 — 도메인 전체 (예: PostgreSQL 인스턴스 전부) 에 같은 임계치 일괄 적용
  2) 개별 정의 — 특정 자원 1개에 한정해 메트릭별 임계치 부여
어느 쪽?
```

---

## Pre-conditions (공통)

- Bootstrap 완료 ([bootstrap.md](bootstrap.md))
- 알람을 받을 자원이 polestar10 에 등록된 상태여야 매칭 가능 (등록은 시나리오 1)

---

## Branch A — 공통 정책 (Common Policy)

UI: **알람 > 정책 관리 > 공통 정책** 탭. polestar10 의 공통 정책은 **순수 신규 정의가 아니라 기존 default 정책 복사** 흐름.

### Dispatch flow

```
1. 도메인 선택
   사용자에게 dropdown:
     server / postgresql / mysql / oracle / tibero / cubrid /
     apm / kcm / weburl / ...
   (정확 목록은 /api/alarm/resource/domain/options 응답 — 세션 캐시)

2. source 정책 후보 조회
   recipes/add-alert-policy.md "공통 알람 정책 — 목록"
     ← /api/alarm/policys
   응답 content[] 에서 default:true 인 항목 필터링
     → 사용자에게 source 후보 dropdown 제시
        (보통 "<도메인> 기본 임계치" 같은 이름)

3. 정책 메타 인터뷰
   - name (UI 표시용. 예: "RCA-Testbed PostgreSQL 임계치")
   - description
   - tagValue (보통 name 과 동일. 자원 등록 시 alarmPolicy 태그로 매칭됨)
   - role (권한 부여 대상. 보통 admin role)
     ⚠️ 현재 role list endpoint 미확정 (TBD) — 알려진 admin roleId 가 있으면 default,
        없으면 사용자에게 24-hex roleId 직접 입력 prompt + UI fallback 안내

4. 이름 중복 검증
   recipes/add-alert-policy.md "이름 중복 검증"
     ← /api/alarm/policys/add/validate/name/duplicate
   중복이면 다른 이름으로 재인터뷰

5. 정책 추가
   recipes/add-alert-policy.md "추가 (기존 정책 복사 기반)"
     ← /api/alarm/policys/add
        body: {name, description, enable:true, copyId:<source>, tagValue,
               authorityInfos:[{roleId, permission:15}], domain}
   ⚠️ 응답에 새 정책의 id 가 안 옴 → 다음 단계 필수

6. 검증 + ID 회수
   recipes/add-alert-policy.md "공통 알람 정책 — 목록" 재호출
     ← /api/alarm/policys
   응답에서 방금 만든 name 매칭해 id 추출 → 사용자에게 표시

7. (선택) 정책 내 정의 customize
   복사한 source 의 임계치를 그대로 쓰면 step 6 으로 끝.
   변경하려면:
     /api/alarm/policy/definitions   (조회)
     /api/alarm/policy/definitions/add / delete   (수정)
   → 보통 사용자가 UI 에서 직접 조정. 본 스킬에서는 안내만.

8. 자원과 연결
   ⚠️ 정책 → 자원 매칭은 자원의 tag (`alarmPolicy` 태그) 가 정책의 tagValue 와 같아야 발동.
       기존 자원에 이 태그를 붙이는 PATCH endpoint 는 미확정 (시나리오 3 PATCH TBD 와 동일 한계).
   현실적 옵션:
     a. 신규 자원이라면 → 시나리오 1 의 register payload 의 tag 필드에 새 tagValue 사용
     b. 기존 자원이라면 → UI fallback: 자원 상세 → 태그 관리 → alarmPolicy 추가

9. 보고
   - 정책 이름 / 도메인 / source 정책 / role
   - 매칭된 자원 수 (등록 직후엔 0 — tag link 후 자동 업데이트)
```

### 멱등성

- 같은 (name, domain) 으로 두 번째 호출 시 step 4 의 중복 검증이 잡아냄 → skip / 다른 이름 prompt
- step 6 에서 list 로 id 회수 후 캐시 → 같은 세션에서 재사용 가능

### 자주 쓰는 도메인 + source 정책

| 도메인 | 추천 source 정책 (default:true 후보) |
|---|---|
| `server` | "Server 기본 임계치" (CPU/MEM/DISK) |
| `postgresql` | "PostgreSQL 기본 임계치" (Lock/Session/BufferHit) |
| `apm` | "APM 기본 임계치" (응답시간/에러율) |
| `kcm` | "KCM 기본 임계치" (Pod restart/메모리) |
| `weburl` | "WebURL 기본 임계치" (응답시간/Availability) |

> 정확한 source 이름은 매번 list 조회로 확인. 도메인 이름이 바뀌었을 가능성 있음.

---

## Branch B — 개별 알람 정의 (Individual Definition)

UI: **알람 > 정책 관리 > 개별 정책** 탭. 자원 1개에 메트릭별 임계치 직접 부여.

### Dispatch flow

```
1. 대상 자원 식별
   - 사용자가 이름으로 지목 → recipes/list-targets.md 의 type 별 list-filter 로
     resourceName / hostname 매칭해 confId 추출
   - 매칭 실패: dropdown (top 30) 보여주고 선택받기

2. 메트릭 카탈로그 조회
   recipes/add-alert-policy.md "메트릭 카탈로그 조회 (필수 — 알람 추가 전 선행)"
     ← /api/measurement/definitions/resource-type
        body: {parameter:{resourceType:"<resourceType>"}}
   응답에서 사용자에게 보여줄 후보:
     - id (= measurementDefinitionId)
     - description (한글 설명)
     - units (COUNT / PERCENTAGE / MILLISECONDS / BYTES …)
     - alias (= measurementAlias)

   ⚠️ 메트릭 prefix 는 자원 resourceType 과 정확히 일치해야 함
      (postgresql.Database vs postgresql.PostgreSQL 등 layer 구분 — DB 단위 vs 인스턴스 단위)

3. 임계치 인터뷰
   기본은 4-step (LEVEL1~LEVEL4). 사용자에게:
     - operator (>= / <= / > / < / == 등)
     - LEVEL2/3/4 의 numericThreshold (LEVEL1 은 정상 범위)
     - 또는 "표준 4-step 자동" → recipes/add-alert-policy.md 의 PostgreSQL Lock 예시처럼 default 값 사용

4. 알람 정의 추가
   recipes/add-alert-policy.md "추가 (POST /api/alarm/alarm-definition)"
     ⚠️ NPE 함정 — 풀 스키마 모두 채워야 detail drawer 정상:
        top-level: measurementType, measurementAlias, activeAlarmPolicy, maxAlarmsPerMin
        condition: measurementType, conditionText, units (메트릭 units 일치)

5. 검증
   recipes/add-alert-policy.md "상세 조회"
     ← /api/alarm/alarm-definition/detail
   - data.conditions[] 가 4-step 그대로 들어갔는지
   - UI 에서도 drawer 가 열리는지 (선택, NPE 가드)

6. 보고
   - 알람 이름 / 대상 자원 / 메트릭 / 4-step 임계치 표
   - UI 경로 안내 (알람 > 정책 관리 > 개별 정책)
```

### 자주 쓰는 메트릭 빠른 가이드

| resourceType | 자주 쓰는 메트릭 | units |
|---|---|---|
| `server.Server` | `server.Server_cpuUtil` / `_memUtil` / `_fileSystemUtil` | PERCENTAGE |
| `weburl.Weburl` | `weburl.Weburl_totalTimeMs` / `_availability` | MILLISECONDS / BOOLEAN |
| `postgresql.Database` | `postgresql.Database_LockCount` / `_sessionCount` / `_bufferHitRatio` | COUNT / PERCENTAGE |
| `apm.Agent` | `apm.Agent_responseTime` / `_errorRate` | MILLISECONDS / PERCENTAGE |
| `kcm.Pod` | `kcm.Pod_cpuUsage` / `_memUsage` / `_restartCount` | PERCENTAGE / COUNT |

전체 수치는 [add-alert-policy.md "자주 쓰일 resourceType 별 메트릭 카운트"](../../../knowledge/polestar10/api/recipes/add-alert-policy.md) 표 참조 — 매번 카탈로그 조회로 동적 확인 권장.

### 멱등성

같은 (대상 자원 + 메트릭) 조합으로 두 번째 호출:
- `alarm/alarm-definitions` list 에서 `targetConfIds` + `measurementDefinitionId` 매칭 검색
- 이미 있으면: skip / 임계치만 update / 삭제 후 재생성 prompt
- update 는 `/api/alarm/alarm-definition/update` (TBD) 또는 delete + add 조합

### 실패 패턴

| 증상 | 원인 | 처리 |
|---|---|---|
| `success:true` 인데 UI drawer 안 열림 | 풀 스키마 누락 (NPE 함정) | recipes/add-alert-policy.md 의 풀 payload 사본 사용 |
| `errorCode:"POLESTAR_xxxx"` units 관련 | condition.units ≠ 메트릭 catalog units | 카탈로그 다시 조회해 정확히 복사 |
| `resourceType` 불일치 NPE | DB/PostgreSQL 두 layer 혼동 | DB 인스턴스 vs Database 단위 구분 |

---

## 어느 쪽을 권할지 — 사용자 가이드

| 상황 | 추천 |
|---|---|
| 같은 도메인 자원 ≥ 5개에 같은 임계치 | Branch A (공통) |
| 특정 자원 1~2개에만 특별한 임계치 | Branch B (개별) |
| 테스트베드 처음 셋업 + default 임계치로 시작 | 시나리오 1 의 register 시 anomalyPolicyTagValue 만 사용 (시스템 default 정책) — 별도 알람 정책 불필요 |
| default 임계치로 부족함이 확인된 후 | A → 도메인 전반 / B → 핀포인트 |

전부 [add-alert-policy.md](../../../knowledge/polestar10/api/recipes/add-alert-policy.md) 에 self-documented.
