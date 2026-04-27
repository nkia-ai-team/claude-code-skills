# Recipe: 이상감지 정책 (Anomaly Policy) — 조회

이상감지 정책은 polestar10 의 AIOps 모듈이 학습한 **메트릭별 이상 패턴**. UI 에서 직접 정책을 만들기보단 시스템이 학습 자동 생성한 default 를 사용.

| 정책 | 용도 |
|---|---|
| `성능 이상감지 기본 정책` | 모든 시스템의 주요 성능 지표 학습 (default + auto) |

리소스 등록 (`weburl/register`, `sms/standby-hosts/register` 등) 시 `anomalyPolicyTagValue` 필드에 정책 **이름** 그대로 넣음.

---

## 환경변수

```bash
: "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
: "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
: "${POLESTAR10_CURL_OPTS:=-sk}"
```

---

## 정책 이름만 (간단 dropdown 용)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{}' \
  "$POLESTAR10_BASE_URL/api/aiops/v1/anomaly-policies/names"
```

응답:
```json
{
  "success": true,
  "data": [
    {"id": "<policy-id>", "name": "성능 이상감지 기본 정책", "auto": true}
  ]
}
```

리소스 등록 시 이 배열의 `.name` 값 중 하나를 `anomalyPolicyTagValue` 에 넣음.

```bash
# 사용 예: 첫 번째 정책의 이름 추출 (default 가 보통 첫 번째)
ANOMALY_POLICY=$(curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' -d '{}' \
  "$POLESTAR10_BASE_URL/api/aiops/v1/anomaly-policies/names" \
  | jq -r '.data[0].name')
echo "$ANOMALY_POLICY"  # → 성능 이상감지 기본 정책
```

---

## 정책 목록 (상세)

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":50,"arguments":{},"tagFilters":[]}' \
  "$POLESTAR10_BASE_URL/api/aiops/v1/anomaly-policies/list-filter"
```

응답 `content[]`:
```json
{
  "id": "<policy-id>",
  "name": "성능 이상감지 기본 정책",
  "description": "관리 주요 지표를 대상으로 학습",
  "enabled": true,
  "systemCount": 11,             // 적용된 시스템 수
  "metricCount": 0,              // 학습된 메트릭 수
  "tags": [
    {"key": "anomalyPolicy", "value": "성능 이상감지 기본 정책", "tagType": "SYSTEM"}
  ],
  "authorityInfos": [{"roleId": "...", "permission": 15}],
  "auto": true,
  "default": true
}
```

`isAuto:true + isDefault:true` 면 시스템 자동 생성/관리 정책.

---

## 정책 상세

```bash
POLICY_ID="<24-hex-char-anomaly-policy-id>"

curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  "$POLESTAR10_BASE_URL/api/aiops/v1/anomaly-policies/$POLICY_ID"
```

응답: 위 list-filter content 항목과 동일한 스키마 + 추가 디테일.

> 참고: body 가 빈 POST. URL path 에 ID 가 들어감.

---

## 권한 정보

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  "$POLESTAR10_BASE_URL/api/aiops/v1/anomaly-policies/$POLICY_ID/authority"
```

---

## 메트릭 모델 목록

이상감지에 사용되는 학습 모델 조회:

```bash
curl $POLESTAR10_CURL_OPTS -X POST \
  --cookie "$POLESTAR10_COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"pageNumber":1,"gridFilters":[],"sortFieldSets":[],"pagePerSize":30,"arguments":{},"tagFilters":[]}' \
  "$POLESTAR10_BASE_URL/api/aiops/v1/anomaly-metric-models/list-filter"
```

---

## 정책 생성/수정/삭제 — TBD

본 캡처 세션에서는 **조회만** 진행. 정책 자체의 CRUD 는 시스템 default 만으로 테스트베드 운영 가능. 신규 정책 생성이 필요하면 follow-up 캡처 필요.

---

## 흐름 요약 (오케스트레이터 관점)

리소스 등록 시:
```
1. /api/aiops/v1/anomaly-policies/names  → 사용 가능한 정책 이름 배열
2. 사용자 선택 (또는 default `"성능 이상감지 기본 정책"` 사용)
3. register payload 의 anomalyPolicyTagValue 에 선택한 이름 그대로 사용
   - weburl/register: { ..., "anomalyPolicyTagValue": "성능 이상감지 기본 정책" }
   - sms/standby-hosts/register: { ..., "anomalyPolicyTagValue": "성능 이상감지 기본 정책" }
```

## UI Fallback

> **알람 > 이상감지 정책** 메뉴에서 정책 목록 확인. 정책 이름을 등록 다이얼로그의 dropdown 에 그대로 사용.
