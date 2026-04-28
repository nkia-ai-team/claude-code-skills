# Recipe: 관리대상 추가 (2-step: staging → register)

polestar10 의 모든 관리대상 등록은 **staging → register** 2단계.
1단계에서 staging 에 항목이 들어가는 방식이 리소스 모델별로 다르고, 2단계 register 는 동일 패턴.

```
┌─ Config-only (Web URL, SLO, Syslog 등) ─┐
│  Step 1: POST /api/<type>/save           │  사용자가 UI + 버튼으로 직접 추가
│         → staging id 반환                │
└──────────────────────────────────────────┘
                                            ┌─ Step 2 (공통) ─────────────────────────┐
                                            │  POST /api/<type-specific>/register     │
                                            │  body = ARRAY [{ id_or_agentId, ... }]  │
                                            │  group/policy/tag 바인딩 + 관리대상 승격 │
                                            └─────────────────────────────────────────┘
┌─ Agent-based (서버, DB, APM, KCM, NMS) ─┐
│  Step 1: 에이전트 설치 + heartbeat       │  자동 — save 호출 없음
│         → standby 자동 등록              │  /api/<type>/standby-* 로 조회 가능
└──────────────────────────────────────────┘
```

---

## 리소스 타입별 레시피 현황

| Type | 모델 | staging 진입 | register | 상태 |
|---|---|---|---|---|
| Web URL | config-only | `/api/weburl/save` | `/api/weburl/register` | |
| 서버 (SMS) | agent-based | heartbeat 자동 → standby | `/api/sms/standby-hosts/register` | |
| **데이터베이스 (DPM)** | **DB-direct** | `/api/dpm/preregister` | `/api/dpm/register` 단일 호출 | [dpm-lifecycle.md](dpm-lifecycle.md) |
| **애플리케이션 (APM/WPM)** | agent-based | heartbeat → `/api/apm/standby-agents-filter-step1` | `/api/apm/standby-agent/register` | |
| **쿠버네티스 (KCM)** | agent-based | heartbeat → `/api/kcm/standby-clusters-filter-step1` | `/api/kcm/standby-clusters/register` | |
| **NMS 네트워크** | **SNMP-polling** (사용자 입력 모델) | `/api/nms/v1/pre/addResource` (SNMP 검증) | `/api/nms/v1/addResource` (단일 객체) | [nms-lifecycle.md](nms-lifecycle.md) |
| 사용자정의 (SLO/Syslog/SQL/SNMP OID) | config-only | `/api/<type>/save` 추정 | `/api/<type>/register` 추정 | SLO [slo.md](slo.md), 나머지 TBD |

### 모델 별 register body 비교

```bash
# Web URL (config-only)
[{ id, dataPolicy, tag, anomalyPolicyTagValue, groupId }]

# SMS server (agent-based)
[{ agentId, managementStatus, collectorPolicyTagValue, serviceGroupTagValue, anomalyPolicyTagValue, groupId }]

# DPM (DB-direct, 단일 객체)
{ resourceType, hostName, port, dbName, userName, passwd, resourceId, managementStatus, ... }

# APM (agent-based, agent 단위 array)
[{ serviceName, agentId, resourceId, collectorPolicyTagValue, anomalyPolicyTagValue, serviceGroupTagValue, managementStatus, category:"APM"|"WPM", groupId }]

# KCM (agent-based, cluster 단위)
[{ clusterId, collectorPolicyTagValue, serviceGroupTagValue, managementStatus, anomalyPolicyTagValue, groupId }]
```

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## 확정 레시피 1: Web URL 등록 (config-only)

### Step 1 — staging 추가 (`POST /api/weburl/save`)

```bash
TARGET_NAME="testbed-probe-$(date +%s)"
TARGET_URL="${POLESTAR10_BASE_URL}/"     # 또는 외부 URL

SAVE=$(curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg name "$TARGET_NAME" --arg url "$TARGET_URL" \
      '{name:$name, description:"", method:"GET", requestBodyType:"form_data",
        url:$url, connectTimeout:10, socketTimeout:10,
        useProxy:false, useSni:false, sslVerify:false, successCode:200}')" \
  "$POLESTAR10_BASE_URL/api/weburl/save")

NEW_ID=$(echo "$SAVE" | jq -r '.data.id')
echo "staging OK → id=$NEW_ID, registered=$(echo "$SAVE" | jq -r '.data.registered')"
```

