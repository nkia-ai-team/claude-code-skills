# Recipe: 관리대상 목록 / 상세 조회

타입별로 list-filter 엔드포인트가 분리되어 있고, 모두 **공통 페이징 스펙** 을 사용한다.

> ⚠️ **중요 정정**: 초기 추론에서 `POST /api/cm/configuration/list` 가 통합 list 라고 추정했으나 실제로는 **catch-all 스텁** (47개 등록된 상태에서도 빈 응답). 사용 금지.
> 진짜 list 는 모두 type-specific `*-filter` 엔드포인트.

## 공통 페이징 body 스펙

```json
{
  "pageNumber": 1,                         // 1-based
  "pagePerSize": 30,
  "gridFilters": [],                       // UI 그리드 필터 (보통 빈 배열)
  "sortFieldSets": [],                     // 정렬 필드 (빈 배열 = 기본)
  "tagFilters": ["confType = <type>"],     // 타입 필터 (필수에 가까움)
  "arguments": {}                          // 일부 엔드포인트만 사용
}
```

응답:
```json
{
  "success": true,
  "data": {
    "content": [...],
    "totalElements": <int>,
    "totalPages": <int>,
    "pageable": {...},
    "first": <bool>, "last": <bool>, "empty": <bool>
  }
}
```

---

## 확정 list 엔드포인트

| Type | URL | tagFilter | content[].id 형식 |
|---|---|---|---|
| Web URL | `POST /api/weburl/list-filter` | `confType = weburl` | `weburl_<bare>` (이미 prefix 됨) |
| 서버 | `POST /api/sms/hosts-filter` | `confType = server` | `resourceId` 필드, 형식 `MA_<hostname>_<timestamp>` |
| 전체 (모든 타입 합산 수) | `POST /api/cm/portal/configuration/count` | — | (count 만 반환) |

agent 기반 다른 타입(DB/APM/KCM/NMS) 은 `POST /api/<type>-filter` 또는 `/api/<type>/list-filter` 형태로 추정 — TBD

---

## 레시피

### 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

### Web URL 목록

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"tagFilters":["confType = weburl"]}' \
  "$POLESTAR10_BASE_URL/api/weburl/list-filter"
```

응답 `content[]` 항목 예:
```json
{
  "id": "weburl_xxxxxxxxxxxxxxxxxxxxxxxx",
  "resourceName": "네이버",
  "totalTimeMs": 378,
  "successCode": 200,
  "availability": "UP",
  "groupPath": "Default",
  "totalAvg": [{"timestamp": ..., "value": 269.5}, ...]
}
```

### Web URL 상세

```bash
WURL_ID="weburl_xxxxxxxxxxxxxxxxxxxxxxxx"  # list-filter 의 content[].id 값 그대로
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$WURL_ID" '{parameter:$id}')" \
  "$POLESTAR10_BASE_URL/api/weburl/detail"
```

응답 `data` 주요 필드:
```
id, resourceName, resourceType, confType, url, method, requestBody,
requestHeaders, connectTimeout, socketTimeout, useProxy, useSni,
sslVerify, successCode, statusCode, success (boolean), availability,
collectorPolicyTag, tags, alarmDefCount, measurementDefCount,
authorityInfos[], measurementLastUpdatedTime
```

### 서버 목록

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"tagFilters":["confType = server"],"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/sms/hosts-filter"
```

응답 `content[]` 항목 예:
```json
{
  "resourceId": "MA_<hostname>_<timestamp>",
  "hostname": "<hostname>",
  "ip": "<host-ip>",
  "os": "LINUX",
  "groupPath": "Default",
  "availabilityStatus": "UP",
  "managementStatus": "MANAGED",
  "cpuUtil": 13.77,
  "memUtil": 50.88,
  "diskIoRate": 2.27,
  "fileSystemUtil": 18.29,
  "trafficRx": 0,
  "trafficTx": 0.4,
  "instancePermission": 15
}
```

**⚠️ 중요**: 서버는 `id` 필드 없이 `resourceId` 사용. 형식 `MA_<hostname>_<timestamp>` — SMS 에이전트가 부여한 agent ID 와 동일. 다른 엔드포인트(delete, register 등)에서 그대로 사용.

### 전체 관리대상 수

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/cm/portal/configuration/count"
# → {"success":true,"data":<int>}
```

---

## Standby 조회 (관리대상 추가 다이얼로그용)

agent 기반 리소스 등록 전 단계. **에이전트가 heartbeat 보낸 호스트 중 아직 등록 안 된 것** 들 조회.

### Step 1 — 기본 standby 목록

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/sms/standby-hosts-filter-step1"
```

응답 (standby 에 호스트 있을 때):
```json
{
  "data": {
    "content": [{
      "agentId": "MA_<agent-host>",
      "hostname": "<agent-host>",
      "ipAddress": "<agent-host-ip>",
      "osType": "LINUX",
      "osVersion": "<os-version>",
      "vendor": "<vendor>",
      "agentVersion": "<agent-version>",
      "timestamp": 1777251718469,
      "hostStatus": "READY",                  // READY / ERROR
      "newHost": true,
      "managementStatus": "STANDBY",          // STANDBY 까지가 미등록
      "collectorPolicyTagValue": "defaultPolicy",
      "serviceGroupTagValue": null,
      "groupId": 1
    }],
    "totalElements": 1
  }
}
```

비어있을 때 `content:[]`, `totalElements:0`.

### Step 2 — 특정 agentId 들 상세 (선택용)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"pagePerSize":1000,"arguments":{"agentId":["MA_<agent-host>"]}}' \
  "$POLESTAR10_BASE_URL/api/sms/standby-hosts-filter-step2"
```

UI 가 다이얼로그에서 사용자가 항목 선택 시 호출. 특정 agentId 의 상세 정보 조회.

### Standby count (status 별)

```bash
# READY 상태 standby 수
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"parameter":"READY"}' \
  "$POLESTAR10_BASE_URL/api/sms/standby-hosts/count"
```

`parameter` 값: `"READY"` / `"ERROR"` 등.

### 서버 상세 — TBD

`/api/sms/hosts/detail`, `/api/sms/hosts/major-info`, `/api/sms/hosts/info` 모두 404. 서버 상세 페이지는 여러 measurement endpoint 를 조합해서 구성:
- `/api/measurement/availability/resource/latest`
- `/api/measurement/metric/aggregation/latest`
- `/api/alarm/resource/alarm-policy-summary`

상세 단일 엔드포인트가 필요하면 별도 캡처 필요.

---

## UI Fallback

API 조회 실패 시:

> **전체구성 > 관리대상 > [리소스타입]** 메뉴로 이동하여 UI 목록 확인. 검색·필터 사용.
