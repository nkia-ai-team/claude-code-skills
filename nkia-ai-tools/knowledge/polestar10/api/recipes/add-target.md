# Recipe: 관리대상 추가 (2-step: staging → register)

polestar10 의 모든 관리대상 등록은 **staging → register** 2단계.
1단계에서 staging 에 항목이 들어가는 방식이 리소스 모델별로 다르고, 2단계 register 는 동일 패턴.

```
┌─ Config-only (Web URL, SLO, Syslog 등) ─┐
│  Step 1: POST /api/<type>/save           │  사용자가 UI + 버튼으로 직접 추가
│         → staging id 반환                │
└──────────────────────────────────────────┘
                                            ┌─ Step 2 (공통) ─────────────────────────┐
                                            │  POST /api/<type-specific>/register     │
                                            │  body = ARRAY [{ id_or_agentId, ... }]  │
                                            │  group/policy/tag 바인딩 + 관리대상 승격 │
                                            └─────────────────────────────────────────┘
┌─ Agent-based (서버, DB, APM, KCM, NMS) ─┐
│  Step 1: 에이전트 설치 + heartbeat       │  자동 — save 호출 없음
│         → standby 자동 등록              │  /api/<type>/standby-* 로 조회 가능
└──────────────────────────────────────────┘
```

---

## 리소스 타입별 레시피 현황

| Type | 모델 | save / staging 진입 | register | 상태 |
|---|---|---|---|---|
| Web URL | config-only | `/api/weburl/save` | `/api/weburl/register` | ✅ 확정 |
| **서버** | agent-based (SMS) | (heartbeat 자동) | `/api/sms/standby-hosts/register` | ✅ 확정 |
| **데이터베이스 (DPM)** | **DB-direct** (별도 패턴) | `/api/dpm/preregister` (DB 접속 입력) | **`/api/dpm/register` 단일 호출** | ✅ **확정 — [dpm-lifecycle.md](dpm-lifecycle.md) 참조** |
| 애플리케이션 | agent-based (APM) | (heartbeat) | `/api/apm/standby-agent/*` 추정 | ⏳ TBD |
| 쿠버네티스 | agent-based (KCM) | (heartbeat) | `/api/kcm/standby-clusters-*` 추정 | ⏳ TBD |
| NMS 네트워크 | agent-based (NMS) | (heartbeat) | `/api/nms/v1/*` 추정 | ⏳ TBD |
| 사용자정의 (SLO/Syslog/SQL/SNMP OID) | config-only | `/api/<type>/save` 추정 | `/api/<type>/register` 추정 | ⏳ TBD (SLO 만 [slo.md](slo.md) 확정) |

> **DPM 은 다른 type 들과 다른 모델 (DB-direct)**: agent heartbeat 가 아닌 polestar10 가 직접 DB 에 SQL 쿼리. 따라서 staging 단계에 사용자가 DB 접속 정보 입력 필요. 라이프사이클 전체는 [dpm-lifecycle.md](dpm-lifecycle.md) 별도 recipe 참조.

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## 확정 레시피 1: Web URL 등록 (config-only)

### Step 1 — staging 추가 (`POST /api/weburl/save`)

```bash
TARGET_NAME="testbed-probe-$(date +%s)"
TARGET_URL="${POLESTAR10_BASE_URL}/"     # 또는 외부 URL

SAVE=$(curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg name "$TARGET_NAME" --arg url "$TARGET_URL" \
      '{name:$name, description:"", method:"GET", requestBodyType:"form_data",
        url:$url, connectTimeout:10, socketTimeout:10,
        useProxy:false, useSni:false, sslVerify:false, successCode:200}')" \
  "$POLESTAR10_BASE_URL/api/weburl/save")

NEW_ID=$(echo "$SAVE" | jq -r '.data.id')
echo "staging OK → id=$NEW_ID, registered=$(echo "$SAVE" | jq -r '.data.registered')"
```

### Step 2 — 등록 (`POST /api/weburl/register`)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$NEW_ID" \
      '[{id:$id, dataPolicy:"defaultPolicy", tag:null,
         anomalyPolicyTagValue:null, groupId:1}]')" \
  "$POLESTAR10_BASE_URL/api/weburl/register"
