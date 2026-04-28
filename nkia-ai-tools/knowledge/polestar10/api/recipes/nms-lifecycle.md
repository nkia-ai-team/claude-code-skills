# Recipe: NMS (Network Monitoring System) 라이프사이클

NMS 는 polestar10 에서 SNMP 기반 네트워크 장비 (라우터/스위치) 모니터링. **agent heartbeat 모델 아님** — polestar10 가 SNMP polling 으로 직접 수집. 따라서 등록 모델은 **DPM 과 유사한 사용자 입력 흐름**:

```
Step 1: POST /api/nms/v1/pre/addResource     ← SNMP 정보 입력 + polestar10 가 SNMP 쿼리로 검증
        (응답에서 systemName/description/resourceId 자동 추출)
Step 2: POST /api/nms/v1/addResource         ← pre 결과 + 사용자 선택 (그룹/정책/태그)
Step 3: POST /api/nms/v1/deleteResource/<id> ← 삭제 (path 에 ID, body 없음)
```

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## 등록된 NMS 목록

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"pagePerSize":30,"sortFieldSets":[{"index":0,"sortDirection":"ASC","fieldName":"systemName"}],"tagFilters":["confType = network"],"gridFilters":[],"timeFilter":{"mode":"LIVE","startTime":0,"endTime":0},"arguments":null}' \
  "$POLESTAR10_BASE_URL/api/nms/v1/list"
```

응답 `content[]` 핵심:
- `resourceId` (24-hex Mongo ID)
- `systemName`, `ipAddress`, `vendor`, `model`
- `snmpVersion`, `serialNumber`, `osVersion`
- `status`, `managementStatus`
- `cpuUtilization`, `memoryUtilization`

---

## Pre-list (SNMP 검증 staging)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30}' \
  "$POLESTAR10_BASE_URL/api/nms/v1/pre/list"
```

> 자동 채워지지 않음 — 사용자가 `pre/addResource` 명시적으로 호출해야 채워짐.

---

## 등록 (3-step)

### Step 1 — SNMP 정보 검증 (`POST /api/nms/v1/pre/addResource`)

```bash
TARGET_IP="<snmp-target-ip>"          # 예: 192.168.x.y
TARGET_PORT=161
SNMP_VERSION="v2c"
SNMP_COMMUNITY="public"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg host "$TARGET_IP" --argjson port "$TARGET_PORT" \
      --arg ver "$SNMP_VERSION" --arg comm "$SNMP_COMMUNITY" \
      '{
        collectType: "snmp",
        snmpVersion: $ver, host: $host, port: $port, community: $comm,
        usmUser: "", secureLevel: "", authAlg: "", authPass: "",
        privacyAlg: "", privacyPass: "", contextName: "",
        backupConnectType: "ssh", connectPort: 0,
        userName: "", password: "", enablePassword: "",
        osVersion: "", connectConfigSysObjectID: "",
        discoverInterfaceList: []
      }')" \
  "$POLESTAR10_BASE_URL/api/nms/v1/pre/addResource"
# → {"success":true,"data":true}     ← SNMP 검증 OK
# 또는 {"success":false,"errorCode":"...","errorMsgArgs":[...]} ← community/IP 잘못
```

성공 시 polestar10 가 내부적으로 SNMP 쿼리해서 systemName/description/sysObjectID 등을 staging 에 캐시. 다음 단계 `addResource` 호출 시 이 데이터를 사용함.

### Step 2 — staging 항목 확인 (resourceId 추출)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30}' \
  "$POLESTAR10_BASE_URL/api/nms/v1/pre/list" \
  | jq '.data.content[] | {resourceId, systemName, ipAddress, description}'