### Step 2 — 등록 (`POST /api/weburl/register`)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$NEW_ID" \
      '[{id:$id, dataPolicy:"defaultPolicy", tag:null,
         anomalyPolicyTagValue:null, groupId:1}]')" \
  "$POLESTAR10_BASE_URL/api/weburl/register"
# → {"success":true,"data":null}
```

### Step 3 — 검증

```bash
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count"
```

---

## 확정 레시피 2: 서버 등록 (agent-based)

**선행 조건**: 타겟 서버에 SMS 에이전트가 설치되어 polestar10-itg 의 collector 로 heartbeat 보내고 있어야 함. `hostStatus:"READY"` 가 standby 에 떠야 등록 가능.

### Step 1 — standby 에 떠있는지 확인

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/sms/standby-hosts-filter-step1" \
  | jq '.data.content[] | {agentId, hostname, ipAddress, hostStatus}'
```

원하는 호스트가 보이고 `hostStatus:"READY"` 면 다음 단계로. 안 보이면 에이전트 heartbeat 대기 (5~10분).

### Step 2 — 등록 (`POST /api/sms/standby-hosts/register`)

```bash
AGENT_ID="MA_<agent-host>"       # standby 응답의 agentId 그대로
SVC_GROUP="RCA-Testbed"          # tag 시스템의 serviceGroup value (없으면 자동 생성)
GROUP_ID=1                       # 1 = Default 시스템 그룹 (list-groups.md 참조)

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg aid "$AGENT_ID" --arg sg "$SVC_GROUP" --argjson gid "$GROUP_ID" \
      '[{
        agentId: $aid,
        managementStatus: "MANAGED",
        collectorPolicyTagValue: "defaultPolicy",
        serviceGroupTagValue: $sg,
        anomalyPolicyTagValue: "성능 이상감지 기본 정책",
        groupId: $gid
      }]')" \
  "$POLESTAR10_BASE_URL/api/sms/standby-hosts/register"
# → {"success":true,"data":{"failedCount":0,"successCount":1}}
```

**body 필드 의미** (Web URL register 와 비교):

| 필드 | Web URL register | 서버 register | 비고 |
|---|---|---|---|
| 식별자 | `id` (staging id) | `agentId` (SMS 에이전트 ID) | **필드명 다름** |
| 데이터 정책 | `dataPolicy:"defaultPolicy"` | `collectorPolicyTagValue:"defaultPolicy"` | **필드명 다름**, 값 동일 |
| 서비스 그룹 | `tag` | `serviceGroupTagValue` | **필드명 다름** |
| 이상감지 정책 | `anomalyPolicyTagValue` | `anomalyPolicyTagValue` | 동일 |
| 시스템 그룹 ID | `groupId` | `groupId` | 동일 |
| 관리 상태 | (없음) | `managementStatus:"MANAGED"` | 서버 전용 |

→ **register payload 가 type 별로 살짝 다름** — 통합 추상화 시 주의.

### Step 3 — 검증

```bash
# 등록된 서버 목록에 떴는지 확인
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"tagFilters":["confType = server"],"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/sms/hosts-filter" \
  | jq --arg aid "$AGENT_ID" '.data.content[] | select(.resourceId == $aid)'
```

---

## 확정 레시피 3: KCM 클러스터 등록 (agent-based)

### Step 1 — standby 확인

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30}' \
  "$POLESTAR10_BASE_URL/api/kcm/standby-clusters-filter-step1"
