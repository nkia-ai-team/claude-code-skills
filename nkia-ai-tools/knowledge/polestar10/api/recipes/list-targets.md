# Recipe: 관리대상 목록 조회

- **엔드포인트**: `POST /api/cm/configuration/list`
- **인증 필요**: `recipes/login.md` 먼저 실행
- **부작용**: 없음 (read-only)

## 전제 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

## 레시피 — 전체 목록 (첫 페이지 50건)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"page":0,"size":50}' \
  "$POLESTAR10_BASE_URL/api/cm/configuration/list"
```

## 레시피 — 타입 필터

```bash
# 서버만
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"page":0,"size":50,"resourceType":"SERVER"}' \
  "$POLESTAR10_BASE_URL/api/cm/configuration/list"
```

지원 `resourceType` 값:

```
SERVER          # 서버
NMS             # 네트워크 (NMS)
APM             # 애플리케이션
KCM             # 쿠버네티스
WEBURL          # 웹 URL
ORACLE, CUBRID, POSTGRESQL, TIBERO, SQLSERVER, MYSQL, MARIADB  # DB 종별
LINKAGE_SYSTEM  # 연계 시스템
```

## 레시피 — id 필드만 추출 (jq)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"page":0,"size":200}' \
  "$POLESTAR10_BASE_URL/api/cm/configuration/list" \
  | jq -r '.data.configItems[] | .id'
```

## 성공 응답 스키마

```json
{
  "success": true,
  "data": {
    "configItems": [
      {
        "id": "<string>",
        "name": "<string>",
        "resourceType": "<string>",
        "...": "..."
      }
    ],
    "latestTimestamp": 1776929008123
  },
  "errorCode": null,
  "errorMsgArgs": null,
  "errorData": null
}
```

`configItems` 가 빈 배열 `[]` 이면 해당 필터에 매칭되는 관리대상 없음 (또는 전체 시스템에 등록된 대상 없음).

## 실패 응답

| 증상 | 원인 | 대응 |
|---|---|---|
| HTML 응답 (로그인 페이지) | 세션 만료 | `recipes/login.md` 재실행 |
| `success: false` + `errorCode: "PERMISSION_DENIED"` | 권한 부족 | 담당자 권한 확인 |
| Connection refused | polestar10-itg 컨테이너 다운 | `docker ps | grep polestar-app-itg` |

## 페이징

```bash
# page 는 0-based
PAGE=0
while true; do
  R=$(curl $POLESTAR10_CURL_OPTS -X POST \
    --cookie "$POLESTAR10_COOKIE_JAR" \
    -H 'Content-Type: application/json' \
    -d "$(jq -cn --argjson p $PAGE '{page:$p, size:50}')" \
    "$POLESTAR10_BASE_URL/api/cm/configuration/list")
  COUNT=$(echo "$R" | jq '.data.configItems | length')
  [ "$COUNT" = "0" ] && break
  echo "$R" | jq -r '.data.configItems[] | .id'
  PAGE=$((PAGE + 1))
done
```

## 참고 — 별칭 경로

Spring 핸들러가 다음 경로들을 동일 기능으로 매핑. `list` 가 canonical:

```
POST /api/cm/configuration/list        ← canonical
POST /api/cm/configuration/search
POST /api/cm/configuration/find-all
POST /api/cm/configuration/paging
POST /api/cm/configuration/list-paging
POST /api/cm/configuration/page
POST /api/cm/configuration/find
```

## UI Fallback

API 조회 실패 시:

> **전체구성 > 관리대상 > 전체** 메뉴에서 UI 로 목록 확인. 필요하면 우측 상단 검색·필터 사용.
