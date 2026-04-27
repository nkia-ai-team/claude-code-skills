# Recipe: 관리대상 삭제

타입별 delete 엔드포인트는 분리되어 있고, **identifier 형식이 type 별로 다름**:

```
POST /api/<type>/delete
body: {"parameter": [<id1>, <id2>, ...]}
```

식별자 형식:

| Type | identifier 형식 | 출처 |
|---|---|---|
| Web URL | `weburl_<bare-mongo-id>` | save 응답 `data.id` 에 prefix 붙여 사용. list-filter `content[].id` 도 이미 prefix 붙은 형태 |
| **서버** | **`MA_<hostname>_<timestamp>`** (그대로) | hosts-filter `content[].resourceId` 또는 SMS 에이전트 자체의 agent ID. **추가 prefix 없음** |
| (다른 타입) | TBD | 캡처 후 확정 |

→ **모든 type 이 `<type>_<id>` 패턴은 아님** — agent-based 는 agent ID 자체를 사용.

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
TARGET_ID="weburl_69eaea2d3c0ebbe080eb999c"   # list-filter 의 content[].id 또는 weburl_<save-data-id>

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$TARGET_ID" '{parameter:[$id]}')" \
  "$POLESTAR10_BASE_URL/api/weburl/delete"
# → {"success":true,"data":"ok"}
```

### 서버 삭제

```bash
RESOURCE_ID="MA_ubuntu2204-230-104_20240523075040"   # hosts-filter 의 content[].resourceId

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

> ⚠️ **에이전트 기반 리소스 삭제 부작용**: SMS 에이전트가 여전히 살아있으면 다음 heartbeat 사이클에 자동으로 standby 에 다시 떠올라옴. 영구 제거하려면 **에이전트 자체를 stop / 제거** 도 같이 해야 함. 이 동작은 NKIAAI-539 검증 세션에서 직접 관찰됨 (109 server 삭제 → 5분 후 standby 재출현).

---

## UI Fallback

> **전체구성 > 관리대상 > [리소스타입]** → 행 체크박스 → 상단 **삭제** → 확인.
