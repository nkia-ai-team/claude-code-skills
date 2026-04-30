---
name: openapi-llm-spec
description: Lucida Spring Boot 도메인 소스(/swagger_model/lucida-domain-*)를 LLM tool용 OpenAPI 3.1 JSON으로 자동 추출. references/OPENAPI_FOR_LLM_TOOL_CONCLUSION.md §0 자동화 추출 3원칙(hand-curate ❌, enum 한글 LLM 추정 ❌, source 없으면 영문 echo) 준수. Spring/TS 소스 정적 분석 + Claude가 한국어 자연어(summary/description/examples)만 생성. 코드 push 금지(로컬 어노테이션 보강은 옵션), 산출물은 openapi/<domain>.openapi.json 단일 자가완결 JSON 파일.
triggers:
  - openapi 작성
  - openapi llm spec
  - LLM tool spec
  - openapi 만들어줘
  - openapi 생성
  - "<도메인> openapi"
argument-hint: "<domain> [endpoint-or-controller]"
scope: project
---

# OpenAPI LLM Tool Spec — Lucida Domain Generator

## 1. When to Activate

- "<도메인> openapi 만들어줘" / "openapi 작성" / "LLM tool spec" 류 요청
- `/swagger_model/lucida-domain-<name>/` 의 controller / DTO 를 LLM 호출 가능한 OpenAPI 3.1 JSON 으로 변환
- 가이드 `references/OPENAPI_FOR_LLM_TOOL_CONCLUSION.md` §0 자동화 추출 3원칙에 맞춘 spec 자동 생성·갱신 (Spring/TS 정적 분석 + 한국어 자연어 LLM 생성)

대상 도메인 (17개): `aiops`, `apm`, `automation`, `dpm`, `itg`, `kcm`, `kcm-proto`, `lms`, `nms`, `rulechain`, `sms`, `syslog`, `tcm`, `tms`, `tnms`, `trap`, `wpm`

---

## 2. Source of Truth

| 종류 | 경로 | 권한 |
| --- | --- | --- |
| 작성 가이드 (절대 기준) | `references/OPENAPI_FOR_LLM_TOOL_CONCLUSION.md` | r/w |
| 도메인 소스 코드 | `/swagger_model/lucida-domain-<name>/src/main/java/...` | **read-only** |
| i18n 사전 (UI 한글 라벨) | `/swagger_model/lucida-ui/shared/i18n/json/messages_google_sheet.json` (54791줄, 구조: `{module, resourceKey, fullResourceKey, ko_kr, en_us, ja_jp}`). 12 모듈(cmm/sms/apm/aiops/auto/db3/dpm/itg/kcm/lms/nms/tcm). **`messages_ko_kr.json` / `combine_messages_ko_kr*.json` 은 빈 placeholder 사용 ❌. lucida-meta 도 i18n source 아님** | **read-only** |
| POLESTAR error codes (한글) | `/swagger_model/lucida-domain-<name>/src/main/java/.../exception/<Domain>ErrorCode.java` Java enum 라인주석. 정규식: `^\s*([A-Z_]+)\("([0-9]+)"\),?\s*//\s*(.+)$` → `{POLESTAR_<숫자>: "<주석>"}`. SMS/NMS만 한글 주석 ✅ 자동 추출, APM/WPM/LMS/etc 는 주석 없음 → 영문 코드만. ITG는 `class + HashMap<Integer,String>` 별도 파싱. **진짜 사전 (`lucida-message/exception_ko.properties`) 은 reach 밖** | **read-only** |
| Grid 컬럼 정의 (TypeScript) | `/swagger_model/lucida-ui/shared/constants/<domain>/gridColumnDefs.ts` — TS 함수가 `{field, headerName, filter, sortable, ...}` 배열 반환. `headerName` 은 `tt('cmm.*')` 형태 i18n 키 → `messages_google_sheet.json` 의 `fullResourceKey == 'cmm.xxx'` 의 `ko_kr` lookup. 정규식 파싱 ❌ — TS AST 또는 LLM 직접 reading | **read-only** |
| Enum 한글 라벨 | **source 부재가 정상** — lucida 가 한국어 사용자에게 enum value 영문 노출 정책 (`cmm.up` ko_kr = "UP" 식). 추출 우선순위: ① Java enum displayName/javadoc 한글 ② google_sheet ko_kr (한글일 때만) ③ ITG `itg_sys_cmn_code.json` (제한적). 모두 실패 → **영문 echo** (`"AIX": "AIX"`). hand-curate / LLM 추정 ❌ | **read-only** |
| 도메인 자체 컨텍스트 | `/swagger_model/lucida-domain-<name>/.claude/` (이전 작업 흔적·도메인 특이 메모) | **read-only** |
| 산출물 (도메인당 1파일) | `openapi/<domain>.openapi.json` | r/w |
| 공용 components / 견본 | `openapi/_shared/` | r/w |
| 진척도 추적 | `openapi/INDEX.md` | r/w |

`<domain>` 은 `lucida-domain-` 접두를 제거한 이름 (예: `lucida-domain-sms` → `sms.openapi.json`).

---

## 3. HARD RULES (위반 금지)

1. **`/swagger_model` 은 push 금지** — 비즈니스 로직 (controller 본문, DTO 필드, entity, build.gradle) 수정 ❌. 분석 정확도 향상을 위한 어노테이션 보강 (`@Operation`, `@Schema`, `@ApiResponse` 등) 은 로컬에서 옵션 — 단 어떤 변경도 push 금지. 보강 없이도 추출 가능해야 하는 게 기본 (어노테이션은 보조).
2. **산출물은 OpenAPI 3.1.0 JSON 단일 파일** (도메인당 1개). YAML 금지.
3. **모든 object schema 는 strict mode** — `additionalProperties: false`, 모든 property 가 `required` 배열에 포함. 보내지 않을 수 있는 필드는 `nullable: true`. 모든 property 에 `description` + `type` + `example` (가능한 한 `enum` / `default` / `min` / `max` / `format` / `pattern`).
4. **Examples 는 한국어 자연어 질의 3 ~ 5 개 강제** — 메타라벨 (`canonical`, `default`, `cards_v2 evidence`, `기본 호출 예시`) 금지, enum 코드값 직접 노출 금지.
5. **응답 200 `data` shape 인라인 정의 필수** — `{type: "null"}` placeholder 금지. action endpoint(empty data) 는 `x-empty-data: true` 명시.
6. **체인 호출 메타 필수** — path / body 의 ID 필드에 `x-source-endpoint`, `x-source-field`, `x-semantic-type` 셋트로 박음.
7. **루트 vocabulary 1번만 정의** — `x-grids`, `x-semantic-types`, `x-tagfilter-grammar`, `x-time-filter-modes`, `x-measurement-catalog`, `x-error-codes`, `x-i18n` 7종은 root 에 두고 endpoint 는 키로만 참조. 각 vocab 의 필수 하위 키는 §4.1 표 참조.
8. **`$ref` 정책 (자가완결 우선)**:
   - **도메인 비즈니스 DTO** (`HostDto`, `AgentInfoDto` 등) → **endpoint 안에 inline** 풀어쓰기. response `data.content.items` / `data.<field>` 도 inline.
   - **도메인 무관 공용 타입** (`TimeFilter`, `ApiResponseDataObject`, `ApiResponseError`) → 같은 파일 `components.schemas` 1번 + 파일 내부 `$ref`. 본문 표준 정의는 §12 부록.
   - **외부 파일 `$ref` 금지** (예: `"../_shared/common.json#/..."`). 도메인당 1 JSON 파일은 **자가완결**해야 함. `_shared/` 는 도메인 간 복사용 **견본 보관소**일 뿐, 런타임 참조 대상 아님.
9. **자동화 추출 3원칙** (가이드 §0 동기화):
   - **Hand-curate 금지** — Claude 가 한글 라벨 사전을 직접 작성하지 않는다 (예: `enum-ko-fallback.json` 신설 ❌)
   - **모든 구조·필드·값 LLM 추정 금지** — Claude 의 도메인 상식으로 추정해 박지 않는 영역:
     1. enum / error code 한글 매핑 (예: `LINUX → "리눅스"`)
     2. **응답 schema 의 필드 (property name)** — `Map<String,Object>` / `ApiResponseData<Object>` 같은 generic erasure 응답이라도 **service 코드 (`...ServiceImpl.java`) 본문까지 따라가서** `data.put("xxx", ...)` 호출의 실제 키만 박는다
     3. **응답 example value 의 필드** — schema 에 박힌 필드와 동일해야 함 (없는 필드 추정 ❌)
     4. **description 의 "반환 핵심 필드: ..." 나열** — Java 코드에서 실제 발견된 필드명만 나열. 도메인 상식으로 (`agentVersion`, `agentPort` 등) 채우는 것 ❌
   - **허용 영역** (자연어 생성):
     - 메서드명/DTO명/필드명 자체 (Java 코드에서 발견된 것) 기반의 한국어 자연어
     - `summary` 본문 (예: "호스트 목록 조회")
     - `description` 의 자연어 설명 (단, 필드 나열은 코드 추적 결과만)
     - `examples[].summary` 한국어 자연어 질의
   - **Source 없으면 영문 echo / 빈 객체** —
     - enum / error code 한글 source 없을 때 → `{"AIX": "AIX"}` 식 키 자체 echo
     - 응답 필드 source 없을 때 (외부 lucida-common 타입 등 reach 밖) → `additionalProperties:true` + **빈 example** (`{}`) + description 에 "응답 구조는 service 구현 의존, 정적 추출 불가" 명시. **추정으로 필드 박는 것 ❌**
   - **자연어 매칭 보강은 examples summary 의 한국어 표현으로** (가이드 §7.2)

---

