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

### 메트릭 카탈로그 조회 (필수 — 알람 추가 전 선행)

알람 정의를 추가하려면 정확한 `measurementDefinitionId` 와 `units` 가 필요. **반드시 먼저 카탈로그 조회**:

```bash
RES_TYPE="postgresql.Database"   # 알람 대상 resourceType (정확히 일치해야 함)

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg rt "$RES_TYPE" '{parameter:{resourceType:$rt}}')" \
  "$POLESTAR10_BASE_URL/api/measurement/definitions/resource-type"
```

응답 (예: postgresql.Database 30개):
```json
{
  "success": true,
  "data": [
    {
      "id": "postgresql.Database_LockCount",
      "name": "LockCount",
      "displayKey": "dpm.lock_count",
      "alias": "LC",
      "description": "데이터베이스 Lock 수",
      "resourceType": "postgresql.Database",
      "category": "postgresql.Database",
      "units": "COUNT",
      "measurementType": "METRIC",
      "numericType": "DYNAMIC",
      "osType": "ALL"
    },
    { "id": "postgresql.Database_sessionCount", "alias": "SC", "units": "COUNT", ... },
    { "id": "postgresql.Database_bufferHitRatio", "alias": "BR", "units": "PERCENTAGE", ... }
  ]
}
```

> **알람 추가 시 활용**: 메트릭 응답의 `id`, `alias`, `units`, `measurementType` 4개 필드가 그대로 알람 정의의 `measurementDefinitionId`, `measurementAlias`, condition.`units`, `measurementType` 로 들어감. 즉 **메트릭 정의 1개 조회로 알람 정의 필수 메타 자동 채울 수 있음**.

**메트릭 prefix 규칙**: `id` 는 항상 `<resourceType>_<metric>` 형식. 알람 정의의 `resourceType` 필드와 prefix 가 **반드시 일치** 해야 함. 불일치 시 detail 호출에서 NPE — UI 의 상세 drawer 안 열림.

**`targetConfIds` 형식 — type 별 표** (NKIAAI-539 Phase B + APM 검증):

| resourceType | targetConfIds 형식 | 추출 endpoint | 비고 |
|---|---|---|---|
| `weburl.Weburl` | `weburl_<24-hex-id>` | `POST /api/weburl/list-filter` `content[].id` | 이미 prefix 된 형태로 응답 |
| `server.Server` | `<resourceId>_server.Server` | `POST /api/sms/hosts-filter` `content[].resourceId` + 뒤에 `_server.Server` 붙임 | resourceId 형식 `MA_<host>_<ts>` |
| `postgresql.Database` | `<resourceId>_postgresql.Database_<dbName>` | DPM list `content[].resourceId` + DB 이름 (수동 조합) | numeric resourceId |
| `postgresql.PostgreSQL` | `<resourceId>_postgresql.PostgreSQL` | 위 + `_postgresql.PostgreSQL` | 인스턴스 단위 알람 |
| **`apm.Agent`** | **`<agent-hash>_apm.Agent`** | ⚠️ **service resourceId 아님!** 다음 endpoint 의 `confId` 필드 그대로 사용:<br>**`POST /api/apm/agents/list-filter`** `content[].confId` (등록된 agent 들)<br>또는 `POST /api/apm/standby-agents-filter-step1` `content[].confId` (등록 전) | agent 별로 hash 다름. service 안에 multiple agent 면 각 agent 마다 별도 confId |
| `kcm.Pod` | `<pod-uuid>` (prefix 없음) | KCM list 의 Pod UUID | 단순 UUID, 다른 type 과 명명 다름 |
| `kcm.Cluster` | `<resourceId>_kcm.Cluster` (추정) | TBD | Cluster 단위 알람 미캡처 |
| `nms.Network` | TBD | NMS list-filter `resourceId` 추정 | TBD |

→ **각 type 별로 추출 규칙 다름**. 오케스트레이터가 target type 에 따라 dispatch 필요.

### APM/WPM 의 confId 추출 — 시나리오별

| 상황 | 추출 방법 |
|---|---|
| 등록된 service 의 agent | `POST /api/apm/agents/list-filter` 응답의 `content[].confId` (recipe `list-targets.md` 참조) |
| Standby 상태 agent (등록 직전) | `POST /api/apm/standby-agents-filter-step1` 응답의 `content[].confId` |
| 이미 알람 있는 service 의 confId | `POST /api/alarm/alarm-definitions` 응답의 `content[].confId` (해당 resourceId 필터) |
| 추측해서 만들기 | ❌ **금지** — service resourceId × `_apm.Agent` 형식이 아님. NPE 발생 |

