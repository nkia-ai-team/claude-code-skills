# Recipe: 알람 정책 등록

polestar10 의 알람 정책은 두 종류:

| 종류 | 정의 | 적용 범위 | 엔드포인트 prefix |
|---|---|---|---|
| **공통 정책** (Common policy) | 도메인별 임계치 템플릿 (예: "PostgreSQL 기본 임계치") | tag 기반 다수 리소스 | `/api/alarm/policys/*` |
| **개별 알람 정의** (Individual definition) | 특정 리소스 한정 알람 | 단일 또는 소수 리소스 | `/api/alarm/alarm-definition*` |

UI: **알람 > 정책 관리 > 공통 정책** vs **개별 정책** 탭으로 나뉨.

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## 공통 알람 정책 — Common Policy

### 목록

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"arguments":{},"tagFilters":null}' \
  "$POLESTAR10_BASE_URL/api/alarm/policys"
```

응답 `content[]`:
```json
{
  "id": "<policy-id>",
  "name": "PostgreSQL 기본 임계치",
  "domain": "postgresql",
  "tagKey": "alarmPolicy",
  "enabled": true,
  "alarmDefinitions": [...],
  "targetResources": [...],
  "enableCount": 5,
  "default": true   // 시스템 기본 정책 여부
}
```

### 추가 (기존 정책 복사 기반)

polestar10 의 공통 정책 추가는 **순수 신규 정의가 아니라 기존 정책 복사** 흐름. UI 도 마찬가지.

```bash
# 0) 복사할 source 정책 ID 먼저 조회 (위 목록에서 적당한 default 정책 하나)
SOURCE_POLICY_ID="<24-hex-char-source-policy-id>"   # 위 list 응답에서 적합한 default 정책 .id
ROLE_ID="<24-hex-char-role-id>"             # 권한 부여할 role (보통 admin role)

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg name "testbed-common-probe" \
      --arg src "$SOURCE_POLICY_ID" \
      --arg role "$ROLE_ID" \
      '{
        name: $name,
        description: $name,
        enable: true,
        copyId: $src,
        tagValue: $name,
        authorityInfos: [{roleId: $role, permission: 15}],
        domain: "server"
      }')" \
  "$POLESTAR10_BASE_URL/api/alarm/policys/add"
# → {"success":true,"data":true}
```

**필드 의미**:
| 필드 | 설명 |
|---|---|
| `name` | 정책 이름 (UI 표시용) |
| `description` | 설명 |
| `enable` | 활성화 여부 |
| `copyId` | 복사 source 정책 ID (필수 — 0 부터 만들지 않음) |
| `tagValue` | 정책 태그 값. 보통 name 과 동일. 리소스 등록 시 `alarmPolicy` 태그로 자동 매칭 |
| `authorityInfos` | 권한 부여. `permission: 15` = 모든 권한 |
| `domain` | 적용 도메인. `server`, `cubrid`, `postgresql`, `oracle`, `apm`, `kcm`, `weburl` 등 |

### 이름 중복 검증

추가 전 호출 권장:
```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"name":"testbed-common-probe","domain":"server"}' \
  "$POLESTAR10_BASE_URL/api/alarm/policys/add/validate/name/duplicate"
```

### 삭제

```bash
POLICY_ID="<24-hex-char-policy-id>"   # add 응답에는 ID 없음 — list 로 조회 필요

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$POLICY_ID" '{ids:[$id]}')" \
  "$POLESTAR10_BASE_URL/api/alarm/policys/delete"
# → {"success":true,"data":{"deletedCount":1,"notDeletedCount":0,"notDeletedList":[]}}
```

---

## 개별 알람 정의 — Individual Definition

### 목록

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"tagFilters":[]}' \
  "$POLESTAR10_BASE_URL/api/alarm/alarm-definitions"
```

### 추가 (`POST /api/alarm/alarm-definition`)

> ⚠️ URL 이 단수 `alarm-definition` (POST 자체가 add). list 는 복수 `alarm-definitions`. 헷갈리지 말 것.