## 4. 입력 → 출력 매핑 (가이드 § ↔ 소스 위치)

| 가이드 § | 채울 것 | 어디서 가져오나 |
| --- | --- | --- |
| §3 | `openapi`/`info`/`servers`/`security` | 고정값 + 도메인명. servers = [절대 URL 1, `/` 1] |
| G1 §4 | `operationId` / `summary` / `description` / `tags` | controller `@Operation`. 부족하면 한국어로 직접 작성. summary 30 ~ 60자, description 100 ~ 200토큰, 반환 핵심 필드 한글 라벨 포함 |
| G1 §4 | `x-side-effect` | HTTP method 패턴: 조회 GET/POST = `read`, 등록/수정 POST/PUT = `write`, DELETE = `delete`, 다운로드 = `download` |
| G1 §4 | `x-llm-intent` | 의미 분류 — `list`, `detail`, `read`, `create`, `update`, `delete`, `export`, `search`, `filter`, `metric` 중 하나 이상. List-filter 는 보통 2~3개 조합 (예: `["list","search","filter"]`) |
| G2 §5 | input schema (strict) | request DTO (`@RequestBody`), `@PathVariable`, `@RequestParam`. 모든 property 에 `description`+`type`+`example`, 가능한 한 `enum`/`default`/`min`/`max`/`format`/`pattern` |
| G2 §5.3 | `x-source-endpoint`/`-field`/`-semantic-type` | 다른 endpoint 의 ID 출처 (예: resourceId → `/api/sms/hosts-filter`). semantic-type 키는 root 에서 정의 |
| G2 §5.4 | `x-source-field` JSONPath 표준 패턴 | paged: `$.data.content[*].<field>` · object: `$.data.<field>` · array: `$.data[*].<field>` · 중첩: `$.data.content[*].<sub>[*].<field>` |
| G2 §5.5 | `x-source-catalog` (operation 자체 메타 참조) | 같은 operation 의 메타 필드(예: `x-allowed-grid-filter-fields`) 를 참조할 때. 다른 endpoint 가 아닌 본 operation 메타에서 값을 가져오는 경우 |
| G3 §6.1 | `x-semantic-types` (root) | ID 종류 사전. 같은 ID 가 여러 endpoint 에서 쓰이면 root 에 1번만. 필수 하위 키는 §4.1 |
| G3 §6.2 | `x-tagfilter-grammar` (root) | tagFilters DSL — 가이드 §6.2 그대로 복사, 도메인별 `common_keys` 만 조정. 필수 하위 키는 §4.1 |
| G3 §6.3 | `x-time-filter-modes` (root) + `TimeFilter` (component) | TimeFilter component 1개 → endpoint 는 `$ref`. operation 별 `x-time-filter` 로 accepted_modes 좁힘. TimeFilter 본문은 §12 부록 |
| G3 §6.4 | `x-grids` (root) | `/swagger_model/lucida-ui` 컬럼 정의 + `/swagger_model/lucida-meta` 한글 라벨 매핑. operation 은 `x-grid: "<GridName>"` 만 적음. 필수 하위 키는 §4.1 |
| G3 §6.5 | `x-measurement-catalog` (root) | metric 카탈로그 (해당 도메인이 metric 지원 시). 필수 하위 키는 §4.1 |
| G3 §6.6 | `x-error-codes` (root) + `x-error-codes-applicable` (per op) | 정적 사전 부재 — 모든 lucida-domain-* 코드에서 호출 grep 후 unique 추출: `grep -rEh '"POLESTAR_[0-9]{5}"' /swagger_model/lucida-domain-*/src/main/java \| grep -oE 'POLESTAR_[0-9]{5}' \| sort -u`. 한글 메시지는 lucida-ui i18n JSON 의 `error.POLESTAR_*` 키 검색 |
| G3 §6.7 | `x-i18n` (root) | 가이드 §6.7 그대로 복사 (도메인 무관 공용). 필수 하위 키는 §4.1 |
| G3 §6.8 | enum 한글 라벨 | component schema enum → `x-enum-descriptions`(멤버→한글 직접). inline enum → `x-i18n-key-prefix`. 응답 단위 → `x-unit-key`. **i18n 키 명명**: `<category>.<scope>.<id>` 점 구분, category = `enum / field / metric / unit / error / filter_type / operator` |
| G4 §7 | examples (3~5개) | 직접 작성 — controller method명·summary 보고 한국어 자연어 질의 5종 (긍정/조건/카운트/구어체/동의어). key 는 영문 snake_case. 종류 1: `requestBody.content.*.examples`, 종류 2: `parameters[].examples`, 종류 3 (트리거): operation level `x-llm-examples` (값 없이 `summary` 만, 동의어/구어체 변형 3~5개) |
| G4 §7.6 | 응답 200 `example` + `data` shape inline | success+data 인라인. paged/object/array/binary 분기. action 은 `data: {type: "null"}` + `x-empty-data: true` |
| G5 §8.1 | `servers` | 고정 (Polestar production + same-origin). `{{template}}` 미해결 변수 금지 |
| G5 §8.2 | `securitySchemes.cookieAuth` | 고정 (가이드 §8.2 그대로). 본문은 §12 부록 |
| G5 §8.3 | `ApiResponseDataObject` envelope (allOf) | `components.schemas` 공용. data shape 만 endpoint 별 inline. 본문은 §12 부록 |
| G5 §8.4 | 4xx / 5xx 응답 | 모든 endpoint: 400/401/403/500. path param 있으면 404 추가. 모두 `ApiResponseError` $ref |
| G5 §8.5 | `x-envelope`, `x-error-codes-applicable` | `x-envelope`: `paged`/`object`/`array`/`binary`. error code 는 발생 가능한 것만 좁혀서 |
| §5.2 | DTO inline vs `$ref` 결정 | 도메인 DTO 는 endpoint 안에 inline, 공용 타입(TimeFilter / ApiResponseDataObject / ApiResponseError) 만 components.schemas + 파일 내부 `$ref`. 외부 파일 `$ref` 금지 |
| §10 | List-filter operation 메타 추가 3종 | `x-grid` (GridName) · `x-default-filter.tagFilters` (도메인 default 절, 예: `["confType = server"]`) · `x-tag-vocabulary` (tagFilters key 별 `enum`/`enum_ref`/`source_endpoint`) |

### 4.1 root vocabulary 필수 하위 키 (가이드 §6.1 ~ §6.7 압축표)

| vocab | 필수 하위 키 |
| --- | --- |
| `x-semantic-types.<id_type>` | `description` (string) · `providers` (string[]) · `field_name` (string) · `label_field` (string\|null) · `example` (string) |
| `x-tagfilter-grammar` | `_description` · `clause_shape` (`key`/`op`/`value`) · `common_keys` (도메인별 핵심 키 설명) · `wire_format` (`single_value`/`list_value`/`string_quoting`) · `compound` · `note` |
| `x-time-filter-modes` | `_description` · `epoch_unit: "milliseconds (int64)"` · `modes.<MODE>: { ko, rule }` · `ko_phrase_mapping_examples` |
| `x-grids.<GridName>` | `applies_to_endpoints` (string[]) · `columns[]: { field, headerName, filterType, sortable }` (옵션 `x-enum-ref`/`x-unit`). filterType ∈ `Text`/`Number`/`DateRange`/`SelectMulti`/`ManageStatus` |
| `x-measurement-catalog` | `_description` · `source` · `resource_types[]: { id, confType, displayNameKey, descriptionKey, icon, monitoring, singleResourceType }` |
| `x-error-codes` | `_description` · `source` · `codes: { POLESTAR_xxxxx: "한글 메시지 (선택적 {0} 치환자)" }` |
| `x-i18n` | `_description` · `filter_types` (5종) · `operators` (8종) · `operators_by_filter_type` (filterType 별 허용 operator 부분집합) |

operation 레벨 메타:

| 키 | 형식 | 비고 |
| --- | --- | --- |
| `x-side-effect` | enum: `read`/`write`/`delete`/`download` | 안전 가드 (가이드 §4.2). 모든 endpoint 필수 |
| `x-llm-intent` | string array | 의미 분류 (라우팅용). 모든 endpoint 필수 |
| `x-envelope` | enum: `paged`/`object`/`array`/`binary` | 응답 모양 분류 |
| `x-error-codes-applicable` | string[] | root `x-error-codes.codes` 키만 허용 |
| `x-grid` | string (GridName) | List-filter 인 경우. root `x-grids` 키 |
| `x-default-filter.tagFilters` | string[] | List-filter 인 경우 도메인 default 절 |
| `x-tag-vocabulary` | object | List-filter 인 경우 tag key 별 enum/source |
| `x-time-filter` | `accepted_modes` (string[]) · `requires_custom_range` (boolean) · `default_mode` (string) | TimeFilter 사용 endpoint |
| `x-empty-data` | boolean | action endpoint (응답 data 의도적 null) |
| `x-llm-examples` | array (`{summary}` 항목) | 트리거 endpoint (인자 없음) — 동의어/구어체 변형 3~5개 |

---

## 5. 8-Phase 워크플로우 (도메인 1개 기준)

> Phase 0 → 0.5 → 1 → 2 → 3 → 4 → 5 → 6. Phase 0.5 (i18n 사전 합성) 가 신설되어 8단계.

