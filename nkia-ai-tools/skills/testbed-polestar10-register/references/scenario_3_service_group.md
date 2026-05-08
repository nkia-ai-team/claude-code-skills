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

   - **신규 자원**: 시나리오 1 흐름의 register payload 에 `serviceGroupTagValue` 로 그룹 이름 포함.
   - **기존 자원**: `recipes/service-group-tag.md` 의 "자원 → 그룹 link 변경" 사용.
       endpoint: `POST /api/cm/tag/resource/insert`
       body: `{confId, tagType:"CUSTOM", key:"serviceGroup", value:"<NEW_GROUP>", tagDataType:"STRING"}`
       (upsert — 신규 link · 기존 link 갱신 둘 다 동일 endpoint)

   대상 자원의 `confId` 추출 패턴:
     - DPM: `<dbtype>/list` 응답의 `confId` 또는 `<resourceId>_<dbtype>.<DBType>`
     - 서버: `sms/hosts-filter` 응답의 `confId` 또는 `MA_<host>_<ts>_server.Server`
     - 그 외: `tag/resource/select/<id>` 로 검증 후 사용

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

## 해소된 항목 — 자원 → 그룹 이동

이전 미확정(TBD) 이었던 PATCH endpoint 가 HAR 캡처(2026-05-08)로 확정:
- endpoint: `POST /api/cm/tag/resource/insert`
- body: `{confId, tagType, key, value, tagDataType}` (parameter wrapping 없음)
- 동작: upsert — 같은 (confId, key) 조합에 link 가 이미 있으면 value 갱신, 없으면 신규 link

상세 body shape · 검증 절차는 `recipes/service-group-tag.md` "자원 → 그룹 link 변경" 섹션.