```

응답 `content[]`: `clusterId` (= resourceId), `clusterName`, `clusterVersion`, `agentVersion`, `registeredStatus:"READY"`

### Step 2 — 등록

```bash
CLUSTER_ID="cluster-<uuid>"   # standby 응답에서 추출

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg cid "$CLUSTER_ID" \
      '[{
        clusterId: $cid,
        managementStatus: "MANAGED",
        collectorPolicyTagValue: "defaultPolicy",
        serviceGroupTagValue: "RCA-Testbed",
        anomalyPolicyTagValue: "성능 이상감지 기본 정책",
        groupId: 1
      }]')" \
  "$POLESTAR10_BASE_URL/api/kcm/standby-clusters/register"
# → {"success":true,"data":{"registrationSucceedClusters":["..."],"registrationFailedClusters":[]}}
```

### Unregister

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg cid "$CLUSTER_ID" '{clusterId:$cid}')" \
  "$POLESTAR10_BASE_URL/api/kcm/standby-clusters/unregister"
# → {"success":true,"data":{"clusterName":"...","ipAddress":null,"agentVersion":"..."}}
```

> KCM unregister 는 SMS hosts/delete 와 다른 패턴: body 가 `{clusterId:"..."}` 단일 객체.

---

## 확정 레시피 4: APM 애플리케이션 등록 (agent-based, service+agent 2-level)

> APM 은 다른 type 과 한 가지 다름: **service 단위로 다수 agent 가 묶여 등록**.
> 한 service (예: plopvape-shop) 안에 여러 agent (각 인스턴스/Pod) 가 있고, register 시 array body 로 모든 agent 동시 등록.

### Step 1 — standby 확인

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/apm/standby-agents-filter-step1"
```

응답 `content[]` 핵심:
- `serviceName` (예: `"plopvape-shop"`)
- `agentId` (예: `"plopvape-inventory"`)
- `resourceId` (numeric 문자열)
- `confId` (예: `"261692996_apm.Agent"`)
- `category` (`"APM"` 또는 `"WPM"`)
- `agentTarget`, `agentVersion`, `langVersion` 등

### Step 2 — 등록 (한 service 의 모든 agent 일괄)

```bash
# standby 응답에서 같은 serviceName 의 agent 들을 모은 array 로 register
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '[
    {
      "serviceName": "plopvape-shop",
      "agentId": "plopvape-inventory",
      "resourceId": "<resourceId from standby>",
      "category": "APM",
      "managementStatus": "MANAGED",
      "collectorPolicyTagValue": "defaultPolicy",
      "anomalyPolicyTagValue": "성능 이상감지 기본 정책",
      "serviceGroupTagValue": "RCA-Testbed",
      "groupId": 1
    },
    { "serviceName": "plopvape-shop", "agentId": "plopvape-order", ... },
    { "serviceName": "plopvape-shop", "agentId": "plopvape-payment", ... }
  ]' \
  "$POLESTAR10_BASE_URL/api/apm/standby-agent/register"
# → {"success":true,"data":{"failedList":[]}}
```

### Unregister (service 단위)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '[{"serviceId":"plopvape-shop","category":"APM"}]' \
  "$POLESTAR10_BASE_URL/api/apm/unregisterservice"
# → {"success":true,"data":{"failedList":[]}}
```

> APM unregister 는 service ID 로 하나의 호출 — 그 service 의 모든 agent 가 함께 제거됨. unregister 후 같은 service 가 standby 에 다시 떠올라옴 (PostgreSQL 과 동일한 orphan + auto-reattach 패턴 추정).

> URL 명명이 일관성 없음: register 는 `standby-agent/register` (단수), unregister 는 `unregisterservice` (단어 전체 한 단어).

---

## 다른 agent-based 타입 (남은 — NMS)

NMS 는 **SNMP polling 모델 — agent heartbeat 가 없음**. 따라서 standby 가 자동으로 채워지지 않음. 사용자가 SNMP 정보 (IP, community, version) 를 직접 입력해서 등록. register endpoint 는 캡처 진행 중 (별도 캡처 세션 필요).

---

## UI Fallback

2-step 어느 단계든 실패 시:

> **전체구성 > 관리대상** → 우측 상단 **+ 추가** → (리소스타입 선택) → 폼/standby 선택 → 저장. **관리대상 추가** 목록에서 항목 체크 → **관리대상 등록** 버튼 → 그룹/이상감지 정책/서비스그룹 지정 → 저장.
