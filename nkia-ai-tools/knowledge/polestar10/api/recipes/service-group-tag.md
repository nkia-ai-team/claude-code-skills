# Recipe: 서비스 그룹 (tag system)

polestar10 의 **서비스 그룹** 은 별도 entity 가 아니라 **tag 시스템의 `serviceGroup` key** 로 구현되어 있음.

> **주의 - 두 가지 그룹 개념을 혼동 금지**:
>
> | 개념 | API | 용도 | 식별 |
> |---|---|---|---|
> | **시스템 그룹** | `/api/cm/groups/list` | 구조적 그룹, 고정 (Default=1, Root=0) | `groupId` (정수) |
> | **서비스 그룹** | `/api/cm/tag/value/insert` (tagKey="serviceGroup") | 사용자 정의 분류 | `tagValue` (문자열) |
>
> register 페이로드의 `groupId` = 시스템 그룹, `tag`/`serviceGroupTagValue` = 서비스 그룹.

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## 서비스 그룹 생성

```bash
SVC_GROUP="RCA-Testbed"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg v "$SVC_GROUP" '{parameter:{tagKey:"serviceGroup", tagValue:$v}}')" \
  "$POLESTAR10_BASE_URL/api/cm/tag/value/insert"
```

응답:
```json
{
  "success": true,
  "data": {
    "key": "serviceGroup",
    "tagDataType": "STRING",
    "tagType": "CUSTOM",
    "values": ["<existing-value-1>", "<existing-value-2>", ...]   // 이미 사용 중인 값 목록
  },
  "errorCode": null
}
```

> **참고**: 응답의 `values` 배열은 **현재 어떤 리소스에 link 된** tag value 만 포함. 방금 insert 했더라도 아직 어떤 리소스에도 사용 안 됐으면 `values` 에 안 보일 수 있음. 등록 후 어떤 관리대상의 `serviceGroupTagValue` 로 사용되면 `values` 에 등장.

> **자동 생성**: 서버/Web URL register 시 `serviceGroupTagValue` 또는 `tag` 필드에 새 값 넣으면 자동으로 tag value 가 생성됨. 사전 insert 없이도 동작. insert 는 UI 에서 미리 dropdown 옵션으로 보이게 하기 위한 절차.

## 서비스 그룹 삭제

> ⚠️ **delete 는 path 가 비대칭** (`/value/insert` vs `/link/delete/value`)

```bash
SVC_GROUP="RCA-Testbed"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg v "$SVC_GROUP" \
      '[{currentTagKey:"serviceGroup", currentTagValue:$v}]')" \
  "$POLESTAR10_BASE_URL/api/cm/tag/link/delete/value"
# → {"success":true,"data":null}
```

`currentTagKey/currentTagValue` 라는 prefix 가 있는 것은 **rename 변형도 존재할 가능성** 시사 (`newTagKey/newTagValue` 추정).

## 다중 삭제

```bash
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '[
    {"currentTagKey":"serviceGroup","currentTagValue":"group-A"},
    {"currentTagKey":"serviceGroup","currentTagValue":"group-B"}
  ]' \
  "$POLESTAR10_BASE_URL/api/cm/tag/link/delete/value"
```

## tag schema 조회 (참고용)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/cm/tag/key/list" \
  | jq '.data[] | select(.tagType=="CUSTOM") | {key, tagType, tagDataType}'
```

CUSTOM tag key 목록 (사용자 정의 가능):
- `serviceGroup` — 서비스 그룹
- `logType` — 로그 타입 분류

다른 모든 key 는 `tagType:"SYSTEM"` (시스템이 자동 부여, 사용자 수정 불가).

---

## 자원 → 그룹 link 변경 (기존 자원의 서비스 그룹 갱신)

기존 등록된 자원의 `serviceGroup` 태그값을 다른 값으로 바꿀 때. 같은 endpoint 가 **신규 link / 기존 link 갱신 모두** 수행 (upsert).

```bash
CONF_ID="-395796245_mysql.MySQL"   # 자원의 confId (resourceId + "_" + resourceType)
NEW_GROUP="social-feed"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg c "$CONF_ID" --arg v "$NEW_GROUP" \
        '{confId:$c, tagType:"CUSTOM", key:"serviceGroup", value:$v, tagDataType:"STRING"}')" \
  "$POLESTAR10_BASE_URL/api/cm/tag/resource/insert"
```

> **body 핵심**: `confId` (path 아님 body), `tagType:"CUSTOM"`, `key`/`value` (tagKey/tagValue 아님), `tagDataType:"STRING"` 5개 모두 필수. parameter wrapping 없음. 누락 시 `POLESTAR_00004`.

응답 (성공):
```json
{
  "success": true,
  "data": {
    "id": "-395796245_mysql.MySQL",
    "tags": [ ... 갱신된 tag 목록 ..., {"key":"serviceGroup","value":"social-feed","tagType":"CUSTOM"} ],
    "managementStatus": "MANAGED",
    ...
  }
}
```

검증:
```bash
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  "$POLESTAR10_BASE_URL/api/cm/tag/resource/select/$CONF_ID" \
  | jq '.data[] | select(.key=="serviceGroup")'
```

> **CUSTOM tag 일반 변경 패턴**: 같은 endpoint 로 다른 CUSTOM key (`logType` 등) 도 갱신 가능. `tagType:"SYSTEM"` 으로는 거부됨.

> **confId 형식**: 자원 타입별 prefix 가 다름.
> - DPM: `<resourceId>_<dbType>.<DBType>` (예: `-395796245_mysql.MySQL`)
> - 서버: `MA_<host>_<ts>_server.Server`
> - APM: `<resourceId>_apm.Agent`
> - Web URL: `weburl_<id>` (자체가 이미 confId 형태)
>
> list-filter 응답의 `confId` 또는 `id` 필드 또는 `tag/resource/select` 응답의 `confId` tag 값에서 추출.

---

## 사용 흐름 — 테스트베드 시나리오

```bash
# 1. 테스트베드용 서비스 그룹 생성
curl ... /api/cm/tag/value/insert  -d '{"parameter":{"tagKey":"serviceGroup","tagValue":"RCA-Testbed"}}'

# 2. (각 관리대상 등록 시) register 페이로드의 tag/serviceGroupTagValue 에 "RCA-Testbed" 사용
curl ... /api/sms/standby-hosts/register \
  -d '[{"agentId":"...","serviceGroupTagValue":"RCA-Testbed",...}]'

# 3. 테스트베드 정리 시 — 관리대상 모두 삭제 후 그룹도 정리
curl ... /api/cm/tag/link/delete/value -d '[{"currentTagKey":"serviceGroup","currentTagValue":"RCA-Testbed"}]'
```

---

## UI Fallback

> 우측 상단 톱니바퀴 / 설정 메뉴 → **태그 관리** (또는 `/setting/tag` 직접 이동) → **+ 태그 값 추가** / 삭제.
