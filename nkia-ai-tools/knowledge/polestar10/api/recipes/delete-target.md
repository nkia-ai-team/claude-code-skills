# Recipe: 관리대상 삭제

polestar10 의 삭제 엔드포인트는 **type-specific prefix** 를 사용:

```
POST /api/<type>/delete
body: {"parameter": ["<type>_<id>", ...]}
```

예: WebURL id `69eacd...995` 를 삭제하려면 `weburl_69eacd...995` 를 배열에 담아 POST.

## 리소스 타입별 현황

| Type | 경로 | parameter prefix | 확정 여부 |
|---|---|---|---|
| Web URL | `POST /api/weburl/delete` | `weburl_` | ✅ (아래 레시피) |
| 서버 | `POST /api/sms/hosts/delete` (추정) | `server_` (추정) | ⏳ TBD |
| DB | `POST /api/dpm/delete` (추정) | `database_` (추정) | ⏳ TBD |
| APM | `POST /api/apm/delete` (추정) | `apm_` (추정) | ⏳ TBD |
| KCM | `POST /api/kcm/delete` (추정) | `kcm_` (추정) | ⏳ TBD |
| NMS | `POST /api/nms/delete` (추정) | `nms_` (추정) | ⏳ TBD |

---

## 확정 레시피: Web URL 삭제

### 전제 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

### 단일 항목 삭제

```bash
TARGET_ID="<staging id from add-target save step>"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg pid "weburl_${TARGET_ID}" '{parameter:[$pid]}')" \
  "$POLESTAR10_BASE_URL/api/weburl/delete"
# → {"success":true,"data":"ok","errorCode":null,...}
```

### 다중 항목 일괄 삭제

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"parameter":["weburl_69eacd...995","weburl_69ead6...998"]}' \
  "$POLESTAR10_BASE_URL/api/weburl/delete"
```

### 검증

```bash
# 삭제 전후 count 비교
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count"
```

---

## 응답 스키마

성공:
```json
{"success": true, "data": "ok", "errorCode": null, "errorMsgArgs": null, "errorData": null}
```

실패 (예: 존재하지 않는 id):
```json
{"success": false, "data": null, "errorCode": "POLESTAR_XXXXX", "errorMsgArgs": [...], "errorData": null}
```

## 전체 라이프사이클 (참고)

```bash
# 1. 로그인 (recipes/login.md)
# 2. 등록 (recipes/add-target.md Web URL 레시피 — save → register)
# 3. 검증: /api/weburl/count 가 1 증가
# 4. 삭제: 위 레시피
# 5. 재검증: /api/weburl/count 가 원래대로 돌아왔는지
```

## UI Fallback

API 삭제 실패 시:

> **전체구성 > 관리대상 > Web URL** (또는 해당 리소스타입) 목록에서 행 체크박스 선택 → 상단 **삭제** 버튼 → 확인.
