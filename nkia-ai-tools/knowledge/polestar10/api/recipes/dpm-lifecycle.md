# Recipe: DPM (DB Performance Monitoring) 라이프사이클

DPM 은 polestar10 의 다른 리소스 타입과 **등록/삭제 패턴이 다름**:

- **에이전트 heartbeat 모델 아님** — polestar10 가 직접 DB 에 접속해서 SQL 쿼리로 모니터링
- 따라서 사용자가 등록 시점에 **DB 접속 정보를 직접 입력** 해야 함
- staging step (`save`) 가 없는 대신 **`preregister` (사용자 입력 폼) → `register` (활성화)** 흐름
- 삭제는 **GET method + path 에 resourceId** (다른 타입의 POST + body 와 다름)

지원 DB:
```bash
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  "$POLESTAR10_BASE_URL/api/dpm/preregister/dbtypes"
# → ["postgresql.PostgreSQL","oracle.Oracle","mysql.MySQL","sqlserver.SQLServer","cubrid.Cubrid","tibero.Tibero","mariadb.MariaDB"]
```

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## DB 타입별 list

각 DB 종류마다 별도 list endpoint:
```
POST /api/dpm/postgresql/list
POST /api/dpm/oracle/list
POST /api/dpm/mysql/list
POST /api/dpm/mariadb/list
POST /api/dpm/sqlserver/list
POST /api/dpm/cubrid/list
POST /api/dpm/tibero/list
```

body 공통:
```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"pagePerSize":20,"sortFieldSets":[],"gridFilters":[],"tagFilters":["confType = postgresql"]}' \
  "$POLESTAR10_BASE_URL/api/dpm/postgresql/list"
```

응답 `content[]` 핵심 필드:
- `resourceId` (numeric 문자열, 예 `"954854831"`)
- `resourceType` (`"postgresql.PostgreSQL"` 등)
- `hostName`, `dbName`, `port`, `version`
- `availabilityStatus`, `managementStatus`, `cpuRatio`, `sessionUtilization` 등 메트릭

---

## 등록 (3-step: dbtypes → preregister → register)

### Step 1 — DB 타입 + staging 정보 입력 (`POST /api/dpm/preregister`)

```bash
# 사용자 입력값 모음
DB_TYPE="postgresql.PostgreSQL"
DB_HOST="<db-host-ip>"        # 모니터링 대상 DB 서버의 IP/host
DB_PORT=30432
DB_NAME="plopvape"
DB_USER="plopvape"
DB_PASS="plopvape1234"
SVC_GROUP="RCA-Testbed"

# preregister body (search-time 자동 표시용)
SEARCH_TIME=$(date '+%Y-%m-%d %H:%M:%S')

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg rt "$DB_TYPE" --arg host "$DB_HOST" --argjson port "$DB_PORT" \
      --arg dbname "$DB_NAME" --arg user "$DB_USER" --arg pass "$DB_PASS" \
      --arg sg "$SVC_GROUP" --arg t "$SEARCH_TIME" \
      '{resourceType:$rt, hostName:$host, port:$port, dbName:$dbname,
        userName:$user, passwd:$pass, searchTime:$t,
        connectType:null, ssl:false, cmUserName:null, cmPassWord:null, cmPort:0,
        topSQLCount:30, sessionHistoryInterval:0,
        tableHistory:false, indexHistory:false, sessionHistory:true,
        planHistory:false, topSQLHistory:true,
        collectorPolicyTagValue:"defaultPolicy",
        anomalyPolicyTagValue:"성능 이상감지 기본 정책",
        serviceGroupTagValue:$sg,
        groupId:"1"}')" \
  "$POLESTAR10_BASE_URL/api/dpm/preregister"
```

이 호출이 polestar10 가 DB 접속 시도 + 검증을 하는 단계. 성공 시 staging 에 들어감.

### Step 2 — staging 확인 (`GET /api/dpm/preregister/list`)

```bash
curl $POLESTAR10_CURL_OPTS -X GET \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/dpm/preregister/list"
# → {"success":true,"data":[ ... staging 항목들 ... ]}
```

여기서 등록 대상의 `resourceId` 추출 (성공 시점에 polestar10 가 자동 부여, 또는 재등록 시 사용자가 명시).

### Step 3 — 활성화 (`POST /api/dpm/register`)