> **참고**: 응답 필드 이름이 endpoint 별로 약간 다름. `/api/measurement/definitions/resource-type` 은 `id` 필드, `/api/alarm/options/measurementDefinition` 은 `measurementDefinitionId` 필드 — 같은 값이지만 키 이름 차이. 위 카탈로그 endpoint 사용 권장 (스키마 풍부).

자주 쓰일 resourceType 별 메트릭 카운트 참고:

| resourceType | 메트릭 수 | 단위 예 |
|---|---|---|
| `postgresql.Database` | 30 | COUNT, PERCENTAGE |
| `postgresql.PostgreSQL` | 28 | (DB 자체) |
| `weburl.Weburl` | 9 | MILLISECONDS, BOOLEAN |
| `server.Server` | 15 | PERCENTAGE, COUNT, BYTES |
| `server.LogMonitor` | 8 | (사용자 정의 LOG) |
| `server.ProcessMonitor` | 15 | (사용자 정의 프로세스) |
| `apm.Agent` | 48 | MILLISECONDS, COUNT, ... |
| `kcm.Pod` | 39 | (Pod 단위) |
| `kcm.Cluster` | 39 | (Cluster 전체) |
| `kcm.Container` | 15 | |
| `kcm.Node` | 32 | |
| `mysql.MySQL` | 30 | |
| `oracle.Oracle` | 26 | |
| `tibero.Tibero` | 26 | |

→ DB 류는 `<vendor>.<Vendor>` (인스턴스) vs `<vendor>.Database` (DB 단위) 두 layer 가 존재. 알람은 **Database 단위에 거는 게 일반적**.

### 추가 (`POST /api/alarm/alarm-definition`)

> ⚠️ URL 이 단수 `alarm-definition` (POST 자체가 add). list 는 복수 `alarm-definitions`. 헷갈리지 말 것.

> ⚠️ **POST body 에 누락하면 detail 호출 시 NPE 발생 (UI drawer 안 열림)**:
> - top-level: `measurementType`, `measurementAlias`, `activeAlarmPolicy`, `maxAlarmsPerMin`
> - 각 condition: `measurementType`, `conditionText`, `units` (메트릭의 units 와 일치)
> - 메트릭 prefix 가 `resourceType` prefix 와 일치해야 함

기존 polestar10 알람을 그대로 본떠 만든 검증된 payload (PostgreSQL Lock 수 알람):

```bash
# 1) 메트릭 카탈로그에서 단위(units) + displayKey 조회 (위 절차)
METRIC_ID="postgresql.Database_LockCount"
METRIC_UNITS="COUNT"
RES_TYPE="postgresql.Database"

# 2) 대상 conf id (alarm-definitions list 의 기존 항목 confId 와 동일 형식)
TARGET_CONF_ID="954854831_postgresql.Database_plopvape"

# 3) POST body 풀 스키마
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg conf "$TARGET_CONF_ID" \
      --arg metric "$METRIC_ID" \
      --arg units "$METRIC_UNITS" \
      --arg rt "$RES_TYPE" \
      '{
        # target
        targetConfIds: [$conf],
        # 메타
        name: "plopvape DB Lock 수 알람",
        description: "DB lock 건수 4-step 임계치",
        enabled: true,
        resourceType: $rt,
        # 메시지 + 타임아웃
        alarmMessageTemplate: "${resourceName} ${defaultConditionLog}",
        alarmTimeout: 3,
        timeoutSeverity: "LEVEL1",
        # 메트릭 — 누락하면 NPE
        measurementDefinitionId: $metric,
        measurementType: "METRIC",
        measurementAlias: "LC",
        activeAlarmPolicy: "LAST_ONE",
        maxAlarmsPerMin: 10,
        # 4-step conditions
        conditions: [
          { type:"THRESHOLD", alarmSeverity:"LEVEL1", measurementDefinitionId:$metric,
            measurementType:"METRIC", operator:"LESS_THAN", numericThreshold:12,
            conditionText:"Lock 수 < 12", units:$units,
            dampeningType:"NONE", byAi:false },
          { type:"THRESHOLD", alarmSeverity:"LEVEL2", measurementDefinitionId:$metric,
            measurementType:"METRIC", operator:"GREATER_THAN_OR_EQUAL", numericThreshold:12,
            conditionText:"Lock 수 >= 12", units:$units,
            dampeningType:"NONE", byAi:false },
          { type:"THRESHOLD", alarmSeverity:"LEVEL3", measurementDefinitionId:$metric,
            measurementType:"METRIC", operator:"GREATER_THAN_OR_EQUAL", numericThreshold:20,
            conditionText:"Lock 수 >= 20", units:$units,
            dampeningType:"NONE", byAi:false },
          { type:"THRESHOLD", alarmSeverity:"LEVEL4", measurementDefinitionId:$metric,
            measurementType:"METRIC", operator:"GREATER_THAN_OR_EQUAL", numericThreshold:40,
            conditionText:"Lock 수 >= 40", units:$units,
            dampeningType:"NONE", byAi:false }
        ],
        alarmNotifications: [],
        triggerActions: []
      }')" \
  "$POLESTAR10_BASE_URL/api/alarm/alarm-definition"
# → {"success":true,"data":<numeric-affected-count>}
```