```bash
TARGET_CONF_ID="weburl_xxxxxxxxxxxxxxxxxxxxxxxx"   # weburl/list-filter 등에서 가져옴
METRIC_ID="weburl.Weburl_Total"                     # measurement/definitions 에서 조회

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg conf "$TARGET_CONF_ID" \
      --arg metric "$METRIC_ID" \
      '{
        targetConfIds: [$conf],
        name: "네이버 응답시간 임계치",
        description: "네이버 HTTP 응답시간 4-step 임계치",
        enabled: true,
        resourceType: "weburl.Weburl",
        alarmMessageTemplate: "${resourceId} 응답시간 알람",
        alarmTimeout: 10,
        timeoutSeverity: "LEVEL1",
        measurementDefinitionId: $metric,
        maxAlarmsPerMin: null,
        conditions: [
          {
            type: "THRESHOLD",
            alarmSeverity: "LEVEL1",
            measurementDefinitionId: $metric,
            operator: "LESS_THAN",
            numericThreshold: 500,
            units: "MILLISECONDS",
            dampeningType: "NONE",
            byAi: false
          },
          {
            type: "THRESHOLD",
            alarmSeverity: "LEVEL2",
            measurementDefinitionId: $metric,
            operator: "GREATER_THAN_OR_EQUAL",
            numericThreshold: 500,
            units: "MILLISECONDS",
            dampeningType: "NONE",
            byAi: false
          },
          {
            type: "THRESHOLD",
            alarmSeverity: "LEVEL3",
            measurementDefinitionId: $metric,
            operator: "GREATER_THAN_OR_EQUAL",
            numericThreshold: 1000,
            units: "MILLISECONDS",
            dampeningType: "NONE",
            byAi: false
          },
          {
            type: "THRESHOLD",
            alarmSeverity: "LEVEL4",
            measurementDefinitionId: $metric,
            operator: "GREATER_THAN_OR_EQUAL",
            numericThreshold: 1100,
            units: "MILLISECONDS",
            dampeningType: "NONE",
            byAi: false
          }
        ],
        alarmNotifications: [],
        triggerActions: []
      }')" \
  "$POLESTAR10_BASE_URL/api/alarm/alarm-definition"
# → {"success":true,"data":<numeric-affected-count>}
```

**조건 (`conditions[]`) 필드**:
| 필드 | 설명 | 값 예 |
|---|---|---|
| `type` | 조건 타입 | `"THRESHOLD"` (다른 값: AI 기반 등) |
| `alarmSeverity` | 심각도 | `"LEVEL1"` (정상/낮음) ~ `"LEVEL4"` (위험) |
| `operator` | 비교 연산자 | `"GREATER_THAN_OR_EQUAL"`, `"LESS_THAN"`, `"EQUALS"` 등 |
| `numericThreshold` | 임계값 | 메트릭에 따라 ms / % / count |
| `numericThreshold2` | 두번째 임계값 (range 비교 시) | 보통 null |
| `units` | 단위 | `"MILLISECONDS"`, `"PERCENTAGE"`, `"COUNT"` 등 |
| `dampeningType` | 노이즈 억제 | `"NONE"`, `"OCCURRENCES"`, `"EVALUATIONS"` |
| `occurrences`, `evaluations` | dampening 파라미터 | dampeningType 별로 사용 |
| `byAi` | AI 자동 임계치 여부 | `false` (수동), `true` (AI 학습) |

### 상세 조회

```bash
DEF_ID="<24-hex-char-definition-id>"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$DEF_ID" '{parameter:$id}')" \
  "$POLESTAR10_BASE_URL/api/alarm/alarm-definition/detail"
```

응답 `data` 주요 필드:
- `id`, `name`, `type:"Individual"`, `description`, `enabled`
- `hostName`, `resourceId`, `resourceName`, `confId`, `resourceType`
- `alarmMessageTemplate`, `measurementDefinitionId`
- `conditions[]` (위 add 와 동일 스키마)
- `createdBy`, `modifiedBy`

### 삭제

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$DEF_ID" '{parameter:[$id]}')" \
  "$POLESTAR10_BASE_URL/api/alarm/alarm-definition/delete"
```

### 수정 — TBD

`POST /api/alarm/alarm-definition/update` 가 endpoints 에 존재. body 형태 미캡처 — 추정: add body + `id` 추가.

---

## 부가: 메트릭 / Severity 메타 (정책 정의 시 필요)

```bash
# 1) measurementDefinitionId 후보 조회 (resourceType 별)
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"resourceType":"weburl.Weburl"}' \
  "$POLESTAR10_BASE_URL/api/alarm/options/measurementDefinition"

# 2) Severity 메타
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/alarm/severity/list"

# 3) 도메인 옵션 (정책 추가 시)
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/alarm/resource/domain/options"
```

---

## 흐름 요약 (오케스트레이터 관점)

### 공통 정책으로 도메인 전체 커버하기
```
1. /api/alarm/policys 로 default 정책 조회 → 적합한 source 정책 ID 확보
2. /api/alarm/policys/add (copyId=source) 로 신규 정책 생성
3. (옵션) /api/alarm/policy/definitions 로 임계치 customize
4. 리소스 등록 시 register payload 의 anomalyPolicyTagValue / 알람 태그에 정책 이름 사용
```

### 개별 정의로 특정 리소스 커버
```
1. /api/alarm/options/measurementDefinition 로 메트릭 후보 조회
2. /api/alarm/alarm-definition (POST) 로 정의 생성
3. /api/alarm/alarm-definition/detail 로 검증
4. (필요 시) /api/alarm/alarm-definition/update 로 수정
5. /api/alarm/alarm-definition/delete 로 정리
```

---

## UI Fallback

> **알람 > 정책 관리 > 공통 정책** (또는 **개별 정책**) → 우측 상단 **+ 추가** → (공통: 도메인 선택 + 복사 source 선택 / 개별: 대상 리소스 + 메트릭 + 임계값 입력) → 저장.
