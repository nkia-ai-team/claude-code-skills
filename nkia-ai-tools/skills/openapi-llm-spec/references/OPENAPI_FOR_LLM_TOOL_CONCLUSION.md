# OpenAPI를 LLM Tool로 쓰기 위한 작성 가이드

> **갱신일**: 2026-04-28
> **적용 기준 파일**: `sms.openapi.json` (Polestar10 SMS 모듈, OpenAPI 3.1.0). 본 문서의 모든 예시는 이 파일에서 직접 인용했다.
> **목표**: 새 endpoint 하나를 LLM 호출 가능한 상태로 작성하기 위해 필요한 모든 필드, 허용 값, 기본값을 명시한다.
> **형식**: 최종 파일은 **JSON**으로 저장한다 (가독성을 위해 본 문서 일부 예시는 indent된 JSON으로 표기).

## 0. 자동화 추출 원칙 (절대 기준)

본 가이드는 **자동화 스킬** 이 Spring/TS 소스에서 OpenAPI JSON 을 추출하는 contract. 다음 3원칙을 어기지 않는다:

1. **Hand-curate 금지** — 사람이 한글 라벨/메시지를 직접 적어 사전 파일에 박지 않는다
2. **모든 구조·필드·값 LLM 추정 금지** — Claude 의 도메인 상식으로 추정해 박지 않는다. 추정 금지 영역:
   - **enum / error code 한글 매핑** (예: `LINUX → "리눅스"`)
   - **응답 schema 의 필드 (property name)** — `Map<String,Object>` / `ApiResponseData<Object>` 같은 generic erasure 응답이라도 service 코드 (`...ServiceImpl.java`) 본문까지 따라가서 `data.put("xxx", ...)` 호출의 실제 키만 박는다 (PoC 발견 #8)
   - **응답 example 의 필드** — schema 에 박힌 필드와 1:1 동일해야 함 (없는 필드 추정 ❌, §11 #16 검증)
   - **description 의 "반환 핵심 필드: ..." 나열** — Java 코드에서 실제 발견된 필드명만. 도메인 상식 (`agentVersion`, `agentPort`) 으로 채우는 것 ❌
   - **허용 영역**: 메서드명/DTO명/필드명 자체 기반의 한국어 자연어 — `summary` 본문 / `description` 자연어 설명 / `examples[].summary` 한국어 자연어 질의 (자연어 생성은 추출이 아님)
3. **Source 없으면 영문 echo / 빈 객체** —
   - enum / error code 한글 source 없을 때: `"LINUX": "LINUX"`, `"POLESTAR_00500": "POLESTAR_00500"` 식 키 자체 echo
   - 응답 필드 source 없을 때 (외부 lucida-common 타입 등 reach 밖): `additionalProperties: true` + 빈 example (`{}`) + description 에 "응답 구조는 service 구현 의존, 정적 추출 불가" 명시. **추정으로 필드 박는 것 ❌**
   - 자연어 매칭 보강은 `examples[].summary` 의 한국어 표현으로 (§7.2 표현 다양성 룰)

추출 source 우선순위 / 위치는 §6 각 vocab 섹션의 **Source / Reality 룰** 참조. 응답 schema 작성 절차는 스킬 §5 Phase 4 참조.

---

## 목차

0. [자동화 추출 원칙 (절대 기준)](#0-자동화-추출-원칙-절대-기준)
1. [이 문서 사용법](#1-이-문서-사용법)
2. [5개 정보 그룹](#2-5개-정보-그룹)
3. [루트 메타 (file header)](#3-루트-메타-file-header)
4. [G1. Tool 식별 정보](#4-g1-tool-식별-정보)
5. [G2. Input Schema](#5-g2-input-schema)
6. [G3. Vocabulary (root extensions)](#6-g3-vocabulary-root-extensions)
7. [G4. Examples](#7-g4-examples)
8. [G5. 실행 메타](#8-g5-실행-메타)
10. [완성형 예시 — `/api/sms/hosts-filter`](#10-완성형-예시--apismshosts-filter)
11. [검증 체크리스트 (CI)](#11-검증-체크리스트-ci)

---

## 1. 이 문서 사용법

새 endpoint를 추가할 때 다음 순서로 채운다.

| 순서 | 작업                  | 참조 섹션 |
| -- | ------------------- | ----- |
| 1  | endpoint 패턴 결정       | §9    |
| 2  | G1 식별 필드 작성         | §4    |
| 3  | G2 Input Schema 작성  | §5    |
| 4  | G5 실행 메타 작성         | §8    |
| 5  | G4 Examples 작성      | §7    |
| 6  | G3 root vocabulary 참조 | §6    |
| 7  | CI 검증               | §11   |

§9의 4가지 패턴(List-filter / Detail / Action / Measurement) 중 하나에 정확히 맞춘다. 패턴을 벗어나는 endpoint는 추가하지 않는다.

---

## 2. 5개 정보 그룹

| #  | 그룹             | 누락 시 발생하는 실패        | 채워야 하는 핵심                                                                    |
| -- | -------------- | -------------------- | ---------------------------------------------------------------------------- |
| G1 | Tool 식별        | LLM이 잘못된 endpoint 선택  | `operationId`, `summary`, `description`, `tags`, `x-side-effect`, `x-llm-intent` |
| G2 | Input Schema   | LLM이 인자 값을 못 채움       | endpoint별 inline schema, `additionalProperties: false`, 모든 property `required`, `enum`/`default`/`example` |
| G3 | Vocabulary     | 한국어→코드 변환 실패, ID 환각   | root `x-grids`, `x-measurement-catalog`, `x-error-codes`, `x-i18n`, `x-semantic-types`, `x-tagfilter-grammar`, `x-time-filter-modes` |
| G4 | Examples       | 정확도 부족              | 요청 examples **3 ~ 5 개 강제** (메타라벨 금지, NL 질의만), **응답 200 `example` 1 개 + `data` shape 인라인 정의 (placeholder `{type: null}` 금지, action 은 `x-empty-data: true` 명시)** |
| G5 | 실행 메타          | HTTP 호출 실패           | `servers`, `securitySchemes` + `security`, 4xx/5xx 응답 정의, `x-envelope`, `x-error-codes-applicable` |

- G1·G2: LLM 인지 정확도
- G3·G4: 도메인 특수성 (한국어 처리)
- G5: 실행 가능성

---

## 3. 루트 메타 (file header)

`sms.openapi.json` 그대로:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title":   "Polestar10 SMS module API — Goal-state exemplar",
    "version": "10.2.x-exemplar",
    "description": "Hand-curated OpenAPI 3.1 spec for the Polestar10 sms module."
  },
  "servers": [
    { "url": "https://polestar.example.com", "description": "Polestar10 production base URL (replace per deployment)" },
    { "url": "/",                            "description": "Same-origin (when Polestar UI mounts API on its own host)" }
  ],
  "security": [{ "cookieAuth": [] }]
}
```

| 필드        | 필수 | 형식                                              | 작성 규칙                                       |
| --------- | -- | ----------------------------------------------- | ------------------------------------------- |
| `openapi` | ✅  | 고정 문자열 `"3.1.0"`                                  | 3.0.x는 사용하지 않는다.                            |
| `info.title` | ✅ | string                                          | 모듈명 명시.                                     |
| `info.version` | ✅ | string                                       | 배포 버전 또는 `*-exemplar`.                      |
| `servers` | ✅  | 배열 (절대 URL 1개 + `"/"` 1개)                       | `{{template}}` 같은 미해결 변수 금지.                |
| `security`| ✅  | `[{ "cookieAuth": [] }]`                          | 글로벌 default. operation에서 override 가능.       |

---

## 4. G1. Tool 식별 정보

LLM이 "이 사용자 질의에 어느 endpoint를 써야 하는가?"를 결정할 때 읽는 필드.

### 4.1 필수 필드

| 필드               | 필수 | 형식                                                                            | 작성 규칙                                                                |
| ---------------- | -- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `operationId`    | ✅  | string, camelCase                                                             | 파일 내 unique. 한글·공백·중복 금지. 예: `getHostListByGridFilter`              |
| `summary`        | ✅  | string, 한국어, 30~60자                                                           | 동사+목적어 형태. 예: `"호스트(서버) 목록을 페이지/필터/정렬 조건으로 조회"`                    |
| `description`    | ✅  | markdown, 한국어, 100~200토큰                                                      | ① 한 문장 핵심 ② 반환 핵심 필드(한글 라벨 포함). 자연어 질의 예시는 여기 두지 않고 `examples[].summary`에 둔다. |
| `tags`           | ✅  | string array (1개)                                                             | 도메인 prefix 일관 사용. 예: `["SMS - Host"]`                              |
| `x-side-effect`  | ✅  | enum (단일 값)                                                                   | `read` / `write` / `delete` / `download` 중 하나                       |
| `x-llm-intent`   | ✅  | string array (1개 이상)                                                          | `list`, `detail`, `read`, `create`, `update`, `delete`, `export`, `search`, `filter`, `metric` 중 |

### 4.2 `x-side-effect` vs `x-llm-intent` — 둘 다 필수

| 필드              | 목적                              | 사용 단계         | 값 예                       |
| --------------- | ------------------------------- | ------------- | -------------------------- |
| `x-llm-intent`  | 의미 분류. 사용자 질의 ↔ endpoint 매칭       | 라우팅·검색       | `list`, `metric`, `update` |
| `x-side-effect` | 안전 가드. 데이터 변경 차단                | 호출 전 화이트리스트 검증 | `read`, `write`, `delete`  |

`x-llm-intent`만으로 의미 추론이 가능해도, `x-side-effect`가 없으면 라우터가 변경성 endpoint를 후보에 올린다. 둘 다 필수.

### 4.3 안티패턴 vs 정확한 작성

```json
// ❌ 나쁨 — operationId 의미 없음, summary 부족, x-side-effect 누락
{ "operationId": "post1", "summary": "호스트 목록 조회" }

// ✅ 좋음 (sms.openapi.json /api/sms/hosts-filter 그대로)
{
  "operationId":   "getHostListByGridFilter",
  "summary":       "호스트(서버) 목록을 페이지/필터/정렬 조건으로 조회",
  "tags":          ["SMS - Host"],
  "x-side-effect": "read",
  "x-llm-intent":  ["list", "search", "filter"],
  "description":   "등록된 서버(호스트, 장비) 의 목록 조회. CPU/메모리/OS 등 조건으로\n필터·페이지네이션·정렬 가능.\n\n반환 필드:\n시스템 이름(hostname), IP, CPU 사용률(cpuUtil), 메모리 사용률(memUtil),\nOS, 가용성(availabilityStatus), 관리상태(managementStatus)"
}
```

---

## 5. G2. Input Schema

LLM이 인자 값을 채울 때 읽는 구조. **strict mode 호환을 강제한다.**

### 5.1 모든 object schema에 적용되는 규칙

| #  | 규칙                                                          | 비고                                                |
| -- | ----------------------------------------------------------- | ------------------------------------------------- |
| 1  | `type: "object"` 명시                                          | 모든 object schema.                                  |
| 2  | `additionalProperties: false`                               | 모든 object schema. LLM hallucination 차단.            |
| 3  | 모든 property 를 `required` 배열에 포함                              | default 있는 optional 도 포함. 진짜 보내지 않을 수 있는 필드는 `nullable: true`. |
| 4  | 모든 property 에 `description` + `type`                         | string 보다 enum/integer/boolean 우선.                  |
| 5  | 가능한 모든 곳에 `enum`                                              | 자유 string 은 hallucination 원인.                      |
| 6  | optional 필드에 `default`                                       | strict mode 에서 LLM 이 default 를 명시해 보냄.             |
| 7  | 모든 property 에 `example`                                      | 응답 200 예시는 schema 옆에 1 개.                          |
| 8  | 제약 명시: `minimum`, `maximum`, `minLength`, `maxLength`, `minItems`, `maxItems`, `format`, `pattern` | 가능한 한 좁혀서 명시.       |

### 5.2 endpoint 별 inline schema 원칙

- request body schema 는 endpoint 마다 inline 으로 풀어 쓴다. 단일 공용 DTO 에 `$ref` 만 거는 방식 ❌
- 단, 모든 endpoint 가 동일 모양으로 받는 공용 타입은 `$ref` ✅ (예: `TimeFilter`)
- path / query parameter 도 동일 룰 (`description` + `type` + `enum`/`format`/`example` 필수)
- **외부 lucida-common 타입 (`Map<String,Object>`, `ApiResponseData<Object>`, `Page<T>`, `LinkedHashMap`, `Authority`, Spring Data Pageable/Sort 등 우리 reach 밖 타입) 은 §0 #3 fallback 적용** — `additionalProperties: true` + 빈 example (`{}`) + description 에 "외부 타입, 정적 추출 불가" 명시. 추정으로 필드 박지 않음 (HARD RULE / §0 #2 #3, 스킬 §3 #9, 스킬 §5 Phase 4 절차)

### 5.3 chain call — `x-source-endpoint` / `x-source-field` / `x-semantic-type` / `x-external`

다른 endpoint 의 응답에서 값을 가져오는 경우 출처를 명시한다.

```json
{
  "name": "resourceId",
  "in": "path",
  "required": true,
  "schema": { "type": "string" },
  "description": "서버 리소스 식별자 (보통 'MA_' 접두). /api/sms/hosts-filter 응답의 resourceId 필드 사용.",
  "example": "MA_LINUX_TEST_SERVER_01",
  "x-source-endpoint": "/api/sms/hosts-filter",
  "x-source-field":    "$.data.content[*].resourceId",
  "x-semantic-type":   "server_resource_id"
}
```

**정책 (chain 동작 보장 우선)**:

| 확장                  | 필수 | 형식           | 설명                                                         |
| ------------------- | -- | ------------ | ---------------------------------------------------------- |
| `x-source-endpoint` | ✅  | endpoint path | 이 값의 출처 endpoint. **chain router 가 ID 후보 목록을 가져올 곳**         |
| `x-source-field`    | ✅  | JSONPath      | 출처 응답 안에서의 위치 (표준 패턴은 §5.4)                                 |
| `x-semantic-type`   | ▲  | string        | root `x-semantic-types` 의 키. **추출 가능 시 채움. 도메인 간 ID 호환성 판단용** |
| `x-external`        | ▲  | boolean       | `true` 면 외부 시스템 ID (free-form, source endpoint 없음). `x-source-endpoint` / `x-source-field` 면제. **`x-semantic-type` 만 박혀있을 때 chain 불가 시그널** |

> **결정 근거**: chain 동작 (`x-source-endpoint` + `x-source-field`) 이 1순위. `x-semantic-type` 은 도메인 간 ID 충돌 판단에 유용한 부가정보지만 없어도 chain 자체는 동작. 단 `x-source-endpoint` 가 진짜 없는 외부 ID (예: `if_id`, `job_id` 같은 외부 시스템 식별자) 는 거짓 source 박지 말고 `x-external: true` 로 명시.

**도메인 일관성 (CI #5 강제)**: 한 도메인 안의 모든 path_param 은 다음 중 하나에 정확히 해당:
1. **chain 가능**: `x-source-endpoint` + `x-source-field` 둘 다 보유 (sem 은 옵션)
2. **외부 ID**: `x-external: true` (sem 만 보유 가능)

위 두 케이스 외 (예: sem 만 있고 src 없으면서 `x-external` 도 없음) → CI 위반.

#### 5.3.1 body 필드도 chain 의무 (path param 과 동일 정책)

> **중요**: chain meta 는 **path param 만의 문제가 아님**. body 안의 ID-shape 필드도 LLM 이 값을 어디서 가져올지 모르면 호출 불가. v1 단계에서 path param 만 적용된 게 발견된 갭 (642 fields 누락 — 도메인별 분포 INDEX.md 참조).

**ID-shape 필드 자동 검출 룰** (CI 가 grep):
- naming: `*Id` / `*Ids` / `*Key` / `*Name` (단 `name`/`displayName`/`hostName` 같은 free-form label 은 제외 — `description` 에 free-form 명시)
- 패턴 예: `agentIds`, `serviceId`, `resourceId`, `traceID`, `interfaceKey`, `userId`, `roleIds`

**의무 사항**: 위 패턴에 매칭되는 body 필드는 path param 과 **동일한 chain meta 박기**:

```json
"properties": {
  "agentIds": {
    "type": ["array", "null"],
    "items": { "type": "string" },
    "example": ["tomcat10"],
    "description": "분석 대상 에이전트 ID 배열. /api/apm/agents/list-filter 응답의 agentId 필드 사용.",
    "x-source-endpoint": "/api/apm/agents/list-filter",
    "x-source-field":    "$.data.content[*].agentId",
    "x-semantic-type":   "apm_agent_id"
  }
}
```

**Array 필드 (`*Ids`)**: items 가 ID 면 위와 같이 schema 자체에 chain meta 박음 (items.x-source-* 가 아니라 array 자체). LLM 은 array 면 multi-select 로 해석.

**External 케이스**: 외부 시스템 credential / token / 클라우드 ID (`awsAccessKeyID`, `azureClientID`, `gcpProjectID`, `if_id`, `job_id`) 는 `x-external: true` 박기.

**Free-form label 면제**: `name`/`displayName` 같이 사용자가 자유 입력하는 label 은 chain 면제. 단 `description` 에 "사용자 자유 입력" 명시.

### 5.4 `x-source-field` 표준 JSONPath 패턴

| 응답 envelope    | JSONPath 패턴                            | 예                                       |
| -------------- | -------------------------------------- | --------------------------------------- |
| paged (가장 흔함)  | `$.data.content[*].<field>`            | `$.data.content[*].resourceId`          |
| object (단건)    | `$.data.<field>`                       | `$.data.resourceId`                     |
| array (목록)     | `$.data[*].<field>`                    | `$.data[*].agentId`                     |
| 중첩            | `$.data.content[*].<sub>[*].<field>`   | `$.data.content[*].agents[*].agentId`   |

### 5.5 `x-source-catalog` — 본 operation 메타에서 값 가져오기

```json
{
  "field": {
    "type": "string",
    "description": "필터 대상 컬럼명. operation의 x-allowed-grid-filter-fields 안에 있어야 함.",
    "x-source-catalog": "operation.x-allowed-grid-filter-fields"
  }
}
```

| 확장               | 형식        | 설명                                          |
| ---------------- | --------- | ------------------------------------------- |
| `x-source-catalog` | string    | 값 출처 (다른 endpoint 가 아니라 본 operation 의 메타 필드) |

---

## 6. G3. Vocabulary (root extensions)

도메인 사전은 **루트 레벨 `x-*` 확장**에 1번 정의하고 endpoint 는 키로 참조한다.

### 6.0 vocab 도메인 정책 (transfer 금지)

**원칙**: 각 도메인은 자기 controller 가 실제 지원하는 vocab 만 박는다. 다른 도메인의 vocab 을 빌려오지 (transfer) 않는다.

| key | 정책 |
| --- | --- |
| `x-tagfilter-grammar` | controller 가 `tagFilters` 파라미터를 실제로 받는 도메인만 보유. 미지원 도메인은 root `x-vocab-supported.tagfilter: false` 명시 |
| `x-time-filter-modes` | controller 가 `timeFilter` / `TimeFilter` 를 실제로 받는 도메인만 보유. 미지원은 `x-vocab-supported.timefilter: false` |
| `x-measurement-catalog` | controller 가 measurement / metric API 를 실제로 노출하는 도메인만. 미지원은 `x-vocab-supported.measurement: false` |
| `x-grids` | grid 컬럼 API 를 노출하는 도메인만. 미지원은 `x-vocab-supported.grid: false` |
| `x-semantic-types` | path_param chain 이 1건 이상 있는 도메인은 필수. 외부 ID 만 있으면 빈 객체 (`{ "_description": "..." }`) 박고 `x-vocab-supported.semantic_types: false` 도 명시 |

**root `x-vocab-supported` 마커** (모든 도메인 필수):

```json
"x-vocab-supported": {
  "_description": "이 도메인이 실제로 지원하는 vocab 종류. false 인 키는 spec 에 root 정의 없음 — LLM 은 해당 발화 (예: '최근 1시간') 를 raw param 으로만 전달.",
  "tagfilter":      true,
  "timefilter":     true,
  "measurement":    false,
  "grid":           true,
  "semantic_types": true
}
```

> **결정 근거**: vocab 은 controller 본문이 받는 파라미터 형식의 명시이므로 다른 도메인 vocab 을 복사하면 없는 기능을 있다고 거짓말하게 됨. 미지원 도메인은 `false` 로 명시해 LLM 이 시간/태그 발화를 시도하지 않도록 신호.

### 6.1 `x-semantic-types` — ID 종류 → 출처 endpoint 매핑

체인 호출 자동 계획용.

```json
"x-semantic-types": {
  "_description": "ID 종류 → 출처 endpoint 매핑. chain-call 자동 계획에 사용.",
  "server_resource_id": {
    "description": "서버 리소스 식별자 (보통 'MA_' 접두)",
    "providers":   ["/api/sms/hosts-filter"],
    "field_name":  "resourceId",
    "label_field": "hostName",
    "example":     "MA_LINUX_TEST_SERVER_01"
  }
}
```

| 키             | 필수 | 형식         | 설명                                                |
| ------------- | -- | ---------- | ------------------------------------------------- |
| `description` | ✅  | string     | 이 ID 종류의 의미                                        |
| `providers`   | ✅  | string[]   | 이 ID 를 발급/조회하는 endpoint path 목록. 비어있을 수 있음 (예: 세션) |
| `field_name`  | ✅  | string     | 응답 안에서 ID 가 들어있는 필드명                              |
| `label_field` | ✅  | string\|null | 사용자에게 보여줄 라벨이 들어있는 필드명. 없으면 null                |
| `example`     | ✅  | string     | 실제 ID 1 개                                          |

### 6.2 `x-tagfilter-grammar` — `tagFilters` DSL 문법

```json
"x-tagfilter-grammar": {
  "_description": "tagFilters 구조화 형식. 배열 원소 1건 = clause 1건. 원소 간 AND.",
  "clause_shape": {
    "key":   "string. 예: confType, tag.<name>, os, hostName",
    "op":    "= | != | IN | NOT IN",
    "value": "string (단일) | string[] (IN/NOT IN 시)"
  },
  "common_keys": {
    "confType":   "리소스 타입. sms 모듈은 거의 항상 'server'",
    "tag.<key>":  "사용자 태그. 예: tag.env, tag.role",
    "os":         "OS 타입 (OsTypeEnum 멤버)",
    "hostName":   "호스트 이름 직접 지정"
  },
  "wire_format": {
    "single_value":   "key op value      (예: 'confType = server')",
    "list_value":     "key op [a, b, c]  (예: 'tag.env IN [prod, stg]')",
    "string_quoting": "영숫자는 그대로; 공백/특수문자는 single-quoted"
  },
  "compound": "tagFilters 배열 원소 간 AND. 한 문자열 내부 AND/OR 미지원.",
  "note":     "operation의 x-default-filter.tagFilters에 명시된 clause는 호출 시 반드시 포함."
}
```

직렬화 예:

| 구조화 입력                                              | wire 문자열                       |
| -------------------------------------------------- | ----------------------------- |
| `{ key: "confType", op: "=", value: "server" }`     | `"confType = server"`         |
| `{ key: "os", op: "=", value: "LINUX" }`            | `"os = LINUX"`                |
| `{ key: "tag.env", op: "IN", value: ["prod","stg"] }` | `"tag.env IN [prod, stg]"`    |

### 6.3 `x-time-filter-modes` + `TimeFilter` schema

`TimeFilter` 는 component schema 1개로 정의하고, 모든 endpoint 가 `$ref` 로 참조한다.

**Component schema** (`#/components/schemas/TimeFilter`):

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["mode"],
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["LIVE","MIN_15","MIN_30","HOUR","HOUR_3","NOW","TODAY",
               "DAY_3","WEEK","MONTH","MONTH_3","MONTH_6","YEAR","CUSTOM"],
      "x-enum-descriptions": {
        "LIVE": "실시간", "MIN_15": "최근 15분", "MIN_30": "최근 30분",
        "HOUR": "최근 1시간", "HOUR_3": "최근 3시간", "NOW": "현재",
        "TODAY": "오늘", "DAY_3": "최근 3일", "WEEK": "최근 1주",
        "MONTH": "최근 1개월", "MONTH_3": "최근 3개월", "MONTH_6": "최근 6개월",
        "YEAR": "최근 1년", "CUSTOM": "사용자 지정"
      }
    },
    "startTime": { "type": "integer", "format": "int64", "description": "시작 시각 (epoch milliseconds). mode=CUSTOM일 때 필수." },
    "endTime":   { "type": "integer", "format": "int64", "description": "종료 시각 (epoch milliseconds). mode=CUSTOM일 때 필수." }
  }
}
```

**Root**: 한국어 phrase → mode 매핑 사전 (`x-time-filter-modes`):

```json
"x-time-filter-modes": {
  "_description": "TimeFilter.mode enum reference. 모드가 CUSTOM이 아니면 startTime/endTime은 서버가 모드 규칙대로 채움.",
  "epoch_unit": "milliseconds (int64)",
  "modes": {
    "LIVE":   { "ko": "실시간",     "rule": "endTime=now; 짧은 슬라이딩 윈도우" },
    "TODAY":  { "ko": "오늘",       "rule": "오늘 00:00 ~ now" },
    "WEEK":   { "ko": "최근 1주",   "rule": "now-7d ~ now" },
    "CUSTOM": { "ko": "사용자 지정", "rule": "startTime + endTime (epoch-millis) 명시 필수" }
  },
  "ko_phrase_mapping_examples": {
    "지금": "NOW", "실시간": "LIVE", "최근 15분": "MIN_15",
    "오늘": "TODAY", "어제부터": "CUSTOM (startTime=어제 00:00, endTime=now)",
    "지난 3일간": "DAY_3"
  }
}
```

**Operation 별 좁히기** (`x-time-filter`):

```json
"x-time-filter": {
  "accepted_modes": ["LIVE","TODAY","WEEK","MONTH","CUSTOM"],
  "requires_custom_range": false,
  "default_mode": "TODAY"
}
```

| 키                          | 필수 | 형식         | 설명                          |
| -------------------------- | -- | ---------- | --------------------------- |
| `accepted_modes`           | ✅  | string[]   | 이 endpoint 가 받는 mode 목록      |
| `requires_custom_range`    | ✅  | boolean    | true 면 `mode=CUSTOM` 강제      |
| `default_mode`             | ✅  | string     | 사용자가 mode 미지정 시 기본값          |

### 6.4 `x-grids` — Grid 컬럼 카탈로그

paged 목록 응답의 컬럼 사전. operation 에는 `x-grid: "<GridName>"` 만 적고 컬럼 메타는 root 에 모은다.

**Source / 추출 룰**:
- 컬럼 정의: `/swagger_model/lucida-ui/shared/constants/<domain>/gridColumnDefs.ts` (TypeScript, 함수형 export)
  - 정규식 파싱 ❌ — TS AST (`ts-morph` 류) 또는 LLM 직접 reading
  - 함수 인자에 따라 컬럼이 동적으로 바뀌는 경우 (예: `isFilterServer`) 가장 일반적인 호출 컨텍스트 기준으로 추출
  - `cellRenderer` 만 있고 `field` 없는 컬럼 (UI 전용) 은 `x-grids` 에서 제외
  - `hide:true` 컬럼은 포함 (데이터에는 존재)
- 컬럼 한글 라벨 (`headerName`): 위 파일의 `tt('cmm.system_name')` 같은 i18n key 호출 → `/swagger_model/lucida-ui/shared/i18n/json/messages_google_sheet.json` 에서 `fullResourceKey == 'cmm.system_name'` 의 `ko_kr` 값 lookup
  - lookup 실패 시 i18n key 그대로 노출 (예: `headerName: "cmm.system_name"`)
- `filterType` 매핑: TS 의 `GridFilter[Text|Number|ManageStatus|...]` → OpenAPI `Text` / `Number` / `DateRange` / `SelectMulti` / `ManageStatus` 그대로

```json
"x-grids": {
  "_description": "Grid 컬럼 → 한글 라벨 카탈로그.",
  "HostGrid": {
    "applies_to_endpoints": ["/api/sms/hosts-filter"],
    "columns": [
      { "field": "hostName",            "headerName": "시스템 이름",   "filterType": "Text",         "sortable": true },
      { "field": "representativeIp",    "headerName": "IP",           "filterType": "Text",         "sortable": true },
      { "field": "osType",              "headerName": "OS 종류",      "filterType": "ManageStatus", "sortable": false, "x-enum-ref": "OsTypeEnum" },
      { "field": "osVersion",           "headerName": "OS 버전",      "filterType": "Text",         "sortable": true },
      { "field": "cpuUtil",             "headerName": "CPU 사용률",   "filterType": "Number",       "sortable": true,  "x-unit": "%" },
      { "field": "memUtil",             "headerName": "메모리 사용률", "filterType": "Number",       "sortable": true,  "x-unit": "%" },
      { "field": "availabilityStatus",  "headerName": "가용성",       "filterType": "ManageStatus", "sortable": false, "x-enum-ref": "AvailabilityStatusEnum" },
      { "field": "registDateTime",      "headerName": "등록일",       "filterType": "DateRange",    "sortable": true }
    ]
  }
}
```

각 컬럼 필드:

| 필드            | 필수    | 형식                                                                         | 설명                                                          |
| ------------- | ----- | -------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `field`       | ✅     | string                                                                     | 응답 객체 property 이름. request `gridFilters[].field` 와 동일.     |
| `headerName`  | ✅     | string (한국어 직접)                                                            | 컬럼 한글 라벨. UI / LLM 응답 모두에서 사용.                              |
| `filterType`  | ✅     | enum: `Text` / `Number` / `DateRange` / `SelectMulti` / `ManageStatus`     | 컬럼 타입. 허용 operator 는 §6.7 `operators_by_filter_type` 참조.   |
| `sortable`    | ✅     | boolean                                                                    | 정렬 가능 여부. `sortFieldSets[].fieldName` 에 사용 가능한지.            |
| `x-enum-ref`  | enum 일 때 | string (component schema 이름)                                               | 값이 enum 인 경우 component schema 참조. 예: `OsTypeEnum`           |
| `x-unit`      | 단위가 있을 때 | string (한국어/기호 직접)                                                        | 표시 단위. 예: `"%"`, `"core"`                                   |

### 6.5 `x-measurement-catalog` — 성능 지표 카탈로그

```json
"x-measurement-catalog": {
  "_description": "Metric 카탈로그 — confType=server 한정.",
  "source": "/api/cm/configuration/resource-types + sms_metrics endpoint",
  "resource_types": [
    {
      "id": "server.Server",
      "confType": "server",
      "displayNameKey": "sms.server_config",
      "descriptionKey": "sms.server_config_info",
      "icon": "it-server-5-f",
      "monitoring": true,
      "singleResourceType": false
    },
    {
      "id": "server.FileSystem",
      "confType": "server",
      "displayNameKey": "cmm.individual_file_system",
      "descriptionKey": null,
      "icon": "it-storage-group-f",
      "monitoring": true,
      "singleResourceType": true
    }
  ]
}
```

각 resource type 필드:

| 필드                    | 필수 | 형식                | 설명                                              |
| --------------------- | -- | ----------------- | ----------------------------------------------- |
| `id`                  | ✅  | string            | 카탈로그 키. 예: `server.Server`, `server.FileSystem` |
| `confType`            | ✅  | string            | 상위 분류. 예: `server`                              |
| `displayNameKey`      | ✅  | string (i18n key) | UI 라벨 사전 키                                       |
| `descriptionKey`      | ✅  | string \| null    | 설명 사전 키                                          |
| `icon`                | ✅  | string            | 아이콘 식별자                                          |
| `monitoring`          | ✅  | boolean           | 모니터링 대상 여부                                       |
| `singleResourceType`  | ✅  | boolean           | 단일 리소스 타입인지                                      |

### 6.6 `x-error-codes` — 에러 코드 사전

```json
"x-error-codes": {
  "_description": "Polestar 표준 에러 코드 → 한글 메시지. 모든 4xx/5xx 응답의 errorCode는 이 카탈로그의 키.",
  "source": "/swagger_model/lucida-domain-<name>/src/main/java/.../exception/<Domain>ErrorCode.java (Java enum, 한글은 라인주석)",
  "codes": {
    "POLESTAR_00000": "정의되지 않은 예외가 발생하였습니다.",
    "POLESTAR_00006": "제한된 명령어 입니다. ({0})",
    "POLESTAR_00305": "지원하지 않는 파라미터 — arguments 키 확인",
    "POLESTAR_00404": "리소스 없음",
    "POLESTAR_00500": "APM에서 알수 없는 예외가 발생하였습니다."
  }
}
```

**Source / 추출 룰**:
- 진짜 i18n 사전 (`lucida-message/.../exception_ko.properties`) 은 `/swagger_model/` 트리 밖 — 접근 불가
- 대안: 도메인별 `<Domain>ErrorCode.java` enum 파일의 라인주석 파싱
- 정규식: `^\s*([A-Z_]+)\("([0-9]+)"\),?\s*//\s*(.+)$` → `{POLESTAR_<숫자>: "<주석>"}`
- prefix `POLESTAR_` 는 `ErrorCode` interface (lucida-common, reach 밖) 에 정의 — 가이드에서는 고정 prefix 가정
- **도메인마다 패턴 다름**:
  - SMS/NMS — 모든 멤버에 한글 주석 ✅ 자동 추출
  - APM/WPM/LMS/DPM/TCM/KCM/automation/aiops/forecast — 주석 없거나 부분만 → **source 있는 것만 채우고 나머지는 코드 키만 (한글 메시지 없이)**
  - ITG — `class` + `static final int` + `HashMap<Integer,String>` 구조 → 별도 파싱
- 한글 메시지 없는 코드는 `codes` 에서 빈 문자열 또는 키 자체 (`"POLESTAR_00500": "POLESTAR_00500"`) 로 두되 `x-error-codes-applicable` 에는 포함

| 키              | 필수 | 형식                                  | 설명                                       |
| -------------- | -- | ----------------------------------- | ---------------------------------------- |
| `_description` | ✅  | string                              | 카탈로그 설명                                  |
| `source`       | ✅  | string                              | 사전 출처                                    |
| `codes`        | ✅  | `{ "POLESTAR_xxxxx": "한글 메시지" }`     | 코드 → 한글. `{0}` 은 `errorMsgArgs` 치환 자리.  |

각 endpoint 는 발생 가능한 코드만 `x-error-codes-applicable` 배열로 좁혀 명시한다 (§8.5).

### 6.7 `x-i18n` — filter type / operator 한글

```json
"x-i18n": {
  "_description": "도메인 한글 사전. UI 메뉴/라벨 같은 런타임 설정은 제외; OpenAPI 계약에 필요한 것만.",
  "filter_types": {
    "DateRange":    "날짜 범위 필터",
    "ManageStatus": "상태 필터 (아이콘)",
    "Number":       "숫자 필터",
    "SelectMulti":  "다중 선택 필터",
    "Text":         "텍스트 필터"
  },
  "operators": {
    "contains":    "포함",
    "endsWith":    "끝",
    "equals":      "같음",
    "greaterThan": "초과",
    "inRange":     "범위",
    "lessThan":    "미만",
    "notContains": "포함 안함",
    "startsWith":  "시작"
  },
  "operators_by_filter_type": {
    "Text":         ["contains","equals","startsWith","endsWith","notContains"],
    "Number":       ["equals","greaterThan","lessThan","inRange"],
    "DateRange":    ["inRange"],
    "SelectMulti":  ["equals","contains"],
    "ManageStatus": ["equals"]
  }
}
```

`gridFilters[].operator` 는 컬럼 `filterType` 에 따라 `operators_by_filter_type[<filterType>]` 안의 값만 사용.

### 6.8 Enum 한글 라벨 — 두 가지 표기

(a) **Component schema 의 enum** → `x-enum-descriptions` (Redocly de facto, 멤버→한글 직접):

```json
"OsTypeEnum": {
  "type": "string",
  "description": "OsTypeEnum — 멤버별 한글 라벨은 x-enum-descriptions 참조.",
  "enum": ["AIX", "HPUX", "LINUX", "SUNOS", "WINDOWS"],
  "x-enum-descriptions": {
    "AIX": "AIX", "HPUX": "HP-UX", "LINUX": "리눅스",
    "SUNOS": "솔라리스", "WINDOWS": "윈도우"
  }
}
```

**Source / Reality 룰** (2026-04 조사 결과 반영):
- enum 멤버의 한글 라벨이 lucida 트리에서 1:1 추출 가능한 경우는 **AggregationType (AVG/MIN/MAX/SUM → 평균/최소/최대/합계) 정도가 사실상 유일**. lucida 시스템이 한국어 사용자에게도 `cmm.up` ko_kr = "UP" / `cmm.debug` ko_kr = "DEBUG" 식 영문 노출을 정책으로 채택하고 있음 (반면 ja_jp 는 한글/일본어 번역 보유)
- **추출 우선순위**:
  1. Java enum 자체에 displayName 한글 박힌 경우 (예: WPM `AlarmSeverity` LEVEL1→해제, AIOps `LogSeverity` TRACE→추적, AIOps forecast `ResourceType` SERVER→서버, SMS `CustomScriptCategory` NONE→미지정)
  2. Java enum javadoc / 라인주석 한글 (예: NMS `AvailabilityStatus`)
  3. `messages_google_sheet.json` lookup (UI key → ko_kr 가 한글인 경우만 — server/network/oracle 등)
  4. ITG `itg_sys_cmn_code.json` (제한적: `instOsType` 등 일부 그룹)
- 1~4 모두 실패 → **영문 echo** (`"AIX": "AIX"`). hand-curate / LLM 추정 ❌
- 위 예시의 `OsTypeEnum.x-enum-descriptions` 는 가이드 작성 시점의 이상치 — 실제로 source 가 없는 멤버는 영문 echo 됨

(b) **Inline enum 필드** (request body / response body 의 enum property) → `x-i18n-key-prefix` (사전 키만):

```json
"operator": {
  "type": "string",
  "enum": ["contains","equals","startsWith","endsWith","notContains","greaterThan","lessThan","inRange"],
  "x-i18n-key-prefix": "operator",
  "description": "필터 연산자. 한국어 매핑은 /swagger_model/lucida-ui/shared/i18n/json/messages_google_sheet.json (fullResourceKey 매칭, ko_kr 추출) 의 operator.* 키."
}
// 라벨 키: operator.contains → "포함", operator.equals → "같음", ...

"sortDirection": {
  "type": "string",
  "enum": ["ASC","DESC"],
  "x-i18n-key-prefix": "enum.SortDirectionEnum",
  "description": "오름차순/내림차순"
}
```

(c) **응답 필드의 단위** → `x-unit-key` (사전 키만):

```json
"cpuUtil": {
  "type": "number", "format": "double",
  "description": "CPU 사용률 (%)",
  "example": 1.725,
  "x-unit-key": "unit.PERCENTAGE"
}
```

| 위치                                  | 표기 방법                                                 | 라벨 위치                |
| ----------------------------------- | ----------------------------------------------------- | -------------------- |
| `components.schemas.<Enum>`         | `x-enum-descriptions: { 멤버: "한글 라벨" }`                  | spec 안에 직접          |
| inline property (request/response) | `x-i18n-key-prefix: "<prefix>"`                       | `/swagger_model/lucida-ui/shared/i18n/json/messages_google_sheet.json (fullResourceKey 매칭, ko_kr 추출)` 외부 사전 |
| 응답 필드 단위                          | `x-unit-key: "unit.<KEY>"`                            | `/swagger_model/lucida-ui/shared/i18n/json/messages_google_sheet.json (fullResourceKey 매칭, ko_kr 추출)` 외부 사전 |

i18n 키 명명 규칙: `<category>.<scope>.<id>` (점 구분). category = `enum / field / metric / unit / error / filter_type / operator`.

---

## 7. G4. Examples — 자연어 ↔ 호출 페어

LLM 은 examples 에서 패턴을 빠르게 학습한다. `summary` 는 사용자 발화 매칭의 1차 시드 (시멘틱 서치 임베딩 인덱스 대상).

### 7.1 모든 endpoint 에 3 ~ 5 개 강제

위치는 endpoint 종류에 따라 셋 중 하나를 사용한다. **모두 OpenAPI 3.1 표준 슬롯을 우선** 쓰고, 표준이 없는 종류 3 만 사내 확장.

| 종류 | endpoint 모양                          | 위치                                                       | 표준/확장          |
| -- | ------------------------------------ | -------------------------------------------------------- | -------------- |
| 1  | request body 있음                       | `requestBody.content."application/json".examples`        | OpenAPI 표준     |
| 2  | request body 없음 + path 또는 query param | `parameters[].examples` (대표 parameter 1 개에 모음)             | OpenAPI 표준     |
| 3  | 인자 없음 (트리거 endpoint)                  | `x-llm-examples` (operation 레벨)                          | 사내 확장          |

### 7.2 모든 종류 공통 규칙

| 항목       | 필수 | 규칙                                                                                                                       |
| -------- | -- | ------------------------------------------------------------------------------------------------------------------------ |
| 개수       | ✅  | endpoint 당 **3 ~ 5 개 강제**. 예외 없음.                                                                                       |
| `key`    | ✅  | 영문 snake_case. 시나리오 함축. 예: `cpu_over_80`, `linux_only`. 메타라벨 (`canonical`, `default`) 금지.                               |
| `summary`| ✅  | 한국어 자연어 질의 (사용자 발화). 시멘틱 서치 벡터 인덱싱 대상. **출처 표시·메타라벨 ("기본 호출 예시", "cards_v2 evidence") 금지. enum 코드값 직접 노출 금지.**       |
| `value`  | ✅ (종류 1, 2) | `summary` 에 대응하는 호출 값. 종류 1 = request body 풀 페이로드 (모든 `required` 필드). 종류 2 = parameter 값.                  |
| 표현 다양성   | ✅  | 같은 endpoint 의 examples 3 ~ 5 개가 서로 다른 의도 / 필터 / 값을 표현. 도메인 동의어 (서버/호스트/장비), 표현 변형 (긍정/조건/카운트/구어체) 섞기. 동일 단어 반복 금지. **enum 한글 라벨 부재 보강**: enum value 의 한국어 표현 (예: `LINUX` → "리눅스", `WINDOWS` → "윈도우 호스트", `FATAL` → "치명 알람", `DEBUG` → "디버그 로그") 을 examples summary 에 풍부하게 박아 LLM 이 자연어 ↔ enum value 매칭을 학습할 수 있게 한다 (§6.8 Source / Reality 룰 보완). |
| CI 검증    | ✅  | 종류 1·2: 각 `value` 를 stage 호출 → 200 응답. 종류 3: NL 매칭 룰 통과만 검증.                                                            |

### 7.3 종류 1 — request body 있는 endpoint

표준 위치: `requestBody.content."application/json".examples`. `key + summary + value` 3 필드. `value` 는 strict mode 풀 페이로드.

`/api/sms/hosts-filter` 5 개 예시:

```json
"examples": {
  "cpu_over_80":   { "summary": "CPU 80% 넘는 서버 보여줘",  "value": { "pageNumber": 0, "pagePerSize": 25, "tagFilters": ["confType = server"], "gridFilters": [{"field":"cpuUtil","operator":"greaterThan","values":[80]}], "sortFieldSets": [], "arguments": {} } },
  "linux_only":    { "summary": "리눅스 장비 목록",           "value": { "pageNumber": 0, "pagePerSize": 25, "tagFilters": ["confType = server AND os = LINUX"], "gridFilters": [], "sortFieldSets": [], "arguments": {} } },
  "ad_prefix":     { "summary": "AD 로 시작하는 호스트",      "value": { "pageNumber": 0, "pagePerSize": 25, "tagFilters": ["confType = server"], "gridFilters": [{"field":"hostName","operator":"startsWith","values":["AD"]}], "sortFieldSets": [], "arguments": {} } },
  "mem_heavy":     { "summary": "메모리 많이 쓰는 서버 5개",  "value": { "pageNumber": 0, "pagePerSize": 5,  "tagFilters": ["confType = server"], "gridFilters": [], "sortFieldSets": [{"fieldName":"memUtil","index":0,"sortDirection":"DESC"}], "arguments": {} } },
  "count_windows": { "summary": "윈도우 호스트 몇 대야?",     "value": { "pageNumber": 0, "pagePerSize": 1,  "tagFilters": ["confType = server AND os = WINDOWS"], "gridFilters": [], "sortFieldSets": [], "arguments": {} } }
}
```

### 7.4 종류 2 — body 없음 + path/query param 있는 endpoint

표준 위치: `parameters[].examples`. examples 는 **대표 parameter 1 개** (보통 path 의 chain ID parameter) 에 모은다. `value` 는 **그 parameter 값**.

`value` 작성 규칙:
- `x-semantic-type` 있는 parameter → root `x-semantic-types[<type>].example` 값 사용 (실제 ID 모양의 illustrative 예시)
- 그 외 → 그 parameter schema 의 enum 값 / 최소 길이 만족하는 placeholder

`/api/sms/configuration/{resourceId}/basic-info` 예시:

```json
"parameters": [{
  "name": "resourceId",
  "in": "path",
  "required": true,
  "schema": { "type": "string" },
  "description": "서버 리소스 식별자. /api/sms/hosts-filter 응답의 resourceId 사용.",
  "x-source-endpoint": "/api/sms/hosts-filter",
  "x-source-field":    "$.data.content[*].resourceId",
  "x-semantic-type":   "server_resource_id",
  "examples": {
    "ad_server":   { "summary": "ad-01 서버 정보 보여줘",     "value": "MA_AD_SERVER_01" },
    "linux_box":   { "summary": "리눅스 서버 기본 사양 알려줘", "value": "MA_LINUX_TEST_SERVER_01" },
    "previous":    { "summary": "그 호스트 OS 뭐야",          "value": "MA_LINUX_TEST_SERVER_01" }
  }
}]
```

`value` 의 `MA_AD_SERVER_01` 등은 illustrative — 실제 DB 의 ID 가 아니라 "이런 모양의 ID 가 들어간다" 는 형태 예시. 실제 호출 시 LLM 은 user query 에서 entity (hostName="ad-01") 를 뽑아 `parameters[].x-source-endpoint` 의 chain 호출로 진짜 ID 를 resolve.

### 7.5 종류 3 — 인자 자체 없는 트리거 endpoint

사내 확장: `x-llm-examples` (operation 레벨). `value` 슬롯 없음 — `summary` 만.

```json
"/api/sms/operation/start-all-agents": {
  "post": {
    "operationId": "startAllAgents",
    "summary": "모든 에이전트 시작",
    "x-side-effect": "write",
    "x-llm-examples": [
      { "summary": "에이전트 전부 시작" },
      { "summary": "agent 일괄 기동" },
      { "summary": "모든 호스트 에이전트 시작해줘" }
    ]
  }
}
```

이 종류는 매우 드물다 (sms 에서는 `start-all-agents`, `os-types`, `gpu-cards` 정도 — 단순 lookup 또는 트리거).

### 7.6 응답 200 — `example` + `data` shape **모두 필수**

모든 endpoint 의 `responses["200"]` 은 다음 두 가지를 반드시 갖는다:

| 항목                  | 필수 | 위치                                                                                  |
| ------------------- | -- | ----------------------------------------------------------------------------------- |
| `example` (1 개)      | ✅  | `responses["200"].content."application/json".example` — 대표 응답 1 개                  |
| `data` shape (인라인 정의) | ✅  | `responses["200"].content."application/json".schema.allOf[1].properties.data`       |

**`data` shape 작성 규칙:**

- 응답 페이로드를 반환하는 endpoint (read / list / detail / count 등): `data` 의 `type` / `properties` / `required` / `additionalProperties: false` 모두 정의. **`{type: "null"}` placeholder 금지.**
- 응답 페이로드가 없는 action endpoint (delete / save / update 등): `data: { type: "null" }` 만 명시 (의도적 null 표시).
  - 동시에 operation 메타에 `x-empty-data: true` 플래그를 박아 작성 의도를 표현.

**예시 — paged 응답 (list-filter):**

```json
"responses": {
  "200": {
    "description": "호스트 목록 (paged)",
    "content": {
      "application/json": {
        "schema": {
          "allOf": [
            { "$ref": "#/components/schemas/ApiResponseDataObject" },
            {
              "type": "object",
              "properties": {
                "data": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["content","totalElements","totalPages","number","size","numberOfElements","first","last","empty","pageable","sort"],
                  "properties": {
                    "content":       { "type": "array", "items": { "$ref": "#/components/schemas/HostDto" } },
                    "totalElements": { "type": "integer", "format": "int64" },
                    "totalPages":    { "type": "integer", "format": "int32" },
                    "number":        { "type": "integer", "format": "int32" },
                    "size":          { "type": "integer", "format": "int32" }
                  }
                }
              }
            }
          ]
        },
        "example": {
          "success": true, "errorCode": null,
          "data": { "content": [{ "...": "..." }], "totalElements": 8, "...": "..." }
        }
      }
    }
  }
}
```

**예시 — action 응답 (의도적 null):**

```json
"x-empty-data": true,
"responses": {
  "200": {
    "description": "삭제 성공 — data 없음.",
    "content": {
      "application/json": {
        "schema": {
          "allOf": [
            { "$ref": "#/components/schemas/ApiResponseDataObject" },
            { "type": "object", "properties": { "data": { "type": "null" } } }
          ]
        },
        "example": { "success": true, "errorCode": null, "data": null }
      }
    }
  }
}
```

---

## 8. G5. 실행 메타

OpenAPI ↔ 실제 API 일치성. HTTP 호출 단계에서 실패하지 않게 한다.

### 8.1 `servers` (절대 URL)

```json
"servers": [
  { "url": "https://polestar.example.com", "description": "Polestar10 production base URL (replace per deployment)" },
  { "url": "/",                            "description": "Same-origin (when Polestar UI mounts API on its own host)" }
]
```

미해결 템플릿 (`{{service-root}}` 등) 금지.

### 8.2 인증 — `cookieAuth`

```json
"components": {
  "securitySchemes": {
    "cookieAuth": {
      "type": "apiKey",
      "in":   "cookie",
      "name": "SESSION_ID",
      "description": "Polestar 표준 세션 쿠키. 로그인 endpoint(/api/account/login)가 발급. 만료 시 401 + POLESTAR_00401."
    }
  }
},
"security": [{ "cookieAuth": [] }]
```

| 필드                                | 필수 | 값                                                          |
| --------------------------------- | -- | ---------------------------------------------------------- |
| `securitySchemes.cookieAuth.type` | ✅  | `"apiKey"`                                                  |
| `securitySchemes.cookieAuth.in`   | ✅  | `"cookie"`                                                  |
| `securitySchemes.cookieAuth.name` | ✅  | `"SESSION_ID"`                                              |
| 글로벌 `security`                    | ✅  | `[{ "cookieAuth": [] }]`                                    |

### 8.3 응답 envelope — `ApiResponseDataObject` + `allOf`

200 응답 schema 는 공용 envelope 을 `allOf` 로 확장하고, `data` 의 모양만 endpoint 별 inline.

```json
"schema": {
  "allOf": [
    { "$ref": "#/components/schemas/ApiResponseDataObject" },
    {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "data": {
          "type": "object",
          "additionalProperties": false,
          "required": ["content","totalElements","totalPages","number","size","numberOfElements","first","last","empty","pageable","sort"],
          "properties": {
            "content":       { "type": "array", "items": { "$ref": "#/components/schemas/HostDto" } },
            "totalElements": { "type": "integer", "format": "int64" },
            "totalPages":    { "type": "integer", "format": "int32" },
            "number":        { "type": "integer", "format": "int32" },
            "size":          { "type": "integer", "format": "int32" }
          }
        }
      }
    }
  ]
}
```

> ⚠️ `allOf` 의 두 번째(파생) 분기에도 `additionalProperties: false` 강제 — §11 #6 strict mode 검증과 일관 (allOf 분기 자체도 object schema 로 평가됨).

`ApiResponseDataObject` (component) 표준 정의 — strict mode 일관 (모든 property 가 `required` 에 포함, optional 영역은 `type: [..., "null"]`):

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["success", "errorCode", "errorMsgArgs", "errorData", "data"],
  "properties": {
    "success":      { "type": "boolean", "description": "성공 여부" },
    "errorCode":    { "type": ["string","null"], "description": "200 이지만 부분 실패 시 채워질 수 있음. 정상은 null." },
    "errorMsgArgs": { "type": ["array","null"], "items": { "type": "string" }, "description": "에러 메시지 i18n 인자. 정상은 null." },
    "errorData":    { "type": ["object","null"], "additionalProperties": true, "description": "추가 컨텍스트. 정상은 null." },
    "data":         { "description": "실제 페이로드. derived schema 에서 구체 모양 지정 (allOf). success=false 면 null." }
  }
}
```

### 8.4 4xx / 5xx 응답 — 모든 endpoint 가 정의

| 코드  | 필수 (path param 있을 때 포함) | description 예                                                                                  |
| --- | ------------------------- | --------------------------------------------------------------------------------------------- |
| 400 | ✅                         | "잘못된 요청. POLESTAR_00006 (잘못된 파라미터): gridFilters의 field/operator 확인. POLESTAR_00305 (지원하지 않는 파라미터): arguments 키 확인" |
| 401 | ✅                         | "인증 실패. SESSION 쿠키 없음/만료."                                                                   |
| 403 | ✅                         | "권한 없음. 사용자 role 부족."                                                                          |
| 404 | path param 있을 때만 ✅       | "리소스 없음. 잘못된 resourceId 등."                                                                   |
| 500 | ✅                         | "서버 내부 오류. POLESTAR_00300: SMS 공통 에러."                                                        |

모두 `application/json.schema = $ref: '#/components/schemas/ApiResponseError'` 사용.

`ApiResponseError` (component) — strict mode 일관 (모든 property 가 `required` 에 포함, optional 영역은 `type: [..., "null"]`):

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["success", "errorCode", "message", "errorMsgArgs", "errorData", "data"],
  "properties": {
    "success":      { "type": "boolean", "enum": [false] },
    "errorCode":    { "type": "string", "description": "에러 코드. 한글 메시지 매핑은 root x-error-codes.codes.<code>." },
    "message":      { "type": ["string","null"], "description": "최종 한글 메시지 (errorMsgArgs 치환 후)." },
    "errorMsgArgs": { "type": ["array","null"], "items": { "type": "string" } },
    "errorData":    { "type": ["object","null"], "additionalProperties": true },
    "data":         { "type": "null" }
  }
}
```

### 8.5 Operation 메타 — `x-envelope`, `x-error-codes-applicable`

```json
"x-envelope": "paged",
"x-error-codes-applicable": ["POLESTAR_00006", "POLESTAR_00300", "POLESTAR_00305"]
```

| 키                            | 필수 | 형식                                              | 설명                                                                                      |
| ---------------------------- | -- | ----------------------------------------------- | --------------------------------------------------------------------------------------- |
| `x-envelope`                 | ✅  | enum: `paged` / `object` / `array` / `binary`   | 응답 모양 분류                                                                                |
| `x-error-codes-applicable`   | ✅  | string array                                    | 발생 가능한 POLESTAR 코드. root `x-error-codes.codes` 키만 허용.                                  |

---

---

## 10. 완성형 예시 — `/api/sms/hosts-filter`

> ⚠️ **이 예시는 List-filter 패턴의 구조(structural) reference 이지 데이터 정답이 아니다.** 가이드 작성 시점의 가공된 sample 이며 **실제 lucida-domain-sms 코드/grid 와 일치하지 않는다** (예: 컬럼명 `hostName` ↔ 실제 `hostname`, `representativeIp` ↔ 실제 `ip`, `osType` ↔ 실제 `os`, `registDateTime` ↔ 실제 코드에 없음). 자동화 스킬은 **이 예시 대신 실제 컨트롤러 / DTO / `gridColumnDefs.ts` 기준** 으로 추출해야 함. 본 §10 은 4-pattern skeleton, root vocab 사용처, examples 위치 같은 **형식 골격** 만 참고하라.

이하 sample 은 새 list-filter endpoint 를 작성할 때 **모양만 복사** 해 시작한다 (데이터 부분은 실제 코드로 교체).

```json
"/api/sms/hosts-filter": {
  "post": {
    "operationId": "getHostListByGridFilter",
    "summary":     "호스트(서버) 목록을 페이지/필터/정렬 조건으로 조회",
    "description": "등록된 서버(호스트, 장비) 의 목록 조회. CPU/메모리/OS 등 조건으로\n필터·페이지네이션·정렬 가능.\n\n반환 필드:\n시스템 이름(hostname), IP, CPU 사용률(cpuUtil), 메모리 사용률(memUtil),\nOS, 가용성(availabilityStatus), 관리상태(managementStatus)",
    "tags":          ["SMS - Host"],
    "x-side-effect": "read",
    "x-llm-intent":  ["list","search","filter"],
    "x-envelope":    "paged",
    "x-grid":        "HostGrid",
    "x-default-filter": { "tagFilters": ["confType = server"] },
    "x-tag-vocabulary": {
      "confType":      { "enum": ["server"] },
      "os":            { "enum_ref": "OsTypeEnum" },
      "resourceGroup": { "source_endpoint": "/api/account/resource-groups/list" }
    },
    "x-time-filter": {
      "accepted_modes": ["LIVE","MIN_15","MIN_30","HOUR","HOUR_3","NOW","TODAY",
                         "DAY_3","WEEK","MONTH","MONTH_3","MONTH_6","YEAR","CUSTOM"],
      "requires_custom_range": false,
      "default_mode": "TODAY"
    },
    "x-error-codes-applicable": ["POLESTAR_00006","POLESTAR_00300","POLESTAR_00305"],
    "security": [{ "cookieAuth": [] }],

    "requestBody": {
      "required": true,
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "additionalProperties": false,
            "required": ["pageNumber","pagePerSize","tagFilters","gridFilters","sortFieldSets","arguments"],
            "properties": {
              "pageNumber":  { "type": "integer", "format": "int32", "description": "0-기반 페이지 번호", "default": 0,  "minimum": 0,                  "example": 0 },
              "pagePerSize": { "type": "integer", "format": "int32", "description": "페이지당 행 수",     "default": 25, "minimum": 1, "maximum": 1000, "example": 25 },
              "tagFilters":  {
                "type": "array",
                "description": "리소스 범위 한정 절. SMS는 'confType = server' 자동 박힘. 추가 clause(예: 'os = LINUX', 'tag.env IN [prod]') 가능. 문법: root x-tagfilter-grammar.",
                "items": { "type": "string" },
                "minItems": 1,
                "default": ["confType = server"],
                "example": ["confType = server AND os = LINUX"]
              },
              "gridFilters": {
                "type": "array",
                "description": "grid 필터. x-grid=HostGrid의 컬럼만 사용 가능.",
                "default": [],
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["field","operator","values"],
                  "properties": {
                    "field":    {
                      "type": "string",
                      "enum": ["hostName","representativeIp","osType","osVersion","cpuUtil","memUtil","availabilityStatus","registDateTime"],
                      "description": "필터 대상 컬럼 (HostGrid sortable/filterable 기준)"
                    },
                    "operator": {
                      "type": "string",
                      "enum": ["equals","contains","startsWith","endsWith","notContains","greaterThan","lessThan","inRange"],
                      "x-i18n-key-prefix": "operator",
                      "description": "연산자. 컬럼 filterType에 따라 허용 어휘가 좁아짐 (root x-i18n.operators_by_filter_type)."
                    },
                    "values":   { "type": "array", "minItems": 1, "items": {}, "description": "비교값. 단일 값이면 [v], 범위면 [low, high]." }
                  }
                },
                "example": [{ "field": "cpuUtil", "operator": "greaterThan", "values": [80] }]
              },
              "sortFieldSets": {
                "type": "array",
                "description": "정렬 조건. x-grid=HostGrid 의 sortable=true 컬럼만 사용 가능.",
                "default": [],
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["fieldName","sortDirection"],
                  "properties": {
                    "fieldName":     {
                      "type": "string",
                      "enum": ["hostName","representativeIp","osVersion","cpuUtil","memUtil","registDateTime"],
                      "description": "정렬 컬럼 (HostGrid sortable=true)"
                    },
                    "index":         { "type": "integer", "format": "int32", "default": 0, "description": "다중 정렬 시 적용 순서 (0이 최상위)" },
                    "sortDirection": { "type": "string", "enum": ["ASC","DESC"], "x-i18n-key-prefix": "enum.SortDirectionEnum", "description": "오름차순/내림차순" }
                  }
                },
                "example": [{ "fieldName": "memUtil", "index": 0, "sortDirection": "DESC" }]
              },
              "timeFilter":  { "$ref": "#/components/schemas/TimeFilter", "description": "조회 시간 범위. accepted modes는 operation x-time-filter 참조." },
              "arguments":   {
                "type": "object",
                "additionalProperties": false,
                "description": "endpoint별 추가 인자.",
                "default": {},
                "properties": {
                  "permission": { "type": "integer", "enum": [1, 3], "default": 1, "description": "최소 권한 필터: 1=읽기, 3=실행", "example": 1 }
                },
                "example": {}
              }
            }
          },
          "examples": {
            "cpu_over_80":   { "summary": "CPU 80% 넘는 서버 보여줘",  "value": { "pageNumber": 0, "pagePerSize": 25, "tagFilters": ["confType = server"], "gridFilters": [{"field":"cpuUtil","operator":"greaterThan","values":[80]}], "sortFieldSets": [], "arguments": {} } },
            "linux_only":    { "summary": "리눅스 장비 목록",           "value": { "pageNumber": 0, "pagePerSize": 25, "tagFilters": ["confType = server AND os = LINUX"], "gridFilters": [], "sortFieldSets": [], "arguments": {} } },
            "ad_prefix":     { "summary": "AD 로 시작하는 호스트",      "value": { "pageNumber": 0, "pagePerSize": 25, "tagFilters": ["confType = server"], "gridFilters": [{"field":"hostName","operator":"startsWith","values":["AD"]}], "sortFieldSets": [], "arguments": {} } },
            "mem_heavy":     { "summary": "메모리 많이 쓰는 서버 5개",  "value": { "pageNumber": 0, "pagePerSize": 5,  "tagFilters": ["confType = server"], "gridFilters": [], "sortFieldSets": [{"fieldName":"memUtil","index":0,"sortDirection":"DESC"}], "arguments": {} } },
            "count_windows": { "summary": "윈도우 호스트 몇 대야?",     "value": { "pageNumber": 0, "pagePerSize": 1,  "tagFilters": ["confType = server AND os = WINDOWS"], "gridFilters": [], "sortFieldSets": [], "arguments": {} } }
          }
        }
      }
    },

    "responses": {
      "200": {
        "description": "호스트 목록 (paged)",
        "content": {
          "application/json": {
            "schema": { "allOf": [
              { "$ref": "#/components/schemas/ApiResponseDataObject" },
              { "type": "object", "properties": { "data": { "type": "object", "/* …content/totalElements/… */": "..." } } }
            ] },
            "example": {
              "success":   true,
              "errorCode": null,
              "data": {
                "content": [{
                  "resourceId": "MA_ADServer_20250108202624",
                  "hostname":   "ADServer", "ip": "192.168.200.197",
                  "os":         "WINDOWS",
                  "cpuUtil":    1.725, "memUtil": 43.116,
                  "availabilityStatus": "UP", "managementStatus": "MANAGED"
                }],
                "totalElements": 8, "totalPages": 4, "number": 0, "size": 25,
                "numberOfElements": 1, "first": true, "last": false, "empty": false
              }
            }
          }
        }
      },
      "400": { "description": "잘못된 요청.\n- POLESTAR_00006 (잘못된 파라미터): gridFilters의 field/operator 확인\n- POLESTAR_00305 (지원하지 않는 파라미터): arguments의 키가 정의된 것만 허용", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } },
      "401": { "description": "인증 실패. SESSION 쿠키 없음/만료.",                                                                                       "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } },
      "403": { "description": "권한 없음.",                                                                                                              "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } },
      "500": { "description": "서버 내부 오류. POLESTAR_00300: SMS 공통 에러.",                                                                              "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } }
    }
  }
}
```

---

---

## 11. 검증 체크리스트 (CI)

작성된 OpenAPI 는 아래 검증을 모두 통과해야 한다.

| #   | 검증                                | 도구              | 룰                                                                                                                  |
| --- | --------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------ |
| 1   | OpenAPI 사양 준수                     | Spectral        | `spectral:oas` ruleset                                                                                              |
| 2   | operationId / summary / description 강제 | Spectral        | `operation-operationId`, `operation-summary`, `operation-description`                                                |
| 3   | examples 강제                       | Spectral 커스텀    | 모든 endpoint 에 NL 질의 examples **3 ~ 5 개** 보유. 종류별 슬롯: 종류 1 (body 있음) → `requestBody.content.*.examples`, 종류 2 (body 없음 + param 있음) → `parameters[].examples`, 종류 3 (인자 없음) → operation-level `x-llm-examples`. 각 `summary` 는 한국어 자연어 질의 (메타라벨 `"기본 호출 예시"`, `"cards_v2 evidence"` 금지). example 키 이름은 시나리오 snake_case (`canonical`, `default` 같은 폴백 이름 금지). |
| 4   | 안전 가드 강제                          | Spectral 커스텀    | 모든 endpoint 에 `x-side-effect` 필드 (`read`/`write`/`delete`/`download` 중 하나)                                        |
| 5   | chain call 메타 강제                  | Spectral 커스텀    | **path 변수 + body 의 ID-shape 필드** 모두 다음 둘 중 하나에 정확히 해당: (a) `x-source-endpoint` + `x-source-field` 둘 다 보유, (b) `x-external: true`. `x-semantic-type` 은 옵션. (a)/(b) 어느 쪽도 아니면 위반. ID-shape 검출 룰: 필드명이 `*Id`/`*Ids`/`*Key`/`*Identifier` 패턴 매치 (free-form label `name`/`displayName`/`hostName` 은 면제 — `description` 에 free-form 명시). 가이드 §5.3.1 참조 |
| 5b  | x-vocab-supported 강제               | Spectral 커스텀    | 모든 도메인 root 에 `x-vocab-supported` 객체 존재. `tagfilter`/`timefilter`/`measurement`/`grid`/`semantic_types` 5개 키 boolean 값. `true` 키는 root 에 대응 vocab 정의 동시 보유 (예: `tagfilter:true` ↔ `x-tagfilter-grammar` 존재) |
| 6   | strict mode 호환                    | Spectral 커스텀    | 모든 object schema 의 `properties` 키가 `required` 배열에 모두 포함, `additionalProperties: false` 존재                          |
| 7   | 4xx / 5xx 응답 강제                   | Spectral 커스텀    | 모든 endpoint 에 400 / 401 / 403 / 500 응답 정의 (path param 있으면 404 추가)                                                  |
| 8   | enum 라벨                          | Spectral 커스텀    | component schema 의 모든 enum 에 `x-enum-descriptions` 가 **enum 값 전부 키 자체는 커버** (값은 한글 또는 영문 echo). hand-curate / LLM 추정 금지 — source 없으면 영문 echo 허용. §6.8 Source / Reality 룰 참조 |
| 9   | error code 정합성                    | 자체 스크립트         | operation 의 `x-error-codes-applicable` 모든 코드가 root `x-error-codes.codes` 키에 존재                                     |
| 10  | grid 정합성                         | 자체 스크립트         | operation `x-grid` 값이 root `x-grids` 에 존재; `gridFilters[].field` enum 이 `x-grids[].columns[].field` 부분집합            |
| 11  | semantic type 정합성                | 자체 스크립트         | `x-semantic-type` 값이 root `x-semantic-types` 키에 존재                                                                  |
| 12  | examples 호출 가능                    | 자체 스크립트         | 각 `examples[].value` 를 stage 호출 → 200 응답, 응답 구조가 `responses['200'].example` 과 일치                                    |
| 13  | 응답 200 example 강제                 | Spectral 커스텀    | 모든 endpoint 가 `responses["200"].content."application/json".example` 보유                                              |
| 14  | 응답 data shape 강제                 | Spectral 커스텀    | 모든 endpoint 의 200 응답 `data` 정의가 `{ "type": "null" }` 면 operation 메타에 `x-empty-data: true` 도 함께. 그 외에는 `data.type` / `properties` / `required` / `additionalProperties: false` 모두 인라인 정의 (placeholder `{type: null}` 금지) |
| 15  | LLM 정확도                          | eval set        | endpoint 선택 정확도 ≥ 95%, args 정확도 ≥ 90% (자연어 50 ~ 100 개 질의 기준)                                                       |

---

---