### Phase 0. 도메인 컨텍스트 로드
1. `/swagger_model/lucida-domain-<name>/src/main/java/` 하위 controller 디렉토리 트리 확인 (Glob `**/*Controller.java`).
2. 각 controller 의 `@RequestMapping`, method 시그니처, request/response DTO 패키지 추출.
3. `<Domain>ErrorCode.java` 위치 확인 (`/swagger_model/lucida-domain-<name>/src/main/java/.../exception/<Domain>ErrorCode.java`). 없으면 도메인에 정의된 코드 0건으로 처리.
4. `/swagger_model/lucida-ui/shared/constants/<name>/gridColumnDefs.ts` 에서 grid 컬럼 정의 확인 (TS 함수가 컬럼 배열 반환).
5. `application.yml` 의 `spring.application.name` 확인 (참고용).
6. `/swagger_model/lucida-domain-<name>/.claude/` 디렉토리 확인 — 이전 작업 흔적이나 도메인-특이 문맥이 있으면 참고.
7. POLESTAR 에러코드 호출처 추출 (코드 사용 여부): `grep -rEh '"POLESTAR_[0-9]{5}"' /swagger_model/lucida-domain-<name>/src/main/java \| grep -oE 'POLESTAR_[0-9]{5}' \| sort -u`. 한글 메시지는 Phase 0.5 에서 `<Domain>ErrorCode.java` 주석으로 매핑.

산출물: 작업 메모 (controller / DTO / ErrorCode / grid / .claude / error code 후보 표).

### Phase 0.5. i18n 사전 합성 (메모리 lookup table)