```

SNMP 응답으로 채워진 staging 항목에서 `resourceId` 추출.

### Step 3 — 정식 등록 (`POST /api/nms/v1/addResource`)

```bash
RESOURCE_ID="<from staging>"
SYSTEM_NAME="<from staging — SNMP sysName>"
DESCRIPTION="<from staging — SNMP sysDescr>"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg host "$TARGET_IP" --argjson port "$TARGET_PORT" \
      --arg ver "$SNMP_VERSION" --arg comm "$SNMP_COMMUNITY" \
      --arg sname "$SYSTEM_NAME" --arg desc "$DESCRIPTION" \
      --arg rid "$RESOURCE_ID" --arg sg "RCA-Testbed" \
      '{
        host: $host, port: $port, snmpVersion: $ver, community: $comm,
        systemName: $sname, description: $desc,
        resourceId: $rid, resourceType: "network.Network",
        collectType: "SNMP",
        secureLevel: "authPriv", authAlg: "MD5", privacyAlg: "DES",
        backupConnectType: "SSH", connectPort: 0,
        userName: "", connectConfigSysObjectID: "", osVersion: "",
        managementStatus: "MANAGED",
        groupId: 1,
        serviceGroupTagValue: $sg,
        anomalyPolicyTagValue: "성능 이상감지 기본 정책",
        collectorPolicyTagValue: "defaultPolicy",
        alarmPolicyTagValue: null,
        searchTime: (now | floor * 1000),
        alarmDefCount: 0, measurementDefCount: 0,
        measurementInterval: 60, configInterval: 3600,
        discoverInterfaceList: []
      }')" \
  "$POLESTAR10_BASE_URL/api/nms/v1/addResource"
```

응답: 등록된 전체 NMS 정보 + `resourceId`.

> **주의**: `collectType` 이 pre 단계는 `"snmp"` (소문자), addResource 단계는 `"SNMP"` (대문자). polestar10 의 명명 비일관성.

---

## 검증

```bash
# count 증가 확인
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"pagePerSize":5,"sortFieldSets":[],"tagFilters":["confType = network"],"gridFilters":[],"timeFilter":{"mode":"LIVE","startTime":0,"endTime":0},"arguments":null}' \
  "$POLESTAR10_BASE_URL/api/nms/v1/list" \
  | jq '.data.totalElements'
```

---

## 삭제

```bash
RESOURCE_ID="<24-hex-resource-id>"    # nms/v1/list 의 content[].resourceId

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  "$POLESTAR10_BASE_URL/api/nms/v1/deleteResource/$RESOURCE_ID"
# → {"success":true,"data":true}
```

> POST method 이지만 body 없음. URL path 에 resourceId.

---

## 부가: 메트릭 / 시스템 정보

```bash
RID="<resourceId>"

# NMS 전용 메트릭 catalog
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  "$POLESTAR10_BASE_URL/api/nms/v1/measurement/definitions/resourcetype/network.Network/metric"

# 시스템 상세
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d "{}" \
  "$POLESTAR10_BASE_URL/api/nms/v1/system/$RID"

# 인터페이스 list
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d "{}" \
  "$POLESTAR10_BASE_URL/api/nms/v1/system/interface/$RID"

# CPU / 메모리 등
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d "{}" \
  "$POLESTAR10_BASE_URL/api/nms/v1/cpu/list"
```

응답 사용 가능 resourceType:
- `network.Network` (장비 자체)
- `network.Cpus`, `network.Memorys`
- `network.Interface`
- `network.Storages`

---

## 흐름 요약 (오케스트레이터 관점)

### 신규 NMS 등록 (인터뷰 흐름)
```
1. 사용자 입력: IP, port (보통 161), SNMP version, community
2. /api/nms/v1/pre/addResource          → polestar10 가 SNMP 쿼리로 검증
3. (실패 시) errorCode 사용자에게 표시 → community 재입력
4. /api/nms/v1/pre/list                 → resourceId / systemName / description 추출
5. (사용자 선택) 그룹, 서비스 그룹, 이상감지 정책
6. /api/nms/v1/addResource              → 정식 등록
7. (검증) /api/nms/v1/list              → totalElements 증가 확인
```

### NMS 영구 제거
```
1. /api/nms/v1/deleteResource/<id>      → 삭제
2. (필요 시) /api/alarm/alarm-definitions 에서 orphan alarm 정리
```

---

## UI Fallback

> **전체구성 > 관리대상 > 네트워크** 메뉴 → 우측 상단 **+ 추가** → **+ 등록** 버튼 → SNMP 정보 폼 (IP, community, version) → **확인** (SNMP 검증) → 그룹/정책 선택 → **저장**.