**Top-level 필드** (모두 누락 시 NPE 위험):
| 필드 | 설명 | 값 예 |
|---|---|---|
| `targetConfIds` | 대상 conf ID 배열 | `["954854831_postgresql.Database_plopvape"]` |
| `name`, `description` | 알람 이름·설명 | |
| `enabled` | 활성화 | `true` |
| `resourceType` | 대상 리소스 타입. metric prefix 와 일치 필수 | `"postgresql.Database"` |
| `alarmMessageTemplate` | 알람 메시지 템플릿 (`${resourceName}`, `${defaultConditionLog}` 등) | `"${resourceName} ${defaultConditionLog}"` |
| `alarmTimeout` | 타임아웃 (초) | `3` |
| `timeoutSeverity` | 타임아웃 심각도 | `"LEVEL1"` |
| **`measurementDefinitionId`** | 정확한 메트릭 ID (카탈로그 조회 결과) | `"postgresql.Database_LockCount"` |
| **`measurementType`** | 메트릭 타입 | `"METRIC"` (`"EVENT"`, `"LOG"` 등도 가능) |
| **`measurementAlias`** | 짧은 별칭 (메시지 템플릿용) | `"LC"`, `"CPU"` 등 |
| **`activeAlarmPolicy`** | 동시 알람 처리 정책 | `"LAST_ONE"` (최근 발생 1건만 활성) |
| `maxAlarmsPerMin` | 분당 알람 발생 한도 | `10` (null 도 가능하지만 명시 권장) |
| `conditions[]` | 조건 배열 (보통 4-step) | 아래 표 |
| `alarmNotifications` | 알림 채널 | `[]` (없으면) |
| `triggerActions` | 트리거 액션 | `[]` |

**조건 (`conditions[]`) 필드** — 각 step 에 모두 채워야 함:
| 필드 | 설명 | 값 예 |
|---|---|---|
| `type` | 조건 타입 | `"THRESHOLD"`, `"BASELINE"`, AI 기반 등 |
| `alarmSeverity` | 심각도 | `"LEVEL1"` (정상) ~ `"LEVEL4"` (위험) |
| `measurementDefinitionId` | top-level 과 동일 메트릭 | (반복) |
| **`measurementType`** | top-level 과 동일 (보통 `"METRIC"`) | `"METRIC"` |
| `operator` | 비교 연산자 | `"GREATER_THAN_OR_EQUAL"`, `"LESS_THAN"`, `"EQUALS"`, ... |
| `numericThreshold` | 임계값 | 메트릭 단위 따라 |
| `numericThreshold2` | 두번째 임계값 (range 비교) | 보통 `null` |
| `stringThreshold` | 문자열 비교용 | 보통 `null` |
| **`conditionText`** | UI 표시용 텍스트 (예: `"Lock 수 < 12"`) | 직접 채워야 함 |
| `units` | 단위. **메트릭 카탈로그의 `units` 와 일치 필수** | `"COUNT"`, `"PERCENTAGE"`, `"MILLISECONDS"`, `"BYTES"` |
| `dampeningType` | 노이즈 억제 | `"NONE"`, `"OCCURRENCES"`, `"EVALUATIONS"` |
| `occurrences`, `evaluations` | dampening 파라미터 | dampeningType 별 |
| `byAi` | AI 자동 임계치 여부 | `false` (수동) |

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

## 부가: Severity / 도메인 / 전체 메트릭 (정책 정의 시 부가 정보)

```bash
# 1) Severity 메타 (LEVEL1~4 의 표시 이름·색상 등)
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/alarm/severity/list"

# 2) 도메인 옵션 (공통 정책 추가 시 도메인 선택지)
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/alarm/resource/domain/options"

# 3) 전체 메트릭 catalog (모든 type 통합, 1400+ 항목 — 클라이언트 필터링 필요)
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/alarm/options/measurementDefinition"
# → type 별 필터된 list 가 필요하면 위 "메트릭 카탈로그 조회" 섹션의 resource-type endpoint 사용
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