```bash
# preregister 와 거의 동일 body + resourceId + managementStatus
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg rt "$DB_TYPE" --arg host "$DB_HOST" --argjson port "$DB_PORT" \
      --arg dbname "$DB_NAME" --arg user "$DB_USER" --arg pass "$DB_PASS" \
      --arg sg "$SVC_GROUP" --arg rid "<resourceId-from-staging>" \
      --arg t "$SEARCH_TIME" \
      '{resourceType:$rt, hostName:$host, port:$port, dbName:$dbname,
        userName:$user, passwd:$pass, resourceId:$rid, searchTime:$t,
        managementStatus:"MANAGED",
        connectType:null, topSQLCount:30, ssl:false,
        cmUserName:null, cmPassWord:null, cmPort:0, sessionHistoryInterval:0,
        tableHistory:false, indexHistory:false, sessionHistory:true,
        planHistory:false, topSQLHistory:true,
        collectorPolicyTagValue:"defaultPolicy",
        anomalyPolicyTagValue:"성능 이상감지 기본 정책",
        serviceGroupTagValue:$sg, groupId:"1"}')" \
  "$POLESTAR10_BASE_URL/api/dpm/register"
# → {"success":true,"data":{... 등록된 정보 ..., resourceId:"..."}}
```

> **중요**: 같은 `resourceId` 로 `unregister` 후 다시 `register` 하면 **이전에 묶여있던 알람 정의들이 자동 reattach**. 새 resourceId 로 등록하면 알람들은 orphan 으로 남음 (다시 매칭 안 됨).

---

## 삭제 (unregister)

```bash
RESOURCE_ID="954854831"

curl $POLESTAR10_CURL_OPTS -X GET \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/dpm/unregister/$RESOURCE_ID"
# → {"success":true,"data":"954854831"}
```

> ⚠️ **다른 type 과 다름**:
> - method = **GET** (POST 아님)
> - body = **없음** (path 에 ID)
> - URL = `/unregister/<id>` (`/delete` 아님)

---

## 알람 cascade 동작 (검증 결과)

검증된 동작:

```
T1: PostgreSQL 알람 4개 묶여있음 (resourceId=954854831)
T2: GET /api/dpm/unregister/954854831  → DB 등록 해제
T3: 같은 resourceId 로 POST /api/dpm/register
T4: PostgreSQL 1건 복귀 + 알람 4개 ctime 변동 없이 reattach
```

→ **cascade rule = orphan + auto-reattach by resourceId**

함의:
- DPM 등록 해제는 **알람을 즉시 삭제하지 않음** (orphan 상태로 남음)
- 같은 `resourceId` 로 재등록하면 알람 자동 reattach
- 다른 `resourceId` 로 재등록하면 alarm 은 영구 orphan (수동 정리 또는 새 알람으로 교체 필요)

---

## 부가 endpoints

### DPM 전용 메트릭 catalog

```bash
RES_TYPE="postgresql.PostgreSQL"
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  "$POLESTAR10_BASE_URL/api/dpm/measurement/definitions/resourcetype/$RES_TYPE/metric"
```

응답 스키마는 `/api/measurement/definitions/resource-type` 과 동일 (id/alias/units/measurementType/description).

### Detail / Summary / Efficiency

```bash
RID="954854831"
# config 정보
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  "$POLESTAR10_BASE_URL/api/dpm/configuration/$RID/basic-info"

# summary
curl $POLESTAR10_CURL_OPTS -X GET --cookie "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/dpm/postgresql/instance/$RID/summary"

# efficiency
curl $POLESTAR10_CURL_OPTS -X GET --cookie "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/dpm/postgresql/instance/$RID/efficiency"

# 상태
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d "{\"resourceId\":\"$RID\"}" \
  "$POLESTAR10_BASE_URL/api/dpm/resource/status"
```

---

## 흐름 요약 (오케스트레이터 관점)

### 신규 DB 등록
```
1. /api/dpm/preregister/dbtypes          → 사용자에게 DB 종류 선택지 제시
2. (사용자 입력)                          → host, port, dbname, user, password, 그룹
3. /api/dpm/preregister                  → polestar10 가 DB 접속 검증
4. /api/dpm/preregister/list             → 신규 staging 항목의 resourceId 추출
5. /api/dpm/register                     → 활성화 (resourceId 명시)
6. (검증) /api/dpm/<dbtype>/list         → totalElements 증가 확인
```

### DB 재등록 (알람 보존)
```
1. (사전) /api/dpm/<dbtype>/list         → 기존 resourceId 보존
2. /api/dpm/unregister/<id>              → 등록 해제 (알람은 orphan 으로 살아남음)
3. /api/dpm/preregister                  → 재입력
4. /api/dpm/register (resourceId 명시)   → 같은 resourceId 로 → 알람 자동 reattach
```

### DB 영구 제거 (알람도 정리)
```
1. (사전) /api/alarm/alarm-definitions   → 해당 resourceId 의 알람 ID 수집
2. /api/dpm/unregister/<id>              → 등록 해제
3. /api/alarm/alarm-definition/delete    → orphan 알람 정리
```

---

## UI Fallback

> **전체구성 > 관리대상 > [DB 종류]** 메뉴에서 + **추가** → DB 타입 선택 → 폼 (host/port/db/user/passwd 등) → 저장. 또는 행 우클릭 → **삭제** 로 unregister.
