# Recipe: 관리대상 추가 (2-step: save → register)

polestar10 의 모든 관리대상 등록은 **2단계 흐름**을 따른다:

```
Step 1: POST /api/<type>/save         → staging 리스트에 추가, id 반환, registered=false
Step 2: POST /api/<type>/register     → 그룹/정책 바인딩 + 실제 관리대상으로 승격
```

이 흐름은 UI 의 "관리대상 추가" 대화상자 + "관리대상 등록" 버튼에 1:1 매핑됨.

## 리소스 타입별 지원 현황

| Type | prefix | save | register | 비고 |
|---|---|---|---|---|
| Web URL | `/api/weburl` | ✅ | ✅ | 에이전트 불필요, 순수 config. 아래 레시피 참조 |
| 서버 | `/api/sms/hosts` (추정) | ⏳ TBD | ⏳ TBD | WPM 에이전트 설치 + heartbeat 필요 (Issue 4 선행) |
| 데이터베이스 | `/api/dpm/*` (추정) | ⏳ TBD | ⏳ TBD | DPM 에이전트 + DB 접속 정보 필요 |
| 애플리케이션 | `/api/apm/*` (추정) | ⏳ TBD | ⏳ TBD | APM 에이전트 필요 |
| 쿠버네티스 | `/api/kcm/*` (추정) | ⏳ TBD | ⏳ TBD | KCM 에이전트 필요 |
| NMS 네트워크 | `/api/nms/*` (추정) | ⏳ TBD | ⏳ TBD | SNMP 타겟 또는 NMS 에이전트 |

→ agent 기반 리소스(서버/DB/APM/K8s/NMS) 는 먼저 타겟 호스트에 에이전트가 설치되어 heartbeat 를 쏘아야 staging 에 자동으로 뜨므로, 이 recipe 들은 Issue 4 (Ansible 플레이북) 이후 DevTools 캡처로 확정.

---

## 확정 레시피: Web URL 등록 (enduring example)

### 전제 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

### Step 1 — staging 추가 (`POST /api/weburl/save`)

```bash
TARGET_NAME="testbed-probe-$(date +%s)"
TARGET_URL="https://192.168.230.104/"

SAVE=$(curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg name "$TARGET_NAME" \
      --arg url "$TARGET_URL" \
      '{
        name: $name,
        description: "",
        method: "GET",
        requestBodyType: "form_data",
        url: $url,
        connectTimeout: 10,
        socketTimeout: 10,
        useProxy: false,
        useSni: false,
        sslVerify: false,
        successCode: 200
      }')" \
  "$POLESTAR10_BASE_URL/api/weburl/save")

# 성공 확인 및 id 추출
NEW_ID=$(echo "$SAVE" | jq -r '.data.id')
echo "staging OK → id=$NEW_ID, registered=$(echo "$SAVE" | jq -r '.data.registered')"
```

응답 스키마:

```json
{
  "success": true,
  "data": {
    "id": "69eacdf93c0ebbe080eb9995",
    "name": "testbed-probe-...",
    "url": "...",
    "method": "GET",
    "connectTimeout": 10,
    "socketTimeout": 10,
    "successCode": 200,
    "useProxy": false,
    "useSni": false,
    "sslVerify": false,
    "requestBodyType": "form_data",
    "registered": false,
    "loginId": "...",
    "ctime": 1776998056683,
    "mtime": 1776998056683,
    "...": "..."
  },
  "errorCode": null
}
```

이 시점에서는 아직 관리대상 **아님**. `registered:false` 로 staging 에만 머무는 상태. UI 에서 "관리대상 추가" 대화상자의 체크리스트에 뜨는 상태.

### Step 2 — 등록 (`POST /api/weburl/register`)

```bash
# body 는 배열 — 여러 staging 을 한 번에 등록 가능
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$NEW_ID" \
      '[{
        id: $id,
        dataPolicy: "defaultPolicy",
        tag: null,
        anomalyPolicyTagValue: null,
        groupId: 1
      }]')" \
  "$POLESTAR10_BASE_URL/api/weburl/register"
# → {"success":true,"data":null,"errorCode":null,...}
```

**필드 의미**:
| 필드 | 설명 | 값 예 |
|---|---|---|
| `id` | `save` 응답에서 받은 staging id | `"69eacd...995"` |
| `dataPolicy` | 데이터 수집 정책명 | `"defaultPolicy"` (기본) |
| `tag` | 사용자 정의 태그(선택) | `"RCA-Testbed"` 또는 `null` |
| `anomalyPolicyTagValue` | 이상감지 정책 라벨 | `"성능 이상감지 기본 정책"` 또는 `null` |
| `groupId` | 리소스 그룹 ID (from `list-groups.md`) | `1` = Default |

### Step 3 — 검증 (`POST /api/weburl/count`)

등록 성공 여부를 빠르게 확인:

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count"
# → {"success":true,"data":<현재 등록된 WebURL 수>,"errorCode":null,...}
```

정리는 [`delete-target.md`](./delete-target.md) 참조.

---

## 공통 패턴 (Issue 4 이후 다른 타입 확정 시 적용)

다른 리소스 타입 녹화 시 확인할 것:

1. **save endpoint**: `/api/<type>/save` 로 예상
2. **save payload**: 타입별 필수 필드 다름 (서버는 hostname/IP/OS, DB 는 DBMS 종류/접속정보 등)
3. **save response**: `data.id` 가 staging id
4. **register endpoint**: `/api/<type>/register` 로 예상
5. **register body**: array `[{id, dataPolicy, groupId, tag?, anomalyPolicyTagValue?}]`
6. **delete prefix**: `<type>_<id>` 형식일 가능성 (e.g. `server_...`, `apm_...`)

DevTools 캡처 절차는 [README.md 의 TBD 확정 절차](../README.md#tbd-엔드포인트-확정-절차) 참조.

## UI Fallback

2-step 플로우 중 어느 단계든 실패 시:

> **전체구성 > 관리대상** → 우측 상단 **+ 추가** 버튼 → 리소스타입 선택 → 폼 입력 (Web URL 의 경우 URL) → 저장. 그 다음 **관리대상 추가 목록** 에서 항목 체크 → **관리대상 등록** 버튼 → 그룹/정책 선택 → 저장.
