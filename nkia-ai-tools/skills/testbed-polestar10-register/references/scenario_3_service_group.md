# Scenario 3 — 서비스 그룹 신규 생성 + 자원 이동

> "RCA-Testbed 그룹 새로 만들어서 자원 옮겨줘"
> "이 서버들 'plopvape' 그룹으로 묶어줘"

서비스 그룹 = tag 시스템의 `serviceGroup` key. **시스템 그룹** (groupId) 과 혼동 금지.

---

## Trigger 키워드

`서비스 그룹`, `그룹 만들`, `묶어`, `분류`, `tag`, `service group`

> "그룹" 만 들어오면 시스템 그룹·서비스 그룹 어느 쪽인지 한 번 더 확인:
> - "Default/Root 같은 구조적 그룹이면 1번, 서비스/제품/팀별 분류면 2번."

---

## Pre-conditions

- Bootstrap 완료
- 이동 대상 자원은 이미 등록된 상태 (시나리오 1 또는 UI)

---

## Dispatch flow

```
1. 그룹 의도 명확화
   - 시스템 그룹 (groupId, 정수, 고정 트리)
       → recipes/list-groups.md 로 조회만 가능, 신규 생성은 본 스킬 범위 밖.
         "현재 시스템 그룹 N개: …"  표시 후 종료
   - 서비스 그룹 (serviceGroupTagValue, 문자열 tag)
       → 이 시나리오 본문 진행

2. 그룹 이름 인터뷰
   - 사용자에게 그룹 이름 입력받기
   - recipes/cm/tag/key/list 로 기존 serviceGroup 값들 조회
     → 이미 같은 이름 있으면 "기존 그룹 사용 vs 다른 이름" prompt

3. 신규 그룹 생성
   recipes/service-group-tag.md "서비스 그룹 생성"
     ← /api/cm/tag/value/insert
        body: {parameter:{tagKey:"serviceGroup", tagValue:"<NAME>"}}

   ⚠️ 응답의 data.values 에 방금 insert 한 값이 안 보일 수 있음 — 어떤 자원에도 link 되기 전이라.
   정상.

4. 대상 자원 식별
   - 사용자가 이름으로 지목 → recipes/list-targets.md 의 type 별 list-filter 로 식별자 추출
     - 서버: hostname 매칭 → resourceId
     - Web URL: resourceName 매칭 → id
     - 그 외 type: 해당 list-filter (TBD 면 UI fallback)

5. 자원에 그룹 적용
   ⚠️ polestar10 의 자원 → 서비스 그룹 변경은 "register payload 갱신" 으로만 가능 (현 캡처 기준).
       기존 자원의 serviceGroupTagValue 를 직접 patch 하는 endpoint 는 미확정 (TBD).

   현실적 옵션:
     a. 신규 자원이라면 → 시나리오 1 흐름의 register payload 에 새 그룹 사용
     b. 기존 자원이라면 → UI fallback: 자원 상세 → 우측 정보 패널 → 서비스 그룹 dropdown 변경
        (또는 follow-up 캡처로 PATCH endpoint 확정)

   본 시나리오는 b 의 안내를 사용자에게 표시하고, 자동화 가능한 부분 (a) 만 dispatch.

6. 검증
   recipes/cm/tag/key/list 또는 cm/tag/resource/select/<resourceId> 로
   해당 자원의 tag 에 새 serviceGroup 값이 link 됐는지 확인
```

---

## 빈 그룹 정리

자원 0개에 link 된 서비스 그룹은 사용자에게 inline 으로 정리 prompt:

```
recipes/service-group-tag.md "서비스 그룹 삭제"
  ← /api/cm/tag/link/delete/value
     body: [{currentTagKey:"serviceGroup", currentTagValue:"<NAME>"}]
```

> path 비대칭 주의 — `/value/insert` 는 단수 object body, `/link/delete/value` 는 array body.

---

## 멱등성

같은 그룹 이름으로 두 번째 insert: 응답 그대로 `success:true` (이미 존재하더라도 에러 아님). 안전하게 호출 가능.

---

## 시스템 그룹과의 차이 정리 (사용자 안내용)

| 개념 | API | 자원 등록 시 필드 | 변경 가능 |
|---|---|---|---|
| 시스템 그룹 | `/api/cm/groups/list` (read-only via 본 스킬) | `groupId` (정수) | UI 만 |
| 서비스 그룹 | `/api/cm/tag/value/*` | `serviceGroupTagValue` / `tag` (문자열) | API + UI |

---

## TBD — 자원 → 그룹 이동 PATCH endpoint

현 캡처에서 미확정. 후속 작업:
1. 크롬 DevTools 로 UI 의 "서비스 그룹 변경" 클릭 시 발생하는 POST 요청 캡처
2. recipes/service-group-tag.md 에 추가 섹션 (`## 자원 → 그룹 link 변경`) 으로 추가
3. 본 시나리오 Step 5 의 b 옵션을 자동화로 승격

위 작업이 완료되기 전까지 Step 5 는 신규 자원만 자동, 기존 자원은 UI fallback.
