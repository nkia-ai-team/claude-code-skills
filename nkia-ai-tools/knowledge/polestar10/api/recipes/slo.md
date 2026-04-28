# Recipe: SLO (Service Level Objective) 등록

SLO 는 서비스 수준 목표 — 가용성, 성능 등 SLI(Service Level Indicator) 의 임계 목표값. polestar10 에서는 **관리대상 추가 다이얼로그의 SLO 탭** 으로 신규 등록.

다른 관리대상과 마찬가지로 **2-step (staging → register)** 패턴이지만 약간 다른 변형:

```
Step 1: POST /api/cm/slo/register/standby   ← staging 등록 (단순 "ok" 반환, id 없음)
Step 2: POST /api/cm/slo/register           ← list-filter 로 standby id 조회 후 활성화
```

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## Step 1 — Staging 등록 (`POST /api/cm/slo/register/standby`)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn \
      --arg name "testbed-slo-probe" \
      --arg svcgroup "RCA-Testbed" \
      --argjson startDate $(date +%s) \
      '{
        name: $name,
        description: null,
        targetTags: [("serviceGroup = " + $svcgroup)],
        targetConfIds: [],
        targetConfNames: [],
        excludedTags: [],
        excludedConfIds: [],
        excludedConfNames: [],
        setting: {
          sloTarget: 10,
          evaluationCycle: "WEEKLY",
          startDate: $startDate,
          weightFormula: "({A}*0.7) + ({B}*0.2) + ({C}*0.1)",
          excludeMaintenance: false
        },
        sliConditions: [
          {type: "AVAILABILITY", rowKey: "A"}
        ]
      }')" \
  "$POLESTAR10_BASE_URL/api/cm/slo/register/standby"
# → {"success":true,"data":"ok"}    ← id 안 반환
```

**필드 의미**:
| 필드 | 설명 | 값 예 |
|---|---|---|
| `name` | SLO 이름 (UI 표시) | `"testbed-slo-probe"` |
| `targetTags` | tag 표현식으로 대상 매칭 | `["serviceGroup = RCA-Testbed"]` |
| `targetConfIds` | 직접 conf ID 지정 (대신) | `["server_<...>"]` 등 |
| `excludedTags` / `excludedConfIds` | 제외 매칭 | 빈 배열 가능 |
| `setting.sloTarget` | 목표값 (%, 0~100) | `99.9` 등 |
| `setting.evaluationCycle` | 평가 주기 | `"DAILY"`, `"WEEKLY"`, `"MONTHLY"` |
| `setting.startDate` | 평가 시작 (Unix epoch sec) | `1777215600` |
| `setting.weightFormula` | 복합 SLI 의 가중치 식 | `"({A}*0.7) + ({B}*0.3)"` |
| `setting.excludeMaintenance` | 유지보수 시간 제외 | `true`/`false` |
| `sliConditions[]` | SLI 정의 배열 | type 별로 다름 |

**`sliConditions[]` type 옵션** (관찰됨):
- `"AVAILABILITY"` — 가용성 (UP/DOWN 비율)
- (기타 type — 캡처 필요)

---

## Step 2 — Standby ID 조회

`/api/cm/slo/register/standby` 가 ID 를 반환하지 않으므로, list-filter 로 standby (`registered:false`) 항목을 조회해서 ID 를 얻어야 함.

```bash
SLO_NAME="testbed-slo-probe"

# standby (registered:false) 만 필터링
SLO_ID=$(curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"sortFieldSets":[],"gridFilters":[{"field":"registered","operator":"Equals","values":[false]}]}' \
  "$POLESTAR10_BASE_URL/api/cm/slo/list-filter" \
  | jq -r --arg name "$SLO_NAME" '.data.content[] | select(.name == $name) | .id' \
  | head -1)
echo "SLO_ID=$SLO_ID"
```

응답 content[] 예:
```json
{
  "id": "<24-hex-char-slo-id>",
  "name": "testbed-slo-probe",
  "sli": ["AVAILABILITY"],
  "target": 10.0,
  "currentValue": 0.0,
  "errorBudgetUsage": 0.0,
  "evaluationCycle": "WEEKLY",
  "startDate": 1777215600,
  "ctime": 1777279932658
}
```

---

## Step 3 — 정식 등록 (`POST /api/cm/slo/register`)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$SLO_ID" '{parameter:[$id]}')" \
  "$POLESTAR10_BASE_URL/api/cm/slo/register"
# → {"success":true,"data":"ok"}
```

---

## 등록된 SLO 조회

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"sortFieldSets":[],"gridFilters":[{"field":"registered","operator":"Equals","values":[true]}]}' \
  "$POLESTAR10_BASE_URL/api/cm/slo/list-filter"
```

---

## 삭제

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "$(jq -cn --arg id "$SLO_ID" '{parameter:[$id]}')" \
  "$POLESTAR10_BASE_URL/api/cm/slo/delete"
# → {"success":true,"data":"ok"}
```

> 등록된 SLO 와 staging SLO 둘 다 같은 endpoint 로 삭제 가능. `gridFilters` 의 `registered` 값으로 list 단계에서만 분리.

---

## 부가: SLI 메트릭 조회

```bash
# 어떤 메트릭이 SLI 로 사용 가능한지 조회
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"resourceType":"server.Server"}' \
  "$POLESTAR10_BASE_URL/api/cm/slo/find-measurement"
```

---

## 흐름 요약 (오케스트레이터 관점)

```
1. (선택) /api/cm/slo/find-measurement → 사용 가능 메트릭 메타
2. /api/cm/slo/register/standby (body 풍부) → "ok"
3. /api/cm/slo/list-filter (gridFilters: registered=false) → standby 항목 ID 추출
4. /api/cm/slo/register (parameter:[id]) → "ok"
5. (검증) /api/cm/slo/list-filter (gridFilters: registered=true) → 새 SLO 보임
6. (정리) /api/cm/slo/delete (parameter:[id])
```

## UI Fallback

> **전체구성 > 관리대상** → 우측 상단 **+ 추가** → 좌측 리소스타입 목록에서 **SLO** 선택 → **+ 추가** 버튼 → 폼 (이름, SLI 조건, 평가 주기, 가중치 식 등) → 저장 → 다이얼로그의 staging 목록에서 **관리대상 등록** 버튼 → 그룹/정책 선택 → 저장.