# → {"success":true,"data":null}
```

### Step 3 — 검증

```bash
curl $POLESTAR10_CURL_OPTS -X POST --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/weburl/count"
```

---

## 확정 레시피 2: 서버 등록 (agent-based)

**선행 조건**: 타겟 서버에 SMS 에이전트가 설치되어 polestar10-itg 의 collector 로 heartbeat 보내고 있어야 함. `hostStatus:"READY"` 가 standby 에 떠야 등록 가능.

### Step 1 — standby 에 떠있는지 확인

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/sms/standby-hosts-filter-step1" \
  | jq '.data.content[] | {agentId, hostname, ipAddress, hostStatus}'
```

원하는 호스트가 보이고 `hostStatus:"READY"` 면 다음 단계로. 안 보이면 에이전트 heartbeat 대기 (5~10분).

### Step 2 — 등록 (`POST /api/sms/standby-hosts/register`)

```bash
AGENT_ID="MA_<agent-host>"       # standby 응답의 agentId 그대로
SVC_GROUP="RCA-Testbed"          # tag 시스템의 serviceGroup value (없으면 자동 생성)
GROUP_ID=1                       # 1 = Default 시스템 그룹 (list-groups.md 참조)

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg aid "$AGENT_ID" --arg sg "$SVC_GROUP" --argjson gid "$GROUP_ID" \
      '[{
        agentId: $aid,
        managementStatus: "MANAGED",
        collectorPolicyTagValue: "defaultPolicy",
        serviceGroupTagValue: $sg,
        anomalyPolicyTagValue: "성능 이상감지 기본 정책",
        groupId: $gid
      }]')" \
  "$POLESTAR10_BASE_URL/api/sms/standby-hosts/register"
# → {"success":true,"data":{"failedCount":0,"successCount":1}}
```

**body 필드 의미** (Web URL register 와 비교):

| 필드 | Web URL register | 서버 register | 비고 |
|---|---|---|---|
| 식별자 | `id` (staging id) | `agentId` (SMS 에이전트 ID) | **필드명 다름** |
| 데이터 정책 | `dataPolicy:"defaultPolicy"` | `collectorPolicyTagValue:"defaultPolicy"` | **필드명 다름**, 값 동일 |
| 서비스 그룹 | `tag` | `serviceGroupTagValue` | **필드명 다름** |
| 이상감지 정책 | `anomalyPolicyTagValue` | `anomalyPolicyTagValue` | 동일 |
| 시스템 그룹 ID | `groupId` | `groupId` | 동일 |
| 관리 상태 | (없음) | `managementStatus:"MANAGED"` | 서버 전용 |

→ **register payload 가 type 별로 살짝 다름** — 통합 추상화 시 주의.

### Step 3 — 검증

```bash
# 등록된 서버 목록에 떴는지 확인
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"tagFilters":["confType = server"],"arguments":{}}' \
  "$POLESTAR10_BASE_URL/api/sms/hosts-filter" \
  | jq --arg aid "$AGENT_ID" '.data.content[] | select(.resourceId == $aid)'
```

---

## 다른 agent-based 타입 확정 절차 (DB/APM/KCM/NMS)

지금 확정된 패턴 일반화 가능한 가설:

```
POST /api/dpm/preregister/list   (이미 HAR 에 관찰됨)
POST /api/dpm/preregister/<???>  (= register, 패턴 추정)

POST /api/apm/standby-agent/count          (관찰됨)
POST /api/apm/standby-agent/new/count      (관찰됨)
POST /api/apm/standby-agent/<???>/register (= register, 패턴 추정)

POST /api/kcm/standby-clusters-filter-step1  (관찰됨)
POST /api/kcm/standby-clusters/<???>/register (= register, 패턴 추정)

POST /api/nms/v1/pre/list   (관찰됨)
POST /api/nms/v1/<???>      (= register, 패턴 추정)
```

각 타입의 register 본문 정확 확정은 해당 타입 에이전트 설치 후 DevTools 캡처 필요.

---

## UI Fallback

2-step 어느 단계든 실패 시:

> **전체구성 > 관리대상** → 우측 상단 **+ 추가** → (리소스타입 선택) → 폼/standby 선택 → 저장. **관리대상 추가** 목록에서 항목 체크 → **관리대상 등록** 버튼 → 그룹/이상감지 정책/서비스그룹 지정 → 저장.
