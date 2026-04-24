# Recipe: 관리대상 조회 (count + per-type list)

⚠️ **중요한 정정**: 초기 추론에서 `POST /api/cm/configuration/list` 가 전체 관리대상 목록 API 로 보였으나, 실제로는 **catch-all 핸들러가 항상 빈 `configItems:[]` 를 반환**하는 스텁이었음. 47개 관리대상이 등록된 상태에서도 empty 를 반환하는 것으로 확인됨. **이 경로는 사용하지 말 것.**

진짜 조회 엔드포인트는 **type-specific**:

| Type | Count 엔드포인트 | List 엔드포인트 | 확정 여부 |
|---|---|---|---|
| Web URL | `POST /api/weburl/count` | TBD | count ✅ / list ⏳ |
| 전체 | `POST /api/cm/portal/configuration/count` | TBD | ✅ |
| 서버 | `POST /api/sms/hosts/count` (추정) | TBD | ⏳ TBD |
| DB | `POST /api/dpm/count` (추정) | TBD | ⏳ TBD |
| APM / KCM / NMS | `POST /api/<type>/count` (추정) | TBD | ⏳ TBD |

- `/api/cm/portal/configuration/count` 는 **전역 총량** 반환 (type 필터 없음)
- `/api/weburl/count` 는 **WebURL 만** 카운트. 검증용으로 충분
- **세부 리스트** (각 항목의 id/name/속성 조회) 엔드포인트는 type 별 UI 목록 페이지에서 DevTools 녹화로 확정 필요 (TBD)

---

## 확정 레시피

### 전체 관리대상 수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/cm/portal/configuration/count"
# → {"success":true,"data":47,"errorCode":null,...}
```

### Web URL 수 (검증용)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count"
# → {"success":true,"data":<N>,"errorCode":null,...}
```

### 용도

`add-target.md` 의 2-step 흐름(save → register) 직후 검증:

```bash
# 등록 전
BEFORE=$(curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count" | jq -r .data)

# ... save + register 실행 ...

AFTER=$(curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count" | jq -r .data)

if [ "$AFTER" -gt "$BEFORE" ]; then
  echo "등록 확인됨 ($BEFORE → $AFTER)"
fi
```

---

## 세부 항목 리스트 (TBD)

각 type 의 **목록 페이지** 를 열 때 브라우저가 쏘는 API 가 진짜 list 엔드포인트임. 캡처 절차:

1. 크롬으로 `https://192.168.230.104/weburl` (Web URL 목록 페이지) 접속
2. DevTools **Network** 탭 > `Fetch/XHR` 필터
3. 페이지 로드 중에 뜨는 요청들 중 응답이 `configItems` 또는 `content` 배열을 포함하는 POST 식별
4. 해당 요청의 URL + body 를 이 recipe 에 업데이트

다른 리소스타입(서버/DB/APM 등) 목록 페이지에서도 동일 절차 반복.

## UI Fallback

> **전체구성 > 관리대상 > [리소스타입]** 메뉴로 이동하여 UI 목록 확인. 필요 시 우측 상단 검색·필터 사용.
