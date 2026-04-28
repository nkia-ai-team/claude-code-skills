# Recipe: 관리대상 삭제

타입별 delete 엔드포인트는 분리되어 있고, **identifier 형식이 type 별로 다름**:

```
POST /api/<type>/delete
body: {"parameter": [<id1>, <id2>, ...]}
```

식별자 형식:

| Type | URL | Method | identifier 형식 / body | 비고 |
|---|---|---|---|---|
| Web URL | `/api/weburl/delete` | POST | `{parameter:["weburl_<id>"]}` | save 응답 `data.id` 에 prefix |
| 서버 (SMS) | `/api/sms/hosts/delete` | POST | `{parameter:["MA_<hostname>_<timestamp>"]}` | hosts-filter `content[].resourceId` 그대로 |
| **DPM (DB)** | **`/api/dpm/unregister/<resourceId>`** | **GET** | path 에 ID, body 없음 | [dpm-lifecycle.md](dpm-lifecycle.md) |
| **APM** | `/api/apm/unregisterservice` | POST | `[{serviceId:"...", category:"APM"|"WPM"}]` (array) | service 단위 (모든 agent 동시 제거) |
| **KCM** | `/api/kcm/standby-clusters/unregister` | POST | `{clusterId:"..."}` (단일 객체) | clusterId 사용 |
| **NMS** | `/api/nms/v1/deleteResource/<resourceId>` | POST | (none, path 에 ID) | DPM 비슷 — body 없음 |
| (다른 사용자정의 타입) | TBD | TBD | TBD | 추후 캡처 |

→ **type 별 패턴 다름** — generic prefix rule 없음. recipe 별로 각자 확인.

> **알람 cascade rule**:
> - DPM `unregister` 후 알람 정의는 **삭제되지 않고 orphan 으로 남음** (resourceId 만 끊김)
> - 같은 `resourceId` 로 재등록 시 알람 자동 reattach
> - 다른 `resourceId` 로 등록 시 alarm 영구 orphan
> - 다른 type 의 cascade 동작은 미검증 (TBD)

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## 확정 레시피

### Web URL 삭제

```bash
TARGET_ID="weburl_xxxxxxxxxxxxxxxxxxxxxxxx"   # list-filter 의 content[].id 또는 weburl_<save-data-id>

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$TARGET_ID" '{parameter:[$id]}')" \
  "$POLESTAR10_BASE_URL/api/weburl/delete"
# → {"success":true,"data":"ok"}
```

### 서버 삭제

```bash
RESOURCE_ID="MA_<hostname>_<timestamp>"   # hosts-filter 의 content[].resourceId

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg rid "$RESOURCE_ID" '{parameter:[$rid]}')" \
  "$POLESTAR10_BASE_URL/api/sms/hosts/delete"
# → {"success":true,"data":"ok"}
```

### 다중 항목 일괄 삭제

```bash
# Web URL 여러 개
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"parameter":["weburl_id1","weburl_id2"]}' \
  "$POLESTAR10_BASE_URL/api/weburl/delete"

# 서버 여러 개
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"parameter":["MA_host1_..","MA_host2_.."]}' \
  "$POLESTAR10_BASE_URL/api/sms/hosts/delete"
```

---

## 검증

### Web URL

```bash
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count"
# 삭제 전후 data 값 비교
```

### 서버

```bash
# 삭제된 서버의 resourceId 가 hosts-filter 결과에 없는지 확인
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":100,"tagFilters":["confType = server"],"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/sms/hosts-filter" \
  | jq --arg rid "$RESOURCE_ID" '.data.content | map(select(.resourceId == $rid)) | length'
# → 0 이면 삭제 확인
```

> ⚠️ **에이전트 기반 리소스 삭제 부작용**: SMS 에이전트가 여전히 살아있으면 다음 heartbeat 사이클에 자동으로 standby 에 다시 떠올라옴. 영구 제거하려면 **에이전트 자체를 stop / 제거** 도 같이 해야 함. 에이전트가 살아있는 한 unregister 후에도 다음 heartbeat 사이클에 standby 로 자동 재진입.

---

## UI Fallback

> **전체구성 > 관리대상 > [리소스타입]** → 행 체크박스 → 상단 **삭제** → 확인.
