# Recipe: 리소스 그룹 조회

- **엔드포인트**: `POST /api/cm/groups/list`
- **인증 필요**: `recipes/login.md` 먼저 실행
- **부작용**: 없음 (read-only)

## 전제 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

## 레시피

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/cm/groups/list"
```

## 레시피 — 그룹명만 뽑기

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/cm/groups/list" \
  | jq -r '.data[] | .name'
```

## 성공 응답 예

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Default",
      "description": "기본 그룹",
      "groupType": "..."
    },
    {
      "id": 2,
      "name": "Root",
      "description": "...",
      "groupType": "..."
    }
  ],
  "errorCode": null
}
```

## 참고 — 관련 엔드포인트

| 엔드포인트 | 용도 |
|---|---|
| `POST /api/cm/groups/list` | flat 리스트 (이 recipe) |
| `POST /api/cm/groups/tree` | 트리 구조 — 중첩 그룹 계층 포함 |

트리 조회가 필요하면 `/tree` 로 대체하면 됨 (같은 body).

## UI Fallback

> **전체구성 > 관리대상** 메뉴 진입 후 좌측 그룹 트리 패널에서 확인.