**자동 추출 3원칙 (HARD RULE #9) 준수**: hand-curate ❌, enum/error code 한글 LLM 추정 ❌, source 없으면 영문 echo. **별도 파일 생성 ❌** — 추출 결과는 메모리에 두고 Phase 3·4·5 에서 도메인 JSON 안에 inline 박는 데만 사용.

1. **UI 라벨 dict** (가장 유용):
   - `/swagger_model/lucida-ui/shared/i18n/json/messages_google_sheet.json` 에서 `module ∈ {"<domain>", "cmm"}` 항목만 필터.
   - `{fullResourceKey: ko_kr}` 매핑 dict 생성. ex: `{"cmm.system_name": "시스템 명", "cmm.cpu_usage_rate": "CPU 사용률"}`
   - 주의: `messages_ko_kr.json` 등 다른 ko_kr 파일은 **빈 placeholder** 라 사용 ❌

2. **Error code 한글 dict** (도메인별 변동):
   - `<Domain>ErrorCode.java` 라인주석 정규식 파싱: `^\s*([A-Z_]+)\("([0-9]+)"\),?\s*//\s*(.+)$`
   - 결과: `{"POLESTAR_<숫자>": "<주석>"}`. SMS/NMS 만 풍부, APM/WPM/LMS/etc 는 빈 dict.
   - ITG 는 `class + HashMap<Integer,String>` 별도 파싱.
   - 추출 실패한 코드 (Phase 0 step 7 호출처에는 있으나 dict 에 매핑 없음) → **영문 코드만** 박음 (`{"POLESTAR_00500": "POLESTAR_00500"}`). hand-curate / LLM 추정 ❌

3. **Enum 한글 dict** (가이드 §6.8 우선순위, 1:1 가능 enum 거의 없음):
   - ① 도메인 Java enum 파일 스캔 — displayName 필드 또는 javadoc/라인주석 한글 추출 (예: WPM `AlarmSeverity` `LEVEL1("...","해제",true)` → `{"LEVEL1": "해제"}`)
   - ② 위에서 빈 enum value → `messages_google_sheet.json` ko_kr lookup (단, ko_kr 가 한글일 때만. `cmm.up → "UP"` 같은 영문 echo 는 제외)
   - ③ ITG `/swagger_model/lucida-domain-itg/src/main/resources/init/data/itg_sys_cmn_code.json` lookup (제한적 — `instOsType` 정도)
   - 1~3 모두 실패 → enum value 자체로 영문 echo (`{"AIX": "AIX"}`). **hand-curate / LLM 추정 ❌**
   - 자연어 매칭 보강은 Phase 5 examples 의 한국어 표현으로 처리

4. **Filter type / operator dict** (가이드 §6.7 default 그대로):
   - 가이드 §6.7 의 `filter_types`, `operators`, `operators_by_filter_type` 그대로 메모리 dict 에 박음 (lookup 불필요, 그대로 출력).

산출물: 메모리 dict 4개 (`ui_labels` / `error_codes` / `enum_labels` / `i18n_defaults`). **파일 생성 ❌** (HARD RULE #6 자가완결 유지).

### Phase 1. Endpoint 인벤토리
모든 endpoint 를 표로 추출해 `openapi/INDEX.md` 의 도메인 섹션에 기록:

```
| HTTP | path                          | controller method                    | summary 후보              |
| POST | /api/sms/hosts-filter         | HostController.getHostListByGridFilter | 호스트 목록 조회         |
| GET  | /api/sms/configuration/{id}/.. | ConfigurationController.getBasicInfo | 호스트 기본 정보         |
```

### Phase 2. 6-Pattern 분류
각 endpoint 를 6가지 패턴 중 하나로 분류 (가이드 §1 의 4-pattern 을 실측 기반으로 확장):
- **List-filter** (`x-envelope: paged`) — paged 응답 + `tagFilters` / `gridFilters` / `sortFieldSets` 받음 (대표: `/api/sms/hosts-filter`)
- **Detail** (`x-envelope: object`) — path param(보통 chain ID) + object 응답
- **Action** (`x-envelope: object` + `x-empty-data: true`) — write / delete / trigger — 응답 data 비어있음
- **Count / Aggregate** (`x-envelope: object`) — scalar 또는 작은 object 집계 응답 (대표: `/standby-hosts/count`, `/resource/status`). `x-llm-intent`: `["count"]` 또는 `["read"]`
- **Export (binary)** (`x-envelope: binary`) — Excel/CSV 다운로드 (대표: `*-filter-excel`). `x-side-effect: download`. 응답 200 = `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (또는 `text/csv`) — JSON envelope 없음, `example` 생략
- **Measurement** (`x-envelope: array` 또는 `object`) — metric 조회. **응답 shape 가 도메인별로 다름**: 진짜 time series (`{resourceId, points[]}` 배열) vs List-filter 변형 (특정 host 의 디스크/프로세스 인벤토리). Phase 0 에서 응답 DTO 확인 후 결정

분류 안되면 List-filter 변형으로 시작 후 보고.

### Phase 3. Root vocabulary 작성
`<name>.openapi.json` skeleton 생성 (도메인당 **자가완결 단일 파일**):
- `openapi: "3.1.0"`, `info`, `servers`, `security: [{cookieAuth: []}]`
- `components.schemas`:
  - **공용** (도메인 무관 공통): `ApiResponseDataObject`, `ApiResponseError`, `TimeFilter` — §12 부록의 strict JSON 그대로 박음 (외부 `$ref` 금지)
  - **도메인 enum** (예: `OsTypeEnum`, `AvailabilityStatusEnum`) — 해당 도메인에서 여러 endpoint 가 공유할 때만 component 로 추출. `x-enum-descriptions` 는 **Phase 0.5 enum_labels dict 결과로 채움** (source 있는 멤버는 한글, 없는 멤버는 영문 echo `{"AIX": "AIX"}`). 전수 한글 강제 ❌. 그 외 enum 은 inline
- `components.securitySchemes.cookieAuth` (§12 부록)
- root 7종 vocabulary: `x-grids`, `x-semantic-types`, `x-tagfilter-grammar`, `x-time-filter-modes`, `x-error-codes`, `x-i18n`, `x-measurement-catalog` (해당 시) — 각 vocab 의 필수 하위 키는 §4.1 따라 채움
- **root `x-vocab-supported` 필수** (가이드 §6.0): `tagfilter`/`timefilter`/`measurement`/`grid`/`semantic_types` 5개 키 boolean. **transfer 금지** — controller 가 실제 받지 않는 vocab 은 `false` 박고 root 정의 생략. 판정 grep:
  ```bash
  BASE=/swagger_model/lucida-domain-<name>/src/main/java
  grep -rln "tagFilters\|TagFilter"      "$BASE" | wc -l   # >0 이면 tagfilter:true
  grep -rln "timeFilter\|TimeFilter"     "$BASE" | wc -l   # >0 이면 timefilter:true
  grep -rln "measurementId\|@Measurement" "$BASE" | wc -l  # >0 이면 measurement:true
  ```

**자가완결 원칙**: 모든 `$ref` 는 같은 파일 내부 (`#/components/...`) 만 사용. 외부 파일 `$ref` 금지.

도메인 비즈니스 DTO (예: `HostDto`, response 의 `data.content.items` 객체) 는 component 로 빼지 말고 endpoint 안에 **inline** 으로 풀어쓴다 (가이드 §5.2).

### Phase 4. Endpoint inline 채우기 (병렬 가능)
endpoint 단위로 §6 의 4-pattern skeleton 복붙 후 수정. 큰 도메인은 controller 단위로 task 위임 (executor agent).
한 endpoint 안에서:
1. `paths.<path>.<method>` G1 (operationId / summary / description / tags / x-side-effect / x-llm-intent / x-envelope / x-error-codes-applicable / x-grid / x-time-filter / x-default-filter / x-tag-vocabulary)
2. `requestBody` 또는 `parameters` G2 (strict object schema 또는 path/query)
3. examples (Phase 5)
4. responses (200 + 400/401/403/[404]/500). 200 응답 `data` shape 는 **inline** (List-filter `data.content.items` 도 inline)

#### Phase 4 — chain meta 의무 (path + body 양쪽)

> **path param 만이 아니라 body 의 ID-shape 필드도 chain meta 박는다** (가이드 §5.3.1).

**ID-shape 검출 룰** (작업 시 grep): 필드명이 `*Id` / `*Ids` / `*Key` / `*Identifier` 패턴 → chain 후보.
- 면제: `name`, `displayName`, `hostName`, `clusterName` 같은 자유 입력 label (`description` 에 "사용자 자유 입력" 명시)
- 외부: cloud credential / token / 외부 시스템 ID (`awsAccessKeyID`, `if_id`) → `x-external: true`

**적용 절차**:
1. body schema 작성 시 `*Id`/`*Ids`/`*Key` 매칭 필드 발견 → controller grep 으로 source endpoint 찾음
2. source 있으면: `x-source-endpoint` + `x-source-field` + `x-semantic-type` 박음 (path param 과 동일 정책)
3. source 없으면 (외부 시스템 / credential): `x-external: true`
4. Array 필드 (`*Ids`): items 가 ID 면 array schema 자체에 chain meta 박음 (LLM 은 multi-select 로 해석)

#### Phase 4 — 응답 schema 작성 절차 (HARD RULE #9 #2 #3 #4 강제)

응답 필드 추정 금지. controller 메서드 시그니처가 generic erasure (`Map<String,Object>`, `ApiResponseData<Object>`, `Object` 등) 면 다음 절차 따름:

1. **Service 메서드까지 추적**: controller 가 호출하는 service 메서드를 찾는다.
   ```bash
   # 예: ConfigurationController.getBasicInfo → ConfigurationService.getBasicInfo
   grep -n "getBasicInfo" /swagger_model/lucida-domain-<name>/src/main/java/.../service/<Domain>ServiceImpl.java
   ```
2. **`data.put("xxx", ...)` 패턴 추출**: service 본문에서 응답 Map 에 박는 키 목록을 그대로 추출.
   ```java
   // 예시 (ConfigurationServiceImpl.getBasicConfig):
   basicInfo.put(SmsConstant.OS_TYPE, ...);   // → "osType"
   basicInfo.put("osPatchLevel", ...);
   basicInfo.put("physicalCpuCount", ...);
   // ... 진짜 키 모두 나열
   ```
3. **Java 상수는 grep**: `SmsConstant.OS_TYPE` 같은 상수는 정의 파일까지 따라가서 진짜 키 값 (`"osType"`) 추출.
4. **빈 객체 wrapping 도 확인**: `data.put("basicConfig", getBasicConfig(...))` 같이 한 단계 wrap 되어 있으면 schema 도 같이 wrap 해야 함 (`data.basicConfig.{...}`)
5. **DTO 반환 (`HostInfoDto` 등) 인 경우**: DTO 클래스 본문 읽고 `private` 필드 모두 그대로 inline.
6. **Service 본문 못 읽거나 외부 lucida-common 타입 (`ApiResponseData`, `Page<T>`, `LinkedHashMap` 자체)** : `additionalProperties: true` + **빈 example `{}`** + description 에 "응답 구조는 service 구현 의존, 정적 추출 불가" 명시. **추정 ❌**

#### Phase 4 — description 작성 절차

`description` 의 자연어 본문은 LLM 자유롭게 작성 OK. 단:
- **"반환 핵심 필드: ..." / "반환 필드: ..." 같은 필드 나열은 응답 schema 의 properties 와 1:1 동일** 해야 함
- schema 에 없는 필드를 description 에 적는 것 ❌ (= 추정)
- schema 가 빈 객체 (`additionalProperties:true`) 면 description 에서도 필드 나열 안 함 — "응답 구조는 service 구현 의존" 만 명시

### Phase 5. Examples 작성
endpoint 당 3 ~ 5 개 한국어 자연어 질의 (key 는 영문 snake_case 시나리오명, 메타라벨 금지):
- 긍정 ("CPU 80% 넘는 서버 보여줘")
- 조건 ("리눅스 장비 목록")
- 카운트 ("윈도우 호스트 몇 대야?")
- 구어체 / 동의어 (서버 / 호스트 / 장비)
- 표현 변형

종류별 위치:
- 종류 1 (request body 있음): `requestBody.content.application/json.examples` — `value` 는 strict mode 풀 페이로드 (모든 required 포함)
- 종류 2 (body 없음 + path/query param 있음): `parameters[].examples` — 대표 parameter 1 개에 모음
- 종류 3 (인자 없는 트리거): operation level `x-llm-examples` — `value` 없이 `summary` 만 3~5개, 동의어/구어체 변형 강제

#### Phase 5 — 작성 후 체크리스트 (audit lessons, 사람용)

> 12 도메인 1705 endpoint audit 에서 발견된 결함 패턴. 각 endpoint 작성 직후 self-check. jq 검증 (Phase 6) 가 못 잡는 semantic 항목 위주.

**1. Key 명명 (메타라벨 blacklist 확장)**
- ❌ 금지: `ex1`/`ex2`/`ex3` (apm 80 endpoint 사례), `default_page`/`page_2`/`sort_asc`/`sort_desc`/`with_filter` (sms 79 endpoint 사례), `monitor_id_1`/`p1`/`canonical`/`default`/`case_N`
- ✅ 권장: 시나리오 영문 snake_case — `cpu_over_80`, `linux_only`, `recent_24h`, `prod_only`, `slow_sql_top10`

**2. Summary (도메인 어휘 강제)**
- ❌ 금지: generic CRUD ("조회", "확인", "검사") — itg 75% 가 이 패턴
- ✅ 권장: 도메인 용어 + 시나리오 (sms "CPU 80% 넘는 서버" / dpm "느린 SQL Top 10" / kcm "default 네임스페이스 running pod" / aiops "CPU 급증 이상감지" / lms "최근 1시간 ERROR 로그")
- **sampling base**: §13 도메인 시나리오 카탈로그 (`scenarios/<domain>.md`, 12 도메인 / 635 시나리오) 에서 매칭 카테고리 3-5개 가져옴

**3. Cross-endpoint 복붙 금지**
- ❌ 금지: 동일 5-key 가 N>5 endpoint 에 박힘 (sms list-filter 40개 동일 / apm scatter-chart 80개 ex1/ex2/ex3 / kcm profile-options 3개 동일 example set)
- ✅ 권장: 각 endpoint 가 자기 리소스/시나리오 반영. N>5 동일 phrase 면 sweep 대상

**4. Summary ↔ Value 일관성**
- ❌ 금지: summary "최근 1시간" 인데 `startTime: null` (kcm time-period 사례) / summary "linux 서버" 인데 value tagFilters 에 windows
- ✅ 권장: summary 의 주장이 value 에 실제 반영

**5. Template substitution bug**
- ❌ 금지: skeleton placeholder `{X}`/`{Y}` 가 같은 값으로 치환되어 "파드 파드" 같은 의미 깨진 텍스트 (kcm 22건 사례)
- ✅ 권장: skeleton 복붙 후 placeholder grep 으로 잔존/이중치환 확인

**6. Skeleton sms-specific 예시 의무 교체**
- ❌ 금지: §6 List-filter skeleton 의 `cpu_over_80`/`linux_only`/`ad_prefix`/`mem_heavy`/`count_windows` 는 **sms 전용** — 다른 도메인에 그대로 박음 ❌
- ✅ 권장: skeleton 은 **구조** 만 복사. examples 는 §13 카탈로그 (`scenarios/<도메인>.md`) 에서 도메인 시나리오 가져와 새로 채움

**7. x-llm-examples (트리거) 강제**
- audit 결과: aiops 1 / apm 2 / dpm 2 / kcm 1 만 사용 — 거의 미활용
- 인자 없는 trigger endpoint 는 `x-llm-examples` 슬롯에 3-5 동의어 변형 필수

**8. Value 의 동일 ID 반복 금지**
- ❌ 금지: response example 의 array 항목이 모두 같은 ID (automation `PLAN-0001` 4회 반복 사례)
- ✅ 권장: array 항목은 서로 다른 대표값 (3~5건)

### Phase 6. 자체 검증 (가이드 §11 15항 동형)

| # | 검증 | 자동화 |
| --- | --- | --- |
| 1 | OpenAPI 사양 준수 (3.1.0, 구조 유효) | `jq . > /dev/null` + `spectral lint --ruleset spectral:oas` |
| 2 | operationId / summary / description 모든 endpoint 존재 | jq (§7) |
| 3 | examples 3~5개 (종류 1·2·3 슬롯), 한국어 NL summary, 메타라벨 키 없음 | jq (§7) |
| 4 | 안전 가드 — 모든 endpoint 에 `x-side-effect` 필드 (read/write/delete/download) | jq (§7) |
| 5 | chain call 메타 — **path 변수 + body 의 ID-shape 필드** 모두 (a) `x-source-endpoint` + `x-source-field` 둘 다 보유, 또는 (b) `x-external: true`. `x-semantic-type` 은 옵션. ID-shape 룰: 필드명이 `*Id`/`*Ids`/`*Key`/`*Identifier` 매치 (free-form label 면제). 가이드 §5.3 / §5.3.1 | jq (§7) |
| 5b | x-vocab-supported — root 에 `x-vocab-supported` 객체 (5 키 boolean). `true` 키는 대응 vocab root 정의 동시 보유 (가이드 §6.0) | jq (§7) |
| 6 | strict mode — 모든 object schema 의 `additionalProperties: false` + `properties ⊆ required` | jq (§7) |
| 7 | 4xx / 5xx 응답 — 400/401/403/500 (path param 시 +404) | jq (§7) |
| 8 | enum 라벨 — component schema enum 의 `x-enum-descriptions` 가 enum 값 전부 커버 | jq (§7) |
| 9 | error code 정합 — operation `x-error-codes-applicable` ⊆ root `x-error-codes.codes` | jq (§7) |
| 10 | grid 정합 — operation `x-grid` ∈ root `x-grids`; `gridFilters[].field` enum ⊆ `x-grids[].columns[].field` | jq (§7) |
| 11 | semantic type 정합 — `x-semantic-type` ∈ root `x-semantic-types` | jq (§7) |
| 12 | examples 호출 가능 (stage 환경 있을 때만) — 각 `examples[].value` 를 stage 호출 → 200 응답, `responses['200'].example` 구조 일치 | (수동) |
| 13 | 응답 200 `example` 필수 — 모든 endpoint 에 `responses["200"].content.application/json.example` 존재. **`x-envelope: "binary"` 는 예외 (Export 패턴)** | jq (§7) |
| 14 | 응답 `data` shape — `data: {type: "null"}` 인 endpoint 는 `x-empty-data: true` 동반. 그 외에는 `data.type` / `properties` / `required` / `additionalProperties: false` 모두 inline 정의 (placeholder `{type: null}` 금지) | jq (§7) |
| 15 | LLM 정확도 (eval set 있을 때만) — endpoint 선택 ≥ 95%, args 채움 ≥ 90% (자연어 50~100개 질의) | (수동) |
| 16 | **응답 example ⊆ schema properties** — 응답 200 `example.data` 의 모든 키가 schema `data.properties` 키 집합의 부분집합. 차집합이 비어야 함 (LLM 추정으로 박힌 가짜 필드 검출) | jq (§7) |
| 17 | **응답 필드 source 추적 검증** — controller 가 `Map<String,Object>` / `Object` / `ApiResponseData<Object>` 같은 generic erasure 를 반환하는 endpoint 에 대해, 응답 schema 의 `data.properties` 키들이 service 메서드 본문의 `data.put("xxx", ...)` 호출 키 집합과 일치 (또는 `additionalProperties:true` + 빈 properties 로 fallback). 자동화 어려움 — 도메인당 sample 1~2개 endpoint 수동 검증 또는 critic agent 위임 | (수동 / critic) |
| ▶ | INDEX.md 진척도 갱신 | (수동) |

검증 실패 항목이 1건이라도 있으면 INDEX.md 의 Phase 6 ❌ — 수정 후 재검증.

#### 새 검증 #16 jq (응답 example ⊆ schema properties)

```bash
F=openapi/<domain>.openapi.json
jq -r '
  .paths | to_entries[] | .key as $p | .value | to_entries[] |
  select(.key | test("^(get|post|put|delete|patch)$")) | .value as $op |
  ($op.responses."200".content."application/json".example.data // null) as $ex |
  ($op.responses."200".content."application/json".schema.allOf // []
   | map(.properties.data.properties // {}) | add // {}) as $sch |
  if $ex == null or ($ex | type) != "object" then empty
  else
    (($ex | keys) - ($sch | keys)) as $diff |
    select($diff | length > 0) | "\($p): example data 에 schema 없는 키 — \($diff)"
  end
' "$F"
# 출력 0줄이면 OK. 한 줄이라도 있으면 LLM 추정 필드 검출 — Phase 4 응답 추적 절차 다시.
```

---

## 6. 6-Pattern Skeleton (붙여넣기 시작점)

> 모든 skeleton 은 **자가완결 원칙** 적용: 도메인 DTO 는 endpoint 안에 inline, `TimeFilter`/`ApiResponseDataObject`/`ApiResponseError` 만 같은 파일 `components.schemas` 의 `$ref`. 응답 200 `data` shape 도 inline (DTO `$ref` 사용 ❌).

### 6.1 List-filter
가이드 §10 `/api/sms/hosts-filter` 전체 블록을 그대로 복사 → 다음만 도메인에 맞게 수정:
- `operationId` / `summary` / `description` / `tags` / `x-llm-intent` (보통 `["list","search","filter"]`)
- `x-grid` 값 (해당 도메인 GridName)
- `x-default-filter.tagFilters` (도메인 default 절, 예: `["confType = server"]`)
- `x-tag-vocabulary` (tag key 별 `enum`/`enum_ref`/`source_endpoint`)
- `x-time-filter.accepted_modes` / `.default_mode`
- `x-error-codes-applicable`
- `tagFilters.default` / `.example`
- `gridFilters.items.properties.field.enum` (도메인 grid 의 컬럼)
- `gridFilters.items.properties.operator.enum` (root `x-i18n.operators_by_filter_type` 부분집합)
- `sortFieldSets.items.properties.fieldName.enum`
- `examples` 3 ~ 5 개 (한국어 NL)
- `responses.200.schema.allOf[1].properties.data.properties.content.items` 를 **inline strict object** 로 (도메인 DTO 의 모든 필드 + description + example) — `$ref` 사용 ❌
- `responses.200.example.data` (실제 모양 1건)

### 6.2 Detail (path param + chain)
```jsonc
"/api/<domain>/<resource>/{<id>}/<aspect>": {
  "get": {
    "operationId": "get<Aspect>By<Id>",
    "summary": "...",
    "description": "...",
    "tags": ["<DOMAIN> - <Resource>"],
    "x-side-effect": "read",
    "x-llm-intent": ["detail"],
    "x-envelope": "object",
    "x-error-codes-applicable": ["POLESTAR_00006","POLESTAR_00404","POLESTAR_00500"],
    "security": [{ "cookieAuth": [] }],
    "parameters": [{
      "name": "<id>", "in": "path", "required": true,
      "schema": { "type": "string" },
      "description": "...",
      "x-source-endpoint": "/api/<domain>/<list>",
      "x-source-field":    "$.data.content[*].<id>",
      "x-semantic-type":   "<id_type>",
      "examples": {
        "scenario1": { "summary": "...", "value": "..." },
        "scenario2": { "summary": "...", "value": "..." },
        "scenario3": { "summary": "...", "value": "..." }
      }
    }],
    "responses": {
      "200": {
        "description": "...",
        "content": { "application/json": {
          "schema": { "allOf": [
            { "$ref": "#/components/schemas/ApiResponseDataObject" },
            { "type": "object", "properties": {
              "data": {
                "type": "object",
                "additionalProperties": false,
                "required": ["<field1>", "<field2>", "..."],
                "properties": {
                  "<field1>": { "type": "string", "description": "...", "example": "..." },
                  "<field2>": { "type": "integer", "format": "int32", "description": "...", "example": 0 }
                }
              }
            }}
          ]},
          "example": { "success": true, "errorCode": null, "data": { "<field1>": "...", "<field2>": 0 } }
        }}
      },
      "400": { "description": "...", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } },
      "401": { "description": "...", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } },
      "403": { "description": "...", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } },
      "404": { "description": "...", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } },
      "500": { "description": "...", "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ApiResponseError" } } } }
    }
  }
}
```

### 6.3 Action (write / delete / trigger)
```jsonc
"/api/<domain>/<action>": {
  "post": {
    "operationId": "<verbNoun>",
    "summary": "...",
    "description": "...",
    "tags": ["<DOMAIN> - <Resource>"],
    "x-side-effect": "write",            // 또는 "delete"
    "x-llm-intent": ["update"],          // 또는 ["create"], ["delete"]
    "x-envelope": "object",
    "x-empty-data": true,
    "x-error-codes-applicable": ["POLESTAR_00006","POLESTAR_00404","POLESTAR_00500"],
    "security": [{ "cookieAuth": [] }],
    "requestBody": {                     // body 있는 경우
      "required": true,
      "content": { "application/json": {
        "schema": { /* strict object */ },
        "examples": { /* 종류 1 — 3~5개 */ }
      }}
    },
    // 또는 body 없는 트리거 endpoint:
    // "x-llm-examples": [
    //   { "summary": "에이전트 전부 시작" },
    //   { "summary": "agent 일괄 기동" },
    //   { "summary": "모든 호스트 에이전트 시작해줘" }
    // ],
    "responses": {
      "200": {
        "description": "성공 — data 없음.",
        "content": { "application/json": {
          "schema": { "allOf": [
            { "$ref": "#/components/schemas/ApiResponseDataObject" },
            { "type": "object", "properties": { "data": { "type": "null" } } }
          ]},
          "example": { "success": true, "errorCode": null, "data": null }
        }}
      },
      "400": { /* ApiResponseError $ref */ },
      "401": { /* ApiResponseError $ref */ },
      "403": { /* ApiResponseError $ref */ },
      "500": { /* ApiResponseError $ref */ }
    }
  }
}
```

### 6.4 Measurement (metric 조회)

> **응답 shape 분류 우선**: endpoint 이름이 `*-filter` / `*-info` 류이면 실제로는 **List-filter 변형** (특정 host 의 디스크/네트워크/프로세스/파일시스템/GPU 인벤토리) 일 수 있음. 진짜 time-series 는 별도 controller (`UserPerformanceMetric`, `RealtimeDashboard` 등) 일 수 있음. 작성 전 **응답 DTO 의 실제 모양**을 확인:
> - paged + grid filter 받음 → §6.1 List-filter 응용 (단 `x-llm-intent: ["metric"]`)
> - `{resourceId, points[]}` 시계열 배열 → 아래 skeleton (진짜 time-series)
> - aggregated object → §6.5 Count/Aggregate 응용

아래는 **진짜 time-series** 케이스 skeleton:

```jsonc
"/api/<domain>/measurement/<aspect>": {
  "post": {
    "operationId": "get<Aspect>Measurement",
    "summary": "...",
    "description": "...반환: 리소스별 시계열({timestamp(epoch ms), value})",
    "tags": ["<DOMAIN> - Measurement"],
    "x-side-effect": "read",
    "x-llm-intent": ["metric"],
    "x-envelope": "array",
    "x-error-codes-applicable": ["POLESTAR_00006","POLESTAR_00305","POLESTAR_00500"],
    "x-time-filter": {
      "accepted_modes": ["LIVE","MIN_15","MIN_30","HOUR","HOUR_3","TODAY","WEEK","MONTH","CUSTOM"],
      "requires_custom_range": false,
      "default_mode": "HOUR"
    },
    "security": [{ "cookieAuth": [] }],
    "requestBody": {
      "required": true,
      "content": { "application/json": {
        "schema": {
          "type": "object",
          "additionalProperties": false,
          "required": ["resourceIds","measurementId","timeFilter","arguments"],
          "properties": {
            "resourceIds": {
              "type": "array",
              "items": { "type": "string" },
              "minItems": 1,
              "description": "측정 대상 리소스 ID 목록. /api/<domain>/<list> 응답의 resourceId 사용.",
              "example": ["MA_LINUX_TEST_SERVER_01"],
              "x-source-endpoint": "/api/<domain>/<list>",
              "x-source-field": "$.data.content[*].resourceId",
              "x-semantic-type": "<id_type>"
            },
            "measurementId": {
              "type": "string",
              "description": "지표 ID. root x-measurement-catalog.resource_types[].id 의 값.",
              "example": "server.Server",
              "x-source-catalog": "x-measurement-catalog.resource_types[*].id"
            },
            "timeFilter": { "$ref": "#/components/schemas/TimeFilter" },
            "arguments": {
              "type": "object",
              "additionalProperties": false,
              "default": {},
              "description": "지표별 추가 인자 (interval 등).",
              "properties": {}
            }
          }
        },
        "examples": {
          "cpu_1h":         { "summary": "이 서버 CPU 1시간 추이 보여줘",     "value": { "resourceIds": ["MA_LINUX_TEST_SERVER_01"], "measurementId": "server.Server", "timeFilter": { "mode": "HOUR" }, "arguments": {} } },
          "memory_today":   { "summary": "오늘 메모리 사용량",                "value": { "resourceIds": ["MA_LINUX_TEST_SERVER_01"], "measurementId": "server.Server", "timeFilter": { "mode": "TODAY" }, "arguments": {} } },
          "multi_disk_io":  { "summary": "서버 5대 디스크 IO 30분치",          "value": { "resourceIds": ["MA_AD_SERVER_01","MA_LINUX_01","MA_LINUX_02","MA_WIN_01","MA_WIN_02"], "measurementId": "server.FileSystem", "timeFilter": { "mode": "MIN_30" }, "arguments": {} } }
        }
      }}
    },
    "responses": {
      "200": {
        "description": "지표 시계열 응답 (리소스별).",
        "content": { "application/json": {
          "schema": { "allOf": [
            { "$ref": "#/components/schemas/ApiResponseDataObject" },
            { "type": "object", "properties": {
              "data": {
                "type": "array",
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["resourceId","points"],
                  "properties": {
                    "resourceId": { "type": "string", "description": "리소스 ID", "example": "MA_LINUX_TEST_SERVER_01" },
                    "points": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["timestamp","value"],
                        "properties": {
                          "timestamp": { "type": "integer", "format": "int64", "description": "epoch milliseconds", "example": 1714280400000 },
                          "value":     { "type": "number",  "description": "측정값",                    "example": 23.5 }
                        }
                      }
                    }
                  }
                }
              }
            }}
          ]},
          "example": { "success": true, "errorCode": null, "data": [{ "resourceId": "MA_LINUX_TEST_SERVER_01", "points": [{ "timestamp": 1714280400000, "value": 23.5 }, { "timestamp": 1714280460000, "value": 25.1 }] }] }
        }}
      },
      "400": { /* ApiResponseError $ref */ },
      "401": { /* ApiResponseError $ref */ },
      "403": { /* ApiResponseError $ref */ },
      "500": { /* ApiResponseError $ref */ }
    }
  }
}
```

> 위 skeleton 은 진짜 time-series 케이스. List-filter 변형 measurement 는 §6.1 List-filter skeleton 응용 (`x-llm-intent: ["metric"]`, response `data` shape 만 metric 모양으로). aggregated object 응답은 §6.5 Count/Aggregate skeleton 응용.

### 6.5 Count / Aggregate (scalar / 작은 object 응답)
```jsonc
"/api/<domain>/<resource>/count": {
  "post": {
    "operationId": "count<Resource>By<Filter>",
    "summary": "...",
    "description": "... 반환: totalCount(전체 개수) / 상태별 개수 등 scalar/object 집계",
    "tags": ["<DOMAIN> - <Resource>"],
    "x-side-effect": "read",
    "x-llm-intent": ["count"],
    "x-envelope": "object",
    "x-error-codes-applicable": ["POLESTAR_00006","POLESTAR_00500"],
    "security": [{ "cookieAuth": [] }],
    "requestBody": { /* 필터 조건 (tagFilters 등). 인자 없으면 생략 또는 트리거 패턴 */ },
    "responses": {
      "200": {
        "description": "집계 결과.",
        "content": { "application/json": {
          "schema": { "allOf": [
            { "$ref": "#/components/schemas/ApiResponseDataObject" },
            { "type": "object", "properties": {
              "data": {
                "type": "object",
                "additionalProperties": false,
                "required": ["totalCount"],
                "properties": {
                  "totalCount": { "type": "integer", "format": "int64", "description": "전체 개수", "example": 8 },
                  "byStatus":   { "type": "object", "additionalProperties": { "type": "integer", "format": "int64" }, "description": "상태별 개수 (예: {UP: 6, DOWN: 2})", "example": { "UP": 6, "DOWN": 2 } }
                }
              }
            }}
          ]},
          "example": { "success": true, "errorCode": null, "data": { "totalCount": 8, "byStatus": { "UP": 6, "DOWN": 2 } } }
        }}
      },
      "400": { /* ApiResponseError $ref */ },
      "401": { /* ApiResponseError $ref */ },
      "403": { /* ApiResponseError $ref */ },
      "500": { /* ApiResponseError $ref */ }
    }
  }
}
```

### 6.6 Export (binary — Excel/CSV 다운로드)
```jsonc
"/api/<domain>/<resource>-filter-excel": {
  "post": {
    "operationId": "export<Resource>ByGridFilter",
    "summary": "...",
    "description": "<List-filter> 와 동일 조건으로 Excel 다운로드.",
    "tags": ["<DOMAIN> - <Resource>"],
    "x-side-effect": "download",
    "x-llm-intent": ["export"],
    "x-envelope": "binary",
    "x-error-codes-applicable": ["POLESTAR_00006","POLESTAR_00500"],
    "security": [{ "cookieAuth": [] }],
    "requestBody": {
      "required": true,
      "content": { "application/json": {
        "schema": { /* List-filter 와 동일 strict object (tagFilters/gridFilters/sortFieldSets/...) */ },
        "examples": { /* 3~5개 — "엑셀로 받아줘" / "다운로드" / 구어체 */ }
      }}
    },
    "responses": {
      "200": {
        "description": "Excel 파일 (binary).",
        "content": {
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": { "type": "string", "format": "binary" }
          }
        },
        "headers": {
          "Content-Disposition": { "schema": { "type": "string", "example": "attachment; filename=\"hosts-2026-04-28.xlsx\"" } }
        }
      },
      "400": { /* ApiResponseError $ref */ },
      "401": { /* ApiResponseError $ref */ },
      "403": { /* ApiResponseError $ref */ },
      "500": { /* ApiResponseError $ref */ }
    }
  }
}
```

> Export 는 binary 응답이므로 가이드 §7.6 의 `data` shape inline 규칙은 적용되지 않음. 200 응답 `example` 도 binary 라 생략. CI 검증 #13 에서 `x-envelope: "binary"` 인 endpoint 는 example 누락 OK.

---

## 7. 검증 명령어 (가이드 §11 15항 동형 jq)

```bash
DOMAIN=sms
F=openapi/$DOMAIN.openapi.json

# #1 JSON 유효성
jq . "$F" > /dev/null && echo "OK #1"

# #2 operationId / summary / description 누락 endpoint 검출 (0 이어야 함)
jq '[.paths | to_entries[] | .key as $p | .value | to_entries[] |
     select(.key | test("^(get|post|put|delete|patch)$")) | .value |
     select((has("operationId") and has("summary") and has("description")) | not)] | length' "$F"

# #3 endpoint 별 examples 개수 (3 ~ 5 강제)
jq -r '.paths | to_entries[] | .key as $p | .value | to_entries[] |
       select(.key | test("^(get|post|put|delete|patch)$")) |
       "\($p) \(.key) examples=\(
          (.value.requestBody.content."application/json".examples // {} | length) +
          ((.value.parameters // []) | map(.examples // {}) | map(length) | add // 0) +
          ((.value."x-llm-examples" // []) | length)
       )"' "$F"

# #4 x-side-effect 누락 endpoint 검출 (0 이어야 함)
jq '[.paths | to_entries[] | .key as $p | .value | to_entries[] |
     select(.key | test("^(get|post|put|delete|patch)$")) | .value |
     select((has("x-side-effect")) | not)] | length' "$F"

# #5a chain call 메타 — path 변수가 (src+field) 또는 (x-external:true) 어느 쪽도 아니면 위반
jq '[.paths | to_entries[] | .key as $p | .value as $pv |
     ($pv | to_entries[] | select(.key | test("^(get|post|put|delete|patch)$"))) as $op |
     ($pv.parameters // []) + ($op.value.parameters // []) |
     .[] | select(.in == "path") |
     select(
       ((has("x-source-endpoint") and has("x-source-field")) or (."x-external" == true)) | not
     )] | length' "$F"

# #5a-body chain call 메타 — body 의 ID-shape 필드 (가이드 §5.3.1)
# free-form label (name/displayName/hostName/clusterName) 은 면제
jq '[.. | objects | .properties // {} | to_entries[] |
     select(.key | test("(?i)Ids?$|Key$|Identifier$|resourceI|agentI|hostI|serviceI|deviceI|nodeI|podI|sessionI|interfaceK|traceI|spanI|policyI|profileI|jobI|taskI|userI|tenantI|clusterI|namespaceI|measurementI|roleI|loginI|organizationI")) |
     select(.key | test("(?i)^(name|displayName|hostName|clusterName|nodeName|podName|namespaceName)$") | not) |
     select((.value | type) == "object") |
     select((.value | (has("x-source-endpoint") and has("x-source-field")) or (."x-external" == true)) | not)
    ] | length' "$F"

# #5b x-vocab-supported root 마커 + true 키 ↔ 대응 vocab 동시 보유
jq '
  (."x-vocab-supported" // null) as $vs |
  if $vs == null then ["MISSING root x-vocab-supported"]
  else
    [
      (if $vs.tagfilter      == true and (has("x-tagfilter-grammar")    | not) then "tagfilter:true but x-tagfilter-grammar absent"     else empty end),
      (if $vs.timefilter     == true and (has("x-time-filter-modes")    | not) then "timefilter:true but x-time-filter-modes absent"   else empty end),
      (if $vs.measurement    == true and (has("x-measurement-catalog")  | not) then "measurement:true but x-measurement-catalog absent" else empty end),
      (if $vs.grid           == true and (has("x-grids")                | not) then "grid:true but x-grids absent"                     else empty end),
      (if $vs.semantic_types == true and (has("x-semantic-types")       | not) then "semantic_types:true but x-semantic-types absent"  else empty end)
    ]
  end
' "$F"

# #6 strict mode — additionalProperties 누락 object schema 검출
jq '[.. | objects | select(.type == "object") | select(has("additionalProperties") | not)] | length' "$F"

# #6 strict mode — properties - required 차집합 (비어야 함)
jq '[.. | objects | select(.type == "object" and (has("properties") and has("required"))) |
     ((.properties | keys) - .required) | select(length > 0)] | length' "$F"

# #7 4xx/5xx 응답 빠짐 검출
jq -r '.paths | to_entries[] | .key as $p | .value | to_entries[] |
       select(.key | test("^(get|post|put|delete|patch)$")) |
       "\($p) \(.key) responses=\(.value.responses // {} | keys | tostring)"' "$F"

# #8 enum 라벨 — component schema enum 의 x-enum-descriptions 멤버 커버
jq '[.components.schemas // {} | to_entries[] |
     select(.value.enum != null) |
     {name: .key, missing: ((.value.enum) - ((.value."x-enum-descriptions" // {}) | keys))} |
     select(.missing | length > 0)]' "$F"

# #9 x-error-codes-applicable ⊆ root x-error-codes.codes
jq '[.paths | .. | objects | ."x-error-codes-applicable" // empty | .[]] - (."x-error-codes".codes // {} | keys)' "$F"

# #10 x-grid 정합 — operation x-grid ∈ root x-grids
jq '[.paths | .. | objects | ."x-grid" // empty] - (."x-grids" // {} | keys | map(select(. != "_description")))' "$F"

# #11 x-semantic-type 정합 — 모든 사용처 ∈ root x-semantic-types
jq '[.. | objects | ."x-semantic-type" // empty] - (."x-semantic-types" // {} | keys | map(select(. != "_description")))' "$F"

# #13 응답 200 example 필수 — 누락 endpoint
jq -r '.paths | to_entries[] | .key as $p | .value | to_entries[] |
       select(.key | test("^(get|post|put|delete|patch)$")) |
       select(.value.responses."200".content."application/json".example == null) |
       "\($p) \(.key) MISSING-200-example"' "$F"

# #14 data shape — data: {type:null} 인 endpoint 는 x-empty-data:true 동반해야 함
jq -r '.paths | to_entries[] | .key as $p | .value | to_entries[] |
       select(.key | test("^(get|post|put|delete|patch)$")) |
       . as $op |
       (.value.responses."200".content."application/json".schema.allOf // []) | map(.properties.data // empty) | .[] |
       select(.type == "null") |
       select($op.value."x-empty-data" != true) |
       "\($p) \($op.key) data:null but x-empty-data missing"' "$F"

# #1 Spectral (있을 때)
spectral lint "$F" --ruleset spectral:oas
```

---

## 8. 진척도 추적 (`openapi/INDEX.md`)

매 phase 완료 시 INDEX.md 의 도메인 행 갱신:
- Phase 0 ~ 1 완료 → endpoint 인벤토리 표 채움
- Phase 2 완료 → 4-pattern 분류 카운트 기록
- Phase 3 완료 → root vocab ✅
- Phase 4 ~ 5 진행 중 → endpoint 작성 진행률 (`12/47`)
- Phase 6 완료 → CI 검증 ✅, 산출물 링크

---

## 9. 작업 시 금지 사항 재확인

- `/swagger_model/**` 의 비즈니스 로직 (controller 본문, DTO 필드, entity, `.gradle` / `.yml` / `.properties`) 수정 금지. 어노테이션 보강은 로컬 옵션, **단 어떤 변경도 push 금지** (HARD RULE #1)
- 산출물 외 다른 위치에 OpenAPI 파일 생성 금지 (`openapi/<name>.openapi.json` 만). 별도 i18n / fallback 사전 파일 생성 ❌ (HARD RULE #6, #9 / Phase 0.5 메모리 dict 만)
- examples summary 에 출처 표시·메타라벨·enum 코드값 노출 금지
- 응답 `data` 를 `{type: "null"}` placeholder 로 두는 것 금지 (의도된 action 응답만 허용 + `x-empty-data: true`)
- 응답 `data.content.items` / `data.<field>` 를 도메인 DTO `$ref` 로 두는 것 금지 — **반드시 inline strict object**
- 외부 파일 `$ref` 금지 (자가완결)
- **enum / error code 한글 라벨 hand-curate 금지** — Claude 가 직접 한글 매핑 작성 ❌ (HARD RULE #9)
- **enum / error code 한글 LLM 추정 금지** — `LINUX → "리눅스"`, `JWT_TOKEN_EXPIRED → "JWT 토큰 만료"` 같은 상식 추정 ❌. source 없으면 영문 echo (HARD RULE #9)
- **응답 schema 필드 LLM 추정 금지** — controller 가 `Map<String,Object>` / `Object` 반환이라도 **service 메서드 본문까지 따라가서 진짜 키 추출**. 도메인 상식으로 (`agentVersion`, `agentPort` 등) 채우기 ❌. 못 추출하면 `additionalProperties:true` + 빈 example (HARD RULE #9 / Phase 4 응답 schema 작성 절차)
- **응답 example 필드 LLM 추정 금지** — schema properties 와 1:1 동일. schema 에 없는 필드 example 에 박는 것 ❌ (Phase 6 #16 검증)
- **description 의 "반환 핵심 필드: ..." 나열 LLM 추정 금지** — Java 코드 추적 결과만 나열. schema 에 없는 필드 description 에 적는 것 ❌
- (단 메서드명·DTO 기반의 `summary` 본문 / `description` 자연어 설명 / `examples[].summary` 한국어 자연어 작성은 **허용** — 추출이 아니라 자연어 생성)

### Examples quality 안티패턴 (12 도메인 audit lessons)

> 1705 endpoint audit 결과 quality 1-2.5/5점 도메인 8/12. 아래 패턴 금지. 상세 체크리스트는 Phase 5 참조.

- **메타라벨 잔존 금지** — examples key 가 `ex1`/`ex2`/`ex3` (apm 80 endpoint), `default_page`/`page_2`/`sort_asc`/`sort_desc`/`with_filter` (sms 79), `monitor_id_N`/`p1`/`p2`/`canonical`/`default`/`case_N`. blacklist 좁게 두지 말고 **시나리오 영문 snake_case** 만 허용 (`cpu_over_80`, `slow_sql_top10`)
- **5-key 복붙 금지 (cross-endpoint)** — 같은 5 examples set 이 N>5 endpoint 에 박힌 형태. 각 endpoint 자기 시나리오 가지기 (sms list-filter 40개 / apm scatter 80개 사례)
- **Generic CRUD summary 금지** — "조회"/"확인"/"검사" 만 쓰면 도메인 어휘 없음 (itg 75% 사례). **§13 도메인 시나리오 카탈로그 에서 sampling 강제**
- **Summary↔Value 불일치 금지** — summary "최근 1시간" 인데 value `startTime: null` (kcm time-period 사례)
- **Template substitution 검증** — skeleton placeholder 가 같은 값으로 양쪽 치환되어 "파드 파드" 같은 깨진 텍스트 만들지 말 것 (kcm 22건 사례)
- **§6 List-filter skeleton 의 sms-specific examples 그대로 박지 말 것** — `cpu_over_80`/`linux_only`/`ad_prefix`/`mem_heavy`/`count_windows` 는 sms 전용. 다른 도메인은 도메인 시나리오 새로 생성. skeleton 은 구조만 복사
- **Response example array 동일 ID 반복 금지** — `PLAN-0001` 4회 같은 케이스 (automation 사례). 서로 다른 대표값 3~5건
- **x-llm-examples 미활용 금지** — 인자 없는 trigger endpoint 는 `x-llm-examples` 슬롯 의무 (audit 결과 aiops/apm/dpm/kcm 1-2건만 사용)

### 알려진 갭 (deferred sweep — 작업 시 인지)

> INDEX.md "발견된 갭" 섹션 동기화. 새 endpoint 작성 시 **반복 회피**.

- **body chain meta 642 fields** (8 도메인) — body 의 `*Id`/`*Ids`/`*Key` 필드에 `x-source-endpoint`/`x-external` 박기. 가이드 §5.3.1 / Phase 4 chain meta 절차 참조
- **x-grids root vocab** 6 도메인 — gridColumnDefs.ts 추출 미완료. operation `x-grid` 박을 때 root `x-grids` 같이 박기
- **examples quality** 1705 endpoint sweep 미완료 — 신규 endpoint 작성 시 위 안티패턴 회피 + Phase 5 체크리스트 8항 self-check

---

## 10. 첫 사용 / 재진입 절차

- `openapi/<name>.openapi.json` 없으면 → Phase 0 ~ 3 후 skeleton 저장 + INDEX.md 행 초기화
- 있으면 → INDEX.md 의 미작성 endpoint 그룹 한 개씩 추가 (Phase 4 ~ 5 반복)
- 끝날 때마다 Phase 6 자체 검증 + INDEX.md 갱신

---

## 11. 참고 견본

가이드 §10 의 `/api/sms/hosts-filter` 전체 블록이 List-filter 의 정답 견본. 의문이 생기면 항상 가이드를 먼저 참조하고, 가이드에 명시되지 않은 부분만 본 스킬에서 결정한다.

---

## 12. 부록 — 공용 component strict JSON

도메인 파일 작성 시 아래 3개 schema + securitySchemes 를 **그대로 복사**해 자기 `components` 에 박는다. (외부 `$ref` 금지)

### 12.1 `ApiResponseDataObject`

> ⚠️ §11 #6 strict mode 와 일관 — 모든 property 가 `required` 에 포함, optional 영역은 `type: [..., "null"]`. 가이드 §8.3 동기화.

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

### 12.2 `ApiResponseError`

> ⚠️ §11 #6 strict mode 와 일관. 가이드 §8.4 동기화.

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

### 12.3 `TimeFilter`
```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["mode"],
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["LIVE","MIN_15","MIN_30","HOUR","HOUR_3","NOW","TODAY","DAY_3","WEEK","MONTH","MONTH_3","MONTH_6","YEAR","CUSTOM"],
      "x-enum-descriptions": {
        "LIVE": "실시간", "MIN_15": "최근 15분", "MIN_30": "최근 30분",
        "HOUR": "최근 1시간", "HOUR_3": "최근 3시간", "NOW": "현재",
        "TODAY": "오늘", "DAY_3": "최근 3일", "WEEK": "최근 1주",
        "MONTH": "최근 1개월", "MONTH_3": "최근 3개월", "MONTH_6": "최근 6개월",
        "YEAR": "최근 1년", "CUSTOM": "사용자 지정"
      }
    },
    "startTime": { "type": "integer", "format": "int64", "description": "시작 시각 (epoch milliseconds). mode=CUSTOM 일 때 필수." },
    "endTime":   { "type": "integer", "format": "int64", "description": "종료 시각 (epoch milliseconds). mode=CUSTOM 일 때 필수." }
  }
}
```

### 12.4 `securitySchemes.cookieAuth`
```json
{
  "type": "apiKey",
  "in":   "cookie",
  "name": "SESSION_ID",
  "description": "Polestar 표준 세션 쿠키. 로그인 endpoint(/api/account/login)가 발급. 만료 시 401 + POLESTAR_00401."
}
```

### 12.5 `x-i18n` (root, 도메인 무관 공용)
```json
{
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

### 12.6 `x-time-filter-modes` (root, 도메인 무관 공용)
```json
{
  "_description": "TimeFilter.mode enum reference. 모드가 CUSTOM 이 아니면 startTime/endTime 은 서버가 모드 규칙대로 채움.",
  "epoch_unit": "milliseconds (int64)",
  "modes": {
    "LIVE":   { "ko": "실시간",     "rule": "endTime=now; 짧은 슬라이딩 윈도우" },
    "MIN_15": { "ko": "최근 15분",  "rule": "now-15m ~ now" },
    "MIN_30": { "ko": "최근 30분",  "rule": "now-30m ~ now" },
    "HOUR":   { "ko": "최근 1시간", "rule": "now-1h ~ now" },
    "HOUR_3": { "ko": "최근 3시간", "rule": "now-3h ~ now" },
    "NOW":    { "ko": "현재",       "rule": "endTime=now; 1포인트" },
    "TODAY":  { "ko": "오늘",       "rule": "오늘 00:00 ~ now" },
    "DAY_3":  { "ko": "최근 3일",   "rule": "now-3d ~ now" },
    "WEEK":   { "ko": "최근 1주",   "rule": "now-7d ~ now" },
    "MONTH":  { "ko": "최근 1개월", "rule": "now-30d ~ now" },
    "MONTH_3":{ "ko": "최근 3개월", "rule": "now-90d ~ now" },
    "MONTH_6":{ "ko": "최근 6개월", "rule": "now-180d ~ now" },
    "YEAR":   { "ko": "최근 1년",   "rule": "now-365d ~ now" },
    "CUSTOM": { "ko": "사용자 지정", "rule": "startTime + endTime (epoch-millis) 명시 필수" }
  },
  "ko_phrase_mapping_examples": {
    "지금": "NOW", "실시간": "LIVE", "최근 15분": "MIN_15",
    "오늘": "TODAY", "어제부터": "CUSTOM (startTime=어제 00:00, endTime=now)",
    "지난 3일간": "DAY_3"
  }
}
```

### 12.7 `x-tagfilter-grammar` (root, 도메인 무관 공용 — `common_keys` 만 도메인별 조정)
```json
{
  "_description": "tagFilters 구조화 형식. 배열 원소 1건 = clause 1건. 원소 간 AND.",
  "clause_shape": {
    "key":   "string. 예: confType, tag.<name>, os, hostName",
    "op":    "= | != | IN | NOT IN",
    "value": "string (단일) | string[] (IN/NOT IN 시)"
  },
  "common_keys": {
    "confType":   "리소스 타입. 도메인별 default 값 명시 (예: sms = 'server')",
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
  "note":     "operation 의 x-default-filter.tagFilters 에 명시된 clause 는 호출 시 반드시 포함."
}
```

---

## 13. 도메인 시나리오 카탈로그

> 12 도메인 examples 작성 시 sampling base. Phase 5 #2/#6 (도메인 어휘 / skeleton sms-specific 적응) 보완용. **새 endpoint 작성 시 generic CRUD ("조회"/"확인") 만들지 말고 이 카탈로그에서 가져옴**.

### 13.1 카탈로그 인덱스

각 파일 = 도메인 1개. 위치: `.omc/skills/openapi-llm-spec/scenarios/<domain>.md`

| 도메인 | 시나리오 # | 파일 | 핵심 시나리오 |
| --- | ---: | --- | --- |
| sms        | 47  | [scenarios/sms.md](scenarios/sms.md)               | `cpu_over_80`, `linux_only`, `agent_old_version`, `cm_log_register` |
| apm        | 108 | [scenarios/apm.md](scenarios/apm.md)               | `slow_trace_top10`, `error_traces_today`, `entrypoint_topn` |
| aiops      | 78  | [scenarios/aiops.md](scenarios/aiops.md)           | `cpu_spike_anomaly`, `disk_capacity_7d`, `error_log_anomaly` |
| automation | 43  | [scenarios/automation.md](scenarios/automation.md) | `daily_backup_2am`, `disaster_recovery_flow`, `aws_credential` |
| dpm        | 67  | [scenarios/dpm.md](scenarios/dpm.md)               | `slow_sql_top10`, `blocking_sessions`, `deadlock_recent` (7 DBMS 대칭) |
| itg        | 28  | [scenarios/itg.md](scenarios/itg.md)               | `batch_executed_today`, `process_engine_run`, `if_id_call` |
| kcm        | 45  | [scenarios/kcm.md](scenarios/kcm.md)               | `crashloopbackoff_pods`, `oomkilled_pods`, `node_not_ready` |
| lms        | 28  | [scenarios/lms.md](scenarios/lms.md)               | `error_logs_recent_1h`, `warn_count_today`, `parsing_test` |
| nms        | 71  | [scenarios/nms.md](scenarios/nms.md)               | `down_interfaces`, `vlan_specific_ports`, `snmp_oid_walk` |
| syslog     | 39  | [scenarios/syslog.md](scenarios/syslog.md)         | `error_recent_1h`, `critical_by_host`, `severity_count_today` |
| tcm        | 46  | [scenarios/tcm.md](scenarios/tcm.md)               | `run_now_pending_jobs`, `pending_approvals`, `force_terminate` |
| wpm        | 35  | [scenarios/wpm.md](scenarios/wpm.md)               | `slow_response_services`, `heap_dump_request`, `running_threads_by_agent` |
| **총** | **635** | — | — |

### 13.2 사용법 (4단계)

1. **endpoint 분류 식별**: operationId / path / x-llm-intent 로 카테고리 판정 (예: `/api/sms/hosts-filter` → list-filter)
2. **카탈로그 sampling**: 위 파일에서 매칭 카테고리 섹션 열고 시나리오 3-5개 선택
3. **Value 적응**: 선택한 시나리오의 summary 는 그대로, value 는 endpoint body schema 에 맞게 채움
4. **Self-check**: Phase 5 체크리스트 8항 통과 (특히 #1 메타라벨 / #3 cross-endpoint dedup / #6 sms skeleton 그대로 박지 않음)

### 13.3 카탈로그 vs §6 skeleton 차이

- **§6 skeleton**: 구조 (operationId/parameters/requestBody/responses 형틀) — sms-specific examples 박혀있음 → **그대로 복붙 ❌**
- **§13 카탈로그**: 도메인별 시나리오 (key + summary + intent) — 도메인 적응 베이스 → **여기서 가져와 §6 skeleton 의 examples block 채움**

### 13.4 카탈로그 보강 / 재생성

도메인 controller 가 추가 / 변경되면 해당 카탈로그 파일 수동 갱신. 단 **30-50 시나리오 / 도메인 한도 유지** (sampling base 라 너무 많으면 부담). intent 미커버 분류 발견 시 우선 추가.
